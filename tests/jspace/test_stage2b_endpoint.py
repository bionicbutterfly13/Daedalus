"""Endpoint tests: the rank convention, the anchors, and the denominator guard.

Everything here runs on fixed arrays.  No model, no GPU, no jlens.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

import pytest

_MODULE_PATH = (
    pathlib.Path(__file__).resolve().parents[2]
    / "EvoScientist/skills/jspace-research-operations/scripts/stage2b_endpoint.py"
)
sys.path.insert(0, str(_MODULE_PATH.parent))
_spec = importlib.util.spec_from_file_location("stage2b_endpoint", _MODULE_PATH)
assert _spec is not None
assert _spec.loader is not None
endpoint = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(endpoint)


def test_unratified_inference_and_decision_helpers_are_not_shipped():
    for name in (
        "cluster_bootstrap_median",
        "combine_per_layer",
        "compose_decision",
        "gate_record",
        "jaccard_top_k",
    ):
        assert not hasattr(endpoint, name), name


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

    def test_parity_agrees_with_the_tie_convention(self):
        """The reference must honour best-rank-among-ties too.

        A stable sort gives tied tokens distinct positions, so comparing against
        those reported a parity failure on every tie — a disagreement about
        convention, not about the statistic.
        """
        logits = [5.0, 5.0, 1.0]
        assert endpoint.target_rank1(logits, 1) == 1
        assert endpoint.verify_rank_parity(logits, 1) is True
        assert endpoint.verify_rank_parity(logits, 0) is True

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

    def test_rank_beyond_the_vocabulary_raises(self):
        """Otherwise the claimed [-1, 0] bound silently does not hold:
        rank_score(11, 10) returned -1.04."""
        with pytest.raises(ValueError, match="exceeds vocab_size"):
            endpoint.rank_score(11, 10)

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


class TestDualFloorNTA:
    def test_records_both_floors_and_named_sensitivity_difference(self):
        result = endpoint.dual_floor_nta(
            s_readout=-0.25,
            s_input_embedding=-0.75,
            s_layer0_residual=-0.5,
            s_output=0.0,
            min_denominator=0.01,
        )
        assert result["input_embedding_decoded"] == pytest.approx(2 / 3)
        assert result["layer0_residual_decoded"] == pytest.approx(0.5)
        assert result["sensitivity_minus_primary"] == pytest.approx(-1 / 6)

    def test_one_excluded_floor_makes_the_difference_unavailable(self):
        result = endpoint.dual_floor_nta(
            s_readout=-0.25,
            s_input_embedding=-0.75,
            s_layer0_residual=0.0,
            s_output=0.0,
            min_denominator=0.01,
        )
        assert isinstance(result["layer0_residual_decoded"], endpoint.NTAExcluded)
        assert result["sensitivity_minus_primary"] is None


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

    def test_mezzadri_correction_scales_columns_not_rows(self):
        """Tested directly, because no statistic on the diagonal can tell them apart.

        For ``J = I`` the SVD is ``U = Vt = I`` and ``S = 1``, so the function
        returns Q itself — which makes the correction checkable exactly rather
        than statistically. That matters: a review showed a diagonal-sign test
        passes identically under correct column scaling and wrong row scaling,
        because ``q[i, i]`` picks up ``sign[i]`` either way. The off-diagonal is
        where they differ.
        """
        np = pytest.importorskip("numpy")
        n, seed = 5, 20260726
        returned = endpoint.build_fit_broken_map(np.eye(n), seed=seed)

        rng = np.random.default_rng(seed)
        gaussian = rng.standard_normal((n, n)).astype(np.float64)
        q, r = np.linalg.qr(gaussian)
        column_scaled = q * np.sign(np.diag(r))
        row_scaled = (q.T * np.sign(np.diag(r))).T

        np.testing.assert_allclose(returned, column_scaled, atol=1e-12)
        assert not np.allclose(returned, row_scaled), (
            "column and row scaling coincide for this seed; pick another"
        )

    def test_correction_makes_the_r_diagonal_positive(self):
        """The mathematical content of the Mezzadri fix: LAPACK fixes no sign
        convention on R's diagonal, and Q is Haar only once that is pinned."""
        np = pytest.importorskip("numpy")
        n, seed = 5, 7
        q_corrected = endpoint.build_fit_broken_map(np.eye(n), seed=seed)
        rng = np.random.default_rng(seed)
        gaussian = rng.standard_normal((n, n)).astype(np.float64)
        r_corrected = q_corrected.T @ gaussian
        assert np.all(np.diag(r_corrected) > 0)

    def test_uncorrected_qr_would_fail_the_positivity_property(self):
        """Proves the property above is not vacuous."""
        np = pytest.importorskip("numpy")
        rng = np.random.default_rng(7)
        gaussian = rng.standard_normal((5, 5))
        q, _ = np.linalg.qr(gaussian)
        assert not np.all(np.diag(q.T @ gaussian) > 0)

    def test_dtype_is_preserved(self):
        """A float64 control map for a float32 Jacobian would break the float32
        contract the study asserts at preflight."""
        np = pytest.importorskip("numpy")
        j = np.eye(4, dtype=np.float32)
        assert endpoint.build_fit_broken_map(j, seed=0).dtype == np.float32

    def test_batch_builder_reuses_one_fitted_decomposition(self, monkeypatch):
        np, j = self._fixture(n=8)
        original_svd = np.linalg.svd
        calls = []

        def counted_svd(*args, **kwargs):
            calls.append((args, kwargs))
            return original_svd(*args, **kwargs)

        monkeypatch.setattr(np.linalg, "svd", counted_svd)
        maps, singular_values = endpoint.build_fit_broken_maps(j, [1, 2, 3])
        assert len(maps) == 3
        assert singular_values.shape == (8,)
        assert len(calls) == 1
        for seed, broken in zip([1, 2, 3], maps, strict=True):
            expected = endpoint.build_fit_broken_map(j, seed)
            np.testing.assert_array_equal(broken, expected)

    def test_batch_builder_rejects_empty_or_non_integer_seeds(self):
        _np, j = self._fixture(n=8)
        with pytest.raises(ValueError, match="at least one"):
            endpoint.build_fit_broken_maps(j, [])
        with pytest.raises(TypeError, match="integers"):
            endpoint.build_fit_broken_maps(j, [False])

    def test_runtime_spectrum_evidence_covers_every_singular_value(self):
        _np, j = self._fixture(n=8)
        broken = endpoint.build_fit_broken_map(j, seed=20260726)
        evidence = endpoint.singular_spectrum_evidence(j, broken)
        assert evidence == {
            **evidence,
            "schema": "stage2b-map-spectrum-check/v1",
            "method": "numpy.linalg.svd-allclose/v1",
            "singular_value_count": 8,
            "rtol": endpoint.SINGULAR_SPECTRUM_RTOL,
            "atol": endpoint.SINGULAR_SPECTRUM_ATOL,
            "verified": True,
        }
        assert evidence["max_normalized_error"] <= 1.0
        assert len(evidence["fitted_singular_values_sha256"]) == 64
        assert len(evidence["broken_singular_values_sha256"]) == 64

    def test_runtime_spectrum_evidence_accepts_shared_fitted_values(self):
        _np, j = self._fixture(n=8)
        maps, fitted_values = endpoint.build_fit_broken_maps(j, [20260726])
        observed = endpoint.singular_spectrum_evidence(
            j,
            maps[0],
            fitted_singular_values=fitted_values,
        )
        direct = endpoint.singular_spectrum_evidence(j, maps[0])
        assert observed["verified"] is True
        assert direct["verified"] is True
        assert (
            observed["broken_singular_values_sha256"]
            == direct["broken_singular_values_sha256"]
        )
        assert observed["singular_value_count"] == direct["singular_value_count"] == 8

    def test_runtime_spectrum_evidence_rejects_invalid_shared_values(self):
        np, j = self._fixture(n=8)
        broken = endpoint.build_fit_broken_map(j, seed=20260726)
        with pytest.raises(ValueError, match="finite vector"):
            endpoint.singular_spectrum_evidence(
                j,
                broken,
                fitted_singular_values=np.ones(7),
            )

    def test_runtime_spectrum_evidence_rejects_a_different_spectrum(self):
        _np, j = self._fixture(n=8)
        evidence = endpoint.singular_spectrum_evidence(j, j * 2.0)
        assert evidence["verified"] is False
        assert evidence["max_normalized_error"] > 1.0


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
        """Compares the returned activation, not only the donor id — the vector
        is what enters the measurement."""
        np, residuals = self._residuals()
        a_vec, a_src = endpoint.select_wrong_activation(residuals, "aaa", seed=7)
        b_vec, b_src = endpoint.select_wrong_activation(residuals, "aaa", seed=7)
        assert a_src == b_src
        np.testing.assert_array_equal(a_vec, b_vec)

    def test_pure_source_selection_matches_the_real_activation_path(self):
        _np, residuals = self._residuals()
        source = endpoint.select_wrong_activation_source(
            tuple(residuals),
            "aaa",
            7,
        )
        _, observed = endpoint.select_wrong_activation(residuals, "aaa", seed=7)
        assert observed == source

    def test_pure_source_selection_changes_when_seed_changes(self):
        import hashlib

        prompts = [
            hashlib.sha256(f"donor-source-{index}".encode()).hexdigest()
            for index in range(20)
        ]
        recipient = prompts[0]
        sources = {
            endpoint.select_wrong_activation_source(prompts, recipient, seed)
            for seed in range(32)
        }
        assert recipient not in sources
        assert len(sources) > 5

    def test_preserves_the_float32_tensor_contract(self):
        """The NumPy adapter must not silently widen a live float32 residual."""
        np = pytest.importorskip("numpy")
        residuals = {
            "1" * 64: np.array([1.0, 2.0], dtype=np.float32),
            "2" * 64: np.array([3.0, 4.0], dtype=np.float32),
        }
        wrong, _ = endpoint.select_wrong_activation(residuals, "1" * 64, seed=7)
        assert wrong.dtype == np.float32

    def test_donors_vary_across_prompts_under_one_preregistered_seed(self):
        """A bare default_rng(seed) reset per call returns the same draw every
        time, so one seed across 200 prompts would concentrate every wrong
        activation on a single donor — reproducible and useless as a control."""
        np = pytest.importorskip("numpy")
        import hashlib

        residuals = {
            hashlib.sha256(f"prompt-{i}".encode()).hexdigest(): np.array(
                [float(i + 1), 1.0]
            )
            for i in range(30)
        }
        sources = {
            endpoint.select_wrong_activation(residuals, key, seed=20260728)[1]
            for key in residuals
        }
        assert len(sources) > 5, f"donors concentrated on {len(sources)} prompts"

    def test_zero_target_norm_is_refused(self):
        """Rescaling to a zero norm yields a zero vector: no donor direction and
        no wrong content, which is not the control the design specifies."""
        np = pytest.importorskip("numpy")
        residuals = {"aaa": np.array([0.0, 0.0]), "bbb": np.array([1.0, 2.0])}
        with pytest.raises(ValueError, match="zero norm"):
            endpoint.select_wrong_activation(residuals, "aaa", seed=0)

    def test_raises_when_no_other_prompt_exists(self):
        np = pytest.importorskip("numpy")
        with pytest.raises(ValueError, match="at least two prompts"):
            endpoint.select_wrong_activation({"only": np.array([1.0])}, "only", seed=0)


def test_unratified_policy_helpers_are_absent():
    assert not hasattr(endpoint, "allocate_wrong_layers")
    assert not hasattr(endpoint, "paired_difference_by_cluster")


class TestAssembleFactorialCells:
    def test_simple_effect_is_the_correct_activation_contrast(self):
        """H1 gates on this per the decision-rule table (research.md R9)."""
        out = endpoint.assemble_factorial_cells(0.8, 0.3, 0.2, 0.1)
        assert out["simple_effect_of_map"] == pytest.approx(0.5)

    def test_main_effect_averages_both_contrasts(self):
        out = endpoint.assemble_factorial_cells(0.8, 0.3, 0.2, 0.1)
        assert out["main_effect_of_map"] == pytest.approx((0.5 + 0.1) / 2)

    def test_main_effect_is_smaller_when_the_expected_interaction_holds(self):
        """The design predicts breaking the map costs more at the correct
        activation. Under that prediction the main effect is diluted, which is
        why H1 gates on the simple effect instead (R9)."""
        out = endpoint.assemble_factorial_cells(0.8, 0.3, 0.2, 0.1)
        assert out["main_effect_of_map"] < out["simple_effect_of_map"]
        assert out["interaction"] > 0

    def test_interaction_is_the_difference_of_contrasts(self):
        out = endpoint.assemble_factorial_cells(0.8, 0.3, 0.2, 0.1)
        assert out["interaction"] == pytest.approx(0.5 - 0.1)

    def test_an_excluded_cell_makes_effects_none_not_zero(self):
        """An absent measurement is not a null effect."""
        out = endpoint.assemble_factorial_cells(
            endpoint.NTAExcluded("denominator_below_min", 0.0), 0.3, 0.2, 0.1
        )
        assert out["simple_effect_of_map"] is None
        assert out["main_effect_of_map"] is None
        assert out["excluded"] == ["correct_act_fitted_map"]

    def test_wrong_side_exclusion_leaves_the_simple_effect_intact(self):
        out = endpoint.assemble_factorial_cells(
            0.8, 0.3, endpoint.NTAExcluded("denominator_below_min", 0.0), 0.1
        )
        assert out["simple_effect_of_map"] == pytest.approx(0.5)
        assert out["main_effect_of_map"] is None

    def test_json_null_is_a_present_exclusion_not_a_missing_cell(self):
        out = endpoint.assemble_factorial_cells(None, 0.3, 0.2, 0.1)
        assert out["cells"]["correct_act_fitted_map"] is None
        assert out["simple_effect_of_map"] is None
        assert out["main_effect_of_map"] is None
        assert out["excluded"] == ["correct_act_fitted_map"]


class TestCrossedFactorialRepresentation:
    @staticmethod
    def _factorized():
        donors = [f"donor-{index}" for index in range(8)]
        maps = [f"map-{index}" for index in range(8)]
        return {
            "correct_act_fitted_map": 0.9,
            "correct_act_broken_map": {
                map_id: 0.2 + index / 100 for index, map_id in enumerate(maps)
            },
            "wrong_act_fitted_map": {
                donor_id: 0.4 + index / 100 for index, donor_id in enumerate(donors)
            },
            "wrong_act_broken_map": {
                donor_id: {
                    map_id: 0.1 + donor_index / 100 + map_index / 1000
                    for map_index, map_id in enumerate(maps)
                }
                for donor_index, donor_id in enumerate(donors)
            },
        }

    def test_materializes_all_sixty_four_logical_crossings_losslessly(self):
        result = endpoint.materialize_crossed_factorials(self._factorized())
        assert result["unique_readout_count"] == 81
        assert result["logical_cell_count"] == 64
        assert len(result["factorials"]) == 64
        identities = {
            (cell["donor_assignment_id"], cell["map_draw_id"])
            for cell in result["factorials"]
        }
        assert len(identities) == 64

    def test_materializes_a_fully_excluded_null_tree(self):
        factorized = self._factorized()
        factorized["correct_act_fitted_map"] = None
        factorized["correct_act_broken_map"] = dict.fromkeys(
            factorized["correct_act_broken_map"]
        )
        factorized["wrong_act_fitted_map"] = dict.fromkeys(
            factorized["wrong_act_fitted_map"]
        )
        factorized["wrong_act_broken_map"] = {
            donor_id: dict.fromkeys(row)
            for donor_id, row in factorized["wrong_act_broken_map"].items()
        }
        result = endpoint.materialize_crossed_factorials(factorized)
        assert result["unique_readout_count"] == 81
        assert result["logical_cell_count"] == 64
        assert all(
            len(cell["factorial"]["excluded"]) == 4 for cell in result["factorials"]
        )

    def test_missing_invariant_key_is_still_rejected(self):
        factorized = self._factorized()
        del factorized["correct_act_fitted_map"]
        with pytest.raises(ValueError, match="invariant fitted readout"):
            endpoint.materialize_crossed_factorials(factorized)

    @pytest.mark.parametrize(
        ("mutation", "message"),
        [
            (lambda value: value["correct_act_broken_map"].pop("map-7"), "eight map"),
            (lambda value: value["wrong_act_fitted_map"].pop("donor-7"), "eight donor"),
            (
                lambda value: value["wrong_act_broken_map"]["donor-0"].pop("map-7"),
                "complete 8x8",
            ),
        ],
    )
    def test_rejects_incomplete_factorized_provenance(self, mutation, message):
        factorized = self._factorized()
        mutation(factorized)
        with pytest.raises(ValueError, match=message):
            endpoint.materialize_crossed_factorials(factorized)
