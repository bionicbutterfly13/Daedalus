"""Static source-contract tests for the excluded-input Colab smoke notebook."""

from __future__ import annotations

import ast
import hashlib
import json
import pathlib
from types import SimpleNamespace

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
NOTEBOOK = ROOT / "j-space-lab/jspace_colab_stage2b_integration_smoke.ipynb"
BUNDLE = (
    ROOT
    / "runs/stage2b-integration-smoke-torchvision-repair-v2-20260730"
    / "stage2b_integration_smoke_bundle.zip"
)


@pytest.fixture(scope="module")
def notebook():
    return json.loads(NOTEBOOK.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def source(notebook):
    return "\n".join(
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    )


def test_notebook_is_canonical_unexecuted_nbformat(notebook):
    assert notebook["nbformat"] == 4
    code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    assert len(code_cells) == 8
    assert all(cell["execution_count"] is None for cell in code_cells)
    assert all(cell["outputs"] == [] for cell in code_cells)


def test_every_ordinary_code_cell_parses(notebook):
    failures = []
    for index, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] != "code":
            continue
        code = "".join(cell["source"])
        if code.lstrip().startswith(("%", "!")):
            continue
        try:
            ast.parse(code)
        except SyntaxError as exc:
            failures.append((index, exc.msg, exc.lineno))
    assert failures == []


def test_notebook_and_code_bundle_are_hash_bound(source):
    assert BUNDLE.is_file()
    digest = hashlib.sha256(BUNDLE.read_bytes()).hexdigest()
    assert digest == "4f18c96303d1451941ca050e3159e12b31b5d8d8dba4d8981a1a03e118f4cbfb"
    assert f'EXPECTED_BUNDLE_SHA256 = "{digest}"' in source
    assert "bundle-manifest.json" in source


def test_canonical_source_fails_closed_before_downloads(source):
    assert "INTEGRATION_SMOKE_AUTHORIZED = False" in source
    assert "ARTIFACT_TRANSFER_AUTHORIZED = False" in source
    assert "if INTEGRATION_SMOKE_AUTHORIZED is not True:" in source
    assert "if ARTIFACT_TRANSFER_AUTHORIZED is not True:" in source
    assert source.index("if INTEGRATION_SMOKE_AUTHORIZED is not True:") < source.index(
        "subprocess.run(runtime_install_command, check=True)"
    )
    assert source.index("nvidia-smi") < source.index(
        "subprocess.run(runtime_install_command, check=True)"
    )


def test_binary_package_install_requires_a_fresh_runtime_process(source):
    required = (
        'RUNTIME_INSTALL_SCHEMA = "stage2b-colab-runtime-install/v2"',
        'RUNTIME_INSTALL_SENTINEL = pathlib.Path("/content/'
        'stage2b_integration_smoke_runtime_install.json")',
        'RUNTIME_REMOVE_PACKAGES = ("torchvision",)',
        '"remove_packages": list(RUNTIME_REMOVE_PACKAGES)',
        "pathlib.Path('/proc/self/stat').read_text(encoding='utf-8').split()[21]",
        '"install_process_identity": PROCESS_IDENTITY',
        "subprocess.run(runtime_remove_command, check=True)",
        "subprocess.run(runtime_install_command, check=True)",
        'raise RuntimeError("runtime restart required before package imports")',
        'raise RuntimeError("torchvision must be absent from the text-only runtime")',
        '"fresh_process_after_install": fresh_process_after_install',
    )
    for marker in required:
        assert marker in source
    assert source.index(
        "runtime restart required before package imports"
    ) < source.index("import numpy as np")
    assert source.index(
        "torchvision must be absent from the text-only runtime"
    ) < source.index("import transformers")


def test_install_sentinel_binds_the_process_and_skips_repeat_install(
    notebook, tmp_path
):
    install_source = next(
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
        and "runtime_install_command = [" in "".join(cell["source"])
    )
    sentinel = tmp_path / "runtime-install.json"
    calls = []
    namespace = {
        "EXPECTED_RUNTIME_VERSIONS": {"numpy": "fixture"},
        "INTEGRATION_SMOKE_AUTHORIZED": True,
        "JLENS_COMMIT": "fixture-commit",
        "JLENS_REPO_URL": "https://example.invalid/lens.git",
        "PROCESS_IDENTITY": "101:1001",
        "RUNTIME_REMOVE_PACKAGES": ("torchvision",),
        "RUNTIME_INSTALL_REQUIREMENTS": ("numpy==fixture",),
        "RUNTIME_INSTALL_SCHEMA": "stage2b-colab-runtime-install/v2",
        "RUNTIME_INSTALL_SENTINEL": sentinel,
        "install_spec_sha256": "a" * 64,
        "json": json,
        "subprocess": SimpleNamespace(
            run=lambda command, check: calls.append((command, check))
        ),
    }
    exec(install_source, namespace)
    assert len(calls) == 2
    assert calls[0][0][-3:] == ["uninstall", "-y", "torchvision"]
    assert calls[1][0][-1] == "numpy==fixture"
    assert namespace["fresh_process_after_install"] is False
    assert json.loads(sentinel.read_text(encoding="utf-8")) == {
        "schema": "stage2b-colab-runtime-install/v2",
        "install_spec_sha256": "a" * 64,
        "install_process_identity": "101:1001",
    }

    exec(install_source, namespace)
    assert len(calls) == 2
    assert namespace["fresh_process_after_install"] is False

    namespace["PROCESS_IDENTITY"] = "202:2002"
    exec(install_source, namespace)
    assert len(calls) == 2
    assert namespace["fresh_process_after_install"] is True


def test_post_install_gate_rejects_the_installing_process(notebook, tmp_path):
    verification_source = next(
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
        and "runtime restart required before package imports" in "".join(cell["source"])
    )
    gate_source = verification_source.split("import importlib.metadata", 1)[0]
    sentinel = tmp_path / "runtime-install.json"
    sentinel.write_text(
        json.dumps(
            {
                "schema": "stage2b-colab-runtime-install/v2",
                "install_spec_sha256": "a" * 64,
                "install_process_identity": "101:1001",
            }
        ),
        encoding="utf-8",
    )
    namespace = {
        "PROCESS_IDENTITY": "101:1001",
        "RUNTIME_INSTALL_SENTINEL": sentinel,
        "install_spec_sha256": "a" * 64,
        "json": json,
    }
    with pytest.raises(RuntimeError, match="runtime restart required"):
        exec(gate_source, namespace)

    namespace["PROCESS_IDENTITY"] = "202:2002"
    exec(gate_source, namespace)
    assert namespace["fresh_process_after_install"] is True


def test_notebook_cannot_open_scientific_inputs_or_emit_scientific_fields(source):
    forbidden = (
        "jspace-stage2b-pilot-v1.json",
        "jspace-stage2b-stimulus-v1.json",
        "stage2_manifest_digests.json",
        "PILOT_AUTHORIZED",
        "PILOT_PROTOCOL_RATIFIED",
        "THRESHOLDS_RATIFIED",
        "NTA_MIN_DENOMINATOR",
        '"gates":',
        '"decision":',
        '"thresholds":',
        '"pilot_results":',
    )
    for marker in forbidden:
        assert marker not in source


def test_notebook_exercises_pinned_full_crossing_and_runtime_evidence(source):
    required = (
        'MODEL_ID = "Qwen/Qwen3-1.7B"',
        'MODEL_REVISION = "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"',
        'JLENS_COMMIT = "581d398613e5602a5af361e1c34d3a92ea82ba8e"',
        "smoke.smoke_prompts()",
        "smoke.select_smoke_donors(",
        "ep.build_fit_broken_map(",
        "ep.materialize_crossed_factorials(",
        'crossing["unique_readout_count"] != 81',
        'crossing["logical_cell_count"] != 64',
        "smoke.array_sha256(",
        "torch.cuda.max_memory_allocated()",
        "torch.cuda.max_memory_reserved()",
        "smoke.project_pilot_readout_seconds(",
        "smoke.validate_runtime_report(report)",
        "runtime_compatibility_only",
        '"source_bundle": {',
        '"sha256": EXPECTED_BUNDLE_SHA256',
        '"install_spec_sha256": install_spec_sha256',
        '"fresh_process_after_install": fresh_process_after_install',
    )
    for marker in required:
        assert marker in source


def test_report_is_retained_until_separate_transfer_authorization(source):
    assert (
        'report_dir = pathlib.Path("/content/jspace_stage2b_integration_smoke")'
        in source
    )
    assert "files.download(str(report_path))" in source
    assert source.index("if ARTIFACT_TRANSFER_AUTHORIZED is not True:") < source.index(
        "files.download(str(report_path))"
    )
    assert 'with report_path.open("xb") as handle:' in source
