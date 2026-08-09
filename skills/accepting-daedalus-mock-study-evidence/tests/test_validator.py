import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "skills" / "accepting-daedalus-mock-study-evidence"
VALID = BASE / "tests" / "fixtures" / "valid-study"
VALIDATOR = BASE / "scripts" / "validate_mock_study.py"
DRIVER = (
    ROOT
    / "skills"
    / "supervising-daedalus-mock-study-runs"
    / "scripts"
    / "drive_stream_json_resume.py"
)
FAKE_CYCLE = (
    ROOT
    / "skills"
    / "supervising-daedalus-mock-study-runs"
    / "tests"
    / "fixtures"
    / "fake_daedalus_cycle.py"
)


def _load_validator():
    spec = importlib.util.spec_from_file_location("validate_mock_study", VALIDATOR)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_driver():
    spec = importlib.util.spec_from_file_location(
        "acceptance_integration_resume_driver", DRIVER
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, value: dict) -> Path:
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
    return path


def _build_completed_supervised_study(tmp_path: Path) -> Path:
    driver = _load_driver()
    attempt_dir = tmp_path / "attempt-001"
    workdir = attempt_dir / "workspace"
    workdir.mkdir(parents=True)
    (workdir / "analysis.py").write_text(
        "from pathlib import Path\nPath('unused.json').write_text('{}')\n",
        encoding="utf-8",
    )

    packet_value = json.loads((VALID / "study-packet.json").read_text(encoding="utf-8"))
    packet = _write_json(tmp_path / "study-packet.json", packet_value)
    authorization = tmp_path / "authorization-record.json"
    shutil.copy2(VALID / "authorization-record.json", authorization)
    allowlist = _write_json(
        tmp_path / "execution-allowlist.json",
        {
            "schema": "daedalus-supervisor-allowlist/v1",
            "packet_id": packet_value["packet_id"],
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
            "allowed_artifact_paths": ["daedalus-primary-study-report.json"],
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
                        "imported": packet_value["source_identity"][
                            "expected_import_root"
                        ],
                        "expected": packet_value["source_identity"][
                            "expected_import_root"
                        ],
                    },
                },
                {
                    "check_id": "source.git_identity",
                    "status": "pass",
                    "blocking": False,
                    "evidence": {
                        "commit": packet_value["source_identity"]["expected_commit"]
                    },
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
    runtime = _write_json(
        tmp_path / "supervisor-runtime.json",
        {
            "schema": "daedalus-supervisor-runtime/v1",
            "packet_id": packet_value["packet_id"],
            "provider": "fixture",
            "model": "fixture",
            "credential_env_names": [],
            "config_overrides": {},
        },
    )
    prompt = tmp_path / "prompt.txt"
    prompt.write_text(
        "Run only the frozen synthetic acceptance fixture.", encoding="utf-8"
    )
    supervisor = driver.SupervisedResumeDriver(
        driver.SupervisorConfig(
            repo_root=ROOT,
            packet_path=packet,
            authorization_path=authorization,
            allowlist_path=allowlist,
            preflight_path=preflight,
            runtime_config_path=runtime,
            prompt_path=prompt,
            attempt_dir=attempt_dir,
            workdir=workdir,
            launcher=Path(sys.executable),
            attempt_id="attempt-001",
            timeout_seconds=2.0,
            max_cycles=3,
            adapter_argv=(
                sys.executable,
                str(FAKE_CYCLE),
                "--scenario",
                "acceptance_happy",
            ),
        )
    )
    awaiting = supervisor.start()
    assert awaiting["outcome"] == "awaiting_approval"
    completed = supervisor.decide(
        decision="approve",
        request_digest=awaiting["pending_request_digest"],
        operator="fixture-human",
    )
    assert completed["outcome"] == "completed"

    evidence_dir = attempt_dir / "supervisor-evidence"
    manifest = json.loads((evidence_dir / "attempt-manifest.json").read_text())
    identities = {
        "packet_id": packet_value["packet_id"],
        "attempt_id": manifest["attempt_id"],
        "run_id": manifest["run_id"],
        "thread_id": manifest["thread_id"],
    }
    artifacts = []
    for logical_path, physical_path, role, producer, stage in (
        (
            "native-events.jsonl",
            evidence_dir / "native-events.jsonl",
            "native_event_stream",
            "daedalus",
            "synthetic_analysis",
        ),
        (
            "status.json",
            evidence_dir / "status.json",
            "terminal_status",
            "daedalus_runtime",
            "primary_report",
        ),
        (
            "daedalus-primary-study-report.json",
            workdir / "daedalus-primary-study-report.json",
            "primary_study_report",
            "daedalus",
            "primary_report",
        ),
    ):
        artifacts.append(
            {
                "path": logical_path,
                "role": role,
                "producer": producer,
                "attempt_id": identities["attempt_id"],
                "stage": stage,
                "byte_size": physical_path.stat().st_size,
                "sha256": hashlib.sha256(physical_path.read_bytes()).hexdigest(),
                "verification_status": "directly_verified",
            }
        )
    _write_json(
        evidence_dir / "evidence-manifest.json",
        {
            "schema": "daedalus-mock-study-evidence-manifest/v1",
            **identities,
            "layout": "supervised_attempt/v1",
            "artifacts": artifacts,
        },
    )
    stage_fields = {
        "question_formulation": "research_question",
        "hypothesis_generation": "hypothesis",
        "method_selection": "methods",
        "synthetic_analysis": "analyses_performed",
        "result_interpretation": "measured_results",
        "primary_report": "outputs_produced",
    }
    _write_json(
        evidence_dir / "archimedes-independent-evidence-report.json",
        {
            "schema": "archimedes-independent-evidence-report/v1",
            **identities,
            "author": "Archimedes",
            "actually_executed": list(stage_fields),
            "workflow_stage_evidence": {
                stage: [
                    {
                        "evidence_ref": ("daedalus-primary-study-report.json#" + field),
                        "evidence_class": "observed_result",
                    }
                ]
                for stage, field in stage_fields.items()
            },
            "directly_verified_artifacts": [item["path"] for item in artifacts],
            "expected_outputs": 1,
            "produced_outputs": 1,
            "checksums_and_provenance": "See evidence-manifest.json.",
            "missing_empty_stale_unlinked_evidence": [],
            "failures_retries_timing_stop_conditions": {
                "failures": [],
                "retries": [],
                "elapsed_seconds": 0.1,
                "stop_conditions_triggered": [],
            },
            "concerns_about_daedalus": [
                "This deterministic adapter establishes E1/E2 harness evidence only."
            ],
            "evidence_ceiling": "E2",
            "blockers": [],
            "verdict": "accepted",
            "verdict_reason": (
                "The deterministic supervised fixture is complete and internally "
                "consistent; this is not E3 runtime evidence."
            ),
        },
    )
    return attempt_dir


def test_unsupervised_flat_fixture_is_rejected_by_default():
    result = _load_validator().validate_study(VALID)

    assert result["valid"] is False
    assert "supervised_layout_required" in result["errors"]


def test_legacy_fixture_mode_is_explicit_and_cannot_return_accepted():
    result = _load_validator().validate_study(VALID, allow_legacy_fixture=True)

    assert result == {"valid": True, "verdict": "fixture_valid", "errors": []}


def test_completed_supervised_attempt_is_accepted_in_place(tmp_path):
    run_dir = _build_completed_supervised_study(tmp_path)

    result = _load_validator().validate_study(run_dir)

    assert result == {"valid": True, "verdict": "accepted", "errors": []}


def test_supervised_attempt_manifest_digest_is_recomputed(tmp_path):
    run_dir = _build_completed_supervised_study(tmp_path)
    manifest_path = run_dir / "supervisor-evidence" / "attempt-manifest.json"
    _rewrite_json(manifest_path, lambda manifest: manifest.update(thread_id="forged"))

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert "attempt_manifest_digest_mismatch" in result["errors"]


def test_supervised_source_snapshot_digest_is_recomputed(tmp_path):
    run_dir = _build_completed_supervised_study(tmp_path)
    source_path = run_dir / "supervisor-evidence" / "supervisor-source.py"
    source_path.write_text("# forged after execution\n", encoding="utf-8")

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert "supervisor_input_digest_mismatch:supervisor_source" in result["errors"]


def test_adapter_evidence_cannot_be_upgraded_to_e3(tmp_path):
    run_dir = _build_completed_supervised_study(tmp_path)
    report_path = (
        run_dir / "supervisor-evidence" / "archimedes-independent-evidence-report.json"
    )
    _rewrite_json(report_path, lambda report: report.update(evidence_ceiling="E3"))

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert "adapter_evidence_overclaim" in result["errors"]


def test_unrelated_unknown_fragment_cannot_certify_all_workflow_stages(tmp_path):
    run_dir = _build_completed_supervised_study(tmp_path)
    report_path = (
        run_dir / "supervisor-evidence" / "archimedes-independent-evidence-report.json"
    )
    packet = json.loads(
        (run_dir / "supervisor-evidence" / "study-packet.json").read_text()
    )

    def weaken(report):
        report["workflow_stage_evidence"] = {
            stage: [
                {
                    "evidence_ref": "daedalus-primary-study-report.json#limitations",
                    "evidence_class": "unknown",
                }
            ]
            for stage in packet["workflow_stages"]
        }

    _rewrite_json(report_path, weaken)
    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert any(
        error.startswith("stage_evidence_class_insufficient:")
        for error in result["errors"]
    )
    assert any(
        error.startswith("stage_evidence_fragment_mismatch:")
        for error in result["errors"]
    )


def test_supervised_attempt_cannot_invent_a_native_run_id(tmp_path):
    run_dir = _build_completed_supervised_study(tmp_path)
    manifest_path = run_dir / "supervisor-evidence" / "attempt-manifest.json"

    def forge_native_identity(manifest):
        manifest["native_run_id"] = "invented-native-run"
        payload = {
            key: value for key, value in manifest.items() if key != "manifest_sha256"
        }
        manifest["manifest_sha256"] = hashlib.sha256(
            json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()

    _rewrite_json(manifest_path, forge_native_identity)

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert "invented_native_run_id" in result["errors"]


def test_supervised_ledger_hash_chain_is_recomputed(tmp_path):
    run_dir = _build_completed_supervised_study(tmp_path)
    ledger_path = run_dir / "supervisor-evidence" / "run-ledger.jsonl"
    entries = [json.loads(line) for line in ledger_path.read_text().splitlines()]
    entries[1]["summary"] = "forged after the run"
    ledger_path.write_text(
        "\n".join(json.dumps(entry, sort_keys=True) for entry in entries) + "\n",
        encoding="utf-8",
    )

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert "supervisor_ledger_digest_mismatch:2" in result["errors"]


def test_supervised_pending_decision_digest_is_recomputed(tmp_path):
    run_dir = _build_completed_supervised_study(tmp_path)
    pending_path = run_dir / "supervisor-evidence" / "decisions" / "pending-001.json"

    def forge_pending_payload(pending):
        pending["payload"]["action_requests"][0]["args"]["command"] = (
            "python3 forged.py"
        )

    _rewrite_json(pending_path, forge_pending_payload)

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert "supervisor_pending_digest_mismatch:1" in result["errors"]


def test_supervised_attempt_requires_complete_cycle_history(tmp_path):
    run_dir = _build_completed_supervised_study(tmp_path)
    (run_dir / "supervisor-evidence" / "cycles" / "worker-result-002.json").unlink()

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert "supervisor_worker_result_missing:2" in result["errors"]


def test_supervised_stage_evidence_reference_must_resolve(tmp_path):
    run_dir = _build_completed_supervised_study(tmp_path)
    report_path = (
        run_dir / "supervisor-evidence" / "archimedes-independent-evidence-report.json"
    )

    def break_stage_reference(report):
        report["workflow_stage_evidence"]["method_selection"][0]["evidence_ref"] = (
            "daedalus-primary-study-report.json#missing_field"
        )

    _rewrite_json(report_path, break_stage_reference)

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert "stage_evidence_fragment_unresolved:method_selection:1" in result["errors"]


def test_missing_expected_artifact_fails_closed(tmp_path):
    run_dir = tmp_path / "run"
    shutil.copytree(VALID, run_dir)
    (run_dir / "daedalus-primary-study-report.json").unlink()

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert result["verdict"] == "failed"
    assert "missing_artifact:daedalus-primary-study-report.json" in result["errors"]


def _copy_valid(tmp_path: Path) -> Path:
    run_dir = tmp_path / "run"
    shutil.copytree(VALID, run_dir)
    return run_dir


def _rewrite_json(path: Path, mutate) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))
    mutate(value)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _refresh_artifact_hash(run_dir: Path, artifact_name: str) -> None:
    artifact = run_dir / artifact_name
    manifest_path = run_dir / "evidence-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = next(
        item for item in manifest["artifacts"] if item["path"] == artifact_name
    )
    entry["byte_size"] = artifact.stat().st_size
    entry["sha256"] = hashlib.sha256(artifact.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def test_empty_artifact_with_success_narration_is_silent_success(tmp_path):
    run_dir = _copy_valid(tmp_path)
    (run_dir / "daedalus-primary-study-report.json").write_bytes(b"")

    result = _load_validator().validate_study(run_dir)

    assert "empty_artifact:daedalus-primary-study-report.json" in result["errors"]
    assert "silent_success" in result["errors"]


def test_mismatched_run_and_thread_identity_fails_closed(tmp_path):
    run_dir = _copy_valid(tmp_path)
    _rewrite_json(
        run_dir / "daedalus-primary-study-report.json",
        lambda value: value.update(run_id="other-run", thread_id="other-thread"),
    )

    result = _load_validator().validate_study(run_dir)

    assert "run_id_mismatch:daedalus-primary-study-report.json" in result["errors"]
    assert "thread_id_mismatch:daedalus-primary-study-report.json" in result["errors"]


def test_corrupted_checksum_and_schema_fail_closed(tmp_path):
    run_dir = _copy_valid(tmp_path)
    _rewrite_json(
        run_dir / "daedalus-primary-study-report.json",
        lambda value: value.update(schema="wrong-schema/v1"),
    )

    result = _load_validator().validate_study(run_dir)

    assert "checksum_mismatch:daedalus-primary-study-report.json" in result["errors"]
    assert "schema_mismatch:daedalus-primary-study-report.json" in result["errors"]


def test_primary_report_measured_results_must_match_synthetic_inputs(tmp_path):
    run_dir = _copy_valid(tmp_path)

    def corrupt_result(value):
        value["measured_results"]["difference"] = 2.0

    _rewrite_json(run_dir / "daedalus-primary-study-report.json", corrupt_result)

    result = _load_validator().validate_study(run_dir)

    assert "measured_result_mismatch:difference" in result["errors"]


def test_privacy_violation_in_ledger_stops_acceptance(tmp_path):
    run_dir = _copy_valid(tmp_path)
    with (run_dir / "run-ledger.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "sequence": 9,
                    "timestamp": "2026-08-07T00:00:08Z",
                    "entry_type": "failure",
                    "attempt_id": "attempt-001",
                    "stage": "synthetic_analysis",
                    "source": "archimedes",
                    "evidence_ref": "native-events.jsonl#event-privacy",
                    "privacy_violation": True,
                }
            )
            + "\n"
        )

    result = _load_validator().validate_study(run_dir)

    assert "privacy_violation" in result["errors"]
    assert result["verdict"] == "stopped"


def test_unauthorized_provider_or_external_action_stops_acceptance(tmp_path):
    run_dir = _copy_valid(tmp_path)
    with (run_dir / "run-ledger.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "sequence": 9,
                    "timestamp": "2026-08-07T00:00:08Z",
                    "entry_type": "operator_action",
                    "attempt_id": "attempt-001",
                    "stage": "synthetic_analysis",
                    "source": "daedalus",
                    "evidence_ref": "native-events.jsonl#event-action",
                    "action": "activate_paid_provider",
                    "authorized": False,
                }
            )
            + "\n"
        )

    result = _load_validator().validate_study(run_dir)

    assert "unauthorized_action:activate_paid_provider" in result["errors"]
    assert result["verdict"] == "stopped"


def test_retry_cannot_overwrite_prior_attempt_evidence(tmp_path):
    run_dir = _copy_valid(tmp_path)

    def duplicate_path(value):
        duplicate = dict(value["artifacts"][0])
        duplicate["attempt_id"] = "attempt-002"
        value["artifacts"].append(duplicate)

    _rewrite_json(run_dir / "evidence-manifest.json", duplicate_path)

    result = _load_validator().validate_study(run_dir)

    assert "retry_overwrite:native-events.jsonl" in result["errors"]


def test_partial_stage_coverage_cannot_be_presented_as_accepted(tmp_path):
    run_dir = _copy_valid(tmp_path)
    events = (run_dir / "native-events.jsonl").read_text(encoding="utf-8").splitlines()
    (run_dir / "native-events.jsonl").write_text(
        "\n".join(line for line in events if '"stage":"method_selection"' not in line)
        + "\n",
        encoding="utf-8",
    )

    result = _load_validator().validate_study(run_dir)

    assert (
        "accepted_with_incomplete_stage_coverage:method_selection" in result["errors"]
    )
    assert result["verdict"] == "partial"


def test_incomplete_study_packet_fails_closed(tmp_path):
    run_dir = _copy_valid(tmp_path)
    (run_dir / "study-packet.json").write_text(
        json.dumps(
            {
                "schema": "daedalus-mock-study-packet/v1",
                "packet_id": "synthetic-vertical-acceptance-001",
                "synthetic_study": True,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert "required_field_missing:study-packet.json:objective" in result["errors"]


def test_null_stage_inventory_fails_closed_without_crashing(tmp_path):
    run_dir = _copy_valid(tmp_path)
    _rewrite_json(
        run_dir / "study-packet.json",
        lambda packet: packet.update(workflow_stages=None),
    )

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert "invalid_workflow_stages" in result["errors"]


def test_execution_without_authorization_stops_validation(tmp_path):
    run_dir = _copy_valid(tmp_path)
    _rewrite_json(
        run_dir / "authorization-record.json",
        lambda record: record.update(study_execution_authorized=False),
    )

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert result["verdict"] == "stopped"
    assert "study_execution_not_authorized" in result["errors"]


def test_authorized_execution_requires_nonempty_approval_evidence(tmp_path):
    run_dir = _copy_valid(tmp_path)
    _rewrite_json(
        run_dir / "authorization-record.json",
        lambda record: record.update(approval_evidence=None),
    )

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert "study_execution_approval_evidence_missing" in result["errors"]


@pytest.mark.parametrize(
    "field",
    [
        "tool_action_approval_policy",
        "tool_action_preapproval_authorized",
        "evoscientist_core_modification_authorized",
    ],
)
def test_authorization_record_requires_explicit_human_gate_fields(tmp_path, field):
    run_dir = _copy_valid(tmp_path)

    def remove_field(record):
        record.pop(field)

    _rewrite_json(run_dir / "authorization-record.json", remove_field)

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert (
        f"required_field_missing:authorization-record.json:{field}" in result["errors"]
    )


def test_authorization_record_rejects_tool_action_preapproval(tmp_path):
    run_dir = _copy_valid(tmp_path)
    _rewrite_json(
        run_dir / "authorization-record.json",
        lambda record: record.update(tool_action_preapproval_authorized=True),
    )

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert "tool_action_human_gate_invalid" in result["errors"]


def test_authorization_record_cannot_exceed_frozen_packet(tmp_path):
    run_dir = _copy_valid(tmp_path)
    _rewrite_json(
        run_dir / "authorization-record.json",
        lambda record: record.update(paid_provider_activation_authorized=True),
    )

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert (
        "authorization_exceeds_packet:paid_provider_activation_authorized"
        in result["errors"]
    )


def test_authorization_boundary_must_be_an_explicit_boolean(tmp_path):
    run_dir = _copy_valid(tmp_path)
    _rewrite_json(
        run_dir / "authorization-record.json",
        lambda record: record.update(private_memory_access_authorized="false"),
    )

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert (
        "authorization_boundary_mismatch:private_memory_access_authorized"
        in result["errors"]
    )


def test_symlinked_evidence_cannot_escape_run_directory(tmp_path):
    run_dir = _copy_valid(tmp_path)
    outside = tmp_path / "outside.json"
    outside.write_text('{"outside":true}\n', encoding="utf-8")
    escaped = run_dir / "escaped-artifact.json"
    escaped.symlink_to(outside)
    _rewrite_json(
        run_dir / "evidence-manifest.json",
        lambda manifest: manifest["artifacts"][0].update(path=escaped.name),
    )
    _refresh_artifact_hash(run_dir, escaped.name)

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert "unsafe_artifact_path:escaped-artifact.json" in result["errors"]


def test_validator_rejects_a_symlinked_run_root(tmp_path):
    run_dir = tmp_path / "run-link"
    run_dir.symlink_to(VALID, target_is_directory=True)

    result = _load_validator().validate_study(run_dir)

    assert result == {
        "valid": False,
        "verdict": "failed",
        "errors": ["unsafe_run_dir"],
    }


def test_validator_does_not_follow_a_symlinked_supervisor_root(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "workspace").mkdir()
    (run_dir / "supervisor-evidence").symlink_to(VALID, target_is_directory=True)

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert "unsafe_supervised_control_root" in result["errors"]


def test_manifest_verification_status_must_be_direct(tmp_path):
    run_dir = _copy_valid(tmp_path)
    _rewrite_json(
        run_dir / "evidence-manifest.json",
        lambda manifest: manifest["artifacts"][0].update(verification_status="pending"),
    )

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert "artifact_not_directly_verified:native-events.jsonl" in result["errors"]


def test_manifest_metadata_must_match_frozen_expected_inventory(tmp_path):
    run_dir = _copy_valid(tmp_path)

    def forge_manifest_metadata(manifest):
        manifest["artifacts"][0].update(
            role="forged_role", producer="forged_producer", stage="forged_stage"
        )

    _rewrite_json(run_dir / "evidence-manifest.json", forge_manifest_metadata)

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert "artifact_role_mismatch:native-events.jsonl" in result["errors"]
    assert "artifact_producer_mismatch:native-events.jsonl" in result["errors"]
    assert "artifact_stage_mismatch:native-events.jsonl" in result["errors"]


def test_expected_artifact_inventory_cannot_be_silently_omitted(tmp_path):
    run_dir = _copy_valid(tmp_path)

    def add_expected_artifact(packet):
        packet["expected_artifacts"].append("missing-required-output.json")

    _rewrite_json(run_dir / "study-packet.json", add_expected_artifact)

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert (
        "expected_artifact_unmanifested:missing-required-output.json"
        in result["errors"]
    )


def test_output_count_mismatch_cannot_be_accepted(tmp_path):
    run_dir = _copy_valid(tmp_path)
    _rewrite_json(
        run_dir / "archimedes-independent-evidence-report.json",
        lambda report: report.update(produced_outputs=99),
    )

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert "output_count_mismatch:99!=1" in result["errors"]


def test_declared_success_without_terminal_event_is_silent_success(tmp_path):
    run_dir = _copy_valid(tmp_path)
    _rewrite_json(
        run_dir / "status.json",
        lambda status: status.update(terminal_event_observed=False),
    )
    _refresh_artifact_hash(run_dir, "status.json")

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert "silent_success:terminal_event_missing" in result["errors"]


def test_malformed_nested_packet_fields_fail_without_crashing(tmp_path):
    run_dir = _copy_valid(tmp_path)

    def corrupt_nested_fields(packet):
        packet["provider_cost_boundary"] = []
        packet["retention_transfer_publication"] = None
        packet["prohibited_operations"] = None
        packet["acceptance_criteria"] = []
        packet["workflow_stages"] = [{}]

    _rewrite_json(run_dir / "study-packet.json", corrupt_nested_fields)

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert "invalid_provider_cost_boundary" in result["errors"]
    assert "invalid_workflow_stages" in result["errors"]


def test_failed_terminal_status_cannot_be_accepted(tmp_path):
    run_dir = _copy_valid(tmp_path)
    _rewrite_json(
        run_dir / "status.json",
        lambda status: status.update(exit_code=1, declared_success=False),
    )
    _refresh_artifact_hash(run_dir, "status.json")

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert "terminal_status_failed" in result["errors"]


def test_empty_primary_method_cannot_be_accepted(tmp_path):
    run_dir = _copy_valid(tmp_path)
    _rewrite_json(
        run_dir / "daedalus-primary-study-report.json",
        lambda report: report.update(methods=""),
    )
    _refresh_artifact_hash(run_dir, "daedalus-primary-study-report.json")

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert (
        "required_field_empty:daedalus-primary-study-report.json:methods"
        in result["errors"]
    )


def test_this_vertical_fixture_requires_exactly_one_frozen_input(tmp_path):
    run_dir = _copy_valid(tmp_path)

    def add_second_input(packet):
        packet["input_inventory"].append(dict(packet["input_inventory"][0]))
        packet["input_inventory"][1]["id"] = "unexpected-second-input"

    _rewrite_json(run_dir / "study-packet.json", add_second_input)

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert "unsupported_input_inventory_count:2" in result["errors"]


def test_native_output_references_must_resolve_inside_run_directory(tmp_path):
    run_dir = _copy_valid(tmp_path)
    events_path = run_dir / "native-events.jsonl"
    events = [json.loads(line) for line in events_path.read_text().splitlines()]
    events[0]["output_ref"] = "missing-output.json#question"
    events_path.write_text(
        "\n".join(json.dumps(event, separators=(",", ":")) for event in events) + "\n",
        encoding="utf-8",
    )
    _refresh_artifact_hash(run_dir, "native-events.jsonl")

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert "native_output_ref_unresolved:1" in result["errors"]


def test_attempt_capture_paths_must_be_unique_present_and_exact(tmp_path):
    run_dir = _copy_valid(tmp_path)

    def collapse_capture_paths(attempt):
        attempt["native_events_path"] = "missing.log"
        attempt["stderr_path"] = "missing.log"
        attempt["status_path"] = "missing.log"

    _rewrite_json(run_dir / "attempt-manifest.json", collapse_capture_paths)

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert "attempt_capture_paths_not_unique" in result["errors"]
    assert "attempt_capture_path_mismatch:native_events_path" in result["errors"]


def test_boolean_output_counts_do_not_equal_integer_counts(tmp_path):
    run_dir = _copy_valid(tmp_path)
    _rewrite_json(
        run_dir / "archimedes-independent-evidence-report.json",
        lambda report: report.update(expected_outputs=True, produced_outputs=True),
    )

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert "independent_report_output_count_invalid" in result["errors"]


def test_accepted_report_cannot_retain_missing_evidence_or_blockers(tmp_path):
    run_dir = _copy_valid(tmp_path)

    def add_unresolved_items(report):
        report["missing_empty_stale_unlinked_evidence"] = ["missing.json"]
        report["blockers"] = ["unresolved blocker"]

    _rewrite_json(
        run_dir / "archimedes-independent-evidence-report.json",
        add_unresolved_items,
    )

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert "accepted_with_missing_or_defective_evidence" in result["errors"]
    assert "accepted_with_blockers" in result["errors"]


def test_duplicate_manifest_entry_fails_closed(tmp_path):
    run_dir = _copy_valid(tmp_path)

    def duplicate_first_artifact(manifest):
        manifest["artifacts"].append(dict(manifest["artifacts"][0]))

    _rewrite_json(run_dir / "evidence-manifest.json", duplicate_first_artifact)

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert "duplicate_manifest_artifact:native-events.jsonl" in result["errors"]


def test_ledger_entry_class_and_evidence_reference_are_validated(tmp_path):
    run_dir = _copy_valid(tmp_path)
    ledger_path = run_dir / "run-ledger.jsonl"
    entries = [json.loads(line) for line in ledger_path.read_text().splitlines()]
    entries[0]["entry_type"] = "forged_entry_class"
    entries[0]["evidence_ref"] = "missing-ledger-evidence.json"
    ledger_path.write_text(
        "\n".join(json.dumps(entry, separators=(",", ":")) for entry in entries) + "\n",
        encoding="utf-8",
    )

    result = _load_validator().validate_study(run_dir)

    assert result["valid"] is False
    assert "run_ledger_entry_type_invalid:1" in result["errors"]
    assert "run_ledger_evidence_ref_unresolved:1" in result["errors"]
