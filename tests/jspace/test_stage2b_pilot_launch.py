"""Tests for the exclusive, byte-verified Stage 2b pilot launch package."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "EvoScientist/skills/jspace-research-operations/scripts"
sys.path.insert(0, str(SCRIPTS))


def _load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


launcher = _load("prepare_stage2b_pilot_launch")
bundle_builder = _load("build_stage2b_pilot_bundle")

NOTEBOOK = ROOT / "j-space-lab/jspace_colab_stage2b_discrimination.ipynb"
PILOT_VIEW = ROOT / "j-space-lab/jspace-stage2b-pilot-v1.json"


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _authorization_record(notebook_sha256, bundle_sha256):
    instruction = "Authorize the bounded Stage 2b pilot test fixture."
    return {
        "schema": "jspace-stage2b-pilot-authorization/v1",
        "run_mode": "pilot",
        "decision": {
            "authority": "Dr. Mani",
            "authorized_at_utc": "2026-07-30T12:00:00Z",
            "instruction": instruction,
            "instruction_sha256": hashlib.sha256(
                (instruction + "\n").encode()
            ).hexdigest(),
        },
        "scope": {
            "pilot_view_sha256": _sha256(PILOT_VIEW),
            "confirmation_access_authorized": False,
            "artifact_transfer_authorized": False,
        },
        "source": {
            "notebook_sha256": notebook_sha256,
            "code_bundle_sha256": bundle_sha256,
        },
        "registry_updates": {
            "PILOT_PROTOCOL_RATIFIED": {
                "declared_value": True,
                "status": "ratified",
            },
            "PILOT_AUTHORIZED": {
                "declared_value": True,
                "status": "ratified",
            },
        },
    }


def _write_record(tmp_path, record):
    payload = (json.dumps(record, sort_keys=True, indent=2) + "\n").encode()
    digest = hashlib.sha256(payload).hexdigest()
    path = tmp_path / f"stage2b-pilot-authorization-{digest}.json"
    path.write_bytes(payload)
    return path, digest


def _sources(tmp_path):
    bundle = tmp_path / "stage2b-pilot-code-bundle.zip"
    bundle_builder.build_bundle(repository_root=ROOT, output_path=bundle)
    record, digest = _write_record(
        tmp_path,
        _authorization_record(_sha256(NOTEBOOK), _sha256(bundle)),
    )
    return bundle, record, digest


def test_launch_package_copies_only_exact_authorized_sources(tmp_path):
    bundle, record, record_digest = _sources(tmp_path)
    output = tmp_path / "exclusive-launch"
    result = launcher.prepare_launch(
        notebook_path=NOTEBOOK,
        code_bundle_path=bundle,
        pilot_view_path=PILOT_VIEW,
        authorization_path=record,
        approved_authorization_sha256=record_digest,
        output_dir=output,
    )
    expected_names = {
        NOTEBOOK.name,
        bundle.name,
        PILOT_VIEW.name,
        record.name,
        "stage2b-pilot-launch-manifest.json",
    }
    assert {path.name for path in output.iterdir()} == expected_names
    assert (output / NOTEBOOK.name).read_bytes() == NOTEBOOK.read_bytes()
    assert (output / bundle.name).read_bytes() == bundle.read_bytes()
    assert (output / PILOT_VIEW.name).read_bytes() == PILOT_VIEW.read_bytes()
    manifest = json.loads((output / "stage2b-pilot-launch-manifest.json").read_text())
    assert manifest["source"] == result["source"]
    assert manifest["boundaries"] == {
        "run_mode": "pilot",
        "confirmation_access_authorized": False,
        "artifact_transfer_authorized": False,
    }


def test_launch_package_rejects_authorized_notebook_claim_not_matching_bytes(tmp_path):
    bundle = tmp_path / "stage2b-pilot-code-bundle.zip"
    bundle_builder.build_bundle(repository_root=ROOT, output_path=bundle)
    record, digest = _write_record(
        tmp_path,
        _authorization_record("f" * 64, _sha256(bundle)),
    )
    with pytest.raises(ValueError, match="notebook identity"):
        launcher.prepare_launch(
            notebook_path=NOTEBOOK,
            code_bundle_path=bundle,
            pilot_view_path=PILOT_VIEW,
            authorization_path=record,
            approved_authorization_sha256=digest,
            output_dir=tmp_path / "launch",
        )


def test_launch_package_refuses_a_preexisting_directory(tmp_path):
    bundle, record, record_digest = _sources(tmp_path)
    output = tmp_path / "exclusive-launch"
    output.mkdir()
    marker = output / "stale.py"
    marker.write_text("stale")
    with pytest.raises(FileExistsError, match="already exists"):
        launcher.prepare_launch(
            notebook_path=NOTEBOOK,
            code_bundle_path=bundle,
            pilot_view_path=PILOT_VIEW,
            authorization_path=record,
            approved_authorization_sha256=record_digest,
            output_dir=output,
        )
    assert marker.read_text() == "stale"
