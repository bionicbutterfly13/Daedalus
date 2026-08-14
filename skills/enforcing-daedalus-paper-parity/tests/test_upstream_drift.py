"""Tests for upstream drift detection (T006).

Built on real throwaway git repositories rather than mocks: the value of this
check is entirely in whether it reads git correctly, and a mocked subprocess
would assert only that the code calls the functions it calls.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from check_upstream_drift import (  # noqa: E402
    UpstreamDriftError,
    build_report,
    count_divergence,
    ref_exists,
)


def _run(repo: Path, *args: str) -> None:
    """Run a git command in *repo*, failing loudly."""
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _commit(repo: Path, relative: str, text: str, message: str) -> None:
    """Write a file and commit it."""
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    _run(repo, "add", "-A")
    _run(repo, "commit", "-m", message)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A repo with an `upstream/main` ref that has diverged from HEAD."""
    root = tmp_path / "fork"
    root.mkdir()
    _run(root, "init", "-q", "-b", "main")
    _run(root, "config", "user.email", "test@example.invalid")
    _run(root, "config", "user.name", "Test")
    _commit(root, "README.md", "base\n", "base")

    # A branch standing in for upstream/main, then local work on top of the
    # shared base so the two genuinely diverge.
    _run(root, "branch", "upstream/main")
    _commit(root, "local-only.txt", "fork work\n", "fork work")
    return root


class TestRefExists:
    def test_true_for_present_ref(self, repo: Path):
        assert ref_exists(repo, "upstream/main")

    def test_false_for_absent_ref(self, repo: Path):
        assert not ref_exists(repo, "upstream/nonexistent")


class TestCountDivergence:
    def test_counts_ahead_and_behind(self, repo: Path):
        ahead, behind = count_divergence(repo, "HEAD", "upstream/main")
        assert (ahead, behind) == (1, 0)

    def test_counts_behind_after_upstream_moves(self, repo: Path):
        _run(repo, "checkout", "-q", "upstream/main")
        _commit(repo, "upstream-only.txt", "new\n", "upstream work")
        _run(repo, "checkout", "-q", "main")

        ahead, behind = count_divergence(repo, "HEAD", "upstream/main")

        assert ahead == 1
        assert behind == 1


class TestBuildReport:
    """Commits-behind alone is not the signal; touched files are."""

    def test_requires_no_review_when_no_tracked_file_differs(self, repo: Path):
        record = build_report(repo)
        assert record["review_required"] is False
        assert record["touched_divergence_files"] == []

    def test_flags_a_divergence_file(self, repo: Path):
        _run(repo, "checkout", "-q", "upstream/main")
        _commit(
            repo, "EvoScientist/config/settings.py", "upstream rewrite\n", "rewrite"
        )
        _run(repo, "checkout", "-q", "main")

        record = build_report(repo)

        assert record["review_required"] is True
        assert "EvoScientist/config/settings.py" in record["touched_divergence_files"]
        assert any("graft" in reason for reason in record["reasons"])

    def test_flags_a_finding_file(self, repo: Path):
        _run(repo, "checkout", "-q", "upstream/main")
        _commit(repo, "EvoScientist/backends.py", "upstream change\n", "backends")
        _run(repo, "checkout", "-q", "main")

        record = build_report(repo)

        assert record["review_required"] is True
        assert "EvoScientist/backends.py" in record["touched_finding_files"]
        assert any("re-verify the review" in reason for reason in record["reasons"])

    def test_unrelated_upstream_change_needs_no_review(self, repo: Path):
        _run(repo, "checkout", "-q", "upstream/main")
        _commit(repo, "docs/unrelated.md", "notes\n", "docs")
        _run(repo, "checkout", "-q", "main")

        record = build_report(repo)

        assert record["commits_behind"] == 1
        assert record["review_required"] is False

    def test_settings_py_counts_as_both_categories(self, repo: Path):
        _run(repo, "checkout", "-q", "upstream/main")
        _commit(repo, "EvoScientist/config/settings.py", "x\n", "settings")
        _run(repo, "checkout", "-q", "main")

        record = build_report(repo)

        assert "EvoScientist/config/settings.py" in record["touched_divergence_files"]
        assert "EvoScientist/config/settings.py" in record["touched_finding_files"]
        assert len(record["reasons"]) == 2

    def test_permanent_fork_divergence_alone_needs_no_review(self, repo: Path):
        """The fork's own deliberate divergences must not fire the check forever.

        Regression: the first implementation diffed HEAD against upstream/main,
        which also surfaces every permanent fork divergence, so a real-repo run
        demanded a review even immediately after a clean merge. Comparing
        against the merge base asks the right question: what did *upstream*
        change since we last merged it?
        """
        # A deliberate fork edit to a tracked divergence file, with upstream
        # standing still.
        _commit(
            repo,
            "EvoScientist/config/settings.py",
            "fork precedence rule\n",
            "fork: deliberate divergence",
        )

        record = build_report(repo)

        assert record["commits_behind"] == 0
        assert record["touched_divergence_files"] == []
        assert record["review_required"] is False

    def test_flags_upstream_change_even_when_fork_also_edited_the_file(
        self, repo: Path
    ):
        """Both sides touching the same divergence file is the dangerous case."""
        _commit(
            repo,
            "EvoScientist/config/settings.py",
            "fork precedence rule\n",
            "fork edit",
        )
        _run(repo, "checkout", "-q", "upstream/main")
        _commit(
            repo,
            "EvoScientist/config/settings.py",
            "upstream rewrite\n",
            "upstream edit",
        )
        _run(repo, "checkout", "-q", "main")

        record = build_report(repo)

        assert record["review_required"] is True
        assert "EvoScientist/config/settings.py" in record["touched_divergence_files"]

    def test_raises_when_upstream_never_fetched(self, repo: Path):
        with pytest.raises(UpstreamDriftError, match="git fetch upstream"):
            build_report(repo, upstream="upstream/absent")

    def test_is_json_serializable(self, repo: Path):
        assert json.loads(json.dumps(build_report(repo)))


class TestCli:
    def test_exits_one_when_review_required(self, repo: Path):
        _run(repo, "checkout", "-q", "upstream/main")
        _commit(repo, "EvoScientist/prompts.py", "changed\n", "prompts")
        _run(repo, "checkout", "-q", "main")

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "check_upstream_drift.py"),
                "--repo",
                str(repo),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "REVIEW" in result.stderr

    def test_exits_zero_when_clean(self, repo: Path, tmp_path: Path):
        report = tmp_path / "drift.json"

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "check_upstream_drift.py"),
                "--repo",
                str(repo),
                "--report",
                str(report),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stderr
        assert (
            json.loads(report.read_text(encoding="utf-8"))["review_required"] is False
        )

    def test_exits_two_when_upstream_missing(self, repo: Path):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "check_upstream_drift.py"),
                "--repo",
                str(repo),
                "--upstream",
                "upstream/absent",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2
        assert "git fetch upstream" in result.stderr
