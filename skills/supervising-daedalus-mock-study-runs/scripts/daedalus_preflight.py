#!/usr/bin/env python3
"""Read-only capability preflight for an authorized Daedalus study.

The preflight inspects only the named repository, data-only work directory,
launcher, and optional WebUI checkout. It does not load user configuration,
inspect private memory, launch a model or service, or mutate the repository.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

SCHEMA = "daedalus-capability-preflight/v1"
Status = Literal["pass", "warn", "fail"]

REQUIRED_PRIMARY_COMMANDS = frozenset(
    {
        "/autoskills",
        "/channel",
        "/help",
        "/current",
        "/initiative",
        "/mcp",
        "/model",
        "/model-fallback",
        "/schedule",
        "/compact",
        "/threads",
        "/resume",
        "/new",
        "/clear",
        "/delete",
        "/exit",
        "/skills",
        "/install-skill",
        "/evoskills",
        "/uninstall-skill",
        "/steer",
        "/install-mcp",
    }
)
REQUIRED_CHANNEL_SUBCOMMANDS = frozenset(
    {
        "status",
        "stop",
        "telegram",
        "discord",
        "slack",
        "feishu",
        "dingtalk",
        "wechat",
        "qq",
        "signal",
        "email",
        "imessage",
    }
)
EXPECTED_PROVIDERS = frozenset(
    {
        "anthropic",
        "openai",
        "google-genai",
        "minimax",
        "zhipu",
        "zhipu-code",
        "volcengine",
        "dashscope",
        "dashscope-code",
        "deepseek",
        "moonshot",
        "kimi-coding",
        "ollama",
        "nvidia",
        "siliconflow",
        "openrouter",
        "custom-openai",
        "custom-anthropic",
    }
)


@dataclass(frozen=True)
class Check:
    """One independently reviewable preflight finding."""

    check_id: str
    status: Status
    blocking: bool
    detail: str
    evidence: dict[str, Any]


def _check(
    check_id: str,
    status: Status,
    detail: str,
    *,
    blocking: bool | None = None,
    **evidence: Any,
) -> Check:
    if blocking is None:
        blocking = status == "fail"
    return Check(check_id, status, blocking, detail, evidence)


def _run(
    argv: Sequence[str],
    *,
    cwd: Path,
    timeout: int = 30,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(argv),
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _resolve_launcher(value: str) -> Path | None:
    candidate = Path(value).expanduser()
    if candidate.parent != Path(".") or candidate.is_absolute():
        return candidate.resolve() if candidate.is_file() else None
    resolved = shutil.which(value)
    return Path(resolved).resolve() if resolved else None


def _launcher_interpreter(launcher: Path) -> Path | None:
    """Resolve the interpreter encoded by a console-script launcher."""

    if launcher.suffix.lower() == ".exe":
        candidate = launcher.parent / "python.exe"
        return candidate.absolute() if candidate.is_file() else None
    try:
        with launcher.open(encoding="utf-8") as stream:
            first_line = stream.readline().strip()
    except (OSError, UnicodeError):
        return None
    if not first_line.startswith("#!"):
        return None
    parts = shlex.split(first_line[2:].strip())
    if not parts:
        return None
    if Path(parts[0]).name == "env" and len(parts) > 1:
        resolved = shutil.which(parts[1])
        return Path(resolved).absolute() if resolved else None
    candidate = Path(parts[0]).expanduser()
    return candidate.absolute() if candidate.is_file() else None


def check_workdir(workdir: Path) -> Check:
    shadow = workdir / "EvoScientist"
    if not workdir.is_dir():
        return _check(
            "workdir.data_only",
            "fail",
            "The named work directory does not exist or is not a directory.",
            workdir=str(workdir),
        )
    if shadow.exists():
        return _check(
            "workdir.data_only",
            "fail",
            "The work directory contains an EvoScientist path that can shadow the installed package.",
            workdir=str(workdir.resolve()),
            shadow_path=str(shadow.resolve()),
        )
    return _check(
        "workdir.data_only",
        "pass",
        "The work directory exists and contains no package-shadowing path.",
        workdir=str(workdir.resolve()),
    )


def check_required_commands(runtime: dict[str, Any]) -> Check:
    actual = frozenset(runtime.get("primary_commands", []))
    missing = sorted(REQUIRED_PRIMARY_COMMANDS - actual)
    extra = sorted(actual - REQUIRED_PRIMARY_COMMANDS)
    status: Status = "fail" if missing else "pass"
    return _check(
        "commands.primary_complete",
        status,
        "Required slash commands are registered."
        if not missing
        else "One or more required slash commands are not registered.",
        expected_count=len(REQUIRED_PRIMARY_COMMANDS),
        actual_count=len(actual),
        missing=missing,
        extra=extra,
    )


def check_required_channels(runtime: dict[str, Any]) -> Check:
    actual = frozenset(runtime.get("subcommands", {}).get("/channel", []))
    missing = sorted(REQUIRED_CHANNEL_SUBCOMMANDS - actual)
    extra = sorted(actual - REQUIRED_CHANNEL_SUBCOMMANDS)
    status: Status = "fail" if missing else "pass"
    return _check(
        "commands.channel_complete",
        status,
        "All channel adapters are exposed through the slash interface."
        if not missing
        else "The slash channel interface omits one or more implemented adapters.",
        expected_count=len(REQUIRED_CHANNEL_SUBCOMMANDS),
        actual_count=len(actual),
        missing=missing,
        extra=extra,
    )


def check_provider_inventory(runtime: dict[str, Any]) -> Check:
    actual = frozenset(runtime.get("providers", []))
    missing = sorted(EXPECTED_PROVIDERS - actual)
    extra = sorted(actual - EXPECTED_PROVIDERS)
    status: Status = "fail" if missing or extra else "pass"
    return _check(
        "providers.inventory",
        status,
        "The provider registry matches the frozen inventory."
        if status == "pass"
        else "The provider registry drifted from the frozen inventory.",
        expected_count=len(EXPECTED_PROVIDERS),
        actual_count=len(actual),
        missing=missing,
        extra=extra,
    )


def check_webui_package(repo_root: Path) -> Check:
    source = repo_root / "EvoScientist" / "deploy" / "webui.py"
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as exc:
        return _check(
            "webui.package_pinned",
            "fail",
            "The WebUI launcher source could not be read.",
            source=str(source),
            error=type(exc).__name__,
        )
    match = re.search(
        r'^_WEBUI_PACKAGE\s*=\s*["\']([^"\']+)["\']',
        text,
        re.MULTILINE,
    )
    if not match:
        return _check(
            "webui.package_pinned",
            "fail",
            "The WebUI package identifier was not found.",
            source=str(source),
        )
    package = match.group(1)
    mutable = package.endswith("@latest") or "@next" in package
    return _check(
        "webui.package_pinned",
        "fail" if mutable else "pass",
        "The normal WebUI launcher uses a mutable package selector."
        if mutable
        else "The normal WebUI launcher uses a pinned package selector.",
        source=str(source),
        package=package,
    )


def check_webui_config(runtime: dict[str, Any]) -> Check:
    fields = set(runtime.get("config_fields", []))
    present = "webui_source_dir" in fields
    return _check(
        "webui.local_source_reachable",
        "pass" if present else "fail",
        "Persisted configuration can select a frozen local WebUI source."
        if present
        else "The launcher reads webui_source_dir, but persisted configuration drops that field.",
        field="webui_source_dir",
        present=present,
    )


def check_webui_source_dir(source_dir: Path | None) -> Check:
    if source_dir is None:
        return _check(
            "webui.local_source_identity",
            "warn",
            "No local WebUI source was named for this preflight.",
            blocking=False,
        )
    package = source_dir / "package.json"
    if not package.is_file():
        return _check(
            "webui.local_source_identity",
            "fail",
            "The named WebUI source has no package.json.",
            source_dir=str(source_dir),
        )
    commit = _run(["git", "rev-parse", "HEAD"], cwd=source_dir)
    status = _run(["git", "status", "--porcelain"], cwd=source_dir)
    if commit.returncode != 0 or status.returncode != 0:
        return _check(
            "webui.local_source_identity",
            "fail",
            "The named WebUI source is not a readable Git checkout.",
            source_dir=str(source_dir.resolve()),
        )
    dirty_count = len([line for line in status.stdout.splitlines() if line.strip()])
    return _check(
        "webui.local_source_identity",
        "fail" if dirty_count else "pass",
        "The named WebUI source is dirty and cannot be frozen by commit alone."
        if dirty_count
        else "The named WebUI source is clean and has an exact commit identity.",
        source_dir=str(source_dir.resolve()),
        commit=commit.stdout.strip(),
        dirty_entry_count=dirty_count,
    )


def check_builtin_skill_claim(repo_root: Path, runtime: dict[str, Any]) -> Check:
    readme = repo_root / "README.md"
    try:
        text = readme.read_text(encoding="utf-8")
    except OSError as exc:
        return _check(
            "skills.packaged_claim",
            "fail",
            "The README could not be read.",
            readme=str(readme),
            error=type(exc).__name__,
        )
    packaged = sorted(runtime.get("builtin_skill_dirs", []))
    claims_200 = bool(
        re.search(r"200\+\s+predefined skills built in", text, re.IGNORECASE)
    )
    mismatch = claims_200 and len(packaged) < 200
    return _check(
        "skills.packaged_claim",
        "fail" if mismatch else "pass",
        "The README built-in skill claim exceeds the packaged source inventory."
        if mismatch
        else "The packaged skill inventory does not contradict the README claim.",
        readme=str(readme),
        claims_200_plus_built_in=claims_200,
        packaged_count=len(packaged),
        packaged_names=packaged,
    )


def check_resume_driver(repo_root: Path, interpreter: Path) -> Check:
    driver = (
        repo_root
        / "skills"
        / "supervising-daedalus-mock-study-runs"
        / "scripts"
        / "drive_stream_json_resume.py"
    )
    present = driver.is_file()
    if not present:
        return _check(
            "runtime.supervised_resume_driver",
            "fail",
            "No supervised stream-json resume driver is present.",
            path=str(driver),
            present=False,
            contract_status="missing",
            contract_safe=False,
            error="missing",
        )
    try:
        result = _run(
            [str(interpreter), str(driver), "--self-check"],
            cwd=repo_root,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return _check(
            "runtime.supervised_resume_driver",
            "fail",
            "The supervised resume driver self-check is unreachable.",
            path=str(driver),
            present=True,
            contract_status="unreachable",
            contract_safe=False,
            error=type(exc).__name__,
        )
    if result.returncode != 0:
        return _check(
            "runtime.supervised_resume_driver",
            "fail",
            "The supervised resume driver self-check returned a failure.",
            path=str(driver),
            present=True,
            contract_status="failed",
            contract_safe=False,
            error=f"exit_{result.returncode}",
        )
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError:
        return _check(
            "runtime.supervised_resume_driver",
            "fail",
            "The supervised resume driver self-check returned malformed JSON.",
            path=str(driver),
            present=True,
            contract_status="malformed",
            contract_safe=False,
            error="invalid_json",
        )
    required_defaults = {
        "auto_approve": False,
        "auto_mode": False,
        "dangerous_mode": False,
        "private_memory": False,
        "network_tools": False,
        "publication": False,
        "transfer": False,
    }
    self_check = report.get("self_check", {}) if isinstance(report, dict) else {}
    containment = report.get("containment", {}) if isinstance(report, dict) else {}
    human_gate = report.get("human_gate", {}) if isinstance(report, dict) else {}
    blocking_reasons = (
        report.get("blocking_reasons", []) if isinstance(report, dict) else []
    )
    same_snapshot = report.get("same_snapshot", {}) if isinstance(report, dict) else {}
    adapter_contract_safe = bool(
        isinstance(report, dict)
        and report.get("schema") == "daedalus-supervised-resume-driver/v1"
        and report.get("adapter_status") == "ready"
        and report.get("interface") == "local_graph_gateway_command_resume"
        and report.get("safe_defaults") == required_defaults
        and containment.get("available") is True
        and containment.get("enforcement")
        == "darwin_sandbox_exec_attempt_write_boundary"
        and containment.get("attempt_only_writes") is True
        and containment.get("network_denied_without_provider_authorization") is True
        and containment.get("tool_network_denied") is True
        and containment.get("tool_private_roots_denied") is True
        and containment.get("tool_workspace_only_writes") is True
        and containment.get("tool_undeclared_subprocesses_denied") is True
        and self_check.get("deterministic") is True
        and self_check.get("containment_probe_executed") is True
        and self_check.get("model_loaded") is False
        and self_check.get("service_started") is False
        and self_check.get("provider_activated") is False
        and same_snapshot.get("supervisor_source_frozen") is True
        and same_snapshot.get("cycle_worker_source_frozen") is True
        and not result.stderr.strip()
    )
    production_contract_safe = bool(
        adapter_contract_safe
        and report.get("status") == "ready"
        and report.get("production_status") == "ready"
        and human_gate.get("main_agent_execute_interrupts") is True
        and human_gate.get("synchronous_subagent_execute_interrupts") is True
        and human_gate.get("all_executable_actions_human_gated") is True
        and same_snapshot.get("production_git_identity_rechecked") is True
        and blocking_reasons == []
    )
    return _check(
        "runtime.supervised_resume_driver",
        "pass" if production_contract_safe else "fail",
        (
            "The supervised resume driver passed its deterministic production "
            "safety contract."
            if production_contract_safe
            else "The supervised resume driver is not safe for production execution."
        ),
        path=str(driver),
        present=True,
        contract_status=report.get("status") if isinstance(report, dict) else None,
        contract_safe=production_contract_safe,
        adapter_contract_safe=adapter_contract_safe,
        production_contract_safe=production_contract_safe,
        interface=report.get("interface") if isinstance(report, dict) else None,
        schema=report.get("schema") if isinstance(report, dict) else None,
        containment=containment if isinstance(containment, dict) else None,
        human_gate=human_gate if isinstance(human_gate, dict) else None,
        same_snapshot=same_snapshot if isinstance(same_snapshot, dict) else None,
        blocking_reasons=(
            blocking_reasons if isinstance(blocking_reasons, list) else None
        ),
        error=None if production_contract_safe else "unsafe_production_contract",
    )


def check_python_command(repo_root: Path, result: dict[str, Any]) -> Check:
    prompt_sources = [
        repo_root / "EvoScientist" / "prompts.py",
        *sorted((repo_root / "EvoScientist" / "subagents").glob("*.yaml")),
    ]
    documented_sources = []
    for source in prompt_sources:
        try:
            if "python -c" in source.read_text(encoding="utf-8"):
                documented_sources.append(str(source))
        except OSError:
            continue
    python_exit = result.get("python_exit")
    python3_exit = result.get("python3_exit")
    broken = bool(documented_sources) and python_exit != 0
    return _check(
        "runtime.documented_python_command",
        "fail" if broken else "pass",
        "Documented Python commands fail through the normal launcher environment."
        if broken
        else "Documented Python commands resolve through the normal launcher environment.",
        documented_sources=documented_sources,
        python_exit=python_exit,
        python3_exit=python3_exit,
        python_output=result.get("python_output", ""),
        python3_output=result.get("python3_output", ""),
    )


def summarize(checks: Sequence[Check]) -> dict[str, Any]:
    blocking = [item.check_id for item in checks if item.blocking]
    return {
        "schema": SCHEMA,
        "status": "blocked" if blocking else "ready",
        "blocking_check_ids": blocking,
        "checks": [asdict(item) for item in checks],
    }


_RUNTIME_PROBE = r"""
import json
from dataclasses import fields
from pathlib import Path
from EvoScientist.commands import manager
from EvoScientist.config.onboard.constants import VALID_PROVIDERS
from EvoScientist.config.settings import EvoScientistConfig

commands = manager.get_all_commands()
print(json.dumps({
    "primary_commands": [command.name for command in commands],
    "aliases": {command.name: list(command.alias) for command in commands},
    "subcommands": {
        command.name: [subcommand.name for subcommand in command.subcommands]
        for command in commands
    },
    "providers": sorted(VALID_PROVIDERS),
    "config_fields": sorted(item.name for item in fields(EvoScientistConfig)),
    "builtin_skill_dirs": sorted(
        path.name
        for path in (Path(__import__("EvoScientist").__file__).parent / "skills").iterdir()
        if path.is_dir()
    ),
}))
"""

_PYTHON_COMMAND_PROBE = r"""
import json
import sys
from EvoScientist.backends import CustomSandboxBackend

backend = CustomSandboxBackend(root_dir=sys.argv[1], virtual_mode=True)
python_result = backend.execute('python -c "print(123)"')
python3_result = backend.execute('python3 -c "print(123)"')
print(json.dumps({
    "python_exit": python_result.exit_code,
    "python3_exit": python3_result.exit_code,
    "python_output": python_result.output,
    "python3_output": python3_result.output,
}))
"""


def _json_probe(
    interpreter: Path,
    source: str,
    *,
    cwd: Path,
    extra_args: Sequence[str] = (),
) -> tuple[dict[str, Any] | None, str | None]:
    try:
        result = _run(
            [str(interpreter), "-c", source, *extra_args],
            cwd=cwd,
            timeout=45,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, type(exc).__name__
    if result.returncode != 0:
        return None, f"exit {result.returncode}: {result.stderr.strip()}"
    try:
        return json.loads(result.stdout), None
    except json.JSONDecodeError:
        return None, "probe returned invalid JSON"


def run_preflight(
    *,
    repo_root: Path,
    workdir: Path,
    launcher_name: str,
    webui_source_dir: Path | None,
) -> dict[str, Any]:
    repo_root = repo_root.expanduser().resolve()
    workdir = workdir.expanduser().resolve()
    workdir_check = check_workdir(workdir)
    checks: list[Check] = [workdir_check]

    if workdir_check.status != "pass":
        checks.append(
            _check(
                "runtime.probes_skipped",
                "fail",
                "Runtime probes were not executed because the work directory failed the data-only gate.",
                workdir=str(workdir),
            )
        )
        return summarize(checks)

    launcher = _resolve_launcher(launcher_name)
    if launcher is None:
        checks.append(
            _check(
                "launcher.resolved",
                "fail",
                "The Daedalus launcher could not be resolved.",
                launcher=launcher_name,
            )
        )
        return summarize(checks)
    checks.append(
        _check(
            "launcher.resolved",
            "pass",
            "The Daedalus launcher resolved to an exact path.",
            launcher=str(launcher),
        )
    )

    interpreter = _launcher_interpreter(launcher)
    if interpreter is None:
        checks.append(
            _check(
                "launcher.interpreter",
                "fail",
                "The exact interpreter behind the launcher could not be resolved.",
                launcher=str(launcher),
            )
        )
        return summarize(checks)
    checks.append(
        _check(
            "launcher.interpreter",
            "pass",
            "The exact interpreter behind the launcher resolved.",
            interpreter=str(interpreter),
        )
    )

    if workdir_check.status == "pass":
        try:
            help_result = _run([str(launcher), "--help"], cwd=workdir)
        except (OSError, subprocess.TimeoutExpired) as exc:
            help_result = None
            help_error = type(exc).__name__
        else:
            help_error = None
        help_ok = bool(
            help_result
            and help_result.returncode == 0
            and "--output-format" in help_result.stdout
            and "stream-json" in help_result.stdout
        )
        checks.append(
            _check(
                "launcher.help",
                "pass" if help_ok else "fail",
                "Launcher help exposes the required headless interface."
                if help_ok
                else "Launcher help failed or omitted the required headless interface.",
                exit_code=help_result.returncode if help_result else None,
                error=help_error,
            )
        )

        import_probe, import_error = _json_probe(
            interpreter,
            "import EvoScientist, json; print(json.dumps({'path': EvoScientist.__file__}))",
            cwd=workdir,
        )
        expected_import = (repo_root / "EvoScientist" / "__init__.py").resolve()
        imported = (
            Path(import_probe["path"]).resolve()
            if import_probe and isinstance(import_probe.get("path"), str)
            else None
        )
        import_ok = imported == expected_import
        checks.append(
            _check(
                "launcher.import_identity",
                "pass" if import_ok else "fail",
                "The launcher interpreter imports the intended repository source."
                if import_ok
                else "The launcher interpreter imports a different or unknown source.",
                expected=str(expected_import),
                imported=str(imported) if imported else None,
                error=import_error,
            )
        )

        runtime, runtime_error = _json_probe(
            interpreter,
            _RUNTIME_PROBE,
            cwd=workdir,
        )
        if runtime is None:
            checks.append(
                _check(
                    "runtime.inventory_probe",
                    "fail",
                    "The runtime inventory probe failed.",
                    error=runtime_error,
                )
            )
        else:
            checks.append(
                _check(
                    "runtime.inventory_probe",
                    "pass",
                    "The runtime inventory probe returned structured data.",
                )
            )
            checks.extend(
                [
                    check_required_commands(runtime),
                    check_required_channels(runtime),
                    check_provider_inventory(runtime),
                    check_webui_config(runtime),
                    check_builtin_skill_claim(repo_root, runtime),
                ]
            )

        with tempfile.TemporaryDirectory(prefix="daedalus-preflight-") as tmp:
            python_probe, python_error = _json_probe(
                interpreter,
                _PYTHON_COMMAND_PROBE,
                cwd=workdir,
                extra_args=(tmp,),
            )
        if python_probe is None:
            checks.append(
                _check(
                    "runtime.documented_python_command",
                    "fail",
                    "The installed-launcher Python command probe failed.",
                    error=python_error,
                )
            )
        else:
            checks.append(check_python_command(repo_root, python_probe))

    commit = _run(["git", "rev-parse", "HEAD"], cwd=repo_root)
    dirty = _run(["git", "status", "--porcelain"], cwd=repo_root)
    if commit.returncode == 0 and dirty.returncode == 0:
        dirty_count = len([line for line in dirty.stdout.splitlines() if line.strip()])
        checks.append(
            _check(
                "source.git_identity",
                "warn" if dirty_count else "pass",
                "The repository has user-owned changes that require a separate frozen manifest."
                if dirty_count
                else "The repository is clean at an exact commit.",
                blocking=False,
                commit=commit.stdout.strip(),
                dirty_entry_count=dirty_count,
            )
        )
    else:
        checks.append(
            _check(
                "source.git_identity",
                "fail",
                "The repository Git identity could not be read.",
            )
        )

    checks.extend(
        [
            check_webui_package(repo_root),
            check_webui_source_dir(
                webui_source_dir.expanduser().resolve()
                if webui_source_dir is not None
                else None
            ),
            check_resume_driver(repo_root, interpreter),
        ]
    )
    return summarize(checks)


def _parser() -> argparse.ArgumentParser:
    default_root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=default_root)
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument("--launcher", default="EvoSci")
    parser.add_argument("--webui-source-dir", type=Path)
    parser.add_argument("--pretty", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = run_preflight(
        repo_root=args.repo_root,
        workdir=args.workdir,
        launcher_name=args.launcher,
        webui_source_dir=args.webui_source_dir,
    )
    print(json.dumps(report, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    sys.exit(main())
