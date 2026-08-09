"""Tests for the F3 memory-path patch and skill digests (T001, T007).

The patch exists because the evolution skills write M_I/M_E to an unmounted
path. These tests hold the two properties that make the fix trustworthy: the
rewrite is complete and idempotent, and the digests that make a run attributable
actually change when skill bytes change.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from patch_evolution_memory_paths import (  # noqa: E402
    MemoryPathPatchError,
    find_singular_references,
    patch_skill,
    patch_skills_root,
)
from skill_digest import (  # noqa: E402
    SkillDigestError,
    digest_skill_dir,
    digest_skill_tree,
)


def _write(path: Path, text: str) -> Path:
    """Create *path* (with parents) holding *text*."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture
def skills_root(tmp_path: Path) -> Path:
    """A miniature installed-skills tree mirroring the real defect."""
    root = tmp_path / "skills"

    _write(
        root / "evo-memory" / "SKILL.md",
        "---\nname: evo-memory\n---\n"
        "**Location**: `/memory/ideation-memory.md`\n"
        "**Location**: `/memory/experiment-memory.md`\n"
        "Reports go to `/memory/evolution-reports/cycle_N_type.md`.\n",
    )
    _write(
        root / "evo-memory" / "references" / "memory-schema.md",
        "| M_I | `/memory/ideation-memory.md` | First IDE |\n"
        "Memory persists because `/memory/` maps to the shared memory directory.\n",
    )
    _write(
        root / "research-ideation" / "SKILL.md",
        "---\nname: research-ideation\n---\n"
        "1. Read M_I at `/memory/ideation-memory.md`\n",
    )
    # A skill with no memory references must be left completely alone.
    _write(
        root / "paper-figures" / "SKILL.md",
        "---\nname: paper-figures\n---\nMake figures.\n",
    )
    # Non-markdown content must not be rewritten even if it mentions the path.
    _write(root / "evo-memory" / "assets" / "helper.py", "PATH = '/memory/x.md'\n")
    return root


class TestFindSingularReferences:
    """Detection must see the defect and must not see a false one."""

    def test_finds_every_markdown_reference(self, skills_root: Path):
        hits = find_singular_references(skills_root)
        assert len(hits) == 6
        assert all("/memory/" in line for _, _, line in hits)

    def test_ignores_already_correct_plural_path(self, tmp_path: Path):
        _write(tmp_path / "SKILL.md", "Read `/memories/ideation-memory.md`\n")
        assert find_singular_references(tmp_path) == []

    def test_ignores_non_markdown(self, skills_root: Path):
        assert not any(
            path.endswith(".py") for path, _, _ in find_singular_references(skills_root)
        )


class TestPatchSkill:
    """The rewrite must be complete, idempotent, and correctly scoped."""

    def test_rewrites_all_references_and_changes_digest(self, skills_root: Path):
        patch = patch_skill(skills_root / "evo-memory", apply=True)

        assert patch.changed
        assert patch.digest_before != patch.digest_after
        assert patch.total_replacements == 5
        assert find_singular_references(skills_root / "evo-memory") == []
        assert "/memories/ideation-memory.md" in (
            skills_root / "evo-memory" / "SKILL.md"
        ).read_text(encoding="utf-8")

    def test_is_idempotent(self, skills_root: Path):
        patch_skill(skills_root / "evo-memory", apply=True)
        second = patch_skill(skills_root / "evo-memory", apply=True)

        assert second.total_replacements == 0
        assert not second.changed

    def test_does_not_double_prefix(self, tmp_path: Path):
        skill = tmp_path / "s"
        _write(skill / "SKILL.md", "`/memory/a.md` and `/memories/b.md`\n")

        patch_skill(skill, apply=True)

        text = (skill / "SKILL.md").read_text(encoding="utf-8")
        assert "/memoriesies/" not in text
        assert text.count("/memories/") == 2

    def test_dry_run_leaves_disk_untouched(self, skills_root: Path):
        before = digest_skill_dir(skills_root / "evo-memory")

        patch = patch_skill(skills_root / "evo-memory", apply=False)

        assert patch.total_replacements == 5
        assert digest_skill_dir(skills_root / "evo-memory") == before
        assert patch.digest_after == before

    def test_leaves_unrelated_skill_untouched(self, skills_root: Path):
        before = digest_skill_dir(skills_root / "paper-figures")
        patch_skills_root(skills_root, apply=True)
        assert digest_skill_dir(skills_root / "paper-figures") == before

    def test_rejects_missing_directory(self, tmp_path: Path):
        with pytest.raises(MemoryPathPatchError):
            patch_skill(tmp_path / "absent", apply=False)


class TestPatchSkillsRoot:
    """The audit record is what the launch record and gate cite."""

    def test_reports_only_skills_that_changed(self, skills_root: Path):
        record = patch_skills_root(skills_root, apply=True)

        assert {entry["skill"] for entry in record["skills"]} == {
            "evo-memory",
            "research-ideation",
        }
        assert record["summary"]["total_replacements"] == 6
        assert record["summary"]["residual_singular_references"] == 0

    def test_names_expected_skills_that_did_not_change(self, skills_root: Path):
        record = patch_skills_root(skills_root, apply=False)

        # These two carry references in the real install but not in this fixture;
        # the gap must be reported rather than pass silently.
        assert record["summary"]["expected_skills_untouched"] == [
            "experiment-iterative-coder",
            "experiment-pipeline",
        ]

    def test_backup_captures_patched_bytes(self, skills_root: Path, tmp_path: Path):
        backup = tmp_path / "patched-skills"

        patch_skills_root(skills_root, apply=True, backup_dir=backup)

        copied = (backup / "evo-memory" / "SKILL.md").read_text(encoding="utf-8")
        assert "/memories/ideation-memory.md" in copied
        assert "/memory/" not in copied
        assert not (backup / "paper-figures").exists()

    def test_record_is_json_serializable(self, skills_root: Path):
        record = patch_skills_root(skills_root, apply=False)
        assert json.loads(json.dumps(record))["finding"] == "F3"


class TestSkillDigest:
    """Attribution (F1) depends on these digests being sensitive and stable."""

    def test_digest_is_stable_across_calls(self, skills_root: Path):
        assert digest_skill_dir(skills_root / "evo-memory") == digest_skill_dir(
            skills_root / "evo-memory"
        )

    def test_digest_changes_when_content_changes(self, skills_root: Path):
        before = digest_skill_dir(skills_root / "evo-memory")
        (skills_root / "evo-memory" / "SKILL.md").write_text(
            "different\n", encoding="utf-8"
        )
        assert digest_skill_dir(skills_root / "evo-memory") != before

    def test_digest_changes_when_a_file_is_renamed(self, tmp_path: Path):
        skill = tmp_path / "s"
        _write(skill / "SKILL.md", "body\n")
        _write(skill / "references" / "a.md", "same bytes\n")
        before = digest_skill_dir(skill)

        (skill / "references" / "a.md").rename(skill / "references" / "b.md")

        assert digest_skill_dir(skill) != before

    def test_digest_ignores_pycache(self, skills_root: Path):
        before = digest_skill_dir(skills_root / "evo-memory")
        _write(skills_root / "evo-memory" / "__pycache__" / "x.pyc", "junk\n")
        assert digest_skill_dir(skills_root / "evo-memory") == before

    def test_tree_covers_only_real_skills(self, skills_root: Path):
        (skills_root / "not-a-skill").mkdir()
        (skills_root / ".installed.yaml").write_text("manifest\n", encoding="utf-8")

        digests = digest_skill_tree(skills_root)

        assert set(digests) == {"evo-memory", "research-ideation", "paper-figures"}

    def test_rejects_missing_root(self, tmp_path: Path):
        with pytest.raises(SkillDigestError):
            digest_skill_tree(tmp_path / "absent")


class TestCli:
    """The CLI is the interface the supervisor calls."""

    def test_reports_without_applying_and_exits_zero(
        self, skills_root: Path, tmp_path: Path
    ):
        report = tmp_path / "report.json"

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "patch_evolution_memory_paths.py"),
                "--skills-root",
                str(skills_root),
                "--report",
                str(report),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stderr
        record = json.loads(report.read_text(encoding="utf-8"))
        assert record["applied"] is False
        assert record["summary"]["residual_singular_references"] == 6
        assert find_singular_references(skills_root)

    def test_apply_clears_all_references(self, skills_root: Path):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "patch_evolution_memory_paths.py"),
                "--skills-root",
                str(skills_root),
                "--apply",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stderr
        assert find_singular_references(skills_root) == []

    def test_missing_root_exits_nonzero(self, tmp_path: Path):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "patch_evolution_memory_paths.py"),
                "--skills-root",
                str(tmp_path / "absent"),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2
        assert "not a directory" in result.stderr
