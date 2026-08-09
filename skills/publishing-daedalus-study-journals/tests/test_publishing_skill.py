import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "skills" / "publishing-daedalus-study-journals"
ACCEPTING = ROOT / "skills" / "accepting-daedalus-mock-study-evidence"
VALID = ACCEPTING / "tests" / "fixtures" / "valid-study"
VALIDATOR = ACCEPTING / "scripts" / "validate_mock_study.py"
ARTICLE_TEMPLATE = BASE / "templates" / "public-journal-article.json"


def _load_validator():
    spec = importlib.util.spec_from_file_location("validate_mock_study", VALIDATOR)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _copy_with_article(tmp_path: Path) -> Path:
    run_dir = tmp_path / "run"
    shutil.copytree(VALID, run_dir)
    shutil.copy2(ARTICLE_TEMPLATE, run_dir / "public-journal-article.json")
    return run_dir


def _rewrite_article(run_dir: Path, mutate) -> None:
    path = run_dir / "public-journal-article.json"
    article = json.loads(path.read_text(encoding="utf-8"))
    mutate(article)
    path.write_text(json.dumps(article, indent=2) + "\n", encoding="utf-8")


def test_publication_skill_requires_distinct_human_gate():
    skill = (BASE / "SKILL.md").read_text(encoding="utf-8")
    gate = (BASE / "references" / "publication-gate.md").read_text(encoding="utf-8")

    assert skill.startswith("---\nname: publishing-daedalus-study-journals\n")
    assert "explicit approval from Dr. Mani" in skill
    assert "does not publish" in skill
    for state in (
        "publication_prepared",
        "awaiting_dr_mani_approval",
        "published",
        "publication_declined",
        "publication_blocked",
    ):
        assert state in gate


def test_article_template_contains_required_sections_and_claim_classes():
    article = json.loads(ARTICLE_TEMPLATE.read_text(encoding="utf-8"))
    approval = json.loads(
        (BASE / "templates" / "publication-approval.json").read_text(encoding="utf-8")
    )

    assert article["schema"] == "daedalus-public-journal-article/v1"
    for key in (
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
    ):
        assert key in article["sections"]
    assert {claim["claim_class"] for claim in article["claims"]} == {
        "verified_execution",
        "observed_result",
        "supported_inference",
        "hypothesis",
        "unknown",
    }
    assert article["publication_state"] == "publication_prepared"
    assert article["publication_authorized"] is False
    assert approval["decision"] == "not_approved"
    assert approval["article_sha256"] is None


def test_prepared_valid_article_passes_without_publishing(tmp_path):
    run_dir = _copy_with_article(tmp_path)

    result = _load_validator().validate_publication(run_dir, allow_legacy_fixture=True)

    assert result == {
        "valid": True,
        "publication_state": "publication_prepared",
        "errors": [],
    }


def test_article_preparation_requires_the_complete_independent_evidence_package(
    tmp_path,
):
    run_dir = _copy_with_article(tmp_path)
    (run_dir / "native-events.jsonl").unlink()

    result = _load_validator().validate_publication(run_dir, allow_legacy_fixture=True)

    assert result["valid"] is False
    assert "study_evidence_invalid_for_publication" in result["errors"]


def test_article_privacy_leak_fails_closed(tmp_path):
    run_dir = _copy_with_article(tmp_path)
    _rewrite_article(
        run_dir,
        lambda article: article["public_content"].update(
            credentials="synthetic-secret"
        ),
    )

    result = _load_validator().validate_publication(run_dir, allow_legacy_fixture=True)

    assert "privacy_leak:credentials" in result["errors"]


@pytest.mark.parametrize("actual_outcome", ["partial", "failed", "stopped"])
def test_article_cannot_overstate_partial_failed_or_stopped_outcome(
    tmp_path, actual_outcome
):
    run_dir = _copy_with_article(tmp_path)
    report_path = run_dir / "archimedes-independent-evidence-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["verdict"] = actual_outcome
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    result = _load_validator().validate_publication(run_dir, allow_legacy_fixture=True)

    assert f"article_outcome_mismatch:accepted!={actual_outcome}" in result["errors"]


@pytest.mark.parametrize("actual_outcome", ["partial", "failed", "stopped"])
def test_matching_terminal_outcome_can_prepare_an_accurate_article(
    tmp_path, actual_outcome
):
    run_dir = _copy_with_article(tmp_path)
    report_path = run_dir / "archimedes-independent-evidence-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["verdict"] = actual_outcome
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    def disclose_outcome(article):
        article["study_outcome"] = actual_outcome
        article["sections"]["what_worked_and_did_not_work"] = (
            f"The actual study outcome was {actual_outcome}; no success upgrade is claimed."
        )

    _rewrite_article(run_dir, disclose_outcome)

    result = _load_validator().validate_publication(run_dir, allow_legacy_fixture=True)

    assert result["valid"] is True


def test_article_must_match_frozen_publication_metadata(tmp_path):
    run_dir = _copy_with_article(tmp_path)
    _rewrite_article(run_dir, lambda article: article.update(destination="other-site"))

    result = _load_validator().validate_publication(run_dir, allow_legacy_fixture=True)

    assert "frozen_publication_mismatch:destination" in result["errors"]


def test_publication_without_approval_fails_closed(tmp_path):
    run_dir = _copy_with_article(tmp_path)
    _rewrite_article(
        run_dir, lambda article: article.update(publication_state="published")
    )

    result = _load_validator().validate_publication(run_dir, allow_legacy_fixture=True)

    assert "publication_without_dr_mani_approval" in result["errors"]


def test_article_cannot_self_assert_dr_mani_approval(tmp_path):
    run_dir = _copy_with_article(tmp_path)
    _rewrite_article(
        run_dir,
        lambda article: article.update(
            publication_state="published",
            publication_authorized=True,
            dr_mani_approval_evidence="self-asserted",
        ),
    )

    result = _load_validator().validate_publication(run_dir, allow_legacy_fixture=True)

    assert result["valid"] is False
    assert result["publication_state"] == "publication_blocked"
    assert "publication_without_verified_dr_mani_approval" in result["errors"]


def test_local_hash_bound_approval_record_does_not_bypass_human_gate(tmp_path):
    run_dir = _copy_with_article(tmp_path)
    _rewrite_article(
        run_dir,
        lambda article: article.update(
            publication_state="published",
            publication_authorized=True,
            dr_mani_approval_evidence="publication-approval.json",
        ),
    )
    article_path = run_dir / "public-journal-article.json"
    approval = {
        "schema": "daedalus-publication-approval/v1",
        "packet_id": "synthetic-vertical-acceptance-001",
        "approver": "Dr. Mani",
        "decision": "approved",
        "article_sha256": hashlib.sha256(article_path.read_bytes()).hexdigest(),
        "approved_at": "2026-08-07T00:30:00Z",
    }
    (run_dir / "publication-approval.json").write_text(
        json.dumps(approval, indent=2) + "\n", encoding="utf-8"
    )

    result = _load_validator().validate_publication(run_dir, allow_legacy_fixture=True)

    assert result["valid"] is False
    assert result["publication_state"] == "publication_blocked"
    assert "publication_requires_external_human_gate" in result["errors"]


def test_material_claim_requires_evidence_reference_or_hash(tmp_path):
    run_dir = _copy_with_article(tmp_path)

    def remove_links(article):
        article["claims"][0]["evidence_ref"] = None
        article["claims"][0]["content_sha256"] = None

    _rewrite_article(run_dir, remove_links)

    result = _load_validator().validate_publication(run_dir, allow_legacy_fixture=True)

    assert "claim_lacks_evidence:claim-001" in result["errors"]


def test_nonhex_claim_hash_is_not_evidence(tmp_path):
    run_dir = _copy_with_article(tmp_path)

    def replace_link_with_nonhex_hash(article):
        article["claims"][0]["evidence_ref"] = None
        article["claims"][0]["content_sha256"] = "z" * 64

    _rewrite_article(run_dir, replace_link_with_nonhex_hash)

    result = _load_validator().validate_publication(run_dir, allow_legacy_fixture=True)

    assert "claim_hash_invalid:claim-001" in result["errors"]


def test_secret_marker_in_article_text_fails_closed(tmp_path):
    run_dir = _copy_with_article(tmp_path)

    def leak_secret(article):
        article["sections"]["limitations"] += " API_KEY=synthetic-secret"

    _rewrite_article(run_dir, leak_secret)

    result = _load_validator().validate_publication(run_dir, allow_legacy_fixture=True)

    assert "privacy_leak:secret_marker" in result["errors"]


def test_claim_evidence_reference_must_resolve_when_no_hash_is_available(tmp_path):
    run_dir = _copy_with_article(tmp_path)

    def break_reference(article):
        article["claims"][2]["evidence_ref"] = "missing-evidence.json#verdict"
        article["claims"][2]["content_sha256"] = None

    _rewrite_article(run_dir, break_reference)

    result = _load_validator().validate_publication(run_dir, allow_legacy_fixture=True)

    assert "claim_evidence_missing:claim-003" in result["errors"]


def test_forbidden_public_content_class_fails_closed(tmp_path):
    run_dir = _copy_with_article(tmp_path)
    _rewrite_article(
        run_dir,
        lambda article: article["included_content_classes"].append("hidden_prompts"),
    )

    result = _load_validator().validate_publication(run_dir, allow_legacy_fixture=True)

    assert "forbidden_public_content_class:hidden_prompts" in result["errors"]


def test_invalid_article_never_returns_published_state(tmp_path):
    run_dir = _copy_with_article(tmp_path)
    _rewrite_article(
        run_dir,
        lambda article: article.update(
            publication_state="published",
            publication_authorized=False,
            dr_mani_approval_evidence=None,
        ),
    )

    result = _load_validator().validate_publication(run_dir, allow_legacy_fixture=True)

    assert result["valid"] is False
    assert result["publication_state"] == "publication_blocked"


def test_malformed_publication_types_fail_without_crashing(tmp_path):
    run_dir = _copy_with_article(tmp_path)

    def corrupt_types(article):
        article["included_content_classes"] = [{}]
        article["claims"][0]["claim_class"] = []
        article["publication_state"] = []

    _rewrite_article(run_dir, corrupt_types)

    result = _load_validator().validate_publication(run_dir, allow_legacy_fixture=True)

    assert result["valid"] is False
    assert result["publication_state"] == "publication_blocked"
