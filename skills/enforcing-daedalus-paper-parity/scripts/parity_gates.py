#!/usr/bin/env python3
"""Acceptance gates that make Daedalus's silent failures loud (T002, T003, T005).

``docs/cognitive-lab-architecture.md`` gives Archimedes the acceptance authority:
a run is accepted only when its task-specific conditions pass, and EvoScientist
is never the sole judge of whether EvoScientist succeeded. Findings F3, F12, and
F14 are all cases where the run reports success while producing nothing
checkable:

* F3  - evolution memory is project-local; changing workspace selects another
        store, and an empty store reads as "first cycle";
* F12 - the pipeline is "recommended", so a run can emit ``done`` having skipped
        Idea Tree Search, the tournament, and every memory update;
* F14 - stage evidence is prose plus a checkbox, so ``C_best``, budget consumption,
        and gate satisfaction cannot be verified from artifacts.

Each gate here returns a structured verdict rather than raising, so a supervisor
can record every failure in one pass instead of stopping at the first. Absence of
evidence is always a failure: a gate never passes because it found nothing to
check.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from memory_persistence import (
    TRACKED_MEMORY_FILES,
    resolve_memory_dir,
    snapshot_memory,
)
from skill_digest import digest_skill_tree

# The paper's ideation stage ranks up to N_I=21 candidates and retains the top 3
# (arXiv 2603.08127 §3.3). A tournament whose field is 3 selects nothing, which
# is finding F5; the gate therefore requires strictly more entrants than winners.
PAPER_TOP_K = 3
MIN_TOURNAMENT_ENTRANTS = PAPER_TOP_K + 1

# Four experiment stages with fixed attempt budgets (§3.4).
PAPER_STAGE_BUDGETS = {1: 20, 2: 12, 3: 12, 4: 18}

_MARKDOWN_TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
_SEPARATOR_ROW = re.compile(r"^\s*\|[\s:|-]+\|\s*$")


@dataclass
class GateResult:
    """One gate's verdict, with the evidence that produced it."""

    gate: str
    finding: str
    passed: bool
    reasons: list[str] = field(default_factory=list)
    evidence: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Return a JSON-serializable verdict."""
        return {
            "gate": self.gate,
            "finding": self.finding,
            "passed": self.passed,
            "reasons": list(self.reasons),
            "evidence": self.evidence,
        }


def _count_table_rows(text: str) -> int:
    """Return the number of data rows across markdown tables in *text*.

    Header and separator rows are excluded, so the count is entrants, not lines.
    """
    rows = 0
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not _MARKDOWN_TABLE_ROW.match(line) or _SEPARATOR_ROW.match(line):
            continue
        # A data row is one whose preceding line is a separator, or whose
        # preceding line is itself a data row in the same block.
        previous = lines[index - 1] if index else ""
        if _SEPARATOR_ROW.match(previous) or (
            _MARKDOWN_TABLE_ROW.match(previous) and not _is_header(lines, index - 1)
        ):
            rows += 1
    return rows


def _is_header(lines: list[str], index: int) -> bool:
    """True when the row at *index* is a table header (followed by a separator)."""
    return index + 1 < len(lines) and bool(_SEPARATOR_ROW.match(lines[index + 1]))


def gate_memory_persistence(
    workspace: Path, baseline: dict[str, str] | None = None
) -> GateResult:
    """Fail when evolution memory is absent or unchanged by the run (F3, T002).

    Args:
        workspace: The run's workspace root.
        baseline: Pre-run ``{filename: sha256}``. When given, at least one
            tracked file must differ afterwards, which is what proves the run
            actually evolved rather than merely reading.

    Returns:
        A :class:`GateResult`; failing reasons name the specific file.
    """
    snapshot = snapshot_memory(workspace)
    reasons: list[str] = []

    if not snapshot.files:
        reasons.append(
            f"no evolution memory at {snapshot.memory_dir}: expected at least one of "
            f"{list(TRACKED_MEMORY_FILES)}. An empty store reads as 'first cycle' to "
            "the skills, so this cannot be distinguished from a wiped memory (F3)."
        )
    elif baseline is not None:
        unchanged = [
            name
            for name, digest in snapshot.files.items()
            if baseline.get(name) == digest
        ]
        if len(unchanged) == len(snapshot.files):
            reasons.append(
                "evolution memory is byte-identical to the pre-run baseline: the run "
                f"recorded no IDE/IVE/ESE update ({sorted(snapshot.files)})"
            )

    return GateResult(
        gate="memory_persistence",
        finding="F3",
        passed=not reasons,
        reasons=reasons,
        evidence={
            "memory_dir": str(snapshot.memory_dir),
            "files": snapshot.files,
            "baseline": baseline or {},
        },
    )


def gate_pipeline_artifacts(workspace: Path) -> GateResult:
    """Fail when the claimed pipeline left no evidence it ran (F12, F5, T003).

    Checks that the run produced a direction summary, a tournament with more
    entrants than winners, at least one stage log, and an evolution report.
    Nothing here trusts the ``done`` event.

    Args:
        workspace: The run's workspace root.

    Returns:
        A :class:`GateResult` naming each missing artifact.
    """
    reasons: list[str] = []
    evidence: dict = {}

    direction_summary = _first_existing(
        workspace, ["direction-summary.md", "artifacts/direction-summary.md"]
    )
    evidence["direction_summary"] = (
        str(direction_summary) if direction_summary else None
    )
    if direction_summary is None:
        reasons.append(
            "no direction-summary.md: research-ideation Step 6 (IDE) never produced "
            "its artifact, so the ideation stage cannot be shown to have run"
        )
        entrants = 0
    else:
        entrants = _count_table_rows(direction_summary.read_text(encoding="utf-8"))
        evidence["tournament_entrants"] = entrants
        if entrants < MIN_TOURNAMENT_ENTRANTS:
            reasons.append(
                f"tournament field is {entrants} candidate(s); the paper ranks up to 21 "
                f"and retains {PAPER_TOP_K}. A field of {PAPER_TOP_K} or fewer means the "
                "Elo ranking selected nothing (F5)."
            )

    stage_dirs = sorted(
        p for p in (workspace / "experiments").glob("stage*") if p.is_dir()
    )
    evidence["stage_dirs"] = [p.name for p in stage_dirs]
    if not stage_dirs:
        reasons.append(
            "no experiments/stage* directories: the 4-stage experiment pipeline left "
            "no evidence it ran (F12)"
        )

    reports_dir = resolve_memory_dir(workspace) / "evolution-reports"
    report_files = sorted(reports_dir.glob("*.md")) if reports_dir.is_dir() else []
    evidence["evolution_reports"] = [p.name for p in report_files]
    if not report_files:
        reasons.append(
            f"no evolution reports under {reports_dir}: no IDE/IVE/ESE mechanism "
            "recorded a memory update (F12)"
        )

    return GateResult(
        gate="pipeline_artifacts",
        finding="F12",
        passed=not reasons,
        reasons=reasons,
        evidence=evidence,
    )


def gate_stage_evidence_machine_checkable(workspace: Path) -> GateResult:
    """Fail when stage logs cannot be verified mechanically (F14, T005).

    The shipped stage template records prose and a checkbox, so an orchestrator
    cannot confirm ``C_best``, budget consumption, or gate satisfaction. This
    gate requires a structured ``stage-record.json`` per stage carrying those
    fields, and checks the attempt count against the paper's budget.

    Args:
        workspace: The run's workspace root.

    Returns:
        A :class:`GateResult` naming each unverifiable stage.
    """
    reasons: list[str] = []
    stages: dict[str, dict] = {}

    stage_dirs = sorted(
        p for p in (workspace / "experiments").glob("stage*") if p.is_dir()
    )
    if not stage_dirs:
        return GateResult(
            gate="stage_evidence_machine_checkable",
            finding="F14",
            passed=False,
            reasons=[
                "no experiments/stage* directories to verify; absence of evidence is "
                "not evidence of a clean run"
            ],
            evidence={},
        )

    for stage_dir in stage_dirs:
        record_path = stage_dir / "stage-record.json"
        if not record_path.is_file():
            reasons.append(
                f"{stage_dir.name}: no stage-record.json; prose logs cannot establish "
                "C_best, attempts used, or gate status (F14)"
            )
            continue
        try:
            record = json.loads(record_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            reasons.append(
                f"{stage_dir.name}: stage-record.json is not valid JSON ({exc})"
            )
            continue

        stages[stage_dir.name] = record
        missing = sorted(
            {"stage", "attempts_used", "budget", "best_attempt_id", "gate_met"}
            - set(record)
        )
        if missing:
            reasons.append(f"{stage_dir.name}: stage-record.json missing {missing}")
            continue

        stage_number = record["stage"]
        expected_budget = PAPER_STAGE_BUDGETS.get(stage_number)
        if expected_budget is not None and record["budget"] != expected_budget:
            reasons.append(
                f"{stage_dir.name}: budget {record['budget']} != paper budget "
                f"{expected_budget} for stage {stage_number}"
            )
        if record["attempts_used"] > record["budget"]:
            reasons.append(
                f"{stage_dir.name}: attempts_used {record['attempts_used']} exceeds "
                f"declared budget {record['budget']}"
            )
        if record["gate_met"] and not record.get("best_attempt_id"):
            reasons.append(
                f"{stage_dir.name}: gate_met is true but best_attempt_id is empty; "
                "C_best is unattributable"
            )

    return GateResult(
        gate="stage_evidence_machine_checkable",
        finding="F14",
        passed=not reasons,
        reasons=reasons,
        evidence={"stages": stages},
    )


def gate_skill_pins(launch_record: dict, skills_root: Path) -> GateResult:
    """Fail when the run's skills are unpinned or drifted (F1, T007).

    Args:
        launch_record: The record written before launch; must carry
            ``skill_digests``.
        skills_root: The installed-skills root to compare against.

    Returns:
        A :class:`GateResult` naming added, removed, and changed skills.
    """
    pinned = launch_record.get("skill_digests")
    if not pinned:
        return GateResult(
            gate="skill_pins",
            finding="F1",
            passed=False,
            reasons=[
                "launch record carries no skill_digests: the scientific method that "
                "produced this run is unattributable, and skill_manager can replace "
                "it between runs"
            ],
            evidence={},
        )

    observed = digest_skill_tree(skills_root)
    changed = sorted(k for k in set(pinned) & set(observed) if pinned[k] != observed[k])
    removed = sorted(set(pinned) - set(observed))
    added = sorted(set(observed) - set(pinned))

    reasons: list[str] = []
    if changed:
        reasons.append(f"skills changed between launch and acceptance: {changed}")
    if removed:
        reasons.append(f"skills present at launch are now missing: {removed}")

    return GateResult(
        gate="skill_pins",
        finding="F1",
        passed=not reasons,
        reasons=reasons,
        evidence={"changed": changed, "removed": removed, "added": added},
    )


def _first_existing(root: Path, candidates: list[str]) -> Path | None:
    """Return the first candidate path that exists under *root*."""
    for candidate in candidates:
        path = root / candidate
        if path.is_file():
            return path
    return None


def run_all_gates(
    workspace: Path,
    *,
    launch_record: dict | None = None,
    skills_root: Path | None = None,
    memory_baseline: dict[str, str] | None = None,
) -> dict:
    """Run every gate and return a combined acceptance verdict.

    Args:
        workspace: The run's workspace root.
        launch_record: Record written before launch (for skill pins, T007).
        skills_root: Installed-skills root to compare pins against.
        memory_baseline: Pre-run memory digests (T002).

    Returns:
        Acceptance record with per-gate verdicts and an overall ``accepted``
        flag that is true only when every gate passed.
    """
    results = [
        gate_memory_persistence(workspace, memory_baseline),
        gate_pipeline_artifacts(workspace),
        gate_stage_evidence_machine_checkable(workspace),
    ]
    if launch_record is not None and skills_root is not None:
        results.append(gate_skill_pins(launch_record, skills_root))

    failed = [result.gate for result in results if not result.passed]
    return {
        "schema": "daedalus-parity-acceptance/v1",
        "workspace": str(workspace),
        "accepted": not failed,
        "failed_gates": failed,
        "gates": [result.to_dict() for result in results],
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Exits nonzero when any gate fails."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--launch-record", type=Path, default=None)
    parser.add_argument(
        "--skills-root", type=Path, default=Path.home() / ".EvoScientist" / "skills"
    )
    parser.add_argument("--memory-baseline", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args(argv)

    launch_record = (
        json.loads(args.launch_record.read_text(encoding="utf-8"))
        if args.launch_record
        else None
    )
    baseline = (
        json.loads(args.memory_baseline.read_text(encoding="utf-8"))
        if args.memory_baseline
        else None
    )

    record = run_all_gates(
        args.workspace,
        launch_record=launch_record,
        skills_root=args.skills_root if launch_record else None,
        memory_baseline=baseline,
    )
    serialized = json.dumps(record, indent=2, sort_keys=True)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(serialized + "\n", encoding="utf-8")
    print(serialized)

    if not record["accepted"]:
        for gate in record["gates"]:
            for reason in gate["reasons"]:
                print(
                    f"REJECT [{gate['gate']}/{gate['finding']}] {reason}",
                    file=sys.stderr,
                )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
