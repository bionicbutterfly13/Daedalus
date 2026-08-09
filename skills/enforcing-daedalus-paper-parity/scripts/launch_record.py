#!/usr/bin/env python3
"""Pin what a Daedalus run depends on, before it starts (T004, T007, T010).

``docs/cognitive-lab-architecture.md`` requires Archimedes to record prompt and
source hashes, model configuration, and permissions before launch. Three
findings make specific additions non-optional:

* F1  - the scientific method is swappable prompt files installed outside the
        repo, so a result is unattributable unless the run pins skill digests.
* F6  - under ``stream-json`` the ``ask_user`` tool is removed entirely, so
        prompts that instruct the agent to consult a human are neither asked
        nor answered. The policy that replaces them must be written down before
        the run, not inferred from the transcript afterwards.
* F4  - retrieval is LLM-judged rather than embedding-based, so which M_I/M_E
        entries were injected is unreproducible unless recorded.

The launch record is the artifact the acceptance gate later checks against.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from memory_persistence import (
    snapshot_memory,
    verify_persistence_config,
)
from skill_digest import digest_skill_tree


class GatePolicy(StrEnum):
    """How the run resolves prompts that ask a human to decide (F6).

    ``stream-json`` removes ``ask_user``, so a prompt-level question has no
    mechanism behind it. Exactly one of these must be declared per run.
    """

    #: Follow the paper: extend the top-ranked idea automatically (P = Extend(Top-1)).
    AUTO_SELECT_TOP1 = "auto_select_top1"
    #: Run with --no-auto-mode and drive the interrupt back to Hermes.
    SURFACE_TO_HERMES = "surface_to_hermes"


#: Prompt-level decision points that have no runtime mechanism under auto-mode.
GOVERNED_DECISION_POINTS = (
    "research_ideation_top3_selection",
    "code_generation_mode_selection",
)

# The model narrating a question instead of asking it is the observable
# signature of F6: the gate dissolved and the run improvised past it.
_NARRATION_PATTERNS = (
    re.compile(
        r"\bwhich (?:idea|option|mode) would you (?:like|prefer)\b", re.IGNORECASE
    ),
    re.compile(r"\bplease (?:choose|select|confirm|pick)\b", re.IGNORECASE),
    re.compile(r"\b(?:1/2/3|\(1/2/3\))\b"),
    # \u2019 is the curly apostrophe models actually emit; escaped rather than
    # literal so the source stays ASCII (ruff RUF001).
    re.compile("\\bI['\u2019]ll (?:assume|default to|proceed with)\\b", re.IGNORECASE),
    re.compile(r"\bsince no (?:user|human) (?:input|response)\b", re.IGNORECASE),
)


class LaunchRecordError(Exception):
    """Raised when a launch record cannot be built or is invalid."""


@dataclass(frozen=True)
class GateNarration:
    """One place the transcript shows a dissolved decision gate."""

    event_index: int
    pattern: str
    excerpt: str

    def to_dict(self) -> dict:
        """Return a JSON-serializable form."""
        return {
            "event_index": self.event_index,
            "pattern": self.pattern,
            "excerpt": self.excerpt,
        }


def sha256_file(path: Path) -> str:
    """Return the hex sha256 of *path*."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_launch_record(
    *,
    run_id: str,
    workspace: Path,
    skills_root: Path,
    gate_policy: GatePolicy,
    prompt_path: Path | None = None,
    injected_memory_entries: dict[str, list[str]] | None = None,
    env: dict[str, str] | None = None,
) -> dict:
    """Assemble the pre-launch record for a Daedalus run.

    Args:
        run_id: Archimedes-assigned identifier for this run.
        workspace: Workspace root the run will use.
        skills_root: Installed-skills root whose digests get pinned (F1).
        gate_policy: How prompt-level human gates are resolved (F6).
        prompt_path: The exact prompt handed to Daedalus, hashed if given.
        injected_memory_entries: ``{"M_I": [...], "M_E": [...]}`` naming the
            entries retrieval selected, so an LLM-judged choice is auditable (F4).
        env: Environment to inspect for workspace pinning. Defaults to the
            process environment.

    Returns:
        The launch record.

    Raises:
        LaunchRecordError: If *gate_policy* is not a :class:`GatePolicy`.
    """
    if not isinstance(gate_policy, GatePolicy):
        raise LaunchRecordError(
            f"gate_policy must be a GatePolicy, got {gate_policy!r}. "
            "An undeclared policy is exactly the F6 failure this record prevents."
        )

    persistence_violations = verify_persistence_config(env)
    return {
        "schema": "daedalus-parity-launch-record/v1",
        "run_id": run_id,
        "workspace": str(workspace),
        "skills_root": str(skills_root),
        "skill_digests": digest_skill_tree(skills_root),
        "gate_policy": str(gate_policy),
        "governed_decision_points": list(GOVERNED_DECISION_POINTS),
        "prompt_sha256": sha256_file(prompt_path) if prompt_path else None,
        "memory_baseline": snapshot_memory(workspace).files,
        "injected_memory_entries": injected_memory_entries or {},
        "workspace_pinned": not persistence_violations,
        "persistence_violations": persistence_violations,
        "notes": {
            "F1": "skill_digests pin the swappable method that produced this run",
            "F4": "injected_memory_entries record an LLM-judged retrieval choice",
            "F6": (
                "stream-json removes ask_user; gate_policy is the declared "
                "replacement for prompts that ask a human to decide"
            ),
        },
    }


def validate_launch_record(record: dict) -> list[str]:
    """Return the reasons *record* is unfit to launch against.

    Args:
        record: A launch record.

    Returns:
        Violation strings; empty when the record is complete.
    """
    violations: list[str] = []

    if not record.get("skill_digests"):
        violations.append(
            "skill_digests is empty: the run would be unattributable (F1)"
        )

    policy = record.get("gate_policy")
    if policy not in {str(member) for member in GatePolicy}:
        violations.append(
            f"gate_policy {policy!r} is not one of "
            f"{sorted(str(m) for m in GatePolicy)}: prompt-level human gates would "
            "resolve by model improvisation (F6)"
        )

    missing = sorted(
        set(GOVERNED_DECISION_POINTS) - set(record.get("governed_decision_points", []))
    )
    if missing:
        violations.append(
            f"decision points not covered by the declared policy: {missing}"
        )

    if not record.get("workspace_pinned", False):
        violations.extend(
            f"workspace not pinned: {reason}"
            for reason in record.get("persistence_violations", ["reason not recorded"])
        )

    return violations


def detect_gate_narration(events: list[dict]) -> list[GateNarration]:
    """Find places the transcript narrates a decision gate instead of asking (F6).

    Under ``stream-json`` auto-mode the ``ask_user`` tool does not exist, so a
    prompt that tells the agent to consult the user produces prose rather than
    an event. Those passages are the observable trace of a dissolved gate.

    Args:
        events: Parsed stream-json events, in order.

    Returns:
        One :class:`GateNarration` per matching passage.
    """
    findings: list[GateNarration] = []
    for index, event in enumerate(events):
        if event.get("type") not in {"text", "assistant", "done", "thinking"}:
            continue
        content = event.get("content") or event.get("response") or ""
        if not isinstance(content, str):
            continue
        for pattern in _NARRATION_PATTERNS:
            match = pattern.search(content)
            if not match:
                continue
            start = max(0, match.start() - 40)
            findings.append(
                GateNarration(
                    event_index=index,
                    pattern=pattern.pattern,
                    excerpt=content[start : match.end() + 40].strip(),
                )
            )
            break
    return findings


def load_events(path: Path) -> list[dict]:
    """Parse a stream-json (JSONL) transcript, skipping unparseable lines.

    Unparseable lines are skipped rather than fatal: the protocol is explicitly
    forward-compatible, and a consumer that dies on an unknown line would be
    less robust than the spec requires.
    """
    events: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            events.append(parsed)
    return events


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: build a record, or audit a transcript against one."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="write a pre-launch record")
    build.add_argument("--run-id", required=True)
    build.add_argument("--workspace", type=Path, required=True)
    build.add_argument(
        "--skills-root", type=Path, default=Path.home() / ".EvoScientist" / "skills"
    )
    build.add_argument(
        "--gate-policy",
        required=True,
        choices=[str(member) for member in GatePolicy],
    )
    build.add_argument("--prompt", type=Path, default=None)
    build.add_argument("--out", type=Path, required=True)

    audit = sub.add_parser("audit", help="check a transcript for dissolved gates")
    audit.add_argument("--events", type=Path, required=True)
    audit.add_argument("--launch-record", type=Path, required=True)

    args = parser.parse_args(argv)

    if args.command == "build":
        record = build_launch_record(
            run_id=args.run_id,
            workspace=args.workspace,
            skills_root=args.skills_root,
            gate_policy=GatePolicy(args.gate_policy),
            prompt_path=args.prompt,
        )
        violations = validate_launch_record(record)
        record["validation_violations"] = violations
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(json.dumps(record, indent=2, sort_keys=True))
        if violations:
            for violation in violations:
                print(f"error: {violation}", file=sys.stderr)
            return 1
        return 0

    record = json.loads(args.launch_record.read_text(encoding="utf-8"))
    narrations = detect_gate_narration(load_events(args.events))
    result = {
        "schema": "daedalus-parity-gate-audit/v1",
        "run_id": record.get("run_id"),
        "gate_policy": record.get("gate_policy"),
        "narrations": [item.to_dict() for item in narrations],
    }
    print(json.dumps(result, indent=2, sort_keys=True))

    if narrations and record.get("gate_policy") == str(GatePolicy.AUTO_SELECT_TOP1):
        print(
            f"error: {len(narrations)} decision gate(s) were narrated rather than "
            "resolved by the declared auto-select policy (F6)",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
