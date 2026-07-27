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
    "CONSUMER_READS",
    "ENDPOINT_FNS",
    "GATES",
    "GATE_READS",
    "INITIAL_REGISTRY",
    "PREFLIGHT_CHECKS",
    "PreflightError",
    "check_constant_registry",
    "check_environment",
    "check_ratification",
    "check_tensor_contracts",
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
        "consumed_by": ["preflight:manifest", "endpoint:allocate_wrong_layers"],
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
        "consumed_by": ["preflight:environment", "endpoint:allocate_wrong_layers"],
    },
    "SELECTED_LAYERS": {
        "kind": "constant",
        "declared_value": [6, 13, 20, 26],  # Q2
        "consumed_by": ["preflight:environment", "endpoint:allocate_wrong_layers"],
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
    "preflight:ratification": ("THRESHOLDS_RATIFIED",),
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
    "endpoint:nta": ("NTA_MIN_DENOMINATOR",),
    "endpoint:target_rank1": ("target_id",),
    "endpoint:build_fit_broken_map": ("BROKEN_MAP_SEED",),
    "endpoint:select_wrong_activation": ("WRONG_ACTIVATION_SEED",),
    "endpoint:allocate_wrong_layers": (
        "WRONG_LAYER_DISTANCES",
        "WRONG_LAYER_SEED",
        "SELECTED_LAYERS",
        "STAGE2B_N_PROMPTS",
        "EXPECTED_MODEL_N_LAYERS",
    ),
}

#: Which constant each gate compares against, so the reverse check covers gates
#: even when ``gates`` is passed as a plain sequence of IDs.
GATE_READS: dict[str, str] = {
    "reproduction": "STAGE1_RERUN_NOISE_MAX_ABS_LOGIT_DIFF",
    "h1_specificity": "SPEC_MIN_EFFECT",
    "h1_interval": "BOOTSTRAP_CI_LEVEL",
    "h2_overlap": "NONREDUNDANCY_MAX_JACCARD",
    "h2_target": "BOOTSTRAP_CI_LEVEL",
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

    softcap = observed.get("logit_softcapping")
    if softcap is not None:
        raise PreflightError(
            "unexpected_softcapping",
            f"final logit softcapping is active ({softcap!r}); it would change "
            "every rank statistic",
            observed=softcap,
        )


def check_ratification(
    thresholds: Mapping[str, Any],
    registry: Mapping[str, Mapping[str, Any]] | None = None,
) -> None:
    """The execution boundary (FR-013, Q10).

    Runs **last**, so every other check is exercisable against the unratified
    configuration the notebook ships in — which is the state every test runs
    against.

    A signed ratification with a still-unset threshold is refused.  Stage 2's
    failure mode was setting a margin without a pilot and then being unable to say
    whether its controls were inseparable or merely under-resolved at that value;
    ``unset_constant`` makes the inverse mistake impossible too, so deferring a
    threshold and signing the ratification are mutually exclusive rather than
    merely discouraged.
    """
    if not thresholds.get("THRESHOLDS_RATIFIED"):
        raise PreflightError(
            "not_ratified",
            "THRESHOLDS_RATIFIED is not set; execution requires Dr. Mani's "
            "ratification of the ten open parameters",
        )

    for name, entry in (registry or {}).items():
        if entry.get("kind") == "constant" and entry.get("declared_value") is None:
            raise PreflightError(
                "unset_constant",
                f"{name!r} is still unset while THRESHOLDS_RATIFIED is true",
                constant=name,
            )


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
