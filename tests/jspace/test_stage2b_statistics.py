"""Ratified Stage 2b pilot statistics on fixed CPU data.

No model, lens, CUDA, notebook execution, or scientific input is used here.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import sys

import pytest

np = pytest.importorskip("numpy")

_MODULE_PATH = (
    pathlib.Path(__file__).resolve().parents[2]
    / "EvoScientist/skills/jspace-research-operations/scripts/stage2b_statistics.py"
)
sys.path.insert(0, str(_MODULE_PATH.parent))
_spec = importlib.util.spec_from_file_location("stage2b_statistics", _MODULE_PATH)
assert _spec is not None
assert _spec.loader is not None
statistics = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(statistics)


def _digest_seed(namespace: str) -> tuple[str, int]:
    digest = hashlib.sha256(namespace.encode("ascii")).hexdigest()
    return digest, int.from_bytes(bytes.fromhex(digest)[:8], "big", signed=False)


class TestSeedDerivation:
    def test_crossing_vectors_are_exactly_namespaced(self):
        vectors = statistics.derive_crossing_seed_vectors()
        assert [entry["id"] for entry in vectors["donors"]] == [
            f"donor-{index}" for index in range(8)
        ]
        assert [entry["id"] for entry in vectors["maps"]] == [
            f"map-{index}" for index in range(8)
        ]
        for kind, stem in (
            ("donors", "donor-assignment"),
            ("maps", "broken-map"),
        ):
            for index, entry in enumerate(vectors[kind]):
                namespace = f"jspace-stage2b/v1|{stem}|{index}"
                digest, seed = _digest_seed(namespace)
                assert entry == {
                    "id": f"{'donor' if kind == 'donors' else 'map'}-{index}",
                    "index": index,
                    "namespace": namespace,
                    "sha256": digest,
                    "seed": seed,
                    "byte_order": "big",
                    "bit_generator": "PCG64",
                }
        assert len({entry["seed"] for entry in vectors["donors"]}) == 8
        assert len({entry["seed"] for entry in vectors["maps"]}) == 8

    @pytest.mark.parametrize("run_mode", ["pilot", "confirmatory"])
    def test_bootstrap_identity_is_exact_and_explicit(self, run_mode):
        namespace = f"jspace-stage2b/v1|{run_mode}|bootstrap-v1"
        digest, seed = _digest_seed(namespace)
        identity = statistics.bootstrap_rng_identity(
            run_mode, numpy_version=np.__version__
        )
        assert identity == {
            "namespace": namespace,
            "sha256": digest,
            "seed": seed,
            "byte_order": "big",
            "bit_generator": "PCG64",
            "numpy_version": np.__version__,
            "iterations": 20_000,
            "weight_distribution": "Exp(1)",
        }

    def test_invalid_run_mode_fails_closed(self):
        with pytest.raises(statistics.Stage2bStatisticsError) as exc:
            statistics.bootstrap_rng_identity(
                "exploratory", numpy_version=np.__version__
            )
        assert exc.value.code == "invalid_run_mode"


class TestDenominatorDerivation:
    def test_exact_80_value_linear_quantile_and_digest(self):
        denominators = [0.1 + index / 1000 for index in range(80)]
        result = statistics.derive_nta_min_denominator(denominators)
        expected = float(np.quantile(denominators, 0.05, method="linear"))
        payload = (
            json.dumps(
                denominators,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            )
            + "\n"
        )
        assert result == {
            "source_floor": "input_embedding_decoded",
            "source_count": 80,
            "source_denominators_sha256": hashlib.sha256(
                payload.encode("ascii")
            ).hexdigest(),
            "quantile": 0.05,
            "quantile_method": "linear",
            "derived_value": pytest.approx(expected),
        }

    @pytest.mark.parametrize(
        ("denominators", "code"),
        [
            ([0.1] * 79, "denominator_source_count"),
            ([0.1] * 79 + [float("nan")], "denominator_source_nonfinite"),
            ([-0.1] * 80, "denominator_guard_nonpositive"),
        ],
    )
    def test_invalid_guard_source_fails_closed(self, denominators, code):
        with pytest.raises(statistics.Stage2bStatisticsError) as exc:
            statistics.derive_nta_min_denominator(denominators)
        assert exc.value.code == code


def _factorized():
    map_ids = [f"map-{index}" for index in range(8)]
    donor_ids = [f"donor-{index}" for index in range(8)]
    return {
        "correct_act_fitted_map": 1.0,
        "correct_act_broken_map": {
            map_id: 0.2 + map_index / 100 for map_index, map_id in enumerate(map_ids)
        },
        "wrong_act_fitted_map": {
            donor_id: 0.5 + donor_index / 100
            for donor_index, donor_id in enumerate(donor_ids)
        },
        "wrong_act_broken_map": {
            donor_id: {
                map_id: 0.4 + donor_index / 100 + map_index / 1000
                for map_index, map_id in enumerate(map_ids)
            }
            for donor_index, donor_id in enumerate(donor_ids)
        },
    }


class TestCrossedEffects:
    def test_effects_preserve_all_draws_then_average_equally(self):
        result = statistics.crossed_prompt_effects(_factorized())
        assert len(result["correct_effects"]) == 8
        assert len(result["wrong_effects"]) == 64
        assert len(result["interactions"]) == 64
        assert result["correct_effect_mean"] == pytest.approx(
            np.mean([1.0 - (0.2 + map_index / 100) for map_index in range(8)])
        )
        expected_wrong = [
            (0.5 + donor_index / 100) - (0.4 + donor_index / 100 + map_index / 1000)
            for donor_index in range(8)
            for map_index in range(8)
        ]
        assert result["wrong_effect_mean"] == pytest.approx(np.mean(expected_wrong))
        assert result["interaction_mean"] == pytest.approx(
            result["correct_effect_mean"] - result["wrong_effect_mean"]
        )

    def test_null_or_incomplete_factorial_is_an_excluded_locus(self):
        factorized = _factorized()
        factorized["wrong_act_broken_map"]["donor-0"]["map-0"] = None
        result = statistics.crossed_prompt_effects(factorized)
        assert result == {
            "eligible": False,
            "exclusion_reason": "floor_denominator_excluded",
        }


def _prompt_rows(*, excluded: set[tuple[str, int]] | None = None):
    excluded = excluded or set()
    rows = []
    for category_index in range(5):
        category = f"category-{category_index}"
        for prompt_index in range(4):
            prompt_id = f"{category}-prompt-{prompt_index}"
            rows.append(
                {
                    "prompt_sha256": prompt_id,
                    "category": category,
                    "eligible": (category, prompt_index) not in excluded,
                    "value": float(category_index + prompt_index / 10),
                }
            )
    return rows


class TestCoverageAndPointEstimate:
    def test_complete_pilot_is_defined(self):
        coverage = statistics.check_floor_layer_coverage(_prompt_rows())
        assert coverage["defined"] is True
        assert coverage["eligible_prompt_count"] == 20
        assert set(coverage["eligible_by_category"].values()) == {4}

    def test_18_of_20_is_still_undefined_if_one_category_has_only_two(self):
        rows = _prompt_rows(excluded={("category-0", 0), ("category-0", 1)})
        coverage = statistics.check_floor_layer_coverage(rows)
        assert coverage["eligible_prompt_count"] == 18
        assert coverage["defined"] is False
        assert coverage["reason"] == "insufficient_category_coverage"

    def test_17_of_20_is_undefined_even_with_three_per_category(self):
        rows = _prompt_rows(
            excluded={
                ("category-0", 0),
                ("category-1", 0),
                ("category-2", 0),
            }
        )
        coverage = statistics.check_floor_layer_coverage(rows)
        assert coverage["eligible_prompt_count"] == 17
        assert coverage["defined"] is False
        assert coverage["reason"] == "insufficient_layer_coverage"

    def test_category_balanced_mean_does_not_weight_by_retained_counts(self):
        rows = _prompt_rows(excluded={("category-0", 0)})
        eligible = [row for row in rows if row["eligible"]]
        expected = np.mean(
            [
                np.mean(
                    [
                        row["value"]
                        for row in eligible
                        if row["category"] == f"category-{category_index}"
                    ]
                )
                for category_index in range(5)
            ]
        )
        assert statistics.category_balanced_mean(eligible) == pytest.approx(expected)
        assert statistics.category_balanced_mean(eligible) != pytest.approx(
            np.mean([row["value"] for row in eligible])
        )


def _product_rows():
    rows = []
    for prompt in _prompt_rows():
        for donor_index in range(8):
            for map_index in range(8):
                rows.append(
                    {
                        "prompt_sha256": prompt["prompt_sha256"],
                        "category": prompt["category"],
                        "donor_assignment_id": f"donor-{donor_index}",
                        "map_draw_id": f"map-{map_index}",
                        "value": (
                            prompt["value"] + donor_index / 100 + map_index / 1000
                        ),
                    }
                )
    return rows


class TestIntervals:
    def test_primary_interval_is_exactly_reproducible(self):
        first = statistics.category_stratified_prompt_interval(_prompt_rows())
        second = statistics.category_stratified_prompt_interval(_prompt_rows())
        assert first == second
        assert first["method"] == "category_stratified_prompt_percentile"
        assert first["iterations"] == 20_000
        assert first["finite_replicates"] == 20_000
        assert first["ci_level"] == 0.99
        assert first["quantile_method"] == "linear"
        assert first["lower"] <= first["point_estimate"] <= first["upper"]

    def test_product_weight_interval_is_exactly_reproducible(self):
        first = statistics.product_weight_interval(_product_rows())
        second = statistics.product_weight_interval(_product_rows())
        assert first == second
        assert first["method"] == "prompt_donor_map_product_weight_percentile"
        assert first["iterations"] == 20_000
        assert first["finite_replicates"] == 20_000
        assert first["weight_distribution"] == "Exp(1)"
        assert first["lower"] <= first["point_estimate"] <= first["upper"]

    def test_interval_refuses_low_coverage(self):
        rows = _prompt_rows(excluded={("category-0", 0), ("category-0", 1)})
        with pytest.raises(statistics.Stage2bStatisticsError) as exc:
            statistics.category_stratified_prompt_interval(rows)
        assert exc.value.code == "coverage_undefined"


class TestPilotThresholdDerivation:
    def _estimates(self, value=0.4):
        return [
            {
                "floor": "input_embedding_decoded",
                "layer": layer,
                "estimand": estimand,
                "method": "category_stratified_prompt_percentile",
                "defined": True,
                "point_estimate": value + index / 100,
            }
            for index, (layer, estimand) in enumerate(
                (
                    (6, "correct_effect"),
                    (6, "interaction"),
                    (13, "correct_effect"),
                    (13, "interaction"),
                    (20, "correct_effect"),
                    (20, "interaction"),
                    (26, "correct_effect"),
                    (26, "interaction"),
                )
            )
        ]

    def test_four_layer_vectors_are_half_positive_primary_means(self):
        result = statistics.derive_pilot_thresholds(
            self._estimates(),
            pilot_measurement_sha256="a" * 64,
            derivation_code_sha256="b" * 64,
        )
        assert result["available"] is True
        assert result["source_floor"] == "input_embedding_decoded"
        assert result["factor"] == 0.5
        assert result["layer_order"] == [6, 13, 20, 26]
        assert result["SPEC_MIN_EFFECT"] == pytest.approx([0.2, 0.21, 0.22, 0.23])
        assert result["INTERACTION_MIN_EFFECT"] == pytest.approx(
            [0.205, 0.215, 0.225, 0.235]
        )
        assert "decision" not in result
        assert "pass" not in result

    @pytest.mark.parametrize(
        ("field", "value"), [("defined", False), ("point_estimate", 0.0)]
    )
    def test_any_undefined_or_nonpositive_source_blocks_both_vectors(
        self, field, value
    ):
        estimates = self._estimates()
        estimates[0][field] = value
        result = statistics.derive_pilot_thresholds(
            estimates,
            pilot_measurement_sha256="a" * 64,
            derivation_code_sha256="b" * 64,
        )
        assert result["available"] is False
        assert "SPEC_MIN_EFFECT" not in result
        assert "INTERACTION_MIN_EFFECT" not in result


def _raw_pilot_records():
    records = []
    for category_index in range(5):
        category = f"category-{category_index}"
        for prompt_index in range(4):
            prompt = f"{category}-prompt-{prompt_index}"
            global_prompt_index = category_index * 4 + prompt_index
            for layer_index, layer in enumerate((6, 13, 20, 26)):
                locus_index = global_prompt_index * 4 + layer_index
                records.append(
                    {
                        "prompt_sha256": prompt,
                        "category": category,
                        "layer": layer,
                        "floor_scores": {
                            "input_embedding_decoded": -0.2 - locus_index / 100,
                            "layer0_residual_decoded": -0.5,
                            "output_decoded": 0.0,
                        },
                        "factorized_scores": {
                            "correct_act_fitted_map": -0.05,
                            "correct_act_broken_map": {
                                f"map-{map_index}": -0.35 - map_index / 1000
                                for map_index in range(8)
                            },
                            "wrong_act_fitted_map": {
                                f"donor-{donor_index}": -0.25 - donor_index / 1000
                                for donor_index in range(8)
                            },
                            "wrong_act_broken_map": {
                                f"donor-{donor_index}": {
                                    f"map-{map_index}": -0.35
                                    - donor_index / 1000
                                    - map_index / 10_000
                                    for map_index in range(8)
                                }
                                for donor_index in range(8)
                            },
                        },
                    }
                )
    return records


class TestPilotInferencePacket:
    def test_guard_then_nta_then_inference_is_one_score_only_pipeline(self):
        raw = _raw_pilot_records()
        records, denominator = statistics.materialize_pilot_nta(raw)
        assert denominator["source_count"] == 80
        assert len(denominator["source_order"]) == 80
        assert all("factorized_nta" in record for record in records)
        assert all("floor_status" in record for record in records)

        inference = statistics.build_pilot_inference(
            records,
            denominator,
            derivation_code_sha256="d" * 64,
            numpy_version=np.__version__,
        )
        assert len(inference["coverage"]) == 8
        assert len(inference["prompt_layer_effects"]) == 160
        assert len(inference["layer_estimates"]) == 48
        assert inference["threshold_derivation"]["available"] is True
        assert (
            inference["threshold_derivation"]["pilot_measurement_sha256"]
            == (inference["pilot_measurement_sha256"])
        )
        assert "decision" not in inference
        assert "gates" not in inference
