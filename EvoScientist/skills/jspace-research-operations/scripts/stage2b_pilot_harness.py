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
import stage2b_statistics as statistics

SCHEMA = "jspace-stage2b-instrument-smoke/v1"
STATISTICAL_SCHEMA = "jspace-stage2b-statistical-smoke/v1"
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


def _map_factorized(source: dict[str, Any], transform: Any) -> dict[str, Any]:
    """Apply ``transform`` to each of the 81 unique readouts."""
    return {
        "correct_act_fitted_map": transform(source["correct_act_fitted_map"]),
        "correct_act_broken_map": {
            map_id: transform(value)
            for map_id, value in source["correct_act_broken_map"].items()
        },
        "wrong_act_fitted_map": {
            donor_id: transform(value)
            for donor_id, value in source["wrong_act_fitted_map"].items()
        },
        "wrong_act_broken_map": {
            donor_id: {map_id: transform(value) for map_id, value in row.items()}
            for donor_id, row in source["wrong_act_broken_map"].items()
        },
    }


def _json_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _real_manifest_digests() -> set[str]:
    repository_root = Path(__file__).resolve().parents[4]
    manifest_path = repository_root / "j-space-lab/jspace-stage2b-stimulus-v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {prompt["sha256"] for prompt in manifest["prompts"]}


def run_synthetic_smoke(out_dir: Path, *, run_id: str) -> Path:
    """Execute the two-floor, eight-donor by eight-map synthetic path."""
    import numpy as np

    synthetic = [
        {
            "id": f"synthetic-smoke-{index}",
            "sha256": hashlib.sha256(
                f"stage2b-dedicated-synthetic-smoke-{index}".encode()
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
    layer0_logits = [0.0, 0.75, 0.25, -0.25, -0.75]
    layer0_score = endpoint.rank_score(
        endpoint.target_rank1(layer0_logits, target_id), len(layer0_logits)
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
        map_draws = []
        broken_maps = {}
        for map_index in range(8):
            map_id = f"map-{map_index}"
            seed = 1000 + layer * 100 + map_index
            broken_map = endpoint.build_fit_broken_map(fitted_map, seed)
            broken_maps[map_id] = broken_map
            map_draws.append(
                {
                    "map_draw_id": map_id,
                    "seed": seed,
                    "sha256": _json_digest(broken_map.tolist()),
                    "spectrum_check": endpoint.singular_spectrum_evidence(
                        fitted_map, broken_map
                    ),
                }
            )
        for prompt in synthetic:
            prompt_sha256 = prompt["sha256"]
            correct = residuals[prompt_sha256]
            donor_assignments = []
            wrong_residuals = {}
            for donor_index in range(8):
                donor_id = f"donor-{donor_index}"
                seed = 29 + layer * 100 + donor_index
                wrong, donor_sha256 = endpoint.select_wrong_activation(
                    residuals,
                    prompt_sha256,
                    seed=seed,
                )
                wrong_residuals[donor_id] = wrong
                donor_assignments.append(
                    {
                        "donor_assignment_id": donor_id,
                        "seed": seed,
                        "source_prompt_sha256": donor_sha256,
                        "residual_sha256": _json_digest(wrong.tolist()),
                    }
                )
            vectors = {
                "correct_act_fitted_map": endpoint.transport_with(correct, fitted_map),
                "correct_act_broken_map": {
                    map_id: endpoint.transport_with(correct, broken_map)
                    for map_id, broken_map in broken_maps.items()
                },
                "wrong_act_fitted_map": {
                    donor_id: endpoint.transport_with(wrong, fitted_map)
                    for donor_id, wrong in wrong_residuals.items()
                },
                "wrong_act_broken_map": {
                    donor_id: {
                        map_id: endpoint.transport_with(wrong, broken_map)
                        for map_id, broken_map in broken_maps.items()
                    }
                    for donor_id, wrong in wrong_residuals.items()
                },
            }
            factorized_scores = _map_factorized(
                vectors, lambda vector: _score_from_vector(vector)[2]
            )
            primary = _map_factorized(
                factorized_scores,
                lambda score: endpoint.nta(
                    score, prompt_score, output_score, MIN_DENOMINATOR
                ),
            )
            sensitivity = _map_factorized(
                factorized_scores,
                lambda score: endpoint.nta(
                    score, layer0_score, output_score, MIN_DENOMINATOR
                ),
            )
            for floor in (primary, sensitivity):
                materialized = endpoint.materialize_crossed_factorials(floor)
                if any(
                    cell["factorial"]["excluded"] for cell in materialized["factorials"]
                ):
                    raise RuntimeError(
                        "synthetic smoke unexpectedly hit the denominator guard"
                    )
            differences = _map_factorized(
                primary,
                lambda value: value,
            )

            def subtract_tree(left: Any, right: Any) -> Any:
                if isinstance(left, dict):
                    return {key: subtract_tree(left[key], right[key]) for key in left}
                return right - left

            differences = subtract_tree(primary, sensitivity)
            factorized_nta = {
                "input_embedding_decoded": primary,
                "layer0_residual_decoded": sensitivity,
                "sensitivity_minus_primary": differences,
            }
            records.append(
                {
                    "prompt_id": prompt["id"],
                    "prompt_sha256": prompt_sha256,
                    "layer": layer,
                    "target_semantics": "model_argmax_synthetic",
                    "target_id": target_id,
                    "donor_assignments": donor_assignments,
                    "map_draws": map_draws,
                    "floor_scores": {
                        "input_embedding_decoded": prompt_score,
                        "layer0_residual_decoded": layer0_score,
                        "output_decoded": output_score,
                    },
                    "inputs": {
                        "correct_residual": correct.tolist(),
                        "wrong_residuals": {
                            key: value.tolist()
                            for key, value in wrong_residuals.items()
                        },
                        "fitted_map": fitted_map.tolist(),
                        "broken_maps": {
                            key: value.tolist() for key, value in broken_maps.items()
                        },
                        "prompt_logits": prompt_logits,
                        "layer0_logits": layer0_logits,
                        "output_logits": output_logits,
                    },
                    "factorized_scores": factorized_scores,
                    "factorized_nta": factorized_nta,
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


def _synthetic_statistical_prompts() -> list[dict[str, str]]:
    return [
        {
            "id": f"synthetic-statistics-{index:02d}",
            "category": f"category-{index // 4}",
            "sha256": hashlib.sha256(
                f"stage2b-dedicated-synthetic-statistics-{index}".encode()
            ).hexdigest(),
        }
        for index in range(20)
    ]


def _synthetic_factorized_scores(
    prompt_index: int,
    layer_index: int,
) -> dict[str, Any]:
    donor_ids = [f"donor-{index}" for index in range(8)]
    map_ids = [f"map-{index}" for index in range(8)]
    correct_fitted = 0.8 + prompt_index / 1000 + layer_index / 500
    return {
        "correct_act_fitted_map": correct_fitted,
        "correct_act_broken_map": {
            map_id: correct_fitted - (0.20 + map_index / 1000)
            for map_index, map_id in enumerate(map_ids)
        },
        "wrong_act_fitted_map": {
            donor_id: 0.40 + donor_index / 1000
            for donor_index, donor_id in enumerate(donor_ids)
        },
        "wrong_act_broken_map": {
            donor_id: {
                map_id: 0.40 + donor_index / 1000 - (0.05 + map_index / 5000)
                for map_index, map_id in enumerate(map_ids)
            }
            for donor_index, donor_id in enumerate(donor_ids)
        },
    }


def run_synthetic_pilot_statistics(out_dir: Path, *, run_id: str) -> Path:
    """Execute the complete ratified two-stage pilot statistics without science."""
    import numpy as np

    prompts = _synthetic_statistical_prompts()
    real_digests = _real_manifest_digests()
    if {prompt["sha256"] for prompt in prompts} & real_digests:
        raise RuntimeError("synthetic statistical input overlaps the real manifest")
    vectors = statistics.derive_crossing_seed_vectors()
    raw_records = []
    for prompt_index, prompt in enumerate(prompts):
        for layer_index, layer in enumerate(SELECTED_LAYERS):
            primary_floor = (
                -0.20
                if prompt_index == 0
                else -(0.50 + prompt_index / 1000 + layer_index / 10000)
            )
            raw_records.append(
                {
                    "prompt_sha256": prompt["sha256"],
                    "category": prompt["category"],
                    "layer": layer,
                    "floor_scores": {
                        "input_embedding_decoded": primary_floor,
                        "layer0_residual_decoded": -0.60,
                        "output_decoded": 0.0,
                    },
                    "factorized_scores": _synthetic_factorized_scores(
                        prompt_index, layer_index
                    ),
                    "donor_seed_identities": vectors["donors"],
                    "map_seed_identities": vectors["maps"],
                }
            )
    records, denominator = statistics.materialize_pilot_nta(raw_records)
    statistics_sha256 = hashlib.sha256(
        Path(statistics.__file__).read_bytes()
    ).hexdigest()
    inference = statistics.build_pilot_inference(
        records,
        denominator,
        derivation_code_sha256=statistics_sha256,
        numpy_version=np.__version__,
    )
    artifact = {
        "schema": STATISTICAL_SCHEMA,
        "artifact_type": "synthetic_pilot_statistics",
        "run_mode": "synthetic_smoke",
        "run_id": run_id,
        "created_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "evidence_class": "synthetic_instrument_test",
        "selected_layers": list(SELECTED_LAYERS),
        "input_set": {
            "kind": "dedicated_synthetic_excluded_from_stage2b_analysis",
            "prompt_ids": [prompt["id"] for prompt in prompts],
            "prompt_sha256": [prompt["sha256"] for prompt in prompts],
            "real_manifest_overlap_count": 0,
            "pilot_prompt_consumed": False,
            "confirmatory_prompt_consumed": False,
        },
        "records": records,
        "denominator_derivation": denominator,
        "inference": inference,
        "statistics_code_sha256": statistics_sha256,
        "numpy_version": np.__version__,
    }
    return write_content_addressed(
        artifact,
        "jspace_stage2b_statistical_smoke",
        out_dir,
    )


def validate_synthetic_pilot_statistics(
    path: Path,
) -> tuple[dict[str, Any], list[str]]:
    """Recompute the complete two-stage statistical packet from retained scores."""
    errors: list[str] = []
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    try:
        artifact = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"path": str(path), "sha256": digest, "valid": False}, [str(exc)]
    if artifact.get("schema") != STATISTICAL_SCHEMA:
        errors.append("statistical smoke schema is invalid")
    for forbidden in ("gates", "decision", "threshold_estimates"):
        if forbidden in artifact:
            errors.append(f"statistical smoke contains forbidden {forbidden}")
    input_set = artifact.get("input_set")
    if not isinstance(input_set, dict) or any(
        input_set.get(field) is not False
        for field in ("pilot_prompt_consumed", "confirmatory_prompt_consumed")
    ):
        errors.append("statistical smoke input boundary is invalid")
    records = artifact.get("records")
    if not isinstance(records, list) or len(records) != 80:
        errors.append("statistical smoke requires exactly 80 records")
        records = []
    if records:
        raw_records = []
        for record in records:
            if not isinstance(record, dict):
                errors.append("statistical smoke record is not an object")
                continue
            raw_records.append(
                {
                    key: value
                    for key, value in record.items()
                    if key not in {"floor_status", "factorized_nta"}
                }
            )
        try:
            expected_records, expected_denominator = statistics.materialize_pilot_nta(
                raw_records
            )
            expected_inference = statistics.build_pilot_inference(
                expected_records,
                expected_denominator,
                derivation_code_sha256=artifact.get("statistics_code_sha256"),
                numpy_version=artifact.get("numpy_version"),
            )
        except (statistics.Stage2bStatisticsError, TypeError, ValueError) as exc:
            errors.append(f"statistical recomputation failed: {exc}")
        else:
            if records != expected_records:
                errors.append("statistical records disagree with recomputation")
            if artifact.get("denominator_derivation") != expected_denominator:
                errors.append("denominator derivation disagrees with recomputation")
            if artifact.get("inference") != expected_inference:
                errors.append("inference disagrees with recomputation")
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


def _same_number(observed: Any, expected: Any) -> bool:
    return (
        isinstance(observed, (int, float))
        and isinstance(expected, (int, float))
        and math.isclose(float(observed), float(expected), rel_tol=1e-9, abs_tol=1e-9)
    )


def _compare_tree(observed: Any, expected: Any, label: str, errors: list[str]) -> None:
    if isinstance(expected, dict):
        if not isinstance(observed, dict) or set(observed) != set(expected):
            errors.append(f"{label} has incomplete keys")
            return
        for key in expected:
            _compare_tree(observed[key], expected[key], f"{label}.{key}", errors)
        return
    if not _same_number(observed, expected):
        errors.append(f"{label} disagrees with recomputed value")


def validate_synthetic_smoke(path: Path) -> tuple[dict[str, Any], list[str]]:
    """Recompute the complete compact 8x8, dual-floor synthetic artifact."""
    import numpy as np

    errors: list[str] = []
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    try:
        artifact = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"path": str(path), "sha256": digest, "valid": False}, [str(exc)]
    if artifact.get("schema") != SCHEMA:
        errors.append(f"schema is {artifact.get('schema')!r}, expected {SCHEMA!r}")
    input_set = artifact.get("input_set")
    if not isinstance(input_set, dict):
        errors.append("input_set must be an object")
    else:
        if input_set.get("real_manifest_overlap_count") != 0:
            errors.append("synthetic input overlaps the real manifest")
        for field in ("pilot_prompt_consumed", "confirmatory_prompt_consumed"):
            if input_set.get(field) is not False:
                errors.append(f"input_set.{field} must be false")
    records = artifact.get("records")
    if not isinstance(records, list) or len(records) != 16:
        errors.append("records must contain four prompts at each of four layers")
        records = []

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"record {index} is not an object")
            continue
        inputs = record.get("inputs")
        donor_assignments = record.get("donor_assignments")
        map_draws = record.get("map_draws")
        if not isinstance(inputs, dict):
            errors.append(f"record {index} inputs are missing")
            continue
        if not isinstance(donor_assignments, list) or len(donor_assignments) != 8:
            errors.append(f"record {index} requires exactly eight donor assignments")
            continue
        if not isinstance(map_draws, list) or len(map_draws) != 8:
            errors.append(f"record {index} requires exactly eight map draws")
            continue
        donor_ids = [item.get("donor_assignment_id") for item in donor_assignments]
        map_ids = [item.get("map_draw_id") for item in map_draws]
        if len(set(donor_ids)) != 8:
            errors.append(f"record {index} donor assignment IDs are not unique")
            continue
        if len(set(map_ids)) != 8:
            errors.append(f"record {index} map draw IDs are not unique")
            continue

        fitted_map = np.asarray(inputs.get("fitted_map"), dtype=np.float32)
        correct = np.asarray(inputs.get("correct_residual"), dtype=np.float32)
        stored_maps = inputs.get("broken_maps")
        stored_wrong = inputs.get("wrong_residuals")
        if not isinstance(stored_maps, dict) or not isinstance(stored_wrong, dict):
            errors.append(f"record {index} factorized inputs are malformed")
            continue
        recomputed_maps = {}
        for item in map_draws:
            map_id, seed = item.get("map_draw_id"), item.get("seed")
            if not isinstance(map_id, str) or not isinstance(seed, int):
                errors.append(f"record {index} map provenance is malformed")
                continue
            broken = endpoint.build_fit_broken_map(fitted_map, seed)
            recomputed_maps[map_id] = broken
            if item.get("sha256") != _json_digest(broken.tolist()):
                errors.append(f"record {index} map hash {map_id} disagrees")
            expected_spectrum = endpoint.singular_spectrum_evidence(fitted_map, broken)
            if item.get("spectrum_check") != expected_spectrum:
                errors.append(f"record {index} map spectrum {map_id} disagrees")
            if map_id not in stored_maps or not np.allclose(
                broken, stored_maps[map_id]
            ):
                errors.append(f"record {index} stored map {map_id} disagrees")
        wrong_residuals = {}
        for item in donor_assignments:
            donor_id = item.get("donor_assignment_id")
            if not isinstance(donor_id, str) or donor_id not in stored_wrong:
                errors.append(f"record {index} donor provenance is malformed")
                continue
            wrong = np.asarray(stored_wrong[donor_id], dtype=np.float32)
            wrong_residuals[donor_id] = wrong
            if item.get("source_prompt_sha256") == record.get("prompt_sha256"):
                errors.append(f"record {index} reused its own activation")
            if item.get("residual_sha256") != _json_digest(wrong.tolist()):
                errors.append(f"record {index} donor hash {donor_id} disagrees")
        if len(recomputed_maps) != 8 or len(wrong_residuals) != 8:
            continue

        vectors = {
            "correct_act_fitted_map": endpoint.transport_with(correct, fitted_map),
            "correct_act_broken_map": {
                map_id: endpoint.transport_with(correct, broken)
                for map_id, broken in recomputed_maps.items()
            },
            "wrong_act_fitted_map": {
                donor_id: endpoint.transport_with(wrong, fitted_map)
                for donor_id, wrong in wrong_residuals.items()
            },
            "wrong_act_broken_map": {
                donor_id: {
                    map_id: endpoint.transport_with(wrong, broken)
                    for map_id, broken in recomputed_maps.items()
                }
                for donor_id, wrong in wrong_residuals.items()
            },
        }
        expected_scores = _map_factorized(
            vectors, lambda vector: _score_from_vector(vector)[2]
        )
        recorded_scores = record.get("factorized_scores")
        try:
            endpoint.materialize_crossed_factorials(recorded_scores)
        except (AttributeError, TypeError, ValueError) as exc:
            errors.append(f"record {index} factorized scores: {exc}")
            continue
        _compare_tree(
            recorded_scores, expected_scores, f"record {index} factorized score", errors
        )

        target_id = record.get("target_id")
        prompt_logits = inputs.get("prompt_logits")
        layer0_logits = inputs.get("layer0_logits")
        output_logits = inputs.get("output_logits")
        if not isinstance(target_id, int) or not all(
            isinstance(value, list)
            for value in (prompt_logits, layer0_logits, output_logits)
        ):
            errors.append(f"record {index} floor inputs are malformed")
            continue
        floor_scores = {
            "input_embedding_decoded": endpoint.rank_score(
                endpoint.target_rank1(prompt_logits, target_id), len(prompt_logits)
            ),
            "layer0_residual_decoded": endpoint.rank_score(
                endpoint.target_rank1(layer0_logits, target_id), len(layer0_logits)
            ),
            "output_decoded": endpoint.rank_score(
                endpoint.target_rank1(output_logits, target_id), len(output_logits)
            ),
        }
        _compare_tree(
            record.get("floor_scores"),
            floor_scores,
            f"record {index} floor score",
            errors,
        )
        primary_floor_score = floor_scores["input_embedding_decoded"]
        sensitivity_floor_score = floor_scores["layer0_residual_decoded"]
        output_floor_score = floor_scores["output_decoded"]
        primary = _map_factorized(
            expected_scores,
            lambda score, floor=primary_floor_score, ceiling=output_floor_score: (
                endpoint.nta(
                    score,
                    floor,
                    ceiling,
                    MIN_DENOMINATOR,
                )
            ),
        )
        sensitivity = _map_factorized(
            expected_scores,
            lambda score, floor=sensitivity_floor_score, ceiling=output_floor_score: (
                endpoint.nta(
                    score,
                    floor,
                    ceiling,
                    MIN_DENOMINATOR,
                )
            ),
        )

        def subtract_tree(left: Any, right: Any) -> Any:
            if isinstance(left, dict):
                return {key: subtract_tree(left[key], right[key]) for key in left}
            return right - left

        expected_nta = {
            "input_embedding_decoded": primary,
            "layer0_residual_decoded": sensitivity,
            "sensitivity_minus_primary": subtract_tree(primary, sensitivity),
        }
        recorded_nta = record.get("factorized_nta")
        _compare_tree(
            recorded_nta,
            expected_nta,
            f"record {index} factorized NTA",
            errors,
        )
        if isinstance(recorded_nta, dict):
            for floor in ("input_embedding_decoded", "layer0_residual_decoded"):
                try:
                    crossed = endpoint.materialize_crossed_factorials(
                        recorded_nta[floor]
                    )
                except (KeyError, TypeError, ValueError) as exc:
                    errors.append(f"record {index} {floor}: {exc}")
                    continue
                if crossed["logical_cell_count"] != 64:
                    errors.append(
                        f"record {index} {floor} does not reconstruct 64 cells"
                    )

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
