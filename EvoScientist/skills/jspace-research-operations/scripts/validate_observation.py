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

Stage 2b validation recomputes the ratified pilot statistics and threshold
derivation from retained scores. A pilot artifact cannot contain a scientific
gate or decision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

import stage2b_statistics as stage2b_statistics_module
from stage2b_endpoint import (
    SINGULAR_SPECTRUM_ATOL,
    SINGULAR_SPECTRUM_RTOL,
    NTAExcluded,
    dual_floor_nta,
    materialize_crossed_factorials,
    select_wrong_activation_source,
    target_decision_sha256,
)
from stage2b_statistics import (
    Stage2bStatisticsError,
    build_pilot_inference,
    derive_crossing_seed_vectors,
    materialize_pilot_nta,
)

DISCRIMINATION_SCHEMA_PREFIX = "jspace-observation-discrimination"
STAGE2B_SCHEMA_PREFIX = "jspace-observation-stage2b"
STAGE2B_SCHEMA = "jspace-observation-stage2b/v1"

STAGE2B_MODEL = {
    "repo_id": "Qwen/Qwen3-1.7B",
    "revision": "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e",
    "n_layers": 28,
    "d_model": 2048,
}
STAGE2B_LENS = {
    "repo_id": "neuronpedia/jacobian-lens",
    "revision": "a4114d7752d11eb546e6cf372213d7e75526d3a1",
    "filename": "qwen3-1.7b/jlens/Salesforce-wikitext/Qwen3-1.7B_jacobian_lens.pt",
    "sha256": "6fcc79011bd921ffd87612255e2e99950a124fa519470ee44ebaf161c39be9d6",
    "d_model": 2048,
}
STAGE2B_INSTRUMENTATION = {
    "repo": "https://github.com/anthropics/jacobian-lens.git",
    "commit": "581d398613e5602a5af361e1c34d3a92ea82ba8e",
}
STAGE2B_RUNTIME_VERSIONS = {
    "transformers": "5.5.4",
    "huggingface_hub": "1.24.0",
    "numpy": "2.5.1",
    "scipy": "1.18.0",
    "safetensors": "0.8.0",
    "accelerate": "1.14.0",
    "torch": "2.13.0",
}
STAGE2B_RUNTIME_INSTALL_SCHEMA = "stage2b-colab-runtime-install/v2"
STAGE2B_RUNTIME_REMOVE_PACKAGES = ["torchvision"]
STAGE2B_RUNTIME_INSTALL_REQUIREMENTS = [
    (
        "git+https://github.com/anthropics/jacobian-lens.git@"
        "581d398613e5602a5af361e1c34d3a92ea82ba8e"
    ),
    "transformers==5.5.4",
    "huggingface_hub==1.24.0",
    "safetensors==0.8.0",
    "scipy==1.18.0",
    "numpy==2.5.1",
    "accelerate==1.14.0",
    "torch==2.13.0",
]
STAGE2B_RUNTIME_INSTALL_SPEC_SHA256 = hashlib.sha256(
    (
        json.dumps(
            {
                "schema": STAGE2B_RUNTIME_INSTALL_SCHEMA,
                "remove_packages": STAGE2B_RUNTIME_REMOVE_PACKAGES,
                "requirements": STAGE2B_RUNTIME_INSTALL_REQUIREMENTS,
                "expected_runtime_versions": STAGE2B_RUNTIME_VERSIONS,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
).hexdigest()
STAGE2B_SELECTED_LAYERS = (6, 13, 20, 26)
STAGE2B_POSITIONS = (-2,)
STAGE2B_FLOORS = {
    "primary": "input_embedding_decoded",
    "sensitivity": "layer0_residual_decoded",
}
STAGE2B_CONTENT_HASH_METHOD = "dtype-shape-bytes-sha256-v1"
STAGE2B_SOURCE_MANIFEST_SHA256 = (
    "ba29c629c7b9601980b6c0bb9cd9730242d7cd6b7eacb1166c307837416d4bbf"
)
STAGE2B_PILOT_VIEW_SHA256 = (
    "5bef8316f72682a628fc1240bf6068a91aa7c8a330377206cbd9145434b797e4"
)
STAGE2B_SOURCE_PROMPTS = 200
STAGE2B_PILOT_PROMPTS = 20
STAGE2B_TARGET_RUNTIME_VERIFIER = (
    "validate_observation.verify_target_derivation_against_logits/v1"
)
STAGE2B_STATISTICS_SHA256 = hashlib.sha256(
    Path(stage2b_statistics_module.__file__).read_bytes()
).hexdigest()
_STAGE2B_INFERENCE_RECOMPUTATION_CACHE: dict[str, dict[str, Any]] = {}


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def verify_target_derivation_against_logits(
    output_logits: Any,
    target_id: int,
    target_derivation: dict[str, Any],
) -> list[str]:
    """Independently recompute target evidence from live full-vocabulary logits."""
    import numpy as np

    errors: list[str] = []
    logits = np.ascontiguousarray(np.asarray(output_logits))
    require(logits.ndim == 1, "runtime target logits must be one-dimensional", errors)
    require(
        str(logits.dtype) == "float32", "runtime target logits must be float32", errors
    )
    if logits.ndim != 1 or logits.size == 0:
        return errors

    max_logit = float(logits.max())
    tie_ids = np.flatnonzero(logits == max_logit).astype(int).tolist()
    metadata = f"{logits.dtype}:{logits.shape}:".encode("ascii")
    logits_sha256 = hashlib.sha256(metadata + logits.tobytes()).hexdigest()
    require(
        target_id == min(tie_ids),
        "runtime target_id is not the lowest-token model argmax",
        errors,
    )
    require(
        target_derivation.get("output_logits_sha256") == logits_sha256,
        "runtime output-logits bytes do not match target evidence",
        errors,
    )
    require(
        target_derivation.get("output_logits_dtype") == str(logits.dtype),
        "runtime output-logits dtype does not match target evidence",
        errors,
    )
    require(
        target_derivation.get("output_logits_shape") == list(logits.shape),
        "runtime output-logits shape does not match target evidence",
        errors,
    )
    require(
        target_derivation.get("max_logit") == max_logit,
        "runtime maximum logit does not match target evidence",
        errors,
    )
    require(
        target_derivation.get("argmax_tie_token_ids") == tie_ids,
        "runtime argmax tie set does not match target evidence",
        errors,
    )
    require(
        target_derivation.get("tie_break_rule") == "lowest_token_id",
        "runtime target tie-break rule is invalid",
        errors,
    )
    require(
        target_derivation.get("runtime_verifier_id") == STAGE2B_TARGET_RUNTIME_VERIFIER,
        "runtime target verifier identity is invalid",
        errors,
    )
    require(
        target_derivation.get("runtime_verified") is True,
        "runtime target evidence is not marked verified",
        errors,
    )
    expected_decision_sha256 = target_decision_sha256(target_id, target_derivation)
    require(
        target_derivation.get("target_decision_sha256") == expected_decision_sha256,
        "runtime target decision digest is invalid",
        errors,
    )
    return errors


def nested(mapping: dict[str, Any], *keys: str) -> Any:
    value: Any = mapping
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def _reject_unknown_fields(
    value: Any, allowed: set[str], label: str, errors: list[str]
) -> None:
    if not isinstance(value, dict):
        return
    unknown = sorted(set(value) - allowed)
    require(not unknown, f"{label} has unknown fields: {unknown}", errors)


def _validate_stage2b_schema_fields(
    artifact: dict[str, Any], errors: list[str]
) -> None:
    """Reject undeclared policy or data fields at every normative object level."""
    _reject_unknown_fields(
        artifact,
        {
            "artifact_type",
            "authorization",
            "constants",
            "created_at_utc",
            "denominator_derivation",
            "design",
            "descriptive",
            "disjointness",
            "evidence_class",
            "instrumentation",
            "inference",
            "lens",
            "model",
            "partition",
            "preflight",
            "registry",
            "retention",
            "run_id",
            "run_mode",
            "runtime",
            "schema",
            "scope",
            "stimulus_manifest",
        },
        "Stage 2b aggregate",
        errors,
    )
    object_fields = {
        "model": {"repo_id", "revision", "n_layers", "d_model"},
        "lens": {
            "repo_id",
            "revision",
            "filename",
            "sha256",
            "source_layers",
            "d_model",
        },
        "instrumentation": {"repo", "commit"},
        "runtime": {
            "python",
            "torch",
            "packages",
            "cuda_runtime",
            "gpu_name",
            "gpu_total_vram_gib",
            "install_schema",
            "install_spec_sha256",
            "fresh_process_after_install",
            "torchvision_state",
        },
        "retention": {
            "raw_activations_persisted",
            "full_logits_persisted",
            "raw_prompt_persisted",
        },
        "disjointness": {
            "checked",
            "stage2b_manifest_sha256",
            "overlap_count",
            "anchor_present",
        },
        "stimulus_manifest": {"sha256", "n_prompts"},
        "authorization": {
            "pilot_authorized",
            "pilot_protocol_ratified",
            "confirmatory_thresholds_ratified",
            "authorization_record_sha256",
            "authority",
            "authorized_at_utc",
            "instruction_sha256",
            "notebook_sha256",
            "code_bundle_sha256",
        },
        "preflight": {
            "pinned_identities_matched",
            "capacity_ok",
            "tensor_contracts_passed",
            "crossing_registry_checked",
        },
        "constants": {
            "min_denominator",
            "guard_quantile",
            "guard_quantile_method",
            "bootstrap_iterations",
            "bootstrap_ci_level",
            "bootstrap_quantile_method",
            "bootstrap_bit_generator",
        },
        "denominator_derivation": {
            "source_floor",
            "source_count",
            "source_denominators_sha256",
            "quantile",
            "quantile_method",
            "derived_value",
            "source_order",
        },
        "partition": {
            "n_prompts",
            "pilot_subset_sha256",
            "pilot_view_sha256",
            "pilot_prompt_ids",
            "pilot_prompt_sha256s",
            "holdout_prompt_count",
            "holdout_accessed",
        },
        "design": {
            "selected_layers",
            "positions",
            "top_k",
            "vocab_size",
            "model_n_layers",
            "primary_floor_id",
            "sensitivity_floor_id",
            "donor_assignment_count",
            "broken_map_draw_count",
            "unique_readouts_per_prompt_layer",
            "logical_crossings_per_prompt_layer",
            "content_hash_method",
        },
        "registry": {
            "entries",
            "gates_declared",
            "preflight_checks_declared",
            "endpoint_fns_declared",
        },
        "descriptive": {"records", "factorization"},
        "inference": {
            "records_sha256",
            "denominator_derivation",
            "coverage",
            "prompt_layer_effects",
            "layer_estimates",
            "rng",
            "pilot_measurement_sha256",
            "threshold_derivation",
        },
    }
    for field, allowed in object_fields.items():
        _reject_unknown_fields(artifact.get(field), allowed, field, errors)

    runtime_packages = nested(artifact, "runtime", "packages")
    _reject_unknown_fields(
        runtime_packages,
        set(STAGE2B_RUNTIME_VERSIONS),
        "runtime.packages",
        errors,
    )
    registry_entries = nested(artifact, "registry", "entries")
    if isinstance(registry_entries, list):
        for index, entry in enumerate(registry_entries):
            _reject_unknown_fields(
                entry,
                {"name", "kind", "declared_value", "status", "consumed_by"},
                f"registry entry {index}",
                errors,
            )

    descriptive = artifact.get("descriptive")
    _reject_unknown_fields(
        descriptive.get("factorization") if isinstance(descriptive, dict) else None,
        {
            "unique_readouts_per_prompt_layer",
            "logical_crossings_per_prompt_layer",
            "donor_assignment_count",
            "broken_map_draw_count",
        },
        "descriptive.factorization",
        errors,
    )
    records = descriptive.get("records") if isinstance(descriptive, dict) else None
    if not isinstance(records, list):
        return
    record_fields = {
        "category",
        "layer",
        "prompt_sha256",
        "target_id",
        "target_source",
        "target_derivation",
        "donor_assignments",
        "map_draws",
        "floor_scores",
        "factorized_scores",
        "factorized_nta",
        "floor_status",
    }
    target_fields = {
        "method",
        "output_logits_sha256",
        "output_logits_dtype",
        "output_logits_shape",
        "max_logit",
        "argmax_tie_token_ids",
        "tie_break_rule",
        "runtime_verifier_id",
        "runtime_verified",
        "target_decision_sha256",
    }
    donor_fields = {
        "donor_assignment_id",
        "seed_index",
        "seed_namespace",
        "seed_sha256",
        "seed",
        "bit_generator",
        "recipient_prompt_sha256",
        "source_prompt_sha256",
        "recipient_to_donor_sha256",
        "residual_sha256",
    }
    map_fields = {
        "map_draw_id",
        "seed_index",
        "seed_namespace",
        "seed_sha256",
        "seed",
        "bit_generator",
        "sha256",
        "spectrum_check",
    }
    spectrum_check_fields = {
        "schema",
        "method",
        "singular_value_count",
        "fitted_singular_values_sha256",
        "broken_singular_values_sha256",
        "rtol",
        "atol",
        "max_abs_diff",
        "max_normalized_error",
        "verified",
    }
    for record_index, record in enumerate(records):
        _reject_unknown_fields(
            record, record_fields, f"compact record {record_index}", errors
        )
        if not isinstance(record, dict):
            continue
        _reject_unknown_fields(
            record.get("target_derivation"),
            target_fields,
            f"compact record {record_index} target_derivation",
            errors,
        )
        donors = record.get("donor_assignments")
        if isinstance(donors, list):
            for donor_index, donor in enumerate(donors):
                _reject_unknown_fields(
                    donor,
                    donor_fields,
                    f"compact record {record_index} donor assignment {donor_index}",
                    errors,
                )
        draws = record.get("map_draws")
        if isinstance(draws, list):
            for draw_index, draw in enumerate(draws):
                _reject_unknown_fields(
                    draw,
                    map_fields,
                    f"compact record {record_index} map draw {draw_index}",
                    errors,
                )
                if isinstance(draw, dict):
                    _reject_unknown_fields(
                        draw.get("spectrum_check"),
                        spectrum_check_fields,
                        f"compact record {record_index} map draw {draw_index} "
                        "spectrum_check",
                        errors,
                    )
        statuses = record.get("floor_status")
        _reject_unknown_fields(
            statuses,
            {"input_embedding_decoded", "layer0_residual_decoded"},
            f"compact record {record_index} floor_status",
            errors,
        )
        if isinstance(statuses, dict):
            for floor, status in statuses.items():
                _reject_unknown_fields(
                    status,
                    {"denominator", "eligible", "exclusion_reason"},
                    f"compact record {record_index} floor_status.{floor}",
                    errors,
                )

    inference = artifact.get("inference")
    if not isinstance(inference, dict):
        return
    rng_fields = {
        "namespace",
        "sha256",
        "seed",
        "byte_order",
        "bit_generator",
        "numpy_version",
        "iterations",
        "weight_distribution",
    }
    _reject_unknown_fields(inference.get("rng"), rng_fields, "inference.rng", errors)
    coverage = inference.get("coverage")
    if isinstance(coverage, list):
        for index, entry in enumerate(coverage):
            _reject_unknown_fields(
                entry,
                {
                    "floor",
                    "layer",
                    "eligible_prompt_count",
                    "eligible_by_category",
                    "excluded_prompt_sha256",
                    "defined",
                    "reason",
                },
                f"inference.coverage {index}",
                errors,
            )
    prompt_effects = inference.get("prompt_layer_effects")
    if isinstance(prompt_effects, list):
        for index, entry in enumerate(prompt_effects):
            _reject_unknown_fields(
                entry,
                {
                    "prompt_sha256",
                    "category",
                    "layer",
                    "floor",
                    "eligible",
                    "exclusion_reason",
                    "correct_effects",
                    "wrong_effects",
                    "interactions",
                    "correct_effect_mean",
                    "wrong_effect_mean",
                    "interaction_mean",
                },
                f"inference.prompt_layer_effects {index}",
                errors,
            )
            if isinstance(entry, dict):
                for field in ("correct_effects", "wrong_effects", "interactions"):
                    effects = entry.get(field)
                    if isinstance(effects, list):
                        for effect_index, effect in enumerate(effects):
                            _reject_unknown_fields(
                                effect,
                                {
                                    "donor_assignment_id",
                                    "map_draw_id",
                                    "value",
                                },
                                f"inference.prompt_layer_effects {index} "
                                f"{field} {effect_index}",
                                errors,
                            )
    estimates = inference.get("layer_estimates")
    if isinstance(estimates, list):
        for index, entry in enumerate(estimates):
            _reject_unknown_fields(
                entry,
                {
                    "floor",
                    "layer",
                    "estimand",
                    "defined",
                    "reason",
                    "method",
                    "point_estimate",
                    "iterations",
                    "finite_replicates",
                    "ci_level",
                    "quantile_method",
                    "lower",
                    "upper",
                    "rng",
                    "weight_distribution",
                },
                f"inference.layer_estimates {index}",
                errors,
            )
            if isinstance(entry, dict):
                _reject_unknown_fields(
                    entry.get("rng"),
                    rng_fields,
                    f"inference.layer_estimates {index} rng",
                    errors,
                )
    thresholds = inference.get("threshold_derivation")
    _reject_unknown_fields(
        thresholds,
        {
            "available",
            "reason",
            "source_floor",
            "source_method",
            "factor",
            "layer_order",
            "source_estimates",
            "SPEC_MIN_EFFECT",
            "INTERACTION_MIN_EFFECT",
            "pilot_measurement_sha256",
            "derivation_code_sha256",
            "invalid_sources",
        },
        "inference.threshold_derivation",
        errors,
    )


def _same_finite_number(observed: Any, expected: float) -> bool:
    return (
        isinstance(observed, (int, float))
        and not isinstance(observed, bool)
        and math.isfinite(float(observed))
        and math.isclose(float(observed), expected, rel_tol=1e-9, abs_tol=1e-9)
    )


def _canonical_json_digest(document: dict[str, Any]) -> str:
    canonical = (
        json.dumps(document, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


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


def _compare_compact_tree(
    observed: Any, expected: Any, label: str, errors: list[str]
) -> None:
    if isinstance(expected, dict):
        if not isinstance(observed, dict):
            errors.append(f"{label} must be an object")
            return
        require(
            set(observed) == set(expected),
            f"{label} components are {sorted(observed)}, expected {sorted(expected)}",
            errors,
        )
        for key in expected.keys() & observed.keys():
            _compare_compact_tree(
                observed[key], expected[key], f"{label}.{key}", errors
            )
        return
    if expected is None:
        require(observed is None, f"{label} disagrees with recomputed value", errors)
        return
    require(
        _same_finite_number(observed, expected),
        f"{label} disagrees with recomputed value",
        errors,
    )


def _compare_normative(
    observed: Any, expected: Any, label: str, errors: list[str]
) -> None:
    if isinstance(expected, dict):
        if not isinstance(observed, dict):
            errors.append(f"{label} must be an object")
            return
        require(
            set(observed) == set(expected),
            f"{label} fields disagree with recomputed content",
            errors,
        )
        for key in expected.keys() & observed.keys():
            _compare_normative(observed[key], expected[key], f"{label}.{key}", errors)
        return
    if isinstance(expected, list):
        if not isinstance(observed, list):
            errors.append(f"{label} must be a list")
            return
        require(
            len(observed) == len(expected),
            f"{label} length disagrees with recomputed content",
            errors,
        )
        for index, (observed_item, expected_item) in enumerate(
            zip(observed, expected, strict=False)
        ):
            _compare_normative(
                observed_item, expected_item, f"{label}[{index}]", errors
            )
        return
    if isinstance(expected, float):
        require(
            _same_finite_number(observed, expected),
            f"{label} disagrees with recomputed value",
            errors,
        )
        return
    require(observed == expected, f"{label} disagrees with recomputed value", errors)


def _map_compact_scores(value: Any, transform: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _map_compact_scores(child, transform) for key, child in value.items()
        }
    if not (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    ):
        raise ValueError("factorized score leaves must be finite numbers")
    return transform(float(value))


def _validate_stage2b_measurement_envelope(
    artifact: dict[str, Any], errors: list[str]
) -> None:
    """Bind a direct Stage 2b pilot artifact to the pinned execution envelope."""
    hex_digest = re.compile(r"[0-9a-f]{64}").fullmatch
    required = {
        "artifact_type",
        "authorization",
        "constants",
        "created_at_utc",
        "denominator_derivation",
        "design",
        "descriptive",
        "disjointness",
        "evidence_class",
        "instrumentation",
        "inference",
        "lens",
        "model",
        "partition",
        "preflight",
        "registry",
        "retention",
        "run_id",
        "run_mode",
        "runtime",
        "schema",
        "scope",
        "stimulus_manifest",
    }
    missing = sorted(required - artifact.keys())
    require(
        not missing, f"Stage 2b aggregate missing top-level fields: {missing}", errors
    )
    require(
        artifact.get("artifact_type") == "aggregate",
        "Stage 2b artifact_type must be aggregate",
        errors,
    )
    require(
        artifact.get("schema") == STAGE2B_SCHEMA,
        f"Stage 2b schema must be {STAGE2B_SCHEMA}",
        errors,
    )
    require(
        artifact.get("run_mode") == "pilot",
        "current Stage 2b measurement contract is pilot-only",
        errors,
    )
    require(
        isinstance(artifact.get("created_at_utc"), str)
        and bool(artifact.get("created_at_utc")),
        "created_at_utc must be a non-empty string",
        errors,
    )

    for section, expected in (
        ("model", STAGE2B_MODEL),
        ("lens", STAGE2B_LENS),
        ("instrumentation", STAGE2B_INSTRUMENTATION),
    ):
        observed = artifact.get(section)
        require(
            isinstance(observed, dict)
            and all(observed.get(key) == value for key, value in expected.items()),
            f"{section} does not match the pinned Stage 2b identity",
            errors,
        )

    source_layers = nested(artifact, "lens", "source_layers")
    require(
        isinstance(source_layers, list)
        and all(
            isinstance(layer, int) and not isinstance(layer, bool)
            for layer in source_layers
        )
        and len(source_layers) == len(set(source_layers))
        and set(STAGE2B_SELECTED_LAYERS) <= set(source_layers),
        "lens.source_layers must be unique integers containing every selected layer",
        errors,
    )

    runtime_versions = nested(artifact, "runtime", "packages")
    require(
        isinstance(runtime_versions, dict)
        and all(
            runtime_versions.get(name) == version
            for name, version in STAGE2B_RUNTIME_VERSIONS.items()
        ),
        "runtime.packages do not match the pinned Stage 2b versions",
        errors,
    )
    runtime = artifact.get("runtime")
    require(
        isinstance(runtime, dict)
        and runtime.get("install_schema") == STAGE2B_RUNTIME_INSTALL_SCHEMA
        and runtime.get("install_spec_sha256") == STAGE2B_RUNTIME_INSTALL_SPEC_SHA256
        and runtime.get("fresh_process_after_install") is True
        and runtime.get("torchvision_state") == "absent",
        "runtime does not prove the exact fresh-process text-only install contract",
        errors,
    )

    authorization = artifact.get("authorization")
    require(
        isinstance(authorization, dict)
        and authorization.get("pilot_authorized") is True
        and authorization.get("pilot_protocol_ratified") is True
        and authorization.get("confirmatory_thresholds_ratified") is False,
        "pilot artifact requires explicit pilot authorization/protocol evidence and no confirmatory authorization",
        errors,
    )
    if isinstance(authorization, dict):
        require(
            hex_digest(authorization.get("authorization_record_sha256")) is not None,
            "authorization record SHA-256 is invalid",
            errors,
        )
        require(
            authorization.get("authority") == "Dr. Mani",
            "pilot artifact authority must be exactly 'Dr. Mani'",
            errors,
        )
        require(
            isinstance(authorization.get("authorized_at_utc"), str)
            and re.fullmatch(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z",
                authorization["authorized_at_utc"],
            )
            is not None,
            "pilot authorization timestamp must use second-resolution UTC RFC 3339",
            errors,
        )
        require(
            hex_digest(authorization.get("instruction_sha256")) is not None,
            "pilot authorization instruction SHA-256 is invalid",
            errors,
        )
        require(
            hex_digest(authorization.get("notebook_sha256")) is not None,
            "authorized notebook SHA-256 is invalid",
            errors,
        )
        require(
            hex_digest(authorization.get("code_bundle_sha256")) is not None,
            "authorized code-bundle SHA-256 is invalid",
            errors,
        )
    preflight = artifact.get("preflight")
    require(
        isinstance(preflight, dict)
        and preflight.get("pinned_identities_matched") is True
        and preflight.get("capacity_ok") is True
        and preflight.get("tensor_contracts_passed") is True
        and preflight.get("crossing_registry_checked") is True,
        "pilot artifact requires complete successful preflight evidence",
        errors,
    )

    manifest = artifact.get("stimulus_manifest")
    require(
        isinstance(manifest, dict)
        and manifest.get("sha256") == STAGE2B_SOURCE_MANIFEST_SHA256
        and manifest.get("n_prompts") == STAGE2B_SOURCE_PROMPTS,
        "stimulus_manifest must bind the pinned 200-prompt source identity",
        errors,
    )

    design = artifact.get("design")
    expected_design = {
        "selected_layers": list(STAGE2B_SELECTED_LAYERS),
        "positions": list(STAGE2B_POSITIONS),
        "primary_floor_id": STAGE2B_FLOORS["primary"],
        "sensitivity_floor_id": STAGE2B_FLOORS["sensitivity"],
        "donor_assignment_count": 8,
        "broken_map_draw_count": 8,
        "unique_readouts_per_prompt_layer": 81,
        "logical_crossings_per_prompt_layer": 64,
        "content_hash_method": STAGE2B_CONTENT_HASH_METHOD,
        "model_n_layers": STAGE2B_MODEL["n_layers"],
    }
    require(
        isinstance(design, dict)
        and all(design.get(key) == value for key, value in expected_design.items())
        and isinstance(design.get("vocab_size"), int)
        and not isinstance(design.get("vocab_size"), bool)
        and design["vocab_size"] > 0,
        "design does not match the ratified dual-floor 81-readout/64-cell contract",
        errors,
    )


def _validate_trusted_pilot_source_binding(
    artifact: dict[str, Any],
    expected_source: dict[str, str] | None,
    errors: list[str],
) -> None:
    """Compare retained source claims with identities supplied outside the artifact."""
    required = {
        "authorization_record_sha256",
        "notebook_sha256",
        "code_bundle_sha256",
    }
    if not isinstance(expected_source, dict) or set(expected_source) != required:
        errors.append(
            "trusted expected pilot source identities are required independently "
            "of the artifact"
        )
        return
    authorization = artifact.get("authorization")
    if not isinstance(authorization, dict):
        return
    for field in sorted(required):
        expected = expected_source[field]
        require(
            isinstance(expected, str)
            and re.fullmatch(r"[0-9a-f]{64}", expected) is not None,
            f"trusted expected {field} is not a lowercase SHA-256",
            errors,
        )
        require(
            authorization.get(field) == expected,
            f"artifact {field} does not match the independently supplied source identity",
            errors,
        )


def _validate_compact_dual_floor_records(
    artifact: dict[str, Any],
    errors: list[str],
    *,
    expected_pilot_view: dict[str, Any] | None,
) -> None:
    """Validate lossless 81-readout records and recompute both 8x8 floors."""
    descriptive = artifact.get("descriptive")
    records = descriptive.get("records") if isinstance(descriptive, dict) else None
    require(
        isinstance(records, list) and bool(records),
        "descriptive must contain non-empty compact records",
        errors,
    )
    if not isinstance(records, list) or not records:
        return

    min_denominator = nested(artifact, "constants", "min_denominator")
    valid_min_denominator = (
        isinstance(min_denominator, (int, float))
        and not isinstance(min_denominator, bool)
        and math.isfinite(float(min_denominator))
    )
    require(
        valid_min_denominator,
        "compact records require a finite constants.min_denominator",
        errors,
    )
    registry_entries = nested(artifact, "registry", "entries")
    denominator_entries = (
        [
            entry
            for entry in registry_entries
            if isinstance(entry, dict) and entry.get("name") == "NTA_MIN_DENOMINATOR"
        ]
        if isinstance(registry_entries, list)
        else []
    )
    denominator_derived = (
        valid_min_denominator
        and len(denominator_entries) == 1
        and denominator_entries[0].get("status") == "derived"
        and _same_finite_number(
            denominator_entries[0].get("declared_value"), float(min_denominator)
        )
    )
    require(
        denominator_derived,
        "compact records require a derived min_denominator matching constants",
        errors,
    )
    if not denominator_derived:
        return
    min_denominator = float(min_denominator)

    hex_digest = re.compile(r"[0-9a-f]{64}").fullmatch
    factor_names = {
        "correct_act_fitted_map",
        "correct_act_broken_map",
        "wrong_act_fitted_map",
        "wrong_act_broken_map",
    }
    floor_names = {
        "input_embedding_decoded",
        "layer0_residual_decoded",
        "output_decoded",
    }
    nta_names = {
        "input_embedding_decoded",
        "layer0_residual_decoded",
        "sensitivity_minus_primary",
    }
    required_compact_fields = {
        "category",
        "layer",
        "prompt_sha256",
        "target_id",
        "target_source",
        "target_derivation",
        "donor_assignments",
        "map_draws",
        "floor_scores",
        "factorized_scores",
        "factorized_nta",
        "floor_status",
    }
    allowed_compact_fields = required_compact_fields
    expected_prompts = (
        {
            prompt.get("sha256"): prompt.get("category")
            for prompt in expected_pilot_view.get("prompts", [])
            if isinstance(prompt, dict)
        }
        if isinstance(expected_pilot_view, dict)
        else {}
    )
    selected_layers = nested(artifact, "design", "selected_layers")
    valid_selected_layers = (
        list(STAGE2B_SELECTED_LAYERS)
        if selected_layers == list(STAGE2B_SELECTED_LAYERS)
        else []
    )
    vocab_size = nested(artifact, "design", "vocab_size")
    seen_loci: list[tuple[str, int]] = []
    donor_seed_registry: dict[str, int] = {}
    donor_source_registry: dict[tuple[str, str], str] = {}
    map_seed_registry: dict[str, int] = {}
    map_hash_registry: dict[tuple[int, str], str] = {}
    map_spectrum_registry: dict[tuple[int, str], dict[str, Any]] = {}
    fitted_spectrum_registry: dict[int, str] = {}
    target_derivation_registry: dict[str, dict[str, Any]] = {}
    crossing_seed_vectors = derive_crossing_seed_vectors()
    expected_donors = {entry["id"]: entry for entry in crossing_seed_vectors["donors"]}
    expected_maps = {entry["id"]: entry for entry in crossing_seed_vectors["maps"]}

    for index, record in enumerate(records):
        label = f"compact record {index}"
        if not isinstance(record, dict):
            errors.append(f"{label} must be an object")
            continue
        record_fields = set(record)
        if not required_compact_fields <= record_fields:
            errors.append(
                f"compact records require fields {sorted(required_compact_fields)}"
            )
            continue
        unknown_fields = sorted(record_fields - allowed_compact_fields)
        require(
            not unknown_fields,
            f"{label} has unknown compact fields: {unknown_fields}",
            errors,
        )
        recipient = record.get("prompt_sha256")
        require(
            isinstance(recipient, str) and hex_digest(recipient) is not None,
            f"{label} has invalid recipient prompt digest",
            errors,
        )
        layer = record.get("layer")
        category = record.get("category")
        require(
            isinstance(layer, int)
            and not isinstance(layer, bool)
            and layer in valid_selected_layers,
            f"{label} has invalid or unselected layer",
            errors,
        )
        require(
            isinstance(category, str)
            and bool(category)
            and expected_prompts.get(recipient) == category,
            f"{label} category does not match the expected pilot view",
            errors,
        )
        if isinstance(recipient, str) and isinstance(layer, int):
            seen_loci.append((recipient, layer))
        target_id = record.get("target_id")
        require(
            isinstance(target_id, int)
            and not isinstance(target_id, bool)
            and target_id >= 0,
            f"{label} has invalid target_id",
            errors,
        )
        if (
            isinstance(target_id, int)
            and not isinstance(target_id, bool)
            and isinstance(vocab_size, int)
        ):
            require(
                target_id < vocab_size,
                f"{label} target_id is outside design.vocab_size",
                errors,
            )
        require(
            record.get("target_source") == "model_argmax",
            f"{label} target_source must be model_argmax",
            errors,
        )
        target_derivation = record.get("target_derivation")
        target_derivation_fields = {
            "method",
            "output_logits_sha256",
            "output_logits_dtype",
            "output_logits_shape",
            "max_logit",
            "argmax_tie_token_ids",
            "tie_break_rule",
            "runtime_verifier_id",
            "runtime_verified",
            "target_decision_sha256",
        }
        valid_target_derivation = (
            isinstance(target_derivation, dict)
            and set(target_derivation) == target_derivation_fields
        )
        require(
            valid_target_derivation,
            f"{label} target_derivation fields are missing, extra, or mislabeled",
            errors,
        )
        if valid_target_derivation:
            assert isinstance(target_derivation, dict)
            logits_digest = target_derivation["output_logits_sha256"]
            logits_shape = target_derivation["output_logits_shape"]
            max_logit = target_derivation["max_logit"]
            tie_ids = target_derivation["argmax_tie_token_ids"]
            require(
                target_derivation["method"] == "model_argmax",
                f"{label} target_derivation method must be model_argmax",
                errors,
            )
            require(
                isinstance(logits_digest, str)
                and hex_digest(logits_digest) is not None,
                f"{label} target_derivation has invalid output-logits identity",
                errors,
            )
            require(
                target_derivation["output_logits_dtype"] == "float32",
                f"{label} target_derivation output-logits dtype must be float32",
                errors,
            )
            require(
                logits_shape == [vocab_size],
                f"{label} target_derivation output-logits shape must match design.vocab_size",
                errors,
            )
            require(
                isinstance(max_logit, (int, float))
                and not isinstance(max_logit, bool)
                and math.isfinite(float(max_logit)),
                f"{label} target_derivation max_logit must be finite",
                errors,
            )
            valid_ties = (
                isinstance(tie_ids, list)
                and bool(tie_ids)
                and all(
                    isinstance(token_id, int)
                    and not isinstance(token_id, bool)
                    and isinstance(vocab_size, int)
                    and 0 <= token_id < vocab_size
                    for token_id in tie_ids
                )
                and tie_ids == sorted(set(tie_ids))
            )
            require(
                valid_ties,
                f"{label} target_derivation argmax tie IDs must be sorted unique in-vocabulary integers",
                errors,
            )
            require(
                target_derivation["tie_break_rule"] == "lowest_token_id",
                f"{label} target_derivation tie-break rule must be lowest_token_id",
                errors,
            )
            require(
                target_derivation["runtime_verifier_id"]
                == STAGE2B_TARGET_RUNTIME_VERIFIER,
                f"{label} target_derivation runtime verifier identity is invalid",
                errors,
            )
            require(
                target_derivation["runtime_verified"] is True,
                f"{label} target_derivation runtime verification is not true",
                errors,
            )
            if valid_ties and isinstance(target_id, int):
                require(
                    target_id == tie_ids[0],
                    f"{label} target_id does not follow the recorded lowest-token tie-break",
                    errors,
                )
            expected_target_digest = (
                target_decision_sha256(target_id, target_derivation)
                if isinstance(target_id, int) and not isinstance(target_id, bool)
                else None
            )
            require(
                target_derivation["target_decision_sha256"] == expected_target_digest,
                f"{label} target decision digest disagrees with retained derivation evidence",
                errors,
            )
            if (
                isinstance(recipient, str)
                and hex_digest(recipient) is not None
                and valid_ties
                and target_derivation["target_decision_sha256"]
                == expected_target_digest
            ):
                previous_derivation = target_derivation_registry.setdefault(
                    recipient, target_derivation
                )
                require(
                    previous_derivation == target_derivation,
                    f"{label} target derivation disagrees across layers for the same prompt",
                    errors,
                )

        donor_assignments = record.get("donor_assignments")
        valid_donor_list = (
            isinstance(donor_assignments, list) and len(donor_assignments) == 8
        )
        require(
            valid_donor_list, f"{label} requires exactly 8 donor assignments", errors
        )
        donor_ids: list[str] = []
        donor_seeds: list[int] = []
        if isinstance(donor_assignments, list):
            for donor_index, assignment in enumerate(donor_assignments):
                item_label = f"{label} donor assignment {donor_index}"
                if not isinstance(assignment, dict):
                    errors.append(f"{item_label} must be an object")
                    continue
                donor_id = assignment.get("donor_assignment_id")
                assignment_recipient = assignment.get("recipient_prompt_sha256")
                source = assignment.get("source_prompt_sha256")
                recipient_to_donor_digest = assignment.get("recipient_to_donor_sha256")
                residual_digest = assignment.get("residual_sha256")
                seed = assignment.get("seed")
                require(
                    isinstance(donor_id, str) and bool(donor_id),
                    f"{item_label} has invalid donor_assignment_id",
                    errors,
                )
                if isinstance(donor_id, str):
                    donor_ids.append(donor_id)
                require(
                    assignment_recipient == recipient,
                    f"{item_label} recipient prompt hash disagrees with record",
                    errors,
                )
                require(
                    isinstance(source, str)
                    and hex_digest(source) is not None
                    and source != recipient,
                    f"{item_label} has invalid/self recipient-to-donor digest",
                    errors,
                )
                require(
                    source in expected_prompts,
                    f"{item_label} donor source is outside the expected pilot view",
                    errors,
                )
                expected_pair_digest = (
                    hashlib.sha256(f"{recipient}->{source}".encode()).hexdigest()
                    if isinstance(recipient, str) and isinstance(source, str)
                    else None
                )
                require(
                    recipient_to_donor_digest == expected_pair_digest,
                    f"{item_label} recipient-to-donor hash disagrees with prompt pair",
                    errors,
                )
                require(
                    isinstance(residual_digest, str)
                    and hex_digest(residual_digest) is not None,
                    f"{item_label} has invalid residual hash",
                    errors,
                )
                require(
                    isinstance(seed, int) and not isinstance(seed, bool),
                    f"{item_label} has invalid seed",
                    errors,
                )
                expected_seed = expected_donors.get(donor_id)
                require(
                    isinstance(expected_seed, dict)
                    and assignment.get("seed_index") == expected_seed["index"]
                    and assignment.get("seed_namespace") == expected_seed["namespace"]
                    and assignment.get("seed_sha256") == expected_seed["sha256"]
                    and seed == expected_seed["seed"]
                    and assignment.get("bit_generator")
                    == expected_seed["bit_generator"],
                    f"{item_label} seed provenance does not match the ratified derivation",
                    errors,
                )
                if (
                    isinstance(recipient, str)
                    and recipient in expected_prompts
                    and isinstance(source, str)
                    and source in expected_prompts
                    and isinstance(seed, int)
                    and not isinstance(seed, bool)
                ):
                    expected_source = select_wrong_activation_source(
                        tuple(expected_prompts),
                        recipient,
                        seed,
                    )
                    require(
                        source == expected_source,
                        f"{item_label} donor source does not match the ratified "
                        "recipient-and-seed selection",
                        errors,
                    )
                if isinstance(seed, int) and not isinstance(seed, bool):
                    donor_seeds.append(seed)
                if (
                    isinstance(donor_id, str)
                    and donor_id
                    and isinstance(recipient, str)
                    and isinstance(source, str)
                    and hex_digest(source) is not None
                ):
                    previous_source = donor_source_registry.setdefault(
                        (recipient, donor_id), source
                    )
                    require(
                        previous_source == source,
                        f"{item_label} source disagrees across layers for the same recipient and donor assignment",
                        errors,
                    )
                if (
                    isinstance(donor_id, str)
                    and donor_id
                    and isinstance(seed, int)
                    and not isinstance(seed, bool)
                ):
                    previous_seed = donor_seed_registry.setdefault(donor_id, seed)
                    require(
                        previous_seed == seed,
                        f"{item_label} seed disagrees with the run-wide donor registry",
                        errors,
                    )
        require(
            len(donor_ids) == 8 and len(set(donor_ids)) == 8,
            f"{label} donor assignment IDs must be exactly 8 unique strings",
            errors,
        )
        require(
            len(donor_seeds) == 8 and len(set(donor_seeds)) == 8,
            f"{label} donor seeds must be exactly 8 unique integers",
            errors,
        )

        map_draws = record.get("map_draws")
        valid_map_list = isinstance(map_draws, list) and len(map_draws) == 8
        require(valid_map_list, f"{label} requires exactly 8 map draws", errors)
        map_ids: list[str] = []
        map_seeds: list[int] = []
        if isinstance(map_draws, list):
            for map_index, draw in enumerate(map_draws):
                item_label = f"{label} map draw {map_index}"
                if not isinstance(draw, dict):
                    errors.append(f"{item_label} must be an object")
                    continue
                map_id = draw.get("map_draw_id")
                seed = draw.get("seed")
                map_hash = draw.get("sha256")
                require(
                    isinstance(map_id, str) and bool(map_id),
                    f"{item_label} has invalid map_draw_id",
                    errors,
                )
                if isinstance(map_id, str):
                    map_ids.append(map_id)
                require(
                    isinstance(seed, int) and not isinstance(seed, bool),
                    f"{item_label} has invalid seed",
                    errors,
                )
                expected_seed = expected_maps.get(map_id)
                require(
                    isinstance(expected_seed, dict)
                    and draw.get("seed_index") == expected_seed["index"]
                    and draw.get("seed_namespace") == expected_seed["namespace"]
                    and draw.get("seed_sha256") == expected_seed["sha256"]
                    and seed == expected_seed["seed"]
                    and draw.get("bit_generator") == expected_seed["bit_generator"],
                    f"{item_label} seed provenance does not match the ratified derivation",
                    errors,
                )
                if isinstance(seed, int) and not isinstance(seed, bool):
                    map_seeds.append(seed)
                require(
                    isinstance(map_hash, str) and hex_digest(map_hash) is not None,
                    f"{item_label} has invalid map hash",
                    errors,
                )
                spectrum = draw.get("spectrum_check")
                spectrum_fields = {
                    "schema",
                    "method",
                    "singular_value_count",
                    "fitted_singular_values_sha256",
                    "broken_singular_values_sha256",
                    "rtol",
                    "atol",
                    "max_abs_diff",
                    "max_normalized_error",
                    "verified",
                }
                valid_spectrum = (
                    isinstance(spectrum, dict) and set(spectrum) == spectrum_fields
                )
                require(
                    valid_spectrum,
                    f"{item_label} requires complete realized-map spectrum evidence",
                    errors,
                )
                if valid_spectrum:
                    assert isinstance(spectrum, dict)
                    max_abs_diff = spectrum["max_abs_diff"]
                    max_normalized_error = spectrum["max_normalized_error"]
                    require(
                        spectrum["schema"] == "stage2b-map-spectrum-check/v1"
                        and spectrum["method"] == "numpy.linalg.svd-allclose/v1"
                        and spectrum["singular_value_count"] == STAGE2B_MODEL["d_model"]
                        and isinstance(spectrum["fitted_singular_values_sha256"], str)
                        and hex_digest(spectrum["fitted_singular_values_sha256"])
                        is not None
                        and isinstance(spectrum["broken_singular_values_sha256"], str)
                        and hex_digest(spectrum["broken_singular_values_sha256"])
                        is not None
                        and spectrum["rtol"] == SINGULAR_SPECTRUM_RTOL
                        and spectrum["atol"] == SINGULAR_SPECTRUM_ATOL
                        and isinstance(max_abs_diff, (int, float))
                        and not isinstance(max_abs_diff, bool)
                        and math.isfinite(float(max_abs_diff))
                        and float(max_abs_diff) >= 0.0
                        and isinstance(max_normalized_error, (int, float))
                        and not isinstance(max_normalized_error, bool)
                        and math.isfinite(float(max_normalized_error))
                        and 0.0 <= float(max_normalized_error) <= 1.0
                        and spectrum["verified"] is True,
                        f"{item_label} realized-map spectrum evidence does not "
                        "prove preservation under the declared tolerance",
                        errors,
                    )
                    if isinstance(layer, int) and isinstance(map_id, str) and map_id:
                        previous_spectrum = map_spectrum_registry.setdefault(
                            (layer, map_id), spectrum
                        )
                        require(
                            previous_spectrum == spectrum,
                            f"{item_label} spectrum evidence disagrees across "
                            "prompts at the same layer",
                            errors,
                        )
                        fitted_spectrum_digest = spectrum[
                            "fitted_singular_values_sha256"
                        ]
                        if isinstance(fitted_spectrum_digest, str):
                            previous_fitted = fitted_spectrum_registry.setdefault(
                                layer, fitted_spectrum_digest
                            )
                            require(
                                previous_fitted == fitted_spectrum_digest,
                                f"{item_label} fitted spectrum identity disagrees "
                                "across draws at the same layer",
                                errors,
                            )
                if (
                    isinstance(map_id, str)
                    and map_id
                    and isinstance(seed, int)
                    and not isinstance(seed, bool)
                ):
                    previous_seed = map_seed_registry.setdefault(map_id, seed)
                    require(
                        previous_seed == seed,
                        f"{item_label} seed disagrees with the run-wide map registry",
                        errors,
                    )
                if (
                    isinstance(layer, int)
                    and isinstance(map_id, str)
                    and map_id
                    and isinstance(map_hash, str)
                    and hex_digest(map_hash) is not None
                ):
                    previous_hash = map_hash_registry.setdefault(
                        (layer, map_id), map_hash
                    )
                    require(
                        previous_hash == map_hash,
                        f"{item_label} hash disagrees across prompts at the same layer",
                        errors,
                    )
        require(
            len(map_ids) == 8 and len(set(map_ids)) == 8,
            f"{label} map draw IDs must be exactly 8 unique strings",
            errors,
        )
        require(
            len(map_seeds) == 8 and len(set(map_seeds)) == 8,
            f"{label} map seeds must be exactly 8 unique integers",
            errors,
        )

        floor_scores = record.get("floor_scores")
        valid_floors = (
            isinstance(floor_scores, dict) and set(floor_scores) == floor_names
        )
        require(valid_floors, f"{label} floor_scores components are mislabeled", errors)
        if not valid_floors:
            continue
        assert isinstance(floor_scores, dict)
        if not all(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(float(value))
            for value in floor_scores.values()
        ):
            errors.append(f"{label} floor_scores must be finite numbers")
            continue
        floor_status = record.get("floor_status")
        expected_floor_status = {}
        for floor in ("input_embedding_decoded", "layer0_residual_decoded"):
            denominator = float(floor_scores["output_decoded"]) - float(
                floor_scores[floor]
            )
            eligible = denominator > min_denominator
            expected_floor_status[floor] = {
                "denominator": denominator,
                "eligible": eligible,
                "exclusion_reason": (
                    None if eligible else "denominator_not_greater_than_guard"
                ),
            }
        require(
            floor_status == expected_floor_status,
            f"{label} floor_status does not match retained scores and derived guard",
            errors,
        )

        factorized_scores = record.get("factorized_scores")
        require(
            isinstance(factorized_scores, dict)
            and set(factorized_scores) == factor_names,
            f"{label} factorized_scores components are missing, extra, or mislabeled",
            errors,
        )
        if (
            not isinstance(factorized_scores, dict)
            or set(factorized_scores) != factor_names
        ):
            continue
        try:
            score_crossing = materialize_crossed_factorials(factorized_scores)
        except (AttributeError, TypeError, ValueError) as exc:
            errors.append(f"{label} factorized_scores cannot materialize: {exc}")
            continue
        require(
            score_crossing.get("unique_readout_count") == 81
            and score_crossing.get("logical_cell_count") == 64,
            f"{label} must contain 81 unique readouts and 64 logical factorials",
            errors,
        )
        require(
            set(score_crossing.get("donor_assignment_ids", [])) == set(donor_ids),
            f"{label} factorized donor labels disagree with donor assignments",
            errors,
        )
        require(
            set(score_crossing.get("map_draw_ids", [])) == set(map_ids),
            f"{label} factorized map labels disagree with map draws",
            errors,
        )

        input_floor = float(floor_scores["input_embedding_decoded"])
        layer0_floor = float(floor_scores["layer0_residual_decoded"])
        output_floor = float(floor_scores["output_decoded"])
        try:
            expected_nta = _map_compact_scores(
                factorized_scores,
                lambda score, input_floor=input_floor, layer0_floor=layer0_floor, output_floor=output_floor: (
                    dual_floor_nta(
                        s_readout=score,
                        s_input_embedding=input_floor,
                        s_layer0_residual=layer0_floor,
                        s_output=output_floor,
                        min_denominator=min_denominator,
                    )
                ),
            )
        except (TypeError, ValueError) as exc:
            errors.append(f"{label} cannot recompute dual-floor NTA: {exc}")
            continue
        recomputed = {
            floor: _extract_compact_floor(expected_nta, floor) for floor in nta_names
        }
        observed_nta = record.get("factorized_nta")
        require(
            isinstance(observed_nta, dict) and set(observed_nta) == nta_names,
            f"{label} factorized_nta components are missing, extra, or mislabeled",
            errors,
        )
        if not isinstance(observed_nta, dict) or set(observed_nta) != nta_names:
            continue
        _compare_compact_tree(
            observed_nta, recomputed, f"{label} factorized_nta", errors
        )
        for floor in ("input_embedding_decoded", "layer0_residual_decoded"):
            try:
                crossing = materialize_crossed_factorials(observed_nta[floor])
            except (AttributeError, TypeError, ValueError) as exc:
                errors.append(f"{label} {floor} cannot materialize: {exc}")
                continue
            require(
                crossing.get("unique_readout_count") == 81
                and crossing.get("logical_cell_count") == 64,
                f"{label} {floor} must materialize 81 unique readouts into 64 factorials",
                errors,
            )

    expected_loci = {
        (prompt_digest, layer)
        for prompt_digest in expected_prompts
        for layer in valid_selected_layers
    }
    require(
        len(seen_loci) == len(set(seen_loci)),
        "compact prompt-layer records must be unique",
        errors,
    )
    require(
        set(seen_loci) == expected_loci,
        "compact prompt-layer coverage must exactly match the expected pilot view and selected layers",
        errors,
    )


def _extract_compact_floor(value: Any, floor: str) -> Any:
    if isinstance(value, dict) and set(value) == {
        "input_embedding_decoded",
        "layer0_residual_decoded",
        "sensitivity_minus_primary",
    }:
        selected = value[floor]
        return None if isinstance(selected, NTAExcluded) else selected
    if isinstance(value, dict):
        return {
            key: _extract_compact_floor(child, floor) for key, child in value.items()
        }
    raise TypeError("dual-floor NTA tree is malformed")


def _validate_stage2b_factorization(descriptive: Any, errors: list[str]) -> None:
    factorization = (
        descriptive.get("factorization") if isinstance(descriptive, dict) else None
    )
    expected = {
        "unique_readouts_per_prompt_layer": 81,
        "logical_crossings_per_prompt_layer": 64,
        "donor_assignment_count": 8,
        "broken_map_draw_count": 8,
    }
    require(
        isinstance(factorization, dict)
        and all(factorization.get(key) == value for key, value in expected.items()),
        "descriptive.factorization must declare exact 81-readout/64-cell/8-donor/8-map structure",
        errors,
    )


def _validate_stage2b_pilot_statistics(
    artifact: dict[str, Any], errors: list[str]
) -> None:
    """Recompute the two-stage guard, NTA, uncertainty, and threshold packet."""
    constants = artifact.get("constants")
    expected_constants = {
        "guard_quantile": 0.05,
        "guard_quantile_method": "linear",
        "bootstrap_iterations": 20_000,
        "bootstrap_ci_level": 0.99,
        "bootstrap_quantile_method": "linear",
        "bootstrap_bit_generator": "PCG64",
    }
    min_denominator = (
        constants.get("min_denominator") if isinstance(constants, dict) else None
    )
    valid_constants = (
        isinstance(constants, dict)
        and all(
            constants.get(key) == value for key, value in expected_constants.items()
        )
        and isinstance(min_denominator, (int, float))
        and not isinstance(min_denominator, bool)
        and math.isfinite(float(min_denominator))
        and float(min_denominator) > 0
    )
    require(
        valid_constants,
        "constants do not match the ratified pilot statistical contract",
        errors,
    )
    records = nested(artifact, "descriptive", "records")
    if not isinstance(records, list) or not records:
        return
    try:
        recomputed_records, denominator = materialize_pilot_nta(records)
    except (Stage2bStatisticsError, TypeError, ValueError) as exc:
        errors.append(f"pilot denominator/NTA recomputation failed: {exc}")
        return
    _compare_normative(
        artifact.get("denominator_derivation"),
        denominator,
        "denominator_derivation",
        errors,
    )
    _compare_normative(records, recomputed_records, "descriptive.records", errors)
    numpy_version = nested(artifact, "runtime", "packages", "numpy")
    if not isinstance(numpy_version, str) or not numpy_version:
        errors.append(
            "runtime NumPy version is unavailable for inference recomputation"
        )
        return
    cache_payload = json.dumps(
        {
            "records": recomputed_records,
            "denominator": denominator,
            "statistics_sha256": STAGE2B_STATISTICS_SHA256,
            "numpy_version": numpy_version,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    cache_key = hashlib.sha256(cache_payload.encode("ascii")).hexdigest()
    expected_inference = _STAGE2B_INFERENCE_RECOMPUTATION_CACHE.get(cache_key)
    if expected_inference is None:
        try:
            expected_inference = build_pilot_inference(
                recomputed_records,
                denominator,
                derivation_code_sha256=STAGE2B_STATISTICS_SHA256,
                numpy_version=numpy_version,
            )
        except (Stage2bStatisticsError, TypeError, ValueError) as exc:
            errors.append(f"pilot inference recomputation failed: {exc}")
            return
        _STAGE2B_INFERENCE_RECOMPUTATION_CACHE[cache_key] = expected_inference
    _compare_normative(
        artifact.get("inference"),
        expected_inference,
        "inference",
        errors,
    )


def _validate_expected_pilot_view(
    artifact: dict[str, Any], expected_view: Any, errors: list[str]
) -> None:
    hex_digest = re.compile(r"[0-9a-f]{64}").fullmatch
    if not isinstance(expected_view, dict):
        errors.append("pilot aggregate requires an expected pilot view object")
        return
    prompts = expected_view.get("prompts")
    n_prompts = expected_view.get("n_prompts")
    subset_digest = expected_view.get("pilot_subset_sha256")
    valid_shape = (
        expected_view.get("manifest_version") == "jspace-stage2b-pilot-view/v1"
        and isinstance(n_prompts, int)
        and not isinstance(n_prompts, bool)
        and n_prompts == STAGE2B_PILOT_PROMPTS
        and isinstance(prompts, list)
        and len(prompts) == n_prompts
        and isinstance(subset_digest, str)
        and hex_digest(subset_digest) is not None
        and isinstance(expected_view.get("source_manifest_sha256"), str)
        and hex_digest(expected_view["source_manifest_sha256"]) is not None
        and expected_view.get("source_n_prompts") == STAGE2B_SOURCE_PROMPTS
    )
    if not valid_shape:
        errors.append("expected pilot view is malformed")
        return
    expected_view_digest = _canonical_json_digest(expected_view)
    if (
        expected_view_digest != STAGE2B_PILOT_VIEW_SHA256
        or expected_view.get("source_manifest_sha256") != STAGE2B_SOURCE_MANIFEST_SHA256
    ):
        errors.append("expected pilot view does not match the pinned Stage 2b view")
        return
    assert isinstance(prompts, list)
    assert isinstance(subset_digest, str)
    ids: list[str] = []
    digests: list[str] = []
    categories: list[str] = []
    for prompt in prompts:
        if not isinstance(prompt, dict):
            errors.append("expected pilot view prompt must be an object")
            return
        prompt_id = prompt.get("id")
        prompt_digest = prompt.get("sha256")
        category = prompt.get("category")
        if not (
            isinstance(prompt_id, str)
            and bool(prompt_id)
            and isinstance(prompt_digest, str)
            and hex_digest(prompt_digest) is not None
            and isinstance(category, str)
            and bool(category)
        ):
            errors.append("expected pilot view prompt identity is malformed")
            return
        ids.append(prompt_id)
        digests.append(prompt_digest)
        categories.append(category)
    if len(set(ids)) != len(ids) or len(set(digests)) != len(digests):
        errors.append("expected pilot view prompt identities must be unique")
        return
    category_counts = {
        category: categories.count(category) for category in set(categories)
    }
    if len(category_counts) != 5 or set(category_counts.values()) != {4}:
        errors.append(
            "expected pilot view must contain four prompts in five categories"
        )
        return

    partition = artifact.get("partition")
    expected_partition = {
        "n_prompts": n_prompts,
        "pilot_subset_sha256": subset_digest,
        "pilot_view_sha256": _canonical_json_digest(expected_view),
        "pilot_prompt_ids": ids,
        "pilot_prompt_sha256s": digests,
    }
    require(
        isinstance(partition, dict)
        and all(
            partition.get(key) == value for key, value in expected_partition.items()
        )
        and partition.get("holdout_prompt_count")
        == STAGE2B_SOURCE_PROMPTS - STAGE2B_PILOT_PROMPTS
        and partition.get("holdout_accessed") is False,
        "pilot partition does not match the expected pilot view",
        errors,
    )
    stimulus_manifest = artifact.get("stimulus_manifest")
    require(
        isinstance(stimulus_manifest, dict)
        and stimulus_manifest.get("sha256")
        == expected_view.get("source_manifest_sha256")
        and stimulus_manifest.get("n_prompts") == expected_view.get("source_n_prompts"),
        "stimulus_manifest does not match the expected pilot view source",
        errors,
    )


def validate_stage2b_aggregate(
    artifact: dict[str, Any],
    path: Path,
    digest: str,
    errors: list[str],
    *,
    expected_pilot_view: dict[str, Any] | None = None,
    expected_source: dict[str, str] | None = None,
) -> None:
    """Validate Stage 2b pilot measurements and recomputable statistics."""
    del path, digest
    _validate_stage2b_schema_fields(artifact, errors)
    _validate_stage2b_measurement_envelope(artifact, errors)
    _validate_trusted_pilot_source_binding(artifact, expected_source, errors)
    _validate_provenance_blocks(artifact, errors)
    _validate_retention(artifact, errors)
    _validate_scope_evidence(artifact, errors)

    disjointness = artifact.get("disjointness")
    require(isinstance(disjointness, dict), "aggregate must carry disjointness", errors)
    if isinstance(disjointness, dict):
        require(
            disjointness.get("checked") is True,
            "disjointness.checked must be true",
            errors,
        )
        require(
            disjointness.get("overlap_count") == 0,
            f"disjointness.overlap_count is {disjointness.get('overlap_count')!r}, must be 0",
            errors,
        )
        require(
            disjointness.get("anchor_present") is False,
            "the Stage 1 anchor must be outside the analysis sample",
            errors,
        )
        require(
            disjointness.get("stage2b_manifest_sha256")
            == nested(artifact, "stimulus_manifest", "sha256"),
            "disjointness manifest identity disagrees with stimulus_manifest",
            errors,
        )

    run_mode = artifact.get("run_mode")
    for field in ("threshold_estimates", "gates", "decision"):
        require(
            field not in artifact,
            f"current measurement schema rejects unratified field {field!r}",
            errors,
        )

    require(
        isinstance(artifact.get("descriptive"), dict),
        "aggregate must carry a descriptive measurement block",
        errors,
    )
    _validate_stage2b_factorization(artifact.get("descriptive"), errors)
    if run_mode == "pilot":
        _validate_expected_pilot_view(artifact, expected_pilot_view, errors)
    _validate_compact_dual_floor_records(
        artifact,
        errors,
        expected_pilot_view=expected_pilot_view,
    )
    if not errors:
        _validate_stage2b_pilot_statistics(artifact, errors)


def validate(
    path: Path,
    expected_sha256: str | None,
    *,
    expected_pilot_view: dict[str, Any] | None = None,
    expected_source: dict[str, str] | None = None,
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
        validate_stage2b_aggregate(
            artifact,
            path,
            digest,
            errors,
            expected_pilot_view=expected_pilot_view,
            expected_source=expected_source,
        )
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
    parser.add_argument(
        "--pilot-view",
        type=Path,
        help="Independently checked pilot-view JSON required for pilot aggregates",
    )
    parser.add_argument(
        "--expected-authorization-record-sha256",
        help="Trusted launch-packet authorization-record identity",
    )
    parser.add_argument(
        "--expected-notebook-sha256",
        help="Trusted launch-packet canonical notebook identity",
    )
    parser.add_argument(
        "--expected-code-bundle-sha256",
        help="Trusted launch-packet code-bundle identity",
    )
    args = parser.parse_args()

    expected_pilot_view = None
    if args.pilot_view is not None:
        try:
            candidate = json.loads(args.pilot_view.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            parser.error(f"cannot read --pilot-view: {type(exc).__name__}: {exc}")
        if not isinstance(candidate, dict):
            parser.error("--pilot-view must contain a JSON object")
        expected_pilot_view = candidate
    expected_source = None
    source_values = {
        "authorization_record_sha256": args.expected_authorization_record_sha256,
        "notebook_sha256": args.expected_notebook_sha256,
        "code_bundle_sha256": args.expected_code_bundle_sha256,
    }
    if any(value is not None for value in source_values.values()):
        if not all(value is not None for value in source_values.values()):
            parser.error(
                "all three --expected-*-sha256 source identities are required together"
            )
        expected_source = source_values
    summary, errors = validate(
        args.artifact,
        args.expected_sha256,
        expected_pilot_view=expected_pilot_view,
        expected_source=expected_source,
    )
    result = {"summary": summary, "errors": errors}
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
