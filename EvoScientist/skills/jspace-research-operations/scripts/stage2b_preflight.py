"""Stage 2b preflight: fail closed before any measurement begins.

Contract: ``specs/001-jspace-stage2b/contracts/preflight-api.md``.

This module MUST import cleanly with neither ``torch``, ``jlens``, nor ``scipy``
installed.  It is the only part of Stage 2b the repo test suite exercises, and the
machine running that suite has no GPU and no interpretability stack.  Every check
therefore takes already-extracted metadata -- shape tuples, dtype *strings*, device
*strings*, digests, floats -- never a live tensor.

That constraint is what makes US3 testable at all.  Stage 2 put the equivalent
logic inside an 18 KB notebook cell, which is why three declared-but-unconsumed
constants survived to an audit: no test could reach any of it.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

__all__ = [
    "ENDPOINT_FNS",
    "GATES",
    "INITIAL_REGISTRY",
    "PREFLIGHT_CHECKS",
    "PreflightError",
    "check_constant_registry",
    "emit_registry_record",
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


# --------------------------------------------------------------------------
# Consumer inventories.
#
# These are declared, never inferred.  A referential check that has to parse
# prose to learn what exists is not a check.  Adding a gate or a function means
# adding it here in the same change -- which is the point, since the alternative
# is a registry whose consumers drift out from under it.
# --------------------------------------------------------------------------

GATES: tuple[str, ...] = (
    "reproduction",
    "h1_specificity",
    "h1_interval",
    "h2_overlap",
    "h2_target",
    "sanity_floor",
)

#: Bare check names.  The implementing function for ``"manifest"`` is
#: ``check_manifest``; the ``check_`` prefix is not part of the identifier, so
#: registry entries read ``preflight:manifest``.  Keeping the prefix out of the
#: name means renaming the function does not silently orphan every constant that
#: pointed at it.
PREFLIGHT_CHECKS: tuple[str, ...] = (
    "tensor_contracts",
    "constant_registry",
    "manifest",
    "ratification",
    "environment",
)

ENDPOINT_FNS: tuple[str, ...] = (
    "target_rank1",
    "nta",
    "verify_rank_parity",
    "build_fit_broken_map",
    "transport_with",
    "select_wrong_activation",
    "allocate_wrong_layers",
    "paired_difference_by_cluster",
    "jaccard_top_k",
    "gate_record",
    "cluster_bootstrap_median",
    "assemble_factorial_cells",
    "compose_decision",
)

#: Constants and derived fields, each mapped to the consumers that read it.
#:
#: ``declared_value`` of ``None`` means deliberately deferred to the Q6 pilot, not
#: forgotten.  :func:`check_ratification` refuses to accept a signed ratification
#: while any registered constant is still ``None``, which makes deferring a
#: threshold and signing the ratification mutually exclusive rather than merely
#: discouraged.
INITIAL_REGISTRY: dict[str, dict[str, Any]] = {
    # -- decision thresholds -------------------------------------------------
    "STAGE1_RERUN_NOISE_MAX_ABS_LOGIT_DIFF": {
        "kind": "constant",
        "declared_value": 0.0,
        "consumed_by": ["reproduction"],
    },
    "SPEC_MIN_EFFECT": {
        "kind": "constant",
        "declared_value": None,  # Q5, pilot-derived
        "consumed_by": ["h1_specificity"],
    },
    "BOOTSTRAP_CI_LEVEL": {
        "kind": "constant",
        "declared_value": 0.99,
        "consumed_by": ["h1_interval", "h2_target"],
    },
    "BOOTSTRAP_ITERATIONS": {
        "kind": "constant",
        "declared_value": 10_000,
        "consumed_by": ["h1_interval", "h2_target", "sanity_floor"],
    },
    "NONREDUNDANCY_MAX_JACCARD": {
        "kind": "constant",
        "declared_value": 0.70,
        "consumed_by": ["h2_overlap"],
    },
    "NTA_MIN_DENOMINATOR": {
        "kind": "constant",
        "declared_value": None,  # Q6, pilot-derived
        "consumed_by": ["endpoint:nta"],
    },
    "TOP_K": {
        "kind": "constant",
        "declared_value": 10,
        "consumed_by": ["h2_overlap", "reproduction"],
    },
    # -- construction constants ----------------------------------------------
    "BROKEN_MAP_SEED": {
        "kind": "constant",
        "declared_value": 20260726,
        "consumed_by": ["endpoint:build_fit_broken_map"],
    },
    "WRONG_LAYER_DISTANCES": {
        "kind": "constant",
        "declared_value": [3, 7, 14],  # Q7
        "consumed_by": ["endpoint:allocate_wrong_layers"],
    },
    # Each stochastic construction gets its own seed rather than sharing one.
    # A shared seed couples three independent draws, so changing the wrong-layer
    # allocation would silently change which broken map was built.
    "WRONG_LAYER_SEED": {
        "kind": "constant",
        "declared_value": 20260727,
        "consumed_by": ["endpoint:allocate_wrong_layers"],
    },
    "WRONG_ACTIVATION_SEED": {
        "kind": "constant",
        "declared_value": 20260728,
        "consumed_by": ["endpoint:select_wrong_activation"],
    },
    # -- preflight constants -------------------------------------------------
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
        "consumed_by": ["preflight:manifest", "reproduction"],
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
        "consumed_by": ["h1_specificity", "h2_target", "sanity_floor"],
    },
    "nta_fit_broken_same_layer": {
        "kind": "derived_field",
        "declared_value": None,
        "consumed_by": ["h1_specificity"],
    },
    "nta_logit_lens": {
        "kind": "derived_field",
        "declared_value": None,
        "consumed_by": ["h2_target"],
    },
    "nta_random_vector": {
        "kind": "derived_field",
        "declared_value": None,
        "consumed_by": ["sanity_floor"],
    },
    "jaccard_top10_jacobian_vs_logit_lens": {
        "kind": "derived_field",
        "declared_value": None,
        "consumed_by": ["h2_overlap"],
    },
    "target_id": {
        "kind": "derived_field",
        "declared_value": None,
        "consumed_by": ["endpoint:target_rank1"],
    },
}


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
    for consumer, reads in (consumer_reads or {}).items():
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
                "consumed_by": list(entry.get("consumed_by") or []),
            }
            for name, entry in sorted(registry.items())
        ],
        "gates_declared": sorted(gates),
        "preflight_checks_declared": sorted(PREFLIGHT_CHECKS),
        "endpoint_fns_declared": sorted(ENDPOINT_FNS),
    }
