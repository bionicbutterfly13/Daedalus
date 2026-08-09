"""End-to-end demonstration of the parity criteria.

Each test walks the full supervisor sequence -- build a launch record, run the
cycle, run every gate -- and asserts the outcome the parity definition requires.
The point is not unit coverage (the other modules have that) but that the pieces
compose into an acceptance decision, and that a run which does nothing is
rejected rather than accepted.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from evolution_enforcement import build_report as evolution_report  # noqa: E402
from launch_record import (  # noqa: E402
    GatePolicy,
    build_launch_record,
    detect_gate_narration,
    validate_launch_record,
)
from memory_persistence import WORKSPACE_ENV_VAR, verify_shared_memory  # noqa: E402
from parity_gates import run_all_gates  # noqa: E402

STAGE_BUDGETS = {1: 20, 2: 12, 3: 12, 4: 18}


@pytest.fixture
def skills_root(tmp_path: Path) -> Path:
    """A stand-in installed-skills tree."""
    root = tmp_path / "skills"
    for name in ("evo-memory", "research-ideation", "experiment-pipeline"):
        skill = root / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")
    return root


@pytest.fixture
def lab_workspace(tmp_path: Path) -> Path:
    """The durable, pinned lab workspace shared by every cycle."""
    workspace = tmp_path / "lab-workspace"
    (workspace / "memory").mkdir(parents=True)
    return workspace


def _run_cycle(
    workspace: Path,
    *,
    cycle: int,
    entrants: int = 7,
    stages: tuple[int, ...] = (1, 2, 3, 4),
    gate_met: bool = True,
    mechanisms: tuple[str, ...] = ("ide", "ese"),
) -> None:
    """Write the artifacts a compliant Daedalus cycle would leave behind."""
    memory = workspace / "memory"
    memory.mkdir(parents=True, exist_ok=True)

    ideation = memory / "ideation-memory.md"
    existing = ideation.read_text(encoding="utf-8") if ideation.is_file() else "# M_I\n"
    ideation.write_text(
        f"{existing}- cycle {cycle}: direction-{cycle} (feasible)\n", encoding="utf-8"
    )
    (memory / "experiment-memory.md").write_text(
        f"# M_E\n- cycle {cycle}: lr warmup helps\n", encoding="utf-8"
    )

    reports = memory / "evolution-reports"
    reports.mkdir(exist_ok=True)
    for mechanism in mechanisms:
        (reports / f"cycle_{cycle}_{mechanism}.md").write_text(
            f"{mechanism.upper()} for cycle {cycle}\n", encoding="utf-8"
        )

    header = "| Rank | Title | ELO |\n|---|---|---|\n"
    body = "".join(f"| {i} | idea-{i} | {1500 - i} |\n" for i in range(1, entrants + 1))
    (workspace / "direction-summary.md").write_text(header + body, encoding="utf-8")

    for stage in stages:
        stage_dir = workspace / "experiments" / f"stage{stage}_x"
        stage_dir.mkdir(parents=True, exist_ok=True)
        (stage_dir / "stage-record.json").write_text(
            json.dumps(
                {
                    "stage": stage,
                    "budget": STAGE_BUDGETS[stage],
                    "attempts_used": 4,
                    "best_attempt_id": f"stage{stage}-attempt-004",
                    "gate_met": gate_met,
                }
            ),
            encoding="utf-8",
        )


class TestParityCriterion1:
    """Two consecutive cycles in different workdirs share M_I/M_E."""

    def test_pinned_workspace_carries_memory_between_cycles(
        self, lab_workspace: Path, tmp_path: Path
    ):
        # Cycle 1 runs from one launch directory, cycle 2 from another. Both are
        # pinned to the same workspace, which is the whole mitigation.
        (tmp_path / "launch-dir-a").mkdir()
        (tmp_path / "launch-dir-b").mkdir()

        _run_cycle(lab_workspace, cycle=1)
        after_first = (lab_workspace / "memory" / "ideation-memory.md").read_text(
            encoding="utf-8"
        )
        _run_cycle(lab_workspace, cycle=2)
        after_second = (lab_workspace / "memory" / "ideation-memory.md").read_text(
            encoding="utf-8"
        )

        shared, reasons = verify_shared_memory(lab_workspace, lab_workspace)

        assert shared, reasons
        assert "cycle 1" in after_first
        # The decisive assertion: cycle 2 can still see what cycle 1 learned.
        assert "cycle 1" in after_second
        assert "cycle 2" in after_second

    def test_unpinned_workspaces_do_not_share(self, tmp_path: Path):
        ws_a = tmp_path / "run-a"
        ws_b = tmp_path / "run-b"
        _run_cycle(ws_a, cycle=1)
        ws_b.mkdir()

        shared, reasons = verify_shared_memory(ws_a, ws_b)

        assert not shared
        assert any("memory directories differ" in reason for reason in reasons)


class TestParityCriterion2:
    """Gates fail loudly on missing memory, artifacts, and skill pins."""

    def test_full_sequence_accepts_a_compliant_run(
        self, lab_workspace: Path, skills_root: Path
    ):
        record = build_launch_record(
            run_id="run-001",
            workspace=lab_workspace,
            skills_root=skills_root,
            gate_policy=GatePolicy.AUTO_SELECT_TOP1,
            env={WORKSPACE_ENV_VAR: str(lab_workspace)},
        )
        assert validate_launch_record(record) == []
        baseline = record["memory_baseline"]

        _run_cycle(lab_workspace, cycle=1)

        acceptance = run_all_gates(
            lab_workspace,
            launch_record=record,
            skills_root=skills_root,
            memory_baseline=baseline,
        )

        assert acceptance["accepted"] is True, acceptance["failed_gates"]

    def test_a_run_that_did_nothing_is_rejected(
        self, lab_workspace: Path, skills_root: Path
    ):
        """The silent-success case: the run 'completed' and produced nothing."""
        record = build_launch_record(
            run_id="run-002",
            workspace=lab_workspace,
            skills_root=skills_root,
            gate_policy=GatePolicy.AUTO_SELECT_TOP1,
            env={WORKSPACE_ENV_VAR: str(lab_workspace)},
        )

        acceptance = run_all_gates(
            lab_workspace,
            launch_record=record,
            skills_root=skills_root,
            memory_baseline=record["memory_baseline"],
        )

        assert acceptance["accepted"] is False
        assert set(acceptance["failed_gates"]) == {
            "memory_persistence",
            "pipeline_artifacts",
            "stage_evidence_machine_checkable",
        }

    def test_three_candidate_tournament_is_rejected(
        self, lab_workspace: Path, skills_root: Path
    ):
        record = build_launch_record(
            run_id="run-003",
            workspace=lab_workspace,
            skills_root=skills_root,
            gate_policy=GatePolicy.AUTO_SELECT_TOP1,
            env={WORKSPACE_ENV_VAR: str(lab_workspace)},
        )
        _run_cycle(lab_workspace, cycle=1, entrants=3)

        acceptance = run_all_gates(
            lab_workspace,
            launch_record=record,
            skills_root=skills_root,
            memory_baseline=record["memory_baseline"],
        )

        assert "pipeline_artifacts" in acceptance["failed_gates"]

    def test_skill_swap_mid_run_is_rejected(
        self, lab_workspace: Path, skills_root: Path
    ):
        record = build_launch_record(
            run_id="run-004",
            workspace=lab_workspace,
            skills_root=skills_root,
            gate_policy=GatePolicy.AUTO_SELECT_TOP1,
            env={WORKSPACE_ENV_VAR: str(lab_workspace)},
        )
        _run_cycle(lab_workspace, cycle=1)

        # skill_manager replaces the method mid-flight.
        (skills_root / "evo-memory" / "SKILL.md").write_text(
            "# different method\n", encoding="utf-8"
        )

        acceptance = run_all_gates(
            lab_workspace,
            launch_record=record,
            skills_root=skills_root,
            memory_baseline=record["memory_baseline"],
        )

        assert acceptance["accepted"] is False
        assert "skill_pins" in acceptance["failed_gates"]


class TestParityCriterion3:
    """ESE runs on partial trajectories; IVE is recorded on failure runs."""

    def test_failed_run_owes_both_ive_and_ese(self, lab_workspace: Path):
        _run_cycle(
            lab_workspace,
            cycle=1,
            stages=(1,),
            gate_met=False,
            mechanisms=(),
        )
        # Budget exhaustion is what makes IVE owed.
        stage_record = lab_workspace / "experiments" / "stage1_x" / "stage-record.json"
        record = json.loads(stage_record.read_text(encoding="utf-8"))
        record["attempts_used"] = record["budget"]
        stage_record.write_text(json.dumps(record), encoding="utf-8")

        result = evolution_report(lab_workspace)

        owed = {item["mechanism"] for item in result["missing"]}
        assert {"IVE", "ESE"} <= owed

    def test_recording_both_satisfies_the_obligation(self, lab_workspace: Path):
        _run_cycle(
            lab_workspace,
            cycle=1,
            stages=(1,),
            gate_met=False,
            mechanisms=("ide", "ive", "ese"),
        )
        stage_record = lab_workspace / "experiments" / "stage1_x" / "stage-record.json"
        record = json.loads(stage_record.read_text(encoding="utf-8"))
        record["attempts_used"] = record["budget"]
        stage_record.write_text(json.dumps(record), encoding="utf-8")

        assert evolution_report(lab_workspace)["complete"] is True


class TestParityCriterion4:
    """Gate policy is recorded, and dissolved gates are detectable."""

    def test_policy_is_recorded_and_narration_is_caught(
        self, lab_workspace: Path, skills_root: Path
    ):
        record = build_launch_record(
            run_id="run-005",
            workspace=lab_workspace,
            skills_root=skills_root,
            gate_policy=GatePolicy.AUTO_SELECT_TOP1,
            env={WORKSPACE_ENV_VAR: str(lab_workspace)},
        )
        assert record["gate_policy"] == "auto_select_top1"

        # Under the auto-select policy the run must not stop to ask.
        transcript = [
            {
                "type": "text",
                "content": "Ranked 7 candidates; extending the top-ranked.",
            },
            {
                "type": "text",
                "content": "Which idea would you like to develop? (1/2/3)",
            },
        ]

        narrations = detect_gate_narration(transcript)

        assert len(narrations) == 1
        assert narrations[0].event_index == 1

    def test_clean_transcript_under_auto_policy(self):
        transcript = [
            {"type": "text", "content": "Ranked 18 candidates."},
            {
                "type": "done",
                "response": "Extended the top-ranked idea into a proposal.",
            },
        ]
        assert detect_gate_narration(transcript) == []
