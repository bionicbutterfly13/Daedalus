"""Stage 2b endpoint: normalized target attainment and its supporting statistics.

Contracts: ``specs/001-jspace-stage2b/data-model.md`` §3, ``contracts/artifact-schema.md``.

Like :mod:`stage2b_preflight`, nothing here imports ``torch``, ``jlens``, or
``scipy`` at module scope.  The numeric primitives operate on any sequence of
floats, so they are testable with fixed arrays on a machine with no GPU.  Only
:func:`cluster_bootstrap_median` needs ``scipy``, and it imports it inside the
function body.

The endpoint replaces Stage 2's readout-difference metric, which measured how much
two readouts *differ* and therefore had no notion of correct.  A difference metric
cannot distinguish an informative disagreement from an arbitrary one, so Stage 2's
strongest possible conclusion was always non-identity, whatever the data said.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

from stage2b_decision import compose_confirmatory_decision, derive_gate_outcome

__all__ = [
    "RANK_CONVENTION",
    "NTAExcluded",
    "allocate_wrong_layers",
    "assemble_factorial_cells",
    "build_fit_broken_map",
    "cluster_bootstrap_median",
    "combine_per_layer",
    "compose_decision",
    "gate_record",
    "jaccard_top_k",
    "nta",
    "paired_difference_by_cluster",
    "rank_score",
    "select_wrong_activation",
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


def verify_rank_parity(logits: Sequence[float], target_id: int) -> bool:
    """FR-010: the fast rank must equal a full-sort reference on a fixed probe.

    Returns the boolean recorded as ``contracts.rank_parity_verified``.  This
    exists because an optimization that silently changes a statistic is
    indistinguishable from a correct one until the results are wrong, and Stage 2's
    full-vocabulary ``argsort`` is the thing being replaced.

    The reference here mirrors ``jlens.vis._ranks_of``'s documented convention
    (0-indexed, rank 0 = top) with ``+1`` applied.  In Colab the same assertion
    should be repeated against the real ``_ranks_of``; locally jlens is not
    installed, so the naive sort stands in.
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
    import numpy as np

    j = np.asarray(jacobian)
    if j.ndim != 2 or j.shape[0] != j.shape[1]:
        raise ValueError(f"expected a square matrix, got shape {j.shape}")

    u, s, vt = np.linalg.svd(j, full_matrices=False)

    rng = np.random.default_rng(seed)
    # Match the Jacobian's dtype. Defaulting to float64 would silently return a
    # float64 control map for a float32 Jacobian, breaking the float32 contract
    # the study asserts at preflight.
    gaussian = rng.standard_normal((u.shape[0], u.shape[0])).astype(j.dtype)
    q, r = np.linalg.qr(gaussian)
    q = q * np.sign(np.diag(r))  # Mezzadri correction; without it Q is not Haar

    return ((q @ u) * s @ vt).astype(j.dtype)


def transport_with(residual: Any, jacobian: Any) -> Any:
    """Apply a supplied map to a residual: ``residual @ J.T``.

    Reimplements the body of ``JacobianLens.transport`` rather than mutating
    ``lens.jacobians[layer]`` in place.  Mutating the lens would make every later
    read of that layer silently return the broken map -- correct today, invisible
    when wrong, which is the same class of defect as Stage 2's dead constants.
    """
    import numpy as np

    return np.asarray(residual) @ np.asarray(jacobian).T


def select_wrong_activation(
    residuals_by_prompt: Mapping[str, Any],
    exclude_prompt_sha256: str,
    seed: int,
) -> tuple[Any, str]:
    """FR-005: a real residual from a different prompt, rescaled to match norm.

    Returns ``(activation, source_prompt_sha256)``.  The source digest is recorded
    in the artifact so "this was a real activation, not noise" is a checkable
    property of the run rather than a claim in a design document.

    Stage 2 already showed a norm-matched *random vector* is easy to beat (fraction
    1.00), so it survives here only as the sanity floor.  A real activation from a
    real prompt is the honest hard case: correct distributional structure, wrong
    content.  Norm-matching removes magnitude as an explanation for any difference.
    """
    import numpy as np

    candidates = sorted(k for k in residuals_by_prompt if k != exclude_prompt_sha256)
    if not candidates:
        raise ValueError(
            "no other prompt available to draw a wrong activation from; "
            "the manifest must hold at least two prompts at this layer"
        )

    # Derive a per-prompt seed. A bare default_rng(seed) reset on every call
    # returns the same draw each time, so calling this once per prompt with one
    # preregistered seed would concentrate every wrong activation on one or two
    # donors -- reproducible, and useless as a control.
    # Use the WHOLE digest, not a prefix. A prefix collides whenever digests
    # share leading characters, and a collision here silently returns the same
    # donor for different prompts -- the concentration this derivation exists to
    # prevent, reintroduced quietly.
    per_prompt = np.random.default_rng([seed, int(exclude_prompt_sha256, 16)])
    source = candidates[int(per_prompt.integers(len(candidates)))]

    donor = np.asarray(residuals_by_prompt[source], dtype=np.float64)
    target = np.asarray(residuals_by_prompt[exclude_prompt_sha256], dtype=np.float64)

    donor_norm = float(np.linalg.norm(donor))
    if donor_norm == 0.0:
        raise ValueError(f"donor residual for {source!r} has zero norm")

    target_norm = float(np.linalg.norm(target))
    if target_norm == 0.0:
        raise ValueError(
            f"target residual for {exclude_prompt_sha256!r} has zero norm; "
            "rescaling to it would produce a zero vector with no donor direction"
        )

    return donor * (target_norm / donor_norm), source


def allocate_wrong_layers(
    selected_layers: Sequence[int],
    distances: Sequence[int],
    n_prompts: int,
    n_layers_total: int,
    seed: int,
) -> list[dict[str, int]]:
    """FR-008: assign each prompt a wrong-layer distance band, near-equally.

    Exact balance is not generally achievable -- 200 prompts over 3 bands is 66.67 --
    so the rule is ``floor(n/k)`` per band with the remainder going to the
    lowest-indexed bands, under the preregistered seed.  Realized counts are
    recorded in the artifact rather than assumed.

    Stage 2 did not balance this at all, which is why its mismatched-probe fraction
    of 0.40 mixes near and far regimes and cannot be interpreted: a map from an
    adjacent layer is nearly correct, one from the opposite end is trivially wrong,
    and pooling them yields a number that describes neither.

    Sign is balanced where the layer index permits.  A band whose offset would fall
    outside ``[0, n_layers_total)`` in one direction takes the other; if neither
    direction fits, that assignment is impossible and it raises rather than
    silently clamping to an edge layer, which would make the realized distance
    differ from the declared one.
    """
    import numpy as np

    if not distances:
        raise ValueError("distances must be non-empty")

    k = len(distances)
    base, remainder = divmod(n_prompts, k)
    counts = [base + (1 if i < remainder else 0) for i in range(k)]

    bands: list[int] = []
    for distance, count in zip(distances, counts, strict=True):
        bands.extend([distance] * count)

    rng = np.random.default_rng(seed)
    rng.shuffle(bands)

    # Sign is balanced within each (correct_layer, distance) cell, not by
    # positional parity. Deriving it from `index` couples direction to layer:
    # with four loci and two options, index % 4 determines index % 2, so every
    # eligible cell came out entirely one direction (verified: layer 6 / distance
    # 3 gave 18 up and 0 down). That confounds direction with layer, which is the
    # exact confound this control exists to remove.
    cells: dict[tuple[int, int], list[int]] = {}
    plan: list[tuple[int, int]] = []
    for index, distance in enumerate(bands):
        correct = selected_layers[index % len(selected_layers)]
        plan.append((correct, distance))
        cells.setdefault((correct, distance), []).append(index)

    signs: dict[int, int] = {}
    for (correct, distance), members in cells.items():
        options = [
            delta
            for delta in (distance, -distance)
            if 0 <= correct + delta < n_layers_total
        ]
        if not options:
            raise ValueError(
                f"distance {distance} does not fit around layer {correct} "
                f"within [0, {n_layers_total})"
            )
        # Alternate through the eligible directions so each cell splits as evenly
        # as its membership allows, then rotate the starting direction by cell so
        # an odd remainder does not always favour the same sign.
        offset = (correct + distance) % len(options)
        for position, member in enumerate(members):
            signs[member] = options[(position + offset) % len(options)]

    assignments: list[dict[str, int]] = []
    for index, (correct, distance) in enumerate(plan):
        assignments.append(
            {
                "correct_layer": correct,
                "wrong_layer": correct + signs[index],
                "distance": distance,
            }
        )
    return assignments


def paired_difference_by_cluster(
    instrument: Mapping[str, float | NTAExcluded],
    control: Mapping[str, float | NTAExcluded],
) -> dict[str, float]:
    """One paired difference per prompt, at a single layer (FR-006).

    Both mappings are prompt digest -> that prompt's NTA **at one layer**.  The
    prompt is the cluster; layers are repeated measures and are never mixed here.
    Callers run this once per layer.

    A cell excluded on either side drops the pair: a difference against an excluded
    denominator is not a small effect, it is an absent measurement, and averaging
    the two together is how an absent measurement becomes a null result.

    This function deliberately cannot return a depth-pooled value.  Pooling layers
    would let a strong late layer carry the result, since a late-layer residual sits
    close to the output and scores well for trivial reasons.
    """
    paired: dict[str, float] = {}
    for prompt, value in instrument.items():
        other = control.get(prompt)
        if other is None:
            continue
        if isinstance(value, NTAExcluded) or isinstance(other, NTAExcluded):
            continue
        paired[prompt] = value - other
    return paired


# --------------------------------------------------------------------------
# US2: non-redundancy, gate records, and decision composition.
# --------------------------------------------------------------------------


def jaccard_top_k(readout_a: Sequence[int], readout_b: Sequence[int], k: int) -> float:
    """Top-k token overlap between two readouts.

    Carried over from Stage 2's ``jaccard_top10`` so the H2 overlap clause stays
    commensurable with the pilot.  Low overlap alone is a weak claim — it is
    satisfied by a readout that is different *and useless* — which is why H2 also
    requires a target-relative difference.  This clause only establishes that the
    two readouts are not the same object.
    """
    if k < 1:
        raise ValueError(f"k must be >= 1, got {k}")
    top_a, top_b = set(readout_a[:k]), set(readout_b[:k])
    union = top_a | top_b
    if not union:
        raise ValueError("both readouts are empty; Jaccard is undefined")
    return len(top_a & top_b) / len(union)


def gate_record(
    name: str,
    constant_name: str | None,
    declared_value: Any,
    statistic: float,
    interval: Mapping[str, Any],
    n_clusters: int,
    *,
    comparison: str,
    exclusions: Sequence[Mapping[str, Any]] = (),
    crosscheck: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """One gate's full record, per ``contracts/artifact-schema.md``.

    ``outcome`` is ``pass`` | ``fail`` | ``undefined``.  A non-finite interval
    bound yields **undefined, never fail**.

    That distinction is the whole point.  BCa's acceleration term is estimated from
    the skewness of leave-one-out replicates, and a median is discontinuous under
    leave-one-out — with few clusters or many ties scipy returns NaN bounds and
    emits ``DegenerateDataWarning``.  A NaN lower bound means *the interval could
    not be computed*, which is a different result from *the interval included
    zero*.  Collapsing them would let a degenerate bootstrap be reported as a
    measured null, which is exactly the overstatement Principle V forbids.
    """
    outcome = derive_gate_outcome(
        statistic=statistic,
        interval=interval,
        declared_value=declared_value,
        comparison=comparison,
    )

    record: dict[str, Any] = {
        "name": name,
        "constant_name": constant_name,
        "declared_value": declared_value,
        "statistic": statistic,
        "interval": dict(interval),
        "comparison": comparison,
        "n_clusters": n_clusters,
        "exclusions": [dict(e) for e in exclusions],
        "outcome": outcome,
    }
    if str(interval.get("method", "")).lower() == "bca":
        if crosscheck is None:
            raise ValueError(
                f"gate {name!r} gates on a BCa interval but records no percentile "
                "cross-check; a degenerate BCa would then be undetectable after "
                "the fact"
            )
        record["interval_crosscheck"] = dict(crosscheck)
    return record


def combine_per_layer(name: str, per_layer: Mapping[int, Mapping[str, Any]]) -> str:
    """Fold per-layer gate outcomes into one, conjunctively.

    All comparisons are within layer, so a gate holds only if it holds at *every*
    layer. A measured failure dominates an undefined layer because missing data
    cannot erase a falsification. With no failures, any undefined layer makes the
    conjunction undefined rather than manufacturing a failed measurement.
    """
    outcomes = [layer["outcome"] for layer in per_layer.values()]
    if not outcomes:
        raise ValueError(f"gate {name!r} has no per-layer results to combine")
    if "fail" in outcomes:
        return "fail"
    if "undefined" in outcomes:
        return "undefined"
    return "pass" if all(o == "pass" for o in outcomes) else "fail"


def assemble_factorial_cells(
    correct_act_fitted_map: float | NTAExcluded,
    correct_act_broken_map: float | NTAExcluded,
    wrong_act_fitted_map: float | NTAExcluded,
    wrong_act_broken_map: float | NTAExcluded,
) -> dict[str, Any]:
    """The 2x2 at one ``(prompt, layer)``, plus effects (FR-003).

    ``simple_effect_of_map`` is H1's statistic per the decision-rule table: the
    map contrast **at the correct activation only**.

    ``main_effect_of_map`` averages that contrast with the one at the wrong
    activation.  It is computed and reported, but it does **not** gate.  The design
    document calls it H1 in §4 while §2 and §6 name the simple effect; the two
    coincide only if the interaction is zero, and §4 itself predicts a nonzero one.
    Gating on the diluted quantity would penalize the instrument using cells where
    the design expects the effect to be weakest.  See research.md R9 — this is
    flagged for ratification, and switching would change only which value reaches
    ``gate_record``.

    ``interaction`` **gates**, as of open item 7. It is compared against
    ``INTERACTION_MIN_EFFECT``, derived from the Q6 pilot alongside
    ``SPEC_MIN_EFFECT`` and ``NTA_MIN_DENOMINATOR`` rather than guessed --- which
    is what removes the original objection to gating it. The design calls the
    interaction the signature of a real instrument; without this gate a pass would
    assert input-specific work the study had not established.

    Any excluded cell makes every effect that depends on it ``None`` rather than
    zero.  An absent measurement is not a null effect.
    """
    cells = {
        "correct_act_fitted_map": correct_act_fitted_map,
        "correct_act_broken_map": correct_act_broken_map,
        "wrong_act_fitted_map": wrong_act_fitted_map,
        "wrong_act_broken_map": wrong_act_broken_map,
    }

    def diff(a: str, b: str) -> float | None:
        x, y = cells[a], cells[b]
        if isinstance(x, NTAExcluded) or isinstance(y, NTAExcluded):
            return None
        return x - y

    simple = diff("correct_act_fitted_map", "correct_act_broken_map")
    wrong_side = diff("wrong_act_fitted_map", "wrong_act_broken_map")
    main = None if simple is None or wrong_side is None else (simple + wrong_side) / 2
    interaction = None if simple is None or wrong_side is None else simple - wrong_side

    return {
        "cells": {
            k: (None if isinstance(v, NTAExcluded) else v) for k, v in cells.items()
        },
        "excluded": [k for k, v in cells.items() if isinstance(v, NTAExcluded)],
        "simple_effect_of_map": simple,  # H1 gates on this
        "main_effect_of_map": main,  # descriptive only (R9)
        "interaction": interaction,  # descriptive only, no pilot estimate
    }


def compose_decision(
    gates: Mapping[str, str],
    *,
    pinned_identities_matched: bool = True,
    capacity_ok: bool = True,
) -> dict[str, Any]:
    """Fold gate outcomes into ``pass`` | ``ambiguity`` | ``fail`` | ``kill``.

    ``gates`` maps gate ID to its outcome string. H1 holds only if all three of
    ``h1_specificity``, ``h1_interval``, and ``h1_interaction`` pass.  The kill conditions cannot be
    derived from gate records alone — a pinned-identity mismatch and a capacity
    failure are preflight outcomes with no gate of their own — so they arrive as
    explicit keyword arguments rather than being silently assumed to hold.

    An ``undefined`` gate never counts toward a pass.  H1 and H2 are each
    conjunctive over their two clauses, so a single undefined clause is enough to
    stop that hypothesis passing, and the reason is recorded in ``notes``.
    """
    return compose_confirmatory_decision(
        gates,
        pinned_identities_matched=pinned_identities_matched,
        capacity_ok=capacity_ok,
    )


def cluster_bootstrap_median(
    cluster_values: Mapping[str, float],
    level: float,
    iterations: int,
    seed: int,
) -> dict[str, Any]:
    """BCa interval on the median paired difference, resampling whole prompts.

    ``cluster_values`` maps prompt digest -> that prompt's paired difference **at
    one layer**.  The bootstrap runs once per layer; it never concatenates across
    layers, which would pool depth into the gate — the same defect the design
    forbids for absolute NTA, one level down and harder to see because each
    individual difference is already within-layer.

    scipy has no first-class cluster parameter.  Resampling an array of cluster
    *indices* and looking each one up gives a genuine cluster bootstrap: whole
    prompts enter or leave together, and BCa's jackknife leaves out one cluster at
    a time rather than one observation.

    Returns both the BCa interval and a percentile cross-check.  BCa's acceleration
    term is unstable for a median under leave-one-out, so recording only the
    interval that gated would leave a degenerate result undetectable afterwards.
    ``scipy`` is imported here so the module still loads without it.
    """
    import numpy as np
    from scipy.stats import bootstrap

    if len(cluster_values) < 2:
        raise ValueError("cluster bootstrap needs at least two clusters")

    keys = sorted(cluster_values)
    table = np.array([cluster_values[k] for k in keys], dtype=np.float64)
    indices = np.arange(len(keys))

    def statistic(idx: np.ndarray) -> float:
        return float(np.median(table[idx.astype(int)]))

    def interval_for(method: str) -> dict[str, Any]:
        result = bootstrap(
            (indices,),
            statistic,
            n_resamples=iterations,
            confidence_level=level,
            method=method,
            rng=np.random.default_rng(seed),
        )
        return {
            "method": method,
            "level": level,
            "low": float(result.confidence_interval.low),
            "high": float(result.confidence_interval.high),
        }

    return {
        "statistic": float(np.median(table)),
        "n_clusters": len(keys),
        "interval": interval_for("bca"),
        "crosscheck": interval_for("percentile"),
    }
