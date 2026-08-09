"""Pure Stage 2b gate and decision recomputation primitives.

This module uses only the standard library so artifact producers, validators, and
CPU-only smoke tests can share exactly one implementation.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

COMPARISONS = frozenset(
    {
        "statistic_gt_threshold",
        "statistic_lt_threshold",
        "interval_low_gt_threshold",
        "interval_high_lt_threshold",
        "interval_excludes_zero",
    }
)


def _finite_number(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        candidate = float(value)
        if math.isfinite(candidate):
            return candidate
    return None


def derive_gate_outcome(
    *,
    statistic: Any,
    interval: Mapping[str, Any],
    declared_value: Any,
    comparison: str,
) -> str:
    """Derive ``pass``/``fail``/``undefined`` from a complete gate record."""
    if comparison not in COMPARISONS:
        raise ValueError(f"unknown gate comparison {comparison!r}")

    low = _finite_number(interval.get("low"))
    high = _finite_number(interval.get("high"))
    measured = _finite_number(statistic)
    if low is None or high is None or measured is None:
        return "undefined"
    if low > high:
        raise ValueError(f"interval low {low!r} exceeds high {high!r}")

    if comparison == "interval_excludes_zero":
        passes = low > 0 or high < 0
    else:
        threshold = _finite_number(declared_value)
        if threshold is None:
            raise ValueError(
                f"comparison {comparison!r} requires a finite declared threshold"
            )
        if comparison == "statistic_gt_threshold":
            passes = measured > threshold
        elif comparison == "statistic_lt_threshold":
            passes = measured < threshold
        elif comparison == "interval_low_gt_threshold":
            passes = low > threshold
        else:
            passes = high < threshold
    return "pass" if passes else "fail"


def compose_confirmatory_decision(
    gates: Mapping[str, str],
    *,
    pinned_identities_matched: bool,
    capacity_ok: bool,
) -> dict[str, str]:
    """Compose the confirmatory result from canonical gates and kill inputs."""
    notes: list[str] = []
    if not pinned_identities_matched:
        return {"result": "kill", "notes": "pinned identity mismatch"}
    if not capacity_ok:
        return {"result": "kill", "notes": "capacity gate failed"}
    if gates.get("reproduction") != "pass":
        return {
            "result": "kill",
            "notes": f"reproduction {gates.get('reproduction', 'missing')}",
        }

    def holds(*gate_ids: str) -> bool:
        held = True
        for gate_id in gate_ids:
            outcome = gates.get(gate_id)
            if outcome == "undefined":
                notes.append(f"{gate_id} undefined")
            if outcome != "pass":
                held = False
        return held

    h1 = holds("h1_specificity", "h1_interval", "h1_interaction")
    h2 = holds("h2_overlap", "h2_target")
    if not holds("sanity_floor"):
        return {
            "result": "fail",
            "notes": "; ".join([*notes, "sanity floor not cleared"]),
        }
    if h1 and h2:
        result = "pass"
    elif h1 or h2:
        result = "ambiguity"
        notes.append("H1 holds, H2 does not" if h1 else "H2 holds, H1 does not")
    else:
        result = "fail"
    return {"result": result, "notes": "; ".join(notes)}
