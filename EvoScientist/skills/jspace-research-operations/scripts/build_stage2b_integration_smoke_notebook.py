#!/usr/bin/env python3
"""Generate the canonical fail-closed Stage 2b Colab integration-smoke notebook."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _markdown(source: str) -> dict[str, object]:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source.splitlines(keepends=True),
    }


def _code(source: str) -> dict[str, object]:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


def build_notebook(*, bundle_sha256: str) -> dict[str, object]:
    if len(bundle_sha256) != 64:
        raise ValueError("bundle SHA-256 must be a 64-character digest")
    cells = [
        _markdown(
            """# Stage 2b excluded-input Colab integration smoke

This notebook verifies pinned model/lens API compatibility, the recovered
81-readout/64-cell engineering path, runtime, and VRAM on nine fixed inputs that
are absent from every scientific manifest. It cannot emit scientific gates,
thresholds, decisions, or pilot results. The canonical source ships unauthorized
and must be executed only from a separately authorized disposable copy.
"""
        ),
        _code(
            f'''import hashlib
import json
import os
import pathlib

INTEGRATION_SMOKE_AUTHORIZED = False
ARTIFACT_TRANSFER_AUTHORIZED = False

EXPECTED_BUNDLE_SHA256 = "{bundle_sha256}"
BUNDLE_FILENAME = "stage2b_integration_smoke_bundle.zip"
MODEL_ID = "Qwen/Qwen3-1.7B"
MODEL_REVISION = "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
EXPECTED_MODEL_D_MODEL = 2048
EXPECTED_MODEL_N_LAYERS = 28
LENS_REPO = "neuronpedia/jacobian-lens"
LENS_REVISION = "a4114d7752d11eb546e6cf372213d7e75526d3a1"
LENS_FILE = "qwen3-1.7b/jlens/Salesforce-wikitext/Qwen3-1.7B_jacobian_lens.pt"
EXPECTED_LENS_SHA256 = "6fcc79011bd921ffd87612255e2e99950a124fa519470ee44ebaf161c39be9d6"
JLENS_REPO_URL = "https://github.com/anthropics/jacobian-lens.git"
JLENS_COMMIT = "581d398613e5602a5af361e1c34d3a92ea82ba8e"
EXPECTED_RUNTIME_VERSIONS = {{
    "transformers": "5.5.4",
    "huggingface_hub": "1.24.0",
    "numpy": "2.5.1",
    "scipy": "1.18.0",
    "safetensors": "0.8.0",
    "accelerate": "1.14.0",
    "torch": "2.13.0",
}}
SELECTED_LAYERS = [6, 13, 20, 26]
REPRESENTATIVE_LAYER = 13
POSITIONS = [-2]
MAX_PROMPT_TOKENS = 128
MIN_VRAM_MIB = 14 * 1024
RUNTIME_INSTALL_SCHEMA = "stage2b-colab-runtime-install/v2"
RUNTIME_INSTALL_SENTINEL = pathlib.Path("/content/stage2b_integration_smoke_runtime_install.json")
RUNTIME_REMOVE_PACKAGES = ("torchvision",)
RUNTIME_INSTALL_REQUIREMENTS = (
    f"git+{{JLENS_REPO_URL}}@{{JLENS_COMMIT}}",
    f"transformers=={{EXPECTED_RUNTIME_VERSIONS['transformers']}}",
    f"huggingface_hub=={{EXPECTED_RUNTIME_VERSIONS['huggingface_hub']}}",
    f"safetensors=={{EXPECTED_RUNTIME_VERSIONS['safetensors']}}",
    f"scipy=={{EXPECTED_RUNTIME_VERSIONS['scipy']}}",
    f"numpy=={{EXPECTED_RUNTIME_VERSIONS['numpy']}}",
    f"accelerate=={{EXPECTED_RUNTIME_VERSIONS['accelerate']}}",
    f"torch=={{EXPECTED_RUNTIME_VERSIONS['torch']}}",
)
runtime_install_spec = {{
    "schema": RUNTIME_INSTALL_SCHEMA,
    "remove_packages": list(RUNTIME_REMOVE_PACKAGES),
    "requirements": list(RUNTIME_INSTALL_REQUIREMENTS),
    "expected_runtime_versions": EXPECTED_RUNTIME_VERSIONS,
}}
runtime_install_spec_payload = (
    json.dumps(runtime_install_spec, sort_keys=True, separators=(",", ":")) + "\\n"
).encode("utf-8")
install_spec_sha256 = hashlib.sha256(runtime_install_spec_payload).hexdigest()
PROCESS_IDENTITY = (
    f"{{os.getpid()}}:"
    f"{{pathlib.Path('/proc/self/stat').read_text(encoding='utf-8').split()[21]}}"
)
'''
        ),
        _markdown(
            """## 1. Authorization, code-bundle identity, and accelerator gate

This cell must stop before package, model, or lens downloads unless Dr. Mani has
separately authorized the integration smoke. It verifies only the uploaded
code-only bundle and GPU capacity.
"""
        ),
        _code(
            """import subprocess

if INTEGRATION_SMOKE_AUTHORIZED is not True:
    raise RuntimeError("integration smoke is not authorized")

BUNDLE_PATH = pathlib.Path("/content") / BUNDLE_FILENAME
if not BUNDLE_PATH.is_file():
    raise FileNotFoundError(f"upload the authorized code-only bundle to {BUNDLE_PATH}")
if hashlib.sha256(BUNDLE_PATH.read_bytes()).hexdigest() != EXPECTED_BUNDLE_SHA256:
    raise RuntimeError("uploaded code-only bundle SHA-256 mismatch")

query = subprocess.check_output(
    [
        "nvidia-smi",
        "--query-gpu=name,memory.total",
        "--format=csv,noheader,nounits",
    ],
    text=True,
).strip().splitlines()
if len(query) != 1:
    raise RuntimeError(f"expected one GPU, observed {query!r}")
gpu_name, total_mib_text = [part.strip() for part in query[0].rsplit(",", 1)]
preinstall_vram_mib = int(total_mib_text)
if preinstall_vram_mib < MIN_VRAM_MIB:
    raise RuntimeError(
        f"GPU capacity {preinstall_vram_mib} MiB is below {MIN_VRAM_MIB} MiB"
    )
print(f"authorized accelerator: {gpu_name}, {preinstall_vram_mib} MiB")
"""
        ),
        _markdown(
            """## 2. Install exact pinned runtime dependencies

The pinned binary stack replaces packages preloaded by Colab. After the first
successful install, use **Runtime → Restart session**, reconnect the same runtime,
then rerun cells 1, 3, and 5 before continuing. The sentinel below proves that
the post-install imports occur in a different Python process.
"""
        ),
        _code(
            """import sys

runtime_install_command = [
    sys.executable,
    "-m",
    "pip",
    "install",
    "-q",
    *RUNTIME_INSTALL_REQUIREMENTS,
]
runtime_remove_command = [
    sys.executable,
    "-m",
    "pip",
    "uninstall",
    "-y",
    *RUNTIME_REMOVE_PACKAGES,
]
if RUNTIME_INSTALL_SENTINEL.is_file():
    install_record = json.loads(
        RUNTIME_INSTALL_SENTINEL.read_text(encoding="utf-8")
    )
    if set(install_record) != {
        "schema",
        "install_spec_sha256",
        "install_process_identity",
    }:
        raise RuntimeError("runtime install sentinel has unexpected fields")
    if install_record["schema"] != RUNTIME_INSTALL_SCHEMA:
        raise RuntimeError("runtime install sentinel schema mismatch")
    if install_record["install_spec_sha256"] != install_spec_sha256:
        raise RuntimeError("runtime install specification SHA-256 mismatch")
    fresh_process_after_install = (
        install_record["install_process_identity"] != PROCESS_IDENTITY
    )
    if fresh_process_after_install:
        print("fresh Colab Python process verified after pinned installation")
    else:
        print("pinned installation is complete; restart the Colab session")
else:
    subprocess.run(runtime_remove_command, check=True)
    subprocess.run(runtime_install_command, check=True)
    install_record = {
        "schema": RUNTIME_INSTALL_SCHEMA,
        "install_spec_sha256": install_spec_sha256,
        "install_process_identity": PROCESS_IDENTITY,
    }
    install_record_payload = (
        json.dumps(install_record, sort_keys=True, indent=2) + "\\n"
    ).encode("utf-8")
    with RUNTIME_INSTALL_SENTINEL.open("xb") as handle:
        handle.write(install_record_payload)
    if RUNTIME_INSTALL_SENTINEL.read_bytes() != install_record_payload:
        raise RuntimeError("runtime install sentinel readback mismatch")
    fresh_process_after_install = False
    print("pinned installation complete; use Runtime > Restart session")
"""
        ),
        _markdown(
            """## 3. Verify the source bundle and immutable remote identities

No scientific manifest is opened. The only inputs are embedded in the
hash-verified smoke module.
"""
        ),
        _code(
            """if not RUNTIME_INSTALL_SENTINEL.is_file():
    raise RuntimeError("runtime install sentinel is missing")
install_record = json.loads(RUNTIME_INSTALL_SENTINEL.read_text(encoding="utf-8"))
if install_record.get("install_spec_sha256") != install_spec_sha256:
    raise RuntimeError("runtime install specification SHA-256 mismatch")
fresh_process_after_install = (
    install_record.get("install_process_identity") != PROCESS_IDENTITY
)
if not fresh_process_after_install:
    raise RuntimeError("runtime restart required before package imports")

import importlib.metadata
import importlib.util
import sys
import zipfile

torchvision_distribution = None
try:
    torchvision_distribution = importlib.metadata.version("torchvision")
except importlib.metadata.PackageNotFoundError:
    pass
if (
    torchvision_distribution is not None
    or importlib.util.find_spec("torchvision") is not None
):
    raise RuntimeError("torchvision must be absent from the text-only runtime")
torchvision_state = "absent"

import huggingface_hub
import numpy as np
import torch
import transformers

observed_runtime_versions = {
    name: importlib.metadata.version(name.replace("_", "-"))
    for name in EXPECTED_RUNTIME_VERSIONS
}
if observed_runtime_versions != EXPECTED_RUNTIME_VERSIONS:
    raise RuntimeError(
        f"runtime version mismatch: {observed_runtime_versions!r}"
    )
if not torch.cuda.is_available():
    raise RuntimeError("CUDA is required")
torch_vram_gib = torch.cuda.get_device_properties(0).total_memory / (1024**3)
if torch_vram_gib < MIN_VRAM_MIB / 1024:
    raise RuntimeError("Torch reports insufficient GPU VRAM")

CODE_DIR = pathlib.Path("/content/stage2b_integration_smoke_code")
CODE_DIR.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(BUNDLE_PATH) as archive:
    expected_names = {
        "stage2b_endpoint.py",
        "stage2b_preflight.py",
        "stage2b_integration_smoke.py",
        "bundle-manifest.json",
    }
    if set(archive.namelist()) != expected_names:
        raise RuntimeError("code-only bundle contains unexpected paths")
    manifest = json.loads(archive.read("bundle-manifest.json"))
    for entry in manifest["files"]:
        payload = archive.read(entry["name"])
        if len(payload) != entry["size_bytes"]:
            raise RuntimeError(f"bundle size mismatch for {entry['name']}")
        if hashlib.sha256(payload).hexdigest() != entry["sha256"]:
            raise RuntimeError(f"bundle hash mismatch for {entry['name']}")
        (CODE_DIR / entry["name"]).write_bytes(payload)
sys.path.insert(0, str(CODE_DIR))

import stage2b_endpoint as ep  # noqa: E402
import stage2b_integration_smoke as smoke  # noqa: E402
import stage2b_preflight as pf  # noqa: E402

if tuple(SELECTED_LAYERS) != smoke.SELECTED_LAYERS:
    raise RuntimeError("notebook and smoke module selected layers disagree")
if REPRESENTATIVE_LAYER != smoke.REPRESENTATIVE_LAYER:
    raise RuntimeError("notebook and smoke module representative layer disagree")

distribution = importlib.metadata.distribution("jlens")
installed_commit = pf.installed_vcs_commit(
    distribution.read_text("direct_url.json"),
    expected_repo_url=JLENS_REPO_URL,
)
if installed_commit != JLENS_COMMIT:
    raise RuntimeError("installed Jacobian Lens commit mismatch")

api = huggingface_hub.HfApi()
if api.model_info(MODEL_ID, revision=MODEL_REVISION).sha != MODEL_REVISION:
    raise RuntimeError("resolved model revision mismatch")
if api.model_info(LENS_REPO, revision=LENS_REVISION).sha != LENS_REVISION:
    raise RuntimeError("resolved lens revision mismatch")

prompts = smoke.smoke_prompts()
if len(prompts) != 9 or len({item["sha256"] for item in prompts}) != 9:
    raise RuntimeError("smoke module did not provide nine unique inputs")
print("source bundle, runtime, and immutable identities verified")
"""
        ),
        _markdown(
            """## 4. Load the pinned model and fitted lens; probe all selected layers\n"""
        ),
        _code(
            """import time
import uuid

import jlens
from jlens.hooks import ActivationRecorder
from jlens.vis import _ranks_of

torch.cuda.empty_cache()
torch.cuda.reset_peak_memory_stats()
timings = {}

started = time.perf_counter()
tokenizer = transformers.AutoTokenizer.from_pretrained(
    MODEL_ID, revision=MODEL_REVISION
)
model_hf = transformers.AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    revision=MODEL_REVISION,
    torch_dtype=torch.bfloat16,
    device_map="cuda",
)
timings["model_load"] = time.perf_counter() - started
if model_hf.config.hidden_size != EXPECTED_MODEL_D_MODEL:
    raise RuntimeError("model width mismatch")
if model_hf.config.num_hidden_layers != EXPECTED_MODEL_N_LAYERS:
    raise RuntimeError("model layer count mismatch")

tokenizer.padding_side = "right"
model = jlens.from_hf(model_hf, tokenizer, compile=False)
started = time.perf_counter()
lens_path = huggingface_hub.hf_hub_download(
    repo_id=LENS_REPO, revision=LENS_REVISION, filename=LENS_FILE
)
if hashlib.sha256(pathlib.Path(lens_path).read_bytes()).hexdigest() != EXPECTED_LENS_SHA256:
    raise RuntimeError("fitted-lens SHA-256 mismatch")
lens = jlens.JacobianLens.load(lens_path)
timings["lens_load"] = time.perf_counter() - started

if not set(SELECTED_LAYERS) <= set(lens.source_layers):
    raise RuntimeError("fitted lens does not cover every selected layer")
for layer in SELECTED_LAYERS:
    matrix = lens.jacobians[layer]
    if tuple(matrix.shape) != (EXPECTED_MODEL_D_MODEL, EXPECTED_MODEL_D_MODEL):
        raise RuntimeError(f"Jacobian shape mismatch at layer {layer}")
    if str(matrix.dtype) != "torch.float32":
        raise RuntimeError(f"Jacobian dtype mismatch at layer {layer}")


def capture_prompt(text):
    input_ids = model.encode(text, max_length=MAX_PROMPT_TOKENS)
    if input_ids.shape[-1] < 2:
        raise RuntimeError("smoke input is too short for position -2")
    final_layer = model.n_layers - 1
    record_at = sorted(set(SELECTED_LAYERS) | {0, final_layer})
    with torch.inference_mode(), ActivationRecorder(model.layers, at=record_at) as recorder:
        model.forward(input_ids)
    selected = {
        layer: recorder.activations[layer][0, POSITIONS[0], :].detach().float().cpu()
        for layer in SELECTED_LAYERS
    }
    layer0 = recorder.activations[0][0, POSITIONS[0], :].detach().float().cpu()
    final = recorder.activations[final_layer][0, POSITIONS[0], :].detach().float()
    output_logits = model.unembed(final).float().cpu()
    return selected, layer0, output_logits, input_ids


def decode_numpy(vector):
    tensor = torch.as_tensor(vector, dtype=torch.float32, device=model.input_device)
    return model.unembed(tensor).float().cpu()


started = time.perf_counter()
captured = {}
for prompt in prompts:
    captured[prompt["sha256"]] = capture_prompt(prompt["text"])
timings["capture_nine_prompts"] = time.perf_counter() - started

recipient = prompts[0]
recipient_digest = recipient["sha256"]
recipient_residuals, recipient_layer0, output_logits, recipient_ids = captured[
    recipient_digest
]
target_id = int(output_logits.argmax())
vocab_size = int(model_hf.config.vocab_size)

rank_probe_logits = torch.tensor([[0.1, 0.4, -0.2, 0.3]], dtype=torch.float32)
rank_probe_targets = torch.tensor([0, 1, 2, 3], dtype=torch.long)
jlens_rank1 = (_ranks_of(rank_probe_logits, rank_probe_targets) + 1)[0].tolist()
rank_parity_verified = all(
    ep.target_rank1(rank_probe_logits[0].tolist(), int(target)) == reference
    for target, reference in zip(rank_probe_targets, jlens_rank1, strict=True)
)
if not rank_parity_verified:
    raise RuntimeError("rank convention parity failed")

started = time.perf_counter()
transport_parity = {}
for layer in SELECTED_LAYERS:
    residual = recipient_residuals[layer]
    numpy_value = residual.numpy()
    expected = ep.transport_with(numpy_value, lens.jacobians[layer].numpy())
    observed = lens.transport(residual, layer).cpu().numpy()
    transport_parity[str(layer)] = bool(
        np.allclose(expected, observed, rtol=1e-5, atol=1e-5)
    )
if not all(transport_parity.values()):
    raise RuntimeError(f"transport parity failed: {transport_parity!r}")
timings["selected_layer_probes"] = time.perf_counter() - started
"""
        ),
        _markdown(
            """## 5. Run one full excluded-input 81-readout crossing

This is an engineering compatibility measurement at layer 13. Smoke-only seeds
are not pilot seeds, and no NTA threshold, gate, or scientific decision is
computed.
"""
        ),
        _code(
            """def score_logits(logits):
    rank1 = ep.target_rank1(logits.tolist(), target_id)
    return ep.rank_score(rank1, vocab_size)


prompt_embedding = model_hf.get_input_embeddings()(
    recipient_ids.to(model.input_device)
)[0, POSITIONS[0], :]
primary_floor_score = score_logits(model.unembed(prompt_embedding).float().cpu())
layer0_floor_score = score_logits(decode_numpy(recipient_layer0.numpy()))
output_score = score_logits(output_logits)

layer = REPRESENTATIVE_LAYER
residuals_at_layer = {
    digest: values[0][layer].numpy() for digest, values in captured.items()
}
donor_assignments = smoke.select_smoke_donors(
    residuals_at_layer, recipient_sha256=recipient_digest
)
wrong_residuals = {
    assignment["donor_assignment_id"]: assignment.pop("residual")
    for assignment in donor_assignments
}
fitted = lens.jacobians[layer].numpy()
broken_maps = {}
map_draws = []
for index, seed in enumerate(smoke.SMOKE_MAP_SEEDS):
    map_id = f"smoke-map-{index}"
    broken = ep.build_fit_broken_map(fitted, seed)
    digest_once = smoke.array_sha256(broken)
    digest_twice = smoke.array_sha256(broken.copy())
    if digest_once != digest_twice:
        raise RuntimeError("broken-map runtime hash repetition failed")
    broken_maps[map_id] = broken
    map_draws.append({"map_draw_id": map_id, "seed": seed, "sha256": digest_once})

correct = residuals_at_layer[recipient_digest]
started = time.perf_counter()
vectors = {
    "correct_act_fitted_map": ep.transport_with(correct, fitted),
    "correct_act_broken_map": {
        map_id: ep.transport_with(correct, matrix)
        for map_id, matrix in broken_maps.items()
    },
    "wrong_act_fitted_map": {
        donor_id: ep.transport_with(residual, fitted)
        for donor_id, residual in wrong_residuals.items()
    },
    "wrong_act_broken_map": {
        donor_id: {
            map_id: ep.transport_with(residual, matrix)
            for map_id, matrix in broken_maps.items()
        }
        for donor_id, residual in wrong_residuals.items()
    },
}


def map_factorized(tree, transform):
    if isinstance(tree, dict):
        return {key: map_factorized(value, transform) for key, value in tree.items()}
    return transform(tree)


factorized_scores = map_factorized(
    vectors, lambda vector: score_logits(decode_numpy(vector))
)
crossing = ep.materialize_crossed_factorials(factorized_scores)
timings["full_81_readout_crossing"] = time.perf_counter() - started
if crossing["unique_readout_count"] != 81 or crossing["logical_cell_count"] != 64:
    raise RuntimeError("full smoke crossing did not produce 81/64 counts")

runtime_hashes_repeated = all(
    assignment["residual_sha256"]
    == smoke.array_sha256(wrong_residuals[assignment["donor_assignment_id"]])
    for assignment in donor_assignments
)
if not runtime_hashes_repeated:
    raise RuntimeError("donor residual runtime hash repetition failed")

projection = smoke.project_pilot_readout_seconds(
    timings["full_81_readout_crossing"], observed_readouts=81
)
peak_allocated_gib = torch.cuda.max_memory_allocated() / (1024**3)
peak_reserved_gib = torch.cuda.max_memory_reserved() / (1024**3)
print(
    f"full crossing completed in {timings['full_81_readout_crossing']:.3f}s; "
    f"peak allocated {peak_allocated_gib:.3f} GiB"
)
"""
        ),
        _markdown(
            """## 6. Validate and retain a content-addressed runtime report

The report contains hashes, counts, timings, and VRAM only. Raw prompts,
activations, full logits, scientific gates, thresholds, and decisions are absent.
"""
        ),
        _code(
            """import datetime

report = {
    "schema": smoke.SMOKE_SCHEMA,
    "artifact_type": "integration_smoke",
    "run_id": str(uuid.uuid4()),
    "created_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
    "evidence_class": "runtime_compatibility_only",
    "scope": "excluded_input_open_loop_measurement",
    "authorization": {
        "integration_smoke_authorized": INTEGRATION_SMOKE_AUTHORIZED,
        "artifact_transfer_authorized": ARTIFACT_TRANSFER_AUTHORIZED,
    },
    "model": dict(smoke.PINNED_MODEL),
    "lens": {**smoke.PINNED_LENS, "source_layers": list(lens.source_layers)},
    "instrumentation": dict(smoke.PINNED_INSTRUMENTATION),
    "source_bundle": {
        "sha256": EXPECTED_BUNDLE_SHA256,
        "manifest": manifest,
    },
    "inputs": {
        "prompt_sha256s": [item["sha256"] for item in prompts],
        "recipient_sha256": recipient_digest,
        "raw_prompt_persisted": False,
        "prohibited_overlap_count": 0,
    },
    "design": {
        "selected_layers": SELECTED_LAYERS,
        "representative_crossing_layer": REPRESENTATIVE_LAYER,
        "positions": POSITIONS,
        "donor_assignment_count": 8,
        "broken_map_draw_count": 8,
        "unique_readouts": 81,
        "logical_crossings": 64,
        "smoke_donor_seeds": list(smoke.SMOKE_DONOR_SEEDS),
        "smoke_map_seeds": list(smoke.SMOKE_MAP_SEEDS),
    },
    "runtime": {
        "python": sys.version,
        "packages": observed_runtime_versions,
        "cuda_runtime": torch.version.cuda,
        "gpu_name": torch.cuda.get_device_name(0),
        "gpu_total_vram_gib": torch_vram_gib,
        "peak_allocated_gib": peak_allocated_gib,
        "peak_reserved_gib": peak_reserved_gib,
        "install_spec_sha256": install_spec_sha256,
        "fresh_process_after_install": fresh_process_after_install,
        "torchvision_state": torchvision_state,
    },
    "timings_seconds": timings,
    "measurement": {
        "all_selected_layers_probed": set(transport_parity) == {
            str(layer) for layer in SELECTED_LAYERS
        },
        "rank_parity_verified": rank_parity_verified,
        "transport_parity_verified": all(transport_parity.values()),
        "dual_floor_scores_recorded": all(
            np.isfinite(value)
            for value in (primary_floor_score, layer0_floor_score, output_score)
        ),
        "runtime_content_hashes_repeated": runtime_hashes_repeated,
        "unique_readout_count": crossing["unique_readout_count"],
        "logical_cell_count": crossing["logical_cell_count"],
    },
    "projection": projection,
    "retention": {
        "raw_activations_persisted": False,
        "full_logits_persisted": False,
        "raw_prompt_persisted": False,
    },
}
report_errors = smoke.validate_runtime_report(report)
if report_errors:
    raise RuntimeError("integration smoke report invalid: " + "; ".join(report_errors))

payload = (
    json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\\n"
).encode("utf-8")
report_sha256 = hashlib.sha256(payload).hexdigest()
report_dir = pathlib.Path("/content/jspace_stage2b_integration_smoke")
report_dir.mkdir(parents=True, exist_ok=True)
report_path = report_dir / f"stage2b_integration_smoke_{report_sha256[:16]}.json"
try:
    with report_path.open("xb") as handle:
        handle.write(payload)
except FileExistsError:
    if report_path.read_bytes() != payload:
        raise RuntimeError("content-addressed report path has different bytes") from None
if hashlib.sha256(report_path.read_bytes()).hexdigest() != report_sha256:
    raise RuntimeError("runtime report readback hash mismatch")
print(
    json.dumps(
        {
            "report_path": str(report_path),
            "sha256": report_sha256,
            "size_bytes": len(payload),
            "timings_seconds": timings,
            "projection": projection,
            "peak_allocated_gib": peak_allocated_gib,
            "peak_reserved_gib": peak_reserved_gib,
        },
        indent=2,
        sort_keys=True,
    )
)
"""
        ),
        _markdown("## 7. Optional artifact transfer: separately authorized\n"),
        _code(
            """if ARTIFACT_TRANSFER_AUTHORIZED is not True:
    print("runtime report retained in Colab; transfer not authorized")
else:
    from google.colab import files

    files.download(str(report_path))
"""
        ),
        _markdown(
            """## Stage gate

A successful run establishes API compatibility and measured engineering burden
for one excluded-input crossing only. It does not ratify statistical methods,
thresholds, multiplicity, pilot seeds, pilot execution, confirmation, artifact
transfer, publication, or scientific interpretation.
"""
        ),
    ]
    return {
        "cells": cells,
        "metadata": {
            "accelerator": "GPU",
            "colab": {"gpuType": "T4", "provenance": []},
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    notebook = build_notebook(bundle_sha256=args.bundle_sha256)
    payload = json.dumps(notebook, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
