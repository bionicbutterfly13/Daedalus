import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = (
    ROOT
    / "skills"
    / "supervising-daedalus-mock-study-runs"
    / "scripts"
    / "daedalus_preflight.py"
)


def _load_preflight():
    spec = importlib.util.spec_from_file_location("daedalus_preflight", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def preflight():
    return _load_preflight()


def test_workdir_check_rejects_package_shadow(preflight, tmp_path):
    (tmp_path / "EvoScientist").mkdir()

    result = preflight.check_workdir(tmp_path)

    assert result.status == "fail"
    assert result.blocking is True
    assert result.check_id == "workdir.data_only"


def test_workdir_check_accepts_data_only_directory(preflight, tmp_path):
    result = preflight.check_workdir(tmp_path)

    assert result.status == "pass"
    assert result.blocking is False


def test_launcher_interpreter_preserves_virtualenv_symlink(preflight, tmp_path):
    base_interpreter = tmp_path / "base-python"
    base_interpreter.write_text("", encoding="utf-8")
    venv_interpreter = tmp_path / "venv-python"
    venv_interpreter.symlink_to(base_interpreter)
    launcher = tmp_path / "daedalus"
    launcher.write_text(f"#!{venv_interpreter}\n", encoding="utf-8")

    result = preflight._launcher_interpreter(launcher)

    assert result == venv_interpreter
    assert result != base_interpreter.resolve()


def test_preflight_stops_before_resolving_launcher_for_shadowed_workdir(
    preflight, tmp_path, monkeypatch
):
    (tmp_path / "EvoScientist").mkdir()

    def unexpected_launcher_resolution(_value):
        raise AssertionError("launcher resolution must not run")

    monkeypatch.setattr(preflight, "_resolve_launcher", unexpected_launcher_resolution)

    report = preflight.run_preflight(
        repo_root=ROOT,
        workdir=tmp_path,
        launcher_name="EvoSci",
        webui_source_dir=None,
    )

    assert report["status"] == "blocked"
    assert report["blocking_check_ids"] == [
        "workdir.data_only",
        "runtime.probes_skipped",
    ]


def test_command_completeness_fails_when_feature_is_unreachable(preflight):
    actual = sorted(preflight.REQUIRED_PRIMARY_COMMANDS - {"/install-mcp"})

    result = preflight.check_required_commands({"primary_commands": actual})

    assert result.status == "fail"
    assert result.evidence["missing"] == ["/install-mcp"]


def test_command_completeness_passes_for_full_registry(preflight):
    result = preflight.check_required_commands(
        {"primary_commands": sorted(preflight.REQUIRED_PRIMARY_COMMANDS)}
    )

    assert result.status == "pass"
    assert result.evidence["missing"] == []


def test_channel_completeness_fails_when_adapters_are_unreachable(preflight):
    actual = sorted(preflight.REQUIRED_CHANNEL_SUBCOMMANDS - {"qq", "signal"})

    result = preflight.check_required_channels({"subcommands": {"/channel": actual}})

    assert result.status == "fail"
    assert result.evidence["missing"] == ["qq", "signal"]


def test_webui_latest_is_a_blocker(preflight, tmp_path):
    source = tmp_path / "EvoScientist" / "deploy"
    source.mkdir(parents=True)
    (source / "webui.py").write_text(
        '_WEBUI_PACKAGE = "@evoscientist/webui@latest"\n', encoding="utf-8"
    )

    result = preflight.check_webui_package(tmp_path)

    assert result.status == "fail"
    assert result.evidence["package"].endswith("@latest")


def test_webui_pinned_package_passes(preflight, tmp_path):
    source = tmp_path / "EvoScientist" / "deploy"
    source.mkdir(parents=True)
    (source / "webui.py").write_text(
        '_WEBUI_PACKAGE = "@evoscientist/webui@0.1.7"\n', encoding="utf-8"
    )

    result = preflight.check_webui_package(tmp_path)

    assert result.status == "pass"


def test_built_in_skill_claim_fails_on_packaged_count_mismatch(preflight, tmp_path):
    (tmp_path / "README.md").write_text(
        "- [x] 200+ predefined skills built in\n", encoding="utf-8"
    )
    runtime = {"builtin_skill_dirs": ["one", "two", "three"]}

    result = preflight.check_builtin_skill_claim(tmp_path, runtime)

    assert result.status == "fail"
    assert result.evidence["packaged_count"] == 3


def test_webui_source_field_must_be_reachable(preflight):
    missing = preflight.check_webui_config({"config_fields": []})
    present = preflight.check_webui_config({"config_fields": ["webui_source_dir"]})

    assert missing.status == "fail"
    assert present.status == "pass"


def test_python_command_failure_is_blocking_when_documented(preflight, tmp_path):
    package = tmp_path / "EvoScientist"
    package.mkdir()
    (package / "prompts.py").write_text(
        "EXAMPLE = 'python -c \"print(1)\"'\n", encoding="utf-8"
    )
    (package / "subagents").mkdir()

    result = preflight.check_python_command(
        tmp_path,
        {
            "python_exit": 127,
            "python3_exit": 0,
            "python_output": "python: command not found",
            "python3_output": "123",
        },
    )

    assert result.status == "fail"
    assert result.blocking is True


def test_summary_is_ready_only_without_blockers(preflight):
    passed = preflight._check("pass", "pass", "ok")
    warning = preflight._check("warn", "warn", "review", blocking=False)
    failed = preflight._check("fail", "fail", "blocked")

    ready = preflight.summarize([passed, warning])
    blocked = preflight.summarize([passed, failed])

    assert ready["status"] == "ready"
    assert blocked["status"] == "blocked"
    assert blocked["blocking_check_ids"] == ["fail"]


def _write_driver_fixture(repo_root, report):
    script = (
        repo_root
        / "skills"
        / "supervising-daedalus-mock-study-runs"
        / "scripts"
        / "drive_stream_json_resume.py"
    )
    script.parent.mkdir(parents=True)
    script.write_text(
        f"import json\nREPORT = {report!r}\nprint(json.dumps(REPORT))\n",
        encoding="utf-8",
    )
    return script


def _safe_driver_report():
    return {
        "schema": "daedalus-supervised-resume-driver/v1",
        "status": "ready",
        "adapter_status": "ready",
        "production_status": "ready",
        "interface": "local_graph_gateway_command_resume",
        "safe_defaults": {
            "auto_approve": False,
            "auto_mode": False,
            "dangerous_mode": False,
            "private_memory": False,
            "network_tools": False,
            "publication": False,
            "transfer": False,
        },
        "containment": {
            "available": True,
            "enforcement": "darwin_sandbox_exec_attempt_write_boundary",
            "attempt_only_writes": True,
            "network_denied_without_provider_authorization": True,
            "tool_network_denied": True,
            "tool_private_roots_denied": True,
            "tool_workspace_only_writes": True,
            "tool_undeclared_subprocesses_denied": True,
        },
        "human_gate": {
            "main_agent_execute_interrupts": True,
            "synchronous_subagent_execute_interrupts": True,
            "all_executable_actions_human_gated": True,
        },
        "blocking_reasons": [],
        "same_snapshot": {
            "supervisor_source_frozen": True,
            "cycle_worker_source_frozen": True,
            "production_git_identity_rechecked": True,
        },
        "self_check": {
            "deterministic": True,
            "containment_probe_executed": True,
            "model_loaded": False,
            "service_started": False,
            "provider_activated": False,
        },
    }


def test_resume_driver_check_blocks_real_ungated_production_contract(preflight):
    result = preflight.check_resume_driver(ROOT, Path(sys.executable))

    assert result.status == "fail"
    assert result.evidence["contract_status"] == "blocked"
    assert result.evidence["adapter_contract_safe"] is True
    assert result.evidence["production_contract_safe"] is False
    assert result.evidence["blocking_reasons"] == [
        "subagent_execute_human_gate_unresolved",
        "provider_cost_enforcement_unavailable",
    ]
    assert result.evidence["interface"] == "local_graph_gateway_command_resume"


def test_resume_driver_check_accepts_a_fully_gated_contract(preflight, tmp_path):
    _write_driver_fixture(tmp_path, _safe_driver_report())

    result = preflight.check_resume_driver(tmp_path, Path(sys.executable))

    assert result.status == "pass"
    assert result.evidence["adapter_contract_safe"] is True
    assert result.evidence["production_contract_safe"] is True


def test_resume_driver_check_fails_when_driver_is_removed(preflight, tmp_path):
    result = preflight.check_resume_driver(tmp_path, Path(sys.executable))

    assert result.status == "fail"
    assert result.evidence["present"] is False


def test_resume_driver_check_fails_on_malformed_self_check(preflight, tmp_path):
    script = (
        tmp_path
        / "skills"
        / "supervising-daedalus-mock-study-runs"
        / "scripts"
        / "drive_stream_json_resume.py"
    )
    script.parent.mkdir(parents=True)
    script.write_text("print('{not-json')\n", encoding="utf-8")

    result = preflight.check_resume_driver(tmp_path, Path(sys.executable))

    assert result.status == "fail"
    assert result.evidence["error"] == "invalid_json"


@pytest.mark.parametrize(
    "mutation",
    [
        {"status": "disabled"},
        {"production_status": "blocked"},
        {"interface": "subprocess_cli_resume"},
        {"safe_defaults": {"auto_approve": True}},
        {"containment": {"available": False}},
        {"human_gate": {"all_executable_actions_human_gated": False}},
        {"same_snapshot": {"production_git_identity_rechecked": False}},
        {"self_check": {"deterministic": False}},
    ],
)
def test_resume_driver_check_fails_on_disabled_or_unsafe_contract(
    preflight, tmp_path, mutation
):
    report = _safe_driver_report()
    report.update(mutation)
    _write_driver_fixture(tmp_path, report)

    result = preflight.check_resume_driver(tmp_path, Path(sys.executable))

    assert result.status == "fail"
    assert (
        result.evidence["contract_status"] != "ready"
        or result.evidence["contract_safe"] is False
    )
