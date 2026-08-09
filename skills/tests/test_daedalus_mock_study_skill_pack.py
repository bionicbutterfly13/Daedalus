import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NAMES = (
    "conducting-daedalus-mock-studies",
    "preparing-daedalus-mock-studies",
    "supervising-daedalus-mock-study-runs",
    "accepting-daedalus-mock-study-evidence",
    "publishing-daedalus-study-journals",
)


def test_one_canonical_skill_package_exists():
    readme = (ROOT / "skills" / "README.md").read_text(encoding="utf-8")

    for name in NAMES:
        canonical = ROOT / "skills" / name
        assert (canonical / "SKILL.md").is_file()
        assert name in readme
    assert "only canonical source" in readme


def test_codex_and_hermes_discovery_links_resolve_to_canonical_packages():
    for name in NAMES:
        link = ROOT / ".agents" / "skills" / name
        canonical = ROOT / "skills" / name
        assert link.is_symlink()
        assert link.resolve() == canonical.resolve()


def test_claude_local_discovery_links_resolve_without_duplicate_copies():
    for name in NAMES:
        link = ROOT / ".claude" / "skills" / name
        canonical = ROOT / "skills" / name
        assert link.is_symlink()
        assert link.resolve() == canonical.resolve()


def test_project_pytest_configuration_collects_skill_tests():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert "skills" in config["tool"]["pytest"]["ini_options"]["testpaths"]


def test_skill_tdd_baselines_cover_all_five_skills():
    baseline = (
        ROOT
        / "skills"
        / "conducting-daedalus-mock-studies"
        / "references"
        / "tdd-baseline-observations.md"
    ).read_text(encoding="utf-8")

    for heading in (
        "Conducting",
        "Preparing",
        "Supervising",
        "Accepting",
        "Publishing",
    ):
        assert f"## {heading}" in baseline
    assert baseline.count("Baseline gap:") == 5
    assert baseline.count("Post-skill check:") == 5
