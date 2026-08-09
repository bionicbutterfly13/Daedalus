#!/usr/bin/env python3
"""Validate bounded synthetic Daedalus study and publication evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

EXPECTED_SCHEMAS = {
    "study-packet.json": "daedalus-mock-study-packet/v1",
    "authorization-record.json": "daedalus-mock-study-authorization/v1",
    "attempt-manifest.json": "daedalus-mock-study-attempt/v1",
    "status.json": "daedalus-mock-study-status/v1",
    "evidence-manifest.json": "daedalus-mock-study-evidence-manifest/v1",
    "daedalus-primary-study-report.json": "daedalus-primary-study-report/v1",
    "archimedes-independent-evidence-report.json": (
        "archimedes-independent-evidence-report/v1"
    ),
}
PACKET_FIELDS = {
    "packet_id",
    "synthetic_study",
    "objective",
    "research_question",
    "hypothesis",
    "input_inventory",
    "daedalus_interface",
    "source_identity",
    "workflow_stages",
    "expected_artifacts",
    "permitted_operations",
    "prohibited_operations",
    "provider_cost_boundary",
    "retention_transfer_publication",
    "retry_timeout_stop_policy",
    "acceptance_criteria",
    "public_journal",
}
PRIMARY_REPORT_FIELDS = {
    "research_question",
    "hypothesis",
    "synthetic_inputs",
    "methods",
    "workflow_stages_attempted",
    "analyses_performed",
    "outputs_produced",
    "measured_results",
    "failures_and_retries",
    "limitations",
    "unresolved_scientific_questions",
}
ARCHIMEDES_REPORT_FIELDS = {
    "actually_executed",
    "directly_verified_artifacts",
    "expected_outputs",
    "produced_outputs",
    "checksums_and_provenance",
    "missing_empty_stale_unlinked_evidence",
    "failures_retries_timing_stop_conditions",
    "concerns_about_daedalus",
    "blockers",
    "verdict",
    "verdict_reason",
}
ARTICLE_SECTION_FIELDS = {
    "research_question_and_selection_rationale",
    "daedalus_and_archimedes_roles",
    "study_design",
    "synthetic_inputs_and_methods",
    "what_actually_ran",
    "verified_outputs_and_results",
    "failures_retries_and_missing_evidence",
    "what_worked_and_did_not_work",
    "limitations",
    "concerns_about_daedalus",
    "needed_repairs_or_evaluations",
    "next_study_or_engineering_decision",
}
CLAIM_CLASSES = {
    "verified_execution",
    "observed_result",
    "supported_inference",
    "hypothesis",
    "unknown",
}
EXECUTION_EVIDENCE_CLASSES = {"verified_execution", "observed_result"}
STAGE_FRAGMENT_CONTRACTS = {
    "question_formulation": {"research_question"},
    "hypothesis_generation": {"hypothesis"},
    "method_selection": {"methods"},
    "synthetic_analysis": {"analyses_performed"},
    "result_interpretation": {"measured_results"},
    "primary_report": {"outputs_produced"},
}
FORBIDDEN_PUBLIC_CLASSES = {
    "credentials",
    "secrets",
    "private_memory",
    "private_research_data",
    "hidden_prompts",
    "unsafe_internal_paths",
    "sensitive_logs",
    "unsupported_claims",
    "full_validation_claims",
    "consciousness_claims",
}
STOP_ERROR_PREFIXES = (
    "authorization_exceeds_packet:",
    "privacy_violation",
    "study_execution_not_authorized",
    "unauthorized_action:",
)

SUPERVISED_LAYOUT = "supervised_attempt/v1"
SUPERVISOR_RUN_AUTHORITY = "archimedes_supervisor"
SUPERVISOR_CONTROL_ROLES = frozenset(
    {"native_event_stream", "terminal_status", "supervisor_evidence"}
)


class _StudyLayout:
    __slots__ = ("attempt_root", "control_root", "supervised", "workspace_root")

    def __init__(
        self,
        attempt_root: Path,
        control_root: Path,
        workspace_root: Path,
        supervised: bool,
    ) -> None:
        self.attempt_root = attempt_root
        self.control_root = control_root
        self.workspace_root = workspace_root
        self.supervised = supervised


def _resolve_layout(
    root: Path, errors: list[str], *, allow_legacy_fixture: bool
) -> _StudyLayout:
    control = root / "supervisor-evidence"
    workspace = root / "workspace"
    control_is_dir = control.is_dir()
    workspace_is_dir = workspace.is_dir()
    if control_is_dir or workspace_is_dir:
        if not control_is_dir:
            errors.append("supervised_control_root_missing")
        if not workspace_is_dir:
            errors.append("supervised_workspace_root_missing")
        if control.is_symlink():
            errors.append("unsafe_supervised_control_root")
            control = root / ".invalid-supervisor-evidence"
        if workspace.is_symlink():
            errors.append("unsafe_supervised_workspace_root")
            workspace = root / ".invalid-workspace"
        flat_control_names = {
            "study-packet.json",
            "authorization-record.json",
            "attempt-manifest.json",
            "status.json",
            "native-events.jsonl",
            "run-ledger.jsonl",
        }
        if any((root / name).exists() for name in flat_control_names):
            errors.append("ambiguous_study_layout")
        return _StudyLayout(root, control, workspace, True)
    if not allow_legacy_fixture:
        errors.append("supervised_layout_required")
    return _StudyLayout(root, root, root, False)


def _artifact_location(
    layout: _StudyLayout,
    value: Any,
    *,
    role: Any = None,
    producer: Any = None,
) -> tuple[str | None, Path | None]:
    relative = _safe_relative_path(value)
    if relative is None:
        return None, None
    if not layout.supervised:
        return _contained_path(layout.attempt_root, relative)
    base = (
        layout.control_root
        if role in SUPERVISOR_CONTROL_ROLES or producer != "daedalus"
        else layout.workspace_root
    )
    _, candidate = _contained_path(base, relative)
    return relative, candidate


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_sha256(value: Any) -> str:
    rendered = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(rendered).hexdigest()


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _safe_relative_path(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    return candidate.as_posix()


def _contained_path(root: Path, value: Any) -> tuple[str | None, Path | None]:
    relative = _safe_relative_path(value)
    if relative is None:
        return None, None
    candidate = root / relative
    try:
        candidate.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return relative, None
    if candidate.is_symlink():
        return relative, None
    return relative, candidate


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("top-level JSON value must be an object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError("JSONL entries must be objects")
        records.append(value)
    if not records:
        raise ValueError("JSONL evidence is empty")
    return records


def _load_named_json(root: Path, name: str, errors: list[str]) -> dict[str, Any]:
    path = root / name
    if not path.is_file():
        errors.append(f"missing_record:{name}")
        return {}
    if path.stat().st_size == 0:
        errors.append(f"empty_artifact:{name}")
        return {}
    try:
        value = _read_json(path)
    except (OSError, ValueError, json.JSONDecodeError):
        errors.append(f"invalid_json:{name}")
        return {}
    expected_schema = EXPECTED_SCHEMAS.get(name)
    if expected_schema is not None and value.get("schema") != expected_schema:
        errors.append(f"schema_mismatch:{name}")
    return value


def _require_fields(
    record: dict[str, Any], name: str, fields: set[str], errors: list[str]
) -> None:
    for field in sorted(fields):
        if field not in record or record[field] is None:
            errors.append(f"required_field_missing:{name}:{field}")


def _require_nonempty_fields(
    record: dict[str, Any], name: str, fields: set[str], errors: list[str]
) -> None:
    for field in sorted(fields):
        if record.get(field) in (None, "", [], {}):
            errors.append(f"required_field_empty:{name}:{field}")


def _check_identity(
    candidate: dict[str, Any],
    name: str,
    expected: dict[str, Any],
    errors: list[str],
) -> None:
    for field, expected_value in expected.items():
        if not expected_value or candidate.get(field) != expected_value:
            errors.append(f"{field}_mismatch:{name}")


def _normalize_expected_artifacts(raw: Any, errors: list[str]) -> list[dict[str, Any]]:
    if not isinstance(raw, list) or not raw:
        errors.append("invalid_expected_artifacts")
        return []
    normalized: list[dict[str, Any]] = []
    for position, entry in enumerate(raw, 1):
        if isinstance(entry, str):
            normalized.append({"path": entry, "required": True})
        elif isinstance(entry, dict) and entry.get("path"):
            normalized.append(entry)
        else:
            errors.append(f"invalid_expected_artifact_entry:{position}")
    return normalized


def _validate_input_inventory(packet: dict[str, Any], errors: list[str]) -> None:
    inventory = packet.get("input_inventory")
    if not isinstance(inventory, list) or not inventory:
        errors.append("invalid_input_inventory")
        return
    if len(inventory) != 1:
        errors.append(f"unsupported_input_inventory_count:{len(inventory)}")
    for position, item in enumerate(inventory, 1):
        if not isinstance(item, dict):
            errors.append(f"invalid_input_inventory_entry:{position}")
            continue
        content = item.get("content")
        digest = item.get("content_sha256")
        if content is None or not _is_sha256(digest):
            errors.append(f"invalid_input_identity:{position}")
            continue
        canonical = json.dumps(content, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
        if hashlib.sha256(canonical).hexdigest() != digest:
            errors.append(f"input_checksum_mismatch:{position}")


def _validate_supervised_attempt(
    layout: _StudyLayout,
    attempt: dict[str, Any],
    status: dict[str, Any],
    identities: dict[str, Any],
    errors: list[str],
) -> None:
    control = layout.control_root
    manifest_digest = attempt.get("manifest_sha256")
    manifest_payload = {
        key: value for key, value in attempt.items() if key != "manifest_sha256"
    }
    if (
        not _is_sha256(manifest_digest)
        or _json_sha256(manifest_payload) != manifest_digest
    ):
        errors.append("attempt_manifest_digest_mismatch")

    expected_input_files = {
        "packet": "study-packet.json",
        "authorization": "authorization-record.json",
        "allowlist": "execution-allowlist.json",
        "preflight": "preflight.json",
        "runtime_config": "supervisor-runtime.json",
        "prompt": "prompt.txt",
        "supervisor_source": "supervisor-source.py",
        "cycle_worker_source": "cycle-worker-source.py",
    }
    input_paths = attempt.get("input_paths")
    input_digests = attempt.get("input_sha256")
    if not isinstance(input_paths, dict) or set(input_paths) != set(
        expected_input_files
    ):
        errors.append("supervisor_input_paths_invalid")
        input_paths = {}
    if not isinstance(input_digests, dict) or set(input_digests) != set(
        expected_input_files
    ):
        errors.append("supervisor_input_digests_invalid")
        input_digests = {}
    for name, filename in expected_input_files.items():
        path_value = input_paths.get(name)
        try:
            path = Path(str(path_value)).resolve()
            path.relative_to(control.resolve())
        except (OSError, ValueError):
            errors.append(f"supervisor_input_path_unsafe:{name}")
            continue
        if (
            path != (control / filename).resolve()
            or path.is_symlink()
            or not path.is_file()
        ):
            errors.append(f"supervisor_input_path_mismatch:{name}")
            continue
        if input_digests.get(name) != _sha256(path):
            errors.append(f"supervisor_input_digest_mismatch:{name}")

    states_dir = control / "states"
    state_files = sorted(states_dir.glob("*.json")) if states_dir.is_dir() else []
    if not state_files:
        errors.append("supervisor_state_chain_missing")
        return
    previous_state_digest: str | None = None
    states: list[dict[str, Any]] = []
    for sequence, path in enumerate(state_files, 1):
        try:
            state = _read_json(path)
        except (OSError, ValueError, json.JSONDecodeError):
            errors.append(f"supervisor_state_invalid:{sequence}")
            continue
        payload = {key: value for key, value in state.items() if key != "state_sha256"}
        if path.name != f"{sequence:06d}.json" or state.get("sequence") != sequence:
            errors.append(f"supervisor_state_sequence_invalid:{sequence}")
        if state.get("schema") != "daedalus-supervisor-state/v1":
            errors.append(f"supervisor_state_schema_mismatch:{sequence}")
        if state.get("previous_state_sha256") != previous_state_digest:
            errors.append(f"supervisor_state_chain_mismatch:{sequence}")
        if state.get("manifest_sha256") != manifest_digest:
            errors.append(f"supervisor_state_manifest_mismatch:{sequence}")
        state_digest = state.get("state_sha256")
        if not _is_sha256(state_digest) or _json_sha256(payload) != state_digest:
            errors.append(f"supervisor_state_digest_mismatch:{sequence}")
        for field, expected in (
            ("packet_id", identities["packet_id"]),
            ("attempt_id", identities["attempt_id"]),
            ("supervisor_run_id", identities["run_id"]),
            ("thread_id", identities["thread_id"]),
        ):
            if state.get(field) != expected:
                errors.append(f"supervisor_state_{field}_mismatch:{sequence}")
        previous_state_digest = state_digest if isinstance(state_digest, str) else None
        states.append(state)
    if not states:
        return
    terminal = states[-1]
    if status.get("state_sha256") != terminal.get("state_sha256"):
        errors.append("supervisor_status_state_mismatch")
    for field in (
        "outcome",
        "exit_code",
        "terminal_event_observed",
        "monotonic_started_seconds",
        "monotonic_finished_seconds",
    ):
        if status.get(field) != terminal.get(field):
            errors.append(f"supervisor_terminal_{field}_mismatch")

    cycles_dir = control / "cycles"
    request_files = (
        sorted(cycles_dir.glob("cycle-request-*.json")) if cycles_dir.is_dir() else []
    )
    if not request_files:
        errors.append("supervisor_cycle_history_missing")
        return
    if terminal.get("cycle_count") != len(request_files):
        errors.append("supervisor_cycle_count_mismatch")
    stdout_parts: list[bytes] = []
    stderr_parts: list[bytes] = []
    approved_digests: set[str] = set()
    for sequence, request_path in enumerate(request_files, 1):
        expected_request_name = f"cycle-request-{sequence:03d}.json"
        if request_path.name != expected_request_name:
            errors.append(f"supervisor_cycle_sequence_invalid:{sequence}")
        try:
            request = _read_json(request_path)
        except (OSError, ValueError, json.JSONDecodeError):
            errors.append(f"supervisor_cycle_request_invalid:{sequence}")
            continue
        request_payload = {
            key: value for key, value in request.items() if key != "request_sha256"
        }
        if request.get("schema") != "daedalus-supervisor-cycle-request/v1":
            errors.append(f"supervisor_cycle_request_schema_mismatch:{sequence}")
        if request.get("request_sha256") != _json_sha256(request_payload):
            errors.append(f"supervisor_cycle_request_digest_mismatch:{sequence}")
        expected_mode = "start" if sequence == 1 else "resume"
        if request.get("mode") != expected_mode:
            errors.append(f"supervisor_cycle_mode_mismatch:{sequence}")
        for field, expected in (
            ("packet_id", identities["packet_id"]),
            ("attempt_id", identities["attempt_id"]),
            ("supervisor_run_id", identities["run_id"]),
            ("thread_id", identities["thread_id"]),
            ("cycle_id", f"cycle-{sequence:03d}"),
        ):
            if request.get(field) != expected:
                errors.append(f"supervisor_cycle_{field}_mismatch:{sequence}")
        if request.get("native_run_id") is not None:
            errors.append(f"supervisor_cycle_invented_native_run_id:{sequence}")
        try:
            request_workdir = Path(str(request.get("workdir", ""))).resolve()
        except (OSError, ValueError):
            request_workdir = Path()
        if request_workdir != layout.workspace_root.resolve():
            errors.append(f"supervisor_cycle_workdir_mismatch:{sequence}")

        if sequence == 1:
            if (
                not isinstance(request.get("prompt"), str)
                or not request["prompt"].strip()
            ):
                errors.append("supervisor_start_prompt_missing")
            if request.get("resume_payload") is not None:
                errors.append("supervisor_start_resume_payload_present")
        else:
            approved = request.get("approved_request_digest")
            if not _is_sha256(approved) or approved in approved_digests:
                errors.append(f"supervisor_resume_approval_invalid:{sequence}")
            elif isinstance(approved, str):
                approved_digests.add(approved)
            if (
                not isinstance(request.get("resume_payload"), dict)
                or not request["resume_payload"]
            ):
                errors.append(f"supervisor_resume_payload_missing:{sequence}")
            pending_path = control / "decisions" / f"pending-{sequence - 1:03d}.json"
            try:
                pending = _read_json(pending_path)
            except (OSError, ValueError, json.JSONDecodeError):
                errors.append(f"supervisor_pending_record_missing:{sequence - 1}")
                pending = {}
            pending_payload = pending.get("payload")
            if pending.get("schema") != "daedalus-supervisor-pending-decision/v1":
                errors.append(f"supervisor_pending_schema_mismatch:{sequence - 1}")
            if not isinstance(pending_payload, dict) or pending.get(
                "request_digest"
            ) != _json_sha256(pending_payload):
                errors.append(f"supervisor_pending_digest_mismatch:{sequence - 1}")
            if pending.get("request_digest") != approved:
                errors.append(f"supervisor_pending_approval_mismatch:{sequence - 1}")
            for field, expected in (
                ("attempt_id", identities["attempt_id"]),
                ("supervisor_run_id", identities["run_id"]),
                ("thread_id", identities["thread_id"]),
                ("cycle_id", f"cycle-{sequence - 1:03d}"),
            ):
                if pending.get(field) != expected:
                    errors.append(f"supervisor_pending_{field}_mismatch:{sequence - 1}")
            if isinstance(pending_payload, dict) and pending.get(
                "interrupt_id"
            ) != pending_payload.get("interrupt_id"):
                errors.append(
                    f"supervisor_pending_interrupt_id_mismatch:{sequence - 1}"
                )
            decision_path = control / "decisions" / f"decision-{sequence - 1:03d}.json"
            try:
                decision = _read_json(decision_path)
            except (OSError, ValueError, json.JSONDecodeError):
                errors.append(f"supervisor_resume_decision_missing:{sequence}")
                decision = {}
            if decision.get("schema") != "daedalus-supervisor-decision/v1":
                errors.append(f"supervisor_decision_schema_mismatch:{sequence}")
            if decision.get("request_digest") != approved:
                errors.append(f"supervisor_resume_decision_mismatch:{sequence}")
            if decision.get("decision") not in {"approve", "answer"}:
                errors.append(f"supervisor_resume_not_approved:{sequence}")
            for field, expected in (
                ("attempt_id", identities["attempt_id"]),
                ("supervisor_run_id", identities["run_id"]),
                ("thread_id", identities["thread_id"]),
            ):
                if decision.get(field) != expected:
                    errors.append(f"supervisor_decision_{field}_mismatch:{sequence}")
            resume_payload = request.get("resume_payload")
            if decision.get("decision") == "approve":
                actions = (
                    pending_payload.get("action_requests")
                    if isinstance(pending_payload, dict)
                    else None
                )
                expected_resume = (
                    {"decisions": [{"type": "approve"} for _ in actions]}
                    if isinstance(actions, list) and actions
                    else None
                )
                if (
                    pending.get("kind") != "tool_approval"
                    or resume_payload != expected_resume
                ):
                    errors.append(f"supervisor_resume_payload_mismatch:{sequence}")
            elif decision.get("decision") == "answer":
                expected_resume = {
                    "answers": decision.get("answers"),
                    "status": "answered",
                }
                if (
                    pending.get("kind") != "ask_user"
                    or resume_payload != expected_resume
                ):
                    errors.append(f"supervisor_resume_payload_mismatch:{sequence}")

        stdout_path = cycles_dir / f"native-events-{sequence:03d}.jsonl"
        stderr_path = cycles_dir / f"stderr-{sequence:03d}.log"
        result_path = cycles_dir / f"worker-result-{sequence:03d}.json"
        if not stdout_path.is_file() or not stderr_path.is_file():
            errors.append(f"supervisor_cycle_capture_missing:{sequence}")
            continue
        stdout = stdout_path.read_bytes()
        stderr = stderr_path.read_bytes()
        stdout_parts.append(stdout)
        stderr_parts.append(stderr)
        try:
            cycle_events = _read_jsonl(stdout_path)
        except (OSError, ValueError, json.JSONDecodeError):
            errors.append(f"supervisor_cycle_events_invalid:{sequence}")
            cycle_events = []
        if not cycle_events or cycle_events[-1].get("type") != "done":
            errors.append(f"supervisor_cycle_terminal_event_missing:{sequence}")
        try:
            worker_result = _read_json(result_path)
        except (OSError, ValueError, json.JSONDecodeError):
            errors.append(f"supervisor_worker_result_missing:{sequence}")
            worker_result = {}
        if worker_result.get("schema") != "daedalus-supervisor-worker-result/v1":
            errors.append(f"supervisor_worker_result_schema_mismatch:{sequence}")
        for field, expected in (
            ("attempt_id", identities["attempt_id"]),
            ("supervisor_run_id", identities["run_id"]),
            ("thread_id", identities["thread_id"]),
            ("cycle_id", f"cycle-{sequence:03d}"),
            ("request_sha256", request.get("request_sha256")),
        ):
            if worker_result.get(field) != expected:
                errors.append(f"supervisor_worker_{field}_mismatch:{sequence}")
        if sequence > 1 and worker_result.get("approved_request_digest") != request.get(
            "approved_request_digest"
        ):
            errors.append(f"supervisor_worker_approval_mismatch:{sequence}")

    aggregate_stdout = control / "native-events.jsonl"
    aggregate_stderr = control / "stderr.log"
    if aggregate_stdout.is_file() and aggregate_stdout.read_bytes() != b"".join(
        stdout_parts
    ):
        errors.append("supervisor_native_event_aggregate_mismatch")
    if aggregate_stderr.is_file() and aggregate_stderr.read_bytes() != b"".join(
        stderr_parts
    ):
        errors.append("supervisor_stderr_aggregate_mismatch")


def _final_verdict(report_verdict: Any, errors: list[str]) -> str:
    if not errors:
        return (
            report_verdict
            if report_verdict in {"accepted", "partial", "failed", "stopped"}
            else "failed"
        )
    if report_verdict == "stopped" or any(
        error.startswith(STOP_ERROR_PREFIXES) for error in errors
    ):
        return "stopped"
    if report_verdict == "partial" or any(
        error.startswith("accepted_with_incomplete_stage_coverage:") for error in errors
    ):
        return "partial"
    return "failed"


def validate_study(
    run_dir: str | Path, *, allow_legacy_fixture: bool = False
) -> dict[str, Any]:
    """Return a deterministic fail-closed study validation result."""
    root = Path(run_dir)
    errors: list[str] = []
    if root.is_symlink():
        return {"valid": False, "verdict": "failed", "errors": ["unsafe_run_dir"]}
    if not root.is_dir():
        return {"valid": False, "verdict": "failed", "errors": ["run_dir_missing"]}

    layout = _resolve_layout(root, errors, allow_legacy_fixture=allow_legacy_fixture)
    if any(error.startswith("unsafe_supervised_") for error in errors):
        return {"valid": False, "verdict": "failed", "errors": errors}
    control_root = layout.control_root
    workspace_root = layout.workspace_root
    packet = _load_named_json(control_root, "study-packet.json", errors)
    authorization = _load_named_json(control_root, "authorization-record.json", errors)
    attempt = _load_named_json(control_root, "attempt-manifest.json", errors)
    status = _load_named_json(control_root, "status.json", errors)
    evidence = _load_named_json(control_root, "evidence-manifest.json", errors)
    primary = _load_named_json(
        workspace_root, "daedalus-primary-study-report.json", errors
    )
    report = _load_named_json(
        control_root, "archimedes-independent-evidence-report.json", errors
    )

    if layout.supervised and evidence.get("layout") != SUPERVISED_LAYOUT:
        errors.append("supervised_layout_marker_missing")

    _require_fields(packet, "study-packet.json", PACKET_FIELDS, errors)
    _require_fields(
        authorization,
        "authorization-record.json",
        {
            "packet_id",
            "study_execution_authorized",
            "tool_action_approval_policy",
            "tool_action_preapproval_authorized",
            "paid_provider_activation_authorized",
            "private_memory_access_authorized",
            "private_research_data_access_authorized",
            "artifact_transfer_authorized",
            "publication_authorized",
            "evoscientist_core_modification_authorized",
        },
        errors,
    )
    if "approval_evidence" not in authorization:
        errors.append(
            "required_field_missing:authorization-record.json:approval_evidence"
        )
    attempt_fields = {
        "packet_id",
        "attempt_id",
        "run_id",
        "thread_id",
        "source_commit",
        "imported_package_path",
        "workdir_kind",
        "native_events_path",
        "stderr_path",
        "status_path",
        "monotonic_started_seconds",
    }
    if layout.supervised:
        attempt_fields.update(
            {
                "run_id_authority",
                "supervisor_run_id",
                "native_run_id_status",
                "thread_id_authority",
                "workdir",
                "manifest_sha256",
                "input_paths",
                "input_sha256",
                "supervisor_source_path",
                "execution_mode",
                "evidence_ceiling",
            }
        )
        for field in (
            "native_run_id",
            "monotonic_finished_seconds",
            "exit_code",
            "terminal_event_observed",
        ):
            if field not in attempt:
                errors.append(f"required_field_missing:attempt-manifest.json:{field}")
    else:
        attempt_fields.update(
            {
                "monotonic_finished_seconds",
                "exit_code",
                "terminal_event_observed",
            }
        )
    _require_fields(attempt, "attempt-manifest.json", attempt_fields, errors)
    if layout.supervised:
        execution_mode = attempt.get("execution_mode")
        evidence_ceiling = attempt.get("evidence_ceiling")
        report_ceiling = report.get("evidence_ceiling")
        if execution_mode == "deterministic_adapter":
            if evidence_ceiling != "E2" or report_ceiling != "E2":
                errors.append("adapter_evidence_overclaim")
        elif execution_mode == "production":
            if evidence_ceiling != "E3" or report_ceiling != "E3":
                errors.append("production_evidence_class_mismatch")
        else:
            errors.append("supervisor_execution_mode_invalid")
    _require_fields(
        status,
        "status.json",
        {
            "packet_id",
            "attempt_id",
            "run_id",
            "thread_id",
            "exit_code",
            "terminal_event_observed",
            "declared_success",
        },
        errors,
    )
    _require_fields(
        evidence,
        "evidence-manifest.json",
        {"packet_id", "attempt_id", "run_id", "thread_id", "artifacts"},
        errors,
    )
    _require_fields(
        primary, "daedalus-primary-study-report.json", PRIMARY_REPORT_FIELDS, errors
    )
    _require_fields(
        report,
        "archimedes-independent-evidence-report.json",
        ARCHIMEDES_REPORT_FIELDS,
        errors,
    )
    _require_nonempty_fields(
        primary,
        "daedalus-primary-study-report.json",
        {
            "research_question",
            "hypothesis",
            "synthetic_inputs",
            "methods",
            "workflow_stages_attempted",
            "analyses_performed",
            "outputs_produced",
            "measured_results",
            "limitations",
        },
        errors,
    )
    if report.get("verdict") == "accepted":
        _require_nonempty_fields(
            report,
            "archimedes-independent-evidence-report.json",
            {
                "actually_executed",
                "directly_verified_artifacts",
                "checksums_and_provenance",
                "failures_retries_timing_stop_conditions",
                "verdict_reason",
            },
            errors,
        )

    if packet.get("synthetic_study") is not True:
        errors.append("study_not_synthetic")
    _validate_input_inventory(packet, errors)

    if authorization.get("study_execution_authorized") is not True:
        errors.append("study_execution_not_authorized")
    approval_evidence = authorization.get("approval_evidence")
    if authorization.get("study_execution_authorized") is True and (
        not isinstance(approval_evidence, str) or not approval_evidence.strip()
    ):
        errors.append("study_execution_approval_evidence_missing")
    if (
        authorization.get("tool_action_approval_policy")
        != "separate_per_interrupt_exact_digest"
        or authorization.get("tool_action_preapproval_authorized") is not False
    ):
        errors.append("tool_action_human_gate_invalid")
    if authorization.get("evoscientist_core_modification_authorized") is not False:
        errors.append(
            "authorization_exceeds_packet:evoscientist_core_modification_authorized"
        )
    provider_boundary = packet.get("provider_cost_boundary")
    if not isinstance(provider_boundary, dict):
        errors.append("invalid_provider_cost_boundary")
        provider_boundary = {}
    retention_boundary = packet.get("retention_transfer_publication")
    if not isinstance(retention_boundary, dict):
        errors.append("invalid_retention_transfer_publication")
        retention_boundary = {}
    prohibited_operations = packet.get("prohibited_operations")
    if not isinstance(prohibited_operations, list) or not all(
        isinstance(value, str) for value in prohibited_operations
    ):
        errors.append("invalid_prohibited_operations")
        prohibited_operations = []
    acceptance_criteria = packet.get("acceptance_criteria")
    if not isinstance(acceptance_criteria, dict):
        errors.append("invalid_acceptance_criteria")
        acceptance_criteria = {}
    frozen_authorizations = {
        "paid_provider_activation_authorized": provider_boundary.get(
            "paid_providers_authorized"
        ),
        "artifact_transfer_authorized": retention_boundary.get(
            "artifact_transfer_authorized"
        ),
        "publication_authorized": retention_boundary.get("publication_authorized"),
        "private_memory_access_authorized": (
            "access_private_memory" not in prohibited_operations
        ),
        "private_research_data_access_authorized": (
            "access_private_research_data" not in prohibited_operations
        ),
    }
    for field, frozen_value in frozen_authorizations.items():
        actual_value = authorization.get(field)
        if actual_value is True and frozen_value is not True:
            errors.append(f"authorization_exceeds_packet:{field}")
        elif (
            not isinstance(actual_value, bool)
            or not isinstance(frozen_value, bool)
            or actual_value is not frozen_value
        ):
            errors.append(f"authorization_boundary_mismatch:{field}")

    source_identity = packet.get("source_identity")
    if not isinstance(source_identity, dict):
        source_identity = {}
    if attempt.get("source_commit") != source_identity.get("expected_commit"):
        errors.append("source_commit_mismatch:attempt-manifest.json")
    if attempt.get("imported_package_path") != source_identity.get(
        "expected_import_root"
    ):
        errors.append("imported_package_path_mismatch:attempt-manifest.json")
    if attempt.get("workdir_kind") != "data_only":
        errors.append("workdir_not_data_only")
    if layout.supervised:
        try:
            recorded_workdir = Path(str(attempt.get("workdir", ""))).resolve()
        except (OSError, ValueError):
            recorded_workdir = Path()
        if recorded_workdir != workspace_root.resolve():
            errors.append("supervised_workdir_mismatch")
    expected_capture_paths = {
        "native_events_path": "native-events.jsonl",
        "stderr_path": "stderr.log",
        "status_path": "status.json",
    }
    capture_values = [attempt.get(field) for field in expected_capture_paths]
    if len({value for value in capture_values if isinstance(value, str)}) != 3:
        errors.append("attempt_capture_paths_not_unique")
    for field, expected_path in expected_capture_paths.items():
        if attempt.get(field) != expected_path:
            errors.append(f"attempt_capture_path_mismatch:{field}")
        relative, capture_path = _contained_path(control_root, attempt.get(field))
        if relative is None or capture_path is None or not capture_path.is_file():
            errors.append(f"attempt_capture_path_unresolved:{field}")
    started = attempt.get("monotonic_started_seconds")
    finished = (
        status.get("monotonic_finished_seconds")
        if layout.supervised
        else attempt.get("monotonic_finished_seconds")
    )
    if (
        not isinstance(started, (int, float))
        or not isinstance(finished, (int, float))
        or finished < started
    ):
        errors.append("attempt_timing_invalid")
    if layout.supervised:
        if status.get("monotonic_started_seconds") != started:
            errors.append("attempt_status_start_time_mismatch")
        if (
            attempt.get("monotonic_finished_seconds") is not None
            or attempt.get("exit_code") is not None
            or attempt.get("terminal_event_observed") is not False
        ):
            errors.append("immutable_attempt_terminal_fields_modified")
        if attempt.get("run_id_authority") != SUPERVISOR_RUN_AUTHORITY:
            errors.append("supervisor_run_authority_mismatch")
        if attempt.get("run_id") != attempt.get("supervisor_run_id"):
            errors.append("supervisor_run_id_mismatch")
        if attempt.get("native_run_id") is not None:
            errors.append("invented_native_run_id")
        if attempt.get("native_run_id_status") != "not_exposed_by_local_stream_gateway":
            errors.append("native_run_id_status_mismatch")
        if attempt.get("thread_id_authority") != "exact_local_gateway_run_request":
            errors.append("thread_id_authority_mismatch")
        for field in (
            "run_id_authority",
            "supervisor_run_id",
            "native_run_id",
            "native_run_id_status",
        ):
            if status.get(field) != attempt.get(field):
                errors.append(f"attempt_status_{field}_mismatch")

    identities = {
        "packet_id": packet.get("packet_id"),
        "attempt_id": attempt.get("attempt_id"),
        "run_id": attempt.get("run_id"),
        "thread_id": attempt.get("thread_id"),
    }
    if layout.supervised:
        _validate_supervised_attempt(layout, attempt, status, identities, errors)
    _check_identity(
        authorization,
        "authorization-record.json",
        {"packet_id": identities["packet_id"]},
        errors,
    )
    for name, value in (
        ("status.json", status),
        ("evidence-manifest.json", evidence),
        ("daedalus-primary-study-report.json", primary),
        ("archimedes-independent-evidence-report.json", report),
    ):
        _check_identity(value, name, identities, errors)

    expected_artifacts = _normalize_expected_artifacts(
        packet.get("expected_artifacts"), errors
    )
    required_paths: list[str] = []
    for expected in expected_artifacts:
        if expected.get("required", True) is not True:
            continue
        relative, artifact_path = _artifact_location(
            layout,
            expected.get("path"),
            role=expected.get("role"),
            producer=expected.get("producer"),
        )
        if relative is None:
            errors.append("invalid_expected_artifact_path")
            continue
        required_paths.append(relative)
        if artifact_path is None:
            errors.append(f"unsafe_artifact_path:{relative}")
        elif not artifact_path.is_file():
            errors.append(f"missing_artifact:{relative}")
        elif artifact_path.stat().st_size == 0:
            errors.append(f"empty_artifact:{relative}")

    manifest_entries = evidence.get("artifacts")
    if not isinstance(manifest_entries, list) or not manifest_entries:
        errors.append("invalid_evidence_manifest_artifacts")
        manifest_entries = []
    manifest_by_path: dict[str, list[dict[str, Any]]] = {}
    for position, artifact in enumerate(manifest_entries, 1):
        if not isinstance(artifact, dict):
            errors.append(f"invalid_artifact_entry:{position}")
            continue
        for field in (
            "path",
            "role",
            "producer",
            "attempt_id",
            "stage",
            "byte_size",
            "sha256",
            "verification_status",
        ):
            if field not in artifact or artifact[field] is None:
                errors.append(f"artifact_field_missing:{position}:{field}")
        relative, artifact_path = _artifact_location(
            layout,
            artifact.get("path"),
            role=artifact.get("role"),
            producer=artifact.get("producer"),
        )
        if relative is None:
            errors.append("invalid_manifest_artifact_path")
            continue
        if artifact_path is None:
            errors.append(f"unsafe_artifact_path:{relative}")
            continue
        manifest_by_path.setdefault(relative, []).append(artifact)
        if artifact.get("verification_status") != "directly_verified":
            errors.append(f"artifact_not_directly_verified:{relative}")
        if artifact.get("attempt_id") != identities["attempt_id"]:
            errors.append(f"artifact_attempt_id_mismatch:{relative}")
        if not _is_sha256(artifact.get("sha256")):
            errors.append(f"artifact_checksum_invalid:{relative}")
        if not artifact_path.is_file():
            errors.append(f"missing_artifact:{relative}")
            continue
        if artifact_path.stat().st_size == 0:
            errors.append(f"empty_artifact:{relative}")
            continue
        if artifact.get("byte_size") != artifact_path.stat().st_size:
            errors.append(f"size_mismatch:{relative}")
        if artifact.get("sha256") != _sha256(artifact_path):
            errors.append(f"checksum_mismatch:{relative}")

    for relative in required_paths:
        if relative not in manifest_by_path:
            errors.append(f"expected_artifact_unmanifested:{relative}")
            errors.append(f"unlinked_artifact:{relative}")
    for expected in expected_artifacts:
        relative = _safe_relative_path(expected.get("path"))
        if relative is None or relative not in manifest_by_path:
            continue
        for field in ("role", "producer", "stage"):
            expected_value = expected.get(field)
            if not expected_value:
                errors.append(f"expected_artifact_field_missing:{relative}:{field}")
                continue
            if any(
                entry.get(field) != expected_value
                for entry in manifest_by_path[relative]
            ):
                errors.append(f"artifact_{field}_mismatch:{relative}")
    for relative, entries in manifest_by_path.items():
        attempts = {entry.get("attempt_id") for entry in entries}
        if len(entries) > 1:
            errors.append(f"duplicate_manifest_artifact:{relative}")
        if len(entries) > 1 and len(attempts) > 1:
            errors.append(f"retry_overwrite:{relative}")

    if primary.get("author") != "Daedalus":
        errors.append("primary_report_wrong_author")
    if report.get("author") != "Archimedes":
        errors.append("independent_report_wrong_author")
    if primary.get("research_question") != packet.get("research_question"):
        errors.append("primary_report_question_mismatch")
    if primary.get("hypothesis") != packet.get("hypothesis"):
        errors.append("primary_report_hypothesis_mismatch")
    report_verdict = report.get("verdict")
    if not isinstance(report_verdict, str) or report_verdict not in {
        "accepted",
        "partial",
        "failed",
        "stopped",
    }:
        errors.append("invalid_independent_verdict")
    if report_verdict == "accepted":
        if report.get("missing_empty_stale_unlinked_evidence") != []:
            errors.append("accepted_with_missing_or_defective_evidence")
        if report.get("blockers") != []:
            errors.append("accepted_with_blockers")

    packet_inputs = packet.get("input_inventory")
    frozen_content = (
        packet_inputs[0].get("content")
        if isinstance(packet_inputs, list)
        and packet_inputs
        and isinstance(packet_inputs[0], dict)
        else None
    )
    if primary.get("synthetic_inputs") != frozen_content:
        errors.append("primary_inputs_mismatch:frozen_packet")
    control = (
        frozen_content.get("control") if isinstance(frozen_content, dict) else None
    )
    treatment = (
        frozen_content.get("treatment") if isinstance(frozen_content, dict) else None
    )
    if (
        isinstance(control, list)
        and control
        and isinstance(treatment, list)
        and treatment
        and all(
            isinstance(value, (int, float)) and not isinstance(value, bool)
            for value in control + treatment
        )
    ):
        expected_results = {
            "control_mean": sum(control) / len(control),
            "treatment_mean": sum(treatment) / len(treatment),
        }
        expected_results["difference"] = (
            expected_results["treatment_mean"] - expected_results["control_mean"]
        )
        measured = primary.get("measured_results")
        for key, expected_value in expected_results.items():
            actual_value = measured.get(key) if isinstance(measured, dict) else None
            if actual_value != expected_value:
                errors.append(f"measured_result_mismatch:{key}")

    try:
        events = _read_jsonl(control_root / "native-events.jsonl")
    except (OSError, ValueError, json.JSONDecodeError):
        events = []
        errors.append("invalid_native_events")
    for position, event in enumerate(events, 1):
        if layout.supervised:
            if not isinstance(event.get("type"), str) or not event["type"]:
                errors.append(f"native_event_type_missing:{position}")
        else:
            _check_identity(
                event, f"native-events.jsonl:{position}", identities, errors
            )
            for field in ("event_id", "stage", "event_type", "output_ref"):
                if not event.get(field):
                    errors.append(f"native_event_field_missing:{position}:{field}")
            output_ref = event.get("output_ref")
            if output_ref:
                output_path_text = str(output_ref).split("#", 1)[0]
                relative, output_path = _contained_path(root, output_path_text)
                if relative is None or output_path is None or not output_path.is_file():
                    errors.append(f"native_output_ref_unresolved:{position}")
    if layout.supervised and (not events or events[-1].get("type") != "done"):
        errors.append("supervised_native_terminal_event_missing")

    try:
        ledger = _read_jsonl(control_root / "run-ledger.jsonl")
    except (OSError, ValueError, json.JSONDecodeError):
        ledger = []
        errors.append("invalid_run_ledger")
    previous_sequence = 0
    previous_record_digest: str | None = None
    allowed_ledger_types = {
        "operator_action",
        "daedalus_event",
        "failure",
        "retry",
        "verification",
    }
    if layout.supervised:
        allowed_ledger_types.update(
            {"preflight", "approval_request", "operator_decision", "terminal"}
        )
    for position, entry in enumerate(ledger, 1):
        for field in (
            "sequence",
            "timestamp",
            "entry_type",
            "attempt_id",
            "stage",
            "source",
            "evidence_ref",
        ):
            if not entry.get(field):
                errors.append(f"run_ledger_field_missing:{position}:{field}")
        sequence = entry.get("sequence")
        if not isinstance(sequence, int) or sequence <= previous_sequence:
            errors.append(f"run_ledger_sequence_invalid:{position}")
        elif isinstance(sequence, int):
            previous_sequence = sequence
        if layout.supervised:
            payload = {
                key: value for key, value in entry.items() if key != "record_sha256"
            }
            if entry.get("schema") != "daedalus-supervisor-ledger-entry/v1":
                errors.append(f"supervisor_ledger_schema_mismatch:{position}")
            if entry.get("previous_record_sha256") != previous_record_digest:
                errors.append(f"supervisor_ledger_chain_mismatch:{position}")
            record_digest = entry.get("record_sha256")
            if not _is_sha256(record_digest) or _json_sha256(payload) != record_digest:
                errors.append(f"supervisor_ledger_digest_mismatch:{position}")
            previous_record_digest = (
                record_digest if isinstance(record_digest, str) else None
            )
        if entry.get("attempt_id") != identities["attempt_id"]:
            errors.append(f"attempt_id_mismatch:run-ledger.jsonl:{position}")
        if entry.get("entry_type") not in allowed_ledger_types:
            errors.append(f"run_ledger_entry_type_invalid:{position}")
        evidence_ref = entry.get("evidence_ref")
        if evidence_ref:
            ledger_path_text = str(evidence_ref).split("#", 1)[0]
            relative, ledger_path = _contained_path(control_root, ledger_path_text)
            if relative is None or ledger_path is None or not ledger_path.is_file():
                errors.append(f"run_ledger_evidence_ref_unresolved:{position}")
        if entry.get("privacy_violation") is True:
            errors.append("privacy_violation")
        action = entry.get("action")
        if action and (
            entry.get("authorized") is not True or action in prohibited_operations
        ):
            errors.append(f"unauthorized_action:{action}")

    expected_stages = packet.get("workflow_stages")
    if (
        not isinstance(expected_stages, list)
        or not expected_stages
        or not all(isinstance(stage, str) and stage for stage in expected_stages)
    ):
        errors.append("invalid_workflow_stages")
        expected_stages = []
    stage_evidence = report.get("workflow_stage_evidence")
    observed_stages: set[str]
    if layout.supervised:
        if not isinstance(stage_evidence, dict):
            errors.append(
                "required_field_missing:archimedes-independent-evidence-report.json:workflow_stage_evidence"
            )
            stage_evidence = {}
        observed_stages = set()
        used_stage_refs: dict[tuple[str, str], str] = {}
        expected_by_path = {
            _safe_relative_path(item.get("path")): item
            for item in expected_artifacts
            if _safe_relative_path(item.get("path")) is not None
        }
        for stage, entries in stage_evidence.items():
            if (
                not isinstance(stage, str)
                or not isinstance(entries, list)
                or not entries
            ):
                errors.append(f"invalid_stage_evidence:{stage}")
                continue
            valid_stage = True
            allowed_fragments = STAGE_FRAGMENT_CONTRACTS.get(stage)
            if stage not in expected_stages:
                errors.append(f"unexpected_stage_evidence:{stage}")
                valid_stage = False
            if allowed_fragments is None:
                errors.append(f"stage_evidence_contract_unknown:{stage}")
                valid_stage = False
            for position, item in enumerate(entries, 1):
                if not isinstance(item, dict):
                    errors.append(f"invalid_stage_evidence:{stage}:{position}")
                    valid_stage = False
                    continue
                evidence_ref = item.get("evidence_ref")
                evidence_class = item.get("evidence_class")
                if evidence_class not in CLAIM_CLASSES:
                    errors.append(f"invalid_stage_evidence_class:{stage}:{position}")
                    valid_stage = False
                elif evidence_class not in EXECUTION_EVIDENCE_CLASSES:
                    errors.append(
                        f"stage_evidence_class_insufficient:{stage}:{position}"
                    )
                    valid_stage = False
                if not isinstance(evidence_ref, str) or not evidence_ref:
                    errors.append(f"stage_evidence_ref_missing:{stage}:{position}")
                    valid_stage = False
                    continue
                ref_path, _, fragment = evidence_ref.partition("#")
                expected = expected_by_path.get(_safe_relative_path(ref_path))
                if expected is None:
                    errors.append(f"stage_evidence_ref_unmanifested:{stage}:{position}")
                    valid_stage = False
                    continue
                if expected.get("role") != "primary_study_report":
                    errors.append(
                        f"stage_evidence_artifact_role_mismatch:{stage}:{position}"
                    )
                    valid_stage = False
                relative, physical = _artifact_location(
                    layout,
                    ref_path,
                    role=expected.get("role"),
                    producer=expected.get("producer"),
                )
                if relative is None or physical is None or not physical.is_file():
                    errors.append(f"stage_evidence_ref_unresolved:{stage}:{position}")
                    valid_stage = False
                    continue
                if fragment and physical.suffix == ".json":
                    try:
                        referenced = _read_json(physical)
                    except (OSError, ValueError, json.JSONDecodeError):
                        referenced = {}
                    if fragment not in referenced:
                        errors.append(
                            f"stage_evidence_fragment_unresolved:{stage}:{position}"
                        )
                        valid_stage = False
                if not fragment or (
                    allowed_fragments is not None and fragment not in allowed_fragments
                ):
                    errors.append(
                        f"stage_evidence_fragment_mismatch:{stage}:{position}"
                    )
                    valid_stage = False
                ref_identity = (_safe_relative_path(ref_path) or "", fragment)
                prior_stage = used_stage_refs.get(ref_identity)
                if prior_stage is not None and prior_stage != stage:
                    errors.append(
                        f"stage_evidence_reused:{stage}:{position}:{prior_stage}"
                    )
                    valid_stage = False
                else:
                    used_stage_refs[ref_identity] = stage
            if valid_stage:
                observed_stages.add(stage)
    else:
        observed_stages = {
            entry.get("stage")
            for entry in events
            if isinstance(entry.get("stage"), str)
        }
    for stage in expected_stages:
        if stage not in observed_stages and report_verdict == "accepted":
            errors.append(f"accepted_with_incomplete_stage_coverage:{stage}")
    if report_verdict == "accepted":
        primary_stages = primary.get("workflow_stages_attempted")
        report_stages = report.get("actually_executed")
        if (
            not isinstance(primary_stages, list)
            or not all(isinstance(stage, str) for stage in primary_stages)
            or set(primary_stages) != set(expected_stages)
        ):
            errors.append("primary_report_stage_inventory_mismatch")
        if (
            not isinstance(report_stages, list)
            or not all(isinstance(stage, str) for stage in report_stages)
            or set(report_stages) != set(expected_stages)
        ):
            errors.append("independent_report_stage_inventory_mismatch")

    directly_verified = report.get("directly_verified_artifacts")
    if (
        not isinstance(directly_verified, list)
        or not all(isinstance(path, str) for path in directly_verified)
        or set(directly_verified) != set(manifest_by_path)
    ):
        errors.append("independent_report_artifact_inventory_mismatch")

    expected_count = acceptance_criteria.get("expected_output_count")
    produced_count = report.get("produced_outputs")
    report_expected_count = report.get("expected_outputs")
    if (
        not isinstance(expected_count, int)
        or isinstance(expected_count, bool)
        or expected_count < 0
    ):
        errors.append("packet_expected_output_count_invalid")
    if (
        not isinstance(produced_count, int)
        or isinstance(produced_count, bool)
        or not isinstance(report_expected_count, int)
        or isinstance(report_expected_count, bool)
    ):
        errors.append("independent_report_output_count_invalid")
    if produced_count != expected_count:
        errors.append(f"output_count_mismatch:{produced_count}!={expected_count}")
    if report_expected_count != expected_count:
        errors.append("independent_report_expected_output_count_mismatch")
    primary_outputs = primary.get("outputs_produced")
    if isinstance(primary_outputs, list) and len(primary_outputs) != expected_count:
        errors.append("primary_report_output_count_mismatch")

    if status.get("exit_code") != 0 or status.get("declared_success") is not True:
        errors.append("terminal_status_failed")
    if status.get("terminal_event_observed") is not True:
        errors.append("terminal_event_missing")
    if not layout.supervised:
        if attempt.get("exit_code") != status.get("exit_code"):
            errors.append("attempt_status_exit_code_mismatch")
        if attempt.get("terminal_event_observed") != status.get(
            "terminal_event_observed"
        ):
            errors.append("attempt_status_terminal_event_mismatch")
    if status.get("declared_success") is True:
        if status.get("terminal_event_observed") is not True:
            errors.append("silent_success:terminal_event_missing")
        if status.get("exit_code") != 0:
            errors.append("silent_success:nonzero_exit")
        if any(
            error.startswith(
                (
                    "missing_artifact:",
                    "empty_artifact:",
                    "expected_artifact_unmanifested:",
                    "unlinked_artifact:",
                )
            )
            for error in errors
        ):
            errors.append("silent_success")

    errors = sorted(set(errors))
    verdict = _final_verdict(report_verdict, errors)
    if not errors and not layout.supervised and allow_legacy_fixture:
        verdict = "fixture_valid"
    return {"valid": not errors, "verdict": verdict, "errors": errors}


def _public_text_has_secret_marker(article: dict[str, Any]) -> bool:
    sections = article.get("sections")
    claims = article.get("claims")
    values: list[str] = []
    if isinstance(sections, dict):
        values.extend(str(value) for value in sections.values())
    if isinstance(claims, list):
        values.extend(
            str(claim.get("text", "")) for claim in claims if isinstance(claim, dict)
        )
    text = "\n".join(values)
    return bool(
        re.search(
            r"(?i)(?:api[_-]?key|password|access[_-]?token|private[_-]?key)\s*[:=]|/Users/|/Volumes/Asylum/",
            text,
        )
    )


def _verified_publication_approval(
    root: Path, packet_id: Any, article_path: Path, errors: list[str]
) -> None:
    approval_path = root / "publication-approval.json"
    if not approval_path.is_file():
        errors.append("publication_without_verified_dr_mani_approval")
        return
    try:
        approval = _read_json(approval_path)
    except (OSError, ValueError, json.JSONDecodeError):
        errors.append("publication_approval_invalid")
        return
    if approval.get("schema") != "daedalus-publication-approval/v1":
        errors.append("publication_approval_schema_mismatch")
    if approval.get("packet_id") != packet_id:
        errors.append("publication_approval_packet_mismatch")
    if approval.get("approver") != "Dr. Mani" or approval.get("decision") != "approved":
        errors.append("publication_approval_not_explicit")
    if not approval.get("approved_at"):
        errors.append("publication_approval_timestamp_missing")
    if approval.get("article_sha256") != _sha256(article_path):
        errors.append("publication_approval_article_hash_mismatch")


def validate_publication(
    run_dir: str | Path, *, allow_legacy_fixture: bool = False
) -> dict[str, Any]:
    """Validate a prepared public article without an outward action."""
    root = Path(run_dir)
    errors: list[str] = []
    study_result = validate_study(root, allow_legacy_fixture=allow_legacy_fixture)
    if not study_result["valid"]:
        errors.append("study_evidence_invalid_for_publication")
    packet = _load_named_json(root, "study-packet.json", errors)
    report = _load_named_json(
        root, "archimedes-independent-evidence-report.json", errors
    )
    article_path = root / "public-journal-article.json"
    if not article_path.is_file():
        return {
            "valid": False,
            "publication_state": "publication_blocked",
            "errors": ["missing_record:public-journal-article.json"],
        }
    try:
        article = _read_json(article_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return {
            "valid": False,
            "publication_state": "publication_blocked",
            "errors": ["invalid_json:public-journal-article.json"],
        }

    if article.get("schema") != "daedalus-public-journal-article/v1":
        errors.append("schema_mismatch:public-journal-article.json")
    if article.get("packet_id") != packet.get("packet_id"):
        errors.append("packet_id_mismatch:public-journal-article.json")
    frozen_publication = packet.get("public_journal")
    if not isinstance(frozen_publication, dict):
        errors.append("frozen_publication_metadata_missing")
        frozen_publication = {}
    for key in ("destination", "title"):
        if article.get(key) != frozen_publication.get(key):
            errors.append(f"frozen_publication_mismatch:{key}")
    if article.get("authors") != frozen_publication.get("authorship"):
        errors.append("frozen_publication_mismatch:authorship")

    report_outcome = report.get("verdict")
    article_outcome = article.get("study_outcome")
    if article_outcome != report_outcome:
        errors.append(f"article_outcome_mismatch:{article_outcome}!={report_outcome}")

    sections = article.get("sections")
    if not isinstance(sections, dict):
        errors.append("article_sections_missing")
        sections = {}
    for field in sorted(ARTICLE_SECTION_FIELDS):
        if not isinstance(sections.get(field), str) or not sections[field].strip():
            errors.append(f"article_section_missing:{field}")

    included = article.get("included_content_classes")
    if not isinstance(included, list):
        errors.append("invalid_included_content_classes")
        included = []
    valid_included = {
        content_class for content_class in included if isinstance(content_class, str)
    }
    if len(valid_included) != len(included):
        errors.append("invalid_included_content_classes")
    for content_class in sorted(valid_included & FORBIDDEN_PUBLIC_CLASSES):
        errors.append(f"forbidden_public_content_class:{content_class}")
    public_content = article.get("public_content")
    if not isinstance(public_content, dict):
        errors.append("invalid_public_content")
        public_content = {}
    for forbidden in sorted(FORBIDDEN_PUBLIC_CLASSES):
        if public_content.get(forbidden) not in (None, False, "", [], {}):
            errors.append(f"privacy_leak:{forbidden}")
    if _public_text_has_secret_marker(article):
        errors.append("privacy_leak:secret_marker")

    claims = article.get("claims")
    if not isinstance(claims, list) or not claims:
        errors.append("article_claims_missing")
        claims = []
    observed_classes: set[str] = set()
    for position, claim in enumerate(claims, 1):
        if not isinstance(claim, dict):
            errors.append(f"invalid_claim:{position}")
            continue
        claim_id = claim.get("claim_id") or str(position)
        claim_class = claim.get("claim_class")
        if not isinstance(claim_class, str) or claim_class not in CLAIM_CLASSES:
            errors.append(f"invalid_claim_class:{claim_id}")
        else:
            observed_classes.add(claim_class)
        evidence_ref = claim.get("evidence_ref")
        content_hash = claim.get("content_sha256")
        valid_hash = _is_sha256(content_hash)
        if content_hash is not None and not valid_hash:
            errors.append(f"claim_hash_invalid:{claim_id}")
        if not evidence_ref and not valid_hash:
            errors.append(f"claim_lacks_evidence:{claim_id}")
        if evidence_ref:
            evidence_path_text = str(evidence_ref).split("#", 1)[0]
            relative, evidence_path = _contained_path(root, evidence_path_text)
            if relative is None or evidence_path is None:
                errors.append(f"claim_evidence_path_invalid:{claim_id}")
            elif not evidence_path.is_file() and not valid_hash:
                errors.append(f"claim_evidence_missing:{claim_id}")
            elif evidence_path.is_file() and valid_hash:
                if _sha256(evidence_path) != content_hash:
                    errors.append(f"claim_hash_mismatch:{claim_id}")
        text = str(claim.get("text", "")).lower()
        if (
            "fully validates daedalus" in text
            or "every daedalus function works" in text
            or "daedalus is conscious" in text
            or "phenomenal consciousness" in text
        ):
            errors.append(f"unsupported_public_claim:{claim_id}")
    for missing_class in sorted(CLAIM_CLASSES - observed_classes):
        errors.append(f"claim_class_missing:{missing_class}")

    state = article.get("publication_state")
    allowed_states = {
        "publication_prepared",
        "awaiting_dr_mani_approval",
        "published",
        "publication_declined",
        "publication_blocked",
    }
    if not isinstance(state, str) or state not in allowed_states:
        errors.append(f"invalid_publication_state:{state}")
    if state == "published":
        if article.get("publication_authorized") is not True:
            errors.append("publication_without_dr_mani_approval")
        if article.get("dr_mani_approval_evidence") != "publication-approval.json":
            errors.append("publication_without_verified_dr_mani_approval")
        _verified_publication_approval(
            root, packet.get("packet_id"), article_path, errors
        )
        errors.append("publication_requires_external_human_gate")
    elif article.get("publication_authorized") is True:
        errors.append("publication_state_authorization_inconsistent")

    errors = sorted(set(errors))
    return {
        "valid": not errors,
        "publication_state": (
            state if not errors and state in allowed_states else "publication_blocked"
        ),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate synthetic Daedalus mock-study evidence"
    )
    parser.add_argument("run_dir", type=Path)
    parser.add_argument(
        "--publication",
        action="store_true",
        help="validate public-journal-article.json without publishing it",
    )
    parser.add_argument(
        "--legacy-fixture-only",
        action="store_true",
        help="allow flat validator fixtures, capped below production acceptance",
    )
    args = parser.parse_args()
    result = (
        validate_publication(
            args.run_dir, allow_legacy_fixture=args.legacy_fixture_only
        )
        if args.publication
        else validate_study(args.run_dir, allow_legacy_fixture=args.legacy_fixture_only)
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
