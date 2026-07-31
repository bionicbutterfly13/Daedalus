"""Pure contract helpers for the excluded-input Stage 2b runtime smoke.

This module does not load a model, lens, CUDA runtime, pilot prompt, or
confirmatory prompt. The Colab notebook uses it to keep runtime compatibility
evidence separate from the scientific Stage 2b measurement schema.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Collection, Mapping, Sequence
from typing import Any

from stage2b_endpoint import select_wrong_activation

SMOKE_SCHEMA = "jspace-stage2b-integration-smoke/v3"
SELECTED_LAYERS = (6, 13, 20, 26)
REPRESENTATIVE_LAYER = 13
SMOKE_DONOR_SEEDS = (0, 1, 3, 4, 8, 9, 16, 30)
SMOKE_MAP_SEEDS = tuple(range(5000, 5008))

PINNED_MODEL = {
    "repo_id": "Qwen/Qwen3-1.7B",
    "revision": "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e",
    "n_layers": 28,
    "d_model": 2048,
}
PINNED_LENS = {
    "repo_id": "neuronpedia/jacobian-lens",
    "revision": "a4114d7752d11eb546e6cf372213d7e75526d3a1",
    "filename": "qwen3-1.7b/jlens/Salesforce-wikitext/Qwen3-1.7B_jacobian_lens.pt",
    "sha256": "6fcc79011bd921ffd87612255e2e99950a124fa519470ee44ebaf161c39be9d6",
    "d_model": 2048,
}
PINNED_INSTRUMENTATION = {
    "repo": "https://github.com/anthropics/jacobian-lens.git",
    "commit": "581d398613e5602a5af361e1c34d3a92ea82ba8e",
}

_PROMPT_TEXTS = (
    "Excluded integration recipient: the next word follows",
    "Excluded integration donor zero: alpha beta gamma",
    "Excluded integration donor one: copper silver gold",
    "Excluded integration donor two: north east west",
    "Excluded integration donor three: cedar pine maple",
    "Excluded integration donor four: orbit comet planet",
    "Excluded integration donor five: violin cello flute",
    "Excluded integration donor six: quartz granite marble",
    "Excluded integration donor seven: winter spring summer",
)


def smoke_prompts() -> list[dict[str, Any]]:
    """Return the fixed, non-scientific inputs used only for API/runtime smoke."""
    prompts = []
    for index, text in enumerate(_PROMPT_TEXTS):
        prompts.append(
            {
                "id": "smoke-recipient" if index == 0 else f"smoke-donor-{index - 1}",
                "text": text,
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "utf8_byte_count": len(text.encode("utf-8")),
            }
        )
    return prompts


def require_disjoint_inputs(
    prompts: Sequence[Mapping[str, Any]], prohibited_digests: Collection[str]
) -> None:
    """Reject any smoke input that overlaps a scientific input identity."""
    digests = [prompt.get("sha256") for prompt in prompts]
    if len(digests) != 9 or len(set(digests)) != 9:
        raise ValueError(
            "integration smoke requires exactly nine unique prompt digests"
        )
    overlap = set(digests) & set(prohibited_digests)
    if overlap:
        raise ValueError(
            f"integration smoke inputs overlap prohibited digests: {overlap}"
        )
    for prompt in prompts:
        text = prompt.get("text")
        digest = prompt.get("sha256")
        if not isinstance(text, str) or not text:
            raise ValueError("integration smoke prompt text must be non-empty")
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != digest:
            raise ValueError("integration smoke prompt digest disagrees with text")


def select_smoke_donors(
    residuals_by_prompt: Mapping[str, Any], *, recipient_sha256: str
) -> list[dict[str, Any]]:
    """Exercise donor selection with smoke-only seeds and require all eight donors."""
    assignments = []
    seen_sources: set[str] = set()
    for index, seed in enumerate(SMOKE_DONOR_SEEDS):
        residual, source = select_wrong_activation(
            residuals_by_prompt, recipient_sha256, seed=seed
        )
        if source in seen_sources:
            raise ValueError("smoke-only donor seeds did not cover eight unique donors")
        seen_sources.add(source)
        assignments.append(
            {
                "donor_assignment_id": f"smoke-donor-assignment-{index}",
                "seed": seed,
                "recipient_prompt_sha256": recipient_sha256,
                "source_prompt_sha256": source,
                "recipient_to_donor_sha256": hashlib.sha256(
                    f"{recipient_sha256}->{source}".encode("ascii")
                ).hexdigest(),
                "residual_sha256": array_sha256(residual),
                "residual": residual,
            }
        )
    return assignments


def array_sha256(value: Any) -> str:
    """Hash a runtime array using the Stage 2b dtype/shape/bytes convention."""
    import numpy as np

    array = np.ascontiguousarray(value)
    metadata = f"{array.dtype}:{array.shape}:".encode("ascii")
    return hashlib.sha256(metadata + array.tobytes()).hexdigest()


def project_pilot_readout_seconds(
    observed_seconds: float, *, observed_readouts: int
) -> dict[str, Any]:
    """Return a linear engineering projection, never a measured pilot runtime."""
    if (
        not isinstance(observed_seconds, (int, float))
        or isinstance(observed_seconds, bool)
        or not math.isfinite(float(observed_seconds))
        or observed_seconds <= 0
        or not isinstance(observed_readouts, int)
        or isinstance(observed_readouts, bool)
        or observed_readouts <= 0
    ):
        raise ValueError("projection inputs must be finite and positive")
    return {
        "basis_readouts": observed_readouts,
        "pilot_readouts": 6480,
        "linear_seconds": float(observed_seconds) * 6480 / observed_readouts,
        "status": "engineering_projection_not_measured_pilot_runtime",
    }


def _finite_nonnegative(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and value >= 0
    )


def validate_runtime_report(report: Mapping[str, Any]) -> list[str]:
    """Validate runtime-compatibility evidence without scientific interpretation."""
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    required = {
        "schema",
        "artifact_type",
        "run_id",
        "created_at_utc",
        "evidence_class",
        "scope",
        "authorization",
        "model",
        "lens",
        "instrumentation",
        "source_bundle",
        "inputs",
        "design",
        "runtime",
        "timings_seconds",
        "measurement",
        "projection",
        "retention",
    }
    require(required <= set(report), "integration smoke report is incomplete")
    require(report.get("schema") == SMOKE_SCHEMA, "integration smoke schema is wrong")
    require(
        report.get("artifact_type") == "integration_smoke",
        "artifact_type must be integration_smoke",
    )
    require(
        report.get("evidence_class") == "runtime_compatibility_only",
        "evidence_class must be runtime_compatibility_only",
    )
    require(
        report.get("scope") == "excluded_input_open_loop_measurement",
        "scope must be excluded_input_open_loop_measurement",
    )
    authorization = report.get("authorization")
    require(
        isinstance(authorization, Mapping)
        and authorization.get("integration_smoke_authorized") is True,
        "integration smoke authorization must be explicit",
    )
    require(
        isinstance(authorization, Mapping)
        and authorization.get("artifact_transfer_authorized") is False,
        "artifact transfer must remain unauthorized",
    )
    for section, expected in (
        ("model", PINNED_MODEL),
        ("lens", PINNED_LENS),
        ("instrumentation", PINNED_INSTRUMENTATION),
    ):
        observed = report.get(section)
        require(
            isinstance(observed, Mapping)
            and all(observed.get(key) == value for key, value in expected.items()),
            f"{section} identity is not pinned",
        )
    source_bundle = report.get("source_bundle")
    bundle_manifest = (
        source_bundle.get("manifest") if isinstance(source_bundle, Mapping) else None
    )
    bundle_files = (
        bundle_manifest.get("files") if isinstance(bundle_manifest, Mapping) else None
    )
    require(
        isinstance(source_bundle, Mapping)
        and isinstance(source_bundle.get("sha256"), str)
        and len(source_bundle["sha256"]) == 64
        and all(
            character in "0123456789abcdef" for character in source_bundle["sha256"]
        )
        and isinstance(bundle_manifest, Mapping)
        and bundle_manifest.get("schema")
        == "jspace-stage2b-integration-smoke-bundle/v1"
        and isinstance(bundle_files, list)
        and [entry.get("name") for entry in bundle_files if isinstance(entry, Mapping)]
        == [
            "stage2b_endpoint.py",
            "stage2b_preflight.py",
            "stage2b_integration_smoke.py",
        ],
        "source bundle identity or manifest is invalid",
    )
    source_layers = (
        report.get("lens", {}).get("source_layers")
        if isinstance(report.get("lens"), Mapping)
        else None
    )
    require(
        isinstance(source_layers, list)
        and all(
            isinstance(layer, int) and not isinstance(layer, bool)
            for layer in source_layers
        )
        and len(source_layers) == len(set(source_layers))
        and set(SELECTED_LAYERS) <= set(source_layers),
        "lens source layers do not cover the selected layers",
    )
    inputs = report.get("inputs")
    prompts = smoke_prompts()
    require(
        isinstance(inputs, Mapping)
        and inputs.get("prompt_sha256s") == [prompt["sha256"] for prompt in prompts]
        and inputs.get("recipient_sha256") == prompts[0]["sha256"]
        and inputs.get("raw_prompt_persisted") is False
        and inputs.get("prohibited_overlap_count") == 0,
        "integration smoke inputs are not the fixed excluded identities",
    )
    design = report.get("design")
    require(
        isinstance(design, Mapping)
        and design.get("selected_layers") == list(SELECTED_LAYERS)
        and design.get("representative_crossing_layer") == REPRESENTATIVE_LAYER
        and design.get("positions") == [-2]
        and design.get("donor_assignment_count") == 8
        and design.get("broken_map_draw_count") == 8
        and design.get("unique_readouts") == 81
        and design.get("logical_crossings") == 64
        and design.get("smoke_donor_seeds") == list(SMOKE_DONOR_SEEDS)
        and design.get("smoke_map_seeds") == list(SMOKE_MAP_SEEDS),
        "smoke design must retain the 81-readout/64-cell technical crossing",
    )
    measurement = report.get("measurement")
    require(
        isinstance(measurement, Mapping)
        and measurement.get("all_selected_layers_probed") is True
        and measurement.get("rank_parity_verified") is True
        and measurement.get("transport_parity_verified") is True
        and measurement.get("dual_floor_scores_recorded") is True
        and measurement.get("runtime_content_hashes_repeated") is True
        and measurement.get("unique_readout_count") == 81
        and measurement.get("logical_cell_count") == 64,
        "smoke measurement did not verify all technical contracts and 81/64 counts",
    )
    runtime = report.get("runtime")
    require(
        isinstance(runtime, Mapping)
        and _finite_nonnegative(runtime.get("gpu_total_vram_gib"))
        and _finite_nonnegative(runtime.get("peak_allocated_gib"))
        and _finite_nonnegative(runtime.get("peak_reserved_gib")),
        "runtime VRAM measurements must be finite and nonnegative",
    )
    require(
        isinstance(runtime, Mapping)
        and isinstance(runtime.get("install_spec_sha256"), str)
        and len(runtime["install_spec_sha256"]) == 64
        and all(
            character in "0123456789abcdef"
            for character in runtime["install_spec_sha256"]
        ),
        "runtime install specification SHA-256 is invalid",
    )
    require(
        isinstance(runtime, Mapping)
        and runtime.get("fresh_process_after_install") is True,
        "runtime must prove a fresh process after pinned package installation",
    )
    require(
        isinstance(runtime, Mapping) and runtime.get("torchvision_state") == "absent",
        "runtime must prove torchvision is absent",
    )
    timings = report.get("timings_seconds")
    require(
        isinstance(timings, Mapping)
        and bool(timings)
        and all(_finite_nonnegative(value) for value in timings.values()),
        "runtime timings must be finite and nonnegative",
    )
    projection = report.get("projection")
    require(
        isinstance(projection, Mapping)
        and projection.get("basis_readouts") == 81
        and projection.get("pilot_readouts") == 6480
        and _finite_nonnegative(projection.get("linear_seconds"))
        and projection.get("status")
        == "engineering_projection_not_measured_pilot_runtime",
        "projection must remain a labeled 81-to-6480 engineering projection",
    )
    retention = report.get("retention")
    require(
        isinstance(retention, Mapping)
        and all(
            retention.get(field) is False
            for field in (
                "raw_activations_persisted",
                "full_logits_persisted",
                "raw_prompt_persisted",
            )
        ),
        "integration smoke retention boundary is incomplete",
    )
    for field in ("gates", "decision", "thresholds", "pilot_results"):
        require(field not in report, f"integration smoke report rejects {field}")
    return errors
