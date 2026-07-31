"""CPU-only contract tests for the excluded-input Stage 2b integration smoke."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import sys

import numpy as np
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "EvoScientist/skills/jspace-research-operations/scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location(
    "stage2b_integration_smoke", SCRIPTS / "stage2b_integration_smoke.py"
)
assert SPEC is not None
assert SPEC.loader is not None
smoke = importlib.util.module_from_spec(SPEC)
sys.modules["stage2b_integration_smoke"] = smoke
SPEC.loader.exec_module(smoke)


def _prohibited_digests() -> set[str]:
    digests: set[str] = set()
    for name in (
        "j-space-lab/jspace-stage2b-stimulus-v1.json",
        "j-space-lab/jspace-stage2b-pilot-v1.json",
    ):
        document = json.loads((ROOT / name).read_text(encoding="utf-8"))
        digests.update(prompt["sha256"] for prompt in document["prompts"])
    stage2 = json.loads(
        (ROOT / "tests/jspace/fixtures/stage2_manifest_digests.json").read_text(
            encoding="utf-8"
        )
    )
    digests.update(stage2["digests"])
    digests.add("daeaa63881dc0f58be689307a81b1fbc347674424f1cae45819f82372804f5a6")
    return digests


def _valid_report() -> dict:
    prompts = smoke.smoke_prompts()
    return {
        "schema": smoke.SMOKE_SCHEMA,
        "artifact_type": "integration_smoke",
        "run_id": "fixture-run",
        "created_at_utc": "2026-07-29T00:00:00+00:00",
        "evidence_class": "runtime_compatibility_only",
        "scope": "excluded_input_open_loop_measurement",
        "authorization": {
            "integration_smoke_authorized": True,
            "artifact_transfer_authorized": False,
        },
        "model": dict(smoke.PINNED_MODEL),
        "lens": {
            **smoke.PINNED_LENS,
            "source_layers": list(smoke.SELECTED_LAYERS),
        },
        "instrumentation": dict(smoke.PINNED_INSTRUMENTATION),
        "source_bundle": {
            "sha256": "a" * 64,
            "manifest": {
                "schema": "jspace-stage2b-integration-smoke-bundle/v1",
                "files": [
                    {"name": "stage2b_endpoint.py"},
                    {"name": "stage2b_preflight.py"},
                    {"name": "stage2b_integration_smoke.py"},
                ],
            },
        },
        "inputs": {
            "prompt_sha256s": [prompt["sha256"] for prompt in prompts],
            "recipient_sha256": prompts[0]["sha256"],
            "raw_prompt_persisted": False,
            "prohibited_overlap_count": 0,
        },
        "design": {
            "selected_layers": list(smoke.SELECTED_LAYERS),
            "representative_crossing_layer": smoke.REPRESENTATIVE_LAYER,
            "positions": [-2],
            "donor_assignment_count": 8,
            "broken_map_draw_count": 8,
            "unique_readouts": 81,
            "logical_crossings": 64,
            "smoke_donor_seeds": list(smoke.SMOKE_DONOR_SEEDS),
            "smoke_map_seeds": list(smoke.SMOKE_MAP_SEEDS),
        },
        "runtime": {
            "gpu_name": "fixture",
            "gpu_total_vram_gib": 16.0,
            "peak_allocated_gib": 4.0,
            "peak_reserved_gib": 5.0,
            "install_spec_sha256": "b" * 64,
            "fresh_process_after_install": True,
            "torchvision_state": "absent",
        },
        "timings_seconds": {
            "model_load": 1.0,
            "lens_load": 1.0,
            "capture_nine_prompts": 1.0,
            "selected_layer_probes": 1.0,
            "full_81_readout_crossing": 1.0,
        },
        "measurement": {
            "all_selected_layers_probed": True,
            "rank_parity_verified": True,
            "transport_parity_verified": True,
            "dual_floor_scores_recorded": True,
            "runtime_content_hashes_repeated": True,
            "unique_readout_count": 81,
            "logical_cell_count": 64,
        },
        "projection": {
            "basis_readouts": 81,
            "pilot_readouts": 6480,
            "linear_seconds": 80.0,
            "status": "engineering_projection_not_measured_pilot_runtime",
        },
        "retention": {
            "raw_activations_persisted": False,
            "full_logits_persisted": False,
            "raw_prompt_persisted": False,
        },
    }


def test_smoke_inputs_are_hash_bound_and_excluded():
    prompts = smoke.smoke_prompts()
    assert len(prompts) == 9
    assert len({prompt["sha256"] for prompt in prompts}) == 9
    for prompt in prompts:
        assert prompt["sha256"] == hashlib.sha256(prompt["text"].encode()).hexdigest()
        assert prompt["utf8_byte_count"] == len(prompt["text"].encode())
    smoke.require_disjoint_inputs(prompts, _prohibited_digests())


def test_smoke_seed_vectors_cover_eight_distinct_donors_without_becoming_pilot_seeds():
    prompts = smoke.smoke_prompts()
    residuals = {
        prompt["sha256"]: np.asarray([index + 1.0, index + 2.0], dtype=np.float32)
        for index, prompt in enumerate(prompts)
    }
    assignments = smoke.select_smoke_donors(
        residuals, recipient_sha256=prompts[0]["sha256"]
    )
    assert len(assignments) == 8
    assert len({assignment["source_prompt_sha256"] for assignment in assignments}) == 8
    assert [assignment["seed"] for assignment in assignments] == list(
        smoke.SMOKE_DONOR_SEEDS
    )
    assert smoke.SMOKE_DONOR_SEEDS != tuple(range(8))


def test_array_hash_binds_dtype_shape_and_bytes():
    value = np.asarray([[1.0, 2.0]], dtype=np.float32)
    assert smoke.array_sha256(value) == smoke.array_sha256(value.copy())
    assert smoke.array_sha256(value) != smoke.array_sha256(value.astype(np.float64))
    assert smoke.array_sha256(value) != smoke.array_sha256(value.reshape(2, 1))


def test_linear_projection_is_labeled_and_bounded():
    projection = smoke.project_pilot_readout_seconds(10.0, observed_readouts=81)
    assert projection == {
        "basis_readouts": 81,
        "pilot_readouts": 6480,
        "linear_seconds": pytest.approx(800.0),
        "status": "engineering_projection_not_measured_pilot_runtime",
    }


def test_valid_runtime_report_is_accepted():
    assert smoke.validate_runtime_report(_valid_report()) == []


@pytest.mark.parametrize(
    ("path", "value", "needle"),
    [
        (("authorization", "integration_smoke_authorized"), False, "authorization"),
        (("authorization", "artifact_transfer_authorized"), True, "transfer"),
        (("inputs", "prohibited_overlap_count"), 1, "excluded"),
        (("design", "unique_readouts"), 80, "81"),
        (("measurement", "logical_cell_count"), 63, "64"),
        (
            ("projection", "status"),
            "measured_pilot_runtime",
            "engineering projection",
        ),
        (("source_bundle", "sha256"), "not-a-digest", "source bundle"),
        (
            ("runtime", "fresh_process_after_install"),
            False,
            "fresh process",
        ),
        (
            ("runtime", "install_spec_sha256"),
            "not-a-digest",
            "install specification",
        ),
        (
            ("runtime", "torchvision_state"),
            "present",
            "torchvision",
        ),
    ],
)
def test_runtime_report_rejects_boundary_violations(path, value, needle):
    report = _valid_report()
    section, field = path
    report[section][field] = value
    assert any(needle in error for error in smoke.validate_runtime_report(report))


@pytest.mark.parametrize("field", ["gates", "decision", "thresholds", "pilot_results"])
def test_runtime_report_rejects_scientific_fields(field):
    report = _valid_report()
    report[field] = {}
    assert any(field in error for error in smoke.validate_runtime_report(report))
