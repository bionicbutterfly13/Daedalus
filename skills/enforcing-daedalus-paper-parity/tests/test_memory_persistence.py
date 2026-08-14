"""Tests for evolution-memory persistence (T001, finding F3).

The load-bearing test here is ``test_memories_mount_rejects_raw_writes``: it
runs against live engine code and is the reason the fix pins the workspace
instead of repointing the skills at ``/memories/``. If a future change makes
that mount writable, the test fails and the simpler fix becomes available.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from memory_persistence import (  # noqa: E402
    EXPERIMENT_MEMORY,
    IDEATION_MEMORY,
    WORKSPACE_ENV_VAR,
    build_report,
    resolve_memory_dir,
    snapshot_memory,
    verify_persistence_config,
    verify_shared_memory,
)


def _seed_memory(workspace: Path, *, ideation: str = "# M_I\n- direction A\n") -> Path:
    """Create a workspace whose /memory/ holds an ideation memory file."""
    memory_dir = resolve_memory_dir(workspace)
    memory_dir.mkdir(parents=True, exist_ok=True)
    (memory_dir / IDEATION_MEMORY).write_text(ideation, encoding="utf-8")
    return memory_dir


class TestEngineWritePolicy:
    """Boundary capture: what the engine actually accepts, not what we assume."""

    def test_memories_mount_rejects_raw_writes(self, tmp_path: Path):
        """The persistent mount refuses M_I/M_E creation, so path-repointing fails.

        This is why T001 pins the workspace. Upstream contribution draft
        `engine-issue-memory-path.md` reports this pairing as the real defect.
        """
        from deepagents.backends import CompositeBackend

        from EvoScientist.backends import FilesystemBackend, MemoryFilesystemBackend

        workspace = tmp_path / "ws"
        memories = tmp_path / "memories"
        workspace.mkdir()
        memories.mkdir()
        backend = CompositeBackend(
            default=FilesystemBackend(root_dir=str(workspace), virtual_mode=True),
            routes={
                "/memories/": MemoryFilesystemBackend(
                    root_dir=str(memories), virtual_mode=True
                )
            },
        )

        blocked = backend.write("/memories/ideation-memory.md", "# M_I\n")

        assert blocked.error is not None
        assert "blocked" in blocked.error.lower()

    def test_singular_memory_path_writes_into_the_workspace(self, tmp_path: Path):
        """`/memory/` succeeds but lands in the selected project workspace."""
        from deepagents.backends import CompositeBackend

        from EvoScientist.backends import FilesystemBackend, MemoryFilesystemBackend

        workspace = tmp_path / "ws"
        memories = tmp_path / "memories"
        workspace.mkdir()
        memories.mkdir()
        backend = CompositeBackend(
            default=FilesystemBackend(root_dir=str(workspace), virtual_mode=True),
            routes={
                "/memories/": MemoryFilesystemBackend(
                    root_dir=str(memories), virtual_mode=True
                )
            },
        )

        result = backend.write("/memory/ideation-memory.md", "# M_I\n")

        assert result.error is None
        assert (workspace / "memory" / "ideation-memory.md").is_file()
        assert not any(memories.rglob("*.md"))


class TestVerifyPersistenceConfig:
    """Pinning the workspace is the mitigation; unpinned must be reported."""

    def test_unset_workspace_var_is_a_violation(self):
        violations = verify_persistence_config({})
        assert len(violations) == 1
        assert WORKSPACE_ENV_VAR in violations[0]

    def test_relative_path_is_a_violation(self, tmp_path: Path):
        violations = verify_persistence_config({WORKSPACE_ENV_VAR: "./lab"})
        assert any("relative" in v for v in violations)

    def test_missing_directory_is_a_violation(self, tmp_path: Path):
        violations = verify_persistence_config(
            {WORKSPACE_ENV_VAR: str(tmp_path / "absent")}
        )
        assert any("does not exist" in v for v in violations)

    def test_pinned_absolute_existing_dir_is_clean(self, tmp_path: Path):
        assert verify_persistence_config({WORKSPACE_ENV_VAR: str(tmp_path)}) == []

    def test_blank_value_is_treated_as_unset(self, tmp_path: Path):
        violations = verify_persistence_config({WORKSPACE_ENV_VAR: "   "})
        assert any("unset" in v for v in violations)


class TestSnapshotMemory:
    """Snapshots are how the acceptance gate detects a wiped store."""

    def test_absent_memory_yields_empty_snapshot(self, tmp_path: Path):
        snapshot = snapshot_memory(tmp_path)
        assert snapshot.files == {}
        assert snapshot.memory_dir == tmp_path / "memory"

    def test_digests_existing_files(self, tmp_path: Path):
        _seed_memory(tmp_path)
        snapshot = snapshot_memory(tmp_path)
        assert snapshot.present == (IDEATION_MEMORY,)

    def test_digest_changes_with_content(self, tmp_path: Path):
        _seed_memory(tmp_path)
        first = snapshot_memory(tmp_path).files[IDEATION_MEMORY]
        _seed_memory(tmp_path, ideation="# M_I\n- direction B\n")
        assert snapshot_memory(tmp_path).files[IDEATION_MEMORY] != first

    def test_tracks_both_memory_files(self, tmp_path: Path):
        memory_dir = _seed_memory(tmp_path)
        (memory_dir / EXPERIMENT_MEMORY).write_text("# M_E\n", encoding="utf-8")
        assert snapshot_memory(tmp_path).present == (
            EXPERIMENT_MEMORY,
            IDEATION_MEMORY,
        )


class TestVerifySharedMemory:
    """Parity criterion 1: two runs in different workdirs share M_I/M_E."""

    def test_distinct_workspaces_do_not_share(self, tmp_path: Path):
        ws_a = tmp_path / "run-a"
        ws_b = tmp_path / "run-b"
        _seed_memory(ws_a)
        ws_b.mkdir()

        shared, reasons = verify_shared_memory(ws_a, ws_b)

        assert not shared
        assert any("memory directories differ" in r for r in reasons)

    def test_pinned_workspace_shares(self, tmp_path: Path):
        pinned = tmp_path / "lab-workspace"
        _seed_memory(pinned)

        shared, reasons = verify_shared_memory(pinned, pinned)

        assert shared, reasons

    def test_empty_store_cannot_pass_as_success(self, tmp_path: Path):
        """Two empty workspaces resolve identically but prove nothing."""
        pinned = tmp_path / "lab-workspace"
        pinned.mkdir()

        shared, reasons = verify_shared_memory(pinned, pinned)

        assert not shared
        assert any("first cycle" in r for r in reasons)


class TestBuildReport:
    """The record the launch record and acceptance gate cite."""

    def test_reports_unpinned_configuration(self, tmp_path: Path):
        record = build_report(tmp_path, env={})
        assert record["workspace_pinned"] is False
        assert record["finding"] == "F3"
        assert json.loads(json.dumps(record))

    def test_reports_pinned_configuration(self, tmp_path: Path):
        record = build_report(tmp_path, env={WORKSPACE_ENV_VAR: str(tmp_path)})
        assert record["workspace_pinned"] is True
        assert record["config_violations"] == []


class TestCli:
    """The supervisor calls this before launching a cycle."""

    def test_require_pinned_fails_when_unpinned(self, tmp_path: Path, monkeypatch):
        monkeypatch.delenv(WORKSPACE_ENV_VAR, raising=False)
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "memory_persistence.py"),
                "--workspace",
                str(tmp_path),
                "--require-pinned",
            ],
            capture_output=True,
            text=True,
            env={"PATH": "/usr/bin:/bin"},
        )
        assert result.returncode == 1
        assert WORKSPACE_ENV_VAR in result.stderr

    def test_passes_when_pinned(self, tmp_path: Path):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "memory_persistence.py"),
                "--workspace",
                str(tmp_path),
                "--require-pinned",
            ],
            capture_output=True,
            text=True,
            env={"PATH": "/usr/bin:/bin", WORKSPACE_ENV_VAR: str(tmp_path)},
        )
        assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("name", [IDEATION_MEMORY, EXPERIMENT_MEMORY])
def test_tracked_names_match_the_installed_skills(name: str):
    """Guard against the skills renaming M_I/M_E out from under the gate."""
    skills_root = Path.home() / ".EvoScientist" / "skills"
    skill = skills_root / "evo-memory" / "SKILL.md"
    if not skill.is_file():
        pytest.skip("evo-memory skill not installed")
    assert name in skill.read_text(encoding="utf-8")
