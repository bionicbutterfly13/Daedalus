"""Tests for the pre-launch record and gate audit (T004, T007, T010).

The record's job is to make three unrecorded things recorded: which skill bytes
ran (F1), how human decision gates were resolved once ``ask_user`` was removed
(F6), and which memory entries retrieval picked (F4). Its failure mode is
accepting an incomplete record, so most tests here assert rejection.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from launch_record import (  # noqa: E402
    GOVERNED_DECISION_POINTS,
    GatePolicy,
    LaunchRecordError,
    build_launch_record,
    detect_gate_narration,
    load_events,
    validate_launch_record,
)
from memory_persistence import WORKSPACE_ENV_VAR  # noqa: E402


@pytest.fixture
def skills_root(tmp_path: Path) -> Path:
    """A minimal installed-skills tree."""
    root = tmp_path / "skills"
    for name in ("evo-memory", "research-ideation"):
        skill = root / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")
    return root


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """A pinned workspace holding one memory file."""
    ws = tmp_path / "lab-workspace"
    (ws / "memory").mkdir(parents=True)
    (ws / "memory" / "ideation-memory.md").write_text("# M_I\n", encoding="utf-8")
    return ws


def _record(workspace: Path, skills_root: Path, **overrides):
    """Build a valid launch record with a pinned workspace."""
    kwargs = {
        "run_id": "run-001",
        "workspace": workspace,
        "skills_root": skills_root,
        "gate_policy": GatePolicy.AUTO_SELECT_TOP1,
        "env": {WORKSPACE_ENV_VAR: str(workspace)},
    }
    kwargs.update(overrides)
    return build_launch_record(**kwargs)


class TestBuildLaunchRecord:
    """What gets pinned before launch."""

    def test_pins_skill_digests(self, workspace: Path, skills_root: Path):
        record = _record(workspace, skills_root)
        assert set(record["skill_digests"]) == {"evo-memory", "research-ideation"}

    def test_records_memory_baseline(self, workspace: Path, skills_root: Path):
        record = _record(workspace, skills_root)
        assert "ideation-memory.md" in record["memory_baseline"]

    def test_records_gate_policy_and_decision_points(
        self, workspace: Path, skills_root: Path
    ):
        record = _record(workspace, skills_root)
        assert record["gate_policy"] == "auto_select_top1"
        assert record["governed_decision_points"] == list(GOVERNED_DECISION_POINTS)

    def test_hashes_the_prompt(
        self, workspace: Path, skills_root: Path, tmp_path: Path
    ):
        prompt = tmp_path / "prompt.txt"
        prompt.write_text("do science\n", encoding="utf-8")

        record = _record(workspace, skills_root, prompt_path=prompt)

        assert len(record["prompt_sha256"]) == 64

    def test_records_injected_memory_entries(self, workspace: Path, skills_root: Path):
        record = _record(
            workspace,
            skills_root,
            injected_memory_entries={"M_I": ["contrastive-learning"], "M_E": []},
        )
        assert record["injected_memory_entries"]["M_I"] == ["contrastive-learning"]

    def test_flags_unpinned_workspace(self, workspace: Path, skills_root: Path):
        record = _record(workspace, skills_root, env={})
        assert record["workspace_pinned"] is False
        assert record["persistence_violations"]

    def test_rejects_a_non_policy_value(self, workspace: Path, skills_root: Path):
        with pytest.raises(LaunchRecordError, match="F6"):
            build_launch_record(
                run_id="r",
                workspace=workspace,
                skills_root=skills_root,
                gate_policy="whatever",  # type: ignore[arg-type]
            )

    def test_is_json_serializable(self, workspace: Path, skills_root: Path):
        assert json.loads(json.dumps(_record(workspace, skills_root)))


class TestValidateLaunchRecord:
    """An incomplete record must not be launched against."""

    def test_accepts_complete_record(self, workspace: Path, skills_root: Path):
        assert validate_launch_record(_record(workspace, skills_root)) == []

    def test_rejects_empty_skill_digests(self, workspace: Path, skills_root: Path):
        record = _record(workspace, skills_root)
        record["skill_digests"] = {}

        violations = validate_launch_record(record)

        assert any("unattributable" in v for v in violations)

    def test_rejects_unknown_gate_policy(self, workspace: Path, skills_root: Path):
        record = _record(workspace, skills_root)
        record["gate_policy"] = "ask_nicely"

        violations = validate_launch_record(record)

        assert any("model improvisation" in v for v in violations)

    def test_rejects_uncovered_decision_point(self, workspace: Path, skills_root: Path):
        record = _record(workspace, skills_root)
        record["governed_decision_points"] = ["research_ideation_top3_selection"]

        violations = validate_launch_record(record)

        assert any("code_generation_mode_selection" in v for v in violations)

    def test_rejects_unpinned_workspace(self, workspace: Path, skills_root: Path):
        record = _record(workspace, skills_root, env={})
        violations = validate_launch_record(record)
        assert any("workspace not pinned" in v for v in violations)

    def test_accepts_surface_to_hermes_policy(self, workspace: Path, skills_root: Path):
        record = _record(
            workspace, skills_root, gate_policy=GatePolicy.SURFACE_TO_HERMES
        )
        assert validate_launch_record(record) == []


class TestDetectGateNarration:
    """F6's observable signature: a gate narrated instead of asked."""

    def test_detects_a_selection_prompt_in_prose(self):
        events = [
            {
                "type": "text",
                "content": "Here are the top-3. Which idea would you like "
                "to develop into a full proposal? (1/2/3)",
            }
        ]

        findings = detect_gate_narration(events)

        assert len(findings) == 1
        assert findings[0].event_index == 0

    def test_detects_an_assumed_default(self):
        events = [
            {
                "type": "text",
                "content": "No mode was specified, so I'll assume Lite mode.",
            }
        ]
        assert detect_gate_narration(events)

    def test_ignores_ordinary_output(self):
        events = [
            {"type": "text", "content": "Stage 1 reproduced the baseline within 1.4%."},
            {"type": "tool_use", "content": "please choose"},
        ]
        assert detect_gate_narration(events) == []

    def test_reports_one_finding_per_event(self):
        events = [
            {
                "type": "text",
                "content": "please choose one. which idea would you prefer?",
            }
        ]
        assert len(detect_gate_narration(events)) == 1

    def test_tolerates_non_string_content(self):
        events = [{"type": "text", "content": {"blocks": []}}, {"type": "text"}]
        assert detect_gate_narration(events) == []

    def test_scans_the_done_event(self):
        events = [
            {"type": "done", "response": "Please confirm which direction to expand."}
        ]
        assert detect_gate_narration(events)


class TestLoadEvents:
    """The stream-json protocol is forward-compatible; the reader must be too."""

    def test_skips_unparseable_lines(self, tmp_path: Path):
        path = tmp_path / "events.jsonl"
        path.write_text(
            '{"type":"text","content":"a"}\nnot json\n\n{"type":"done"}\n',
            encoding="utf-8",
        )
        assert len(load_events(path)) == 2

    def test_skips_non_object_lines(self, tmp_path: Path):
        path = tmp_path / "events.jsonl"
        path.write_text('[1,2,3]\n{"type":"done"}\n', encoding="utf-8")
        assert len(load_events(path)) == 1


class TestCli:
    """The supervisor builds before launch and audits after."""

    def test_build_writes_record_and_exits_zero(
        self, workspace: Path, skills_root: Path, tmp_path: Path, monkeypatch
    ):
        out = tmp_path / "launch-record.json"
        monkeypatch.setenv(WORKSPACE_ENV_VAR, str(workspace))

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "launch_record.py"),
                "build",
                "--run-id",
                "run-001",
                "--workspace",
                str(workspace),
                "--skills-root",
                str(skills_root),
                "--gate-policy",
                "auto_select_top1",
                "--out",
                str(out),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stderr
        assert json.loads(out.read_text(encoding="utf-8"))["run_id"] == "run-001"

    def test_build_fails_when_workspace_unpinned(
        self, workspace: Path, skills_root: Path, tmp_path: Path, monkeypatch
    ):
        monkeypatch.delenv(WORKSPACE_ENV_VAR, raising=False)

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "launch_record.py"),
                "build",
                "--run-id",
                "r",
                "--workspace",
                str(workspace),
                "--skills-root",
                str(skills_root),
                "--gate-policy",
                "auto_select_top1",
                "--out",
                str(tmp_path / "r.json"),
            ],
            capture_output=True,
            text=True,
            env={"PATH": "/usr/bin:/bin"},
        )

        assert result.returncode == 1
        assert "workspace not pinned" in result.stderr

    def test_audit_flags_narrated_gate_under_auto_policy(
        self, workspace: Path, skills_root: Path, tmp_path: Path
    ):
        record_path = tmp_path / "launch-record.json"
        record_path.write_text(
            json.dumps(_record(workspace, skills_root)), encoding="utf-8"
        )
        events = tmp_path / "events.jsonl"
        events.write_text(
            json.dumps(
                {
                    "type": "text",
                    "content": "Which idea would you like to develop? (1/2/3)",
                }
            )
            + "\n",
            encoding="utf-8",
        )

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "launch_record.py"),
                "audit",
                "--events",
                str(events),
                "--launch-record",
                str(record_path),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "narrated rather than resolved" in result.stderr

    def test_audit_passes_on_clean_transcript(
        self, workspace: Path, skills_root: Path, tmp_path: Path
    ):
        record_path = tmp_path / "launch-record.json"
        record_path.write_text(
            json.dumps(_record(workspace, skills_root)), encoding="utf-8"
        )
        events = tmp_path / "events.jsonl"
        events.write_text(
            json.dumps({"type": "done", "response": "Stage 4 ablation complete."})
            + "\n",
            encoding="utf-8",
        )

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "launch_record.py"),
                "audit",
                "--events",
                str(events),
                "--launch-record",
                str(record_path),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stderr
