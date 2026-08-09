import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "skills" / "preparing-daedalus-mock-studies"


def _load(name: str) -> dict:
    return json.loads((BASE / "templates" / name).read_text(encoding="utf-8"))


def test_study_packet_freezes_complete_synthetic_and_publication_boundary():
    packet = _load("study-packet.json")

    assert packet["schema"] == "daedalus-mock-study-packet/v1"
    assert packet["synthetic_study"] is True
    for key in (
        "packet_id",
        "objective",
        "research_question",
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
    ):
        assert key in packet
    journal = packet["public_journal"]
    for key in (
        "destination",
        "title",
        "authorship",
        "public_artifacts",
        "private_artifacts",
        "redaction_privacy_rules",
        "evidence_linking_requirements",
        "approval_status",
        "rollback_correction_procedure",
    ):
        assert key in journal
    assert journal["approval_status"] == "not_approved"
    assert packet["provider_cost_boundary"]["paid_providers_authorized"] is False
    assert packet["retention_transfer_publication"]["publication_authorized"] is False


def test_authorization_record_fails_closed_for_unapproved_actions():
    authorization = _load("authorization-record.json")

    assert authorization["schema"] == "daedalus-mock-study-authorization/v1"
    assert authorization["study_execution_authorized"] is False
    assert authorization["paid_provider_activation_authorized"] is False
    assert authorization["private_memory_access_authorized"] is False
    assert authorization["artifact_transfer_authorized"] is False
    assert authorization["publication_authorized"] is False
    assert authorization["approval_evidence"] is None


def test_preparation_skill_forbids_substitution_and_requires_immutability():
    skill = (BASE / "SKILL.md").read_text(encoding="utf-8")

    assert skill.startswith("---\nname: preparing-daedalus-mock-studies\n")
    assert "must not substitute" in skill
    assert "immutable" in skill
