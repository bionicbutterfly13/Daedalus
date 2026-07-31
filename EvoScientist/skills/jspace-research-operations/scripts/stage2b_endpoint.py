"""Stage 2b endpoint: normalized target attainment and its supporting statistics.

Contracts: ``specs/001-jspace-stage2b/data-model.md`` §3, ``contracts/artifact-schema.md``.

Like :mod:`stage2b_preflight`, nothing here imports ``torch`` or ``jlens``. The
numeric primitives operate on fixed CPU values without selecting an uncertainty,
threshold, multiplicity, gate-composition, or decision rule.

The endpoint replaces Stage 2's readout-difference metric, which measured how much
two readouts *differ* and therefore had no notion of correct.  A difference metric
cannot distinguish an informative disagreement from an arbitrary one, so Stage 2's
strongest possible conclusion was always non-identity, whatever the data said.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from typing import Any

__all__ = [
    "RANK_CONVENTION",
    "SINGULAR_SPECTRUM_ATOL",
    "SINGULAR_SPECTRUM_RTOL",
    "NTAExcluded",
    "assemble_factorial_cells",
    "build_fit_broken_map",
    "build_fit_broken_maps",
    "dual_floor_nta",
    "materialize_crossed_factorials",
    "nta",
    "rank_score",
    "select_wrong_activation",
    "select_wrong_activation_source",
    "singular_spectrum_evidence",
    "target_decision_sha256",
    "target_rank1",
    "transport_with",
    "verify_rank_parity",
]

#: Recorded in every artifact so the choice is not silently re-decided later.
#:
#: 0-indexed comparison count plus one, using a strict ``>``.  ``jlens.vis._ranks_of``
#: documents 0-indexed with rank 0 = top; the ``+1`` is required because the score
#: takes ``log(rank)`` and ``log(0)`` is undefined.  Strict ``>`` gives the *best*
#: rank among tied tokens; ``>=`` would give the worst.  Ties at the top of a
#: vocab-sized float distribution are rare but not impossible after fp16
#: round-tripping, so the convention is preregistered rather than incidental.
RANK_CONVENTION = "strict_gt_1indexed"
SINGULAR_SPECTRUM_RTOL = 1e-5
SINGULAR_SPECTRUM_ATOL = 1e-6


def target_decision_sha256(target_id: int, target_derivation: Mapping[str, Any]) -> str:
    """Bind a model-argmax decision to retained output-logits evidence."""
    bound = {
        "target_id": target_id,
        **{
            key: value
            for key, value in target_derivation.items()
            if key != "target_decision_sha256"
        },
    }
    payload = json.dumps(
        bound, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    return hashlib.sha256((payload + "\n").encode("ascii")).hexdigest()


class NTAExcluded:
    """A cell excluded by the denominator guard.

    Returned instead of a float so an exclusion can never be silently averaged in
    as a number.  Carries the reason for per-layer exclusion accounting, which the
    artifact reports rather than dropping.
    """

    __slots__ = ("denominator", "reason")

    def __init__(self, reason: str, denominator: float) -> None:
        self.reason = reason
        self.denominator = denominator

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"NTAExcluded(reason={self.reason!r}, denominator={self.denominator!r})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, NTAExcluded)
            and other.reason == self.reason
            and other.denominator == self.denominator
        )


def target_rank1(logits: Sequence[float], target_id: int) -> int:
    """Rank of ``target_id`` in ``logits``, 1-indexed, best-rank-among-ties.

    Computed as a comparison count rather than by sorting.  ``jlens.vis._ranks_of``
    is the reference implementation and is *not* usable here: it chunks along the
    sequence dimension only and still calls ``argsort`` over the full vocabulary
    per chunk, materializing a ``[chunk, vocab]`` rank buffer before gathering the
    target column.  That is a memory optimization, not an algorithmic one.

    This is O(V) time against O(V log V), and one boolean temporary against a full
    int64 buffer.  It is *not* O(1) memory -- the comparison materializes V bytes
    before reducing -- but at vocab 151936 the sort and the scatter buffer are what
    actually hurt.

    FR-010 requires this be verified against the reference on a fixed probe, so an
    optimization cannot silently change the statistic.  See
    :func:`verify_rank_parity`.
    """
    if not 0 <= target_id < len(logits):
        raise IndexError(
            f"target_id {target_id} outside vocabulary of size {len(logits)}"
        )
    target_logit = logits[target_id]
    return sum(1 for value in logits if value > target_logit) + 1


def rank_score(rank: int, vocab_size: int) -> float:
    """``s(r) = -log(rank) / log(V)``.

    Bounded on ``[-1, 0]``: rank 1 gives 0, the worst possible rank gives -1.
    Monotone in rank and insensitive to the long tail of logit magnitudes -- a rank
    statistic rather than a scale-dependent one, so it cannot be moved by a
    readout's overall temperature.
    """
    if rank < 1:
        raise ValueError(f"rank must be 1-indexed and >= 1, got {rank}")
    if vocab_size < 2:
        raise ValueError(f"vocab_size must be >= 2, got {vocab_size}")
    if rank > vocab_size:
        raise ValueError(
            f"rank {rank} exceeds vocab_size {vocab_size}; the claimed [-1, 0] "
            "bound would not hold"
        )
    return -math.log(rank) / math.log(vocab_size)


def nta(
    s_readout: float,
    s_prompt_only: float,
    s_output: float,
    min_denominator: float,
) -> float | NTAExcluded:
    """Normalized target attainment: where a readout sits between floor and ceiling.

    ``prompt_only`` maps to 0 and ``output`` maps to 1 *by construction*.  Stage 2's
    preregistration required, conjunctively, that the Jacobian readout not be within
    rerun noise of either baseline; that clause was never implemented, and the
    2026-07-26 audit found it.  Rather than reinstating it as a fourth gate that
    could be dropped again, the endpoint is *defined* in terms of both baselines: it
    is impossible to compute NTA without them, so the omission is unrepresentable.

    Cells whose denominator falls at or below ``min_denominator`` are excluded, not
    divided.  The output being no better placed than the prompt floor leaves no
    range to be positioned within, and dividing into a near-zero denominator would
    manufacture enormous values out of noise.  Exclusions are a reported quantity.
    """
    denominator = s_output - s_prompt_only
    if denominator <= min_denominator:
        return NTAExcluded("denominator_below_min", denominator)
    return (s_readout - s_prompt_only) / denominator


def dual_floor_nta(
    *,
    s_readout: float,
    s_input_embedding: float,
    s_layer0_residual: float,
    s_output: float,
    min_denominator: float,
) -> dict[str, float | NTAExcluded | None]:
    """Compute the ratified primary and layer-0 sensitivity normalizations.

    The named difference is always sensitivity minus primary.  It is absent when
    either denominator guard excludes its floor; an excluded measurement is not a
    numeric zero and therefore cannot participate in subtraction.
    """
    primary = nta(s_readout, s_input_embedding, s_output, min_denominator)
    sensitivity = nta(s_readout, s_layer0_residual, s_output, min_denominator)
    difference = (
        None
        if isinstance(primary, NTAExcluded) or isinstance(sensitivity, NTAExcluded)
        else sensitivity - primary
    )
    return {
        "input_embedding_decoded": primary,
        "layer0_residual_decoded": sensitivity,
        "sensitivity_minus_primary": difference,
    }


def verify_rank_parity(logits: Sequence[float], target_id: int) -> bool:
    """FR-010: the fast rank must equal a full-sort reference on a fixed probe.

    Returns the boolean recorded as ``contracts.rank_parity_verified``.  This
    exists because an optimization that silently changes a statistic is
    indistinguishable from a correct one until the results are wrong, and Stage 2's
    full-vocabulary ``argsort`` is the thing being replaced.

    The reference mirrors ``jlens.vis._ranks_of`` on unique logits (0-indexed,
    rank 0 = top) with ``+1`` applied. In Colab the notebook repeats the assertion
    against the pinned real ``_ranks_of``. Ties are deliberately outside that
    parity claim: Stage 2b assigns every tied token the best shared rank, while
    jlens' stable full sort assigns token-specific positions.
    """
    order = sorted(range(len(logits)), key=lambda i: logits[i], reverse=True)
    # Apply the preregistered best-rank-among-ties convention to the reference
    # too: take the FIRST position holding the target's logit value, not the
    # target's own position. A stable sort gives tied tokens distinct positions,
    # so comparing against those would report a parity failure on every tie --
    # a disagreement about convention, not about the statistic.
    target_logit = logits[target_id]
    reference = (
        next(i for i, token in enumerate(order) if logits[token] == target_logit) + 1
    )
    return target_rank1(logits, target_id) == reference


def _fit_broken_map_from_svd(
    u: Any,
    singular_values: Any,
    vt: Any,
    *,
    dtype: Any,
    seed: int,
) -> Any:
    """Construct one control map from a shared fitted-map decomposition."""
    import numpy as np

    rng = np.random.Generator(np.random.PCG64(seed))
    gaussian = rng.standard_normal((u.shape[0], u.shape[0])).astype(dtype)
    q, r = np.linalg.qr(gaussian)
    q = q * np.sign(np.diag(r))
    return ((q @ u) * singular_values @ vt).astype(dtype)


def build_fit_broken_maps(jacobian: Any, seeds: Sequence[int]) -> tuple[list[Any], Any]:
    """Build several broken maps while decomposing the fitted map exactly once.

    Stage 2b requires eight draws for each selected layer. Repeating the fitted
    map's 2048x2048 SVD for every draw adds no information, so this batch surface
    shares the decomposition and returns its singular values for the independent
    per-realization spectrum checks.
    """
    import numpy as np

    j = np.asarray(jacobian)
    if j.ndim != 2 or j.shape[0] != j.shape[1]:
        raise ValueError(f"expected a square matrix, got shape {j.shape}")
    if not seeds:
        raise ValueError("at least one broken-map seed is required")
    if any(not isinstance(seed, int) or isinstance(seed, bool) for seed in seeds):
        raise TypeError("broken-map seeds must be integers")

    u, singular_values, vt = np.linalg.svd(j, full_matrices=False)
    maps = [
        _fit_broken_map_from_svd(
            u,
            singular_values,
            vt,
            dtype=j.dtype,
            seed=seed,
        )
        for seed in seeds
    ]
    return maps, singular_values


def build_fit_broken_map(jacobian: Any, seed: int) -> Any:
    """FR-004: destroy the fitted correspondence, preserve everything nuisance.

    ``J = U S Vt`` becomes ``(Q U) S Vt`` for a Haar-random orthogonal ``Q``.  Left
    multiplying ``U`` by an orthogonal matrix leaves the singular values untouched,
    so the operator norm, Frobenius norm, and conditioning are all identical to the
    original.  What changes is which input direction maps to which output
    direction.

    That preservation is what makes this a control rather than a different object.
    A map with a different spectrum could beat or lose to the real one for reasons
    having nothing to do with the fit.

    ``Q`` comes from a QR decomposition of a Gaussian matrix **with the sign
    correction** (Mezzadri 2007): ``numpy.linalg.qr`` does not return a Haar-
    distributed ``Q`` on its own, because LAPACK fixes no sign convention on ``R``'s
    diagonal.  Without multiplying by ``sign(diag(R))`` the result is biased, which
    would quietly make the control non-uniform over the orthogonal group.

    ``numpy`` is imported here rather than at module scope so the rest of this
    module keeps loading in an environment without it.
    """
    maps, _singular_values = build_fit_broken_maps(jacobian, [seed])
    return maps[0]


def _array_sha256(value: Any) -> str:
    """Return the project-wide dtype/shape/bytes identity for a NumPy array."""
    import numpy as np

    array = np.ascontiguousarray(value)
    metadata = f"{array.dtype}:{array.shape}:".encode("ascii")
    return hashlib.sha256(metadata + array.tobytes()).hexdigest()


def singular_spectrum_evidence(
    fitted_map: Any,
    broken_map: Any,
    *,
    fitted_singular_values: Any | None = None,
    rtol: float = SINGULAR_SPECTRUM_RTOL,
    atol: float = SINGULAR_SPECTRUM_ATOL,
) -> dict[str, Any]:
    """Verify and summarize every singular value of one realized broken map.

    The retained evidence is sufficient for the offline validator to recompute
    the allclose decision from the maximum normalized error. The singular-value
    vectors themselves are deliberately not persisted.
    """
    import numpy as np

    fitted = np.asarray(fitted_map)
    broken = np.asarray(broken_map)
    if (
        fitted.ndim != 2
        or broken.ndim != 2
        or fitted.shape != broken.shape
        or fitted.shape[0] != fitted.shape[1]
    ):
        raise ValueError(
            "spectrum verification requires same-shaped square fitted and broken maps"
        )
    if (
        not isinstance(rtol, (int, float))
        or isinstance(rtol, bool)
        or not math.isfinite(float(rtol))
        or float(rtol) <= 0.0
        or not isinstance(atol, (int, float))
        or isinstance(atol, bool)
        or not math.isfinite(float(atol))
        or float(atol) <= 0.0
    ):
        raise ValueError("spectrum tolerances must be finite positive numbers")

    fitted_values = (
        np.linalg.svd(fitted, compute_uv=False)
        if fitted_singular_values is None
        else np.asarray(fitted_singular_values)
    )
    if (
        fitted_values.ndim != 1
        or fitted_values.size != fitted.shape[0]
        or not np.all(np.isfinite(fitted_values))
    ):
        raise ValueError(
            "fitted singular values must be a finite vector matching the map dimension"
        )
    broken_values = np.linalg.svd(broken, compute_uv=False)
    absolute_error = np.abs(fitted_values - broken_values)
    allowance = float(atol) + float(rtol) * np.abs(fitted_values)
    normalized_error = absolute_error / allowance
    max_abs_diff = float(np.max(absolute_error))
    max_normalized_error = float(np.max(normalized_error))
    verified = bool(
        np.all(np.isfinite(fitted_values))
        and np.all(np.isfinite(broken_values))
        and np.all(np.isfinite(normalized_error))
        and max_normalized_error <= 1.0
    )
    return {
        "schema": "stage2b-map-spectrum-check/v1",
        "method": "numpy.linalg.svd-allclose/v1",
        "singular_value_count": int(fitted_values.size),
        "fitted_singular_values_sha256": _array_sha256(fitted_values),
        "broken_singular_values_sha256": _array_sha256(broken_values),
        "rtol": float(rtol),
        "atol": float(atol),
        "max_abs_diff": max_abs_diff,
        "max_normalized_error": max_normalized_error,
        "verified": verified,
    }


def transport_with(residual: Any, jacobian: Any) -> Any:
    """Apply a supplied map to a residual: ``residual @ J.T``.

    Reimplements the body of ``JacobianLens.transport`` rather than mutating
    ``lens.jacobians[layer]`` in place.  Mutating the lens would make every later
    read of that layer silently return the broken map -- correct today, invisible
    when wrong, which is the same class of defect as Stage 2's dead constants.
    """
    import numpy as np

    return np.asarray(residual) @ np.asarray(jacobian).T


def select_wrong_activation_source(
    prompt_sha256s: Sequence[str],
    exclude_prompt_sha256: str,
    seed: int,
) -> str:
    """Choose the exact donor implied by a recipient digest and ratified seed."""
    import numpy as np

    candidates = sorted(k for k in prompt_sha256s if k != exclude_prompt_sha256)
    if not candidates:
        raise ValueError(
            "no other prompt available to draw a wrong activation from; "
            "the manifest must hold at least two prompts at this layer"
        )

    # Derive a per-prompt seed. A bare generator reset on every call
    # returns the same draw each time, so calling this once per prompt with one
    # preregistered seed would concentrate every wrong activation on one or two
    # donors -- reproducible, and useless as a control.
    # Use the WHOLE digest, not a prefix. A prefix collides whenever digests
    # share leading characters, and a collision here silently returns the same
    # donor for different prompts -- the concentration this derivation exists to
    # prevent, reintroduced quietly.
    per_prompt = np.random.Generator(
        np.random.PCG64([seed, int(exclude_prompt_sha256, 16)])
    )
    return candidates[int(per_prompt.integers(len(candidates)))]


def select_wrong_activation(
    residuals_by_prompt: Mapping[str, Any],
    exclude_prompt_sha256: str,
    seed: int,
) -> tuple[Any, str]:
    """FR-005: a real residual from a different prompt, rescaled to match norm.

    Returns ``(activation, source_prompt_sha256)``. The pure source-selection
    helper is shared with the offline validator so a coordinated donor rewrite
    cannot pass by recomputing only its self-consistent pair digest.
    """
    import numpy as np

    source = select_wrong_activation_source(
        tuple(residuals_by_prompt),
        exclude_prompt_sha256,
        seed,
    )

    target_input = np.asarray(residuals_by_prompt[exclude_prompt_sha256])
    dtype = (
        target_input.dtype
        if np.issubdtype(target_input.dtype, np.floating)
        else np.float64
    )
    donor = np.asarray(residuals_by_prompt[source], dtype=dtype)
    target = np.asarray(target_input, dtype=dtype)

    donor_norm = float(np.linalg.norm(donor))
    if donor_norm == 0.0:
        raise ValueError(f"donor residual for {source!r} has zero norm")

    target_norm = float(np.linalg.norm(target))
    if target_norm == 0.0:
        raise ValueError(
            f"target residual for {exclude_prompt_sha256!r} has zero norm; "
            "rescaling to it would produce a zero vector with no donor direction"
        )

    return (donor * (target_norm / donor_norm)).astype(dtype, copy=False), source


def assemble_factorial_cells(
    correct_act_fitted_map: float | NTAExcluded,
    correct_act_broken_map: float | NTAExcluded,
    wrong_act_fitted_map: float | NTAExcluded,
    wrong_act_broken_map: float | NTAExcluded,
) -> dict[str, Any]:
    """Materialize one descriptive 2x2 factorial and its algebraic contrasts.

    The contrasts preserve the ratified donor-by-map interaction measurement without
    choosing an aggregation, uncertainty procedure, threshold, gate, or decision
    rule. Those uses remain deferred.

    Any excluded cell makes every effect that depends on it ``None`` rather than
    zero.  An absent measurement is not a null effect.
    """
    cells = {
        "correct_act_fitted_map": correct_act_fitted_map,
        "correct_act_broken_map": correct_act_broken_map,
        "wrong_act_fitted_map": wrong_act_fitted_map,
        "wrong_act_broken_map": wrong_act_broken_map,
    }

    def is_excluded(value: Any) -> bool:
        return value is None or isinstance(value, NTAExcluded)

    def diff(a: str, b: str) -> float | None:
        x, y = cells[a], cells[b]
        if is_excluded(x) or is_excluded(y):
            return None
        return x - y

    simple = diff("correct_act_fitted_map", "correct_act_broken_map")
    wrong_side = diff("wrong_act_fitted_map", "wrong_act_broken_map")
    main = None if simple is None or wrong_side is None else (simple + wrong_side) / 2
    interaction = None if simple is None or wrong_side is None else simple - wrong_side

    return {
        "cells": {k: (None if is_excluded(v) else v) for k, v in cells.items()},
        "excluded": [k for k, v in cells.items() if is_excluded(v)],
        "simple_effect_of_map": simple,
        "main_effect_of_map": main,
        "interaction": interaction,
    }


def materialize_crossed_factorials(
    factorized: Mapping[str, Any],
) -> dict[str, Any]:
    """Reconstruct every donor/map factorial from 81 unique readouts.

    The persisted form is factorized: one invariant correct/fitted readout, eight
    map-indexed correct/broken readouts, eight donor-indexed wrong/fitted readouts,
    and an 8x8 donor/map wrong/broken matrix.  This function proves that compact
    form is lossless by materializing all 64 logical combinations in memory.
    """
    if "correct_act_fitted_map" not in factorized:
        raise ValueError(
            "factorized representation requires the invariant fitted readout"
        )
    correct_fitted = factorized["correct_act_fitted_map"]
    correct_broken = factorized.get("correct_act_broken_map")
    wrong_fitted = factorized.get("wrong_act_fitted_map")
    wrong_broken = factorized.get("wrong_act_broken_map")
    if not isinstance(correct_broken, Mapping) or len(correct_broken) != 8:
        raise ValueError("factorized representation requires exactly eight map draws")
    if not isinstance(wrong_fitted, Mapping) or len(wrong_fitted) != 8:
        raise ValueError(
            "factorized representation requires exactly eight donor assignments"
        )
    if not isinstance(wrong_broken, Mapping):
        raise ValueError("factorized representation requires a complete 8x8 crossing")

    if not all(isinstance(value, str) for value in correct_broken):
        raise ValueError("map draw identifiers must be strings")
    if not all(isinstance(value, str) for value in wrong_fitted):
        raise ValueError("donor assignment identifiers must be strings")
    map_ids = sorted(correct_broken)
    donor_ids = sorted(wrong_fitted)
    if set(wrong_broken) != set(wrong_fitted):
        raise ValueError("factorized representation requires a complete 8x8 crossing")
    for donor_id in donor_ids:
        row = wrong_broken.get(donor_id)
        if not isinstance(row, Mapping) or set(row) != set(correct_broken):
            raise ValueError(
                "factorized representation requires a complete 8x8 crossing"
            )

    factorials = []
    for donor_id in donor_ids:
        for map_id in map_ids:
            factorials.append(
                {
                    "donor_assignment_id": donor_id,
                    "map_draw_id": map_id,
                    "factorial": assemble_factorial_cells(
                        correct_fitted,
                        correct_broken[map_id],
                        wrong_fitted[donor_id],
                        wrong_broken[donor_id][map_id],
                    ),
                }
            )
    return {
        "donor_assignment_ids": donor_ids,
        "map_draw_ids": map_ids,
        "unique_readout_count": 1 + len(map_ids) + len(donor_ids) + len(factorials),
        "logical_cell_count": len(factorials),
        "factorials": factorials,
    }
