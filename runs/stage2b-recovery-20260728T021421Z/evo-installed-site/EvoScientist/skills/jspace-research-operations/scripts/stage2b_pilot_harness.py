"""CPU-only executable smoke harness for the Stage 2b pilot instrument.

The smoke input is synthetic and cryptographically checked against the real
Stage 2b manifest. It exercises the same transport, fit-broken control,
wrong-activation selection, NTA, and factorial assembly functions used by the
pilot without consuming pilot or confirmatory prompts.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import stage2b_endpoint as endpoint

SCHEMA = "jspace-stage2b-instrument-smoke/v1"
SELECTED_LAYERS = (6, 13, 20, 26)
MIN_DENOMINATOR = 0.01


def _canonical_payload(document: dict[str, Any]) -> bytes:
    return (
        json.dumps(document, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def write_content_addressed(
    document: dict[str, Any], prefix: str, out_dir: Path
) -> Path:
    """Write canonical JSON once and verify any pre-existing path byte-for-byte."""
    payload = _canonical_payload(document)
    digest = hashlib.sha256(payload).hexdigest()
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{prefix}_{digest[:16]}.json"
    try:
        with path.open("xb") as handle:
            handle.write(payload)
    except FileExistsError:
        if path.read_bytes() != payload:
            raise RuntimeError(
                f"existing content-addressed path {path} does not match its payload"
            ) from None
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise RuntimeError(f"content-addressed readback failed for {path}")
    return path


def _score_from_vector(vector: Any) -> tuple[list[float], int, float]:
    """Decode a synthetic two-vector into a deterministic five-token readout."""
    import numpy as np

    value = np.asarray(vector, dtype=np.float64)
    signal = float(value[0] + 0.25 * value[1])
    logits = [signal, 0.75, 0.25, -0.25, -0.75]
    target_id = 0
    rank = endpoint.target_rank1(logits, target_id)
    return logits, rank, endpoint.rank_score(rank, len(logits))


def _real_manifest_digests() -> set[str]:
    repository_root = Path(__file__).resolve().parents[4]
    manifest_path = repository_root / "sakshi notes/jspace-stage2b-stimulus-v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {prompt["sha256"] for prompt in manifest["prompts"]}


def run_synthetic_smoke(out_dir: Path, *, run_id: str) -> Path:
    """Execute the complete synthetic 2×2 path and write one smoke artifact."""
    import numpy as np

    synthetic = [
        {
            "id": f"synthetic-smoke-{index}",
            "sha256": hashlib.sha256(
                f"stage2b-dedicated-synthetic-smoke-{index}".encode("utf-8")
            ).hexdigest(),
        }
        for index in range(4)
    ]
    real_digests = _real_manifest_digests()
    overlap = {prompt["sha256"] for prompt in synthetic} & real_digests
    if overlap:
        raise RuntimeError("dedicated synthetic smoke input overlaps the real manifest")

    prompt_logits = [-1.0, 0.75, 0.25, -0.25, -0.75]
    output_logits = [2.0, 0.75, 0.25, -0.25, -0.75]
    target_id = max(range(len(output_logits)), key=output_logits.__getitem__)
    prompt_score = endpoint.rank_score(
        endpoint.target_rank1(prompt_logits, target_id), len(prompt_logits)
    )
    output_score = endpoint.rank_score(
        endpoint.target_rank1(output_logits, target_id), len(output_logits)
    )

    records: list[dict[str, Any]] = []
    for layer in SELECTED_LAYERS:
        residuals = {
            prompt["sha256"]: np.asarray(
                [1.0 + index * 0.2, 0.3 + layer * 0.01 + index * 0.05],
                dtype=np.float32,
            )
            for index, prompt in enumerate(synthetic)
        }
        fitted_map = np.asarray(
            [[1.1 + layer * 0.002, 0.15], [0.05, 0.9]], dtype=np.float32
        )
        broken_seed = 1000 + layer
        broken_map = endpoint.build_fit_broken_map(fitted_map, broken_seed)
        for prompt in synthetic:
            prompt_sha256 = prompt["sha256"]
            correct = residuals[prompt_sha256]
            wrong, donor_sha256 = endpoint.select_wrong_activation(
                residuals,
                prompt_sha256,
                seed=29 + layer,
            )
            vectors = {
                "correct_act_fitted_map": endpoint.transport_with(correct, fitted_map),
                "correct_act_broken_map": endpoint.transport_with(correct, broken_map),
                "wrong_act_fitted_map": endpoint.transport_with(wrong, fitted_map),
                "wrong_act_broken_map": endpoint.transport_with(wrong, broken_map),
            }
            readout_scores = {
                name: _score_from_vector(vector)[2] for name, vector in vectors.items()
            }
            nta_cells = {
                name: endpoint.nta(
                    score,
                    prompt_score,
                    output_score,
                    MIN_DENOMINATOR,
                )
                for name, score in readout_scores.items()
            }
            if any(isinstance(value, endpoint.NTAExcluded) for value in nta_cells.values()):
                raise RuntimeError("synthetic smoke unexpectedly hit the denominator guard")
            factorial = endpoint.assemble_factorial_cells(**nta_cells)
            records.append(
                {
                    "prompt_id": prompt["id"],
                    "prompt_sha256": prompt_sha256,
                    "layer": layer,
                    "target_semantics": "model_argmax_synthetic",
                    "target_id": target_id,
                    "wrong_activation_source_sha256": donor_sha256,
                    "broken_map_seed": broken_seed,
                    "inputs": {
                        "correct_residual": correct.tolist(),
                        "wrong_residual": wrong.tolist(),
                        "fitted_map": fitted_map.tolist(),
                        "broken_map": broken_map.tolist(),
                        "prompt_logits": prompt_logits,
                        "output_logits": output_logits,
                    },
                    "readout_scores": readout_scores,
                    "factorial": factorial,
                }
            )

    artifact = {
        "schema": SCHEMA,
        "artifact_type": "synthetic_instrument_smoke",
        "run_mode": "synthetic_smoke",
        "run_id": run_id,
        "created_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "evidence_class": "synthetic_instrument_test",
        "selected_layers": list(SELECTED_LAYERS),
        "constants": {
            "min_denominator": MIN_DENOMINATOR,
            "rank_convention": endpoint.RANK_CONVENTION,
        },
        "input_set": {
            "kind": "dedicated_synthetic_excluded_from_stage2b_analysis",
            "prompt_ids": [prompt["id"] for prompt in synthetic],
            "prompt_sha256": [prompt["sha256"] for prompt in synthetic],
            "real_manifest_overlap_count": 0,
            "pilot_prompt_consumed": False,
            "confirmatory_prompt_consumed": False,
        },
        "pipeline": {
            "transport": "stage2b_endpoint.transport_with",
            "fit_broken_control": "stage2b_endpoint.build_fit_broken_map",
            "wrong_activation": "stage2b_endpoint.select_wrong_activation",
            "endpoint": "stage2b_endpoint.nta",
            "factorial": "stage2b_endpoint.assemble_factorial_cells",
        },
        "records": records,
        "retention": {
            "real_prompt_persisted": False,
            "model_activations_persisted": False,
        },
    }
    return write_content_addressed(
        artifact,
        "jspace_stage2b_instrument_smoke",
        out_dir,
    )


def _same_number(observed: Any, expected: Any) -> bool:
    return (
        isinstance(observed, (int, float))
        and isinstance(expected, (int, float))
        and math.isclose(float(observed), float(expected), rel_tol=1e-9, abs_tol=1e-9)
    )


def validate_synthetic_smoke(path: Path) -> tuple[dict[str, Any], list[str]]:
    """Recompute transports, scores, NTA cells, and factorial effects from a file."""
    errors: list[str] = []
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    try:
        artifact = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"path": str(path), "sha256": digest, "valid": False}, [str(exc)]
    if artifact.get("schema") != SCHEMA:
        errors.append(f"schema is {artifact.get('schema')!r}, expected {SCHEMA!r}")
    if artifact.get("artifact_type") != "synthetic_instrument_smoke":
        errors.append("artifact_type must be synthetic_instrument_smoke")
    input_set = artifact.get("input_set")
    if not isinstance(input_set, dict):
        errors.append("input_set must be an object")
    else:
        if input_set.get("real_manifest_overlap_count") != 0:
            errors.append("synthetic input overlaps the real manifest")
        for field in ("pilot_prompt_consumed", "confirmatory_prompt_consumed"):
            if input_set.get(field) is not False:
                errors.append(f"input_set.{field} must be false")
    layers = artifact.get("selected_layers")
    if layers != list(SELECTED_LAYERS):
        errors.append(f"selected_layers is {layers!r}, expected {list(SELECTED_LAYERS)!r}")
    records = artifact.get("records")
    if not isinstance(records, list) or len(records) != 16:
        errors.append("records must contain four prompts at each of four layers")
        records = []

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"record {index} is not an object")
            continue
        inputs = record.get("inputs")
        if not isinstance(inputs, dict):
            errors.append(f"record {index} inputs are missing")
            continue
        vectors = {
            "correct_act_fitted_map": endpoint.transport_with(
                inputs.get("correct_residual"), inputs.get("fitted_map")
            ),
            "correct_act_broken_map": endpoint.transport_with(
                inputs.get("correct_residual"), inputs.get("broken_map")
            ),
            "wrong_act_fitted_map": endpoint.transport_with(
                inputs.get("wrong_residual"), inputs.get("fitted_map")
            ),
            "wrong_act_broken_map": endpoint.transport_with(
                inputs.get("wrong_residual"), inputs.get("broken_map")
            ),
        }
        target_id = record.get("target_id")
        prompt_logits = inputs.get("prompt_logits")
        output_logits = inputs.get("output_logits")
        if not isinstance(target_id, int) or not isinstance(prompt_logits, list) or not isinstance(output_logits, list):
            errors.append(f"record {index} target/logit inputs are malformed")
            continue
        prompt_score = endpoint.rank_score(
            endpoint.target_rank1(prompt_logits, target_id), len(prompt_logits)
        )
        output_score = endpoint.rank_score(
            endpoint.target_rank1(output_logits, target_id), len(output_logits)
        )
        recomputed_scores = {
            name: _score_from_vector(vector)[2] for name, vector in vectors.items()
        }
        recorded_scores = record.get("readout_scores")
        for name, expected in recomputed_scores.items():
            observed = recorded_scores.get(name) if isinstance(recorded_scores, dict) else None
            if not _same_number(observed, expected):
                errors.append(f"record {index} score {name} disagrees with recomputed value")
        nta_cells = {
            name: endpoint.nta(
                score,
                prompt_score,
                output_score,
                MIN_DENOMINATOR,
            )
            for name, score in recomputed_scores.items()
        }
        if any(isinstance(value, endpoint.NTAExcluded) for value in nta_cells.values()):
            errors.append(f"record {index} recomputation hit denominator exclusion")
            continue
        recomputed_factorial = endpoint.assemble_factorial_cells(**nta_cells)
        recorded_factorial = record.get("factorial")
        if not isinstance(recorded_factorial, dict):
            errors.append(f"record {index} factorial is missing")
            continue
        for field in ("simple_effect_of_map", "main_effect_of_map", "interaction"):
            if not _same_number(recorded_factorial.get(field), recomputed_factorial[field]):
                errors.append(f"record {index} {field} disagrees with recomputed value")
        recorded_cells = recorded_factorial.get("cells")
        for name, expected in recomputed_factorial["cells"].items():
            observed = recorded_cells.get(name) if isinstance(recorded_cells, dict) else None
            if not _same_number(observed, expected):
                errors.append(f"record {index} cell {name} disagrees with recomputed value")
        if record.get("wrong_activation_source_sha256") == record.get("prompt_sha256"):
            errors.append(f"record {index} reused its own activation as the wrong control")

    filename_prefix = path.stem.rsplit("_", 1)[-1]
    if len(filename_prefix) == 16 and not digest.startswith(filename_prefix):
        errors.append("content-addressed filename does not match artifact SHA-256")
    return {
        "path": str(path.resolve()),
        "sha256": digest,
        "size_bytes": len(payload),
        "record_count": len(records),
        "valid": not errors,
    }, errors
