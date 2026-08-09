#!/usr/bin/env python3
"""Supervise evidence-grade Daedalus interrupt and resume cycles.

The module is deliberately stdlib-only until the isolated worker entry point.
Importing it for preflight or tests never imports Daedalus, loads user
configuration, starts a provider, or accesses a memory store.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import math
import os
import re
import shlex
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DRIVER_SCHEMA = "daedalus-supervised-resume-driver/v1"
OFFICIAL_INTERFACE = "local_graph_gateway_command_resume"
SAFE_DEFAULTS: dict[str, bool] = {
    "auto_approve": False,
    "auto_mode": False,
    "dangerous_mode": False,
    "private_memory": False,
    "network_tools": False,
    "publication": False,
    "transfer": False,
}
PRODUCTION_BLOCKER_CODE = "subagent_execute_human_gate_unresolved"
COST_BLOCKER_CODE = "provider_cost_enforcement_unavailable"
WORKER_RESULT_SCHEMA = "daedalus-supervisor-worker-result/v1"
ALLOWLIST_SCHEMA = "daedalus-supervisor-allowlist/v1"
RUNTIME_SCHEMA = "daedalus-supervisor-runtime/v1"
STATE_SCHEMA = "daedalus-supervisor-state/v1"
LEDGER_SCHEMA = "daedalus-supervisor-ledger-entry/v1"
CYCLE_REQUEST_SCHEMA = "daedalus-supervisor-cycle-request/v1"
ATTEMPT_SCHEMA = "daedalus-mock-study-attempt/v1"
STATUS_SCHEMA = "daedalus-mock-study-status/v1"

_FORBIDDEN_EXECUTABLES = frozenset(
    {
        "curl",
        "wget",
        "nc",
        "ncat",
        "netcat",
        "ssh",
        "scp",
        "sftp",
        "rsync",
        "ftp",
        "telnet",
        "git",
        "gh",
        "open",
    }
)
_SHELL_CONTROL_TOKENS = frozenset(
    {"|", "||", "&", "&&", ";", ">", ">>", "<", "<<", "2>", "2>>"}
)
_SAFE_SHELL_TOKEN = re.compile(r"[A-Za-z0-9_./:=+,@%^-]+")
_PROVIDER_ENV_NAMES = frozenset(
    {
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_BASE_URL",
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "GOOGLE_API_KEY",
        "NVIDIA_API_KEY",
        "MINIMAX_API_KEY",
        "MINIMAX_BASE_URL",
        "SILICONFLOW_API_KEY",
        "OPENROUTER_API_KEY",
        "DEEPSEEK_API_KEY",
        "ZHIPU_API_KEY",
        "VOLCENGINE_API_KEY",
        "DASHSCOPE_API_KEY",
        "MOONSHOT_API_KEY",
        "KIMI_API_KEY",
        "CUSTOM_OPENAI_API_KEY",
        "CUSTOM_OPENAI_BASE_URL",
        "CUSTOM_ANTHROPIC_API_KEY",
        "CUSTOM_ANTHROPIC_BASE_URL",
        "OLLAMA_BASE_URL",
    }
)
_SAFE_RUNTIME_OVERRIDES = frozenset(
    {
        "reasoning_effort",
        "recursion_limit",
        "default_initiative",
        "steer_mode",
        "use_responses_api",
        "code_interpreter_timeout",
        "code_interpreter_max_result_chars",
        "sandbox_execute_timeout",
        "checkpoint_keep_per_thread",
    }
)
_SECRET_MARKERS = (
    re.compile(rb"sk-[A-Za-z0-9_-]{12,}"),
    re.compile(rb"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*[^\s,;]+"),
)


class DriverError(RuntimeError):
    """A fail-closed supervisor error with a stable machine code."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


@dataclass(frozen=True, slots=True)
class SupervisorConfig:
    """Frozen inputs needed to start one supervised attempt."""

    repo_root: Path
    packet_path: Path
    authorization_path: Path
    allowlist_path: Path
    preflight_path: Path
    runtime_config_path: Path
    prompt_path: Path
    attempt_dir: Path
    workdir: Path
    launcher: Path
    attempt_id: str
    timeout_seconds: float
    max_cycles: int = 8
    adapter_argv: tuple[str, ...] | None = None


@dataclass(frozen=True, slots=True)
class _FrozenInputs:
    packet: dict[str, Any]
    authorization: dict[str, Any]
    allowlist: dict[str, Any]
    preflight: dict[str, Any]
    runtime: dict[str, Any]
    prompt: str
    packet_id: str
    source_commit: str
    imported_package_path: str
    interpreter: str
    digests: dict[str, str]


@dataclass(frozen=True, slots=True)
class _CycleResult:
    exit_code: int | None
    timed_out: bool
    stdout: bytes
    stderr: bytes
    elapsed_seconds: float
    containment_active: bool


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _canonical_bytes(value: Any) -> bytes:
    try:
        rendered = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise DriverError(
            "noncanonical_json", "A control record is not canonical JSON."
        ) from exc
    return rendered.encode("utf-8")


def _json_digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise DriverError(
            "unreadable_input", f"Required input is unreadable: {path.name}"
        ) from exc
    return digest.hexdigest()


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _read_json(path: Path, expected_schema: str | None = None) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DriverError("invalid_json", f"Invalid JSON input: {path.name}") from exc
    if not isinstance(value, dict):
        raise DriverError(
            "invalid_json_type", f"JSON input must be an object: {path.name}"
        )
    if expected_schema is not None and value.get("schema") != expected_schema:
        raise DriverError("schema_mismatch", f"Unexpected schema in {path.name}")
    return value


def _write_new_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise DriverError(
            "immutable_path_exists", f"Refusing to overwrite {path.name}"
        ) from exc
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        with contextlib.suppress(OSError):
            path.unlink()
        raise


def _write_new_json(path: Path, value: dict[str, Any]) -> None:
    _write_new_bytes(path, _canonical_bytes(value) + b"\n")


def _append_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(descriptor, "ab") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return False
    return True


def _safe_relative_path(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise DriverError("unsafe_path", f"{field} must be a nonempty relative path.")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise DriverError("unsafe_path", f"{field} escapes the frozen workspace.")
    return path.as_posix()


def _snapshot_tree(root: Path) -> dict[str, dict[str, Any]]:
    snapshot: dict[str, dict[str, Any]] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            try:
                target = path.resolve(strict=True)
            except OSError as exc:
                raise DriverError(
                    "unsafe_symlink", f"Broken symlink in workspace: {relative}"
                ) from exc
            if not _inside(target, root):
                raise DriverError(
                    "symlink_escape", f"Symlink escapes workspace: {relative}"
                )
            snapshot[relative] = {"kind": "symlink", "target": str(target)}
        elif path.is_file():
            snapshot[relative] = {
                "kind": "file",
                "size": path.stat().st_size,
                "sha256": _file_digest(path),
            }
        elif path.is_dir():
            snapshot[relative] = {"kind": "directory"}
        else:
            raise DriverError(
                "unsafe_file_type", f"Unsupported workspace entry: {relative}"
            )
    return snapshot


def _sanitize_capture(
    data: bytes, secret_values: Sequence[bytes]
) -> tuple[bytes, bool]:
    redacted = data
    detected = False
    for secret in secret_values:
        if len(secret) >= 8 and secret in redacted:
            redacted = redacted.replace(secret, b"[REDACTED]")
            detected = True
    for pattern in _SECRET_MARKERS:
        if pattern.search(redacted):
            redacted = pattern.sub(b"[REDACTED]", redacted)
            detected = True
    return redacted, detected


def _check_map(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    checks = report.get("checks")
    if not isinstance(checks, list):
        raise DriverError("invalid_preflight", "Preflight report has no typed checks.")
    result: dict[str, dict[str, Any]] = {}
    for item in checks:
        if isinstance(item, dict) and isinstance(item.get("check_id"), str):
            result[item["check_id"]] = item
    return result


def _require_pass(checks: dict[str, dict[str, Any]], check_id: str) -> dict[str, Any]:
    item = checks.get(check_id)
    if item is None or item.get("status") != "pass":
        raise DriverError(
            "preflight_not_ready", f"Required preflight check did not pass: {check_id}"
        )
    evidence = item.get("evidence")
    if not isinstance(evidence, dict):
        raise DriverError(
            "invalid_preflight", f"Preflight check has no evidence: {check_id}"
        )
    return evidence


def _validate_runtime_config(runtime: dict[str, Any], *, adapter: bool) -> None:
    provider = runtime.get("provider")
    model = runtime.get("model")
    if not isinstance(provider, str) or not provider:
        raise DriverError("invalid_runtime", "Runtime provider is missing.")
    if not isinstance(model, str) or not model:
        raise DriverError("invalid_runtime", "Runtime model is missing.")
    if provider == "fixture" and not adapter:
        raise DriverError(
            "fixture_runtime_forbidden",
            "Fixture runtime cannot drive a production cycle.",
        )
    names = runtime.get("credential_env_names", [])
    if not isinstance(names, list) or any(
        name not in _PROVIDER_ENV_NAMES for name in names
    ):
        raise DriverError(
            "unsafe_runtime_environment",
            "Runtime requested an undeclared environment variable.",
        )
    overrides = runtime.get("config_overrides", {})
    if not isinstance(overrides, dict) or not set(overrides).issubset(
        _SAFE_RUNTIME_OVERRIDES
    ):
        raise DriverError(
            "unsafe_runtime_override", "Runtime config contains a forbidden override."
        )


def _validate_authorization(
    packet: dict[str, Any],
    authorization: dict[str, Any],
    runtime: dict[str, Any],
    *,
    adapter: bool,
) -> None:
    if packet.get("synthetic_study") is not True:
        raise DriverError(
            "non_synthetic_packet",
            "The supervised harness accepts synthetic packets only.",
        )
    if authorization.get("study_execution_authorized") is not True:
        raise DriverError(
            "study_not_authorized", "Study execution has not been authorized."
        )
    approval_evidence = authorization.get("approval_evidence")
    if not isinstance(approval_evidence, str) or not approval_evidence.strip():
        raise DriverError(
            "missing_human_gate", "Study authorization has no human approval evidence."
        )
    if (
        authorization.get("tool_action_approval_policy")
        != "separate_per_interrupt_exact_digest"
        or authorization.get("tool_action_preapproval_authorized") is not False
    ):
        raise DriverError(
            "missing_human_gate",
            "Every tool action requires a separate exact-digest human decision.",
        )
    required_false = (
        "private_memory_access_authorized",
        "private_research_data_access_authorized",
        "artifact_transfer_authorized",
        "publication_authorized",
        "evoscientist_core_modification_authorized",
    )
    if any(authorization.get(key) is not False for key in required_false):
        raise DriverError(
            "broadened_authorization",
            "Authorization exceeds the supervised study boundary.",
        )
    boundary = packet.get("provider_cost_boundary")
    prohibited = packet.get("prohibited_operations")
    if (
        not isinstance(boundary, dict)
        or not isinstance(prohibited, list)
        or any(not isinstance(value, str) for value in prohibited)
    ):
        raise DriverError(
            "invalid_provider_boundary", "The provider and cost boundary is malformed."
        )
    allowed = boundary.get("allowed_providers")
    paid_allowed = boundary.get("paid_providers_authorized")
    maximum_cost = boundary.get("maximum_cost_usd")
    if (
        not isinstance(allowed, list)
        or any(not isinstance(value, str) or not value for value in allowed)
        or not isinstance(paid_allowed, bool)
        or isinstance(maximum_cost, bool)
        or not isinstance(maximum_cost, (int, float))
        or not math.isfinite(float(maximum_cost))
        or maximum_cost < 0
    ):
        raise DriverError(
            "invalid_provider_boundary", "The provider and cost boundary is malformed."
        )
    if adapter:
        if (
            authorization.get("paid_provider_activation_authorized") is not False
            or paid_allowed is not False
            or maximum_cost != 0
            or "activate_paid_provider" not in prohibited
        ):
            raise DriverError(
                "broadened_authorization",
                "Adapter execution must explicitly prohibit and zero paid providers.",
            )
        return
    if runtime.get("provider") not in allowed:
        raise DriverError(
            "provider_not_authorized",
            "Runtime provider is outside the packet allowlist.",
        )
    if (
        authorization.get("paid_provider_activation_authorized") is not True
        or paid_allowed is not True
        or "activate_paid_provider" in prohibited
    ):
        raise DriverError(
            "provider_not_authorized", "Provider activation has not been authorized."
        )
    if maximum_cost <= 0:
        raise DriverError(
            "provider_cost_invalid",
            "Paid provider execution requires a positive cost cap.",
        )
    raise DriverError(
        COST_BLOCKER_CODE,
        "Paid provider execution remains blocked until the supervised driver can "
        "deterministically enforce maximum_cost_usd.",
    )


def _validate_literal_shell_command(command: str, argv: list[str]) -> None:
    """Require a literal, expansion-free shell command for the first harness."""

    if command != " ".join(argv) or any(
        _SAFE_SHELL_TOKEN.fullmatch(token) is None for token in argv
    ):
        raise DriverError(
            "unsafe_shell_syntax",
            "The first supervised harness permits literal shell tokens only.",
        )


def _validate_allowlist(allowlist: dict[str, Any], workdir: Path) -> None:
    for field in (
        "network_operations_allowed",
        "private_memory_allowed",
        "transfer_allowed",
        "publication_allowed",
    ):
        if allowlist.get(field) is not False:
            raise DriverError(
                "broadened_allowlist",
                f"The first supervised harness requires {field}=false.",
            )
    actions = allowlist.get("allowed_actions")
    artifacts = allowlist.get("allowed_artifact_paths")
    if not isinstance(actions, list) or not actions:
        raise DriverError(
            "empty_action_allowlist", "At least one exact action must be declared."
        )
    if not isinstance(artifacts, list):
        raise DriverError(
            "invalid_artifact_allowlist", "Artifact allowlist must be a list."
        )
    for artifact in artifacts:
        relative = _safe_relative_path(artifact, field="allowed_artifact_paths")
        if not _inside(workdir / relative, workdir):
            raise DriverError("unsafe_path", "Artifact path escapes the workspace.")
    for action in actions:
        if not isinstance(action, dict) or action.get("name") != "execute":
            raise DriverError(
                "unsafe_action_allowlist", "Only exact execute actions are supported."
            )
        args = action.get("args")
        argv = action.get("argv")
        if not isinstance(args, dict) or set(args) != {"command"}:
            raise DriverError(
                "unsafe_action_allowlist", "Execute args must contain only command."
            )
        command = args.get("command")
        if not isinstance(command, str) or not isinstance(argv, list) or not argv:
            raise DriverError(
                "unsafe_action_allowlist", "Execute command and argv are required."
            )
        try:
            parsed = shlex.split(command)
        except ValueError as exc:
            raise DriverError(
                "unsafe_command", "Execute command is not valid shell syntax."
            ) from exc
        if parsed != argv or any(not isinstance(value, str) for value in argv):
            raise DriverError(
                "command_identity_mismatch",
                "Declared command does not match exact argv.",
            )
        executable = Path(argv[0]).name.lower()
        if executable in _FORBIDDEN_EXECUTABLES or any(
            token in _SHELL_CONTROL_TOKENS for token in argv
        ):
            raise DriverError(
                "forbidden_command",
                "Network, transfer, or shell-control command is forbidden.",
            )
        if argv[0] != "python3":
            raise DriverError(
                "unsupported_executable",
                "The first supervised harness requires its nested python3 wrapper.",
            )
        indexes = action.get("path_argument_indexes", [])
        path_digests = action.get("path_sha256")
        if not isinstance(indexes, list) or any(
            not isinstance(index, int) for index in indexes
        ):
            raise DriverError(
                "invalid_path_indexes", "Path argument indexes must be integers."
            )
        if len(argv) < 2 or 1 not in indexes or argv[1].startswith("-"):
            raise DriverError(
                "unsafe_python_invocation",
                "Python argv[1] must be a frozen script with a SHA-256 identity.",
            )
        _validate_literal_shell_command(command, argv)
        expected_digest_keys = {str(index) for index in indexes}
        if (
            not isinstance(path_digests, dict)
            or set(path_digests) != expected_digest_keys
            or any(not _is_sha256(value) for value in path_digests.values())
        ):
            raise DriverError(
                "invalid_path_identity",
                "Every command path requires one frozen SHA-256 identity.",
            )
        for index in indexes:
            if index <= 0 or index >= len(argv):
                raise DriverError(
                    "invalid_path_indexes", "Path argument index is outside argv."
                )
            relative = _safe_relative_path(argv[index], field="command path")
            if not _inside(workdir / relative, workdir):
                raise DriverError("unsafe_path", "Command path escapes the workspace.")
            path = workdir / relative
            if not path.is_file() or path.is_symlink():
                raise DriverError(
                    "command_path_unresolved",
                    "A frozen command path is missing or unsafe.",
                )
            if _file_digest(path) != path_digests[str(index)]:
                raise DriverError(
                    "command_path_digest_mismatch",
                    "A frozen command path changed after approval preparation.",
                )


def _verify_current_source_snapshot(repo_root: Path, expected_commit: str) -> None:
    """Fail if the production source no longer matches its clean preflight."""

    try:
        before = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        status = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        after = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DriverError(
            "source_snapshot_unreachable",
            "The production source identity could not be rechecked.",
        ) from exc
    if before.returncode != 0 or status.returncode != 0 or after.returncode != 0:
        raise DriverError(
            "source_snapshot_unreachable",
            "The production source identity could not be rechecked.",
        )
    commits = {before.stdout.strip(), after.stdout.strip()}
    if commits != {expected_commit}:
        raise DriverError(
            "source_snapshot_changed",
            "The production source commit differs from the frozen preflight.",
        )
    if status.stdout.strip():
        raise DriverError(
            "source_snapshot_dirty",
            "The production source changed after its clean preflight.",
        )


def _validate_action_request(
    action: dict[str, Any], allowlist: dict[str, Any], workdir: Path
) -> None:
    if not isinstance(action.get("id"), str) or not action["id"]:
        raise DriverError("missing_action_identity", "Action request has no stable ID.")
    if action.get("name") == "execute":
        args = action.get("args")
        command = args.get("command") if isinstance(args, dict) else None
        if not isinstance(command, str):
            raise DriverError(
                "malformed_action", "Execute request has no command string."
            )
        try:
            requested_argv = shlex.split(command)
        except ValueError as exc:
            raise DriverError(
                "unsafe_command", "Execute request has invalid shell syntax."
            ) from exc
        if not requested_argv:
            raise DriverError("unsafe_command", "Execute request has an empty command.")
        _validate_literal_shell_command(command, requested_argv)
        if Path(requested_argv[0]).name.lower() in _FORBIDDEN_EXECUTABLES or any(
            token in _SHELL_CONTROL_TOKENS for token in requested_argv
        ):
            raise DriverError(
                "forbidden_command",
                "Network, transfer, or shell-control command is forbidden.",
            )
        for token in requested_argv[1:]:
            candidate = Path(token)
            if candidate.is_absolute() or ".." in candidate.parts:
                raise DriverError(
                    "unsafe_path", "Execute request contains a path escape."
                )
    candidates = allowlist["allowed_actions"]
    exact = next(
        (
            item
            for item in candidates
            if item.get("name") == action.get("name")
            and item.get("args") == action.get("args")
        ),
        None,
    )
    if exact is None:
        known_names = {item.get("name") for item in candidates}
        code = (
            "unknown_tool"
            if action.get("name") not in known_names
            else "action_not_allowlisted"
        )
        raise DriverError(code, "Action request is outside the exact frozen allowlist.")
    _validate_allowlist({**allowlist, "allowed_actions": [exact]}, workdir)


def _worker_config_values(runtime: dict[str, Any], workdir: Path) -> dict[str, Any]:
    """Build explicit worker config values with non-negotiable safe settings."""

    values = dict(runtime.get("config_overrides", {}))
    values.update(
        {
            "provider": runtime["provider"],
            "model": runtime["model"],
            "default_mode": "run",
            "default_workdir": str(workdir.resolve()),
            "ui_backend": "cli",
            "auto_approve": False,
            "auto_mode": False,
            "dangerous_mode": False,
            "shell_allow_list": "",
            "enable_ask_user": True,
            "memory_profile_enabled": False,
            "memory_observations_enabled": False,
            "memory_observation_writer": "off",
            "memory_workers_enabled": False,
            "memory_skill_synthesis_enabled": False,
            "enable_async_subagents": False,
            "enable_scheduler": False,
            "channel_enabled": False,
        }
    )
    return values


def _build_graph_run_message(request: dict[str, Any]) -> Any:
    """Build the exact official local-gateway input for one cycle."""

    if request.get("mode") == "start":
        prompt = request.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise DriverError("invalid_worker_request", "Start request has no prompt.")
        return prompt
    if request.get("mode") == "resume":
        payload = request.get("resume_payload")
        if not isinstance(payload, dict) or not payload:
            raise DriverError(
                "invalid_worker_request", "Resume request has no payload."
            )
        from langgraph.types import Command

        return Command(resume=payload)
    raise DriverError("invalid_worker_request", "Worker request mode is unsupported.")


def _assert_worker_isolation(request: dict[str, Any]) -> None:
    """Prove all state-bearing worker paths point at the isolated attempt root."""

    runtime_root = Path(str(request.get("runtime_root", ""))).resolve()
    workdir = Path(str(request.get("workdir", ""))).resolve()
    expected = {
        "HOME": runtime_root / "home",
        "XDG_CONFIG_HOME": runtime_root / "xdg-config",
        "XDG_CACHE_HOME": runtime_root / "xdg-cache",
        "TMPDIR": runtime_root / "tmp",
        "TMP": runtime_root / "tmp",
        "TEMP": runtime_root / "tmp",
        "EVOSCIENTIST_DATA_DIR": runtime_root / "data",
        "EVOSCIENTIST_MEMORIES_DIR": runtime_root / "memories",
        "EVOSCIENTIST_SKILLS_DIR": runtime_root / "skills",
        "EVOSCIENTIST_RUNS_DIR": runtime_root / "runs",
        "EVOSCIENTIST_MEDIA_DIR": runtime_root / "media",
        "EVOSCIENTIST_WORKSPACE_DIR": workdir,
    }
    for key, path in expected.items():
        value = os.environ.get(key)
        if not value or Path(value).resolve() != path:
            raise DriverError(
                "worker_isolation_failure",
                f"Worker isolation variable does not match its frozen path: {key}",
            )


def _state_hash_payload(state: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in state.items() if key != "state_sha256"}


def _ledger_hash_payload(record: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key != "record_sha256"}


def _sandboxed_argv(
    argv: Sequence[str],
    *,
    attempt_dir: Path,
    repo_root: Path,
    env: dict[str, str],
    allow_network: bool,
    restrict_process_exec: bool = False,
) -> list[str]:
    """Wrap one worker in the host's bounded read/write process sandbox."""

    sandbox_exec = Path("/usr/bin/sandbox-exec")
    if sys.platform != "darwin" or not sandbox_exec.is_file():
        raise DriverError(
            "containment_unavailable",
            "The host cannot enforce the required attempt-only write boundary.",
        )
    attempt = attempt_dir.resolve()
    read_exceptions = {
        attempt,
        (repo_root / "EvoScientist").resolve(),
        Path(__file__).resolve().parent,
    }
    executable = Path(str(argv[0])).expanduser()
    executable_paths: set[Path] = set()
    if executable.is_absolute():
        executable_paths.update({executable.absolute(), executable.resolve()})
        read_exceptions.add(executable.parent.parent)
        read_exceptions.add(executable.resolve().parent.parent)
    for value in argv[1:]:
        candidate = Path(str(value)).expanduser()
        if candidate.is_absolute() and candidate.exists():
            read_exceptions.add(candidate.resolve().parent)
    for key in ("SSL_CERT_FILE", "SSL_CERT_DIR"):
        value = env.get(key)
        if value:
            candidate = Path(value).expanduser().resolve()
            read_exceptions.add(candidate if candidate.is_dir() else candidate.parent)
    protected_reads = (Path("/Users"), Path("/Volumes"), Path("/private/var/folders"))
    process_rules = (
        [
            "(allow process-fork)",
            *(
                f"(allow process-exec (literal {json.dumps(str(path))}))"
                for path in sorted(executable_paths, key=str)
            ),
        ]
        if restrict_process_exec
        else ["(allow process*)"]
    )
    profile = " ".join(
        [
            "(version 1)",
            "(deny default)",
            *process_rules,
            "(allow file-read*)",
            "(allow file-read-metadata)",
            *(
                f"(deny file-read* (subpath {json.dumps(str(path.resolve()))}))"
                for path in protected_reads
            ),
            *(
                f"(allow file-read* (subpath {json.dumps(str(path.resolve()))}))"
                for path in sorted(read_exceptions, key=str)
            ),
            f"(allow file-write* (subpath {json.dumps(str(attempt))}))",
            '(allow file-write-data (literal "/dev/null"))',
            "(allow network*)" if allow_network else "(deny network*)",
        ]
    )
    return [str(sandbox_exec), "-p", profile, *argv]


def _probe_containment() -> dict[str, Any]:
    """Exercise the host containment contract without loading Daedalus."""

    available = sys.platform == "darwin" and Path("/usr/bin/sandbox-exec").is_file()
    result: dict[str, Any] = {
        "available": available,
        "enforcement": (
            "darwin_sandbox_exec_attempt_write_boundary" if available else "unavailable"
        ),
        "attempt_only_writes": False,
        "network_denied_without_provider_authorization": False,
        "tool_network_denied": False,
        "tool_private_roots_denied": False,
        "tool_workspace_only_writes": False,
        "tool_undeclared_subprocesses_denied": False,
    }
    if not available:
        return result
    env = {
        key: value
        for key in ("PATH", "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR")
        if (value := os.environ.get(key))
    }
    env.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONUNBUFFERED": "1"})
    repo_root = Path(__file__).resolve().parents[3]

    def run(argv: list[str], cwd: Path) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            argv,
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=5,
            check=False,
        )

    try:
        with tempfile.TemporaryDirectory(prefix="daedalus-containment-probe-") as raw:
            root = Path(raw).resolve()
            attempt = root / "attempt"
            workspace = attempt / "workspace"
            workspace.mkdir(parents=True)
            sentinel = root / "protected-sentinel.txt"
            sentinel.write_text("private", encoding="utf-8")
            outside = root / "outside.txt"
            outer_allowed = workspace / "outer-allowed.txt"
            outer_allowed_run = run(
                _sandboxed_argv(
                    [
                        sys.executable,
                        "-c",
                        f"from pathlib import Path; Path({str(outer_allowed)!r}).write_text('ok')",
                    ],
                    attempt_dir=attempt,
                    repo_root=repo_root,
                    env=env,
                    allow_network=False,
                ),
                workspace,
            )
            outer_denied_run = run(
                _sandboxed_argv(
                    [
                        sys.executable,
                        "-c",
                        f"from pathlib import Path; Path({str(outside)!r}).write_text('bad')",
                    ],
                    attempt_dir=attempt,
                    repo_root=repo_root,
                    env=env,
                    allow_network=False,
                ),
                workspace,
            )
            outer_network_run = run(
                _sandboxed_argv(
                    [
                        sys.executable,
                        "-c",
                        "import socket; s=socket.socket(); s.bind(('127.0.0.1', 0))",
                    ],
                    attempt_dir=attempt,
                    repo_root=repo_root,
                    env=env,
                    allow_network=False,
                ),
                workspace,
            )

            def nested(code: str) -> list[str]:
                return _sandboxed_argv(
                    [sys.executable, "-c", code],
                    attempt_dir=workspace,
                    repo_root=repo_root,
                    env=env,
                    allow_network=False,
                    restrict_process_exec=True,
                )

            nested_network_run = run(
                nested("import socket; s=socket.socket(); s.bind(('127.0.0.1', 0))"),
                workspace,
            )
            nested_read_run = run(
                nested(
                    f"from pathlib import Path; Path({str(sentinel)!r}).read_text()"
                ),
                workspace,
            )
            nested_write_run = run(
                nested(
                    f"from pathlib import Path; Path({str(outside)!r}).write_text('bad')"
                ),
                workspace,
            )
            child_marker = workspace / "undeclared-child.txt"
            nested_child_run = run(
                nested(
                    "import subprocess; "
                    "subprocess.run(['/usr/bin/touch', 'undeclared-child.txt'], check=True)"
                ),
                workspace,
            )
            result.update(
                {
                    "attempt_only_writes": (
                        outer_allowed_run.returncode == 0
                        and outer_allowed.is_file()
                        and outer_denied_run.returncode != 0
                        and not outside.exists()
                    ),
                    "network_denied_without_provider_authorization": (
                        outer_network_run.returncode != 0
                    ),
                    "tool_network_denied": nested_network_run.returncode != 0,
                    "tool_private_roots_denied": nested_read_run.returncode != 0,
                    "tool_workspace_only_writes": (
                        nested_write_run.returncode != 0 and not outside.exists()
                    ),
                    "tool_undeclared_subprocesses_denied": (
                        nested_child_run.returncode != 0 and not child_marker.exists()
                    ),
                }
            )
    except (OSError, subprocess.TimeoutExpired):
        return result
    return result


def _is_containment_denial(stderr: bytes) -> bool:
    lowered = stderr.lower()
    return any(
        marker in lowered
        for marker in (
            b"operation not permitted",
            b"permission denied",
            b"sandbox: deny",
        )
    )


def _scrub_declared_credentials(runtime: dict[str, Any]) -> list[str]:
    names = runtime.get("credential_env_names", [])
    scrubbed: list[str] = []
    if isinstance(names, list):
        for name in names:
            if isinstance(name, str):
                os.environ.pop(name, None)
                scrubbed.append(name)
    return sorted(scrubbed)


class SupervisedResumeDriver:
    """Fail-closed supervisor for one immutable Daedalus attempt."""

    def __init__(self, config: SupervisorConfig) -> None:
        self.config = config
        self.repo_root = config.repo_root.expanduser().resolve()
        self.attempt_dir = config.attempt_dir.expanduser().resolve()
        self.workdir = config.workdir.expanduser().resolve()
        self.evidence_dir = self.attempt_dir / "supervisor-evidence"
        self.cycles_dir = self.evidence_dir / "cycles"
        self.decisions_dir = self.evidence_dir / "decisions"
        self.states_dir = self.evidence_dir / "states"
        self.runtime_dir = self.evidence_dir / "runtime"
        self.manifest_path = self.evidence_dir / "attempt-manifest.json"
        self.ledger_path = self.evidence_dir / "run-ledger.jsonl"
        self.native_events_path = self.evidence_dir / "native-events.jsonl"
        self.stderr_path = self.evidence_dir / "stderr.log"
        self.status_path = self.evidence_dir / "status.json"

    @classmethod
    def from_attempt(cls, attempt_dir: Path) -> SupervisedResumeDriver:
        """Rehydrate production control metadata from an immutable manifest."""

        resolved = attempt_dir.expanduser().resolve()
        manifest_path = resolved / "supervisor-evidence" / "attempt-manifest.json"
        manifest = _read_json(manifest_path, ATTEMPT_SCHEMA)
        expected_digest = manifest.get("manifest_sha256")
        payload = {
            key: value for key, value in manifest.items() if key != "manifest_sha256"
        }
        if (
            not isinstance(expected_digest, str)
            or _json_digest(payload) != expected_digest
        ):
            raise DriverError(
                "corrupted_manifest", "Attempt manifest digest does not match."
            )
        input_paths = manifest.get("input_paths")
        if not isinstance(input_paths, dict):
            raise DriverError(
                "missing_input_paths", "Attempt manifest cannot be rehydrated."
            )
        required = {
            "packet",
            "authorization",
            "allowlist",
            "preflight",
            "runtime_config",
            "prompt",
            "supervisor_source",
            "cycle_worker_source",
        }
        if set(input_paths) != required:
            raise DriverError(
                "missing_input_paths", "Attempt manifest input paths are incomplete."
            )
        config = SupervisorConfig(
            repo_root=Path(str(manifest["repo_root"])),
            packet_path=Path(str(input_paths["packet"])),
            authorization_path=Path(str(input_paths["authorization"])),
            allowlist_path=Path(str(input_paths["allowlist"])),
            preflight_path=Path(str(input_paths["preflight"])),
            runtime_config_path=Path(str(input_paths["runtime_config"])),
            prompt_path=Path(str(input_paths["prompt"])),
            attempt_dir=resolved,
            workdir=Path(str(manifest["workdir"])),
            launcher=Path(str(manifest["launcher"])),
            attempt_id=str(manifest["attempt_id"]),
            timeout_seconds=float(manifest["timeout_seconds"]),
            max_cycles=int(manifest["maximum_cycles"]),
        )
        return cls(config)

    @contextlib.contextmanager
    def _lock(self):
        self.evidence_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        lock = self.evidence_dir / ".driver.lock"
        try:
            descriptor = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as exc:
            raise DriverError(
                "attempt_locked", "Another supervisor operation may still be active."
            ) from exc
        os.close(descriptor)
        try:
            yield
        finally:
            with contextlib.suppress(OSError):
                lock.unlink()

    def _freeze_inputs(self) -> _FrozenInputs:
        if not self.repo_root.is_dir():
            raise DriverError("missing_repo", "Repository root does not exist.")
        if not self.workdir.is_dir() or not _inside(self.workdir, self.attempt_dir):
            raise DriverError(
                "unsafe_workdir",
                "Work directory must exist inside the attempt directory.",
            )
        if self.workdir == self.attempt_dir:
            raise DriverError(
                "unsafe_workdir",
                "Work directory must be isolated from supervisor evidence.",
            )
        if (self.workdir / "EvoScientist").exists():
            raise DriverError(
                "package_shadow", "Work directory contains a package-shadowing path."
            )
        _snapshot_tree(self.workdir)

        packet_path = self.config.packet_path.expanduser().resolve()
        authorization_path = self.config.authorization_path.expanduser().resolve()
        allowlist_path = self.config.allowlist_path.expanduser().resolve()
        preflight_path = self.config.preflight_path.expanduser().resolve()
        runtime_path = self.config.runtime_config_path.expanduser().resolve()
        prompt_path = self.config.prompt_path.expanduser().resolve()
        packet = _read_json(packet_path, "daedalus-mock-study-packet/v1")
        authorization = _read_json(
            authorization_path, "daedalus-mock-study-authorization/v1"
        )
        allowlist = _read_json(allowlist_path, ALLOWLIST_SCHEMA)
        preflight = _read_json(preflight_path, "daedalus-capability-preflight/v1")
        runtime = _read_json(runtime_path, RUNTIME_SCHEMA)
        try:
            prompt = prompt_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise DriverError("invalid_prompt", "Prompt file is unreadable.") from exc
        if not prompt.strip():
            raise DriverError("invalid_prompt", "Prompt file is blank.")

        packet_id = packet.get("packet_id")
        if not isinstance(packet_id, str) or not packet_id:
            raise DriverError(
                "missing_packet_identity", "Study packet has no packet ID."
            )
        for value in (authorization, allowlist, runtime):
            if value.get("packet_id") != packet_id:
                raise DriverError(
                    "packet_identity_mismatch", "Frozen inputs name different packets."
                )
        if preflight.get("status") != "ready" or preflight.get("blocking_check_ids"):
            raise DriverError(
                "preflight_not_ready", "Capability preflight is not ready."
            )
        checks = _check_map(preflight)
        workdir_evidence = _require_pass(checks, "workdir.data_only")
        launcher_evidence = _require_pass(checks, "launcher.resolved")
        interpreter_evidence = _require_pass(checks, "launcher.interpreter")
        import_evidence = _require_pass(checks, "launcher.import_identity")
        source_evidence = _require_pass(checks, "source.git_identity")
        _require_pass(checks, "runtime.supervised_resume_driver")
        if Path(str(workdir_evidence.get("workdir", ""))).resolve() != self.workdir:
            raise DriverError(
                "preflight_identity_mismatch",
                "Preflight covers a different work directory.",
            )
        launcher = self.config.launcher.expanduser().resolve()
        if Path(str(launcher_evidence.get("launcher", ""))).resolve() != launcher:
            raise DriverError(
                "preflight_identity_mismatch", "Preflight covers a different launcher."
            )
        interpreter = interpreter_evidence.get("interpreter")
        imported = import_evidence.get("imported")
        expected = import_evidence.get("expected")
        commit = source_evidence.get("commit")
        if not all(
            isinstance(value, str) and value
            for value in (interpreter, imported, commit)
        ):
            raise DriverError(
                "missing_source_identity", "Preflight omits source identity."
            )
        if expected != imported:
            raise DriverError(
                "preflight_identity_mismatch",
                "Imported package does not match preflight expectation.",
            )
        if self.config.adapter_argv is None:
            _verify_current_source_snapshot(self.repo_root, commit)
            raise DriverError(
                PRODUCTION_BLOCKER_CODE,
                "Daedalus synchronous subagents can execute without the main-agent "
                "human interrupt gate; production execution is disabled.",
            )

        _validate_runtime_config(runtime, adapter=self.config.adapter_argv is not None)
        _validate_authorization(
            packet, authorization, runtime, adapter=self.config.adapter_argv is not None
        )
        _validate_allowlist(allowlist, self.workdir)
        required_artifacts = {
            _safe_relative_path(item.get("path"), field="expected artifact")
            for item in packet.get("expected_artifacts", [])
            if isinstance(item, dict)
            and item.get("required") is True
            and item.get("producer") == "daedalus"
            and item.get("role") not in {"native_event_stream", "terminal_status"}
        }
        allowed_artifacts = set(allowlist.get("allowed_artifact_paths", []))
        if not required_artifacts.issubset(allowed_artifacts):
            raise DriverError(
                "artifact_allowlist_incomplete",
                "Required artifacts are not fully allowlisted.",
            )

        paths = {
            "packet": packet_path,
            "authorization": authorization_path,
            "allowlist": allowlist_path,
            "preflight": preflight_path,
            "runtime_config": runtime_path,
            "prompt": prompt_path,
            "supervisor_source": Path(__file__).resolve(),
            "cycle_worker_source": self._cycle_worker_source(),
        }
        return _FrozenInputs(
            packet=packet,
            authorization=authorization,
            allowlist=allowlist,
            preflight=preflight,
            runtime=runtime,
            prompt=prompt,
            packet_id=packet_id,
            source_commit=commit,
            imported_package_path=imported,
            interpreter=interpreter,
            digests={name: _file_digest(path) for name, path in paths.items()},
        )

    def _cycle_worker_source(self) -> Path:
        if self.config.adapter_argv is None:
            return Path(__file__).resolve()
        argv = self.config.adapter_argv
        if len(argv) < 2 or Path(argv[0]).resolve() != self.config.launcher.resolve():
            raise DriverError(
                "unsafe_adapter",
                "A deterministic adapter must use the frozen launcher interpreter.",
            )
        source = Path(argv[1]).expanduser().resolve()
        if not source.is_file() or source.is_symlink():
            raise DriverError(
                "unsafe_adapter", "The deterministic adapter source is not a safe file."
            )
        return source

    def _preserve_frozen_inputs(self) -> dict[str, str]:
        frozen_dir = self.evidence_dir
        sources = {
            "packet": (self.config.packet_path, "study-packet.json"),
            "authorization": (
                self.config.authorization_path,
                "authorization-record.json",
            ),
            "allowlist": (self.config.allowlist_path, "execution-allowlist.json"),
            "preflight": (self.config.preflight_path, "preflight.json"),
            "runtime_config": (
                self.config.runtime_config_path,
                "supervisor-runtime.json",
            ),
            "prompt": (self.config.prompt_path, "prompt.txt"),
            "supervisor_source": (Path(__file__), "supervisor-source.py"),
            "cycle_worker_source": (
                self._cycle_worker_source(),
                "cycle-worker-source.py",
            ),
        }
        preserved: dict[str, Path] = {}
        for name, (source, filename) in sources.items():
            try:
                data = source.expanduser().resolve().read_bytes()
            except OSError as exc:
                raise DriverError(
                    "unreadable_input", f"Required input is unreadable: {name}"
                ) from exc
            destination = frozen_dir / filename
            _write_new_bytes(destination, data)
            preserved[name] = destination.resolve()
        self.config = replace(
            self.config,
            packet_path=preserved["packet"],
            authorization_path=preserved["authorization"],
            allowlist_path=preserved["allowlist"],
            preflight_path=preserved["preflight"],
            runtime_config_path=preserved["runtime_config"],
            prompt_path=preserved["prompt"],
            adapter_argv=(
                (
                    self.config.adapter_argv[0],
                    str(preserved["cycle_worker_source"]),
                    *self.config.adapter_argv[2:],
                )
                if self.config.adapter_argv is not None
                else None
            ),
        )
        return {name: str(path) for name, path in preserved.items()}

    def _read_manifest(self) -> dict[str, Any]:
        manifest = _read_json(self.manifest_path, ATTEMPT_SCHEMA)
        expected_digest = manifest.get("manifest_sha256")
        payload = {
            key: value for key, value in manifest.items() if key != "manifest_sha256"
        }
        if (
            not isinstance(expected_digest, str)
            or _json_digest(payload) != expected_digest
        ):
            raise DriverError(
                "corrupted_manifest", "Attempt manifest digest does not match."
            )
        return manifest

    def _append_ledger(
        self,
        *,
        entry_type: str,
        stage: str,
        summary: str,
        evidence_ref: str,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        existing = self._read_ledger()
        record: dict[str, Any] = {
            "schema": LEDGER_SCHEMA,
            "sequence": len(existing) + 1,
            "timestamp": _utc_now(),
            "monotonic_seconds": time.monotonic(),
            "entry_type": entry_type,
            "attempt_id": self.config.attempt_id,
            "stage": stage,
            "source": "archimedes_supervisor",
            "evidence_ref": evidence_ref,
            "summary": summary,
            "previous_record_sha256": existing[-1]["record_sha256"]
            if existing
            else None,
        }
        if extra:
            record["detail"] = extra
        record["record_sha256"] = _json_digest(_ledger_hash_payload(record))
        _append_bytes(self.ledger_path, _canonical_bytes(record) + b"\n")
        return record

    def _read_ledger(self) -> list[dict[str, Any]]:
        if not self.ledger_path.exists():
            return []
        try:
            lines = self.ledger_path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            raise DriverError("corrupted_ledger", "Run ledger cannot be read.") from exc
        records: list[dict[str, Any]] = []
        previous = None
        for sequence, line in enumerate(lines, 1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise DriverError(
                    "corrupted_ledger", "Run ledger contains invalid JSON."
                ) from exc
            if (
                not isinstance(record, dict)
                or record.get("sequence") != sequence
                or record.get("previous_record_sha256") != previous
                or record.get("record_sha256")
                != _json_digest(_ledger_hash_payload(record))
            ):
                raise DriverError(
                    "corrupted_ledger", "Run ledger hash chain is invalid."
                )
            previous = record["record_sha256"]
            records.append(record)
        return records

    def _append_state(self, state: dict[str, Any]) -> dict[str, Any]:
        previous_states = self._read_states()
        value = dict(state)
        value.update(
            {
                "schema": STATE_SCHEMA,
                "sequence": len(previous_states) + 1,
                "previous_state_sha256": previous_states[-1]["state_sha256"]
                if previous_states
                else None,
                "manifest_sha256": self._read_manifest()["manifest_sha256"],
                "recorded_at": _utc_now(),
            }
        )
        value["state_sha256"] = _json_digest(_state_hash_payload(value))
        path = self.states_dir / f"{value['sequence']:06d}.json"
        _write_new_json(path, value)
        return value

    def _read_states(self) -> list[dict[str, Any]]:
        if not self.states_dir.exists():
            return []
        files = sorted(self.states_dir.glob("*.json"))
        states: list[dict[str, Any]] = []
        previous = None
        manifest_sha = (
            self._read_manifest()["manifest_sha256"]
            if self.manifest_path.exists()
            else None
        )
        for sequence, path in enumerate(files, 1):
            state = _read_json(path, STATE_SCHEMA)
            if (
                path.name != f"{sequence:06d}.json"
                or state.get("sequence") != sequence
                or state.get("previous_state_sha256") != previous
                or state.get("manifest_sha256") != manifest_sha
                or state.get("state_sha256") != _json_digest(_state_hash_payload(state))
            ):
                raise DriverError(
                    "corrupted_state", "Supervisor state hash chain is invalid."
                )
            previous = state["state_sha256"]
            states.append(state)
        return states

    def _latest_state(self) -> dict[str, Any]:
        states = self._read_states()
        if not states:
            raise DriverError("missing_state", "Supervisor has no state record.")
        return states[-1]

    def _worker_env(self, frozen: _FrozenInputs) -> tuple[dict[str, str], list[bytes]]:
        runtime_root = self.runtime_dir.resolve()
        env: dict[str, str] = {
            "HOME": str(runtime_root / "home"),
            "XDG_CONFIG_HOME": str(runtime_root / "xdg-config"),
            "XDG_CACHE_HOME": str(runtime_root / "xdg-cache"),
            "TMPDIR": str(runtime_root / "tmp"),
            "TMP": str(runtime_root / "tmp"),
            "TEMP": str(runtime_root / "tmp"),
            "EVOSCIENTIST_DATA_DIR": str(runtime_root / "data"),
            "EVOSCIENTIST_MEMORIES_DIR": str(runtime_root / "memories"),
            "EVOSCIENTIST_SKILLS_DIR": str(runtime_root / "skills"),
            "EVOSCIENTIST_RUNS_DIR": str(runtime_root / "runs"),
            "EVOSCIENTIST_MEDIA_DIR": str(runtime_root / "media"),
            "EVOSCIENTIST_WORKSPACE_DIR": str(self.workdir),
            "PYTHONUNBUFFERED": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        for key in ("PATH", "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR"):
            value = os.environ.get(key)
            if value:
                env[key] = value
        secret_values: list[bytes] = []
        for key in frozen.runtime.get("credential_env_names", []):
            value = os.environ.get(key)
            if not value:
                raise DriverError(
                    "missing_runtime_credential",
                    "An authorized credential is unavailable.",
                )
            env[key] = value
            secret_values.append(value.encode("utf-8"))
        for path in (
            runtime_root / "home",
            runtime_root / "xdg-config",
            runtime_root / "xdg-cache",
            runtime_root / "tmp",
            runtime_root / "data",
            runtime_root / "memories",
            runtime_root / "skills",
            runtime_root / "runs",
            runtime_root / "media",
        ):
            path.mkdir(parents=True, exist_ok=True, mode=0o700)
        action_bin = runtime_root / "action-bin"
        action_bin.mkdir(parents=True, exist_ok=True, mode=0o700)
        action_sandbox = _sandboxed_argv(
            [frozen.interpreter],
            attempt_dir=self.workdir,
            repo_root=self.repo_root,
            env=env,
            allow_network=False,
            restrict_process_exec=True,
        )
        wrapper = action_bin / "python3"
        wrapper_bytes = (
            "#!/bin/sh\n"
            f"exec {shlex.quote(action_sandbox[0])} -p "
            f"{shlex.quote(action_sandbox[2])} "
            f'{shlex.quote(action_sandbox[3])} "$@"\n'
        ).encode()
        if wrapper.exists():
            if wrapper.is_symlink() or wrapper.read_bytes() != wrapper_bytes:
                raise DriverError(
                    "action_wrapper_changed",
                    "The no-network action wrapper changed between cycles.",
                )
        else:
            _write_new_bytes(wrapper, wrapper_bytes)
            wrapper.chmod(0o700)
        env["PATH"] = f"{action_bin}{os.pathsep}{env.get('PATH', '')}"
        return env, secret_values

    def _run_process(
        self,
        argv: Sequence[str],
        env: dict[str, str],
        *,
        allow_network: bool,
    ) -> _CycleResult:
        started = time.monotonic()
        sandboxed = _sandboxed_argv(
            argv,
            attempt_dir=self.attempt_dir,
            repo_root=self.repo_root,
            env=env,
            allow_network=allow_network,
        )
        try:
            process = subprocess.Popen(
                sandboxed,
                cwd=self.workdir,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )
        except OSError as exc:
            raise DriverError(
                "worker_unreachable", "Cycle worker could not be launched."
            ) from exc
        try:
            stdout, stderr = process.communicate(timeout=self.config.timeout_seconds)
            return _CycleResult(
                process.returncode,
                False,
                stdout,
                stderr,
                time.monotonic() - started,
                True,
            )
        except subprocess.TimeoutExpired:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGTERM)
            try:
                stdout, stderr = process.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(process.pid, signal.SIGKILL)
                stdout, stderr = process.communicate()
            return _CycleResult(
                process.returncode,
                True,
                stdout,
                stderr,
                time.monotonic() - started,
                True,
            )

    def _worker_argv(
        self, frozen: _FrozenInputs, request: Path, result: Path
    ) -> list[str]:
        if self.config.adapter_argv is not None:
            return [
                *self.config.adapter_argv,
                "--request",
                str(request),
                "--result",
                str(result),
            ]
        return [
            frozen.interpreter,
            str(Path(__file__).resolve()),
            "_worker",
            "--request",
            str(request),
            "--result",
            str(result),
        ]

    def _verify_worker_result(
        self,
        path: Path,
        request: dict[str, Any],
        frozen: _FrozenInputs,
    ) -> None:
        result = _read_json(path, WORKER_RESULT_SCHEMA)
        expected = {
            "attempt_id": request["attempt_id"],
            "supervisor_run_id": request["supervisor_run_id"],
            "cycle_id": request["cycle_id"],
            "thread_id": request["thread_id"],
            "request_sha256": request["request_sha256"],
            "source_commit": frozen.source_commit,
            "imported_package_path": frozen.imported_package_path,
        }
        for key, value in expected.items():
            if result.get(key) != value:
                raise DriverError(
                    "worker_identity_mismatch", f"Worker result mismatched {key}."
                )
        if request["mode"] == "resume" and result.get(
            "approved_request_digest"
        ) != request.get("approved_request_digest"):
            raise DriverError(
                "changed_approval_request",
                "Resume did not preserve the approved request digest.",
            )

    def _parse_events(
        self,
        stdout: bytes,
        *,
        state: dict[str, Any],
        frozen: _FrozenInputs,
    ) -> tuple[list[dict[str, Any]], dict[str, Any] | None, dict[str, Any]]:
        if not stdout:
            raise DriverError("blank_stdout", "Cycle produced no native event output.")
        events: list[dict[str, Any]] = []
        interrupt: dict[str, Any] | None = None
        done: dict[str, Any] | None = None
        seen_tool_ids = set(state.get("seen_tool_call_ids", []))
        cycle_tool_ids: set[str] = set()
        seen_interrupt_ids = set(state.get("seen_interrupt_ids", []))
        for raw_line in stdout.splitlines():
            if not raw_line.strip():
                raise DriverError(
                    "blank_event_line", "Native stream contains a blank event line."
                )
            try:
                event = json.loads(raw_line.decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise DriverError(
                    "malformed_json", "Native stream contains malformed JSON."
                ) from exc
            if not isinstance(event, dict) or not isinstance(event.get("type"), str):
                raise DriverError(
                    "malformed_event", "Native stream event lacks a type."
                )
            if done is not None:
                raise DriverError(
                    "reordered_event", "Native event arrived after terminal done."
                )
            event_thread = event.get("thread_id")
            if event_thread is not None and event_thread != state["thread_id"]:
                raise DriverError(
                    "event_identity_mismatch", "Native event names a different thread."
                )
            event_run = event.get("supervisor_run_id")
            if event_run is not None and event_run != state["supervisor_run_id"]:
                raise DriverError(
                    "event_identity_mismatch", "Native event names a different run."
                )
            event_type = event["type"]
            if event_type == "tool_call":
                tool_id = event.get("id")
                if not isinstance(tool_id, str) or not tool_id:
                    raise DriverError(
                        "missing_action_identity", "Tool call has no stable ID."
                    )
                if tool_id in seen_tool_ids or tool_id in cycle_tool_ids:
                    raise DriverError("replayed_event", "Tool call ID was replayed.")
                cycle_tool_ids.add(tool_id)
            elif event_type in {"interrupt", "ask_user"}:
                if interrupt is not None:
                    raise DriverError(
                        "duplicate_interrupt", "Cycle emitted more than one interrupt."
                    )
                interrupt_id = event.get("interrupt_id")
                if not isinstance(interrupt_id, str) or not interrupt_id:
                    raise DriverError(
                        "missing_interrupt_identity", "Interrupt has no stable ID."
                    )
                if interrupt_id in seen_interrupt_ids:
                    raise DriverError(
                        "replayed_interrupt", "Interrupt ID was replayed."
                    )
                interrupt = event
            elif event_type == "error":
                raise DriverError(
                    "native_error", "Daedalus emitted a native error event."
                )
            elif event_type == "done":
                done = event
            events.append(event)
        if done is None:
            raise DriverError(
                "missing_done", "Native stream ended without terminal done."
            )
        return (
            events,
            interrupt,
            {
                "seen_tool_call_ids": sorted(seen_tool_ids | cycle_tool_ids),
                "done": done,
            },
        )

    def _pending_from_interrupt(
        self, interrupt: dict[str, Any], frozen: _FrozenInputs
    ) -> dict[str, Any]:
        event_type = interrupt["type"]
        if event_type == "interrupt":
            actions = interrupt.get("action_requests")
            reviews = interrupt.get("review_configs")
            if (
                not isinstance(actions, list)
                or not actions
                or not isinstance(reviews, list)
            ):
                raise DriverError(
                    "malformed_interrupt", "Interrupt payload is incomplete."
                )
            action_ids: set[str] = set()
            for action in actions:
                if not isinstance(action, dict):
                    raise DriverError(
                        "malformed_interrupt", "Action request is not an object."
                    )
                _validate_action_request(action, frozen.allowlist, self.workdir)
                if action["id"] in action_ids:
                    raise DriverError(
                        "duplicate_action", "Interrupt repeats an action ID."
                    )
                action_ids.add(action["id"])
            payload = {
                "interrupt_id": interrupt["interrupt_id"],
                "action_requests": actions,
                "review_configs": reviews,
            }
            kind = "tool_approval"
        else:
            questions = interrupt.get("questions")
            tool_call_id = interrupt.get("tool_call_id")
            if (
                not isinstance(questions, list)
                or not questions
                or not isinstance(tool_call_id, str)
            ):
                raise DriverError(
                    "malformed_interrupt", "ask_user payload is incomplete."
                )
            payload = {
                "interrupt_id": interrupt["interrupt_id"],
                "questions": questions,
                "tool_call_id": tool_call_id,
            }
            kind = "ask_user"
        return {
            "schema": "daedalus-supervisor-pending-decision/v1",
            "kind": kind,
            "interrupt_id": interrupt["interrupt_id"],
            "request_digest": _json_digest(payload),
            "payload": payload,
        }

    def _verify_pending_record(
        self,
        state: dict[str, Any],
        frozen: _FrozenInputs,
        request_digest: str,
    ) -> dict[str, Any]:
        pending_path = self.decisions_dir / f"pending-{state['cycle_count']:03d}.json"
        pending = _read_json(pending_path, "daedalus-supervisor-pending-decision/v1")
        payload = pending.get("payload")
        expected_identity = {
            "attempt_id": state["attempt_id"],
            "supervisor_run_id": state["supervisor_run_id"],
            "thread_id": state["thread_id"],
            "cycle_id": state.get("last_cycle_id"),
            "kind": state["pending_kind"],
            "request_digest": request_digest,
        }
        if not isinstance(payload, dict) or any(
            pending.get(field) != expected
            for field, expected in expected_identity.items()
        ):
            raise DriverError(
                "corrupted_pending_record", "Pending decision identity changed."
            )
        if (
            _json_digest(payload) != request_digest
            or pending.get("interrupt_id") != payload.get("interrupt_id")
            or pending["interrupt_id"] not in state.get("seen_interrupt_ids", [])
        ):
            raise DriverError(
                "corrupted_pending_record", "Pending decision payload changed."
            )
        if state["pending_kind"] == "tool_approval":
            actions = payload.get("action_requests")
            if not isinstance(actions, list) or not actions:
                raise DriverError(
                    "corrupted_pending_record", "Pending approval actions are missing."
                )
            for action in actions:
                if not isinstance(action, dict):
                    raise DriverError(
                        "corrupted_pending_record", "Pending approval action changed."
                    )
                _validate_action_request(action, frozen.allowlist, self.workdir)
        else:
            questions = payload.get("questions")
            if (
                not isinstance(questions, list)
                or not questions
                or any(
                    not isinstance(question, dict)
                    or not isinstance(question.get("question"), str)
                    or not question["question"].strip()
                    for question in questions
                )
            ):
                raise DriverError(
                    "corrupted_pending_record", "Pending questions are malformed."
                )
        return pending

    def _check_workspace_changes(
        self,
        before: dict[str, dict[str, Any]],
        after: dict[str, dict[str, Any]],
        frozen: _FrozenInputs,
    ) -> None:
        changed = {
            path
            for path in set(before) | set(after)
            if before.get(path) != after.get(path)
        }
        allowed = set(frozen.allowlist.get("allowed_artifact_paths", []))
        undeclared = sorted(changed - allowed)
        deleted = sorted(
            path for path in changed if path in before and path not in after
        )
        if undeclared or deleted:
            raise DriverError(
                "outside_allowlist_write",
                "Workspace changed outside the artifact allowlist.",
            )

    def _required_artifacts(self, frozen: _FrozenInputs) -> list[str]:
        return [
            _safe_relative_path(item.get("path"), field="expected artifact")
            for item in frozen.packet.get("expected_artifacts", [])
            if isinstance(item, dict)
            and item.get("required") is True
            and item.get("producer") == "daedalus"
            and item.get("role") not in {"native_event_stream", "terminal_status"}
        ]

    def _record_terminal(
        self,
        state: dict[str, Any],
        *,
        outcome: str,
        failure_code: str | None = None,
        stop_reason: str | None = None,
        exit_code: int | None = None,
        terminal_event_observed: bool = False,
    ) -> dict[str, Any]:
        terminal = {
            **state,
            "outcome": outcome,
            "failure_code": failure_code,
            "stop_reason": stop_reason,
            "pending_request_digest": None,
            "pending_kind": None,
            "exit_code": exit_code,
            "terminal_event_observed": terminal_event_observed,
            "monotonic_finished_seconds": time.monotonic(),
        }
        terminal = self._append_state(terminal)
        status = {
            "schema": STATUS_SCHEMA,
            "packet_id": terminal["packet_id"],
            "attempt_id": terminal["attempt_id"],
            "run_id": terminal["supervisor_run_id"],
            "run_id_authority": "archimedes_supervisor",
            "supervisor_run_id": terminal["supervisor_run_id"],
            "native_run_id": None,
            "native_run_id_status": "not_exposed_by_local_stream_gateway",
            "thread_id": terminal["thread_id"],
            "outcome": outcome,
            "failure_code": failure_code,
            "stop_reason": stop_reason,
            "exit_code": exit_code,
            "terminal_event_observed": terminal_event_observed,
            "declared_success": outcome == "completed",
            "monotonic_started_seconds": terminal["monotonic_started_seconds"],
            "monotonic_finished_seconds": terminal["monotonic_finished_seconds"],
            "state_sha256": terminal["state_sha256"],
            "recorded_at": _utc_now(),
        }
        _write_new_json(self.status_path, status)
        self._append_ledger(
            entry_type="terminal",
            stage="completion" if outcome == "completed" else "stop",
            summary=f"Attempt ended with outcome {outcome}.",
            evidence_ref="status.json",
            extra={"failure_code": failure_code, "stop_reason": stop_reason},
        )
        return self._result_view(terminal)

    @staticmethod
    def _result_view(state: dict[str, Any]) -> dict[str, Any]:
        keys = (
            "packet_id",
            "attempt_id",
            "supervisor_run_id",
            "native_run_id",
            "thread_id",
            "outcome",
            "pending_kind",
            "pending_request_digest",
            "failure_code",
            "stop_reason",
            "cycle_count",
        )
        return {key: state.get(key) for key in keys}

    def _run_cycle(
        self,
        *,
        state: dict[str, Any],
        frozen: _FrozenInputs,
        mode: str,
        resume_payload: dict[str, Any] | None = None,
        approved_request_digest: str | None = None,
    ) -> dict[str, Any]:
        if state["cycle_count"] >= self.config.max_cycles:
            return self._record_terminal(
                state, outcome="failed", failure_code="maximum_cycles_exceeded"
            )
        cycle_number = state["cycle_count"] + 1
        cycle_id = f"cycle-{cycle_number:03d}"
        request: dict[str, Any] = {
            "schema": CYCLE_REQUEST_SCHEMA,
            "mode": mode,
            "attempt_id": state["attempt_id"],
            "supervisor_run_id": state["supervisor_run_id"],
            "native_run_id": None,
            "cycle_id": cycle_id,
            "thread_id": state["thread_id"],
            "packet_id": state["packet_id"],
            "workdir": str(self.workdir),
            "runtime_config_path": str(self.config.runtime_config_path.resolve()),
            "runtime_root": str(self.runtime_dir.resolve()),
            "checkpoint_path": str((self.runtime_dir / "checkpoints.db").resolve()),
            "expected_identity": {
                "source_commit": frozen.source_commit,
                "imported_package_path": frozen.imported_package_path,
            },
            "prompt": frozen.prompt if mode == "start" else None,
            "resume_payload": resume_payload,
            "approved_request_digest": approved_request_digest,
        }
        request["request_sha256"] = _json_digest(request)
        request_path = self.cycles_dir / f"cycle-request-{cycle_number:03d}.json"
        result_path = self.cycles_dir / f"worker-result-{cycle_number:03d}.json"
        stdout_path = self.cycles_dir / f"native-events-{cycle_number:03d}.jsonl"
        stderr_path = self.cycles_dir / f"stderr-{cycle_number:03d}.log"
        _write_new_json(request_path, request)
        self._append_ledger(
            entry_type="operator_action",
            stage="resume" if mode == "resume" else "launch",
            summary=f"Started supervised {mode} cycle {cycle_id}.",
            evidence_ref=f"cycles/{request_path.name}",
            extra={"cycle_id": cycle_id, "request_sha256": request["request_sha256"]},
        )

        state = {
            **state,
            "cycle_count": cycle_number,
            "last_cycle_id": cycle_id,
            "last_exit_code": None,
            "last_elapsed_seconds": None,
        }
        try:
            before = _snapshot_tree(self.workdir)
            env, secret_values = self._worker_env(frozen)
            process_result = self._run_process(
                self._worker_argv(frozen, request_path, result_path),
                env,
                allow_network=(
                    self.config.adapter_argv is None
                    and frozen.authorization.get("paid_provider_activation_authorized")
                    is True
                ),
            )
        except DriverError as exc:
            return self._record_terminal(
                state,
                outcome="failed",
                failure_code=exc.code,
                terminal_event_observed=False,
            )
        stdout, stdout_secret = _sanitize_capture(process_result.stdout, secret_values)
        stderr, stderr_secret = _sanitize_capture(process_result.stderr, secret_values)
        _write_new_bytes(stdout_path, stdout)
        _write_new_bytes(stderr_path, stderr)
        _append_bytes(self.native_events_path, stdout)
        _append_bytes(self.stderr_path, stderr)
        state = {
            **state,
            "last_exit_code": process_result.exit_code,
            "last_elapsed_seconds": process_result.elapsed_seconds,
        }
        try:
            if stdout_secret or stderr_secret:
                raise DriverError(
                    "secret_detected",
                    "Sensitive material was redacted from cycle output.",
                )
            if process_result.timed_out:
                raise DriverError("timeout", "Cycle exceeded the frozen timeout.")
            if process_result.exit_code != 0:
                if process_result.containment_active and _is_containment_denial(stderr):
                    raise DriverError(
                        "containment_violation",
                        "The worker attempted a denied filesystem or network operation.",
                    )
                raise DriverError(
                    "nonzero_exit", "Cycle worker returned a nonzero exit status."
                )
            self._verify_worker_result(result_path, request, frozen)
            events, interrupt, parsed = self._parse_events(
                stdout, state=state, frozen=frozen
            )
            after = _snapshot_tree(self.workdir)
            self._check_workspace_changes(before, after, frozen)
            state["seen_tool_call_ids"] = parsed["seen_tool_call_ids"]
            state["terminal_event_observed"] = True
            self._append_ledger(
                entry_type="daedalus_event",
                stage="native_stream",
                summary=f"Preserved {len(events)} native events for {cycle_id}.",
                evidence_ref=f"cycles/{stdout_path.name}",
                extra={"cycle_id": cycle_id, "event_count": len(events)},
            )
            if interrupt is not None:
                pending = self._pending_from_interrupt(interrupt, frozen)
                seen_interrupts = set(state.get("seen_interrupt_ids", []))
                seen_interrupts.add(pending["interrupt_id"])
                state.update(
                    {
                        "outcome": "awaiting_approval"
                        if pending["kind"] == "tool_approval"
                        else "awaiting_user_input",
                        "pending_kind": pending["kind"],
                        "pending_request_digest": pending["request_digest"],
                        "seen_interrupt_ids": sorted(seen_interrupts),
                    }
                )
                pending.update(
                    {
                        "attempt_id": state["attempt_id"],
                        "supervisor_run_id": state["supervisor_run_id"],
                        "thread_id": state["thread_id"],
                        "cycle_id": cycle_id,
                        "recorded_at": _utc_now(),
                    }
                )
                pending_path = self.decisions_dir / f"pending-{cycle_number:03d}.json"
                _write_new_json(pending_path, pending)
                state = self._append_state(state)
                self._append_ledger(
                    entry_type="approval_request",
                    stage="human_gate",
                    summary="Stopped at an explicit human decision gate.",
                    evidence_ref=f"decisions/{pending_path.name}",
                    extra={
                        "kind": pending["kind"],
                        "request_digest": pending["request_digest"],
                    },
                )
                return self._result_view(state)

            done = parsed["done"]
            missing = [
                path
                for path in self._required_artifacts(frozen)
                if not (self.workdir / path).is_file()
                or (self.workdir / path).stat().st_size == 0
            ]
            response = done.get("response", "") or done.get("content", "") or ""
            if missing and not response:
                raise DriverError(
                    "silent_success",
                    "Done event had no response or required artifacts.",
                )
            if missing:
                raise DriverError(
                    "missing_artifact",
                    "Required Daedalus artifact is missing or empty.",
                )
            return self._record_terminal(
                state,
                outcome="completed",
                exit_code=process_result.exit_code,
                terminal_event_observed=True,
            )
        except DriverError as exc:
            return self._record_terminal(
                state,
                outcome="failed",
                failure_code=exc.code,
                exit_code=process_result.exit_code,
                terminal_event_observed=False,
            )

    def start(self) -> dict[str, Any]:
        """Freeze inputs, create immutable identity, and run the first cycle."""

        with self._lock():
            if self.manifest_path.exists():
                raise DriverError("attempt_exists", "Attempt already has a manifest.")
            frozen = self._freeze_inputs()
            input_paths = self._preserve_frozen_inputs()
            self.cycles_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
            self.decisions_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
            self.states_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
            supervisor_run_id = str(uuid.uuid4())
            thread_id = str(uuid.uuid4())
            monotonic_started = time.monotonic()
            manifest: dict[str, Any] = {
                "schema": ATTEMPT_SCHEMA,
                "repo_root": str(self.repo_root),
                "packet_id": frozen.packet_id,
                "attempt_id": self.config.attempt_id,
                "run_id": supervisor_run_id,
                "run_id_authority": "archimedes_supervisor",
                "supervisor_run_id": supervisor_run_id,
                "native_run_id": None,
                "native_run_id_status": "not_exposed_by_local_stream_gateway",
                "thread_id": thread_id,
                "thread_id_authority": "exact_local_gateway_run_request",
                "source_commit": frozen.source_commit,
                "supervisor_source_path": str(Path(__file__).resolve()),
                "imported_package_path": frozen.imported_package_path,
                "execution_mode": (
                    "deterministic_adapter"
                    if self.config.adapter_argv is not None
                    else "production"
                ),
                "evidence_ceiling": (
                    "E2" if self.config.adapter_argv is not None else "E3"
                ),
                "launcher": str(self.config.launcher.resolve()),
                "interpreter": frozen.interpreter,
                "workdir": str(self.workdir),
                "workdir_kind": "data_only",
                "native_events_path": "native-events.jsonl",
                "stderr_path": "stderr.log",
                "status_path": "status.json",
                "input_sha256": frozen.digests,
                "input_paths": input_paths,
                "interface": OFFICIAL_INTERFACE,
                "safe_defaults": dict(SAFE_DEFAULTS),
                "maximum_cycles": self.config.max_cycles,
                "timeout_seconds": self.config.timeout_seconds,
                "monotonic_started_seconds": monotonic_started,
                "monotonic_finished_seconds": None,
                "exit_code": None,
                "terminal_event_observed": False,
                "created_at": _utc_now(),
            }
            manifest["manifest_sha256"] = _json_digest(manifest)
            _write_new_json(self.manifest_path, manifest)
            initial = self._append_state(
                {
                    "packet_id": frozen.packet_id,
                    "attempt_id": self.config.attempt_id,
                    "supervisor_run_id": supervisor_run_id,
                    "native_run_id": None,
                    "thread_id": thread_id,
                    "outcome": "running",
                    "pending_kind": None,
                    "pending_request_digest": None,
                    "failure_code": None,
                    "stop_reason": None,
                    "cycle_count": 0,
                    "monotonic_started_seconds": monotonic_started,
                    "seen_interrupt_ids": [],
                    "seen_tool_call_ids": [],
                }
            )
            self._append_ledger(
                entry_type="preflight",
                stage="preflight",
                summary="Accepted exact ready preflight and frozen attempt identity.",
                evidence_ref="attempt-manifest.json",
                extra={"preflight_sha256": frozen.digests["preflight"]},
            )
            return self._run_cycle(state=initial, frozen=frozen, mode="start")

    def inspect(self) -> dict[str, Any]:
        """Verify immutable identity and hash chains without launching a cycle."""

        with self._lock():
            manifest = self._read_manifest()
            input_paths = manifest.get("input_paths", {})
            expected = manifest.get("input_sha256", {})
            if not isinstance(input_paths, dict) or not isinstance(expected, dict):
                raise DriverError(
                    "corrupted_manifest", "Attempt manifest omits frozen inputs."
                )
            current = {
                name: _file_digest(Path(str(path)))
                for name, path in input_paths.items()
            }
            if current != expected:
                raise DriverError(
                    "frozen_input_changed",
                    "A frozen attempt input changed after launch.",
                )
            if manifest.get("supervisor_source_path") != str(
                Path(__file__).resolve()
            ) or _file_digest(Path(__file__).resolve()) != expected.get(
                "supervisor_source"
            ):
                raise DriverError(
                    "supervisor_source_changed",
                    "The active supervisor source differs from the frozen attempt.",
                )
            self._read_ledger()
            return self._result_view(self._latest_state())

    def _verify_frozen_inputs(self, manifest: dict[str, Any]) -> _FrozenInputs:
        frozen = self._freeze_inputs()
        expected_digests = manifest.get("input_sha256")
        if (
            not isinstance(expected_digests, dict)
            or set(expected_digests) != set(frozen.digests)
            or any(not _is_sha256(value) for value in expected_digests.values())
        ):
            raise DriverError(
                "corrupted_manifest", "Attempt manifest input digests are invalid."
            )
        if manifest.get("supervisor_source_path") != str(
            Path(__file__).resolve()
        ) or frozen.digests.get("supervisor_source") != expected_digests.get(
            "supervisor_source"
        ):
            raise DriverError(
                "supervisor_source_changed",
                "The active supervisor source differs from the frozen attempt.",
            )
        if frozen.digests != expected_digests:
            raise DriverError(
                "frozen_input_changed", "A frozen attempt input changed after launch."
            )
        if (
            frozen.packet_id != manifest.get("packet_id")
            or frozen.source_commit != manifest.get("source_commit")
            or frozen.imported_package_path != manifest.get("imported_package_path")
        ):
            raise DriverError(
                "frozen_identity_changed",
                "Frozen attempt identity changed after launch.",
            )
        return frozen

    def decide(
        self,
        *,
        decision: str,
        request_digest: str,
        operator: str,
        answers: list[str] | None = None,
    ) -> dict[str, Any]:
        """Record one explicit decision and optionally resume the exact thread."""

        with self._lock():
            manifest = self._read_manifest()
            frozen = self._verify_frozen_inputs(manifest)
            state = self._latest_state()
            self._read_ledger()
            expected_outcomes = {"awaiting_approval", "awaiting_user_input"}
            if state.get("outcome") not in expected_outcomes:
                raise DriverError(
                    "not_awaiting_decision", "Attempt has no pending human decision."
                )
            if request_digest != state.get("pending_request_digest"):
                raise DriverError(
                    "decision_digest_mismatch",
                    "Decision does not match the pending request.",
                )
            pending = self._verify_pending_record(state, frozen, request_digest)
            if not isinstance(operator, str) or not operator.strip():
                raise DriverError(
                    "missing_operator", "Decision requires an operator identity."
                )
            allowed = (
                {"approve", "reject"}
                if state["pending_kind"] == "tool_approval"
                else {"answer", "reject"}
            )
            if decision not in allowed:
                raise DriverError(
                    "invalid_decision", "Decision is invalid for the pending request."
                )
            resume_payload: dict[str, Any] | None = None
            if decision == "approve":
                actions = pending["payload"]["action_requests"]
                resume_payload = {"decisions": [{"type": "approve"} for _ in actions]}
            elif decision == "answer":
                questions = pending["payload"]["questions"]
                if (
                    not isinstance(answers, list)
                    or len(answers) != len(questions)
                    or any(not isinstance(item, str) for item in answers)
                    or any(
                        question.get("required", True) is not False
                        and not answer.strip()
                        for question, answer in zip(questions, answers, strict=True)
                    )
                ):
                    raise DriverError(
                        "invalid_answers",
                        "ask_user requires one valid string answer per question.",
                    )
                resume_payload = {"answers": answers, "status": "answered"}
            decision_record = {
                "schema": "daedalus-supervisor-decision/v1",
                "attempt_id": state["attempt_id"],
                "supervisor_run_id": state["supervisor_run_id"],
                "thread_id": state["thread_id"],
                "request_digest": request_digest,
                "decision": decision,
                "operator": operator,
                "answers": answers if decision == "answer" else None,
                "recorded_at": _utc_now(),
            }
            decision_path = (
                self.decisions_dir / f"decision-{state['cycle_count']:03d}.json"
            )
            _write_new_json(decision_path, decision_record)
            self._append_ledger(
                entry_type="operator_decision",
                stage="human_gate",
                summary=f"Recorded explicit operator decision: {decision}.",
                evidence_ref=f"decisions/{decision_path.name}",
                extra={"request_digest": request_digest, "operator": operator},
            )
            if decision == "reject":
                return self._record_terminal(
                    state,
                    outcome="stopped",
                    stop_reason="operator_rejected",
                    terminal_event_observed=True,
                )
            resumed = {
                **state,
                "outcome": "running",
                "pending_kind": None,
                "pending_request_digest": None,
            }
            resumed = self._append_state(resumed)
            return self._run_cycle(
                state=resumed,
                frozen=frozen,
                mode="resume",
                resume_payload=resume_payload,
                approved_request_digest=request_digest,
            )

    def cancel(
        self, *, operator: str, reason: str = "operator_cancelled"
    ) -> dict[str, Any]:
        """Record an explicit operator cancellation without issuing a resume."""

        with self._lock():
            manifest = self._read_manifest()
            self._verify_frozen_inputs(manifest)
            state = self._latest_state()
            if state.get("outcome") in {"completed", "failed", "stopped"}:
                raise DriverError(
                    "attempt_terminal", "A terminal attempt cannot be cancelled again."
                )
            if not isinstance(operator, str) or not operator.strip():
                raise DriverError(
                    "missing_operator", "Cancellation requires an operator identity."
                )
            if not isinstance(reason, str) or not reason.strip():
                raise DriverError(
                    "missing_stop_reason", "Cancellation requires a stop reason."
                )
            record = {
                "schema": "daedalus-supervisor-cancellation/v1",
                "attempt_id": state["attempt_id"],
                "supervisor_run_id": state["supervisor_run_id"],
                "thread_id": state["thread_id"],
                "operator": operator,
                "reason": reason,
                "recorded_at": _utc_now(),
            }
            path = self.decisions_dir / f"cancellation-{state['cycle_count']:03d}.json"
            _write_new_json(path, record)
            self._append_ledger(
                entry_type="operator_decision",
                stage="human_gate",
                summary="Recorded explicit operator cancellation.",
                evidence_ref=f"decisions/{path.name}",
                extra={"operator": operator, "reason": reason},
            )
            return self._record_terminal(
                state,
                outcome="stopped",
                stop_reason=reason,
                terminal_event_observed=bool(state.get("terminal_event_observed")),
            )


async def _run_isolated_worker(
    request_path: Path,
    result_path: Path,
) -> None:
    """Execute one official local-gateway cycle inside the isolated worker."""

    request = _read_json(request_path, CYCLE_REQUEST_SCHEMA)
    claimed_digest = request.get("request_sha256")
    digest_payload = {
        key: value for key, value in request.items() if key != "request_sha256"
    }
    if (
        not isinstance(claimed_digest, str)
        or _json_digest(digest_payload) != claimed_digest
    ):
        raise DriverError(
            "corrupted_worker_request", "Worker request digest does not match."
        )
    _assert_worker_isolation(request)
    runtime = _read_json(Path(str(request["runtime_config_path"])), RUNTIME_SCHEMA)
    if runtime.get("packet_id") != request.get("packet_id"):
        raise DriverError(
            "packet_identity_mismatch", "Worker runtime names a different packet."
        )
    _validate_runtime_config(runtime, adapter=False)

    from EvoScientist import EvoScientistConfig, create_cli_agent
    from EvoScientist.cli._constants import build_metadata
    from EvoScientist.config import apply_config_to_env
    from EvoScientist.gateway import GraphTarget, LocalGraphGateway, RunRequest
    from EvoScientist.llm import get_chat_model
    from EvoScientist.sessions import PruningCheckpointer
    from EvoScientist.stream.json_sink import (
        redirect_console_to_stderr,
        write_events_as_json,
    )

    redirect_console_to_stderr()
    workdir = Path(str(request["workdir"])).resolve()
    config = EvoScientistConfig(**_worker_config_values(runtime, workdir))
    if config.auto_approve or config.auto_mode or config.dangerous_mode:
        raise DriverError(
            "unsafe_effective_config", "Worker safety settings did not remain disabled."
        )
    apply_config_to_env(config)
    chat_model = get_chat_model(config.model, provider=config.provider)
    _scrub_declared_credentials(runtime)
    message = _build_graph_run_message(request)
    checkpoint_path = Path(str(request["checkpoint_path"])).resolve()
    if not _inside(checkpoint_path, Path(str(request["runtime_root"]))):
        raise DriverError(
            "worker_isolation_failure", "Checkpoint path escapes runtime isolation."
        )

    async with PruningCheckpointer.from_conn_string_with_keep(
        str(checkpoint_path), keep_per_ns=0
    ) as checkpointer:
        await checkpointer.setup()
        agent = create_cli_agent(
            workspace_dir=str(workdir),
            checkpointer=checkpointer,
            config=config,
            chat_model=chat_model,
        )
        gateway = LocalGraphGateway()
        metadata = build_metadata(str(workdir), config.model)
        metadata.update(
            {
                "supervisor_run_id": request["supervisor_run_id"],
                "supervisor_cycle_id": request["cycle_id"],
                "attempt_id": request["attempt_id"],
                "packet_id": request["packet_id"],
            }
        )
        run_request = RunRequest(
            message=message,
            thread_id=str(request["thread_id"]),
            metadata=metadata,
            target=GraphTarget(local_graph=agent, workspace_dir=str(workdir)),
        )

        async def _strict_events():
            async for event in gateway.stream_events(run_request):
                _canonical_bytes(event)
                yield event

        try:
            await write_events_as_json(_strict_events(), sys.stdout)
        finally:
            from EvoScientist.middleware.code_interpreter import (
                aclose_code_interpreters,
            )

            await aclose_code_interpreters()

    import EvoScientist

    imported_path = str(Path(EvoScientist.__file__).resolve())
    expected_identity = request.get("expected_identity", {})
    if imported_path != expected_identity.get("imported_package_path"):
        raise DriverError(
            "worker_identity_mismatch", "Worker imported an unexpected package path."
        )
    result = {
        "schema": WORKER_RESULT_SCHEMA,
        "attempt_id": request["attempt_id"],
        "supervisor_run_id": request["supervisor_run_id"],
        "cycle_id": request["cycle_id"],
        "thread_id": request["thread_id"],
        "request_sha256": request["request_sha256"],
        "source_commit": expected_identity["source_commit"],
        "imported_package_path": imported_path,
        "approved_request_digest": request.get("approved_request_digest"),
    }
    _write_new_json(result_path, result)


def _worker_cli(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        import asyncio

        asyncio.run(_run_isolated_worker(args.request, args.result))
    except DriverError as exc:
        print(
            json.dumps(
                {
                    "schema": "daedalus-supervisor-worker-error/v1",
                    "code": exc.code,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1
    except Exception:
        print(
            json.dumps(
                {
                    "schema": "daedalus-supervisor-worker-error/v1",
                    "code": "worker_failure",
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1
    return 0


def self_check() -> dict[str, Any]:
    """Return the deterministic, model-free supervisor contract report."""

    containment = _probe_containment()
    containment_available = containment.get("available") is True
    containment_ready = containment_available and all(
        containment.get(field) is True
        for field in (
            "attempt_only_writes",
            "network_denied_without_provider_authorization",
            "tool_network_denied",
            "tool_private_roots_denied",
            "tool_workspace_only_writes",
            "tool_undeclared_subprocesses_denied",
        )
    )
    blocking_reasons = [PRODUCTION_BLOCKER_CODE, COST_BLOCKER_CODE]
    if not containment_available:
        blocking_reasons.append("host_containment_unavailable")
    elif not containment_ready:
        blocking_reasons.append("containment_probe_failed")
    return {
        "schema": DRIVER_SCHEMA,
        "status": "blocked",
        "adapter_status": "ready" if containment_ready else "blocked",
        "production_status": "blocked",
        "interface": OFFICIAL_INTERFACE,
        "safe_defaults": dict(SAFE_DEFAULTS),
        "containment": containment,
        "human_gate": {
            "main_agent_execute_interrupts": True,
            "synchronous_subagent_execute_interrupts": False,
            "all_executable_actions_human_gated": False,
        },
        "blocking_reasons": blocking_reasons,
        "blocking_evidence": {
            "main_agent_factory": "EvoScientist.EvoScientist.create_cli_agent",
            "subagent_middleware": (
                "EvoScientist.EvoScientist._inject_subagent_middleware"
            ),
            "async_disable_scope": (
                "EvoScientist.EvoScientist._maybe_swap_async_subagents"
            ),
            "paid_provider_cost_enforcement": "unavailable",
        },
        "same_snapshot": {
            "supervisor_source_frozen": True,
            "cycle_worker_source_frozen": True,
            "production_git_identity_rechecked": True,
        },
        "self_check": {
            "deterministic": True,
            "containment_probe_executed": containment_available,
            "model_loaded": False,
            "service_started": False,
            "provider_activated": False,
        },
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="Print the deterministic driver contract without loading Daedalus.",
    )
    parser.add_argument("--pretty", action="store_true")
    operations = parser.add_subparsers(dest="operation")

    start = operations.add_parser("start", help="Start one frozen supervised attempt.")
    start.add_argument("--repo-root", type=Path, required=True)
    start.add_argument("--packet", type=Path, required=True)
    start.add_argument("--authorization", type=Path, required=True)
    start.add_argument("--allowlist", type=Path, required=True)
    start.add_argument("--preflight", type=Path, required=True)
    start.add_argument("--runtime-config", type=Path, required=True)
    start.add_argument("--prompt-file", type=Path, required=True)
    start.add_argument("--attempt-dir", type=Path, required=True)
    start.add_argument("--workdir", type=Path, required=True)
    start.add_argument("--launcher", type=Path, required=True)
    start.add_argument("--attempt-id", required=True)
    start.add_argument("--timeout-seconds", type=float, required=True)
    start.add_argument("--max-cycles", type=int, default=8)

    decide = operations.add_parser("decide", help="Record one explicit human decision.")
    decide.add_argument("--attempt-dir", type=Path, required=True)
    decide.add_argument(
        "--decision", choices=("approve", "reject", "answer"), required=True
    )
    decide.add_argument("--request-digest", required=True)
    decide.add_argument("--operator", required=True)
    decide.add_argument("--answers-file", type=Path)

    cancel = operations.add_parser("cancel", help="Stop a nonterminal attempt.")
    cancel.add_argument("--attempt-dir", type=Path, required=True)
    cancel.add_argument("--operator", required=True)
    cancel.add_argument("--reason", default="operator_cancelled")

    inspect_parser = operations.add_parser(
        "inspect", help="Verify and print the current attempt state."
    )
    inspect_parser.add_argument("--attempt-dir", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    effective_argv = list(argv) if argv is not None else sys.argv[1:]
    if effective_argv and effective_argv[0] == "_worker":
        return _worker_cli(effective_argv[1:])
    parser = _parser()
    args = parser.parse_args(effective_argv)
    if args.self_check:
        print(
            json.dumps(self_check(), indent=2 if args.pretty else None, sort_keys=True)
        )
        return 0
    if args.operation is None:
        parser.error("one operation is required")
    try:
        if args.operation == "start":
            if args.timeout_seconds <= 0 or args.max_cycles <= 0:
                raise DriverError(
                    "invalid_limits", "Timeout and max cycles must be positive."
                )
            supervisor = SupervisedResumeDriver(
                SupervisorConfig(
                    repo_root=args.repo_root,
                    packet_path=args.packet,
                    authorization_path=args.authorization,
                    allowlist_path=args.allowlist,
                    preflight_path=args.preflight,
                    runtime_config_path=args.runtime_config,
                    prompt_path=args.prompt_file,
                    attempt_dir=args.attempt_dir,
                    workdir=args.workdir,
                    launcher=args.launcher,
                    attempt_id=args.attempt_id,
                    timeout_seconds=args.timeout_seconds,
                    max_cycles=args.max_cycles,
                )
            )
            result = supervisor.start()
        else:
            supervisor = SupervisedResumeDriver.from_attempt(args.attempt_dir)
            if args.operation == "inspect":
                result = supervisor.inspect()
            elif args.operation == "cancel":
                result = supervisor.cancel(operator=args.operator, reason=args.reason)
            else:
                answers = None
                if args.answers_file is not None:
                    try:
                        answers = json.loads(
                            args.answers_file.read_text(encoding="utf-8")
                        )
                    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                        raise DriverError(
                            "invalid_answers", "Answers file is invalid JSON."
                        ) from exc
                    if not isinstance(answers, list):
                        raise DriverError(
                            "invalid_answers", "Answers file must contain a JSON list."
                        )
                result = supervisor.decide(
                    decision=args.decision,
                    request_digest=args.request_digest,
                    operator=args.operator,
                    answers=answers,
                )
    except DriverError as exc:
        print(
            json.dumps(
                {
                    "schema": "daedalus-supervisor-cli-error/v1",
                    "code": exc.code,
                    "detail": exc.detail,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    return 1 if result.get("outcome") == "failed" else 0


if __name__ == "__main__":
    sys.exit(main())
