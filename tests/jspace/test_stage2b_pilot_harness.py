"""Executable CPU smoke tests for the Stage 2b pilot harness."""

from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import sys

import pytest

_SCRIPTS = (
    pathlib.Path(__file__).resolve().parents[2]
    / "EvoScientist/skills/jspace-research-operations/scripts"
)
sys.path.insert(0, str(_SCRIPTS))
_spec = importlib.util.spec_from_file_location(
    "stage2b_pilot_harness", _SCRIPTS / "stage2b_pilot_harness.py"
)
assert _spec is not None
assert _spec.loader is not None
harness = importlib.util.module_from_spec(_spec)
sys.modules["stage2b_pilot_harness"] = harness
_spec.loader.exec_module(harness)


@pytest.fixture(scope="module")
def statistical_artifact(tmp_path_factory):
    out_dir = tmp_path_factory.mktemp("stage2b-statistical-smoke")
    return harness.run_synthetic_pilot_statistics(
        out_dir,
        run_id="synthetic-statistical-smoke-test",
    )


def test_module_imports_without_torch_jlens_or_scipy():
    source = (
        "import importlib.util as u,sys,json;"
        f"sys.path.insert(0,{str(_SCRIPTS)!r});"
        f"s=u.spec_from_file_location('h',{str(_SCRIPTS / 'stage2b_pilot_harness.py')!r});"
        "m=u.module_from_spec(s);s.loader.exec_module(m);"
        "print(json.dumps([n for n in ('torch','jlens','scipy') if n in sys.modules]))"
    )
    result = subprocess.run(
        [sys.executable, "-c", source],
        capture_output=True,
        text=True,
        check=True,
        cwd=_SCRIPTS,
    )
    assert json.loads(result.stdout) == []


def test_smoke_writes_nonempty_content_addressed_artifact_and_validates(tmp_path):
    path = harness.run_synthetic_smoke(tmp_path, run_id="synthetic-smoke-test")
    assert path.stat().st_size > 0
    assert path.name.startswith("jspace_stage2b_instrument_smoke_")
    summary, errors = harness.validate_synthetic_smoke(path)
    assert errors == []
    assert summary["valid"] is True
    assert summary["record_count"] == 16
    assert summary["sha256"].startswith(path.stem.rsplit("_", 1)[-1])


def test_smoke_exercises_all_factorial_cells_at_all_study_layers(tmp_path):
    path = harness.run_synthetic_smoke(tmp_path, run_id="synthetic-factorial-test")
    artifact = json.loads(path.read_text())
    assert artifact["selected_layers"] == [6, 13, 20, 26]
    assert len(artifact["records"]) == 16
    for record in artifact["records"]:
        assert len(record["donor_assignments"]) == 8
        assert (
            len({item["donor_assignment_id"] for item in record["donor_assignments"]})
            == 8
        )
        assert len(record["map_draws"]) == 8
        assert len({item["map_draw_id"] for item in record["map_draws"]}) == 8
        for floor in ("input_embedding_decoded", "layer0_residual_decoded"):
            crossed = harness.endpoint.materialize_crossed_factorials(
                record["factorized_nta"][floor]
            )
            assert crossed["unique_readout_count"] == 81
            assert crossed["logical_cell_count"] == 64
        difference = record["factorized_nta"]["sensitivity_minus_primary"]
        assert set(difference) == {
            "correct_act_fitted_map",
            "correct_act_broken_map",
            "wrong_act_fitted_map",
            "wrong_act_broken_map",
        }


def test_smoke_inputs_are_excluded_from_real_stage2b_manifest(tmp_path):
    path = harness.run_synthetic_smoke(tmp_path, run_id="synthetic-isolation-test")
    artifact = json.loads(path.read_text())
    assert artifact["input_set"]["real_manifest_overlap_count"] == 0
    assert artifact["input_set"]["pilot_prompt_consumed"] is False
    assert artifact["input_set"]["confirmatory_prompt_consumed"] is False


def test_validator_rejects_a_corrupted_factorial_effect(tmp_path):
    path = harness.run_synthetic_smoke(tmp_path, run_id="synthetic-corruption-test")
    artifact = json.loads(path.read_text())
    artifact["records"][0]["factorized_nta"]["input_embedding_decoded"][
        "wrong_act_broken_map"
    ]["donor-0"]["map-0"] = 999.0
    corrupted = tmp_path / "corrupted.json"
    corrupted.write_text(json.dumps(artifact, sort_keys=True, indent=2) + "\n")
    _, errors = harness.validate_synthetic_smoke(corrupted)
    assert any("factorized NTA" in error and "recomputed" in error for error in errors)


def test_validator_rejects_a_missing_cross_cell(tmp_path):
    path = harness.run_synthetic_smoke(tmp_path, run_id="synthetic-missing-cross")
    artifact = json.loads(path.read_text())
    del artifact["records"][0]["factorized_scores"]["wrong_act_broken_map"]["donor-0"][
        "map-7"
    ]
    corrupted = tmp_path / "missing-cross.json"
    corrupted.write_text(json.dumps(artifact, sort_keys=True, indent=2) + "\n")
    _, errors = harness.validate_synthetic_smoke(corrupted)
    assert any("complete 8x8" in error for error in errors)


def test_validator_rejects_a_corrupted_sensitivity_difference(tmp_path):
    path = harness.run_synthetic_smoke(tmp_path, run_id="synthetic-bad-sensitivity")
    artifact = json.loads(path.read_text())
    artifact["records"][0]["factorized_nta"]["sensitivity_minus_primary"][
        "correct_act_fitted_map"
    ] = 999.0
    corrupted = tmp_path / "bad-sensitivity.json"
    corrupted.write_text(json.dumps(artifact, sort_keys=True, indent=2) + "\n")
    _, errors = harness.validate_synthetic_smoke(corrupted)
    assert any("sensitivity_minus_primary" in error for error in errors)


def test_content_addressed_writer_refuses_conflicting_existing_file(
    tmp_path, monkeypatch
):
    artifact = {"schema": "test", "value": 1}
    path = harness.write_content_addressed(artifact, "prefix", tmp_path)
    path.write_text("different bytes")
    with pytest.raises(RuntimeError, match="existing content-addressed path"):
        harness.write_content_addressed(artifact, "prefix", tmp_path)


def test_complete_synthetic_pilot_statistics_recompute(statistical_artifact):
    summary, errors = harness.validate_synthetic_pilot_statistics(statistical_artifact)
    assert errors == []
    assert summary["valid"] is True
    assert summary["record_count"] == 80


def test_synthetic_pilot_statistics_cover_the_ratified_packet(statistical_artifact):
    artifact = json.loads(statistical_artifact.read_text())
    assert len(artifact["records"]) == 80
    assert artifact["denominator_derivation"]["source_count"] == 80
    assert len(artifact["inference"]["coverage"]) == 8
    assert len(artifact["inference"]["prompt_layer_effects"]) == 160
    assert len(artifact["inference"]["layer_estimates"]) == 48
    assert artifact["inference"]["rng"]["iterations"] == 20_000
    assert artifact["inference"]["rng"]["bit_generator"] == "PCG64"
    assert artifact["inference"]["threshold_derivation"]["available"] is True
    assert "gates" not in artifact
    assert "decision" not in artifact


def test_synthetic_pilot_statistics_use_exact_seed_provenance(statistical_artifact):
    artifact = json.loads(statistical_artifact.read_text())
    expected = harness.statistics.derive_crossing_seed_vectors()
    first = artifact["records"][0]
    assert first["donor_seed_identities"] == expected["donors"]
    assert first["map_seed_identities"] == expected["maps"]
    assert all(
        entry["bit_generator"] == "PCG64"
        for entry in first["donor_seed_identities"] + first["map_seed_identities"]
    )


@pytest.mark.parametrize(
    ("section", "mutate", "needle"),
    [
        (
            "denominator",
            lambda artifact: artifact["denominator_derivation"].__setitem__(
                "source_denominators_sha256", "f" * 64
            ),
            "denominator derivation",
        ),
        (
            "records",
            lambda artifact: artifact["records"][0]["factorized_nta"][
                "input_embedding_decoded"
            ].__setitem__("correct_act_fitted_map", 999.0),
            "statistical records",
        ),
        (
            "inference",
            lambda artifact: artifact["inference"]["rng"].__setitem__(
                "namespace", "invented"
            ),
            "inference",
        ),
    ],
)
def test_synthetic_statistical_validator_rejects_corruption(
    statistical_artifact, tmp_path, section, mutate, needle
):
    artifact = json.loads(statistical_artifact.read_text())
    mutate(artifact)
    path = tmp_path / f"corrupt-{section}.json"
    path.write_text(json.dumps(artifact, sort_keys=True, indent=2) + "\n")
    _, errors = harness.validate_synthetic_pilot_statistics(path)
    assert any(needle in error for error in errors)
