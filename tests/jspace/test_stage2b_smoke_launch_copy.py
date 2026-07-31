"""Tests for safe creation of an authorized disposable Colab notebook copy."""

from __future__ import annotations

import importlib.util
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "EvoScientist/skills/jspace-research-operations/scripts"
CANONICAL = ROOT / "j-space-lab/jspace_colab_stage2b_integration_smoke.ipynb"
SPEC = importlib.util.spec_from_file_location(
    "authorize_stage2b_integration_smoke_notebook",
    SCRIPTS / "authorize_stage2b_integration_smoke_notebook.py",
)
assert SPEC is not None
assert SPEC.loader is not None
authorizer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(authorizer)


def _code_source(notebook):
    return "\n".join(
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    )


def test_authorized_copy_changes_only_smoke_gate_and_metadata(tmp_path):
    output = tmp_path / "authorized.ipynb"
    result = authorizer.create_authorized_copy(
        canonical_path=CANONICAL,
        output_path=output,
        authorization_record_sha256="a" * 64,
    )
    canonical = json.loads(CANONICAL.read_text(encoding="utf-8"))
    authorized = json.loads(output.read_text(encoding="utf-8"))
    assert result["canonical_notebook_sha256"] == authorizer.CANONICAL_NOTEBOOK_SHA256
    assert result["artifact_transfer_authorized"] is False

    canonical_source = _code_source(canonical)
    authorized_source = _code_source(authorized)
    assert authorizer.AUTHORIZATION_FALSE in canonical_source
    assert authorizer.AUTHORIZATION_TRUE not in canonical_source
    assert authorizer.AUTHORIZATION_TRUE in authorized_source
    assert authorizer.AUTHORIZATION_FALSE not in authorized_source
    assert authorizer.TRANSFER_FALSE in authorized_source
    assert authorizer.TRANSFER_TRUE not in authorized_source
    assert authorized_source == canonical_source.replace(
        authorizer.AUTHORIZATION_FALSE, authorizer.AUTHORIZATION_TRUE, 1
    )
    assert authorized["metadata"]["stage2b_integration_smoke_launch"] == {
        "canonical_notebook_sha256": authorizer.CANONICAL_NOTEBOOK_SHA256,
        "authorization_record_sha256": "a" * 64,
        "artifact_transfer_authorized": False,
        "disposable_copy": True,
    }
    assert all(
        cell["execution_count"] is None and cell["outputs"] == []
        for cell in authorized["cells"]
        if cell["cell_type"] == "code"
    )


def test_authorized_copy_is_repeatable_but_not_overwritable(tmp_path):
    output = tmp_path / "authorized.ipynb"
    first = authorizer.create_authorized_copy(
        canonical_path=CANONICAL,
        output_path=output,
        authorization_record_sha256="a" * 64,
    )
    second = authorizer.create_authorized_copy(
        canonical_path=CANONICAL,
        output_path=output,
        authorization_record_sha256="a" * 64,
    )
    assert first == second
    with pytest.raises(FileExistsError, match="another authorization"):
        authorizer.create_authorized_copy(
            canonical_path=CANONICAL,
            output_path=output,
            authorization_record_sha256="b" * 64,
        )


@pytest.mark.parametrize(
    "authorization_digest",
    ["", "A" * 64, "not-a-digest", "a" * 63],
)
def test_authorization_record_digest_is_strict(authorization_digest, tmp_path):
    with pytest.raises(ValueError, match="64 lowercase hex"):
        authorizer.create_authorized_copy(
            canonical_path=CANONICAL,
            output_path=tmp_path / "authorized.ipynb",
            authorization_record_sha256=authorization_digest,
        )


def test_wrong_canonical_hash_is_rejected(tmp_path):
    fake = tmp_path / "canonical.ipynb"
    fake.write_text(CANONICAL.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="canonical notebook SHA-256"):
        authorizer.create_authorized_copy(
            canonical_path=fake,
            output_path=tmp_path / "authorized.ipynb",
            authorization_record_sha256="a" * 64,
        )
