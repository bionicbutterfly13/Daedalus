#!/usr/bin/env python3
"""Repoint the evolution skills' memory paths at the engine's persistent mount.

Finding F3 of ``docs/daedalus-paper-alignment-review.md``: the EvoSkills
evolution skills read and write Ideation/Experimentation Memory under
``/memory/``, but the engine's ``CompositeBackend`` routes only ``/skills/`` and
``/memories/``. ``/memory/`` matches no route, so it falls through to the
default workspace backend rooted at the run's workdir. Cross-cycle memory never
reaches the persistent store, and the skills' own "if it doesn't exist, this is
your first cycle" fallback makes the loss indistinguishable from a fresh start.

This module rewrites the singular path to the mounted plural one, recording the
skill digests on both sides of the edit so the change is auditable and the
resulting runs are attributable (F1).

The same edit is drafted for upstream at
``specs/005-daedalus-paper-alignment/contributions/evoskills-pr-memory-path.md``;
patching the local install is the interim mitigation, not a substitute.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from skill_digest import digest_skill_dir

# The engine mounts persistent memory at ``/memories/`` (plural). A plain
# literal is sufficient and is what makes the rewrite idempotent: the output
# ``/memories/`` does not contain ``/memory/`` as a substring, so re-running
# the patch matches nothing. ``test_does_not_double_prefix`` pins that property.
_SINGULAR_MEMORY_PATH = re.compile(r"/memory/")
_CORRECT_PREFIX = "/memories/"

# Skills known to carry M_I / M_E path references. Used only to report on
# skills that were expected to change but did not; the patch itself walks
# whatever is present.
EXPECTED_SKILLS = frozenset(
    {
        "evo-memory",
        "research-ideation",
        "experiment-pipeline",
        "experiment-iterative-coder",
    }
)

PATCHABLE_SUFFIXES = frozenset({".md"})


class MemoryPathPatchError(Exception):
    """Raised when the patch cannot be applied safely."""


@dataclass
class FileEdit:
    """One patched file and how many replacements it received."""

    relative_path: str
    replacements: int


@dataclass
class SkillPatch:
    """The result of patching a single skill directory."""

    skill: str
    digest_before: str
    digest_after: str
    edits: list[FileEdit] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        """True when at least one replacement was written."""
        return self.digest_before != self.digest_after

    @property
    def total_replacements(self) -> int:
        """Total ``/memory/`` occurrences rewritten across this skill."""
        return sum(edit.replacements for edit in self.edits)

    def to_dict(self) -> dict:
        """Return a JSON-serializable record of this skill's patch."""
        return {
            "skill": self.skill,
            "digest_before": self.digest_before,
            "digest_after": self.digest_after,
            "changed": self.changed,
            "total_replacements": self.total_replacements,
            "files": [
                {"path": edit.relative_path, "replacements": edit.replacements}
                for edit in self.edits
            ],
        }


def find_singular_references(root: Path) -> list[tuple[str, int, str]]:
    """Return every ``/memory/`` reference under *root*.

    Args:
        root: Directory to scan (a skills root or a single skill).

    Returns:
        List of ``(relative_posix_path, line_number, line_text)``, sorted.
    """
    hits: list[tuple[str, int, str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix not in PATCHABLE_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if _SINGULAR_MEMORY_PATH.search(line):
                hits.append((path.relative_to(root).as_posix(), lineno, line.strip()))
    return hits


def patch_skill(skill_dir: Path, *, apply: bool) -> SkillPatch:
    """Rewrite ``/memory/`` to ``/memories/`` throughout one skill directory.

    Idempotent: running it on an already-patched skill produces zero
    replacements and an unchanged digest.

    Args:
        skill_dir: The skill directory to patch.
        apply: When False, compute the replacement counts without writing. The
            reported ``digest_after`` then equals ``digest_before``, because
            nothing changed on disk.

    Returns:
        A :class:`SkillPatch` describing what changed.

    Raises:
        MemoryPathPatchError: If *skill_dir* is not a directory.
    """
    if not skill_dir.is_dir():
        raise MemoryPathPatchError(f"not a directory: {skill_dir}")

    digest_before = digest_skill_dir(skill_dir)
    edits: list[FileEdit] = []

    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file() or path.suffix not in PATCHABLE_SUFFIXES:
            continue
        try:
            original = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        patched, count = _SINGULAR_MEMORY_PATH.subn(_CORRECT_PREFIX, original)
        if count == 0:
            continue
        edits.append(
            FileEdit(
                relative_path=path.relative_to(skill_dir).as_posix(),
                replacements=count,
            )
        )
        if apply:
            path.write_text(patched, encoding="utf-8")

    digest_after = digest_skill_dir(skill_dir) if apply else digest_before
    return SkillPatch(
        skill=skill_dir.name,
        digest_before=digest_before,
        digest_after=digest_after,
        edits=edits,
    )


def patch_skills_root(
    skills_root: Path,
    *,
    apply: bool,
    backup_dir: Path | None = None,
) -> dict:
    """Patch every skill under *skills_root* and return an audit record.

    Args:
        skills_root: Installed-skills root (e.g. ``~/.EvoScientist/skills``).
        apply: Write the changes. When False, report only.
        backup_dir: When applying, copy each *patched* skill here after the
            edit, so an upstream PR can be cut from the corrected bytes later.

    Returns:
        Audit record with per-skill digests and a summary. The record is what
        the launch record and acceptance gate cite.

    Raises:
        MemoryPathPatchError: If *skills_root* does not exist.
    """
    if not skills_root.is_dir():
        raise MemoryPathPatchError(f"not a directory: {skills_root}")

    patches: list[SkillPatch] = []
    for child in sorted(skills_root.iterdir(), key=lambda p: p.name):
        if not child.is_dir() or not (child / "SKILL.md").is_file():
            continue
        patch = patch_skill(child, apply=apply)
        if patch.edits:
            patches.append(patch)

    if apply and backup_dir is not None:
        backup_dir.mkdir(parents=True, exist_ok=True)
        for patch in patches:
            destination = backup_dir / patch.skill
            if destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(
                skills_root / patch.skill,
                destination,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )

    patched_names = {patch.skill for patch in patches}
    return {
        "schema": "daedalus-parity-memory-path-patch/v1",
        "finding": "F3",
        "skills_root": str(skills_root),
        "applied": apply,
        "from_prefix": "/memory/",
        "to_prefix": _CORRECT_PREFIX,
        "skills": [patch.to_dict() for patch in patches],
        "summary": {
            "skills_patched": len(patches),
            "total_replacements": sum(p.total_replacements for p in patches),
            "expected_skills_untouched": sorted(EXPECTED_SKILLS - patched_names),
            "residual_singular_references": len(find_singular_references(skills_root)),
        },
    }


def _default_skills_root() -> Path:
    """Return the conventional installed-skills root."""
    return Path.home() / ".EvoScientist" / "skills"


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Reports by default; ``--apply`` writes."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--skills-root", type=Path, default=_default_skills_root())
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write the changes (default: report only)",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=None,
        help="copy each patched skill here after applying",
    )
    parser.add_argument(
        "--report", type=Path, default=None, help="write JSON report here"
    )
    args = parser.parse_args(argv)

    try:
        record = patch_skills_root(
            args.skills_root, apply=args.apply, backup_dir=args.backup_dir
        )
    except MemoryPathPatchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    serialized = json.dumps(record, indent=2, sort_keys=True)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(serialized + "\n", encoding="utf-8")
    print(serialized)

    if args.apply and record["summary"]["residual_singular_references"]:
        print("error: singular /memory/ references remain after patch", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
