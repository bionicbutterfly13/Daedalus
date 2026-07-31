#!/usr/bin/env python3
"""Read-only Stage 2b primary-floor diagnostic.

This script reads the retained pilot artifact and the already-authorized pilot
view, verifies both byte identities, and prints a bounded JSON summary to
standard output. It never writes a file, accesses a confirmation input, changes
an eligibility rule, derives a scientific threshold, or selects prompts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

CANONICAL_ARTIFACT_SHA256 = (
    "d138846e7a189ad42955a5990e6d1a5c00553ba768cd838c5b6bf0334095daef"
)
CANONICAL_ARTIFACT_BASENAME = "jspace_discrimination_s2b_pilot_d138846e7a189ad4.json"
CANONICAL_PILOT_VIEW_SHA256 = (
    "5bef8316f72682a628fc1240bf6068a91aa7c8a330377206cbd9145434b797e4"
)
CANONICAL_PILOT_VIEW_BASENAME = "jspace-stage2b-pilot-v1.json"
MODEL_ID = "Qwen/Qwen3-1.7B"
MODEL_REVISION = "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
PRIMARY_FLOOR = "input_embedding_decoded"
SENSITIVITY_FLOOR = "layer0_residual_decoded"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_bound_json(
    path: Path,
    *,
    expected_basename: str,
    expected_sha256: str,
) -> dict[str, Any]:
    if path.name != expected_basename:
        raise ValueError(
            f"refusing unexpected input name {path.name!r}; expected {expected_basename!r}"
        )
    if path.is_symlink():
        raise ValueError(f"refusing symlink input: {path}")
    if not path.is_file():
        raise ValueError(f"required regular file is absent: {path}")
    raw = path.read_bytes()
    observed = sha256_bytes(raw)
    if observed != expected_sha256:
        raise ValueError(
            f"{path.name} SHA-256 mismatch: expected {expected_sha256}, got {observed}"
        )
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise TypeError(f"{path.name} must contain one JSON object")
    return value


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    return hashlib.sha256((payload + "\n").encode("ascii")).hexdigest()


def linear_quantile(values: list[float], q: float) -> tuple[float, dict[str, Any]]:
    """Reproduce the linear quantile definition without importing NumPy."""
    if not values:
        raise ValueError("quantile source cannot be empty")
    ordered = sorted(float(value) for value in values)
    if not all(math.isfinite(value) for value in ordered):
        raise ValueError("quantile source values must be finite")
    position = (len(ordered) - 1) * q
    lower_index = math.floor(position)
    upper_index = math.ceil(position)
    fraction = position - lower_index
    lower = ordered[lower_index]
    upper = ordered[upper_index]
    derived = lower + fraction * (upper - lower)
    return derived, {
        "position": position,
        "lower_index": lower_index,
        "upper_index": upper_index,
        "lower_value": lower,
        "upper_value": upper,
        "interpolation_fraction": fraction,
    }


def rank_from_score(score: float, vocab_size: int) -> int:
    """Invert s(r) = -log(r) / log(V), tolerating stored float roundoff."""
    return round(math.exp(-float(score) * math.log(vocab_size)))


def _finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _expected_floor_status(denominator: float, guard: float) -> dict[str, Any]:
    eligible = denominator > guard
    return {
        "denominator": denominator,
        "eligible": eligible,
        "exclusion_reason": None if eligible else "denominator_not_greater_than_guard",
    }


def _load_cached_tokenizer() -> Any | None:
    try:
        from transformers import AutoTokenizer
    except ImportError:
        return None
    try:
        return AutoTokenizer.from_pretrained(
            MODEL_ID,
            revision=MODEL_REVISION,
            local_files_only=True,
        )
    except (OSError, ValueError):
        return None


def _token_summary(tokenizer: Any | None, text: str, target_id: int) -> dict[str, Any]:
    if tokenizer is None:
        return {"status": "unavailable_from_local_cache"}
    input_ids = tokenizer(text)["input_ids"]
    tokens = tokenizer.convert_ids_to_tokens(input_ids)
    return {
        "status": "available",
        "prompt_token_count": len(input_ids),
        "prompt_token_ids": [int(value) for value in input_ids],
        "prompt_tokens": [str(value) for value in tokens],
        "last_prompt_token_id": int(input_ids[-1]),
        "last_prompt_token": str(tokens[-1]),
        "target_token": tokenizer.decode([target_id]),
        "target_token_piece": str(tokenizer.convert_ids_to_tokens(target_id)),
    }


def build_diagnostic(
    artifact: dict[str, Any],
    pilot_view: dict[str, Any],
    *,
    tokenizer: Any | None,
) -> dict[str, Any]:
    records = artifact.get("descriptive", {}).get("records")
    if not isinstance(records, list) or len(records) != 80:
        raise ValueError(
            "diagnostic requires exactly 80 descriptive prompt-layer records"
        )
    prompts = pilot_view.get("prompts")
    if not isinstance(prompts, list) or len(prompts) != 20:
        raise ValueError("diagnostic requires the exact 20-prompt pilot view")
    prompt_registry = {entry["sha256"]: entry for entry in prompts}
    if len(prompt_registry) != 20:
        raise ValueError("pilot view contains duplicate prompt identities")
    if set(prompt_registry) != {record.get("prompt_sha256") for record in records}:
        raise ValueError("artifact prompt identities do not equal the pilot view")

    guard = float(artifact["constants"]["min_denominator"])
    vocab_size = int(artifact["design"]["vocab_size"])
    if not math.isfinite(guard) or guard <= 0:
        raise ValueError("denominator guard must be finite and positive")
    if vocab_size < 2:
        raise ValueError("design.vocab_size must be at least two")
    per_prompt: list[dict[str, Any]] = []
    all_primary_denominators: list[float] = []

    for prompt_sha256, meta in sorted(
        prompt_registry.items(), key=lambda item: int(item[1]["index"])
    ):
        prompt_records = [
            record for record in records if record["prompt_sha256"] == prompt_sha256
        ]
        if len(prompt_records) != 4:
            raise ValueError(f"{meta['id']} does not have exactly four layer records")
        if {record.get("layer") for record in prompt_records} != {6, 13, 20, 26}:
            raise ValueError(f"{meta['id']} does not cover the four selected layers")
        if any(record.get("category") != meta["category"] for record in prompt_records):
            raise ValueError(f"{meta['id']} category disagrees with the pilot view")
        first = prompt_records[0]
        invariant_fields = (
            "target_id",
            "target_derivation",
            "floor_scores",
            "floor_status",
        )
        if any(
            record.get(field) != first.get(field)
            for record in prompt_records[1:]
            for field in invariant_fields
        ):
            raise ValueError(f"{meta['id']} floor/target fields vary across layers")

        floors = first["floor_scores"]
        if not isinstance(floors, dict) or set(floors) != {
            PRIMARY_FLOOR,
            SENSITIVITY_FLOOR,
            "output_decoded",
        }:
            raise ValueError(f"{meta['id']} has malformed floor_scores")
        if not all(
            _finite_number(value) and -1.0 <= float(value) <= 0.0
            for value in floors.values()
        ):
            raise ValueError(f"{meta['id']} floor scores must be finite in [-1, 0]")
        primary_denominator = float(floors["output_decoded"]) - float(
            floors[PRIMARY_FLOOR]
        )
        sensitivity_denominator = float(floors["output_decoded"]) - float(
            floors[SENSITIVITY_FLOOR]
        )
        all_primary_denominators.extend([primary_denominator] * 4)
        target_id = int(first["target_id"])
        target = first["target_derivation"]
        if not 0 <= target_id < vocab_size:
            raise ValueError(f"{meta['id']} target_id is outside the vocabulary")
        tie_ids = target.get("argmax_tie_token_ids")
        if (
            not isinstance(tie_ids, list)
            or not tie_ids
            or any(not isinstance(value, int) for value in tie_ids)
            or target_id != min(tie_ids)
        ):
            raise ValueError(f"{meta['id']} has inconsistent target tie evidence")
        if not _finite_number(target.get("max_logit")):
            raise ValueError(f"{meta['id']} max_logit is not finite")
        statuses = first.get("floor_status")
        expected_statuses = {
            PRIMARY_FLOOR: _expected_floor_status(primary_denominator, guard),
            SENSITIVITY_FLOOR: _expected_floor_status(sensitivity_denominator, guard),
        }
        if statuses != expected_statuses:
            raise ValueError(f"{meta['id']} retained floor_status does not recompute")
        per_prompt.append(
            {
                "prompt_id": meta["id"],
                "prompt_sha256": prompt_sha256,
                "category": meta["category"],
                "prompt_text": meta["text"],
                "utf8_byte_count": int(meta["utf8_byte_count"]),
                "target_id": target_id,
                "argmax_tie_count": len(tie_ids),
                "argmax_tie_token_ids": tie_ids,
                "max_logit": float(target["max_logit"]),
                "primary_floor_rank": rank_from_score(
                    float(floors[PRIMARY_FLOOR]), vocab_size
                ),
                "sensitivity_floor_rank": rank_from_score(
                    float(floors[SENSITIVITY_FLOOR]), vocab_size
                ),
                "output_rank": rank_from_score(
                    float(floors["output_decoded"]), vocab_size
                ),
                "primary_denominator": primary_denominator,
                "primary_guard_margin": primary_denominator - guard,
                "primary_eligible": primary_denominator > guard,
                "sensitivity_denominator": sensitivity_denominator,
                "sensitivity_guard_margin": sensitivity_denominator - guard,
                "sensitivity_eligible": sensitivity_denominator > guard,
                "tokenization": _token_summary(tokenizer, meta["text"], target_id),
            }
        )

    source_records = sorted(
        records,
        key=lambda record: (
            str(record["prompt_sha256"]),
            (6, 13, 20, 26).index(int(record["layer"])),
        ),
    )
    source_denominators = [
        float(record["floor_scores"]["output_decoded"])
        - float(record["floor_scores"][PRIMARY_FLOOR])
        for record in source_records
    ]
    if sorted(source_denominators) != sorted(all_primary_denominators):
        raise ValueError("primary denominator population is inconsistent")
    recomputed_guard, bracket = linear_quantile(source_denominators, 0.05)
    if recomputed_guard != guard:
        raise ValueError(
            f"denominator guard does not reproduce exactly: {recomputed_guard} != {guard}"
        )
    derivation = artifact.get("denominator_derivation", {})
    expected_derivation = {
        "source_floor": PRIMARY_FLOOR,
        "source_count": 80,
        "source_denominators_sha256": canonical_sha256(source_denominators),
        "quantile": 0.05,
        "quantile_method": "linear",
        "derived_value": guard,
        "source_order": [
            {
                "prompt_sha256": str(record["prompt_sha256"]),
                "layer": int(record["layer"]),
            }
            for record in source_records
        ],
    }
    if derivation != expected_derivation:
        raise ValueError("denominator_derivation does not recompute exactly")

    category_summary: dict[str, dict[str, Any]] = {}
    for category in sorted({entry["category"] for entry in per_prompt}):
        entries = [entry for entry in per_prompt if entry["category"] == category]
        category_summary[category] = {
            "prompt_count": len(entries),
            "primary_eligible": sum(entry["primary_eligible"] for entry in entries),
            "sensitivity_eligible": sum(
                entry["sensitivity_eligible"] for entry in entries
            ),
            "excluded_prompt_ids": [
                entry["prompt_id"] for entry in entries if not entry["primary_eligible"]
            ],
        }

    denominator_counts = Counter(entry["primary_denominator"] for entry in per_prompt)
    excluded = [entry for entry in per_prompt if not entry["primary_eligible"]]
    return {
        "schema": "jspace-stage2b-primary-floor-diagnostic/v1",
        "boundaries": {
            "artifact_modified": False,
            "artifact_transferred": False,
            "confirmation_accessed": False,
            "thresholds_derived": False,
            "replacement_prompts_selected": False,
        },
        "guard": {
            "recorded": guard,
            "recomputed": recomputed_guard,
            "source_count": len(source_denominators),
            "quantile": 0.05,
            "quantile_method": "linear",
            "bracket": bracket,
            "prompt_level_denominator_multiplicities": [
                {"denominator": value, "prompt_count": count}
                for value, count in sorted(denominator_counts.items())
            ],
        },
        "coverage_by_category": category_summary,
        "excluded_primary_prompts": excluded,
        "arithmetic_prompts": [
            entry
            for entry in per_prompt
            if entry["category"] == "arithmetic_completion"
        ],
        "all_prompt_geometry": [
            {
                key: entry[key]
                for key in (
                    "prompt_id",
                    "category",
                    "target_id",
                    "primary_floor_rank",
                    "primary_denominator",
                    "primary_guard_margin",
                    "primary_eligible",
                    "sensitivity_floor_rank",
                    "sensitivity_denominator",
                    "sensitivity_eligible",
                )
            }
            for entry in per_prompt
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path)
    parser.add_argument("pilot_view", type=Path)
    parser.add_argument(
        "--without-tokenizer",
        action="store_true",
        help="Do not inspect the already-cached pinned tokenizer.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    artifact = read_bound_json(
        args.artifact,
        expected_basename=CANONICAL_ARTIFACT_BASENAME,
        expected_sha256=CANONICAL_ARTIFACT_SHA256,
    )
    pilot_view = read_bound_json(
        args.pilot_view,
        expected_basename=CANONICAL_PILOT_VIEW_BASENAME,
        expected_sha256=CANONICAL_PILOT_VIEW_SHA256,
    )
    tokenizer = None if args.without_tokenizer else _load_cached_tokenizer()
    diagnostic = build_diagnostic(artifact, pilot_view, tokenizer=tokenizer)
    print(json.dumps(diagnostic, sort_keys=True, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
