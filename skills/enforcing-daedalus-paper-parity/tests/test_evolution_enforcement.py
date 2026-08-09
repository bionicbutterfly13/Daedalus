"""Tests for evolution-mechanism enforcement (T008, findings F2 and F8).

The sharpest case here is ``test_ese_is_owed_when_the_pipeline_failed``: the
installed skill would skip ESE entirely on a failed run, and the paper would
not. If that test ever starts passing for the wrong reason, the F8 correction
has been quietly reverted.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from evolution_enforcement import (  # noqa: E402
    build_report,
    derive_obligations,
    observed_mechanisms,
)


def _stage(workspace: Path, stage: int, **fields) -> None:
    """Write a stage-record.json for *stage* under *workspace*."""
    record = {
        "stage": stage,
        "budget": {1: 20, 2: 12, 3: 12, 4: 18}[stage],
        "attempts_used": 3,
        "best_attempt_id": f"stage{stage}-attempt-003",
        "gate_met": True,
    }
    record.update(fields)
    stage_dir = workspace / "experiments" / f"stage{stage}_x"
    stage_dir.mkdir(parents=True, exist_ok=True)
    (stage_dir / "stage-record.json").write_text(json.dumps(record), encoding="utf-8")


def _report(workspace: Path, name: str) -> None:
    """Write an evolution report under the workspace's memory dir."""
    reports = workspace / "memory" / "evolution-reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / name).write_text("report\n", encoding="utf-8")


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """A workspace with a completed tournament and four passing stages."""
    ws = tmp_path / "lab-workspace"
    ws.mkdir()
    (ws / "direction-summary.md").write_text("| R |\n|---|\n| 1 |\n", encoding="utf-8")
    for stage in (1, 2, 3, 4):
        _stage(ws, stage)
    return ws


def _mechanisms(workspace: Path) -> set[str]:
    """Return the set of mechanisms derive_obligations says are owed."""
    return {obligation.mechanism for obligation in derive_obligations(workspace)}


class TestDeriveObligations:
    """Obligations come from the paper's rules, not the skill's."""

    def test_tournament_owes_ide(self, workspace: Path):
        assert "IDE" in _mechanisms(workspace)

    def test_no_tournament_owes_no_ide(self, tmp_path: Path):
        ws = tmp_path / "ws"
        ws.mkdir()
        _stage(ws, 1)
        assert "IDE" not in _mechanisms(ws)

    def test_successful_pipeline_owes_ese(self, workspace: Path):
        assert "ESE" in _mechanisms(workspace)

    def test_ese_is_owed_when_the_pipeline_failed(self, tmp_path: Path):
        """The F8 correction: no success precondition.

        The installed evo-memory skill fires ESE only when all four stages pass.
        The paper distils from full search trajectories regardless, which is why
        a ~21% stage-3 success rate can still yield the reported improvement.
        """
        ws = tmp_path / "ws"
        ws.mkdir()
        _stage(ws, 1, attempts_used=20, gate_met=False)

        assert "ESE" in _mechanisms(ws)

    def test_no_stages_owes_no_ese(self, tmp_path: Path):
        ws = tmp_path / "ws"
        ws.mkdir()
        (ws / "direction-summary.md").write_text(
            "| R |\n|---|\n| 1 |\n", encoding="utf-8"
        )
        assert "ESE" not in _mechanisms(ws)

    def test_budget_exhaustion_owes_ive(self, tmp_path: Path):
        ws = tmp_path / "ws"
        ws.mkdir()
        _stage(ws, 1, attempts_used=20, gate_met=False)

        obligations = [o for o in derive_obligations(ws) if o.mechanism == "IVE"]

        assert obligations
        assert "no-executable-within-budget" in obligations[0].reason

    def test_stage_three_underperformance_owes_ive(self, workspace: Path):
        _stage(workspace, 3, gate_met=False)

        obligations = [o for o in derive_obligations(workspace) if o.mechanism == "IVE"]

        assert obligations
        assert "worse-than-baseline" in obligations[0].reason

    def test_clean_run_owes_no_ive(self, workspace: Path):
        assert "IVE" not in _mechanisms(workspace)

    def test_exhaustion_takes_precedence_over_underperformance(self, workspace: Path):
        _stage(workspace, 1, attempts_used=20, gate_met=False)
        _stage(workspace, 3, gate_met=False)

        reasons = [
            o.reason for o in derive_obligations(workspace) if o.mechanism == "IVE"
        ]

        assert len(reasons) == 1
        assert "no-executable-within-budget" in reasons[0]


class TestObservedMechanisms:
    """What the run actually recorded."""

    def test_empty_when_no_reports(self, workspace: Path):
        assert observed_mechanisms(workspace) == {"IDE": [], "IVE": [], "ESE": []}

    def test_detects_each_mechanism(self, workspace: Path):
        _report(workspace, "cycle_1_ide.md")
        _report(workspace, "cycle_1_ese.md")

        observed = observed_mechanisms(workspace)

        assert observed["IDE"] == ["cycle_1_ide.md"]
        assert observed["ESE"] == ["cycle_1_ese.md"]
        assert observed["IVE"] == []

    def test_ignores_unrelated_files(self, workspace: Path):
        _report(workspace, "notes.md")
        assert observed_mechanisms(workspace) == {"IDE": [], "IVE": [], "ESE": []}

    def test_is_case_insensitive(self, workspace: Path):
        _report(workspace, "cycle_2_IDE.md")
        assert observed_mechanisms(workspace)["IDE"] == ["cycle_2_IDE.md"]


class TestBuildReport:
    """The gap between owed and performed is the whole output."""

    def test_reports_everything_missing_when_nothing_ran(self, workspace: Path):
        record = build_report(workspace)

        assert record["complete"] is False
        assert {item["mechanism"] for item in record["missing"]} == {"IDE", "ESE"}

    def test_complete_when_every_obligation_met(self, workspace: Path):
        _report(workspace, "cycle_1_ide.md")
        _report(workspace, "cycle_1_ese.md")

        record = build_report(workspace)

        assert record["complete"] is True, record["missing"]

    def test_failed_run_still_owes_ese(self, tmp_path: Path):
        ws = tmp_path / "ws"
        ws.mkdir()
        _stage(ws, 1, attempts_used=20, gate_met=False)
        _report(ws, "cycle_1_ive.md")

        record = build_report(ws)

        assert record["complete"] is False
        assert [item["mechanism"] for item in record["missing"]] == ["ESE"]

    def test_is_json_serializable(self, workspace: Path):
        assert json.loads(json.dumps(build_report(workspace)))


class TestCli:
    def test_exits_nonzero_and_names_owed_mechanisms(self, workspace: Path):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "evolution_enforcement.py"),
                "--workspace",
                str(workspace),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "OWED IDE" in result.stderr
        assert "OWED ESE" in result.stderr

    def test_exits_zero_when_complete(self, workspace: Path, tmp_path: Path):
        _report(workspace, "cycle_1_ide.md")
        _report(workspace, "cycle_1_ese.md")
        report = tmp_path / "evolution.json"

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "evolution_enforcement.py"),
                "--workspace",
                str(workspace),
                "--report",
                str(report),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stderr
        assert json.loads(report.read_text(encoding="utf-8"))["complete"] is True
