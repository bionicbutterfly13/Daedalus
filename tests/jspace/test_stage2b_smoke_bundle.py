"""Tests for deterministic Stage 2b integration-smoke source packaging."""

from __future__ import annotations

import importlib.util
import json
import pathlib
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "EvoScientist/skills/jspace-research-operations/scripts"
SPEC = importlib.util.spec_from_file_location(
    "build_stage2b_smoke_bundle", SCRIPTS / "build_stage2b_smoke_bundle.py"
)
assert SPEC is not None
assert SPEC.loader is not None
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def test_bundle_is_deterministic_and_code_only(tmp_path):
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"
    first_result = builder.build_bundle(scripts_dir=SCRIPTS, output_path=first)
    second_result = builder.build_bundle(scripts_dir=SCRIPTS, output_path=second)
    assert first.read_bytes() == second.read_bytes()
    assert first_result["sha256"] == second_result["sha256"]

    with zipfile.ZipFile(first) as archive:
        assert archive.namelist() == [
            *builder.BUNDLE_FILES,
            "bundle-manifest.json",
        ]
        manifest = json.loads(archive.read("bundle-manifest.json"))
        assert manifest["schema"] == builder.BUNDLE_SCHEMA
        assert [entry["name"] for entry in manifest["files"]] == list(
            builder.BUNDLE_FILES
        )
        names = "\n".join(archive.namelist()).lower()
        assert "pilot" not in names
        assert "confirm" not in names
        assert "credential" not in names


def test_existing_different_bundle_is_not_overwritten(tmp_path):
    output = tmp_path / "bundle.zip"
    output.write_bytes(b"different")
    try:
        builder.build_bundle(scripts_dir=SCRIPTS, output_path=output)
    except FileExistsError:
        pass
    else:
        raise AssertionError("builder overwrote a bundle from another source state")
    assert output.read_bytes() == b"different"
