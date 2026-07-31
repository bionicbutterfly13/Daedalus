"""Stage 2b stimulus manifest: construction, digesting, and the held-out check.

Contract: ``specs/001-jspace-stage2b/data-model.md`` §1 and
``contracts/preflight-api.md``.

Canonicalization is byte-identical to Stage 2's so the two manifests' digests are
comparable objects rather than merely similar ones.

Stage 2's 50 prompts informed every design choice in Stage 2b — the endpoint, the
controls, the thresholds. Reusing them would make Stage 2b a test of a design
fitted to its own test set, so disjointness is *checked*, not documented as a rule.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from stage2b_preflight import PreflightError

__all__ = [
    "MANIFEST_VERSION",
    "build_manifest",
    "canonical_digest",
    "check_manifest",
    "check_pilot_view",
    "select_partition",
]

MANIFEST_VERSION = "jspace-stage2b-stimulus/v1"

#: Inherited from Stage 2 so per-category reporting stays comparable across stages.
CATEGORIES: tuple[str, ...] = (
    "antonym_negation",
    "arithmetic_completion",
    "category_membership",
    "factual_completion",
    "multi_token_entity",
)


def canonical_digest(document: Mapping[str, Any]) -> str:
    """SHA-256 of the canonical JSON encoding, matching Stage 2 exactly.

    ``sort_keys=True, indent=2, ensure_ascii=False`` plus a trailing newline. Any
    deviation produces a different digest for the same content, which would make
    the Stage 2 comparison meaningless.
    """
    canonical = (
        json.dumps(document, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_manifest(raw_stimuli: Sequence[tuple[str, str]]) -> dict[str, Any]:
    """Build the manifest document from ``(category, text)`` pairs.

    ``id`` is three digits (``s000``), not Stage 2's two: n=200 overflows ``s99``,
    and silently rolling over would give two prompts the same id.

    **Token counts are deliberately not in the manifest.** Tokenizing requires the
    model, which is not available where this file is authored, and writing an
    estimate into a content-addressed document would put a fabricated number into
    the record. Length is a property of the stimulus *under a tokenizer*, not of
    the stimulus, so it is measured at preflight and recorded in the artifact --
    which also keeps the manifest digest stable, since a count filled in later
    would change the digest the repo committed.
    """
    prompts = []
    for index, (category, text) in enumerate(raw_stimuli):
        encoded = text.encode("utf-8")
        prompts.append(
            {
                "id": f"s{index:03d}",
                "index": index,
                "category": category,
                "text": text,
                "sha256": hashlib.sha256(encoded).hexdigest(),
                "utf8_byte_count": len(encoded),
            }
        )
    return {
        "manifest_version": MANIFEST_VERSION,
        "n_prompts": len(prompts),
        "categories": sorted({c for c, _ in raw_stimuli}),
        "prompts": prompts,
    }


def check_pilot_view(
    view: Mapping[str, Any],
    stage2_digests: Sequence[str],
    *,
    expected_view_digest: str,
    expected_source_manifest_digest: str,
    expected_source_n_prompts: int,
    expected_n_categories: int,
    expected_pilot_subset_digest: str,
    expected_pilot_ids: Sequence[str],
    token_counts: Mapping[str, int],
    stage1_anchor_sha256: str,
    max_prompt_tokens: int = 128,
) -> None:
    """Validate the isolated 20-prompt pilot file without loading the holdout.

    The source-manifest digest binds the view to the separately audited 200-prompt
    document. The subset digest binds its ordered ``(id, sha256)`` pairs to that
    source identity. Neither check requires pilot code to read a confirmatory text.
    """
    if view.get("manifest_version") != "jspace-stage2b-pilot-view/v1":
        raise PreflightError(
            "pilot_view_version",
            f"unexpected pilot view version {view.get('manifest_version')!r}",
        )
    source_digest = view.get("source_manifest_sha256")
    if source_digest != expected_source_manifest_digest:
        raise PreflightError(
            "pilot_source_manifest_digest",
            f"pilot view names source {source_digest!r}, expected "
            f"{expected_source_manifest_digest!r}",
            observed=source_digest,
            expected=expected_source_manifest_digest,
        )
    if view.get("source_n_prompts") != expected_source_n_prompts:
        raise PreflightError(
            "pilot_source_manifest_size",
            f"pilot view names {view.get('source_n_prompts')!r} source prompts, "
            f"expected {expected_source_n_prompts}",
        )
    if canonical_digest(view) != expected_view_digest:
        raise PreflightError(
            "pilot_view_digest",
            "pilot view bytes do not match the independently pinned digest",
            observed=canonical_digest(view),
            expected=expected_view_digest,
        )

    prompts = view.get("prompts")
    if (
        not isinstance(prompts, list)
        or view.get("n_prompts") != 20
        or len(prompts) != 20
    ):
        raise PreflightError(
            "pilot_subset_size",
            "isolated pilot view must contain exactly 20 prompts",
            observed_count=len(prompts) if isinstance(prompts, list) else None,
        )
    observed_ids = [
        prompt.get("id") for prompt in prompts if isinstance(prompt, Mapping)
    ]
    if observed_ids != list(expected_pilot_ids):
        raise PreflightError(
            "pilot_subset_identity",
            "pilot view IDs do not match the preregistered ordered subset",
            observed=observed_ids,
        )

    categories = view.get("categories")
    category_counts: dict[str, int] = {}
    seen_digests: set[str] = set()
    stage2 = set(stage2_digests)
    for prompt in prompts:
        if not isinstance(prompt, Mapping):
            raise PreflightError("pilot_prompt_shape", "pilot prompt must be an object")
        text = prompt.get("text")
        digest = prompt.get("sha256")
        if not isinstance(text, str) or not isinstance(digest, str):
            raise PreflightError(
                "pilot_prompt_shape", "pilot prompt text/digest is malformed"
            )
        encoded = text.encode("utf-8")
        if hashlib.sha256(encoded).hexdigest() != digest:
            raise PreflightError(
                "pilot_prompt_digest",
                f"pilot prompt {prompt.get('id')!r} text does not match its digest",
            )
        if prompt.get("utf8_byte_count") != len(encoded):
            raise PreflightError(
                "pilot_prompt_bytes",
                f"pilot prompt {prompt.get('id')!r} byte count is stale",
            )
        if digest in seen_digests:
            raise PreflightError("duplicate_prompt", f"duplicate pilot digest {digest}")
        seen_digests.add(digest)
        if digest in stage2:
            raise PreflightError(
                "stage2_overlap", f"pilot prompt overlaps Stage 2: {digest}"
            )
        if digest == stage1_anchor_sha256:
            raise PreflightError(
                "anchor_contamination", "Stage 1 anchor is in pilot view"
            )
        category = str(prompt.get("category"))
        category_counts[category] = category_counts.get(category, 0) + 1
        measured = token_counts.get(text)
        if not isinstance(measured, int) or isinstance(measured, bool):
            raise PreflightError(
                "prompt_too_long",
                f"pilot prompt {prompt.get('id')!r} has no measured token count",
            )
        if measured > max_prompt_tokens:
            raise PreflightError(
                "prompt_too_long",
                f"pilot prompt {prompt.get('id')!r} has {measured} tokens, max is "
                f"{max_prompt_tokens}",
            )
    if (
        not isinstance(categories, list)
        or len(categories) != expected_n_categories
        or set(category_counts) != set(categories)
        or set(category_counts.values()) != {4}
    ):
        raise PreflightError(
            "pilot_category_imbalance",
            f"pilot view must contain four prompts in every category, got {category_counts}",
        )

    subset_identity = {
        "manifest_sha256": source_digest,
        "pilot_prompts": [
            {"id": prompt["id"], "sha256": prompt["sha256"]} for prompt in prompts
        ],
    }
    observed_subset_digest = canonical_digest(subset_identity)
    if (
        view.get("pilot_subset_sha256") != expected_pilot_subset_digest
        or observed_subset_digest != expected_pilot_subset_digest
    ):
        raise PreflightError(
            "pilot_subset_digest",
            f"pilot subset recomputed {observed_subset_digest!r}, expected "
            f"{expected_pilot_subset_digest!r}",
        )


def select_partition(
    manifest: Mapping[str, Any],
    *,
    mode: str,
    pilot_ids: Sequence[str],
    expected_pilot_subset_sha256: str | None = None,
) -> dict[str, Any]:
    """Return only the prompts authorized for one run mode.

    The caller must supply the preregistered pilot IDs. Their identity is hashed
    together with the full-manifest digest, and that hash can be pinned outside
    the manifest. Pilot code receives only the 20 selected prompt records;
    confirmatory code receives only the disjoint complement.
    """
    if mode not in {"pilot", "confirmatory"}:
        raise PreflightError(
            "invalid_run_mode",
            f"run mode must be 'pilot' or 'confirmatory', got {mode!r}",
            mode=mode,
        )

    unique_pilot_ids = set(pilot_ids)
    if len(pilot_ids) != 20 or len(unique_pilot_ids) != 20:
        raise PreflightError(
            "pilot_subset_size",
            "the preregistered pilot subset must contain exactly 20 unique IDs",
            observed_count=len(pilot_ids),
            unique_count=len(unique_pilot_ids),
        )

    prompts = manifest.get("prompts")
    if not isinstance(prompts, list):
        raise PreflightError("manifest_size", "manifest.prompts must be a list")
    prompt_by_id = {
        prompt.get("id"): prompt for prompt in prompts if isinstance(prompt, Mapping)
    }
    unknown = sorted(unique_pilot_ids - prompt_by_id.keys())
    if unknown:
        raise PreflightError(
            "unknown_pilot_prompt",
            f"pilot IDs are absent from the pinned manifest: {unknown}",
            prompt_ids=unknown,
        )

    pilot_prompts = [
        prompt for prompt in prompts if prompt.get("id") in unique_pilot_ids
    ]
    category_counts: dict[str, int] = {}
    for prompt in pilot_prompts:
        category = str(prompt.get("category"))
        category_counts[category] = category_counts.get(category, 0) + 1
    raw_categories = manifest.get("categories")
    manifest_categories = (
        [str(category) for category in raw_categories]
        if isinstance(raw_categories, list)
        else []
    )
    category_total = len(manifest_categories)
    expected_per_category, remainder = divmod(20, category_total or 1)
    if (
        category_total == 0
        or remainder
        or set(category_counts) != set(manifest_categories)
        or set(category_counts.values()) != {expected_per_category}
    ):
        raise PreflightError(
            "pilot_category_imbalance",
            f"pilot must be balanced across manifest categories, got {category_counts}",
            observed=category_counts,
        )

    manifest_sha256 = canonical_digest(dict(manifest))
    subset_identity = {
        "manifest_sha256": manifest_sha256,
        "pilot_prompts": [
            {"id": prompt["id"], "sha256": prompt["sha256"]} for prompt in pilot_prompts
        ],
    }
    pilot_subset_sha256 = canonical_digest(subset_identity)
    if (
        expected_pilot_subset_sha256 is not None
        and pilot_subset_sha256 != expected_pilot_subset_sha256
    ):
        raise PreflightError(
            "pilot_subset_digest",
            f"recomputed {pilot_subset_sha256!r}, expected "
            f"{expected_pilot_subset_sha256!r}",
            observed=pilot_subset_sha256,
            expected=expected_pilot_subset_sha256,
        )

    selected = (
        pilot_prompts
        if mode == "pilot"
        else [prompt for prompt in prompts if prompt.get("id") not in unique_pilot_ids]
    )
    selected_category_counts: dict[str, int] = {}
    for prompt in selected:
        category = str(prompt.get("category"))
        selected_category_counts[category] = (
            selected_category_counts.get(category, 0) + 1
        )
    return {
        "mode": mode,
        "manifest_sha256": manifest_sha256,
        "pilot_subset_sha256": pilot_subset_sha256,
        "n_prompts": len(selected),
        "category_counts": selected_category_counts,
        "prompts": selected,
    }


def check_manifest(
    manifest: Mapping[str, Any],
    stage2_digests: Sequence[str],
    expected_digest: str | None = None,
    *,
    token_counts: Mapping[str, int] | None = None,
    n_prompts: int = 200,
    n_categories: int = 5,
    max_prompt_tokens: int = 128,
    stage1_anchor_sha256: str | None = None,
) -> None:
    """Fail closed on anything that would compromise held-out status.

    ``expected_digest`` is a parameter rather than a field read back out of
    ``manifest``. A document cannot contain its own hash, and a digest check that
    finds its expected value inside the thing it is checking is a tautology.
    """
    if manifest.get("manifest_version") != MANIFEST_VERSION:
        raise PreflightError(
            "manifest_version",
            f"expected {MANIFEST_VERSION!r}, got {manifest.get('manifest_version')!r}",
        )

    prompts = manifest.get("prompts") or []
    if manifest.get("n_prompts") != len(prompts) or len(prompts) != n_prompts:
        raise PreflightError(
            "manifest_size",
            f"declared {manifest.get('n_prompts')!r}, holds {len(prompts)}, "
            f"expected {n_prompts}",
        )

    per_category: dict[str, int] = {}
    for prompt in prompts:
        per_category[prompt["category"]] = per_category.get(prompt["category"], 0) + 1
    expected_per_category, remainder = divmod(n_prompts, n_categories)
    if (
        len(per_category) != n_categories
        or remainder
        or set(per_category.values()) != {expected_per_category}
    ):
        raise PreflightError(
            "category_imbalance",
            f"expected {n_categories} categories of {expected_per_category}, "
            f"got {per_category}",
            observed=per_category,
        )

    digests: list[str] = []
    for prompt in prompts:
        digest = prompt.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            raise PreflightError(
                "malformed_digest",
                f"{prompt.get('id')!r} has digest {digest!r}",
                prompt_id=prompt.get("id"),
            )
        if digest != hashlib.sha256(prompt["text"].encode("utf-8")).hexdigest():
            raise PreflightError(
                "malformed_digest",
                f"{prompt['id']!r} digest does not match its own text",
                prompt_id=prompt["id"],
            )
        digests.append(digest)

        # Measured at preflight against the live tokenizer, not read from the
        # manifest. Where no counts are supplied the check is skipped rather than
        # faked -- and the notebook must supply them, since a length that was
        # never measured is not a length that passed.
        if token_counts is not None:
            tokens = token_counts.get(prompt["text"])
            if tokens is None or tokens > max_prompt_tokens:
                raise PreflightError(
                    "prompt_too_long",
                    f"{prompt['id']!r} has token_count {tokens!r}, "
                    f"limit {max_prompt_tokens}",
                    prompt_id=prompt["id"],
                    observed=tokens,
                )

    if len(set(digests)) != len(digests):
        raise PreflightError(
            "duplicate_prompt", "the manifest contains a repeated prompt"
        )

    # Two distinct contamination codes on purpose. Both are held-out failures, but
    # the anchor is deliberately retained elsewhere in the protocol as the
    # reproduction kill check, so diagnosing it as an ordinary overlap bug would
    # send someone looking in the wrong place.
    if stage1_anchor_sha256 and stage1_anchor_sha256 in set(digests):
        raise PreflightError(
            "anchor_contamination",
            "the Stage 1 anchor is inside the analysis sample; it is the one "
            "prompt every prior stage has seen",
        )

    overlap = set(digests) & set(stage2_digests)
    if overlap:
        raise PreflightError(
            "stage2_overlap",
            f"{len(overlap)} prompt(s) also appear in the Stage 2 manifest; "
            "Stage 2 is pilot data and its stimuli shaped this design",
            overlap_count=len(overlap),
        )

    if expected_digest is not None:
        actual = canonical_digest(dict(manifest))
        if actual != expected_digest:
            raise PreflightError(
                "manifest_digest",
                f"recomputed {actual!r}, expected {expected_digest!r}",
                observed=actual,
                expected=expected_digest,
            )
