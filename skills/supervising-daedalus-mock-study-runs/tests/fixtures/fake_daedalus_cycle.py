#!/usr/bin/env python3
"""Deterministic subprocess fixture for the supervised resume driver."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


def _emit(event: dict[str, object]) -> None:
    print(json.dumps(event, sort_keys=True), flush=True)


def _result(request: dict[str, object], *, scenario: str) -> dict[str, object]:
    identity = request["expected_identity"]
    assert isinstance(identity, dict)
    result: dict[str, object] = {
        "schema": "daedalus-supervisor-worker-result/v1",
        "attempt_id": request["attempt_id"],
        "supervisor_run_id": request["supervisor_run_id"],
        "cycle_id": request["cycle_id"],
        "thread_id": request["thread_id"],
        "request_sha256": request["request_sha256"],
        "source_commit": identity["source_commit"],
        "imported_package_path": identity["imported_package_path"],
    }
    if request["mode"] == "resume":
        result["approved_request_digest"] = request.get("approved_request_digest")
    if scenario == "mismatched_thread":
        result["thread_id"] = "wrong-thread"
    elif scenario == "mismatched_run":
        result["supervisor_run_id"] = "wrong-run"
    elif scenario == "missing_identity":
        result.pop("thread_id")
    elif scenario == "changed_command" and request["mode"] == "resume":
        result["approved_request_digest"] = "0" * 64
    return result


def _interrupt(
    *,
    interrupt_id: str = "interrupt-001",
    tool_name: str = "execute",
    command: str = "python3 analysis.py",
    tool_id: str = "tool-001",
) -> dict[str, object]:
    return {
        "type": "interrupt",
        "interrupt_id": interrupt_id,
        "action_requests": [
            {
                "name": tool_name,
                "args": {"command": command},
                "id": tool_id,
            }
        ],
        "review_configs": [
            {
                "action_name": tool_name,
                "allowed_decisions": ["approve", "reject"],
            }
        ],
    }


def _run(request: dict[str, object], scenario: str) -> int:
    mode = request["mode"]

    if scenario == "timeout":
        time.sleep(5)
        return 0
    if scenario == "timeout_with_child":
        marker = Path(str(request["workdir"])) / "orphan-survived.txt"
        subprocess.Popen(
            [
                sys.executable,
                "-c",
                (
                    "import time; from pathlib import Path; time.sleep(0.5); "
                    f"Path({str(marker)!r}).write_text('survived')"
                ),
            ]
        )
        time.sleep(5)
        return 0
    if scenario == "malformed_json":
        print("{not-json", flush=True)
        return 0
    if scenario == "blank_stdout":
        return 0
    if scenario == "stderr_only":
        print("simulated fixture failure", file=sys.stderr, flush=True)
        return 0
    if scenario == "nonzero_exit":
        print("simulated nonzero", file=sys.stderr, flush=True)
        return 9
    if scenario == "missing_done":
        _emit({"type": "text", "content": "partial"})
        return 0
    if scenario == "unknown_tool":
        _emit(
            _interrupt(tool_name="network_probe", command="curl https://example.test")
        )
        _emit({"type": "done", "content": "", "response": ""})
        return 0
    if scenario == "unsafe_command":
        _emit(_interrupt(command="curl https://example.test"))
        _emit({"type": "done", "content": "", "response": ""})
        return 0
    if scenario == "unsafe_path":
        _emit(_interrupt(command="python3 ../escape.py"))
        _emit({"type": "done", "content": "", "response": ""})
        return 0
    if scenario == "duplicate_interrupt":
        event = _interrupt()
        _emit(event)
        _emit(event)
        _emit({"type": "done", "content": "", "response": ""})
        return 0
    if scenario == "reordered_event":
        _emit({"type": "done", "content": "complete", "response": "complete"})
        _emit({"type": "text", "content": "late"})
        return 0
    if scenario == "replayed_event":
        event = {
            "type": "tool_call",
            "name": "execute",
            "args": {"command": "python3 analysis.py"},
            "id": "tool-001",
        }
        _emit(event)
        _emit(event)
        _emit(_interrupt())
        _emit({"type": "done", "content": "", "response": ""})
        return 0
    if scenario == "outside_write":
        workdir = Path(str(request["workdir"]))
        (workdir / "undeclared.txt").write_text("not allowed", encoding="utf-8")
        _emit({"type": "done", "content": "complete", "response": "complete"})
        return 0
    if scenario == "silent_success":
        _emit({"type": "done", "content": "", "response": ""})
        return 0
    if scenario == "ask_user" and mode == "start":
        _emit(
            {
                "type": "ask_user",
                "interrupt_id": "ask-001",
                "tool_call_id": "ask-tool-001",
                "questions": [{"question": "Which fixture?", "type": "text"}],
            }
        )
        _emit({"type": "done", "content": "", "response": ""})
        return 0
    if scenario == "repeated_interrupt" and mode == "resume":
        _emit(_interrupt())
        _emit({"type": "done", "content": "", "response": ""})
        return 0

    if mode == "start":
        _emit(
            {
                "type": "tool_call",
                "name": "execute",
                "args": {"command": "python3 analysis.py"},
                "id": "tool-001",
            }
        )
        _emit(_interrupt())
        _emit({"type": "done", "content": "", "response": ""})
        return 0

    workdir = Path(str(request["workdir"]))
    if scenario == "outside_attempt_write":
        (workdir.parent.parent / "escaped.txt").write_text(
            "outside the attempt", encoding="utf-8"
        )
    if scenario == "outside_attempt_read":
        (workdir.parent.parent / "private-sentinel.txt").read_text(encoding="utf-8")
    if scenario == "network_operation":
        import socket

        socket.create_connection(("127.0.0.1", 9), timeout=0.1)
    if scenario == "acceptance_happy":
        report = {
            "schema": "daedalus-primary-study-report/v1",
            "packet_id": request["packet_id"],
            "attempt_id": request["attempt_id"],
            "run_id": request["supervisor_run_id"],
            "thread_id": request["thread_id"],
            "author": "Daedalus",
            "research_question": (
                "Does a deterministic synthetic treatment change a deterministic "
                "synthetic outcome?"
            ),
            "hypothesis": (
                "The treatment group mean exceeds the control group mean in the "
                "frozen synthetic table."
            ),
            "synthetic_inputs": {
                "control": [1.0, 2.0, 3.0],
                "treatment": [2.0, 3.0, 4.0],
            },
            "methods": "Compute both arithmetic means and their difference.",
            "workflow_stages_attempted": [
                "question_formulation",
                "hypothesis_generation",
                "method_selection",
                "synthetic_analysis",
                "result_interpretation",
                "primary_report",
            ],
            "analyses_performed": [
                "control_mean",
                "treatment_mean",
                "difference_in_means",
            ],
            "outputs_produced": ["daedalus-primary-study-report.json"],
            "measured_results": {
                "control_mean": 2.0,
                "treatment_mean": 3.0,
                "difference": 1.0,
            },
            "failures_and_retries": [],
            "limitations": [
                "Synthetic arithmetic does not establish external scientific validity."
            ],
            "unresolved_scientific_questions": [
                "Would a controlled real-runtime run preserve the same evidence chain?"
            ],
        }
        (workdir / "daedalus-primary-study-report.json").write_text(
            json.dumps(report, sort_keys=True), encoding="utf-8"
        )
    else:
        (workdir / "report.json").write_text(
            json.dumps({"result": "synthetic-pass"}), encoding="utf-8"
        )
    _emit({"type": "text", "content": "synthetic complete"})
    _emit(
        {
            "type": "done",
            "content": "synthetic complete",
            "response": "synthetic complete",
        }
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()

    request = json.loads(args.request.read_text(encoding="utf-8"))
    exit_code = _run(request, args.scenario)
    if args.scenario not in {"timeout", "timeout_with_child"}:
        result = _result(request, scenario=args.scenario)
        args.result.write_text(json.dumps(result, sort_keys=True), encoding="utf-8")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
