#!/usr/bin/env python3
"""Mark a task in tasks.md done, replacing its body.

Line-based rather than string-match: task bodies get reworded during
implementation, and an exact-text substitution silently no-ops when they do
(which already cost one commit whose message described files it did not carry).
This keys on the task ID alone.

Usage:
    python mark_task.py T003 "new body text (already wrapped)"
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

TASKS = Path(__file__).resolve().parent / "tasks.md"
_TASK_START = re.compile(r"^- \[( |x)\] (T\d+)\b")


def mark(task_id: str, body: str, *, tasks_path: Path = TASKS) -> None:
    """Replace *task_id*'s entry with a checked entry carrying *body*.

    Args:
        task_id: e.g. ``"T003"``.
        body: Replacement text, without the leading ``- [x] T003 ``.

    Raises:
        SystemExit: If the task ID is absent or appears more than once.
    """
    lines = tasks_path.read_text(encoding="utf-8").splitlines()
    starts = [
        index
        for index, line in enumerate(lines)
        if (match := _TASK_START.match(line)) and match.group(2) == task_id
    ]
    if len(starts) != 1:
        raise SystemExit(f"expected exactly one {task_id} entry, found {len(starts)}")

    start = starts[0]
    end = start + 1
    while (
        end < len(lines)
        and not _TASK_START.match(lines[end])
        and not lines[end].startswith("#")
    ):
        end += 1

    replacement = [f"- [x] {task_id} {body.strip()}"]
    lines[start:end] = replacement
    tasks_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    mark(sys.argv[1], sys.argv[2])
    print(f"marked {sys.argv[1]} done")
