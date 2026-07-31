from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "j-space-lab" / "stage2b_primary_floor_audit.py"
SPEC = importlib.util.spec_from_file_location(
    "stage2b_primary_floor_audit", MODULE_PATH
)
assert SPEC is not None
assert SPEC.loader is not None
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def test_linear_quantile_exposes_exact_bracket() -> None:
    value, evidence = audit.linear_quantile([0.1, 0.2, 0.3, 0.4], 0.05)

    assert value == pytest.approx(0.115)
    assert evidence == {
        "position": pytest.approx(0.15),
        "lower_index": 0,
        "upper_index": 1,
        "lower_value": 0.1,
        "upper_value": 0.2,
        "interpolation_fraction": pytest.approx(0.15),
    }


def test_rank_score_inverse_recovers_integer_rank() -> None:
    vocab_size = 151_936
    for rank in (1, 2, 57, vocab_size):
        score = -audit.math.log(rank) / audit.math.log(vocab_size)
        assert audit.rank_from_score(score, vocab_size) == rank


def test_build_diagnostic_recomputes_guard_without_writes() -> None:
    categories = [f"category-{index}" for index in range(5)]
    prompts = []
    records = []
    denominators = []
    for prompt_index in range(20):
        digest = f"{prompt_index:064x}"
        category = categories[prompt_index // 4]
        prompts.append(
            {
                "category": category,
                "id": f"s{prompt_index:03d}",
                "index": prompt_index,
                "sha256": digest,
                "text": f"Prompt {prompt_index}",
                "utf8_byte_count": len(f"Prompt {prompt_index}"),
            }
        )
        denominator = 0.10 + 0.01 * prompt_index
        denominators.extend([denominator] * 4)
        floor_scores = {
            audit.PRIMARY_FLOOR: -denominator,
            audit.SENSITIVITY_FLOOR: -0.5,
            "output_decoded": 0.0,
        }
        target = {
            "argmax_tie_token_ids": [prompt_index],
            "max_logit": 1.0,
        }
        for layer in (6, 13, 20, 26):
            records.append(
                {
                    "prompt_sha256": digest,
                    "category": category,
                    "layer": layer,
                    "target_id": prompt_index,
                    "target_derivation": target,
                    "floor_scores": floor_scores,
                    "floor_status": {},
                }
            )

    guard, _ = audit.linear_quantile(denominators, 0.05)
    for record in records:
        primary_denominator = -record["floor_scores"][audit.PRIMARY_FLOOR]
        sensitivity_denominator = -record["floor_scores"][audit.SENSITIVITY_FLOOR]
        record["floor_status"] = {
            audit.PRIMARY_FLOOR: audit._expected_floor_status(
                primary_denominator, guard
            ),
            audit.SENSITIVITY_FLOOR: audit._expected_floor_status(
                sensitivity_denominator, guard
            ),
        }
    source_records = sorted(
        records,
        key=lambda record: (
            record["prompt_sha256"],
            (6, 13, 20, 26).index(record["layer"]),
        ),
    )
    source_denominators = [
        -record["floor_scores"][audit.PRIMARY_FLOOR] for record in source_records
    ]
    artifact = {
        "constants": {"min_denominator": guard},
        "denominator_derivation": {
            "source_floor": audit.PRIMARY_FLOOR,
            "source_count": 80,
            "source_denominators_sha256": audit.canonical_sha256(source_denominators),
            "quantile": 0.05,
            "quantile_method": "linear",
            "derived_value": guard,
            "source_order": [
                {
                    "prompt_sha256": record["prompt_sha256"],
                    "layer": record["layer"],
                }
                for record in source_records
            ],
        },
        "design": {"vocab_size": 151_936},
        "descriptive": {"records": records},
    }
    result = audit.build_diagnostic(
        artifact,
        {"prompts": prompts},
        tokenizer=None,
    )

    assert result["guard"]["recomputed"] == guard
    assert result["boundaries"]["artifact_modified"] is False
    assert result["coverage_by_category"]["category-0"]["prompt_count"] == 4
    assert result["all_prompt_geometry"][0]["primary_eligible"] is False

    first_prompt = prompts[0]["sha256"]
    first_records = [
        record
        for record in artifact["descriptive"]["records"]
        if record["prompt_sha256"] == first_prompt
    ]
    original_status = first_records[0]["floor_status"][audit.PRIMARY_FLOOR].copy()
    for record in first_records:
        record["floor_status"][audit.PRIMARY_FLOOR]["eligible"] = True
    with pytest.raises(ValueError, match="retained floor_status does not recompute"):
        audit.build_diagnostic(artifact, {"prompts": prompts}, tokenizer=None)
    for record in first_records:
        record["floor_status"][audit.PRIMARY_FLOOR] = original_status.copy()

    artifact["denominator_derivation"]["quantile"] = 0.10
    with pytest.raises(ValueError, match="denominator_derivation"):
        audit.build_diagnostic(artifact, {"prompts": prompts}, tokenizer=None)


def test_bound_json_fails_closed_on_wrong_identity(tmp_path: Path) -> None:
    candidate = tmp_path / audit.CANONICAL_ARTIFACT_BASENAME
    candidate.write_text("{}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        audit.read_bound_json(
            candidate,
            expected_basename=audit.CANONICAL_ARTIFACT_BASENAME,
            expected_sha256="0" * 64,
        )


def test_unexpected_name_is_refused_before_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    candidate = tmp_path / "confirmation-like.json"
    candidate.write_text("{}\n", encoding="utf-8")

    def forbidden_read(_path: Path) -> bytes:
        raise AssertionError("unexpected input was read")

    monkeypatch.setattr(Path, "read_bytes", forbidden_read)
    with pytest.raises(ValueError, match="refusing unexpected input name"):
        audit.read_bound_json(
            candidate,
            expected_basename=audit.CANONICAL_ARTIFACT_BASENAME,
            expected_sha256=audit.CANONICAL_ARTIFACT_SHA256,
        )


def test_symlink_is_refused_before_read(tmp_path: Path) -> None:
    target = tmp_path / "target.json"
    target.write_text("{}\n", encoding="utf-8")
    candidate = tmp_path / audit.CANONICAL_ARTIFACT_BASENAME
    candidate.symlink_to(target)

    with pytest.raises(ValueError, match="refusing symlink"):
        audit.read_bound_json(
            candidate,
            expected_basename=audit.CANONICAL_ARTIFACT_BASENAME,
            expected_sha256=audit.CANONICAL_ARTIFACT_SHA256,
        )


def test_hash_override_cli_is_not_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "stage2b_primary_floor_audit.py",
            audit.CANONICAL_ARTIFACT_BASENAME,
            audit.CANONICAL_PILOT_VIEW_BASENAME,
            "--artifact-sha256",
            "0" * 64,
        ],
    )

    with pytest.raises(SystemExit):
        audit.parse_args()


def test_tokenizer_probe_is_local_only(monkeypatch: pytest.MonkeyPatch) -> None:
    observed = {}

    class FakeTokenizer:
        @classmethod
        def from_pretrained(cls, model_id: str, **kwargs: object) -> object:
            observed["model_id"] = model_id
            observed.update(kwargs)
            return object()

    class FakeTransformers:
        AutoTokenizer = FakeTokenizer

    monkeypatch.setitem(sys.modules, "transformers", FakeTransformers)
    assert audit._load_cached_tokenizer() is not None
    assert observed == {
        "model_id": audit.MODEL_ID,
        "revision": audit.MODEL_REVISION,
        "local_files_only": True,
    }
