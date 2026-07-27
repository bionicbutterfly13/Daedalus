"""Endpoint tests: the rank convention, the anchors, and the denominator guard.

Everything here runs on fixed arrays.  No model, no GPU, no jlens.
"""

from __future__ import annotations

import importlib.util
import pathlib

import pytest

_MODULE_PATH = (
    pathlib.Path(__file__).resolve().parents[2]
    / "EvoScientist/skills/jspace-research-operations/scripts/stage2b_endpoint.py"
)
_spec = importlib.util.spec_from_file_location("stage2b_endpoint", _MODULE_PATH)
assert _spec is not None
assert _spec.loader is not None
endpoint = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(endpoint)


def _naive_rank1(logits, target_id):
    """Reference implementation: sort the whole vocabulary, then look up.

    Mirrors ``jlens.vis._ranks_of``'s documented convention (0-indexed, rank 0 =
    top) with ``+1`` applied, so FR-010's parity requirement has a local referent
    on a machine where jlens is not installed.
    """
    order = sorted(range(len(logits)), key=lambda i: logits[i], reverse=True)
    return order.index(target_id) + 1


class TestRankConvention:
    def test_top_token_ranks_one_never_zero(self):
        """``log(rank)`` is undefined at 0, so the convention must be 1-indexed."""
        logits = [0.1, 9.0, 0.3]
        assert endpoint.target_rank1(logits, 1) == 1

    def test_rank_increases_down_the_ordering(self):
        logits = [5.0, 3.0, 1.0]
        assert endpoint.target_rank1(logits, 0) == 1
        assert endpoint.target_rank1(logits, 1) == 2
        assert endpoint.target_rank1(logits, 2) == 3

    def test_ties_resolve_to_the_best_rank(self):
        """Strict ``>`` is preregistered; ``>=`` would give the worst rank.

        Rare but reachable after fp16 round-tripping, which is why the convention
        is declared rather than left to whatever ``argsort`` happens to do.
        """
        logits = [1.0, 5.0, 5.0, 0.0]
        assert endpoint.target_rank1(logits, 1) == 1
        assert endpoint.target_rank1(logits, 2) == 1

    def test_out_of_range_target_raises(self):
        with pytest.raises(IndexError):
            endpoint.target_rank1([1.0, 2.0], 7)

    @pytest.mark.parametrize("target_id", range(8))
    def test_parity_with_naive_full_sort_reference(self, target_id):
        """FR-010: the optimization must not change the statistic.

        An optimization that silently changes a statistic is indistinguishable
        from a correct one until the results are wrong.
        """
        logits = [3.5, -1.0, 0.0, 9.25, 2.0, -7.5, 4.0, 1.5]
        assert endpoint.target_rank1(logits, target_id) == _naive_rank1(
            logits, target_id
        )

    def test_convention_is_recorded_for_the_artifact(self):
        assert endpoint.RANK_CONVENTION == "strict_gt_1indexed"


class TestRankScore:
    def test_rank_one_scores_zero(self):
        assert endpoint.rank_score(1, 151936) == 0.0

    def test_worst_rank_scores_minus_one(self):
        assert endpoint.rank_score(151936, 151936) == pytest.approx(-1.0)

    def test_score_is_monotone_decreasing_in_rank(self):
        scores = [endpoint.rank_score(r, 1000) for r in (1, 2, 10, 100, 1000)]
        assert scores == sorted(scores, reverse=True)

    def test_zero_or_negative_rank_raises(self):
        """Guards the ``log(0)`` that a 0-indexed rank would produce."""
        with pytest.raises(ValueError, match="1-indexed"):
            endpoint.rank_score(0, 1000)


class TestNTAAnchors:
    """FR-002: the baselines are structural, so the Stage 2 omission is
    unrepresentable rather than merely discouraged."""

    def test_prompt_only_is_exactly_zero(self):
        assert endpoint.nta(-0.8, -0.8, -0.2, min_denominator=0.01) == 0.0

    def test_output_is_exactly_one(self):
        assert endpoint.nta(-0.2, -0.8, -0.2, min_denominator=0.01) == 1.0

    def test_midpoint_is_one_half(self):
        assert endpoint.nta(-0.5, -0.8, -0.2, min_denominator=0.01) == pytest.approx(
            0.5
        )

    def test_a_readout_below_the_prompt_floor_goes_negative(self):
        """Not clamped.  A readout worse than the surface prompt is a real
        result and must not be floored to zero, which would hide it."""
        assert endpoint.nta(-0.9, -0.8, -0.2, min_denominator=0.01) < 0.0


class TestDenominatorGuard:
    def test_cell_at_or_below_threshold_is_excluded_not_divided(self):
        result = endpoint.nta(-0.5, -0.30, -0.29, min_denominator=0.05)
        assert isinstance(result, endpoint.NTAExcluded)
        assert result.reason == "denominator_below_min"

    def test_exclusion_is_not_a_number(self):
        """So it can never be silently averaged in as one."""
        result = endpoint.nta(-0.5, -0.30, -0.29, min_denominator=0.05)
        assert not isinstance(result, float)

    def test_zero_denominator_is_excluded_rather_than_dividing(self):
        result = endpoint.nta(-0.5, -0.3, -0.3, min_denominator=0.0)
        assert isinstance(result, endpoint.NTAExcluded)
        assert result.denominator == 0.0

    def test_negative_denominator_is_excluded(self):
        """The output placed *worse* than the prompt floor inverts the scale."""
        result = endpoint.nta(-0.5, -0.2, -0.6, min_denominator=0.0)
        assert isinstance(result, endpoint.NTAExcluded)

    def test_denominator_just_above_threshold_is_kept(self):
        result = endpoint.nta(-0.5, -0.8, -0.7, min_denominator=0.05)
        assert isinstance(result, float)

    def test_guard_prevents_the_noise_amplification_it_exists_for(self):
        """Without the guard this cell would report an enormous NTA built from
        a difference indistinguishable from noise."""
        unguarded = (-0.5 - -0.30) / (-0.29 - -0.30)
        assert abs(unguarded) > 19
        assert isinstance(
            endpoint.nta(-0.5, -0.30, -0.29, min_denominator=0.05),
            endpoint.NTAExcluded,
        )
