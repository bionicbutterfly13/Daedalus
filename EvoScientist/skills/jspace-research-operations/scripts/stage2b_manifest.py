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


def build_manifest(
    raw_stimuli: Sequence[tuple[str, str]],
    token_counts: Mapping[str, int] | None = None,
) -> dict[str, Any]:
    """Build the manifest document from ``(category, text)`` pairs.

    ``id`` is three digits (``s000``), not Stage 2's two: n=200 overflows ``s99``,
    and silently rolling over would give two prompts the same id.

    ``token_count`` is supplied by the caller because tokenizing needs the model.
    Where it is absent the field is ``None`` and :func:`check_manifest` will reject
    the manifest rather than skipping the length check.
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
                "token_count": (token_counts or {}).get(text),
            }
        )
    return {
        "manifest_version": MANIFEST_VERSION,
        "n_prompts": len(prompts),
        "categories": sorted({c for c, _ in raw_stimuli}),
        "prompts": prompts,
    }


def check_manifest(
    manifest: Mapping[str, Any],
    stage2_digests: Sequence[str],
    expected_digest: str | None = None,
    *,
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

        tokens = prompt.get("token_count")
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
