"""Stage 2b preflight: fail closed before any measurement begins.

Contract: ``specs/001-jspace-stage2b/contracts/preflight-api.md``.

This module MUST import cleanly with neither ``torch``, ``jlens``, nor ``scipy``
installed.  The repository exercises it on CPU without an interpretability stack.
Every check therefore takes already-extracted metadata -- shape tuples, dtype
*strings*, device
*strings*, digests, floats -- never a live tensor.

That constraint is what makes US3 testable at all.  Stage 2 put the equivalent
logic inside an 18 KB notebook cell, which is why three declared-but-unconsumed
constants survived to an audit: no test could reach any of it.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import re
import string
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any, NoReturn

try:
    from stage2b_statistics import (
        bootstrap_rng_identity,
        derive_crossing_seed_vectors,
    )
except ModuleNotFoundError:
    _statistics_path = Path(__file__).with_name("stage2b_statistics.py")
    _statistics_spec = importlib.util.spec_from_file_location(
        "stage2b_statistics", _statistics_path
    )
    if _statistics_spec is None or _statistics_spec.loader is None:
        raise
    _statistics_module = importlib.util.module_from_spec(_statistics_spec)
    _statistics_spec.loader.exec_module(_statistics_module)
    bootstrap_rng_identity = _statistics_module.bootstrap_rng_identity
    derive_crossing_seed_vectors = _statistics_module.derive_crossing_seed_vectors

__all__ = [
    "CONSUMER_READS",
    "ENDPOINT_FNS",
    "GATES",
    "GATE_READS",
    "INITIAL_REGISTRY",
    "PREFLIGHT_CHECKS",
    "PreflightError",
    "check_constant_registry",
    "check_crossing_registry",
    "check_environment",
    "check_ratification",
    "check_tensor_contracts",
    "emit_registry_record",
    "load_pilot_authorization_record",
    "materialize_pilot_authorization",
]


class PreflightError(Exception):
    """Raised when a preflight assertion fails.

    ``code`` is a stable slug that tests assert on; message text is for humans and
    may change.  ``detail`` carries the offending values so the failure can be
    recorded in the artifact rather than only printed.
    """

    def __init__(self, code: str, message: str, **detail: Any) -> None:
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.detail = detail


PILOT_AUTHORIZATION_SCHEMA = "jspace-stage2b-pilot-authorization/v1"
_PILOT_AUTHORIZATION_FILENAME = re.compile(
    r"stage2b-pilot-authorization-([0-9a-f]{64})\.json"
)


# --------------------------------------------------------------------------
# Consumer inventories.
#
# These are declared, never inferred.  A referential check that has to parse
# prose to learn what exists is not a check.  Adding a gate or a function means
# adding it here in the same change -- which is the point, since the alternative
# is a registry whose consumers drift out from under it.
# --------------------------------------------------------------------------

# Scientific gate composition remains unratified. Deferred inference inputs are
# consumed only by ``preflight:ratification``, which blocks execution until a
# separately approved protocol supplies them.
GATES: tuple[str, ...] = ()

#: Bare check names.  The implementing function for ``"manifest"`` is
#: ``check_manifest``; the ``check_`` prefix is not part of the identifier, so
#: registry entries read ``preflight:manifest``.  Keeping the prefix out of the
#: name means renaming the function does not silently orphan every constant that
#: pointed at it.
PREFLIGHT_CHECKS: tuple[str, ...] = (
    "tensor_contracts",
    "constant_registry",
    "crossing_registry",
    "manifest",
    "ratification",
    "environment",
)

ENDPOINT_FNS: tuple[str, ...] = (
    "target_rank1",
    "nta",
    "verify_rank_parity",
    "build_fit_broken_map",
    "build_fit_broken_maps",
    "singular_spectrum_evidence",
    "transport_with",
    "select_wrong_activation",
    "assemble_factorial_cells",
    "dual_floor_nta",
    "materialize_crossed_factorials",
    "derive_crossing_seed_vectors",
    "derive_nta_min_denominator",
    "crossed_prompt_effects",
    "check_floor_layer_coverage",
    "category_balanced_mean",
    "category_stratified_prompt_interval",
    "product_weight_interval",
    "derive_pilot_thresholds",
)

#: Constants and derived fields, each mapped to the consumers that read it.
#:
#: ``declared_value`` of ``None`` means deliberately unresolved, not forgotten.
#: Pilot-derived thresholds may remain unset only in pilot mode; every other
#: execution-critical unset value blocks both modes. ``status`` independently
#: distinguishes ratification from implementation and derivation.
_CROSSING_VECTORS = derive_crossing_seed_vectors()
_PILOT_BOOTSTRAP_IDENTITY = bootstrap_rng_identity(
    "pilot",
    numpy_version="runtime-recorded",
)

INITIAL_REGISTRY: dict[str, dict[str, Any]] = {
    # -- ratified pilot statistics and derived outputs ------------------------
    "STAGE1_RERUN_NOISE_MAX_ABS_LOGIT_DIFF": {
        "kind": "constant",
        "declared_value": 0.0,
        "consumed_by": ["preflight:ratification"],
    },
    "SPEC_MIN_EFFECT": {
        "kind": "derived_field",
        "declared_value": None,
        "consumed_by": ["endpoint:derive_pilot_thresholds"],
    },
    "BOOTSTRAP_CI_LEVEL": {
        "kind": "constant",
        "declared_value": 0.99,
        "consumed_by": [
            "endpoint:category_stratified_prompt_interval",
            "endpoint:product_weight_interval",
        ],
    },
    "UNCERTAINTY_METHOD": {
        "kind": "constant",
        "declared_value": {
            "primary": "category_stratified_prompt_percentile",
            "sensitivity": "prompt_donor_map_product_weight_percentile",
        },
        "consumed_by": ["preflight:ratification"],
    },
    "RESAMPLING_UNIT": {
        "kind": "constant",
        "declared_value": {
            "primary": "prompt_within_category",
            "sensitivity": "prompt_x_donor_assignment_x_map_draw",
        },
        "consumed_by": ["preflight:ratification"],
    },
    "INTERVAL_METHOD": {
        "kind": "constant",
        "declared_value": "two_sided_99_percentile_linear",
        "consumed_by": ["preflight:ratification"],
    },
    "BOOTSTRAP_ITERATIONS": {
        "kind": "constant",
        "declared_value": 20_000,
        "consumed_by": [
            "endpoint:category_stratified_prompt_interval",
            "endpoint:product_weight_interval",
        ],
    },
    "BOOTSTRAP_SEED": {
        "kind": "constant",
        "declared_value": {
            key: value
            for key, value in _PILOT_BOOTSTRAP_IDENTITY.items()
            if key != "numpy_version"
        },
        "consumed_by": [
            "endpoint:category_stratified_prompt_interval",
            "endpoint:product_weight_interval",
        ],
    },
    "AGGREGATION_RULE": {
        "kind": "constant",
        "declared_value": "equal_draw_mean_then_equal_category_mean_per_layer",
        "consumed_by": ["preflight:ratification"],
    },
    "THRESHOLD_DERIVATION_RULES": {
        "kind": "constant",
        "declared_value": {
            "SPEC_MIN_EFFECT": "0.5 * primary_floor_correct_effect_mean_by_layer",
            "INTERACTION_MIN_EFFECT": "0.5 * primary_floor_interaction_mean_by_layer",
            "NTA_MIN_DENOMINATOR": "linear_quantile_0.05_of_80_primary_denominators",
        },
        "consumed_by": [
            "endpoint:derive_nta_min_denominator",
            "endpoint:derive_pilot_thresholds",
        ],
    },
    "MULTIPLICITY_RULE": {
        "kind": "constant",
        "declared_value": "single_intersection_union_all_components_required",
        "consumed_by": ["preflight:ratification"],
    },
    "NTA_GUARD_QUANTILE": {
        "kind": "constant",
        "declared_value": 0.05,
        "consumed_by": ["endpoint:derive_nta_min_denominator"],
    },
    "NTA_GUARD_QUANTILE_METHOD": {
        "kind": "constant",
        "declared_value": "linear",
        "consumed_by": ["endpoint:derive_nta_min_denominator"],
    },
    "PILOT_MIN_LAYER_PROMPTS": {
        "kind": "constant",
        "declared_value": 18,
        "consumed_by": ["endpoint:check_floor_layer_coverage"],
    },
    "PILOT_MIN_CATEGORY_PROMPTS": {
        "kind": "constant",
        "declared_value": 3,
        "consumed_by": ["endpoint:check_floor_layer_coverage"],
    },
    "INTERACTION_MIN_EFFECT": {
        "kind": "derived_field",
        "declared_value": None,
        "consumed_by": ["endpoint:derive_pilot_thresholds"],
    },
    # Open item 8, decided 2026-07-27: Stage 2's construction, unchanged. The
    # token embedding at the measured position decoded through final norm and
    # lm_head -- the surface prompt with no transformer computation applied,
    # which is what "transporting nothing" means. Keeping it identical also
    # keeps Stage 2's NTA values usable as a magnitude reference.
    "PROMPT_ONLY_CONSTRUCTION": {
        "kind": "constant",
        "declared_value": "input_embedding_decoded",
        "consumed_by": ["endpoint:nta"],
    },
    "TARGET_SOURCE": {
        "kind": "constant",
        "declared_value": "model_argmax",
        "consumed_by": ["endpoint:target_rank1"],
    },
    "PRIMARY_FLOOR_ID": {
        "kind": "constant",
        "declared_value": "input_embedding_decoded",
        "consumed_by": ["endpoint:dual_floor_nta"],
    },
    "SENSITIVITY_FLOOR_ID": {
        "kind": "constant",
        "declared_value": "layer0_residual_decoded",
        "consumed_by": ["endpoint:dual_floor_nta"],
    },
    "NTA_MIN_DENOMINATOR": {
        "kind": "derived_field",
        "declared_value": None,
        "consumed_by": ["endpoint:nta", "endpoint:derive_nta_min_denominator"],
    },
    "TOP_K": {
        "kind": "constant",
        "declared_value": 10,
        "consumed_by": ["preflight:ratification"],
    },
    # -- construction constants ----------------------------------------------
    "WRONG_ACTIVATION_ASSIGNMENT_COUNT": {
        "kind": "constant",
        "declared_value": 8,
        "consumed_by": [
            "preflight:crossing_registry",
            "endpoint:materialize_crossed_factorials",
        ],
    },
    "BROKEN_MAP_DRAW_COUNT": {
        "kind": "constant",
        "declared_value": 8,
        "consumed_by": [
            "preflight:crossing_registry",
            "endpoint:materialize_crossed_factorials",
        ],
    },
    "UNIQUE_READOUT_COUNT": {
        "kind": "constant",
        "declared_value": 81,
        "consumed_by": ["endpoint:materialize_crossed_factorials"],
    },
    "LOGICAL_COMBINATION_COUNT": {
        "kind": "constant",
        "declared_value": 64,
        "consumed_by": ["endpoint:materialize_crossed_factorials"],
    },
    "BROKEN_MAP_DRAWS": {
        "kind": "constant",
        "declared_value": _CROSSING_VECTORS["maps"],
        "consumed_by": [
            "preflight:crossing_registry",
            "endpoint:build_fit_broken_maps",
        ],
    },
    "BROKEN_MAP_SPECTRUM_RTOL": {
        "kind": "constant",
        "declared_value": 1e-5,
        "consumed_by": ["endpoint:singular_spectrum_evidence"],
    },
    "BROKEN_MAP_SPECTRUM_ATOL": {
        "kind": "constant",
        "declared_value": 1e-6,
        "consumed_by": ["endpoint:singular_spectrum_evidence"],
    },
    "WRONG_ACTIVATION_ASSIGNMENTS": {
        "kind": "constant",
        "declared_value": _CROSSING_VECTORS["donors"],
        "consumed_by": [
            "preflight:crossing_registry",
            "endpoint:select_wrong_activation",
        ],
    },
    # -- preflight constants -------------------------------------------------
    "PILOT_AUTHORIZED": {
        "kind": "constant",
        "declared_value": False,
        "consumed_by": ["preflight:ratification"],
    },
    "PILOT_PROTOCOL_RATIFIED": {
        "kind": "constant",
        "declared_value": False,
        "consumed_by": ["preflight:ratification"],
    },
    "DECODE_PARITY_TOL": {
        "kind": "constant",
        "declared_value": 1e-5,
        "consumed_by": ["preflight:tensor_contracts"],
    },
    "THRESHOLDS_RATIFIED": {
        "kind": "constant",
        "declared_value": False,
        "consumed_by": ["preflight:ratification"],
    },
    "MAX_PROMPT_TOKENS": {
        "kind": "constant",
        "declared_value": 128,
        "consumed_by": ["preflight:manifest"],
    },
    "STAGE2B_N_PROMPTS": {
        "kind": "constant",
        "declared_value": 200,  # Q1
        "consumed_by": ["preflight:manifest"],
    },
    "STAGE2B_N_CATEGORIES": {
        "kind": "constant",
        "declared_value": 5,  # Q1
        "consumed_by": ["preflight:manifest"],
    },
    "STAGE1_PROMPT_SHA256": {
        "kind": "constant",
        "declared_value": (
            "daeaa63881dc0f58be689307a81b1fbc347674424f1cae45819f82372804f5a6"
        ),
        "consumed_by": ["preflight:manifest"],
    },
    "STAGE2_MANIFEST_DIGESTS": {
        "kind": "constant",
        "declared_value": "tests/jspace/fixtures/stage2_manifest_digests.json",
        "consumed_by": ["preflight:manifest"],
    },
    "MIN_VRAM_GIB": {
        "kind": "constant",
        "declared_value": 14.0,
        "consumed_by": ["preflight:environment"],
    },
    "JLENS_COMMIT": {
        "kind": "constant",
        "declared_value": "581d398613e5602a5af361e1c34d3a92ea82ba8e",
        "consumed_by": ["preflight:environment"],
    },
    "MODEL_ID": {
        "kind": "constant",
        "declared_value": "Qwen/Qwen3-1.7B",
        "consumed_by": ["preflight:environment"],
    },
    "MODEL_REVISION": {
        "kind": "constant",
        "declared_value": "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e",
        "consumed_by": ["preflight:environment"],
    },
    "LENS_REPO": {
        "kind": "constant",
        "declared_value": "neuronpedia/jacobian-lens",
        "consumed_by": ["preflight:environment"],
    },
    "LENS_REVISION": {
        "kind": "constant",
        "declared_value": "a4114d7752d11eb546e6cf372213d7e75526d3a1",
        "consumed_by": ["preflight:environment"],
    },
    "LENS_FILE": {
        "kind": "constant",
        "declared_value": (
            "qwen3-1.7b/jlens/Salesforce-wikitext/Qwen3-1.7B_jacobian_lens.pt"
        ),
        "consumed_by": ["preflight:environment"],
    },
    "EXPECTED_LENS_SHA256": {
        "kind": "constant",
        "declared_value": (
            "6fcc79011bd921ffd87612255e2e99950a124fa519470ee44ebaf161c39be9d6"
        ),
        "consumed_by": ["preflight:environment"],
    },
    "EXPECTED_MODEL_D_MODEL": {
        "kind": "constant",
        "declared_value": 2048,
        "consumed_by": ["preflight:environment"],
    },
    "EXPECTED_MODEL_N_LAYERS": {
        "kind": "constant",
        "declared_value": 28,
        "consumed_by": ["preflight:environment"],
    },
    "SELECTED_LAYERS": {
        "kind": "constant",
        "declared_value": [6, 13, 20, 26],  # Q2
        "consumed_by": ["preflight:environment"],
    },
    "POSITIONS": {
        "kind": "constant",
        "declared_value": [-2],  # Q2
        "consumed_by": ["preflight:environment"],
    },
    # -- derived fields ------------------------------------------------------
    # Registered because the preregistration describes them as decision-relevant.
    # A registry covering only constants would have missed Stage 2's fourth
    # orphan, which was a computed field: output_argmax_rank_* was computed,
    # stored, and read by no gate while the checklist called it ratified.
    "nta_jacobian": {
        "kind": "derived_field",
        "declared_value": None,
        "consumed_by": ["endpoint:assemble_factorial_cells"],
    },
    "nta_fit_broken_same_layer": {
        "kind": "derived_field",
        "declared_value": None,
        "consumed_by": ["endpoint:assemble_factorial_cells"],
    },
    "target_id": {
        "kind": "derived_field",
        "declared_value": None,
        "consumed_by": ["endpoint:target_rank1"],
    },
}

_RATIFIED_REGISTRY_ENTRIES = {
    "TARGET_SOURCE",
    "PROMPT_ONLY_CONSTRUCTION",
    "PRIMARY_FLOOR_ID",
    "SENSITIVITY_FLOOR_ID",
    "BOOTSTRAP_CI_LEVEL",
    "UNCERTAINTY_METHOD",
    "RESAMPLING_UNIT",
    "INTERVAL_METHOD",
    "BOOTSTRAP_ITERATIONS",
    "BOOTSTRAP_SEED",
    "AGGREGATION_RULE",
    "THRESHOLD_DERIVATION_RULES",
    "MULTIPLICITY_RULE",
    "NTA_GUARD_QUANTILE",
    "NTA_GUARD_QUANTILE_METHOD",
    "PILOT_MIN_LAYER_PROMPTS",
    "PILOT_MIN_CATEGORY_PROMPTS",
    "WRONG_ACTIVATION_ASSIGNMENT_COUNT",
    "BROKEN_MAP_DRAW_COUNT",
    "UNIQUE_READOUT_COUNT",
    "LOGICAL_COMBINATION_COUNT",
    "BROKEN_MAP_DRAWS",
    "WRONG_ACTIVATION_ASSIGNMENTS",
}
_UNRATIFIED_REGISTRY_ENTRIES = {
    "PILOT_AUTHORIZED",
    "PILOT_PROTOCOL_RATIFIED",
    "THRESHOLDS_RATIFIED",
}
for _name, _entry in INITIAL_REGISTRY.items():
    if _entry["kind"] == "derived_field":
        _entry["status"] = "derived"
    elif _name in _RATIFIED_REGISTRY_ENTRIES:
        _entry["status"] = "ratified"
    elif _name in _UNRATIFIED_REGISTRY_ENTRIES:
        _entry["status"] = "unratified"
    else:
        # Historical pins/defaults are implemented, not retroactively ratified.
        _entry["status"] = "implemented"


#: What each non-gate consumer actually reads.
#:
#: This exists because the reverse check was silently inert in the shipped
#: configuration: ``GATES`` is a tuple, so the ``isinstance(gates, Mapping)``
#: branch never ran, and ``consumer_reads`` defaulted to ``None``. The registry
#: therefore proved only forward and referential consistency while its contract
#: promised all three. Declaring the read edges here makes the reverse sweep run
#: by default rather than only when a caller remembers to supply it.
CONSUMER_READS: dict[str, tuple[str, ...]] = {
    "preflight:tensor_contracts": ("DECODE_PARITY_TOL", "EXPECTED_MODEL_D_MODEL"),
    "preflight:ratification": (
        "STAGE1_RERUN_NOISE_MAX_ABS_LOGIT_DIFF",
        "BOOTSTRAP_CI_LEVEL",
        "UNCERTAINTY_METHOD",
        "RESAMPLING_UNIT",
        "INTERVAL_METHOD",
        "BOOTSTRAP_ITERATIONS",
        "BOOTSTRAP_SEED",
        "AGGREGATION_RULE",
        "THRESHOLD_DERIVATION_RULES",
        "MULTIPLICITY_RULE",
        "TOP_K",
        "PILOT_AUTHORIZED",
        "PILOT_PROTOCOL_RATIFIED",
        "THRESHOLDS_RATIFIED",
    ),
    "preflight:crossing_registry": (
        "WRONG_ACTIVATION_ASSIGNMENT_COUNT",
        "BROKEN_MAP_DRAW_COUNT",
        "BROKEN_MAP_DRAWS",
        "WRONG_ACTIVATION_ASSIGNMENTS",
    ),
    "preflight:manifest": (
        "MAX_PROMPT_TOKENS",
        "STAGE2B_N_PROMPTS",
        "STAGE2B_N_CATEGORIES",
        "STAGE1_PROMPT_SHA256",
        "STAGE2_MANIFEST_DIGESTS",
    ),
    "preflight:environment": (
        "MIN_VRAM_GIB",
        "JLENS_COMMIT",
        "MODEL_ID",
        "MODEL_REVISION",
        "LENS_REPO",
        "LENS_REVISION",
        "LENS_FILE",
        "EXPECTED_LENS_SHA256",
        "EXPECTED_MODEL_D_MODEL",
        "EXPECTED_MODEL_N_LAYERS",
        "SELECTED_LAYERS",
        "POSITIONS",
    ),
    "endpoint:nta": ("NTA_MIN_DENOMINATOR", "PROMPT_ONLY_CONSTRUCTION"),
    "endpoint:target_rank1": ("TARGET_SOURCE", "target_id"),
    "endpoint:dual_floor_nta": (
        "PRIMARY_FLOOR_ID",
        "SENSITIVITY_FLOOR_ID",
    ),
    "endpoint:materialize_crossed_factorials": (
        "WRONG_ACTIVATION_ASSIGNMENT_COUNT",
        "BROKEN_MAP_DRAW_COUNT",
        "UNIQUE_READOUT_COUNT",
        "LOGICAL_COMBINATION_COUNT",
    ),
    "endpoint:assemble_factorial_cells": (
        "nta_jacobian",
        "nta_fit_broken_same_layer",
    ),
    "endpoint:build_fit_broken_maps": ("BROKEN_MAP_DRAWS",),
    "endpoint:singular_spectrum_evidence": (
        "BROKEN_MAP_SPECTRUM_RTOL",
        "BROKEN_MAP_SPECTRUM_ATOL",
    ),
    "endpoint:select_wrong_activation": ("WRONG_ACTIVATION_ASSIGNMENTS",),
    "endpoint:derive_nta_min_denominator": (
        "NTA_MIN_DENOMINATOR",
        "NTA_GUARD_QUANTILE",
        "NTA_GUARD_QUANTILE_METHOD",
        "THRESHOLD_DERIVATION_RULES",
    ),
    "endpoint:check_floor_layer_coverage": (
        "PILOT_MIN_LAYER_PROMPTS",
        "PILOT_MIN_CATEGORY_PROMPTS",
    ),
    "endpoint:category_stratified_prompt_interval": (
        "BOOTSTRAP_CI_LEVEL",
        "BOOTSTRAP_ITERATIONS",
        "BOOTSTRAP_SEED",
    ),
    "endpoint:product_weight_interval": (
        "BOOTSTRAP_CI_LEVEL",
        "BOOTSTRAP_ITERATIONS",
        "BOOTSTRAP_SEED",
    ),
    "endpoint:derive_pilot_thresholds": (
        "SPEC_MIN_EFFECT",
        "INTERACTION_MIN_EFFECT",
        "THRESHOLD_DERIVATION_RULES",
    ),
}

# Populated only after scientific gate composition is separately ratified.
GATE_READS: dict[str, str] = {}


def _resolve(
    consumer: str,
    gates: Iterable[str],
    preflight_checks: Iterable[str],
    endpoint_fns: Iterable[str],
) -> bool:
    """Resolve one ``consumed_by`` name against its namespace.

    Matching is exact.  No case folding, no whitespace normalization, no fuzzy
    match: a check that accepts ``"H1 specificity"`` for ``"h1_specificity"``
    cannot tell a real linkage from a typo, which is the whole thing it is for.
    """
    namespace, sep, base = consumer.partition(":")
    if not sep:
        return consumer in gates
    if namespace == "preflight":
        return base in preflight_checks
    if namespace == "endpoint":
        return base in endpoint_fns
    return False


def check_constant_registry(
    registry: Mapping[str, Mapping[str, Any]],
    gates: Mapping[str, Any] | Sequence[str],
    preflight_checks: Sequence[str] = PREFLIGHT_CHECKS,
    endpoint_fns: Sequence[str] = ENDPOINT_FNS,
    consumer_reads: Mapping[str, Sequence[str]] | None = None,
) -> None:
    """Assert the declared-means-consumed linkage in all three directions.

    Forward (``orphaned_constant``)
        Every registry entry has at least one consumer.  Catches a declared
        constant that no gate reads -- Stage 2's ``INFERENCE_SEEDS``, which
        claimed two seeds while only seed 0 ever ran.

    Reverse (``unregistered_constant``)
        Every constant a gate reads is registered.  Catches a value reaching a
        decision without being preregistered, which is the worse of the two.

    Referential (``phantom_consumer``)
        Every consumer named actually exists.  Without it, a typo passes the
        forward check and then writes a ``registry`` block into the artifact
        asserting a linkage that was never built -- the registry manufacturing
        exactly the false assurance it exists to prevent.
    """
    gate_names = set(gates)
    known_checks = set(preflight_checks)
    known_fns = set(endpoint_fns)

    for name, entry in registry.items():
        consumers = entry.get("consumed_by") or []
        if not consumers:
            raise PreflightError(
                "orphaned_constant",
                f"{name!r} is declared but no gate or check consumes it",
                constant=name,
            )
        for consumer in consumers:
            if not _resolve(consumer, gate_names, known_checks, known_fns):
                raise PreflightError(
                    "phantom_consumer",
                    f"{name!r} names consumer {consumer!r}, which does not exist",
                    constant=name,
                    consumer=consumer,
                )

        kind = entry.get("kind")
        value = entry.get("declared_value")
        status = entry.get("status")
        allowed_statuses = {"ratified", "unratified", "implemented", "derived"}
        if status not in allowed_statuses:
            raise PreflightError(
                "invalid_registry_status",
                f"{name!r} has unknown or missing registry status {status!r}",
                constant=name,
                status=status,
            )
        inconsistent = (
            (kind == "derived_field" and status != "derived")
            or (kind == "constant" and status == "derived")
            or (status == "ratified" and value is None)
            or (
                status == "unratified"
                and value is not None
                and value is not False
                and value != []
            )
        )
        if inconsistent:
            raise PreflightError(
                "inconsistent_registry_status",
                f"{name!r} status {status!r} is inconsistent with {kind!r} value {value!r}",
                constant=name,
                kind=kind,
                status=status,
                declared_value=value,
            )

    if isinstance(gates, Mapping):
        for gate_name, gate in gates.items():
            read = gate.get("constant_name") if isinstance(gate, Mapping) else None
            if read is not None and read not in registry:
                raise PreflightError(
                    "unregistered_constant",
                    f"gate {gate_name!r} reads unregistered constant {read!r}",
                    gate=gate_name,
                    constant=read,
                )

    # The reverse check must cover all three namespaces, not just gates.  A
    # preflight check or endpoint function reading an undeclared constant is the
    # same defect as a gate doing it, and restricting the sweep to gates would
    # leave the larger surface unguarded -- most registered constants here are
    # read by preflight, not by a gate.
    # Defaults to the declared read edges rather than to nothing. An empty
    # default made the reverse guarantee vacuous in exactly the configuration
    # the project ships.
    if consumer_reads is None:
        consumer_reads = {
            **CONSUMER_READS,
            **{gate: (constant,) for gate, constant in GATE_READS.items()},
        }
    for consumer, reads in consumer_reads.items():
        for read in reads:
            if read not in registry:
                raise PreflightError(
                    "unregistered_constant",
                    f"consumer {consumer!r} reads unregistered constant {read!r}",
                    consumer=consumer,
                    constant=read,
                )


def emit_registry_record(
    registry: Mapping[str, Mapping[str, Any]],
    gates: Mapping[str, Any] | Sequence[str],
) -> dict[str, Any]:
    """Return the ``registry`` block for the aggregate artifact.

    Pure; no I/O.  The check passing leaves no trace by itself -- this record is
    the trace.  It is what lets a later reader verify the linkage without
    rerunning anything, which is precisely what Stage 2's artifacts could not
    support: its audit had to read notebook source to establish what the gates
    actually did.
    """
    return {
        "entries": [
            {
                "name": name,
                "kind": entry.get("kind"),
                "declared_value": entry.get("declared_value"),
                "status": entry.get("status"),
                "consumed_by": list(entry.get("consumed_by") or []),
            }
            for name, entry in sorted(registry.items())
        ],
        "gates_declared": sorted(gates),
        "preflight_checks_declared": sorted(PREFLIGHT_CHECKS),
        "endpoint_fns_declared": sorted(ENDPOINT_FNS),
    }


# --------------------------------------------------------------------------
# US3: the checks themselves.  Each takes already-extracted metadata, never a
# live tensor, so all of this runs on a machine with no GPU and no jlens.
# --------------------------------------------------------------------------


def check_tensor_contracts(observed: Mapping[str, Any], d_model: int = 2048) -> None:
    """Assert the shape/dtype/device/parity contract before any measurement.

    The dtype requirement is load-bearing rather than hygienic.
    ``JacobianLens.transport`` moves the Jacobian to the residual's *device* but
    does not cast its *dtype* (``jlens/lens.py:142``), and Stage 2b bypasses
    ``lens.apply`` for three of the four factorial cells — losing the ``.float()``
    that path applied at ``lens.py:206``.  A half-precision residual would hit a
    dtype-mismatched matmul that surfaces only under live GPU execution.

    ``apply`` forces ``.float().cpu()`` on its returned logits while a direct
    ``unembed`` call does not (``jlens/hf.py:166-174``), so readouts built the two
    ways come back on different devices and the first cross-readout subtraction
    raises.  Decode parity on a fixed probe is what proves all readouts share one
    vocabulary basis; without it, comparisons across readouts are meaningless
    regardless of the statistics.
    """
    checks: list[tuple[str, Any, Any, str]] = [
        (
            "residual_shape",
            observed.get("residual_shape"),
            (d_model,),
            "shape_mismatch",
        ),
        (
            "residual_dtype",
            observed.get("residual_dtype"),
            "torch.float32",
            "dtype_mismatch",
        ),
        (
            "jacobian_shape",
            observed.get("jacobian_shape"),
            (d_model, d_model),
            "shape_mismatch",
        ),
        (
            "jacobian_dtype",
            observed.get("jacobian_dtype"),
            "torch.float32",
            "dtype_mismatch",
        ),
        ("readout_device", observed.get("readout_device"), "cpu", "device_mismatch"),
    ]
    for key, actual, expected, code in checks:
        normalized = tuple(actual) if isinstance(actual, list) else actual
        if normalized != expected:
            raise PreflightError(
                code,
                f"{key} is {actual!r}, expected {expected!r}",
                field=key,
                observed=actual,
                expected=expected,
            )

    tol = observed.get("decode_parity_tol", 1e-5)
    parity = observed.get("decode_parity_max_abs")
    if parity is None or parity > tol:
        raise PreflightError(
            "decode_parity",
            f"decode parity {parity!r} exceeds tolerance {tol!r}; readouts do not "
            "share one vocabulary basis",
            observed=parity,
            tolerance=tol,
        )

    if observed.get("rank_parity_verified") is not True:
        raise PreflightError(
            "rank_parity",
            "rank parity against the pinned reference was not explicitly verified",
            observed=observed.get("rank_parity_verified"),
            expected=True,
        )

    expected_floors = {
        "primary_floor_id": "input_embedding_decoded",
        "sensitivity_floor_id": "layer0_residual_decoded",
    }
    for field, expected in expected_floors.items():
        actual = observed.get(field)
        if actual != expected:
            raise PreflightError(
                "floor_identity",
                f"{field} is {actual!r}, expected {expected!r}",
                field=field,
                observed=actual,
                expected=expected,
            )

    softcap = observed.get("logit_softcapping")
    if softcap is not None:
        raise PreflightError(
            "unexpected_softcapping",
            f"final logit softcapping is active ({softcap!r}); it would change "
            "every rank statistic",
            observed=softcap,
        )


def check_crossing_registry(
    donor_assignments: Sequence[Mapping[str, Any]],
    map_draws: Sequence[Mapping[str, Any]],
) -> None:
    """Require exact SHA-derived identities for the ratified 8x8 crossing."""
    if len(donor_assignments) != 8 or len(map_draws) != 8:
        raise PreflightError(
            "crossing_registry_size",
            "crossing requires exactly eight donor assignments and eight map draws",
            donor_count=len(donor_assignments),
            map_count=len(map_draws),
        )
    expected_vectors = derive_crossing_seed_vectors()
    for kind, entries, expected in (
        ("donor", donor_assignments, expected_vectors["donors"]),
        ("map", map_draws, expected_vectors["maps"]),
    ):
        if not all(isinstance(entry, Mapping) for entry in entries):
            raise PreflightError(
                "crossing_registry_identity",
                f"every {kind} crossing entry must be an object",
            )
        identities = [entry.get("id") for entry in entries]
        seeds = [entry.get("seed") for entry in entries]
        if not all(isinstance(value, str) and value for value in identities):
            raise PreflightError(
                "crossing_registry_identity",
                f"every {kind} crossing entry needs a non-empty string id",
            )
        if not all(
            isinstance(value, int) and not isinstance(value, bool) for value in seeds
        ):
            raise PreflightError(
                "crossing_registry_seed",
                f"every {kind} crossing entry needs an integer seed",
            )
        if len(set(identities)) != 8 or len(set(seeds)) != 8:
            raise PreflightError(
                "crossing_registry_duplicate",
                f"{kind} crossing IDs and seeds must each be unique",
            )
        if list(entries) != expected:
            raise PreflightError(
                "crossing_registry_derivation",
                f"{kind} crossing entries do not match the ratified SHA-256 derivation",
                observed=list(entries),
                expected=expected,
            )


def _authorization_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate JSON keys instead of accepting the last value silently."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key {key!r}")
        result[key] = value
    return result


def _require_exact_fields(
    value: Any,
    expected: set[str],
    *,
    context: str,
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise PreflightError(
            "authorization_record_schema",
            f"{context} must be a JSON object",
            context=context,
        )
    observed = set(value)
    if observed != expected:
        raise PreflightError(
            "authorization_record_schema",
            f"{context} fields do not match the contract",
            context=context,
            missing=sorted(expected - observed),
            unknown=sorted(observed - expected),
        )
    return value


def load_pilot_authorization_record(
    path: str | Path,
    *,
    approved_record_sha256: str,
    expected_pilot_view_sha256: str,
    observed_code_bundle_sha256: str,
) -> dict[str, Any]:
    """Load one content-addressed, pilot-only authorization record.

    The record is external to the notebook, so an authorization transition never
    requires editing executable source. The independently supplied approved digest
    binds both the filename and exact bytes, while the scope block keeps
    confirmation access and artifact transfer false.
    """
    record_path = Path(path)
    if re.fullmatch(r"[0-9a-f]{64}", approved_record_sha256) is None:
        raise PreflightError(
            "authorization_record_approval",
            "independently approved authorization SHA-256 must be 64 lowercase hex",
            observed=approved_record_sha256,
        )
    match = _PILOT_AUTHORIZATION_FILENAME.fullmatch(record_path.name)
    if match is None:
        raise PreflightError(
            "authorization_record_name",
            "pilot authorization filename must contain its lowercase SHA-256",
            path=str(record_path),
        )
    if match.group(1) != approved_record_sha256:
        raise PreflightError(
            "authorization_record_approval",
            "authorization filename does not match the independently approved digest",
            approved=approved_record_sha256,
            observed=match.group(1),
        )
    try:
        payload = record_path.read_bytes()
    except OSError as exc:
        raise PreflightError(
            "authorization_record_unreadable",
            f"pilot authorization record cannot be read: {exc}",
            path=str(record_path),
        ) from exc
    observed_sha256 = hashlib.sha256(payload).hexdigest()
    if observed_sha256 != approved_record_sha256:
        raise PreflightError(
            "authorization_record_digest",
            "pilot authorization record bytes do not match the approved digest",
            expected=approved_record_sha256,
            observed=observed_sha256,
        )
    try:
        record = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_authorization_object,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise PreflightError(
            "authorization_record_json",
            f"pilot authorization record is not unambiguous UTF-8 JSON: {exc}",
        ) from exc

    root = _require_exact_fields(
        record,
        {"schema", "run_mode", "decision", "scope", "source", "registry_updates"},
        context="authorization record",
    )
    if root["schema"] != PILOT_AUTHORIZATION_SCHEMA or root["run_mode"] != "pilot":
        raise PreflightError(
            "authorization_record_scope",
            "authorization record must use the pilot schema and pilot run mode",
            schema=root["schema"],
            run_mode=root["run_mode"],
        )

    decision = _require_exact_fields(
        root["decision"],
        {"authority", "authorized_at_utc", "instruction", "instruction_sha256"},
        context="authorization record decision",
    )
    for name in ("authority", "authorized_at_utc", "instruction"):
        if not isinstance(decision[name], str) or not decision[name].strip():
            raise PreflightError(
                "authorization_record_decision",
                f"decision field {name!r} must be a non-empty string",
                field=name,
            )
    if decision["authority"] != "Dr. Mani":
        raise PreflightError(
            "authorization_record_authority",
            "pilot execution authority must be exactly 'Dr. Mani'",
            observed=decision["authority"],
        )
    try:
        datetime.strptime(decision["authorized_at_utc"], "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise PreflightError(
            "authorization_record_decision",
            "authorized_at_utc must use second-resolution UTC RFC 3339 form",
            observed=decision["authorized_at_utc"],
        ) from None
    instruction_sha256 = hashlib.sha256(
        (decision["instruction"] + "\n").encode("utf-8")
    ).hexdigest()
    if decision["instruction_sha256"] != instruction_sha256:
        raise PreflightError(
            "authorization_record_decision",
            "decision instruction does not match its recorded SHA-256",
            expected=instruction_sha256,
            observed=decision["instruction_sha256"],
        )

    scope = _require_exact_fields(
        root["scope"],
        {
            "pilot_view_sha256",
            "confirmation_access_authorized",
            "artifact_transfer_authorized",
        },
        context="authorization record scope",
    )
    if scope["pilot_view_sha256"] != expected_pilot_view_sha256:
        raise PreflightError(
            "authorization_record_pilot_view",
            "authorization record targets a different pilot view",
            expected=expected_pilot_view_sha256,
            observed=scope["pilot_view_sha256"],
        )
    if (
        scope["confirmation_access_authorized"] is not False
        or scope["artifact_transfer_authorized"] is not False
    ):
        raise PreflightError(
            "authorization_record_boundary",
            "pilot authorization cannot grant confirmation access or artifact transfer",
        )

    source = _require_exact_fields(
        root["source"],
        {"notebook_sha256", "code_bundle_sha256"},
        context="authorization record source",
    )
    notebook_sha256 = source["notebook_sha256"]
    if (
        not isinstance(notebook_sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", notebook_sha256) is None
    ):
        raise PreflightError(
            "authorization_record_source",
            "authorization record notebook_sha256 is not a lowercase SHA-256",
            field="notebook_sha256",
            approved=notebook_sha256,
        )
    approved_bundle_sha256 = source["code_bundle_sha256"]
    if (
        not isinstance(approved_bundle_sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", approved_bundle_sha256) is None
        or approved_bundle_sha256 != observed_code_bundle_sha256
    ):
        raise PreflightError(
            "authorization_record_source",
            "authorization record code_bundle_sha256 does not match the observed bundle bytes",
            field="code_bundle_sha256",
            approved=approved_bundle_sha256,
            observed=observed_code_bundle_sha256,
        )

    updates = _require_exact_fields(
        root["registry_updates"],
        set(root["registry_updates"])
        if isinstance(root["registry_updates"], Mapping)
        else set(),
        context="authorization record registry_updates",
    )
    if not updates:
        raise PreflightError(
            "authorization_record_schema",
            "authorization record registry_updates must not be empty",
        )
    for name, update in updates.items():
        _require_exact_fields(
            update,
            {"declared_value", "status"},
            context=f"authorization record registry_updates.{name}",
        )
    return {**root, "_record_sha256": observed_sha256}


def materialize_pilot_authorization(
    record: Mapping[str, Any],
    registry: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Apply a complete pilot decision record without mutating the base registry."""
    required_updates = {"PILOT_AUTHORIZED", "PILOT_PROTOCOL_RATIFIED"}
    updates = record.get("registry_updates")
    if not isinstance(updates, Mapping) or set(updates) != required_updates:
        observed = set(updates) if isinstance(updates, Mapping) else set()
        raise PreflightError(
            "authorization_record_incomplete",
            "pilot authorization may update exactly the protocol and execution flags",
            missing=sorted(required_updates - observed),
            unknown=sorted(observed - required_updates),
        )

    resolved = {name: dict(entry) for name, entry in registry.items()}
    check_constant_registry(resolved, GATES)
    check_crossing_registry(
        resolved["WRONG_ACTIVATION_ASSIGNMENTS"]["declared_value"],
        resolved["BROKEN_MAP_DRAWS"]["declared_value"],
    )
    for name in sorted(required_updates):
        base = resolved.get(name)
        update = updates[name]
        if base is None or base.get("status") != "unratified":
            raise PreflightError(
                "authorization_record_registry",
                f"{name!r} is not an unresolved registry entry",
                constant=name,
            )
        if not isinstance(update, Mapping) or set(update) != {
            "declared_value",
            "status",
        }:
            raise PreflightError(
                "authorization_record_schema",
                f"registry update {name!r} must contain declared_value and status",
                constant=name,
            )
        if update.get("status") != "ratified":
            raise PreflightError(
                "authorization_record_unratified",
                f"registry update {name!r} is not explicitly ratified",
                constant=name,
            )
        resolved[name] = {
            **base,
            "declared_value": update.get("declared_value"),
            "status": "ratified",
        }

    configuration = {
        name: resolved[name]["declared_value"]
        for name in (
            "PILOT_AUTHORIZED",
            "PILOT_PROTOCOL_RATIFIED",
            "THRESHOLDS_RATIFIED",
            "BROKEN_MAP_DRAWS",
            "WRONG_ACTIVATION_ASSIGNMENTS",
        )
    }
    return configuration, resolved


def check_ratification(
    thresholds: Mapping[str, Any],
    registry: Mapping[str, Mapping[str, Any]] | None = None,
    *,
    mode: str = "confirmatory",
) -> None:
    """Fail closed unless the selected run mode is explicitly and fully ratified."""
    if mode not in {"pilot", "confirmatory"}:
        raise PreflightError(
            "invalid_run_mode",
            f"run mode must be 'pilot' or 'confirmatory', got {mode!r}",
            mode=mode,
        )
    if registry is None:
        raise PreflightError(
            "registry_required",
            "pilot and confirmatory execution require an explicitly supplied registry",
            mode=mode,
        )
    check_constant_registry(registry, GATES)

    if mode == "pilot":
        pilot_authorization = registry.get("PILOT_AUTHORIZED", {})
        if (
            thresholds.get("PILOT_AUTHORIZED") is not True
            or pilot_authorization.get("declared_value") is not True
            or pilot_authorization.get("status") != "ratified"
        ):
            raise PreflightError(
                "pilot_not_authorized",
                "PILOT_AUTHORIZED must be explicitly true and ratified in the registry for a pilot run",
            )
        if thresholds.get("PILOT_PROTOCOL_RATIFIED") is not True:
            raise PreflightError(
                "pilot_protocol_not_ratified",
                "PILOT_PROTOCOL_RATIFIED must be explicitly true for a pilot run",
            )
    else:
        threshold_ratification = registry.get("THRESHOLDS_RATIFIED", {})
        if (
            thresholds.get("THRESHOLDS_RATIFIED") is not True
            or threshold_ratification.get("declared_value") is not True
            or threshold_ratification.get("status") != "ratified"
        ):
            raise PreflightError(
                "not_ratified",
                "THRESHOLDS_RATIFIED must be explicitly true and ratified in the registry for confirmatory execution",
            )

    donors = thresholds.get("WRONG_ACTIVATION_ASSIGNMENTS", ())
    maps = thresholds.get("BROKEN_MAP_DRAWS", ())
    check_crossing_registry(donors, maps)
    for name, supplied in (
        ("WRONG_ACTIVATION_ASSIGNMENTS", donors),
        ("BROKEN_MAP_DRAWS", maps),
    ):
        entry = registry.get(name, {})
        if entry.get("declared_value") != supplied:
            raise PreflightError(
                "registry_value_mismatch",
                f"{name!r} differs between authorization and registry",
                constant=name,
            )

    required_ratification = (
        {"PILOT_AUTHORIZED", "PILOT_PROTOCOL_RATIFIED"}
        if mode == "pilot"
        else {"THRESHOLDS_RATIFIED"}
    )
    for name in sorted(required_ratification):
        entry = registry.get(name, {})
        value = entry.get("declared_value")
        if value is None:
            raise PreflightError(
                "unset_constant",
                f"{name!r} remains unset for {mode} execution",
                constant=name,
            )
        if entry.get("status") != "ratified":
            raise PreflightError(
                "unratified_constant",
                f"{name!r} has a value but is not explicitly ratified",
                constant=name,
                status=entry.get("status"),
            )

    expected_bootstrap_seed = {
        key: value
        for key, value in bootstrap_rng_identity(
            "pilot" if mode == "pilot" else "confirmatory",
            numpy_version="runtime-recorded",
        ).items()
        if key != "numpy_version"
    }
    expected_protocol = {
        "BOOTSTRAP_CI_LEVEL": 0.99,
        "UNCERTAINTY_METHOD": {
            "primary": "category_stratified_prompt_percentile",
            "sensitivity": "prompt_donor_map_product_weight_percentile",
        },
        "RESAMPLING_UNIT": {
            "primary": "prompt_within_category",
            "sensitivity": "prompt_x_donor_assignment_x_map_draw",
        },
        "INTERVAL_METHOD": "two_sided_99_percentile_linear",
        "BOOTSTRAP_ITERATIONS": 20_000,
        "BOOTSTRAP_SEED": expected_bootstrap_seed,
        "AGGREGATION_RULE": "equal_draw_mean_then_equal_category_mean_per_layer",
        "THRESHOLD_DERIVATION_RULES": {
            "SPEC_MIN_EFFECT": "0.5 * primary_floor_correct_effect_mean_by_layer",
            "INTERACTION_MIN_EFFECT": "0.5 * primary_floor_interaction_mean_by_layer",
            "NTA_MIN_DENOMINATOR": "linear_quantile_0.05_of_80_primary_denominators",
        },
        "MULTIPLICITY_RULE": "single_intersection_union_all_components_required",
        "NTA_GUARD_QUANTILE": 0.05,
        "NTA_GUARD_QUANTILE_METHOD": "linear",
        "PILOT_MIN_LAYER_PROMPTS": 18,
        "PILOT_MIN_CATEGORY_PROMPTS": 3,
    }
    for name, expected in expected_protocol.items():
        entry = registry.get(name, {})
        if entry.get("declared_value") != expected or entry.get("status") != "ratified":
            code = (
                "pilot_protocol_incomplete" if mode == "pilot" else "invalid_constant"
            )
            raise PreflightError(
                code,
                f"{name!r} does not match the ratified protocol",
                constant=name,
                observed=entry.get("declared_value"),
                expected=expected,
            )

    if mode == "pilot":
        for name in (
            "NTA_MIN_DENOMINATOR",
            "SPEC_MIN_EFFECT",
            "INTERACTION_MIN_EFFECT",
        ):
            entry = registry.get(name, {})
            if entry.get("kind") != "derived_field" or entry.get("status") != "derived":
                raise PreflightError(
                    "pilot_derived_input",
                    f"{name!r} must remain a derived pilot output",
                    constant=name,
                )
            if entry.get("declared_value") is not None:
                raise PreflightError(
                    "pilot_derived_input",
                    f"{name!r} cannot be supplied before pilot measurement",
                    constant=name,
                    observed=entry.get("declared_value"),
                )
    else:
        nta_guard = registry["NTA_MIN_DENOMINATOR"]["declared_value"]
        if not (
            isinstance(nta_guard, (int, float))
            and not isinstance(nta_guard, bool)
            and math.isfinite(float(nta_guard))
            and float(nta_guard) > 0
        ):
            raise PreflightError(
                "invalid_constant",
                "'NTA_MIN_DENOMINATOR' must be finite and positive",
                constant="NTA_MIN_DENOMINATOR",
                observed=nta_guard,
            )
        for name in ("SPEC_MIN_EFFECT", "INTERACTION_MIN_EFFECT"):
            value = registry[name]["declared_value"]
            if not (
                isinstance(value, Sequence)
                and not isinstance(value, (str, bytes))
                and len(value) == 4
                and all(
                    isinstance(item, (int, float))
                    and not isinstance(item, bool)
                    and math.isfinite(float(item))
                    and float(item) > 0
                    for item in value
                )
            ):
                raise PreflightError(
                    "invalid_constant",
                    f"{name!r} must be four finite positive layer values",
                    constant=name,
                    observed=value,
                )


def installed_vcs_commit(
    direct_url_text: str | None,
    *,
    expected_repo_url: str,
) -> str:
    """Read a full commit from pip-generated ``direct_url.json`` metadata.

    The expected pin is intentionally not accepted as an input or fallback. A
    missing distribution record, non-VCS install, different repository, or
    abbreviated commit makes the installed source identity unverifiable.
    """

    def fail(detail: str) -> NoReturn:
        raise PreflightError(
            "jlens_identity_unverifiable",
            detail,
        )

    if not isinstance(direct_url_text, str):
        fail("installed distribution has no direct_url.json metadata")
    try:
        record = json.loads(direct_url_text)
    except (TypeError, json.JSONDecodeError) as exc:
        fail(f"installed direct_url.json is not valid JSON: {exc}")
    if not isinstance(record, dict):
        fail("installed direct_url.json is not an object")
    if record.get("url") != expected_repo_url:
        fail(
            f"installed source URL is {record.get('url')!r}, expected "
            f"{expected_repo_url!r}"
        )
    vcs_info = record.get("vcs_info")
    if not isinstance(vcs_info, dict) or vcs_info.get("vcs") != "git":
        fail("installed direct_url.json does not record a git VCS source")
    commit = vcs_info.get("commit_id")
    if not (
        isinstance(commit, str)
        and len(commit) == 40
        and all(character in string.hexdigits for character in commit)
    ):
        fail(f"installed VCS commit is not a full 40-hex identity: {commit!r}")
    return commit.lower()


def check_environment(env: Mapping[str, Any], pins: Mapping[str, Any]) -> None:
    """Identity and capacity, asserted against the declared pins.

    ``jlens_commit`` is read back from the *installed* package rather than trusted
    from the install line.  `%pip` does interpolate ``{JLENS_COMMIT}`` — verified
    from IPython's source — but that was established on a machine with no IPython
    installed, so the read-back converts an inference into a measurement for the
    cost of one line.
    """
    version = env.get("python_version")
    if version is None or tuple(version[:2]) < (3, 11):
        raise PreflightError(
            "python_version",
            f"python {version!r} is below the 3.11 floor",
            observed=version,
        )

    if not env.get("cuda_available"):
        raise PreflightError("no_cuda", "CUDA is not available")

    vram, floor = env.get("vram_gib"), pins["MIN_VRAM_GIB"]
    if vram is None or vram < floor:
        raise PreflightError(
            "insufficient_vram",
            f"{vram!r} GiB available, {floor} required",
            observed=vram,
            required=floor,
        )

    installed = env.get("jlens_commit")
    if installed != pins["JLENS_COMMIT"]:
        raise PreflightError(
            "jlens_commit",
            f"installed jlens is {installed!r}, pinned {pins['JLENS_COMMIT']!r}",
            observed=installed,
            expected=pins["JLENS_COMMIT"],
        )

    for key in (
        "MODEL_ID",
        "MODEL_REVISION",
        "LENS_REPO",
        "LENS_REVISION",
        "LENS_FILE",
        "EXPECTED_LENS_SHA256",
        "EXPECTED_MODEL_D_MODEL",
        "EXPECTED_MODEL_N_LAYERS",
    ):
        expected = pins[key]
        actual = env.get(key.lower())
        if actual != expected:
            raise PreflightError(
                "identity_mismatch",
                f"{key} is {actual!r}, pinned {expected!r}",
                field=key,
                observed=actual,
                expected=expected,
            )
