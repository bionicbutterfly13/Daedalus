#!/usr/bin/env python3
"""Report how far the fork has drifted from upstream, and whether it matters (T006).

Deployment gap D1: the fork sat three releases behind (v0.2.3 vs V0.2.6) with no
update cadence, which is how a paper-alignment review came to be written against
stale code. The v0.2.3 -> V0.2.6 sync then found upstream had rewritten the exact
function holding a deliberate fork fix, and had shipped a test asserting the
opposite behavior.

So "how many commits behind" is not the useful signal on its own. What matters is
whether upstream touched the files where this fork carries deliberate divergences,
or the files the alignment findings cite. This reports both, and exits nonzero
only when a review is actually warranted.

Read-only: fetches nothing, mutates nothing. The caller decides when to fetch.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Files carrying deliberate fork divergences. Upstream changes here need the
# graft-not-pick treatment; see the fork-merge-deliberate-divergences skill and
# the "Fork resolutions" section of the V0.2.6 merge commit.
DIVERGENCE_FILES = (
    "EvoScientist/config/settings.py",
    "EvoScientist/langgraph_dev/manager.py",
    "EvoScientist/llm/models.py",
    "EvoScientist/deploy/webui.py",
    "EvoScientist/runtime/__init__.py",
    "EvoScientist/subagents/_factory.py",
    "tests/test_config.py",
)

# Files whose behavior the alignment findings depend on. Upstream changes here
# may confirm, refute, or obsolete a finding, so the review needs re-running.
FINDING_FILES = (
    "EvoScientist/EvoScientist.py",
    "EvoScientist/backends.py",
    "EvoScientist/paths.py",
    "EvoScientist/prompts.py",
    "EvoScientist/memory/search.py",
    "EvoScientist/cli/commands.py",
    "EvoScientist/config/settings.py",
    "EvoScientist/utils.py",
    "docs/guides/stream-json.md",
    "CONTRIBUTING.md",
)


class UpstreamDriftError(Exception):
    """Raised when the comparison cannot be made."""


def _git(repo: Path, *args: str) -> str:
    """Run a read-only git command in *repo* and return stdout.

    Raises:
        UpstreamDriftError: If git exits nonzero.
    """
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise UpstreamDriftError(
            f"git {' '.join(args)} failed: {result.stderr.strip() or 'no stderr'}"
        )
    return result.stdout


def ref_exists(repo: Path, ref: str) -> bool:
    """True when *ref* resolves in *repo*."""
    try:
        _git(repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    except UpstreamDriftError:
        return False
    return True


def count_divergence(repo: Path, local: str, upstream: str) -> tuple[int, int]:
    """Return ``(ahead, behind)`` commit counts for *local* against *upstream*."""
    output = _git(repo, "rev-list", "--left-right", "--count", f"{local}...{upstream}")
    ahead, behind = output.split()
    return int(ahead), int(behind)


def merge_base(repo: Path, local: str, upstream: str) -> str:
    """Return the commit where *local* and *upstream* last shared history."""
    return _git(repo, "merge-base", local, upstream).strip()


def changed_files(repo: Path, local: str, upstream: str) -> list[str]:
    """Return files *upstream* changed since it last shared history with *local*.

    Diffing ``local`` against ``upstream`` directly would also surface this
    fork's permanent deliberate divergences, so every check would demand a
    review forever. The merge base answers the question actually being asked:
    what has upstream changed since we last merged it?
    """
    base = merge_base(repo, local, upstream)
    output = _git(repo, "diff", "--name-only", base, upstream)
    return sorted(line for line in output.splitlines() if line)


def build_report(
    repo: Path, *, local: str = "HEAD", upstream: str = "upstream/main"
) -> dict:
    """Assess drift and decide whether a review is warranted.

    Args:
        repo: Repository root.
        local: Local ref.
        upstream: Upstream tracking ref.

    Returns:
        A record with counts, the touched divergence/finding files, and a
        ``review_required`` flag.

    Raises:
        UpstreamDriftError: If *upstream* does not resolve (never fetched).
    """
    if not ref_exists(repo, upstream):
        raise UpstreamDriftError(
            f"{upstream} does not resolve; run `git fetch upstream` first. "
            "This check is deliberately read-only."
        )

    ahead, behind = count_divergence(repo, local, upstream)
    changed = changed_files(repo, local, upstream)
    base = merge_base(repo, local, upstream)
    changed_set = set(changed)

    touched_divergences = sorted(changed_set & set(DIVERGENCE_FILES))
    touched_findings = sorted(changed_set & set(FINDING_FILES))

    reasons: list[str] = []
    if touched_divergences:
        reasons.append(
            "upstream differs in files carrying deliberate fork divergences; a merge "
            "must graft the fork rule onto upstream's version rather than pick a side: "
            f"{touched_divergences}"
        )
    if touched_findings:
        reasons.append(
            "upstream differs in files the alignment findings cite; re-verify the "
            f"review before acting on it: {touched_findings}"
        )

    return {
        "schema": "daedalus-parity-upstream-drift/v1",
        "task": "T006",
        "local_ref": local,
        "upstream_ref": upstream,
        "merge_base": base,
        "commits_ahead": ahead,
        "commits_behind": behind,
        "changed_file_count": len(changed),
        "touched_divergence_files": touched_divergences,
        "touched_finding_files": touched_findings,
        "review_required": bool(reasons),
        "reasons": reasons,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Exits nonzero when a review is warranted."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--local", default="HEAD")
    parser.add_argument("--upstream", default="upstream/main")
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        record = build_report(args.repo, local=args.local, upstream=args.upstream)
    except UpstreamDriftError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    serialized = json.dumps(record, indent=2, sort_keys=True)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(serialized + "\n", encoding="utf-8")
    print(serialized)

    if record["review_required"]:
        for reason in record["reasons"]:
            print(f"REVIEW {reason}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
