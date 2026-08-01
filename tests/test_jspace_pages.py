"""Source-level tests for the public J-space Pages builder."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "docs" / "site" / "build.py"


def _load_builder():
    spec = importlib.util.spec_from_file_location("jspace_pages_build", BUILDER)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_metadata_and_sidebar_cover_every_public_wiki_page() -> None:
    build = _load_builder()
    metadata = build.load_metadata()
    filenames = {path.name for path in build.wiki_pages()}
    assert set(metadata) == filenames

    navigation = build.sidebar_navigation(metadata, "/EvoScientist")
    assert {entry["filename"] for entry in navigation} == filenames
    assert len(navigation) == len(filenames) == 13


def test_wiki_links_rewrite_to_pages_paths() -> None:
    build = _load_builder()
    metadata = build.load_metadata()
    source = "See [[Stage 2b Pilot Result]] and [[Label|Primary-Floor-Decision]]."
    rewritten = build.rewrite_wiki_links(source, metadata, "/EvoScientist")
    assert "[[" not in rewritten
    assert "](/EvoScientist/Stage-2b-Pilot-Result/)" in rewritten
    assert "[Label](/EvoScientist/Primary-Floor-Decision/)" in rewritten


def test_page_paths_are_stable_and_project_relative() -> None:
    build = _load_builder()
    assert build.page_path("/EvoScientist", "Home.md") == "/EvoScientist/"
    assert (
        build.page_path("/EvoScientist", "Why-IWMT-Matters.md")
        == "/EvoScientist/Why-IWMT-Matters/"
    )


def test_builder_refuses_a_nonempty_output_directory(tmp_path) -> None:
    build = _load_builder()
    output = tmp_path / "site"
    output.mkdir()
    sentinel = output / "preserve.txt"
    sentinel.write_text("do not delete")

    try:
        build.build_site(
            output,
            site_url=build.DEFAULT_SITE_URL,
            base_path=build.DEFAULT_BASE_PATH,
        )
    except FileExistsError:
        pass
    else:
        raise AssertionError("nonempty output directory was accepted")

    assert sentinel.read_text() == "do not delete"
