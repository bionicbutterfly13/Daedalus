"""Tests for deterministic Stage 2b pilot code-only packaging."""

from __future__ import annotations

import importlib.util
import json
import pathlib
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "EvoScientist/skills/jspace-research-operations/scripts"
SPEC = importlib.util.spec_from_file_location(
    "build_stage2b_pilot_bundle",
    SCRIPTS / "build_stage2b_pilot_bundle.py",
)
assert SPEC is not None
assert SPEC.loader is not None
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def test_pilot_bundle_is_deterministic_and_allowlisted(tmp_path):
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"
    first_result = builder.build_bundle(repository_root=ROOT, output_path=first)
    second_result = builder.build_bundle(repository_root=ROOT, output_path=second)
    assert first.read_bytes() == second.read_bytes()
    assert first_result["sha256"] == second_result["sha256"]

    with zipfile.ZipFile(first) as archive:
        expected = [
            *[
                (f"EvoScientist/skills/jspace-research-operations/scripts/{name}")
                for name in builder.SCRIPT_NAMES
            ],
            builder.STAGE2_DIGESTS_PATH,
            "bundle-manifest.json",
        ]
        assert archive.namelist() == expected
        manifest = json.loads(archive.read("bundle-manifest.json"))
        assert manifest["schema"] == builder.BUNDLE_SCHEMA
        assert [entry["name"] for entry in manifest["files"]] == expected[:-1]
        lowered = "\n".join(archive.namelist()).lower()
        for forbidden in (
            ".ipynb",
            "jspace-stage2b-pilot-v1.json",
            "jspace-stage2b-stimulus-v1.json",
            "credential",
            "token",
            "secret",
        ):
            assert forbidden not in lowered


def test_pilot_bundle_refuses_to_overwrite_different_bytes(tmp_path):
    output = tmp_path / "bundle.zip"
    output.write_bytes(b"different")
    try:
        builder.build_bundle(repository_root=ROOT, output_path=output)
    except FileExistsError:
        pass
    else:
        raise AssertionError("builder overwrote a bundle from another source state")
    assert output.read_bytes() == b"different"
