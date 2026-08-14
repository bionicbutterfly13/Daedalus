"""Tests for the acceptance gates (T002, T003, T005, T007).

Every gate exists to convert a silent Daedalus success into a loud rejection.
The tests therefore care most about the negative cases: a gate that passes when
it found nothing to check is the exact bug these gates were written to prevent.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from parity_gates import (  # noqa: E402
    MIN_TOURNAMENT_ENTRANTS,
    PAPER_STAGE_BUDGETS,
    gate_memory_persistence,
    gate_pipeline_artifacts,
    gate_skill_pins,
    gate_stage_evidence_machine_checkable,
    run_all_gates,
)


def _tournament_table(rows: int) -> str:
    """Return a direction summary whose tournament table has *rows* entrants."""
    header = "| Rank | Title | ELO |\n|---|---|---|\n"
    body = "".join(f"| {i} | idea-{i} | {1500 - i} |\n" for i in range(1, rows + 1))
    return "# Direction Summary\n\n" + header + body


def _stage_record(stage: int, **overrides) -> dict:
    """Return a valid stage record for *stage*, with optional overrides."""
    record = {
        "stage": stage,
        "attempts_used": 3,
        "budget": PAPER_STAGE_BUDGETS[stage],
        "best_attempt_id": f"stage{stage}-attempt-003",
        "gate_met": True,
    }
    record.update(overrides)
    return record


@pytest.fixture
def passing_workspace(tmp_path: Path) -> Path:
    """A workspace carrying every artifact the gates require."""
    ws = tmp_path / "lab-workspace"
    memory = ws / "memory"
    memory.mkdir(parents=True)
    (memory / "ideation-memory.md").write_text(
        "# M_I\n- direction A\n", encoding="utf-8"
    )
    (memory / "experiment-memory.md").write_text(
        "# M_E\n- lr warmup\n", encoding="utf-8"
    )
    (memory / "evolution-reports").mkdir()
    (memory / "evolution-reports" / "cycle_1_ide.md").write_text(
        "IDE\n", encoding="utf-8"
    )
    (ws / "direction-summary.md").write_text(_tournament_table(7), encoding="utf-8")
    for stage in (1, 2):
        stage_dir = ws / "experiments" / f"stage{stage}_x"
        stage_dir.mkdir(parents=True)
        (stage_dir / "stage-record.json").write_text(
            json.dumps(_stage_record(stage)), encoding="utf-8"
        )
    return ws


class TestGateMemoryPersistence:
    """F3: an empty or unchanged store must never be accepted."""

    def test_rejects_absent_memory(self, tmp_path: Path):
        result = gate_memory_persistence(tmp_path)
        assert not result.passed
        assert "first cycle" in result.reasons[0]

    def test_accepts_populated_memory(self, passing_workspace: Path):
        assert gate_memory_persistence(passing_workspace).passed

    def test_rejects_memory_unchanged_from_baseline(self, passing_workspace: Path):
        baseline = gate_memory_persistence(passing_workspace).evidence["files"]

        result = gate_memory_persistence(passing_workspace, baseline)

        assert not result.passed
        assert "byte-identical" in result.reasons[0]

    def test_accepts_when_one_file_changed(self, passing_workspace: Path):
        baseline = dict(gate_memory_persistence(passing_workspace).evidence["files"])
        baseline["ideation-memory.md"] = "0" * 64

        assert gate_memory_persistence(passing_workspace, baseline).passed


class TestGatePipelineArtifacts:
    """F12/F5: the run must leave proof each claimed stage happened."""

    def test_rejects_empty_workspace(self, tmp_path: Path):
        result = gate_pipeline_artifacts(tmp_path)
        assert not result.passed
        assert len(result.reasons) == 3

    def test_accepts_complete_workspace(self, passing_workspace: Path):
        result = gate_pipeline_artifacts(passing_workspace)
        assert result.passed, result.reasons

    def test_rejects_three_candidate_tournament(self, passing_workspace: Path):
        (passing_workspace / "direction-summary.md").write_text(
            _tournament_table(3), encoding="utf-8"
        )

        result = gate_pipeline_artifacts(passing_workspace)

        assert not result.passed
        assert any("selected nothing" in reason for reason in result.reasons)

    def test_accepts_minimum_viable_tournament(self, passing_workspace: Path):
        (passing_workspace / "direction-summary.md").write_text(
            _tournament_table(MIN_TOURNAMENT_ENTRANTS), encoding="utf-8"
        )
        assert gate_pipeline_artifacts(passing_workspace).passed

    def test_rejects_missing_evolution_report(self, passing_workspace: Path):
        (passing_workspace / "memory" / "evolution-reports" / "cycle_1_ide.md").unlink()

        result = gate_pipeline_artifacts(passing_workspace)

        assert not result.passed
        assert any("evolution report" in reason for reason in result.reasons)

    def test_rejects_missing_stage_dirs(self, passing_workspace: Path):
        import shutil

        shutil.rmtree(passing_workspace / "experiments")

        result = gate_pipeline_artifacts(passing_workspace)

        assert not result.passed
        assert any("stage*" in reason for reason in result.reasons)


class TestGateStageEvidence:
    """F14: stage claims must be machine-checkable, not prose."""

    def test_rejects_when_no_stages_exist(self, tmp_path: Path):
        result = gate_stage_evidence_machine_checkable(tmp_path)
        assert not result.passed
        assert "absence of evidence" in result.reasons[0]

    def test_accepts_valid_records(self, passing_workspace: Path):
        assert gate_stage_evidence_machine_checkable(passing_workspace).passed

    def test_rejects_prose_only_stage(self, passing_workspace: Path):
        (passing_workspace / "experiments" / "stage1_x" / "stage-record.json").unlink()

        result = gate_stage_evidence_machine_checkable(passing_workspace)

        assert not result.passed
        assert any("prose logs cannot establish" in r for r in result.reasons)

    def test_rejects_missing_fields(self, passing_workspace: Path):
        record = _stage_record(1)
        del record["best_attempt_id"]
        (
            passing_workspace / "experiments" / "stage1_x" / "stage-record.json"
        ).write_text(json.dumps(record), encoding="utf-8")

        result = gate_stage_evidence_machine_checkable(passing_workspace)

        assert not result.passed
        assert any("missing ['best_attempt_id']" in r for r in result.reasons)

    def test_rejects_budget_that_contradicts_the_paper(self, passing_workspace: Path):
        (
            passing_workspace / "experiments" / "stage1_x" / "stage-record.json"
        ).write_text(json.dumps(_stage_record(1, budget=99)), encoding="utf-8")

        result = gate_stage_evidence_machine_checkable(passing_workspace)

        assert not result.passed
        assert any("paper budget 20" in r for r in result.reasons)

    def test_rejects_attempts_over_budget(self, passing_workspace: Path):
        (
            passing_workspace / "experiments" / "stage1_x" / "stage-record.json"
        ).write_text(json.dumps(_stage_record(1, attempts_used=21)), encoding="utf-8")

        result = gate_stage_evidence_machine_checkable(passing_workspace)

        assert not result.passed
        assert any("exceeds" in r for r in result.reasons)

    def test_rejects_gate_met_without_best_attempt(self, passing_workspace: Path):
        (
            passing_workspace / "experiments" / "stage1_x" / "stage-record.json"
        ).write_text(json.dumps(_stage_record(1, best_attempt_id="")), encoding="utf-8")

        result = gate_stage_evidence_machine_checkable(passing_workspace)

        assert not result.passed
        assert any("C_best is unattributable" in r for r in result.reasons)

    def test_rejects_malformed_json(self, passing_workspace: Path):
        (
            passing_workspace / "experiments" / "stage1_x" / "stage-record.json"
        ).write_text("{not json", encoding="utf-8")

        result = gate_stage_evidence_machine_checkable(passing_workspace)

        assert not result.passed
        assert any("not valid JSON" in r for r in result.reasons)


class TestGateSkillPins:
    """F1: a run whose skills are unpinned or drifted is unattributable."""

    @pytest.fixture
    def skills_root(self, tmp_path: Path) -> Path:
        root = tmp_path / "skills"
        for name in ("evo-memory", "research-ideation"):
            skill = root / name
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")
        return root

    def test_rejects_launch_record_without_pins(self, skills_root: Path):
        result = gate_skill_pins({}, skills_root)
        assert not result.passed
        assert "unattributable" in result.reasons[0]

    def test_accepts_matching_pins(self, skills_root: Path):
        from skill_digest import digest_skill_tree

        record = {"skill_digests": digest_skill_tree(skills_root)}

        assert gate_skill_pins(record, skills_root).passed

    def test_rejects_changed_skill(self, skills_root: Path):
        from skill_digest import digest_skill_tree

        record = {"skill_digests": digest_skill_tree(skills_root)}
        (skills_root / "evo-memory" / "SKILL.md").write_text(
            "changed\n", encoding="utf-8"
        )

        result = gate_skill_pins(record, skills_root)

        assert not result.passed
        assert "evo-memory" in result.reasons[0]

    def test_rejects_removed_skill(self, skills_root: Path):
        import shutil

        from skill_digest import digest_skill_tree

        record = {"skill_digests": digest_skill_tree(skills_root)}
        shutil.rmtree(skills_root / "research-ideation")

        result = gate_skill_pins(record, skills_root)

        assert not result.passed
        assert any("now missing" in r for r in result.reasons)

    def test_added_skill_is_reported_but_not_fatal(self, skills_root: Path):
        from skill_digest import digest_skill_tree

        record = {"skill_digests": digest_skill_tree(skills_root)}
        extra = skills_root / "paper-figures"
        extra.mkdir()
        (extra / "SKILL.md").write_text("# new\n", encoding="utf-8")

        result = gate_skill_pins(record, skills_root)

        assert result.passed
        assert result.evidence["added"] == ["paper-figures"]


class TestRunAllGates:
    """The combined verdict is what Archimedes records."""

    def test_rejects_empty_workspace(self, tmp_path: Path):
        record = run_all_gates(tmp_path)
        assert record["accepted"] is False
        assert set(record["failed_gates"]) == {
            "memory_persistence",
            "pipeline_artifacts",
            "stage_evidence_machine_checkable",
        }

    def test_accepts_complete_workspace(self, passing_workspace: Path):
        record = run_all_gates(passing_workspace)
        assert record["accepted"] is True, record["failed_gates"]

    def test_is_json_serializable(self, passing_workspace: Path):
        assert json.loads(json.dumps(run_all_gates(passing_workspace)))


class TestCli:
    """Exit status is the signal the supervisor acts on."""

    def test_exits_nonzero_and_explains_each_rejection(self, tmp_path: Path):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "parity_gates.py"),
                "--workspace",
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert result.stderr.count("REJECT") >= 3

    def test_exits_zero_on_complete_workspace(
        self, passing_workspace: Path, tmp_path: Path
    ):
        report = tmp_path / "acceptance.json"

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "parity_gates.py"),
                "--workspace",
                str(passing_workspace),
                "--report",
                str(report),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stderr
        assert json.loads(report.read_text(encoding="utf-8"))["accepted"] is True
