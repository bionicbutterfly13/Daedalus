"""Ratified Stage 2b pilot statistics, independent of model and GPU code.

Every stochastic helper constructs NumPy ``Generator(PCG64(seed))`` explicitly.
The module accepts retained normalized scores and identities only; it cannot run a
model, load a lens, authorize execution, or emit a scientific decision.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any, NoReturn

N_DONORS = 8
N_MAPS = 8
N_PILOT_PROMPTS = 20
N_CATEGORIES = 5
PILOT_MIN_LAYER_PROMPTS = 18
PILOT_MIN_CATEGORY_PROMPTS = 3
BOOTSTRAP_ITERATIONS = 20_000
BOOTSTRAP_CI_LEVEL = 0.99
LOWER_QUANTILE = 0.005
UPPER_QUANTILE = 0.995
QUANTILE_METHOD = "linear"
BIT_GENERATOR = "PCG64"
PRODUCT_WEIGHT_DISTRIBUTION = "Exp(1)"
PRIMARY_FLOOR_ID = "input_embedding_decoded"
SELECTED_LAYERS = (6, 13, 20, 26)

__all__ = [
    "BIT_GENERATOR",
    "BOOTSTRAP_CI_LEVEL",
    "BOOTSTRAP_ITERATIONS",
    "PILOT_MIN_CATEGORY_PROMPTS",
    "PILOT_MIN_LAYER_PROMPTS",
    "PRODUCT_WEIGHT_DISTRIBUTION",
    "Stage2bStatisticsError",
    "bootstrap_rng_identity",
    "build_pilot_inference",
    "category_balanced_mean",
    "category_stratified_prompt_interval",
    "check_floor_layer_coverage",
    "crossed_prompt_effects",
    "derive_crossing_seed_vectors",
    "derive_nta_min_denominator",
    "derive_pilot_thresholds",
    "derive_seed_identity",
    "materialize_pilot_nta",
    "product_weight_interval",
]


class Stage2bStatisticsError(ValueError):
    """Fail-closed statistical-contract error with a stable code."""

    def __init__(self, code: str, message: str, **detail: Any) -> None:
        super().__init__(message)
        self.code = code
        self.detail = detail


def _fail(code: str, message: str, **detail: Any) -> NoReturn:
    raise Stage2bStatisticsError(code, message, **detail)


def _finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _canonical_sha256(value: Any) -> str:
    try:
        payload = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        _fail("canonicalization", f"value is not canonical finite JSON: {exc}")
    return hashlib.sha256((payload + "\n").encode("ascii")).hexdigest()


def derive_seed_identity(
    *, identifier: str, index: int, namespace: str
) -> dict[str, Any]:
    """Derive one unsigned big-endian seed from an exact ASCII namespace."""
    if not isinstance(identifier, str) or not identifier:
        _fail("seed_identity", "seed identifier must be a non-empty string")
    if not isinstance(index, int) or isinstance(index, bool) or index < 0:
        _fail("seed_index", "seed index must be a non-negative integer", index=index)
    try:
        digest_bytes = hashlib.sha256(namespace.encode("ascii")).digest()
    except (AttributeError, UnicodeEncodeError) as exc:
        _fail("seed_namespace", f"seed namespace must be an ASCII string: {exc}")
    return {
        "id": identifier,
        "index": index,
        "namespace": namespace,
        "sha256": digest_bytes.hex(),
        "seed": int.from_bytes(digest_bytes[:8], "big", signed=False),
        "byte_order": "big",
        "bit_generator": BIT_GENERATOR,
    }


def derive_crossing_seed_vectors() -> dict[str, list[dict[str, Any]]]:
    """Return the ratified eight donor and eight map seed identities."""
    donors = [
        derive_seed_identity(
            identifier=f"donor-{index}",
            index=index,
            namespace=f"jspace-stage2b/v1|donor-assignment|{index}",
        )
        for index in range(N_DONORS)
    ]
    maps = [
        derive_seed_identity(
            identifier=f"map-{index}",
            index=index,
            namespace=f"jspace-stage2b/v1|broken-map|{index}",
        )
        for index in range(N_MAPS)
    ]
    for kind, entries in (("donor", donors), ("map", maps)):
        if len({entry["id"] for entry in entries}) != len(entries) or len(
            {entry["seed"] for entry in entries}
        ) != len(entries):
            _fail(
                "seed_collision",
                f"{kind} seed derivation produced an identity or seed collision",
            )
    return {"donors": donors, "maps": maps}


def bootstrap_rng_identity(
    run_mode: str,
    *,
    numpy_version: str,
) -> dict[str, Any]:
    """Return the exact root identity for each independently constructed interval RNG."""
    if run_mode not in {"pilot", "confirmatory"}:
        _fail(
            "invalid_run_mode",
            "bootstrap run mode must be 'pilot' or 'confirmatory'",
            run_mode=run_mode,
        )
    namespace = f"jspace-stage2b/v1|{run_mode}|bootstrap-v1"
    digest = hashlib.sha256(namespace.encode("ascii")).digest()
    return {
        "namespace": namespace,
        "sha256": digest.hex(),
        "seed": int.from_bytes(digest[:8], "big", signed=False),
        "byte_order": "big",
        "bit_generator": BIT_GENERATOR,
        "numpy_version": numpy_version,
        "iterations": BOOTSTRAP_ITERATIONS,
        "weight_distribution": PRODUCT_WEIGHT_DISTRIBUTION,
    }


def _pilot_rng(*, numpy_version: str | None = None):
    import numpy as np

    identity = bootstrap_rng_identity(
        "pilot", numpy_version=numpy_version or np.__version__
    )
    return np.random.Generator(np.random.PCG64(identity["seed"])), identity


def derive_nta_min_denominator(
    denominators: Sequence[float],
) -> dict[str, Any]:
    """Derive the run-wide guard from exactly 80 retained primary denominators."""
    import numpy as np

    values = list(denominators)
    if len(values) != N_PILOT_PROMPTS * len(SELECTED_LAYERS):
        _fail(
            "denominator_source_count",
            "NTA guard requires exactly 80 primary-floor denominators",
            observed=len(values),
            expected=80,
        )
    if not all(_finite_number(value) for value in values):
        _fail(
            "denominator_source_nonfinite",
            "every primary-floor denominator must be finite before guard derivation",
        )
    numeric = [float(value) for value in values]
    derived = float(np.quantile(numeric, 0.05, method=QUANTILE_METHOD))
    if not math.isfinite(derived) or derived <= 0:
        _fail(
            "denominator_guard_nonpositive",
            "derived NTA denominator guard must be finite and strictly positive",
            observed=derived,
        )
    return {
        "source_floor": PRIMARY_FLOOR_ID,
        "source_count": len(numeric),
        "source_denominators_sha256": _canonical_sha256(numeric),
        "quantile": 0.05,
        "quantile_method": QUANTILE_METHOD,
        "derived_value": derived,
    }


def _map_factorized(tree: Any, transform: Any) -> Any:
    if isinstance(tree, Mapping):
        return {key: _map_factorized(value, transform) for key, value in tree.items()}
    return transform(tree)


def _difference_tree(primary: Any, sensitivity: Any) -> Any:
    if isinstance(primary, Mapping) and isinstance(sensitivity, Mapping):
        if set(primary) != set(sensitivity):
            _fail("floor_tree_mismatch", "floor NTA trees have different keys")
        return {
            key: _difference_tree(primary[key], sensitivity[key]) for key in primary
        }
    if primary is None or sensitivity is None:
        return None
    if not _finite_number(primary) or not _finite_number(sensitivity):
        _fail("floor_tree_nonfinite", "numeric floor NTA leaves must be finite")
    return float(sensitivity) - float(primary)


def _validate_pilot_record_population(
    records: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    materialized = list(records)
    if len(materialized) != N_PILOT_PROMPTS * len(SELECTED_LAYERS):
        _fail(
            "pilot_locus_count",
            "pilot statistics require exactly 80 prompt-layer records",
            observed=len(materialized),
        )
    loci = [
        (record.get("prompt_sha256"), record.get("layer")) for record in materialized
    ]
    if len(set(loci)) != len(loci):
        _fail("pilot_locus_duplicate", "pilot prompt-layer loci must be unique")
    prompts = sorted({record.get("prompt_sha256") for record in materialized})
    if len(prompts) != N_PILOT_PROMPTS or any(
        not isinstance(prompt, str) or not prompt for prompt in prompts
    ):
        _fail(
            "pilot_prompt_population", "pilot statistics require 20 prompt identities"
        )
    expected_loci = {(prompt, layer) for prompt in prompts for layer in SELECTED_LAYERS}
    if set(loci) != expected_loci:
        _fail(
            "pilot_locus_coverage",
            "pilot statistics require every prompt at all four selected layers",
        )
    prompt_categories = {}
    for record in materialized:
        prompt = record.get("prompt_sha256")
        category = record.get("category")
        if not isinstance(category, str) or not category:
            _fail("pilot_category_population", "every record needs a category")
        if prompt in prompt_categories and prompt_categories[prompt] != category:
            _fail(
                "pilot_category_population", "a prompt changes category across layers"
            )
        prompt_categories[prompt] = category
    category_counts = {
        category: sum(value == category for value in prompt_categories.values())
        for category in set(prompt_categories.values())
    }
    if len(category_counts) != N_CATEGORIES or set(category_counts.values()) != {4}:
        _fail(
            "pilot_category_population",
            "pilot statistics require four prompts in each of five categories",
        )
    return materialized


def materialize_pilot_nta(
    records: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Derive one guard, then compute both NTA floors from retained scores."""
    from stage2b_endpoint import NTAExcluded, dual_floor_nta

    materialized = _validate_pilot_record_population(records)
    ordered = sorted(
        materialized,
        key=lambda record: (
            str(record["prompt_sha256"]),
            SELECTED_LAYERS.index(int(record["layer"])),
        ),
    )
    denominators = []
    for record in ordered:
        floors = record.get("floor_scores")
        if not isinstance(floors, Mapping) or set(floors) != {
            "input_embedding_decoded",
            "layer0_residual_decoded",
            "output_decoded",
        }:
            _fail("floor_scores", "each record needs the exact three retained scores")
        if not all(_finite_number(value) for value in floors.values()):
            _fail(
                "floor_scores_nonfinite", "retained floor/output scores must be finite"
            )
        denominators.append(
            float(floors["output_decoded"]) - float(floors["input_embedding_decoded"])
        )
    derivation = derive_nta_min_denominator(denominators)
    derivation["source_order"] = [
        {
            "prompt_sha256": str(record["prompt_sha256"]),
            "layer": int(record["layer"]),
        }
        for record in ordered
    ]
    guard = float(derivation["derived_value"])
    output_records: list[dict[str, Any]] = []
    for source in materialized:
        record = deepcopy(dict(source))
        floors = record["floor_scores"]
        scores = record.get("factorized_scores")
        if not isinstance(scores, Mapping):
            _fail("factorized_scores", "record factorized_scores must be an object")
        _exact_factor_keys(scores)
        input_floor = float(floors["input_embedding_decoded"])
        layer0_floor = float(floors["layer0_residual_decoded"])
        output_floor = float(floors["output_decoded"])
        dual_tree = _map_factorized(
            scores,
            lambda score, input_floor=input_floor, layer0_floor=layer0_floor, output_floor=output_floor: (
                dual_floor_nta(
                    s_readout=float(score),
                    s_input_embedding=input_floor,
                    s_layer0_residual=layer0_floor,
                    s_output=output_floor,
                    min_denominator=guard,
                )
            ),
        )

        def select(value: Any, floor: str) -> Any:
            if isinstance(value, Mapping) and set(value) == {
                "input_embedding_decoded",
                "layer0_residual_decoded",
                "sensitivity_minus_primary",
            }:
                selected = value[floor]
                return None if isinstance(selected, NTAExcluded) else selected
            if isinstance(value, Mapping):
                return {key: select(child, floor) for key, child in value.items()}
            _fail("dual_floor_tree", "dual-floor tree is malformed")

        primary = select(dual_tree, "input_embedding_decoded")
        sensitivity = select(dual_tree, "layer0_residual_decoded")
        primary_denominator = float(floors["output_decoded"]) - float(
            floors["input_embedding_decoded"]
        )
        sensitivity_denominator = float(floors["output_decoded"]) - float(
            floors["layer0_residual_decoded"]
        )
        record["floor_status"] = {
            "input_embedding_decoded": {
                "denominator": primary_denominator,
                "eligible": primary_denominator > guard,
                "exclusion_reason": (
                    None
                    if primary_denominator > guard
                    else "denominator_not_greater_than_guard"
                ),
            },
            "layer0_residual_decoded": {
                "denominator": sensitivity_denominator,
                "eligible": sensitivity_denominator > guard,
                "exclusion_reason": (
                    None
                    if sensitivity_denominator > guard
                    else "denominator_not_greater_than_guard"
                ),
            },
        }
        record["factorized_nta"] = {
            "input_embedding_decoded": primary,
            "layer0_residual_decoded": sensitivity,
            "sensitivity_minus_primary": _difference_tree(primary, sensitivity),
        }
        output_records.append(record)
    return output_records, derivation


def _exact_factor_keys(factorized: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    required = {
        "correct_act_fitted_map",
        "correct_act_broken_map",
        "wrong_act_fitted_map",
        "wrong_act_broken_map",
    }
    if set(factorized) != required:
        _fail(
            "crossing_incomplete",
            "factorized floor tree fields do not exactly match the contract",
            missing=sorted(required - set(factorized)),
            unknown=sorted(set(factorized) - required),
        )
    map_values = factorized["correct_act_broken_map"]
    donor_values = factorized["wrong_act_fitted_map"]
    matrix = factorized["wrong_act_broken_map"]
    if not all(
        isinstance(value, Mapping) for value in (map_values, donor_values, matrix)
    ):
        _fail("crossing_incomplete", "factorized draw dimensions must be mappings")
    map_ids = [f"map-{index}" for index in range(N_MAPS)]
    donor_ids = [f"donor-{index}" for index in range(N_DONORS)]
    if set(map_values) != set(map_ids) or set(donor_values) != set(donor_ids):
        _fail("crossing_incomplete", "factorized donor/map IDs are not exact")
    if set(matrix) != set(donor_ids) or any(
        not isinstance(matrix[donor_id], Mapping)
        or set(matrix[donor_id]) != set(map_ids)
        for donor_id in donor_ids
    ):
        _fail("crossing_incomplete", "factorized donor-by-map matrix is incomplete")
    return donor_ids, map_ids


def crossed_prompt_effects(factorized: Mapping[str, Any]) -> dict[str, Any]:
    """Preserve draw-level effects and compute equal-weight prompt-layer means."""
    donor_ids, map_ids = _exact_factor_keys(factorized)
    values = [factorized["correct_act_fitted_map"]]
    values.extend(factorized["correct_act_broken_map"][map_id] for map_id in map_ids)
    values.extend(
        factorized["wrong_act_fitted_map"][donor_id] for donor_id in donor_ids
    )
    values.extend(
        factorized["wrong_act_broken_map"][donor_id][map_id]
        for donor_id in donor_ids
        for map_id in map_ids
    )
    if any(value is None for value in values):
        return {
            "eligible": False,
            "exclusion_reason": "floor_denominator_excluded",
        }
    if not all(_finite_number(value) for value in values):
        _fail(
            "factorized_nonfinite",
            "eligible factorized NTA trees must contain only finite numbers",
        )

    correct_fitted = float(factorized["correct_act_fitted_map"])
    correct_effects = [
        {
            "map_draw_id": map_id,
            "value": correct_fitted
            - float(factorized["correct_act_broken_map"][map_id]),
        }
        for map_id in map_ids
    ]
    wrong_effects = []
    interactions = []
    for donor_id in donor_ids:
        wrong_fitted = float(factorized["wrong_act_fitted_map"][donor_id])
        for map_id in map_ids:
            wrong = wrong_fitted - float(
                factorized["wrong_act_broken_map"][donor_id][map_id]
            )
            correct = next(
                item["value"]
                for item in correct_effects
                if item["map_draw_id"] == map_id
            )
            wrong_effects.append(
                {
                    "donor_assignment_id": donor_id,
                    "map_draw_id": map_id,
                    "value": wrong,
                }
            )
            interactions.append(
                {
                    "donor_assignment_id": donor_id,
                    "map_draw_id": map_id,
                    "value": correct - wrong,
                }
            )
    correct_mean = sum(item["value"] for item in correct_effects) / N_MAPS
    wrong_mean = sum(item["value"] for item in wrong_effects) / (N_DONORS * N_MAPS)
    interaction_mean = sum(item["value"] for item in interactions) / (N_DONORS * N_MAPS)
    return {
        "eligible": True,
        "exclusion_reason": None,
        "correct_effects": correct_effects,
        "wrong_effects": wrong_effects,
        "interactions": interactions,
        "correct_effect_mean": correct_mean,
        "wrong_effect_mean": wrong_mean,
        "interaction_mean": interaction_mean,
    }


def _validate_prompt_rows(rows: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    materialized = list(rows)
    if len(materialized) != N_PILOT_PROMPTS:
        _fail(
            "coverage_population",
            "pilot coverage requires exactly 20 prompt rows",
            observed=len(materialized),
        )
    prompts = [row.get("prompt_sha256") for row in materialized]
    categories = [row.get("category") for row in materialized]
    if (
        not all(isinstance(value, str) and value for value in prompts + categories)
        or len(set(prompts)) != N_PILOT_PROMPTS
        or len(set(categories)) != N_CATEGORIES
    ):
        _fail(
            "coverage_population",
            "pilot rows require 20 unique prompts in five non-empty categories",
        )
    category_counts = {
        category: sum(row.get("category") == category for row in materialized)
        for category in set(categories)
    }
    if set(category_counts.values()) != {4}:
        _fail(
            "coverage_population",
            "the pilot population must contain four prompts in each category",
            observed=category_counts,
        )
    if not all(isinstance(row.get("eligible"), bool) for row in materialized):
        _fail("coverage_population", "every prompt row needs a boolean eligible field")
    return materialized


def check_floor_layer_coverage(
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Apply the fixed 18/20 and 3/4-per-category pilot coverage rule."""
    materialized = _validate_prompt_rows(rows)
    categories = sorted({str(row["category"]) for row in materialized})
    eligible = [row for row in materialized if row["eligible"]]
    by_category = {
        category: sum(
            row["eligible"] and row["category"] == category for row in materialized
        )
        for category in categories
    }
    result: dict[str, Any] = {
        "eligible_prompt_count": len(eligible),
        "eligible_by_category": by_category,
        "excluded_prompt_sha256": sorted(
            str(row["prompt_sha256"]) for row in materialized if not row["eligible"]
        ),
    }
    if len(eligible) < PILOT_MIN_LAYER_PROMPTS:
        return {
            **result,
            "defined": False,
            "reason": "insufficient_layer_coverage",
        }
    if any(count < PILOT_MIN_CATEGORY_PROMPTS for count in by_category.values()):
        return {
            **result,
            "defined": False,
            "reason": "insufficient_category_coverage",
        }
    return {**result, "defined": True, "reason": None}


def category_balanced_mean(
    rows: Sequence[Mapping[str, Any]],
    *,
    value_key: str = "value",
) -> float:
    """Mean within category, followed by an equal mean of five categories."""
    materialized = list(rows)
    categories = sorted({row.get("category") for row in materialized})
    if len(categories) != N_CATEGORIES or not all(
        isinstance(category, str) and category for category in categories
    ):
        _fail("category_structure", "point estimate requires exactly five categories")
    category_means = []
    for category in categories:
        values = [
            row.get(value_key)
            for row in materialized
            if row.get("category") == category
        ]
        if not values or not all(_finite_number(value) for value in values):
            _fail(
                "category_value",
                "each category requires at least one finite value",
                category=category,
            )
        category_means.append(sum(float(value) for value in values) / len(values))
    return sum(category_means) / N_CATEGORIES


def _interval_result(
    *,
    method: str,
    point_estimate: float,
    replicates: Any,
    identity: Mapping[str, Any],
    weight_distribution: str | None = None,
) -> dict[str, Any]:
    import numpy as np

    array = np.asarray(replicates, dtype=np.float64)
    finite_count = int(np.isfinite(array).sum())
    if array.shape != (BOOTSTRAP_ITERATIONS,) or finite_count != BOOTSTRAP_ITERATIONS:
        _fail(
            "bootstrap_nonfinite",
            "every one of the 20,000 bootstrap statistics must be finite",
            observed_shape=list(array.shape),
            finite_replicates=finite_count,
        )
    lower, upper = np.quantile(
        array,
        [LOWER_QUANTILE, UPPER_QUANTILE],
        method=QUANTILE_METHOD,
    )
    result = {
        "method": method,
        "point_estimate": float(point_estimate),
        "iterations": BOOTSTRAP_ITERATIONS,
        "finite_replicates": finite_count,
        "ci_level": BOOTSTRAP_CI_LEVEL,
        "quantile_method": QUANTILE_METHOD,
        "lower": float(lower),
        "upper": float(upper),
        "rng": dict(identity),
    }
    if weight_distribution is not None:
        result["weight_distribution"] = weight_distribution
    return result


def category_stratified_prompt_interval(
    rows: Sequence[Mapping[str, Any]],
    *,
    numpy_version: str | None = None,
) -> dict[str, Any]:
    """Category-preserving prompt bootstrap for one floor-layer-estimand."""
    import numpy as np

    materialized = _validate_prompt_rows(rows)
    coverage = check_floor_layer_coverage(materialized)
    if not coverage["defined"]:
        _fail(
            "coverage_undefined",
            "primary interval is undefined because pilot coverage failed",
            coverage=coverage,
        )
    eligible = [row for row in materialized if row["eligible"]]
    if not all(_finite_number(row.get("value")) for row in eligible):
        _fail("category_value", "eligible prompt effects must be finite")
    point = category_balanced_mean(eligible)
    rng, identity = _pilot_rng(numpy_version=numpy_version)
    category_replicates = []
    for category in sorted({str(row["category"]) for row in materialized}):
        values = np.asarray(
            [float(row["value"]) for row in eligible if row["category"] == category],
            dtype=np.float64,
        )
        indices = rng.integers(
            0,
            len(values),
            size=(BOOTSTRAP_ITERATIONS, len(values)),
        )
        category_replicates.append(values[indices].mean(axis=1))
    replicates = np.mean(np.stack(category_replicates, axis=1), axis=1)
    return _interval_result(
        method="category_stratified_prompt_percentile",
        point_estimate=point,
        replicates=replicates,
        identity=identity,
    )


def product_weight_interval(
    rows: Sequence[Mapping[str, Any]],
    *,
    numpy_version: str | None = None,
) -> dict[str, Any]:
    """Prompt x donor x map product-weight sensitivity for one layer estimand."""
    import numpy as np

    materialized = list(rows)
    prompt_ids = sorted({row.get("prompt_sha256") for row in materialized})
    categories = sorted({row.get("category") for row in materialized})
    map_ids = [f"map-{index}" for index in range(N_MAPS)]
    has_donor = all("donor_assignment_id" in row for row in materialized)
    donor_ids = [f"donor-{index}" for index in range(N_DONORS)] if has_donor else []
    if (
        not PILOT_MIN_LAYER_PROMPTS <= len(prompt_ids) <= N_PILOT_PROMPTS
        or len(categories) != N_CATEGORIES
        or any(
            not isinstance(value, str) or not value for value in prompt_ids + categories
        )
    ):
        _fail(
            "product_weight_structure",
            "product-weight input requires 18-20 eligible prompts in five categories",
        )
    prompt_category = {}
    value_index = {}
    for row in materialized:
        prompt = row.get("prompt_sha256")
        category = row.get("category")
        map_id = row.get("map_draw_id")
        donor_id = row.get("donor_assignment_id") if has_donor else None
        value = row.get("value")
        if (
            map_id not in map_ids
            or (has_donor and donor_id not in donor_ids)
            or not _finite_number(value)
        ):
            _fail("product_weight_structure", "product-weight row is malformed")
        if prompt in prompt_category and prompt_category[prompt] != category:
            _fail("product_weight_structure", "a prompt changes category")
        prompt_category[prompt] = category
        key = (prompt, donor_id, map_id)
        if key in value_index:
            _fail("product_weight_structure", "duplicate crossed effect row")
        value_index[key] = float(value)
    expected = len(prompt_ids) * N_MAPS * (N_DONORS if has_donor else 1)
    if len(materialized) != expected:
        _fail(
            "product_weight_structure",
            "product-weight rows do not form the complete declared crossing",
            observed=len(materialized),
            expected=expected,
        )
    category_prompts = {
        category: sorted(
            prompt for prompt in prompt_ids if prompt_category.get(prompt) == category
        )
        for category in categories
    }
    if any(
        not PILOT_MIN_CATEGORY_PROMPTS <= len(prompts) <= 4
        for prompts in category_prompts.values()
    ):
        _fail(
            "product_weight_structure",
            "product-weight input requires three or four prompts per category",
        )

    point = category_balanced_mean(
        [{"category": row["category"], "value": row["value"]} for row in materialized]
    )
    prompt_position = {prompt: index for index, prompt in enumerate(prompt_ids)}
    rng, identity = _pilot_rng(numpy_version=numpy_version)
    replicates = np.empty(BOOTSTRAP_ITERATIONS, dtype=np.float64)
    batch_size = 250
    for start in range(0, BOOTSTRAP_ITERATIONS, batch_size):
        stop = min(start + batch_size, BOOTSTRAP_ITERATIONS)
        size = stop - start
        prompt_weights = rng.exponential(scale=1.0, size=(size, len(prompt_ids)))
        map_weights = rng.exponential(scale=1.0, size=(size, N_MAPS))
        donor_weights = (
            rng.exponential(scale=1.0, size=(size, N_DONORS)) if has_donor else None
        )
        category_statistics = []
        for category in categories:
            prompts = category_prompts[category]
            pweights = prompt_weights[
                :, [prompt_position[prompt] for prompt in prompts]
            ]
            if has_donor:
                values = np.asarray(
                    [
                        [
                            [
                                value_index[(prompt, donor_id, map_id)]
                                for map_id in map_ids
                            ]
                            for donor_id in donor_ids
                        ]
                        for prompt in prompts
                    ],
                    dtype=np.float64,
                )
                numerator = np.einsum(
                    "bp,bd,bm,pdm->b",
                    pweights,
                    donor_weights,
                    map_weights,
                    values,
                    optimize=True,
                )
                denominator = (
                    pweights.sum(axis=1)
                    * donor_weights.sum(axis=1)
                    * map_weights.sum(axis=1)
                )
            else:
                values = np.asarray(
                    [
                        [value_index[(prompt, None, map_id)] for map_id in map_ids]
                        for prompt in prompts
                    ],
                    dtype=np.float64,
                )
                numerator = np.einsum(
                    "bp,bm,pm->b",
                    pweights,
                    map_weights,
                    values,
                    optimize=True,
                )
                denominator = pweights.sum(axis=1) * map_weights.sum(axis=1)
            category_statistics.append(numerator / denominator)
        replicates[start:stop] = np.mean(np.stack(category_statistics, axis=1), axis=1)
    return _interval_result(
        method="prompt_donor_map_product_weight_percentile",
        point_estimate=point,
        replicates=replicates,
        identity=identity,
        weight_distribution=PRODUCT_WEIGHT_DISTRIBUTION,
    )


def build_pilot_inference(
    records: Sequence[Mapping[str, Any]],
    denominator_derivation: Mapping[str, Any],
    *,
    derivation_code_sha256: str,
    numpy_version: str,
) -> dict[str, Any]:
    """Recompute the full pilot estimation packet from retained NTA records."""
    materialized = _validate_pilot_record_population(records)
    prompt_effects = []
    for record in sorted(
        materialized,
        key=lambda item: (
            SELECTED_LAYERS.index(int(item["layer"])),
            str(item["prompt_sha256"]),
        ),
    ):
        floor_status = record.get("floor_status")
        nta = record.get("factorized_nta")
        if not isinstance(floor_status, Mapping) or not isinstance(nta, Mapping):
            _fail("pilot_inference_input", "record lacks floor status or NTA trees")
        for floor in (PRIMARY_FLOOR_ID, "layer0_residual_decoded"):
            status = floor_status.get(floor)
            if not isinstance(status, Mapping) or not isinstance(
                status.get("eligible"), bool
            ):
                _fail("pilot_inference_input", "floor status is malformed")
            if status["eligible"]:
                effects = crossed_prompt_effects(nta.get(floor, {}))
                if effects.get("eligible") is not True:
                    _fail(
                        "pilot_inference_input",
                        "eligible floor cannot contain excluded NTA leaves",
                    )
            else:
                effects = {
                    "eligible": False,
                    "exclusion_reason": status.get("exclusion_reason"),
                }
            prompt_effects.append(
                {
                    "prompt_sha256": record["prompt_sha256"],
                    "category": record["category"],
                    "layer": record["layer"],
                    "floor": floor,
                    **effects,
                }
            )

    coverage_records = []
    layer_estimates = []
    methods = (
        "category_stratified_prompt_percentile",
        "prompt_donor_map_product_weight_percentile",
    )
    estimands = ("correct_effect", "wrong_effect", "interaction")
    for floor in (PRIMARY_FLOOR_ID, "layer0_residual_decoded"):
        for layer in SELECTED_LAYERS:
            layer_rows = [
                row
                for row in prompt_effects
                if row["floor"] == floor and row["layer"] == layer
            ]
            coverage_input = [
                {
                    "prompt_sha256": row["prompt_sha256"],
                    "category": row["category"],
                    "eligible": row["eligible"],
                }
                for row in layer_rows
            ]
            coverage = check_floor_layer_coverage(coverage_input)
            coverage_records.append({"floor": floor, "layer": layer, **coverage})
            for estimand in estimands:
                if not coverage["defined"]:
                    for method in methods:
                        layer_estimates.append(
                            {
                                "floor": floor,
                                "layer": layer,
                                "estimand": estimand,
                                "method": method,
                                "defined": False,
                                "reason": coverage["reason"],
                                "point_estimate": None,
                                "iterations": 0,
                                "finite_replicates": 0,
                                "ci_level": BOOTSTRAP_CI_LEVEL,
                                "quantile_method": QUANTILE_METHOD,
                                "lower": None,
                                "upper": None,
                            }
                        )
                    continue
                mean_key = f"{estimand}_mean"
                primary_rows = [
                    {
                        "prompt_sha256": row["prompt_sha256"],
                        "category": row["category"],
                        "eligible": row["eligible"],
                        "value": row.get(mean_key),
                    }
                    for row in layer_rows
                ]
                primary = category_stratified_prompt_interval(
                    primary_rows, numpy_version=numpy_version
                )
                layer_estimates.append(
                    {
                        "floor": floor,
                        "layer": layer,
                        "estimand": estimand,
                        "defined": True,
                        "reason": None,
                        **primary,
                    }
                )

                draw_key = {
                    "correct_effect": "correct_effects",
                    "wrong_effect": "wrong_effects",
                    "interaction": "interactions",
                }[estimand]
                product_rows = []
                for row in layer_rows:
                    if not row["eligible"]:
                        continue
                    for draw in row[draw_key]:
                        product_rows.append(
                            {
                                "prompt_sha256": row["prompt_sha256"],
                                "category": row["category"],
                                **draw,
                            }
                        )
                sensitivity = product_weight_interval(
                    product_rows, numpy_version=numpy_version
                )
                layer_estimates.append(
                    {
                        "floor": floor,
                        "layer": layer,
                        "estimand": estimand,
                        "defined": True,
                        "reason": None,
                        **sensitivity,
                    }
                )

    rng = bootstrap_rng_identity("pilot", numpy_version=numpy_version)
    records_sha256 = _canonical_sha256(materialized)
    measurement_core = {
        "records_sha256": records_sha256,
        "denominator_derivation": dict(denominator_derivation),
        "coverage": coverage_records,
        "prompt_layer_effects": prompt_effects,
        "layer_estimates": layer_estimates,
        "rng": rng,
    }
    pilot_measurement_sha256 = _canonical_sha256(measurement_core)
    thresholds = derive_pilot_thresholds(
        layer_estimates,
        pilot_measurement_sha256=pilot_measurement_sha256,
        derivation_code_sha256=derivation_code_sha256,
    )
    return {
        **measurement_core,
        "pilot_measurement_sha256": pilot_measurement_sha256,
        "threshold_derivation": thresholds,
    }


def derive_pilot_thresholds(
    layer_estimates: Sequence[Mapping[str, Any]],
    *,
    pilot_measurement_sha256: str,
    derivation_code_sha256: str,
) -> dict[str, Any]:
    """Derive both four-layer vectors or make both unavailable."""
    for name, value in (
        ("pilot_measurement_sha256", pilot_measurement_sha256),
        ("derivation_code_sha256", derivation_code_sha256),
    ):
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)
        ):
            _fail("threshold_identity", f"{name} must be 64 lowercase hex")
    expected_keys = {
        (layer, estimand)
        for layer in SELECTED_LAYERS
        for estimand in ("correct_effect", "interaction")
    }
    selected = {}
    for entry in layer_estimates:
        if (
            entry.get("floor") == PRIMARY_FLOOR_ID
            and entry.get("method") == "category_stratified_prompt_percentile"
            and (entry.get("layer"), entry.get("estimand")) in expected_keys
        ):
            key = (entry["layer"], entry["estimand"])
            if key in selected:
                _fail("threshold_source", "duplicate threshold source estimate")
            selected[key] = entry
    if set(selected) != expected_keys:
        return {
            "available": False,
            "reason": "threshold_source_incomplete",
            "source_floor": PRIMARY_FLOOR_ID,
            "layer_order": list(SELECTED_LAYERS),
        }
    invalid = [
        key
        for key, entry in selected.items()
        if entry.get("defined") is not True
        or not _finite_number(entry.get("point_estimate"))
        or float(entry["point_estimate"]) <= 0
    ]
    if invalid:
        return {
            "available": False,
            "reason": "threshold_source_nonpositive_or_undefined",
            "source_floor": PRIMARY_FLOOR_ID,
            "layer_order": list(SELECTED_LAYERS),
            "invalid_sources": [
                {"layer": layer, "estimand": estimand}
                for layer, estimand in sorted(invalid)
            ],
        }
    source_estimates = [
        {
            "layer": layer,
            "estimand": estimand,
            "point_estimate": float(selected[(layer, estimand)]["point_estimate"]),
        }
        for layer in SELECTED_LAYERS
        for estimand in ("correct_effect", "interaction")
    ]
    return {
        "available": True,
        "source_floor": PRIMARY_FLOOR_ID,
        "source_method": "category_stratified_prompt_percentile",
        "factor": 0.5,
        "layer_order": list(SELECTED_LAYERS),
        "source_estimates": source_estimates,
        "SPEC_MIN_EFFECT": [
            0.5 * float(selected[(layer, "correct_effect")]["point_estimate"])
            for layer in SELECTED_LAYERS
        ],
        "INTERACTION_MIN_EFFECT": [
            0.5 * float(selected[(layer, "interaction")]["point_estimate"])
            for layer in SELECTED_LAYERS
        ],
        "pilot_measurement_sha256": pilot_measurement_sha256,
        "derivation_code_sha256": derivation_code_sha256,
    }
