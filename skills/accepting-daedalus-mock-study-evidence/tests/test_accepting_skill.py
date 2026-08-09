import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "skills" / "accepting-daedalus-mock-study-evidence"


def test_acceptance_skill_keeps_authorship_and_verdict_boundaries():
    skill = (BASE / "SKILL.md").read_text(encoding="utf-8")

    assert skill.startswith("---\nname: accepting-daedalus-mock-study-evidence\n")
    assert "Daedalus primary study report" in skill
    assert "Archimedes independent evidence report" in skill
    assert "must not manufacture" in skill
    assert "must not convert" in skill


def test_evidence_and_report_templates_are_distinct_and_complete():
    manifest = json.loads(
        (BASE / "templates" / "evidence-manifest.json").read_text(encoding="utf-8")
    )
    report = json.loads(
        (BASE / "templates" / "archimedes-independent-evidence-report.json").read_text(
            encoding="utf-8"
        )
    )

    assert manifest["schema"] == "daedalus-mock-study-evidence-manifest/v1"
    assert manifest["layout"] == "supervised_attempt/v1"
    assert {item["role"] for item in manifest["artifacts"]} >= {
        "native_event_stream",
        "terminal_status",
        "primary_study_report",
    }
    assert report["schema"] == "archimedes-independent-evidence-report/v1"
    for key in (
        "actually_executed",
        "workflow_stage_evidence",
        "directly_verified_artifacts",
        "expected_outputs",
        "produced_outputs",
        "checksums_and_provenance",
        "missing_empty_stale_unlinked_evidence",
        "failures_retries_timing_stop_conditions",
        "concerns_about_daedalus",
        "verdict",
        "verdict_reason",
    ):
        assert key in report
    assert report["verdict"] in {"accepted", "partial", "failed", "stopped"}
