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
from collections.abc import Sequence

__all__ = [
    "RANK_CONVENTION",
    "NTAExcluded",
    "nta",
    "rank_score",
    "target_rank1",
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
