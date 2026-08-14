#!/usr/bin/env python3
"""Verify stable same-workspace evolution memory (T001, finding F3).

Background
----------
The evolution skills read and write Ideation/Experimentation Memory under
``/memory/``. Upstream deliberately lets that path resolve through the default
workspace backend to ``<workdir>/memory/``. Sessions that reuse one workspace
see the same M_I/M_E. A new workdir starts with different files, and the skills'
own "if it doesn't exist, this is your first cycle" fallback makes that scope
change look like a fresh start.

Why the obvious fix is wrong
----------------------------
Repointing the skills at ``/memories/`` does **not** work.
``MemoryFilesystemBackend`` refuses every raw write and permits edits only to
*existing* files under ``/memories/profile/``. Verified against live engine
code (see ``test_memories_mount_rejects_raw_writes``):

    backend.write("/memories/ideation-memory.md", ...)
        -> error: "Raw writes to /memories are blocked."
    backend.write("/memory/ideation-memory.md", ...)
        -> ok, lands at <workspace>/memory/ideation-memory.md

Pinning ``EVOSCIENTIST_WORKSPACE_DIR`` keeps one local project on the same
workspace and prevents accidental scope changes. It does not implement the
paper's cross-project learning promise. That requires connecting EvoSkills to
the engine's separate shared memory system.

That is a configuration fix, so it carries no upstream merge surface.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

# Where the evolution skills put M_I / M_E, relative to the agent's virtual root.
MEMORY_SUBDIR = "memory"
IDEATION_MEMORY = "ideation-memory.md"
EXPERIMENT_MEMORY = "experiment-memory.md"
EVOLUTION_REPORTS_SUBDIR = "evolution-reports"

# The env var that pins the workspace root; see EvoScientist/paths.py.
WORKSPACE_ENV_VAR = "EVOSCIENTIST_WORKSPACE_DIR"

TRACKED_MEMORY_FILES = (IDEATION_MEMORY, EXPERIMENT_MEMORY)


class MemoryPersistenceError(Exception):
    """Raised when persistence cannot be resolved or verified."""


@dataclass(frozen=True)
class MemorySnapshot:
    """Content digests of the evolution-memory files under one workspace."""

    workspace: Path
    memory_dir: Path
    files: dict[str, str]

    @property
    def present(self) -> tuple[str, ...]:
        """Names of tracked memory files that exist."""
        return tuple(sorted(self.files))

    def to_dict(self) -> dict:
        """Return a JSON-serializable form."""
        return {
            "workspace": str(self.workspace),
            "memory_dir": str(self.memory_dir),
            "files": dict(sorted(self.files.items())),
        }


def resolve_memory_dir(workspace_dir: Path) -> Path:
    """Return the real directory the skills' ``/memory/`` resolves to.

    Args:
        workspace_dir: The run's workspace root (``EVOSCIENTIST_WORKSPACE_DIR``
            or the process cwd).

    Returns:
        ``<workspace_dir>/memory``.
    """
    return Path(workspace_dir) / MEMORY_SUBDIR


def snapshot_memory(workspace_dir: Path) -> MemorySnapshot:
    """Digest the evolution-memory files under *workspace_dir*.

    Missing files are simply absent from the mapping; that is the state the
    skills read as "first cycle", so callers must distinguish it explicitly
    rather than treating an empty snapshot as success.

    Args:
        workspace_dir: The run's workspace root.

    Returns:
        A :class:`MemorySnapshot` with a sha256 per existing tracked file.
    """
    memory_dir = resolve_memory_dir(workspace_dir)
    files: dict[str, str] = {}
    for name in TRACKED_MEMORY_FILES:
        path = memory_dir / name
        if path.is_file():
            files[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return MemorySnapshot(
        workspace=Path(workspace_dir), memory_dir=memory_dir, files=files
    )


def verify_persistence_config(env: dict[str, str] | None = None) -> list[str]:
    """Return reasons the supervised workspace is not explicitly pinned.

    An empty list means the configuration pins one durable workspace. It says
    nothing about sharing evolution memory with another workspace.

    Args:
        env: Environment mapping to inspect. Defaults to ``os.environ``.

    Returns:
        Human-readable violation strings, empty when configuration is sound.
    """
    env = dict(os.environ if env is None else env)
    violations: list[str] = []

    pinned = env.get(WORKSPACE_ENV_VAR, "").strip()
    if not pinned:
        violations.append(
            f"{WORKSPACE_ENV_VAR} is unset: same-directory sessions may reuse "
            "their /memory/ files, but changing the launch directory selects a "
            "different project-local store (F3)."
        )
        return violations

    path = Path(pinned)
    if not path.is_absolute():
        violations.append(
            f"{WORKSPACE_ENV_VAR}={pinned!r} is relative; it resolves against the "
            "launch directory and therefore does not pin anything."
        )
    if not path.exists():
        violations.append(
            f"{WORKSPACE_ENV_VAR}={pinned!r} does not exist; the run would create "
            "a fresh workspace and start from empty memory."
        )
    return violations


def verify_shared_memory(
    workspace_a: Path, workspace_b: Path
) -> tuple[bool, list[str]]:
    """Check that two workspaces resolve evolution memory to the same store.

    This is parity criterion 1: two consecutive cycles must share M_I/M_E.

    Args:
        workspace_a: First run's workspace root.
        workspace_b: Second run's workspace root.

    Returns:
        ``(shared, reasons)``. ``shared`` is True only when both workspaces
        resolve to the same memory directory *and* that directory holds at
        least one tracked memory file, so an "everything is empty" state can
        never pass as success.
    """
    snap_a = snapshot_memory(workspace_a)
    snap_b = snapshot_memory(workspace_b)
    reasons: list[str] = []

    if snap_a.memory_dir.resolve() != snap_b.memory_dir.resolve():
        reasons.append(
            f"memory directories differ: {snap_a.memory_dir} != {snap_b.memory_dir}; "
            "each run would read its own empty M_I/M_E"
        )
    if not snap_a.files and not snap_b.files:
        reasons.append(
            "no tracked memory files exist in either workspace; an empty store "
            "reads as 'first cycle' and cannot demonstrate persistence"
        )
    elif snap_a.files != snap_b.files:
        reasons.append(
            f"memory contents differ between workspaces: {snap_a.files} != {snap_b.files}"
        )
    return (not reasons), reasons


def build_report(workspace_dir: Path, env: dict[str, str] | None = None) -> dict:
    """Return the persistence record cited by the launch record and gate."""
    config_violations = verify_persistence_config(env)
    snapshot = snapshot_memory(workspace_dir)
    return {
        "schema": "daedalus-parity-memory-persistence/v1",
        "finding": "F3",
        "task": "T001",
        "workspace_pinned": not config_violations,
        "config_violations": config_violations,
        "snapshot": snapshot.to_dict(),
        "note": (
            "This verifies stable reuse of one workspace only. It does not prove "
            "cross-project paper memory. Do not repoint the skills at /memories/: "
            "that mount rejects raw writes."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Exits nonzero when the workspace is not pinned."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path(os.environ.get(WORKSPACE_ENV_VAR, Path.cwd())),
        help="workspace root to inspect",
    )
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument(
        "--require-pinned",
        action="store_true",
        help="exit nonzero when the workspace is not explicitly pinned",
    )
    args = parser.parse_args(argv)

    record = build_report(args.workspace)
    serialized = json.dumps(record, indent=2, sort_keys=True)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(serialized + "\n", encoding="utf-8")
    print(serialized)

    if args.require_pinned and record["config_violations"]:
        for violation in record["config_violations"]:
            print(f"error: {violation}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
