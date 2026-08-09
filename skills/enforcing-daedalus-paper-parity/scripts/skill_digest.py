#!/usr/bin/env python3
"""Deterministic content digests for installed skill directories.

Daedalus's scientific method lives in skill directories installed outside this
repository (``~/.EvoScientist/skills``), which ``skill_manager`` can replace at
runtime. Finding F1 of ``docs/daedalus-paper-alignment-review.md``: a result is
not attributable unless the run records which skill bytes produced it.

The digest here is the anchor the launch record and acceptance gate both cite,
so it must be stable across machines and independent of filesystem ordering,
mtimes, and directory-walk order.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

# Artifacts that a skill directory may accumulate at runtime without changing
# the instructions the agent actually reads. Including them would make the
# digest unstable for reasons unrelated to skill content.
EXCLUDED_DIR_NAMES = frozenset({"__pycache__", ".git", ".pytest_cache"})
EXCLUDED_SUFFIXES = frozenset({".pyc", ".pyo"})


class SkillDigestError(Exception):
    """Raised when a skill tree cannot be digested."""


def _iter_skill_files(skill_dir: Path) -> list[Path]:
    """Return digestible files under *skill_dir*, sorted by relative POSIX path."""
    files: list[Path] = []
    for path in skill_dir.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        if any(
            part in EXCLUDED_DIR_NAMES for part in path.relative_to(skill_dir).parts
        ):
            continue
        if path.suffix in EXCLUDED_SUFFIXES:
            continue
        files.append(path)
    return sorted(files, key=lambda p: p.relative_to(skill_dir).as_posix())


def digest_skill_dir(skill_dir: Path) -> str:
    """Return the sha256 of a skill directory's content.

    The hash covers relative path *and* bytes for every file, so a rename is a
    different digest even when the bytes are unchanged. A NUL separator keeps
    path/content boundaries unambiguous.

    Args:
        skill_dir: Directory holding one skill (the parent of its ``SKILL.md``).

    Returns:
        Hex sha256 over the sorted (path, content) pairs.

    Raises:
        SkillDigestError: If *skill_dir* is not an existing directory.
    """
    if not skill_dir.is_dir():
        raise SkillDigestError(f"not a directory: {skill_dir}")

    digest = hashlib.sha256()
    for path in _iter_skill_files(skill_dir):
        rel = path.relative_to(skill_dir).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def digest_skill_tree(skills_root: Path) -> dict[str, str]:
    """Return ``{skill_name: sha256}`` for every skill under *skills_root*.

    A skill is any immediate subdirectory containing ``SKILL.md``; anything else
    (manifests such as ``.installed.yaml``, stray directories) is ignored so the
    map holds only things that can steer the agent.

    Args:
        skills_root: The installed-skills root (e.g. ``~/.EvoScientist/skills``).

    Returns:
        Mapping of skill directory name to its content digest, in sorted order.

    Raises:
        SkillDigestError: If *skills_root* is not an existing directory.
    """
    if not skills_root.is_dir():
        raise SkillDigestError(f"not a directory: {skills_root}")

    digests: dict[str, str] = {}
    for child in sorted(skills_root.iterdir(), key=lambda p: p.name):
        if not child.is_dir() or child.name in EXCLUDED_DIR_NAMES:
            continue
        if not (child / "SKILL.md").is_file():
            continue
        digests[child.name] = digest_skill_dir(child)
    return digests
