#!/usr/bin/env python3
"""Decide which evolution mechanisms a run owed, and which actually ran (T008).

One paper finding and one local policy meet here:

* F2 - the paper makes the Evolution Manager a first-class agent (§3.5). Daedalus
       has no such agent; IDE/IVE/ESE are optional skill prose that nothing
       obliges the model to execute. So a run can complete having evolved nothing.
* Local policy - require ESE after any recorded experiment pipeline so failed
  trajectories remain available to later local runs. This is useful Archimedes
  policy, but it is not established as a paper requirement. The former F8 claim
  was withdrawn on 2026-08-09 after reading the available paper prompt.

This module derives the obligations from run artifacts using the paper's rules
plus the declared local ESE policy, compares them against what the run actually
recorded, and reports the gap. It never edits the installed skills; the Hermes
supervisor acts on the report.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from memory_persistence import resolve_memory_dir

#: The paper's three evolution mechanisms (§3.5).
MECHANISMS = ("IDE", "IVE", "ESE")

_REPORT_NAME = re.compile(r"cycle_(\d+)_(ide|ive|ese)\.md$", re.IGNORECASE)


@dataclass(frozen=True)
class Obligation:
    """One mechanism the paper's rules say this run owed."""

    mechanism: str
    reason: str

    def to_dict(self) -> dict:
        """Return a JSON-serializable form."""
        return {"mechanism": self.mechanism, "reason": self.reason}


def observed_mechanisms(workspace: Path) -> dict[str, list[str]]:
    """Return ``{mechanism: [report filenames]}`` recorded under this workspace.

    Args:
        workspace: The run's workspace root.

    Returns:
        Mapping from mechanism name to the evolution reports evidencing it.
    """
    reports_dir = resolve_memory_dir(workspace) / "evolution-reports"
    found: dict[str, list[str]] = {name: [] for name in MECHANISMS}
    if not reports_dir.is_dir():
        return found
    for path in sorted(reports_dir.iterdir()):
        match = _REPORT_NAME.search(path.name)
        if match:
            found[match.group(2).upper()].append(path.name)
    return found


def _load_stage_records(workspace: Path) -> list[dict]:
    """Return parsed ``stage-record.json`` files, ordered by stage number."""
    records: list[dict] = []
    for stage_dir in sorted((workspace / "experiments").glob("stage*")):
        record_path = stage_dir / "stage-record.json"
        if not record_path.is_file():
            continue
        try:
            records.append(json.loads(record_path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return sorted(records, key=lambda r: r.get("stage", 0))


def derive_obligations(workspace: Path) -> list[Obligation]:
    """Return mechanisms owed by paper rules plus declared local policy.

    Args:
        workspace: The run's workspace root.

    Returns:
        Obligations, in mechanism order.
    """
    obligations: list[Obligation] = []

    if (workspace / "direction-summary.md").is_file():
        obligations.append(
            Obligation(
                "IDE",
                "a tournament completed and produced direction-summary.md, so the "
                "top-ranked directions owe an M_I update (paper §3.5)",
            )
        )

    records = _load_stage_records(workspace)
    if not records:
        return obligations

    # IVE fires on either of the paper's two conditions.
    exhausted = [
        record
        for record in records
        if record.get("attempts_used", 0) >= record.get("budget", 0)
        and not record.get("gate_met", False)
    ]
    if exhausted:
        obligations.append(
            Obligation(
                "IVE",
                "a stage exhausted its attempt budget without meeting its gate "
                f"(stages {[r.get('stage') for r in exhausted]}): the "
                "no-executable-within-budget condition (paper §3.5)",
            )
        )
    else:
        stage_three = next((r for r in records if r.get("stage") == 3), None)
        if stage_three is not None and not stage_three.get("gate_met", False):
            obligations.append(
                Obligation(
                    "IVE",
                    "stage 3 did not beat the tuned baseline: the "
                    "worse-than-baseline condition (paper §3.5)",
                )
            )

    # Local Archimedes policy requires ESE on any recorded pipeline, including
    # failed or partial ones. F8 is withdrawn: do not describe this as a paper
    # correction or an upstream defect.
    obligations.append(
        Obligation(
            "ESE",
            f"the pipeline produced {len(records)} stage trajector"
            f"{'y' if len(records) == 1 else 'ies'}; local Archimedes policy "
            "retains lessons from unsuccessful and partial pipelines, so ESE is "
            "required whether or not all gates were met",
        )
    )
    return obligations


def build_report(workspace: Path) -> dict:
    """Compare owed mechanisms against recorded ones.

    Args:
        workspace: The run's workspace root.

    Returns:
        A record naming each mechanism that was owed but not performed.
    """
    obligations = derive_obligations(workspace)
    observed = observed_mechanisms(workspace)

    missing = [
        obligation.to_dict()
        for obligation in obligations
        if not observed.get(obligation.mechanism)
    ]
    return {
        "schema": "daedalus-parity-evolution-enforcement/v1",
        "task": "T008",
        "findings": ["F2"],
        "local_policies": ["require_ese_after_any_recorded_pipeline"],
        "workspace": str(workspace),
        "obligations": [obligation.to_dict() for obligation in obligations],
        "observed": observed,
        "missing": missing,
        "complete": not missing,
        "note": (
            "ESE on partial or failed trajectories is a deliberate local policy. "
            "F8 is withdrawn, and this report must not be used to claim an "
            "upstream paper-alignment defect."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Exits nonzero when an owed mechanism did not run."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args(argv)

    record = build_report(args.workspace)
    serialized = json.dumps(record, indent=2, sort_keys=True)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(serialized + "\n", encoding="utf-8")
    print(serialized)

    if not record["complete"]:
        for item in record["missing"]:
            print(
                f"OWED {item['mechanism']}: {item['reason']}",
                file=sys.stderr,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
