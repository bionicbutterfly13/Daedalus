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


class TestRankParityVerification:
    """FR-010's guard against an optimization silently changing the statistic."""

    def test_parity_holds_for_the_shipped_implementation(self):
        logits = [3.5, -1.0, 0.0, 9.25, 2.0, -7.5, 4.0, 1.5]
        assert all(endpoint.verify_rank_parity(logits, t) for t in range(len(logits)))

    def test_parity_detects_a_divergent_implementation(self, monkeypatch):
        """The check must be capable of returning False.

        A parity check that cannot fail is decorative.  Swapping in an off-by-one
        rank proves this one actually compares something.
        """
        monkeypatch.setattr(endpoint, "target_rank1", lambda logits, t: 99)
        assert endpoint.verify_rank_parity([1.0, 2.0, 3.0], 0) is False


class TestFitBrokenMap:
    """FR-004: same object, wrong correspondence."""

    @staticmethod
    def _fixture(n=6, seed=0):
        np = pytest.importorskip("numpy")
        rng = np.random.default_rng(seed)
        return np, rng.standard_normal((n, n))

    def test_singular_values_are_preserved_exactly(self):
        np, j = self._fixture()
        broken = endpoint.build_fit_broken_map(j, seed=20260726)
        np.testing.assert_allclose(
            np.linalg.svd(j, compute_uv=False),
            np.linalg.svd(broken, compute_uv=False),
            rtol=1e-10,
        )

    def test_operator_and_frobenius_norms_are_preserved(self):
        """Preserving these is what makes it a control and not a different object.

        A map with a different scale could beat or lose to the real one for
        reasons having nothing to do with the fit.
        """
        np, j = self._fixture()
        broken = endpoint.build_fit_broken_map(j, seed=20260726)
        assert np.linalg.norm(broken, 2) == pytest.approx(np.linalg.norm(j, 2))
        assert np.linalg.norm(broken, "fro") == pytest.approx(np.linalg.norm(j, "fro"))

    def test_condition_number_is_preserved(self):
        np, j = self._fixture()
        broken = endpoint.build_fit_broken_map(j, seed=20260726)
        assert np.linalg.cond(broken) == pytest.approx(np.linalg.cond(j))

    def test_correspondence_is_actually_destroyed(self):
        """Preservation without destruction would be a no-op control."""
        np, j = self._fixture()
        broken = endpoint.build_fit_broken_map(j, seed=20260726)
        assert not np.allclose(j, broken)

    def test_is_deterministic_under_a_fixed_seed(self):
        np, j = self._fixture()
        a = endpoint.build_fit_broken_map(j, seed=20260726)
        b = endpoint.build_fit_broken_map(j, seed=20260726)
        np.testing.assert_array_equal(a, b)

    def test_different_seeds_give_different_maps(self):
        np, j = self._fixture()
        a = endpoint.build_fit_broken_map(j, seed=1)
        b = endpoint.build_fit_broken_map(j, seed=2)
        assert not np.allclose(a, b)

    def test_rejects_a_non_square_matrix(self):
        np = pytest.importorskip("numpy")
        with pytest.raises(ValueError, match="square"):
            endpoint.build_fit_broken_map(np.zeros((3, 5)), seed=0)

    def test_rotation_is_haar_not_merely_orthogonal(self):
        """The Mezzadri sign correction, tested by its observable consequence.

        Raw ``qr`` on a Gaussian gives an orthogonal Q, but not a Haar-uniform
        one: LAPACK fixes no sign convention on R's diagonal, which biases the
        first row's sign distribution.  Under Haar measure that sign is a fair
        coin.  Without the correction this test fails hard.
        """
        np = pytest.importorskip("numpy")
        identity = np.eye(4)
        signs = [
            np.sign(endpoint.build_fit_broken_map(identity, seed=s)[0, 0])
            for s in range(120)
        ]
        positive = sum(1 for x in signs if x > 0)
        assert 35 < positive < 85, f"first-element sign is biased: {positive}/120"


class TestTransportWith:
    def test_applies_the_supplied_map(self):
        np = pytest.importorskip("numpy")
        j = np.array([[1.0, 2.0], [3.0, 4.0]])
        np.testing.assert_allclose(
            endpoint.transport_with(np.array([1.0, 1.0]), j), np.array([3.0, 7.0])
        )

    def test_uses_the_supplied_map_not_a_stored_one(self):
        """Mutating the lens in place would make later reads silently wrong."""
        np = pytest.importorskip("numpy")
        residual = np.array([1.0, 0.0])
        a = endpoint.transport_with(residual, np.eye(2))
        b = endpoint.transport_with(residual, np.eye(2) * 3)
        assert not np.allclose(a, b)


class TestSelectWrongActivation:
    @staticmethod
    def _residuals():
        np = pytest.importorskip("numpy")
        return np, {
            "aaa": np.array([3.0, 4.0]),  # norm 5
            "bbb": np.array([1.0, 0.0]),  # norm 1
            "ccc": np.array([0.0, 2.0]),  # norm 2
        }

    def test_never_returns_the_excluded_prompts_own_residual(self):
        _np, residuals = self._residuals()
        for seed in range(25):
            _, source = endpoint.select_wrong_activation(residuals, "aaa", seed=seed)
            assert source != "aaa"

    def test_norm_is_matched_to_the_activation_it_replaces(self):
        """Removes magnitude as an explanation for any observed difference."""
        np, residuals = self._residuals()
        wrong, _ = endpoint.select_wrong_activation(residuals, "aaa", seed=0)
        assert np.linalg.norm(wrong) == pytest.approx(np.linalg.norm(residuals["aaa"]))

    def test_direction_is_the_donors_not_the_targets(self):
        """It must be a real activation with the wrong content, not a rescaled
        copy of the right one."""
        np, residuals = self._residuals()
        wrong, source = endpoint.select_wrong_activation(residuals, "aaa", seed=0)
        donor_unit = residuals[source] / np.linalg.norm(residuals[source])
        np.testing.assert_allclose(wrong / np.linalg.norm(wrong), donor_unit)

    def test_is_deterministic_under_a_fixed_seed(self):
        _np, residuals = self._residuals()
        assert (
            endpoint.select_wrong_activation(residuals, "aaa", seed=7)[1]
            == endpoint.select_wrong_activation(residuals, "aaa", seed=7)[1]
        )

    def test_raises_when_no_other_prompt_exists(self):
        np = pytest.importorskip("numpy")
        with pytest.raises(ValueError, match="at least two prompts"):
            endpoint.select_wrong_activation({"only": np.array([1.0])}, "only", seed=0)


class TestAllocateWrongLayers:
    def test_band_counts_differ_by_at_most_one(self):
        """Exact balance is unsatisfiable at n=200 over 3 bands (66.67)."""
        pytest.importorskip("numpy")
        out = endpoint.allocate_wrong_layers(
            [6, 13, 20, 26], [3, 7, 14], 200, 28, seed=1
        )
        counts = {d: sum(1 for a in out if a["distance"] == d) for d in (3, 7, 14)}
        assert sum(counts.values()) == 200
        assert max(counts.values()) - min(counts.values()) <= 1

    def test_exact_balance_when_it_divides_evenly(self):
        pytest.importorskip("numpy")
        out = endpoint.allocate_wrong_layers(
            [6, 13, 20, 26], [3, 7, 14], 201, 28, seed=1
        )
        counts = {d: sum(1 for a in out if a["distance"] == d) for d in (3, 7, 14)}
        assert set(counts.values()) == {67}

    def test_every_wrong_layer_is_in_range(self):
        pytest.importorskip("numpy")
        out = endpoint.allocate_wrong_layers(
            [6, 13, 20, 26], [3, 7, 14], 200, 28, seed=1
        )
        assert all(0 <= a["wrong_layer"] < 28 for a in out)

    def test_realized_distance_matches_the_declared_one(self):
        """Clamping to an edge layer would make these silently disagree."""
        pytest.importorskip("numpy")
        out = endpoint.allocate_wrong_layers(
            [6, 13, 20, 26], [3, 7, 14], 200, 28, seed=1
        )
        for a in out:
            assert abs(a["wrong_layer"] - a["correct_layer"]) == a["distance"]

    def test_sign_is_balanced_rather_than_all_one_direction(self):
        pytest.importorskip("numpy")
        out = endpoint.allocate_wrong_layers(
            [6, 13, 20, 26], [3, 7, 14], 200, 28, seed=1
        )
        up = sum(1 for a in out if a["wrong_layer"] > a["correct_layer"])
        assert 0 < up < len(out)

    def test_raises_rather_than_clamping_when_a_distance_cannot_fit(self):
        pytest.importorskip("numpy")
        with pytest.raises(ValueError, match="does not fit"):
            endpoint.allocate_wrong_layers([5], [40], 4, 10, seed=0)

    def test_is_deterministic_under_a_fixed_seed(self):
        pytest.importorskip("numpy")
        kw = {"n_layers_total": 28, "seed": 3}
        a = endpoint.allocate_wrong_layers([6, 13], [3, 7], 20, **kw)
        b = endpoint.allocate_wrong_layers([6, 13], [3, 7], 20, **kw)
        assert a == b


class TestPairedDifferenceByCluster:
    def test_one_difference_per_prompt(self):
        out = endpoint.paired_difference_by_cluster(
            {"p1": 0.8, "p2": 0.5}, {"p1": 0.3, "p2": 0.5}
        )
        assert out == {"p1": pytest.approx(0.5), "p2": pytest.approx(0.0)}

    def test_excluded_instrument_cell_drops_the_pair(self):
        """An absent measurement is not a zero effect.

        Treating the two alike is how an undefined cell quietly becomes a null.
        """
        out = endpoint.paired_difference_by_cluster(
            {"p1": endpoint.NTAExcluded("denominator_below_min", 0.0)}, {"p1": 0.3}
        )
        assert out == {}

    def test_excluded_control_cell_drops_the_pair(self):
        out = endpoint.paired_difference_by_cluster(
            {"p1": 0.8}, {"p1": endpoint.NTAExcluded("denominator_below_min", 0.0)}
        )
        assert out == {}

    def test_prompt_missing_from_the_control_drops_the_pair(self):
        out = endpoint.paired_difference_by_cluster({"p1": 0.8, "p2": 0.4}, {"p1": 0.3})
        assert set(out) == {"p1"}

    def test_returns_one_cluster_per_prompt_not_per_cell(self):
        """So a caller cannot treat prompt x layer cells as independent."""
        out = endpoint.paired_difference_by_cluster(
            {f"p{i}": 0.5 for i in range(9)}, {f"p{i}": 0.1 for i in range(9)}
        )
        assert len(out) == 9
