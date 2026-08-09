from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "conducting-daedalus-mock-studies" / "SKILL.md"
STATE = SKILL.parent / "references" / "state-contract.md"


def test_conducting_skill_encodes_complete_evidence_backed_state_contract():
    skill = SKILL.read_text(encoding="utf-8")
    state = STATE.read_text(encoding="utf-8")

    assert skill.startswith("---\nname: conducting-daedalus-mock-studies\n")
    assert "four stage skills" in skill
    for stage_skill in (
        "preparing-daedalus-mock-studies",
        "supervising-daedalus-mock-study-runs",
        "accepting-daedalus-mock-study-evidence",
        "publishing-daedalus-study-journals",
    ):
        assert stage_skill in skill
    for transition in (
        "intake -> prepared",
        "prepared -> launched",
        "launched -> monitoring",
        "monitoring -> evidence_ready",
        "evidence_ready -> accepted | partial | failed | stopped",
        "accepted | partial | failed | stopped -> publication_prepared",
        "publication_prepared -> awaiting_dr_mani_approval",
        "awaiting_dr_mani_approval -> published | publication_declined | publication_blocked",
    ):
        assert transition in state
    assert "No transition occurs from narration alone" in state
    assert "does not prove that every Daedalus function works" in skill
