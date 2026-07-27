#!/usr/bin/env python3
"""Validate a downloaded sparse J-space observation artifact.

Uses only the Python standard library. It validates provenance/retention structure,
content addressing, and the bounded observation contract without interpreting the
scientific meaning of token readouts.

Two schema families are auto-detected from the artifact's ``schema`` field:

* ``jspace-observation-smoke-test/*`` (and any non-discrimination schema): the
  original Stage 1 smoke-test contract, validated exactly as before.
* ``jspace-observation-discrimination/*``: the Stage 2 discrimination contract.
  ``artifact_type`` selects the per-prompt or aggregate sub-schema. Per-prompt
  discrimination artifacts remain a structural superset of the smoke-test
  contract; aggregate artifacts carry the cross-prompt statistics, the stimulus
  manifest digest, the preregistered thresholds, and the run decision.

CLI shape is unchanged: ``validate_observation.py <file> [--expected-sha256 X]``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

DISCRIMINATION_SCHEMA_PREFIX = "jspace-observation-discrimination"


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def nested(mapping: dict[str, Any], *keys: str) -> Any:
    value: Any = mapping
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def _validate_provenance_blocks(artifact: dict[str, Any], errors: list[str]) -> None:
    """Shared model/lens/instrumentation/runtime block checks."""
    for section, fields in {
        "model": ("repo_id", "revision", "n_layers", "d_model"),
        "lens": (
            "repo_id",
            "revision",
            "filename",
            "sha256",
            "source_layers",
            "d_model",
        ),
        "instrumentation": ("repo", "commit"),
        "runtime": (
            "python",
            "torch",
            "cuda_runtime",
            "gpu_name",
            "gpu_total_vram_gib",
        ),
    }.items():
        value = artifact.get(section)
        require(isinstance(value, dict), f"{section} must be an object", errors)
        if isinstance(value, dict):
            absent = [field for field in fields if field not in value]
            require(not absent, f"{section} missing fields: {absent}", errors)

    lens_hash = nested(artifact, "lens", "sha256")
    require(
        isinstance(lens_hash, str) and len(lens_hash) == 64,
        "lens.sha256 must be a 64-character digest",
        errors,
    )


def _validate_retention(artifact: dict[str, Any], errors: list[str]) -> None:
    for field in (
        "raw_activations_persisted",
        "full_logits_persisted",
        "raw_prompt_persisted",
    ):
        require(
            nested(artifact, "retention", field) is False,
            f"retention.{field} must be false",
            errors,
        )


def _validate_scope_evidence(artifact: dict[str, Any], errors: list[str]) -> None:
    require(
        artifact.get("evidence_class") == "direct_runtime_measurement",
        "evidence_class must be direct_runtime_measurement",
        errors,
    )
    require(
        artifact.get("scope") == "open_loop_observation_only",
        "scope must be open_loop_observation_only",
        errors,
    )
    require(
        isinstance(artifact.get("schema"), str) and bool(artifact.get("schema")),
        "schema must be a non-empty string",
        errors,
    )
    require(
        isinstance(artifact.get("run_id"), str) and bool(artifact.get("run_id")),
        "run_id must be a non-empty string",
        errors,
    )


def _validate_input_block(artifact: dict[str, Any], errors: list[str]) -> None:
    require(
        nested(artifact, "input", "raw_prompt_persisted") is False,
        "input.raw_prompt_persisted must be false",
        errors,
    )
    require(
        isinstance(nested(artifact, "input", "sha256"), str)
        and len(nested(artifact, "input", "sha256")) == 64,
        "input.sha256 must be a 64-character digest",
        errors,
    )


def _validate_measurement_readouts(artifact: dict[str, Any], errors: list[str]) -> None:
    """Jacobian + logit-lens readouts keyed by selected_layers (shared contract)."""
    selected_layers = nested(artifact, "measurement", "selected_layers")
    jacobian = nested(artifact, "measurement", "jacobian_lens")
    baseline = nested(artifact, "measurement", "logit_lens_baseline")
    repeatability = nested(artifact, "measurement", "repeatability_same_runtime")
    require(
        isinstance(selected_layers, list) and selected_layers,
        "measurement.selected_layers must be a non-empty list",
        errors,
    )
    require(
        isinstance(jacobian, dict) and jacobian,
        "measurement.jacobian_lens must be non-empty",
        errors,
    )
    require(
        isinstance(baseline, dict) and baseline,
        "measurement.logit_lens_baseline must be non-empty",
        errors,
    )
    require(
        isinstance(repeatability, dict),
        "repeatability_same_runtime must be an object",
        errors,
    )
    if (
        isinstance(selected_layers, list)
        and isinstance(jacobian, dict)
        and isinstance(baseline, dict)
    ):
        expected_layer_keys = {str(layer) for layer in selected_layers}
        require(
            set(jacobian) == expected_layer_keys,
            "Jacobian readout layer keys must equal selected_layers",
            errors,
        )
        require(
            set(baseline) == expected_layer_keys,
            "baseline layer keys must equal selected_layers",
            errors,
        )
    return selected_layers


def validate_smoke(
    artifact: dict[str, Any], path: Path, digest: str, errors: list[str]
) -> Any:
    """Original Stage 1 smoke-test contract. Behavior preserved exactly."""
    required_top_level = {
        "created_at_utc",
        "evidence_class",
        "input",
        "instrumentation",
        "lens",
        "measurement",
        "model",
        "retention",
        "run_id",
        "runtime",
        "schema",
        "scope",
    }
    missing = sorted(required_top_level - artifact.keys())
    require(not missing, f"missing top-level fields: {missing}", errors)

    _validate_scope_evidence(artifact, errors)
    _validate_retention(artifact, errors)
    _validate_input_block(artifact, errors)
    _validate_provenance_blocks(artifact, errors)
    selected_layers = _validate_measurement_readouts(artifact, errors)

    if path.name.startswith("jspace_observation_") and path.suffix == ".json":
        prefix = path.stem.removeprefix("jspace_observation_")
        require(
            bool(prefix) and digest.startswith(prefix),
            f"filename digest prefix {prefix!r} does not match SHA-256 {digest}",
            errors,
        )
    return selected_layers


def validate_discrimination_per_prompt(
    artifact: dict[str, Any], path: Path, digest: str, errors: list[str]
) -> Any:
    """Stage 2 per-prompt discrimination artifact (superset of the smoke contract)."""
    required_top_level = {
        "artifact_type",
        "created_at_utc",
        "discrimination",
        "evidence_class",
        "input",
        "instrumentation",
        "lens",
        "measurement",
        "model",
        "retention",
        "run_id",
        "runtime",
        "schema",
        "scope",
        "stimulus",
    }
    missing = sorted(required_top_level - artifact.keys())
    require(not missing, f"missing top-level fields: {missing}", errors)

    _validate_scope_evidence(artifact, errors)
    _validate_retention(artifact, errors)
    _validate_input_block(artifact, errors)
    _validate_provenance_blocks(artifact, errors)
    selected_layers = _validate_measurement_readouts(artifact, errors)

    # Discrimination-specific baselines keyed by selected_layers.
    expected_layer_keys = (
        {str(layer) for layer in selected_layers}
        if isinstance(selected_layers, list)
        else set()
    )
    for baseline_name in (
        "output_baseline",
        "prompt_only_baseline",
        "random_vector_baseline",
        "non_jspace_baseline",
    ):
        block = nested(artifact, "measurement", baseline_name)
        require(
            isinstance(block, dict) and bool(block),
            f"measurement.{baseline_name} must be a non-empty object",
            errors,
        )
        if isinstance(block, dict) and expected_layer_keys:
            require(
                set(block) == expected_layer_keys,
                f"measurement.{baseline_name} layer keys must equal selected_layers",
                errors,
            )

    per_locus = nested(artifact, "discrimination", "per_locus")
    require(
        isinstance(per_locus, dict) and bool(per_locus),
        "discrimination.per_locus must be a non-empty object",
        errors,
    )
    if isinstance(per_locus, dict) and expected_layer_keys:
        require(
            set(per_locus) == expected_layer_keys,
            "discrimination.per_locus layer keys must equal selected_layers",
            errors,
        )
    require(
        isinstance(nested(artifact, "discrimination", "readout_pairs"), list)
        and bool(nested(artifact, "discrimination", "readout_pairs")),
        "discrimination.readout_pairs must be a non-empty list",
        errors,
    )

    stimulus_manifest_sha = nested(artifact, "stimulus", "stimulus_manifest_sha256")
    require(
        isinstance(stimulus_manifest_sha, str) and len(stimulus_manifest_sha) == 64,
        "stimulus.stimulus_manifest_sha256 must be a 64-character digest",
        errors,
    )
    require(
        isinstance(nested(artifact, "stimulus", "category"), str)
        and bool(nested(artifact, "stimulus", "category")),
        "stimulus.category must be a non-empty string",
        errors,
    )

    if path.name.startswith("jspace_observation_") and path.suffix == ".json":
        prefix = path.stem.removeprefix("jspace_observation_")
        require(
            bool(prefix) and digest.startswith(prefix),
            f"filename digest prefix {prefix!r} does not match SHA-256 {digest}",
            errors,
        )
    return selected_layers


def validate_discrimination_aggregate(
    artifact: dict[str, Any], path: Path, digest: str, errors: list[str]
) -> None:
    """Stage 2 aggregate run artifact."""
    required_top_level = {
        "aggregate",
        "artifact_type",
        "created_at_utc",
        "decision",
        "evidence_class",
        "instrumentation",
        "lens",
        "model",
        "retention",
        "run_id",
        "runtime",
        "schema",
        "scope",
        "stimulus_manifest",
        "thresholds",
    }
    missing = sorted(required_top_level - artifact.keys())
    require(not missing, f"missing top-level fields: {missing}", errors)

    _validate_scope_evidence(artifact, errors)
    _validate_retention(artifact, errors)
    _validate_provenance_blocks(artifact, errors)

    manifest_sha = nested(artifact, "stimulus_manifest", "sha256")
    require(
        isinstance(manifest_sha, str) and len(manifest_sha) == 64,
        "stimulus_manifest.sha256 must be a 64-character digest",
        errors,
    )
    require(
        isinstance(nested(artifact, "stimulus_manifest", "n_prompts"), int),
        "stimulus_manifest.n_prompts must be an integer",
        errors,
    )
    require(
        isinstance(artifact.get("thresholds"), dict)
        and bool(artifact.get("thresholds")),
        "thresholds must be a non-empty object",
        errors,
    )
    require(
        isinstance(artifact.get("aggregate"), dict) and bool(artifact.get("aggregate")),
        "aggregate must be a non-empty object",
        errors,
    )
    require(
        isinstance(nested(artifact, "aggregate", "n_prompts"), int),
        "aggregate.n_prompts must be an integer",
        errors,
    )
    decision = nested(artifact, "decision", "result")
    require(
        decision in {"pass", "ambiguity", "fail", "kill", "not_executed"},
        "decision.result must be one of pass/ambiguity/fail/kill/not_executed",
        errors,
    )

    if path.name.startswith("jspace_discrimination_") and path.suffix == ".json":
        prefix = path.stem.removeprefix("jspace_discrimination_")
        require(
            bool(prefix) and digest.startswith(prefix),
            f"filename digest prefix {prefix!r} does not match SHA-256 {digest}",
            errors,
        )


def validate(
    path: Path, expected_sha256: str | None
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    require(path.is_file(), f"artifact is not a file: {path}", errors)
    if errors:
        return {}, errors

    size = path.stat().st_size
    digest = sha256_file(path)

    try:
        artifact = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"path": str(path), "size_bytes": size, "sha256": digest}, [
            f"invalid UTF-8 JSON: {type(exc).__name__}: {exc}"
        ]

    require(isinstance(artifact, dict), "top-level JSON must be an object", errors)
    if not isinstance(artifact, dict):
        return {"path": str(path), "size_bytes": size, "sha256": digest}, errors

    schema = artifact.get("schema")
    schema_str = schema if isinstance(schema, str) else ""
    is_discrimination = schema_str.startswith(DISCRIMINATION_SCHEMA_PREFIX)
    artifact_type = artifact.get("artifact_type")

    selected_layers: Any = None
    if is_discrimination and artifact_type == "aggregate":
        validate_discrimination_aggregate(artifact, path, digest, errors)
        detected = "discrimination_aggregate"
    elif is_discrimination:
        # per_prompt is the default discrimination sub-schema.
        if artifact_type not in (None, "per_prompt"):
            errors.append(f"unknown discrimination artifact_type: {artifact_type!r}")
        selected_layers = validate_discrimination_per_prompt(
            artifact, path, digest, errors
        )
        detected = "discrimination_per_prompt"
    else:
        selected_layers = validate_smoke(artifact, path, digest, errors)
        detected = "smoke_test"

    if expected_sha256 is not None:
        require(
            digest == expected_sha256.lower(),
            f"SHA-256 mismatch: measured {digest}, expected {expected_sha256.lower()}",
            errors,
        )

    summary = {
        "path": str(path.resolve()),
        "size_bytes": size,
        "sha256": digest,
        "schema": artifact.get("schema"),
        "detected_contract": detected,
        "artifact_type": artifact_type,
        "run_id": artifact.get("run_id"),
        "scope": artifact.get("scope"),
        "model": nested(artifact, "model", "repo_id"),
        "model_revision": nested(artifact, "model", "revision"),
        "lens": nested(artifact, "lens", "repo_id"),
        "lens_revision": nested(artifact, "lens", "revision"),
        "lens_sha256": nested(artifact, "lens", "sha256"),
        "gpu": nested(artifact, "runtime", "gpu_name"),
        "gpu_total_vram_gib": nested(artifact, "runtime", "gpu_total_vram_gib"),
        "selected_layers": selected_layers,
        "same_topk_token_ids": nested(
            artifact, "measurement", "repeatability_same_runtime", "same_topk_token_ids"
        ),
        "decision": nested(artifact, "decision", "result"),
        "stimulus_manifest_sha256": (
            nested(artifact, "stimulus_manifest", "sha256")
            or nested(artifact, "stimulus", "stimulus_manifest_sha256")
        ),
        "retention": artifact.get("retention"),
        "valid": not errors,
    }
    return summary, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "artifact", type=Path, help="Downloaded J-space observation JSON"
    )
    parser.add_argument("--expected-sha256", help="Runtime-reported SHA-256 to require")
    args = parser.parse_args()

    summary, errors = validate(args.artifact, args.expected_sha256)
    result = {"summary": summary, "errors": errors}
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
