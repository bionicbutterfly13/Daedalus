import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = (
    ROOT
    / "skills"
    / "supervising-daedalus-mock-study-runs"
    / "scripts"
    / "drive_stream_json_resume.py"
)
FAKE_CYCLE = Path(__file__).parent / "fixtures" / "fake_daedalus_cycle.py"


def _load_driver():
    spec = importlib.util.spec_from_file_location("daedalus_resume_driver", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, value: dict) -> Path:
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
    return path


def _build_case(
    driver, tmp_path, *, scenario="happy", timeout_seconds=2.0, max_cycles=3
):
    attempt_dir = tmp_path / "attempt-001"
    workdir = attempt_dir / "workspace"
    workdir.mkdir(parents=True)
    (workdir / "analysis.py").write_text(
        "from pathlib import Path\nPath('report.json').write_text('{}')\n",
        encoding="utf-8",
    )

    packet = _write_json(
        tmp_path / "study-packet.json",
        {
            "schema": "daedalus-mock-study-packet/v1",
            "packet_id": "synthetic-driver-001",
            "synthetic_study": True,
            "objective": "Run the deterministic supervised-driver fixture.",
            "expected_artifacts": [
                {
                    "path": "report.json",
                    "producer": "daedalus",
                    "required": True,
                }
            ],
            "prohibited_operations": [
                "access_private_memory",
                "activate_paid_provider",
                "publish",
                "transfer_artifacts",
            ],
            "provider_cost_boundary": {
                "allowed_providers": [],
                "paid_providers_authorized": False,
                "maximum_cost_usd": 0,
            },
            "retry_timeout_stop_policy": {
                "maximum_attempts": 1,
                "stage_timeout_seconds": timeout_seconds,
                "stop_on_silent_success": True,
            },
        },
    )
    authorization = _write_json(
        tmp_path / "authorization-record.json",
        {
            "schema": "daedalus-mock-study-authorization/v1",
            "packet_id": "synthetic-driver-001",
            "study_execution_authorized": True,
            "tool_action_approval_policy": "separate_per_interrupt_exact_digest",
            "tool_action_preapproval_authorized": False,
            "paid_provider_activation_authorized": False,
            "private_memory_access_authorized": False,
            "private_research_data_access_authorized": False,
            "artifact_transfer_authorized": False,
            "publication_authorized": False,
            "evoscientist_core_modification_authorized": False,
            "approval_evidence": "fixture-human-approval-001",
        },
    )
    allowlist = _write_json(
        tmp_path / "execution-allowlist.json",
        {
            "schema": "daedalus-supervisor-allowlist/v1",
            "packet_id": "synthetic-driver-001",
            "allowed_actions": [
                {
                    "name": "execute",
                    "args": {"command": "python3 analysis.py"},
                    "argv": ["python3", "analysis.py"],
                    "path_argument_indexes": [1],
                    "path_sha256": {
                        "1": hashlib.sha256(
                            (workdir / "analysis.py").read_bytes()
                        ).hexdigest()
                    },
                }
            ],
            "allowed_artifact_paths": ["report.json"],
            "network_operations_allowed": False,
            "private_memory_allowed": False,
            "transfer_allowed": False,
            "publication_allowed": False,
        },
    )
    preflight = _write_json(
        tmp_path / "preflight.json",
        {
            "schema": "daedalus-capability-preflight/v1",
            "status": "ready",
            "blocking_check_ids": [],
            "checks": [
                {
                    "check_id": "workdir.data_only",
                    "status": "pass",
                    "blocking": False,
                    "evidence": {"workdir": str(workdir.resolve())},
                },
                {
                    "check_id": "launcher.resolved",
                    "status": "pass",
                    "blocking": False,
                    "evidence": {"launcher": str(Path(sys.executable).resolve())},
                },
                {
                    "check_id": "launcher.interpreter",
                    "status": "pass",
                    "blocking": False,
                    "evidence": {"interpreter": str(Path(sys.executable).resolve())},
                },
                {
                    "check_id": "launcher.import_identity",
                    "status": "pass",
                    "blocking": False,
                    "evidence": {
                        "imported": "/frozen/EvoScientist/__init__.py",
                        "expected": "/frozen/EvoScientist/__init__.py",
                    },
                },
                {
                    "check_id": "source.git_identity",
                    "status": "pass",
                    "blocking": False,
                    "evidence": {"commit": "source-commit-001"},
                },
                {
                    "check_id": "runtime.supervised_resume_driver",
                    "status": "pass",
                    "blocking": False,
                    "evidence": {"contract_status": "ready"},
                },
            ],
        },
    )
    runtime_config = _write_json(
        tmp_path / "runtime-config.json",
        {
            "schema": "daedalus-supervisor-runtime/v1",
            "packet_id": "synthetic-driver-001",
            "provider": "fixture",
            "model": "fixture",
            "credential_env_names": [],
            "config_overrides": {},
        },
    )
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Use only the frozen synthetic fixture.", encoding="utf-8")

    config = driver.SupervisorConfig(
        repo_root=ROOT,
        packet_path=packet,
        authorization_path=authorization,
        allowlist_path=allowlist,
        preflight_path=preflight,
        runtime_config_path=runtime_config,
        prompt_path=prompt,
        attempt_dir=attempt_dir,
        workdir=workdir,
        launcher=Path(sys.executable),
        attempt_id="attempt-001",
        timeout_seconds=timeout_seconds,
        max_cycles=max_cycles,
        adapter_argv=(
            sys.executable,
            str(FAKE_CYCLE),
            "--scenario",
            scenario,
        ),
    )
    return driver.SupervisedResumeDriver(config), attempt_dir, workdir


def test_self_check_proves_adapter_safety_and_blocks_ungated_production():
    driver = _load_driver()

    report = driver.self_check()

    assert report["schema"] == "daedalus-supervised-resume-driver/v1"
    assert report["status"] == "blocked"
    assert report["adapter_status"] == "ready"
    assert report["production_status"] == "blocked"
    assert report["interface"] == "local_graph_gateway_command_resume"
    assert report["self_check"]["deterministic"] is True
    assert report["self_check"]["containment_probe_executed"] is True
    assert report["human_gate"] == {
        "main_agent_execute_interrupts": True,
        "synchronous_subagent_execute_interrupts": False,
        "all_executable_actions_human_gated": False,
    }
    assert report["blocking_reasons"] == [
        "subagent_execute_human_gate_unresolved",
        "provider_cost_enforcement_unavailable",
    ]
    assert report["same_snapshot"] == {
        "supervisor_source_frozen": True,
        "cycle_worker_source_frozen": True,
        "production_git_identity_rechecked": True,
    }
    assert report["containment"] == {
        "available": True,
        "enforcement": "darwin_sandbox_exec_attempt_write_boundary",
        "attempt_only_writes": True,
        "network_denied_without_provider_authorization": True,
        "tool_network_denied": True,
        "tool_private_roots_denied": True,
        "tool_workspace_only_writes": True,
        "tool_undeclared_subprocesses_denied": True,
    }
    assert report["safe_defaults"] == {
        "auto_approve": False,
        "auto_mode": False,
        "dangerous_mode": False,
        "private_memory": False,
        "network_tools": False,
        "publication": False,
        "transfer": False,
    }


def test_self_check_blocks_adapter_when_a_containment_probe_fails(monkeypatch):
    driver = _load_driver()
    failed = {
        "available": True,
        "enforcement": "darwin_sandbox_exec_attempt_write_boundary",
        "attempt_only_writes": False,
        "network_denied_without_provider_authorization": True,
        "tool_network_denied": True,
        "tool_private_roots_denied": True,
        "tool_workspace_only_writes": True,
        "tool_undeclared_subprocesses_denied": True,
    }
    monkeypatch.setattr(driver, "_probe_containment", lambda: failed)

    report = driver.self_check()

    assert report["adapter_status"] == "blocked"
    assert "containment_probe_failed" in report["blocking_reasons"]


def test_production_start_fails_before_manifest_when_subagent_gate_is_unresolved(
    tmp_path, monkeypatch
):
    driver = _load_driver()
    monkeypatch.setattr(driver, "_verify_current_source_snapshot", lambda *_: None)
    supervisor, attempt_dir, _workdir = _build_case(driver, tmp_path)
    production = driver.SupervisedResumeDriver(
        replace(supervisor.config, adapter_argv=None)
    )

    with pytest.raises(driver.DriverError) as error:
        production.start()

    assert error.value.code == "subagent_execute_human_gate_unresolved"
    assert not (attempt_dir / "supervisor-evidence" / "attempt-manifest.json").exists()


def test_production_source_snapshot_recheck_detects_commit_and_dirty_drift(tmp_path):
    driver = _load_driver()
    repo = tmp_path / "source"
    repo.mkdir()
    (repo / "tracked.txt").write_text("frozen\n", encoding="utf-8")
    for command in (
        ["git", "init", "-q"],
        ["git", "config", "user.name", "Harness Test"],
        ["git", "config", "user.email", "harness@example.invalid"],
        ["git", "add", "tracked.txt"],
        ["git", "commit", "-q", "-m", "frozen source"],
    ):
        subprocess.run(command, cwd=repo, check=True, capture_output=True)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    driver._verify_current_source_snapshot(repo, commit)
    with pytest.raises(driver.DriverError) as changed:
        driver._verify_current_source_snapshot(repo, "0" * 40)
    assert changed.value.code == "source_snapshot_changed"

    (repo / "tracked.txt").write_text("changed\n", encoding="utf-8")
    with pytest.raises(driver.DriverError) as dirty:
        driver._verify_current_source_snapshot(repo, commit)
    assert dirty.value.code == "source_snapshot_dirty"


def test_start_stops_at_interrupt_without_automatic_approval(tmp_path):
    driver = _load_driver()
    supervisor, attempt_dir, workdir = _build_case(driver, tmp_path)

    result = supervisor.start()

    assert result["outcome"] == "awaiting_approval"
    assert result["pending_request_digest"]
    assert not (workdir / "report.json").exists()
    evidence = attempt_dir / "supervisor-evidence"
    assert len(list((evidence / "cycles").glob("cycle-request-*.json"))) == 1
    assert not (evidence / "status.json").exists()
    manifest = json.loads((evidence / "attempt-manifest.json").read_text())
    assert set(manifest["input_sha256"]) == {
        "packet",
        "authorization",
        "allowlist",
        "preflight",
        "runtime_config",
        "prompt",
        "supervisor_source",
        "cycle_worker_source",
    }
    assert (
        manifest["input_sha256"]["supervisor_source"]
        == hashlib.sha256(SCRIPT.read_bytes()).hexdigest()
    )
    assert manifest["execution_mode"] == "deterministic_adapter"
    assert manifest["evidence_ceiling"] == "E2"
    assert Path(manifest["input_paths"]["cycle_worker_source"]).name == (
        "cycle-worker-source.py"
    )
    for name, path in manifest["input_paths"].items():
        frozen_path = Path(path)
        assert frozen_path.parent == evidence
        assert frozen_path.is_file(), name


def test_changed_supervisor_source_blocks_resume_before_decision(tmp_path, monkeypatch):
    driver = _load_driver()
    source_copy = tmp_path / "frozen-supervisor.py"
    source_copy.write_bytes(SCRIPT.read_bytes())
    monkeypatch.setattr(driver, "__file__", str(source_copy))
    supervisor, attempt_dir, _workdir = _build_case(driver, tmp_path)
    awaiting = supervisor.start()
    source_copy.write_text("# changed supervisor\n", encoding="utf-8")

    with pytest.raises(driver.DriverError) as error:
        supervisor.decide(
            decision="approve",
            request_digest=awaiting["pending_request_digest"],
            operator="fixture-human",
        )

    assert error.value.code == "supervisor_source_changed"
    decisions = attempt_dir / "supervisor-evidence" / "decisions"
    assert not list(decisions.glob("decision-*.json"))


def test_changed_frozen_cycle_worker_blocks_resume_before_decision(tmp_path):
    driver = _load_driver()
    supervisor, attempt_dir, _workdir = _build_case(driver, tmp_path)
    awaiting = supervisor.start()
    worker = attempt_dir / "supervisor-evidence" / "cycle-worker-source.py"
    worker.write_text("# changed adapter\n", encoding="utf-8")

    with pytest.raises(driver.DriverError) as error:
        supervisor.decide(
            decision="approve",
            request_digest=awaiting["pending_request_digest"],
            operator="fixture-human",
        )

    assert error.value.code == "frozen_input_changed"
    decisions = attempt_dir / "supervisor-evidence" / "decisions"
    assert not list(decisions.glob("decision-*.json"))


def test_explicit_approval_resumes_exact_thread_and_completes(tmp_path):
    driver = _load_driver()
    supervisor, attempt_dir, workdir = _build_case(driver, tmp_path)
    awaiting = supervisor.start()

    result = supervisor.decide(
        decision="approve",
        request_digest=awaiting["pending_request_digest"],
        operator="fixture-human",
    )

    assert result["outcome"] == "completed"
    assert (workdir / "report.json").is_file()
    evidence = attempt_dir / "supervisor-evidence"
    manifest = json.loads((evidence / "attempt-manifest.json").read_text())
    status = json.loads((evidence / "status.json").read_text())
    assert status["thread_id"] == manifest["thread_id"]
    assert status["supervisor_run_id"] == manifest["supervisor_run_id"]
    assert status["native_run_id"] is None
    assert status["outcome"] == "completed"
    assert len(list((evidence / "cycles").glob("cycle-request-*.json"))) == 2


@pytest.mark.parametrize(
    "scenario",
    ["outside_attempt_write", "outside_attempt_read", "network_operation"],
)
def test_process_containment_rejects_escape_after_approval(tmp_path, scenario):
    driver = _load_driver()
    supervisor, attempt_dir, _workdir = _build_case(driver, tmp_path, scenario=scenario)
    (attempt_dir.parent / "private-sentinel.txt").write_text(
        "must remain unreadable", encoding="utf-8"
    )
    awaiting = supervisor.start()

    result = supervisor.decide(
        decision="approve",
        request_digest=awaiting["pending_request_digest"],
        operator="fixture-human",
    )

    assert result["outcome"] == "failed"
    assert result["failure_code"] == "containment_violation"
    assert not (attempt_dir.parent / "escaped.txt").exists()


def test_timeout_terminates_the_entire_worker_process_group(tmp_path):
    driver = _load_driver()
    supervisor, _attempt_dir, workdir = _build_case(
        driver, tmp_path, scenario="timeout_with_child", timeout_seconds=0.1
    )

    result = supervisor.start()
    time.sleep(0.7)

    assert result["outcome"] == "failed"
    assert result["failure_code"] == "timeout"
    assert not (workdir / "orphan-survived.txt").exists()


def test_allowlist_cannot_enable_forbidden_boundaries(tmp_path):
    driver = _load_driver()
    supervisor, _attempt_dir, _workdir = _build_case(driver, tmp_path)
    allowlist = json.loads(supervisor.config.allowlist_path.read_text())
    allowlist["network_operations_allowed"] = True
    supervisor.config.allowlist_path.write_text(json.dumps(allowlist), encoding="utf-8")

    with pytest.raises(driver.DriverError) as error:
        supervisor.start()

    assert error.value.code == "broadened_allowlist"


def test_allowlist_requires_a_frozen_script_at_python_argv_one(tmp_path):
    driver = _load_driver()
    supervisor, _attempt_dir, _workdir = _build_case(driver, tmp_path)
    allowlist_path = supervisor.config.allowlist_path
    allowlist = json.loads(allowlist_path.read_text())
    action = allowlist["allowed_actions"][0]
    action["path_argument_indexes"] = []
    action["path_sha256"] = {}
    allowlist_path.write_text(json.dumps(allowlist), encoding="utf-8")

    with pytest.raises(driver.DriverError) as error:
        supervisor.start()

    assert error.value.code == "unsafe_python_invocation"


def test_allowlist_rejects_inline_python_code(tmp_path):
    driver = _load_driver()
    supervisor, _attempt_dir, _workdir = _build_case(driver, tmp_path)
    allowlist_path = supervisor.config.allowlist_path
    allowlist = json.loads(allowlist_path.read_text())
    action = allowlist["allowed_actions"][0]
    action.update(
        {
            "args": {"command": "python3 -c 'print(1)'"},
            "argv": ["python3", "-c", "print(1)"],
            "path_argument_indexes": [],
            "path_sha256": {},
        }
    )
    allowlist_path.write_text(json.dumps(allowlist), encoding="utf-8")

    with pytest.raises(driver.DriverError) as error:
        supervisor.start()

    assert error.value.code == "unsafe_python_invocation"


def test_allowlist_requires_the_nested_python_wrapper_name(tmp_path):
    driver = _load_driver()
    supervisor, _attempt_dir, _workdir = _build_case(driver, tmp_path)
    allowlist_path = supervisor.config.allowlist_path
    allowlist = json.loads(allowlist_path.read_text())
    action = allowlist["allowed_actions"][0]
    action["args"]["command"] = "/usr/bin/python3 analysis.py"
    action["argv"][0] = "/usr/bin/python3"
    allowlist_path.write_text(json.dumps(allowlist), encoding="utf-8")

    with pytest.raises(driver.DriverError) as error:
        supervisor.start()

    assert error.value.code == "unsupported_executable"


@pytest.mark.parametrize(
    "field",
    [
        "paid_provider_activation_authorized",
        "private_memory_access_authorized",
        "private_research_data_access_authorized",
        "artifact_transfer_authorized",
        "publication_authorized",
        "evoscientist_core_modification_authorized",
    ],
)
def test_adapter_authorization_requires_explicit_false_boundaries(tmp_path, field):
    driver = _load_driver()
    supervisor, _attempt_dir, _workdir = _build_case(driver, tmp_path)
    authorization_path = supervisor.config.authorization_path
    authorization = json.loads(authorization_path.read_text())
    authorization.pop(field)
    authorization_path.write_text(json.dumps(authorization), encoding="utf-8")

    with pytest.raises(driver.DriverError) as error:
        supervisor.start()

    assert error.value.code == "broadened_authorization"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("tool_action_preapproval_authorized", True),
        ("tool_action_approval_policy", "packet_preapproval"),
    ],
)
def test_authorization_requires_separate_exact_digest_tool_gates(
    tmp_path, field, value
):
    driver = _load_driver()
    supervisor, _attempt_dir, _workdir = _build_case(driver, tmp_path)
    authorization_path = supervisor.config.authorization_path
    authorization = json.loads(authorization_path.read_text())
    authorization[field] = value
    authorization_path.write_text(json.dumps(authorization), encoding="utf-8")

    with pytest.raises(driver.DriverError) as error:
        supervisor.start()

    assert error.value.code == "missing_human_gate"


@pytest.mark.parametrize(
    ("paid_allowed", "maximum_cost", "prohibited"),
    [
        (False, 1.0, []),
        (True, 0, []),
        (True, 1.0, ["activate_paid_provider"]),
    ],
)
def test_production_authorization_rejects_contradictory_provider_cost_boundary(
    tmp_path, paid_allowed, maximum_cost, prohibited
):
    driver = _load_driver()
    supervisor, _attempt_dir, _workdir = _build_case(driver, tmp_path)
    packet = json.loads(supervisor.config.packet_path.read_text())
    authorization = json.loads(supervisor.config.authorization_path.read_text())
    authorization["paid_provider_activation_authorized"] = True
    packet["provider_cost_boundary"] = {
        "allowed_providers": ["anthropic"],
        "paid_providers_authorized": paid_allowed,
        "maximum_cost_usd": maximum_cost,
    }
    packet["prohibited_operations"] = prohibited

    with pytest.raises(driver.DriverError) as error:
        driver._validate_authorization(
            packet,
            authorization,
            {"provider": "anthropic"},
            adapter=False,
        )

    assert error.value.code in {"provider_not_authorized", "provider_cost_invalid"}


def test_production_authorization_fails_closed_without_cost_enforcement(tmp_path):
    driver = _load_driver()
    supervisor, _attempt_dir, _workdir = _build_case(driver, tmp_path)
    packet = json.loads(supervisor.config.packet_path.read_text())
    authorization = json.loads(supervisor.config.authorization_path.read_text())
    authorization["paid_provider_activation_authorized"] = True
    packet["provider_cost_boundary"] = {
        "allowed_providers": ["anthropic"],
        "paid_providers_authorized": True,
        "maximum_cost_usd": 0.25,
    }
    packet["prohibited_operations"] = []

    with pytest.raises(driver.DriverError) as error:
        driver._validate_authorization(
            packet,
            authorization,
            {"provider": "anthropic"},
            adapter=False,
        )

    assert error.value.code == "provider_cost_enforcement_unavailable"


def test_allowlist_rejects_shell_command_substitution(tmp_path):
    driver = _load_driver()
    supervisor, _attempt_dir, _workdir = _build_case(driver, tmp_path)
    allowlist_path = supervisor.config.allowlist_path
    allowlist = json.loads(allowlist_path.read_text())
    action = allowlist["allowed_actions"][0]
    action["args"]["command"] = "python3 analysis.py '$(curl example.invalid)'"
    action["argv"] = ["python3", "analysis.py", "$(curl example.invalid)"]
    allowlist_path.write_text(json.dumps(allowlist), encoding="utf-8")

    with pytest.raises(driver.DriverError) as error:
        supervisor.start()

    assert error.value.code == "unsafe_shell_syntax"


def test_frozen_command_path_digest_is_rechecked_before_launch(tmp_path):
    driver = _load_driver()
    supervisor, _attempt_dir, workdir = _build_case(driver, tmp_path)
    (workdir / "analysis.py").write_text("print('changed')\n", encoding="utf-8")

    with pytest.raises(driver.DriverError) as error:
        supervisor.start()

    assert error.value.code == "command_path_digest_mismatch"


def test_frozen_command_path_change_blocks_resume(tmp_path):
    driver = _load_driver()
    supervisor, attempt_dir, workdir = _build_case(driver, tmp_path)
    awaiting = supervisor.start()
    (workdir / "analysis.py").write_text("print('changed')\n", encoding="utf-8")

    with pytest.raises(driver.DriverError) as error:
        supervisor.decide(
            decision="approve",
            request_digest=awaiting["pending_request_digest"],
            operator="fixture-human",
        )

    assert error.value.code == "command_path_digest_mismatch"
    cycles = attempt_dir / "supervisor-evidence" / "cycles"
    assert len(list(cycles.glob("cycle-request-*.json"))) == 1


def test_changed_action_wrapper_becomes_a_terminal_failure(tmp_path):
    driver = _load_driver()
    supervisor, attempt_dir, _workdir = _build_case(driver, tmp_path)
    awaiting = supervisor.start()
    wrapper = attempt_dir / "supervisor-evidence" / "runtime" / "action-bin" / "python3"
    wrapper.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")

    result = supervisor.decide(
        decision="approve",
        request_digest=awaiting["pending_request_digest"],
        operator="fixture-human",
    )

    assert result["outcome"] == "failed"
    assert result["failure_code"] == "action_wrapper_changed"
    status = json.loads(
        (attempt_dir / "supervisor-evidence" / "status.json").read_text()
    )
    assert status["failure_code"] == "action_wrapper_changed"


def test_explicit_rejection_stops_without_resume_or_side_effect(tmp_path):
    driver = _load_driver()
    supervisor, attempt_dir, workdir = _build_case(driver, tmp_path)
    awaiting = supervisor.start()

    result = supervisor.decide(
        decision="reject",
        request_digest=awaiting["pending_request_digest"],
        operator="fixture-human",
    )

    assert result["outcome"] == "stopped"
    assert result["stop_reason"] == "operator_rejected"
    assert not (workdir / "report.json").exists()
    evidence = attempt_dir / "supervisor-evidence"
    assert len(list((evidence / "cycles").glob("cycle-request-*.json"))) == 1
    decisions = list((evidence / "decisions").glob("decision-*.json"))
    assert len(decisions) == 1
    assert json.loads(decisions[0].read_text())["decision"] == "reject"


@pytest.mark.parametrize(
    ("scenario", "failure_code"),
    [
        ("malformed_json", "malformed_json"),
        ("blank_stdout", "blank_stdout"),
        ("stderr_only", "blank_stdout"),
        ("nonzero_exit", "nonzero_exit"),
        ("missing_done", "missing_done"),
        ("timeout", "timeout"),
        ("unknown_tool", "unknown_tool"),
        ("unsafe_command", "forbidden_command"),
        ("unsafe_path", "unsafe_path"),
        ("duplicate_interrupt", "duplicate_interrupt"),
        ("reordered_event", "reordered_event"),
        ("replayed_event", "replayed_event"),
        ("outside_write", "outside_allowlist_write"),
        ("silent_success", "silent_success"),
        ("mismatched_thread", "worker_identity_mismatch"),
        ("mismatched_run", "worker_identity_mismatch"),
        ("missing_identity", "worker_identity_mismatch"),
    ],
)
def test_adversarial_cycle_failures_are_terminal_and_typed(
    tmp_path, scenario, failure_code
):
    driver = _load_driver()
    timeout = 0.1 if scenario == "timeout" else 2.0
    supervisor, attempt_dir, _workdir = _build_case(
        driver, tmp_path, scenario=scenario, timeout_seconds=timeout
    )

    result = supervisor.start()

    assert result["outcome"] == "failed"
    assert result["failure_code"] == failure_code
    status = json.loads(
        (attempt_dir / "supervisor-evidence" / "status.json").read_text()
    )
    assert status["declared_success"] is False
    assert status["failure_code"] == failure_code


def test_changed_request_between_interrupt_and_resume_fails_closed(tmp_path):
    driver = _load_driver()
    supervisor, attempt_dir, _workdir = _build_case(
        driver, tmp_path, scenario="changed_command"
    )
    awaiting = supervisor.start()

    result = supervisor.decide(
        decision="approve",
        request_digest=awaiting["pending_request_digest"],
        operator="fixture-human",
    )

    assert result["outcome"] == "failed"
    assert result["failure_code"] == "changed_approval_request"
    evidence = attempt_dir / "supervisor-evidence"
    assert len(list((evidence / "cycles").glob("cycle-request-*.json"))) == 2


def test_replayed_interrupt_after_resume_fails_closed(tmp_path):
    driver = _load_driver()
    supervisor, _attempt_dir, _workdir = _build_case(
        driver, tmp_path, scenario="repeated_interrupt"
    )
    awaiting = supervisor.start()

    result = supervisor.decide(
        decision="approve",
        request_digest=awaiting["pending_request_digest"],
        operator="fixture-human",
    )

    assert result["outcome"] == "failed"
    assert result["failure_code"] == "replayed_interrupt"


def test_duplicate_approval_cannot_launch_another_resume(tmp_path):
    driver = _load_driver()
    supervisor, attempt_dir, _workdir = _build_case(driver, tmp_path)
    awaiting = supervisor.start()
    supervisor.decide(
        decision="approve",
        request_digest=awaiting["pending_request_digest"],
        operator="fixture-human",
    )

    with pytest.raises(driver.DriverError) as error:
        supervisor.decide(
            decision="approve",
            request_digest=awaiting["pending_request_digest"],
            operator="fixture-human",
        )

    assert error.value.code == "not_awaiting_decision"
    evidence = attempt_dir / "supervisor-evidence"
    assert len(list((evidence / "cycles").glob("cycle-request-*.json"))) == 2


def test_corrupted_attempt_manifest_blocks_resume(tmp_path):
    driver = _load_driver()
    supervisor, attempt_dir, _workdir = _build_case(driver, tmp_path)
    awaiting = supervisor.start()
    manifest_path = attempt_dir / "supervisor-evidence" / "attempt-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["thread_id"] = "tampered-thread"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(driver.DriverError) as error:
        supervisor.decide(
            decision="approve",
            request_digest=awaiting["pending_request_digest"],
            operator="fixture-human",
        )

    assert error.value.code == "corrupted_manifest"
    cycles = attempt_dir / "supervisor-evidence" / "cycles"
    assert len(list(cycles.glob("cycle-request-*.json"))) == 1


def test_rehashed_manifest_with_invalid_input_digest_map_fails_typed(tmp_path):
    driver = _load_driver()
    supervisor, attempt_dir, _workdir = _build_case(driver, tmp_path)
    awaiting = supervisor.start()
    manifest_path = attempt_dir / "supervisor-evidence" / "attempt-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["input_sha256"] = []
    manifest["manifest_sha256"] = driver._json_digest(
        {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    )
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(driver.DriverError) as error:
        supervisor.decide(
            decision="approve",
            request_digest=awaiting["pending_request_digest"],
            operator="fixture-human",
        )

    assert error.value.code == "corrupted_manifest"
    decisions = attempt_dir / "supervisor-evidence" / "decisions"
    assert not list(decisions.glob("decision-*.json"))


def test_corrupted_pending_payload_blocks_resume_before_recording_a_decision(tmp_path):
    driver = _load_driver()
    supervisor, attempt_dir, _workdir = _build_case(driver, tmp_path)
    awaiting = supervisor.start()
    decisions = attempt_dir / "supervisor-evidence" / "decisions"
    pending_path = decisions / "pending-001.json"
    pending = json.loads(pending_path.read_text())
    pending["payload"]["action_requests"][0]["args"]["command"] = "python3 changed.py"
    pending_path.write_text(json.dumps(pending), encoding="utf-8")

    with pytest.raises(driver.DriverError) as error:
        supervisor.decide(
            decision="approve",
            request_digest=awaiting["pending_request_digest"],
            operator="fixture-human",
        )

    assert error.value.code == "corrupted_pending_record"
    assert not (decisions / "decision-001.json").exists()


def test_corrupted_ledger_blocks_resume_before_recording_a_decision(tmp_path):
    driver = _load_driver()
    supervisor, attempt_dir, _workdir = _build_case(driver, tmp_path)
    awaiting = supervisor.start()
    evidence = attempt_dir / "supervisor-evidence"
    with (evidence / "run-ledger.jsonl").open("a", encoding="utf-8") as stream:
        stream.write("{}\n")

    with pytest.raises(driver.DriverError) as error:
        supervisor.decide(
            decision="approve",
            request_digest=awaiting["pending_request_digest"],
            operator="fixture-human",
        )

    assert error.value.code == "corrupted_ledger"
    assert not (evidence / "decisions" / "decision-001.json").exists()


def test_package_shadowing_workdir_is_rejected_before_launch(tmp_path):
    driver = _load_driver()
    supervisor, attempt_dir, workdir = _build_case(driver, tmp_path)
    (workdir / "EvoScientist").mkdir()

    with pytest.raises(driver.DriverError) as error:
        supervisor.start()

    assert error.value.code == "package_shadow"
    cycles = attempt_dir / "supervisor-evidence" / "cycles"
    assert not cycles.exists()


def test_ask_user_requires_explicit_answers_before_resume(tmp_path):
    driver = _load_driver()
    supervisor, _attempt_dir, workdir = _build_case(
        driver, tmp_path, scenario="ask_user"
    )

    awaiting = supervisor.start()

    assert awaiting["outcome"] == "awaiting_user_input"
    assert not (workdir / "report.json").exists()
    result = supervisor.decide(
        decision="answer",
        request_digest=awaiting["pending_request_digest"],
        operator="fixture-human",
        answers=["fixture-a"],
    )
    assert result["outcome"] == "completed"


def test_invalid_ask_user_answers_do_not_consume_the_decision_slot(tmp_path):
    driver = _load_driver()
    supervisor, attempt_dir, _workdir = _build_case(
        driver, tmp_path, scenario="ask_user"
    )
    awaiting = supervisor.start()

    with pytest.raises(driver.DriverError) as error:
        supervisor.decide(
            decision="answer",
            request_digest=awaiting["pending_request_digest"],
            operator="fixture-human",
            answers=None,
        )

    assert error.value.code == "invalid_answers"
    decisions = attempt_dir / "supervisor-evidence" / "decisions"
    assert not (decisions / "decision-001.json").exists()
    assert supervisor.inspect()["outcome"] == "awaiting_user_input"

    result = supervisor.decide(
        decision="answer",
        request_digest=awaiting["pending_request_digest"],
        operator="fixture-human",
        answers=["fixture-a"],
    )
    assert result["outcome"] == "completed"


def test_interrupt_cycle_cap_stops_before_another_resume(tmp_path):
    driver = _load_driver()
    supervisor, attempt_dir, _workdir = _build_case(driver, tmp_path, max_cycles=1)
    awaiting = supervisor.start()

    result = supervisor.decide(
        decision="approve",
        request_digest=awaiting["pending_request_digest"],
        operator="fixture-human",
    )

    assert result["outcome"] == "failed"
    assert result["failure_code"] == "maximum_cycles_exceeded"
    cycles = attempt_dir / "supervisor-evidence" / "cycles"
    assert len(list(cycles.glob("cycle-request-*.json"))) == 1


def test_operator_cancellation_records_stopped_without_resume(tmp_path):
    driver = _load_driver()
    supervisor, attempt_dir, _workdir = _build_case(driver, tmp_path)
    supervisor.start()

    result = supervisor.cancel(operator="fixture-human", reason="operator_cancelled")

    assert result["outcome"] == "stopped"
    assert result["stop_reason"] == "operator_cancelled"
    cycles = attempt_dir / "supervisor-evidence" / "cycles"
    assert len(list(cycles.glob("cycle-request-*.json"))) == 1


def test_worker_builds_official_command_resume_payload():
    driver = _load_driver()
    payload = {"decisions": [{"type": "approve"}]}

    message = driver._build_graph_run_message(
        {"mode": "resume", "resume_payload": payload}
    )

    assert message.resume == payload
    assert (
        driver._build_graph_run_message({"mode": "start", "prompt": "synthetic prompt"})
        == "synthetic prompt"
    )


def test_worker_config_forces_every_approval_and_memory_switch_off(tmp_path):
    driver = _load_driver()

    values = driver._worker_config_values(
        {
            "provider": "fixture",
            "model": "fixture",
            "config_overrides": {"recursion_limit": 50},
        },
        tmp_path,
    )

    assert values["auto_approve"] is False
    assert values["auto_mode"] is False
    assert values["dangerous_mode"] is False
    assert values["shell_allow_list"] == ""
    assert values["memory_profile_enabled"] is False
    assert values["memory_observations_enabled"] is False
    assert values["memory_observation_writer"] == "off"
    assert values["memory_workers_enabled"] is False
    assert values["memory_skill_synthesis_enabled"] is False
    assert values["enable_async_subagents"] is False
    assert values["enable_scheduler"] is False
    assert values["channel_enabled"] is False
    assert values["default_workdir"] == str(tmp_path.resolve())


def test_python_action_wrapper_denies_network_and_outside_paths(tmp_path):
    driver = _load_driver()
    supervisor, attempt_dir, workdir = _build_case(driver, tmp_path)
    frozen = supervisor._freeze_inputs()
    env, _secret_values = supervisor._worker_env(frozen)
    wrapper = Path(env["PATH"].split(os.pathsep, 1)[0]) / "python3"
    sentinel = attempt_dir.parent / "private-sentinel.txt"
    sentinel.write_text("private", encoding="utf-8")

    allowed_script = workdir / "allowed.py"
    allowed_script.write_text(
        "from pathlib import Path\nPath('allowed.json').write_text('{}')\n",
        encoding="utf-8",
    )
    allowed = subprocess.run(
        [str(wrapper), str(allowed_script)],
        cwd=workdir,
        env=env,
        capture_output=True,
        timeout=5,
    )
    assert allowed.returncode == 0
    assert (workdir / "allowed.json").is_file()

    denied_scripts = {
        "read.py": f"from pathlib import Path\nPath({str(sentinel)!r}).read_text()\n",
        "write.py": (
            "from pathlib import Path\n"
            f"Path({str(attempt_dir.parent / 'escaped.txt')!r}).write_text('bad')\n"
        ),
        "network.py": (
            "import socket\nsocket.create_connection(('127.0.0.1', 9), timeout=0.1)\n"
        ),
        "undeclared_subprocess.py": (
            "import subprocess\n"
            "subprocess.run(['/usr/bin/touch', 'undeclared-child.txt'], check=True)\n"
        ),
    }
    for name, source in denied_scripts.items():
        script = workdir / name
        script.write_text(source, encoding="utf-8")
        denied = subprocess.run(
            [str(wrapper), str(script)],
            cwd=workdir,
            env=env,
            capture_output=True,
            timeout=5,
        )
        assert denied.returncode != 0, name
        assert b"Operation not permitted" in denied.stderr, name
    assert not (attempt_dir.parent / "escaped.txt").exists()
    assert not (workdir / "undeclared-child.txt").exists()


def test_declared_provider_credentials_are_scrubbed_before_tool_execution(
    monkeypatch,
):
    driver = _load_driver()
    monkeypatch.setenv("OPENAI_API_KEY", "fixture-secret-never-captured")

    scrubbed = driver._scrub_declared_credentials(
        {"credential_env_names": ["OPENAI_API_KEY"]}
    )

    assert scrubbed == ["OPENAI_API_KEY"]
    assert "OPENAI_API_KEY" not in driver.os.environ


def test_existing_attempt_can_be_rehydrated_and_inspected_without_launch(tmp_path):
    driver = _load_driver()
    supervisor, attempt_dir, _workdir = _build_case(driver, tmp_path)
    awaiting = supervisor.start()

    restored = driver.SupervisedResumeDriver.from_attempt(attempt_dir)
    result = restored.inspect()

    assert result == awaiting
    assert restored.config.adapter_argv is None


def test_cli_inspect_returns_structured_state_without_launch(tmp_path, capsys):
    driver = _load_driver()
    supervisor, attempt_dir, _workdir = _build_case(driver, tmp_path)
    awaiting = supervisor.start()

    exit_code = driver.main(["inspect", "--attempt-dir", str(attempt_dir)])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["outcome"] == awaiting["outcome"]


def test_worker_isolation_rejects_environment_outside_runtime_root(
    tmp_path, monkeypatch
):
    driver = _load_driver()
    runtime_root = tmp_path / "runtime"
    request = {
        "runtime_root": str(runtime_root),
        "workdir": str(tmp_path / "workspace"),
    }
    for key, suffix in {
        "HOME": "home",
        "XDG_CONFIG_HOME": "xdg-config",
        "XDG_CACHE_HOME": "xdg-cache",
        "TMPDIR": "tmp",
        "TMP": "tmp",
        "TEMP": "tmp",
        "EVOSCIENTIST_DATA_DIR": "data",
        "EVOSCIENTIST_MEMORIES_DIR": "memories",
        "EVOSCIENTIST_SKILLS_DIR": "skills",
        "EVOSCIENTIST_RUNS_DIR": "runs",
        "EVOSCIENTIST_MEDIA_DIR": "media",
    }.items():
        monkeypatch.setenv(key, str(runtime_root / suffix))
    monkeypatch.setenv("EVOSCIENTIST_WORKSPACE_DIR", str(tmp_path / "workspace"))

    driver._assert_worker_isolation(request)

    monkeypatch.setenv("EVOSCIENTIST_MEMORIES_DIR", str(tmp_path / "private"))
    with pytest.raises(driver.DriverError) as error:
        driver._assert_worker_isolation(request)
    assert error.value.code == "worker_isolation_failure"
