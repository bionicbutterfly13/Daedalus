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
import math
import sys
from pathlib import Path
from typing import Any

from stage2b_decision import compose_confirmatory_decision, derive_gate_outcome

DISCRIMINATION_SCHEMA_PREFIX = "jspace-observation-discrimination"
STAGE2B_SCHEMA_PREFIX = "jspace-observation-stage2b"


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


def validate_stage2b_aggregate(
    artifact: dict[str, Any], path: Path, digest: str, errors: list[str]
) -> None:
    """Stage 2b aggregate: every decision must be recomputable from the artifact.

    The test here is deliberately not "does it parse". It is SC-003: can a reader
    reach each gate's outcome using only fields in this file, with no appeal to
    the notebook? Stage 2's artifacts could not support that, which is why its
    2026-07-26 audit had to read notebook source to establish what the gates
    actually did.
    """
    _validate_provenance_blocks(artifact, errors)
    _validate_retention(artifact, errors)
    _validate_scope_evidence(artifact, errors)

    registry = artifact.get("registry")
    require(isinstance(registry, dict), "aggregate must carry a registry block", errors)
    if isinstance(registry, dict):
        entries = registry.get("entries")
        require(
            isinstance(entries, list) and bool(entries),
            "registry.entries must be a non-empty list",
            errors,
        )
        for entry in entries if isinstance(entries, list) else []:
            name = entry.get("name") if isinstance(entry, dict) else None
            consumers = entry.get("consumed_by") if isinstance(entry, dict) else None
            require(
                isinstance(consumers, list) and bool(consumers),
                f"registry entry {name!r} records no consumer; a declared constant "
                "with no consumer is what the registry exists to catch",
                errors,
            )

    disjointness = artifact.get("disjointness")
    require(isinstance(disjointness, dict), "aggregate must carry disjointness", errors)
    if isinstance(disjointness, dict):
        require(
            disjointness.get("checked") is True,
            "disjointness.checked must be true; FR-011 requires the held-out "
            "property be checked, not documented",
            errors,
        )
        require(
            disjointness.get("overlap_count") == 0,
            f"disjointness.overlap_count is {disjointness.get('overlap_count')!r}, "
            "must be 0",
            errors,
        )
        require(
            disjointness.get("anchor_present") is False,
            "the Stage 1 anchor must be outside the analysis sample",
            errors,
        )

    run_mode = artifact.get("run_mode")
    require(
        run_mode in {"pilot", "confirmatory"},
        f"aggregate run_mode must be pilot or confirmatory, got {run_mode!r}",
        errors,
    )
    if run_mode == "pilot":
        authorization = artifact.get("authorization")
        require(
            isinstance(authorization, dict)
            and authorization.get("pilot_authorized") is True,
            "pilot authorization.pilot_authorized must be true",
            errors,
        )
        partition = artifact.get("partition")
        require(isinstance(partition, dict), "pilot must carry partition", errors)
        if isinstance(partition, dict):
            require(
                partition.get("n_prompts") == 20,
                f"pilot partition.n_prompts must be 20, got {partition.get('n_prompts')!r}",
                errors,
            )
            subset_digest = partition.get("pilot_subset_sha256")
            require(
                isinstance(subset_digest, str) and len(subset_digest) == 64,
                "pilot partition.pilot_subset_sha256 must be a 64-character digest",
                errors,
            )
            require(
                partition.get("holdout_prompt_count") == 180,
                "pilot partition.holdout_prompt_count must be 180",
                errors,
            )
            require(
                partition.get("holdout_accessed") is False,
                "pilot partition.holdout_accessed must be false",
                errors,
            )
        estimates = artifact.get("threshold_estimates")
        expected_estimates = {
            "SPEC_MIN_EFFECT",
            "NTA_MIN_DENOMINATOR",
            "INTERACTION_MIN_EFFECT",
        }
        require(
            isinstance(estimates, dict) and set(estimates) == expected_estimates,
            f"pilot threshold estimates must be exactly {sorted(expected_estimates)}",
            errors,
        )
        if isinstance(estimates, dict):
            for name in expected_estimates:
                estimate = estimates.get(name)
                value = estimate.get("estimate") if isinstance(estimate, dict) else None
                method = estimate.get("method") if isinstance(estimate, dict) else None
                finite = (
                    isinstance(value, (int, float))
                    and not isinstance(value, bool)
                    and math.isfinite(value)
                )
                require(
                    finite and isinstance(method, str) and bool(method),
                    f"pilot threshold estimate {name!r} needs a finite estimate "
                    "and non-empty method",
                    errors,
                )
        require(
            "gates" not in artifact and "decision" not in artifact,
            "pilot must not carry confirmatory gates or a decision",
            errors,
        )
        require(
            isinstance(artifact.get("descriptive"), dict),
            "descriptive must be a sibling block of threshold_estimates",
            errors,
        )
        return

    gates = artifact.get("gates")
    require(isinstance(gates, list) and bool(gates), "aggregate needs gates", errors)
    for gate in gates if isinstance(gates, list) else []:
        if not isinstance(gate, dict):
            errors.append("each gate must be an object")
            continue
        name = gate.get("name")
        outcome = gate.get("outcome")
        require(
            outcome in {"pass", "fail", "undefined"},
            f"gate {name!r} has outcome {outcome!r}",
            errors,
        )
        interval = gate.get("interval")
        require(
            isinstance(interval, dict), f"gate {name!r} records no interval", errors
        )
        if isinstance(interval, dict):
            bounds = (interval.get("low"), interval.get("high"))
            finite = all(
                isinstance(b, (int, float)) and math.isfinite(b) for b in bounds
            )
            # The rule that keeps a failed computation from being read as a
            # measured null. An absent interval and an interval containing zero
            # are different results.
            require(
                finite or outcome == "undefined",
                f"gate {name!r} has a non-finite interval but outcome {outcome!r}; "
                "a non-finite bound must be reported as undefined, never fail",
                errors,
            )
            if str(interval.get("method", "")).lower() == "bca":
                require(
                    isinstance(gate.get("interval_crosscheck"), dict),
                    f"gate {name!r} gates on BCa with no percentile cross-check, "
                    "so a degenerate BCa cannot be detected after the fact",
                    errors,
                )
        # Recomputability: the values and rule the outcome depends on must be present.
        for field in ("statistic", "comparison", "n_clusters", "exclusions"):
            require(
                field in gate,
                f"gate {name!r} omits {field!r}, so its outcome cannot be "
                "recomputed from this artifact alone (SC-003)",
                errors,
            )
        if isinstance(interval, dict) and "comparison" in gate and "statistic" in gate:
            comparison = gate.get("comparison")
            if not isinstance(comparison, str):
                errors.append(f"gate {name!r} comparison must be a string")
            else:
                try:
                    recomputed = derive_gate_outcome(
                        statistic=gate.get("statistic"),
                        interval=interval,
                        declared_value=gate.get("declared_value"),
                        comparison=comparison,
                    )
                except (TypeError, ValueError) as exc:
                    errors.append(f"gate {name!r} comparison cannot be recomputed: {exc}")
                else:
                    require(
                        outcome == recomputed,
                        f"gate {name!r} records outcome {outcome!r}, but its values and "
                        f"comparison recomputed outcome {recomputed!r}",
                        errors,
                    )

    required_gate_names = {
        "reproduction",
        "h1_specificity",
        "h1_interval",
        "h1_interaction",
        "h2_overlap",
        "h2_target",
        "sanity_floor",
    }
    gate_outcomes: dict[str, str] = {}
    if isinstance(gates, list):
        for gate in gates:
            if not isinstance(gate, dict):
                continue
            gate_name = gate.get("name")
            gate_outcome = gate.get("outcome")
            if isinstance(gate_name, str) and isinstance(gate_outcome, str):
                gate_outcomes[gate_name] = gate_outcome
    require(
        set(gate_outcomes) == required_gate_names,
        f"aggregate required gates are {sorted(required_gate_names)}, got "
        f"{sorted(gate_outcomes)}",
        errors,
    )

    preflight = artifact.get("preflight")
    require(
        isinstance(preflight, dict),
        "aggregate must carry preflight kill inputs",
        errors,
    )
    decision = artifact.get("decision")
    require(isinstance(decision, dict), "aggregate must carry a decision", errors)
    if isinstance(decision, dict):
        require(
            decision.get("result") in {"pass", "ambiguity", "fail", "kill"},
            f"decision.result is {decision.get('result')!r}",
            errors,
        )
    if (
        isinstance(preflight, dict)
        and isinstance(decision, dict)
        and set(gate_outcomes) == required_gate_names
    ):
        identities = preflight.get("pinned_identities_matched")
        capacity = preflight.get("capacity_ok")
        require(
            isinstance(identities, bool) and isinstance(capacity, bool),
            "preflight pinned_identities_matched and capacity_ok must be booleans",
            errors,
        )
        if isinstance(identities, bool) and isinstance(capacity, bool):
            recomputed_decision = compose_confirmatory_decision(
                gate_outcomes,
                pinned_identities_matched=identities,
                capacity_ok=capacity,
            )
            require(
                decision.get("result") == recomputed_decision["result"],
                f"recorded decision {decision.get('result')!r} disagrees with "
                f"recomputed decision {recomputed_decision['result']!r}",
                errors,
            )

    require(
        isinstance(artifact.get("descriptive"), dict),
        "descriptive must be a sibling block of gates, so a reported quantity "
        "cannot be mistaken for a decision input",
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
    is_stage2b = schema_str.startswith(STAGE2B_SCHEMA_PREFIX)
    artifact_type = artifact.get("artifact_type")

    selected_layers: Any = None
    if is_stage2b and artifact_type == "aggregate":
        validate_stage2b_aggregate(artifact, path, digest, errors)
        detected = "stage2b_aggregate"
    elif is_stage2b:
        if artifact_type not in (None, "per_prompt"):
            errors.append(f"unknown stage2b artifact_type: {artifact_type!r}")
        selected_layers = validate_discrimination_per_prompt(
            artifact, path, digest, errors
        )
        detected = "stage2b_per_prompt"
    elif is_discrimination and artifact_type == "aggregate":
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
