import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "skills" / "supervising-daedalus-mock-study-runs"


def test_supervision_documents_verified_real_single_shot_interface():
    reference = (BASE / "references" / "current-daedalus-interface.md").read_text(
        encoding="utf-8"
    )

    for token in (
        "EvoSci --mode run",
        "--name",
        "--prompt",
        "--workdir",
        "--output-format stream-json",
        "--no-auto-mode",
        "EvoSci --help",
        "EvoScientist.__file__",
        "daedalus_preflight.py",
        "JSON status `ready`",
        "exact interpreter",
    ):
        assert token in reference
    assert "defaults to unattended auto-mode" in reference
    assert "does not execute a study" in reference
    assert "conversation resume, not interrupt resume" in reference
    assert "LocalGraphGateway" in reference
    assert "Command(resume=...)" in reference
    assert "drive_stream_json_resume.py start" in reference


def test_supervision_preflight_is_present_and_read_only_by_contract():
    script = BASE / "scripts" / "daedalus_preflight.py"
    source = script.read_text(encoding="utf-8")

    assert script.is_file()
    assert "daedalus-capability-preflight/v1" in source
    assert "does not load user configuration" in source
    assert "launch a model or service" in source
    assert '"status": "blocked" if blocking else "ready"' in source
    assert "return summarize(checks)" in source


def test_attempt_manifest_isolates_native_evidence_and_identity():
    manifest = json.loads(
        (BASE / "templates" / "attempt-manifest.json").read_text(encoding="utf-8")
    )

    assert manifest["schema"] == "daedalus-mock-study-attempt/v1"
    paths = [
        manifest[key] for key in ("native_events_path", "stderr_path", "status_path")
    ]
    assert len(paths) == len(set(paths))
    assert paths == ["native-events.jsonl", "stderr.log", "status.json"]
    assert manifest["workdir_kind"] == "data_only"
    for key in (
        "attempt_id",
        "run_id",
        "thread_id",
        "source_commit",
        "imported_package_path",
        "monotonic_started_seconds",
        "monotonic_finished_seconds",
    ):
        assert key in manifest
    assert manifest["run_id_authority"] == "archimedes_supervisor"
    assert manifest["native_run_id"] is None
    assert manifest["native_run_id_status"] == "not_exposed_by_local_stream_gateway"
    assert manifest["thread_id_authority"] == "exact_local_gateway_run_request"
    assert manifest["interface"] == "local_graph_gateway_command_resume"


def test_run_ledger_is_append_only_typed_and_stage_linked():
    lines = (
        (BASE / "templates" / "run-ledger.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    entries = [json.loads(line) for line in lines]

    assert entries
    assert all(entry["attempt_id"] == "attempt-001" for entry in entries)
    assert all(entry["stage"] for entry in entries)
    assert all(entry["evidence_ref"] for entry in entries)
    assert all(
        entry["schema"] == "daedalus-supervisor-ledger-entry/v1" for entry in entries
    )
    assert all("previous_record_sha256" in entry for entry in entries)
    assert all("record_sha256" in entry for entry in entries)
    assert all(entry["entry_type"] != "daedalus_event" for entry in entries)
    assert "Template only" in entries[0]["summary"]


def test_supervision_stops_on_silent_success_and_never_substitutes():
    skill = (BASE / "SKILL.md").read_text(encoding="utf-8")

    assert "Silent success" in skill
    assert "do not substitute" in skill
    assert "distinct evidence paths" in skill
    assert "drive_stream_json_resume.py decide" in skill
    assert "Study authorization is not tool approval" in skill
    assert "Rejection stops without resume" in skill


def test_execution_allowlist_is_exact_and_network_denied():
    allowlist = json.loads(
        (BASE / "templates" / "execution-allowlist.json").read_text(encoding="utf-8")
    )

    assert allowlist["schema"] == "daedalus-supervisor-allowlist/v1"
    assert allowlist["allowed_actions"]
    action = allowlist["allowed_actions"][0]
    assert action["args"]["command"]
    assert action["argv"]
    assert action["path_argument_indexes"]
    assert action["path_sha256"]
    assert allowlist["network_operations_allowed"] is False
    assert allowlist["publication_allowed"] is False
    assert allowlist["transfer_allowed"] is False


def test_runtime_template_names_credentials_without_storing_them():
    runtime = json.loads(
        (BASE / "templates" / "supervisor-runtime.json").read_text(encoding="utf-8")
    )

    assert runtime["schema"] == "daedalus-supervisor-runtime/v1"
    assert runtime["credential_env_names"] == []
    assert runtime["config_overrides"] == {}
    assert not any("api_key" in key.lower() for key in runtime)
