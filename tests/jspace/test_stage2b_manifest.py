"""Manifest tests: held-out status must be checked, never merely documented.

Stage 2's 50 prompts informed every design choice in Stage 2b — the endpoint, the
controls, the thresholds. Reusing any of them would make Stage 2b a test of a
design fitted to its own test set, so the disjointness assertion is the
load-bearing test in this file.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import sys

import pytest

_SCRIPTS = (
    pathlib.Path(__file__).resolve().parents[2]
    / "EvoScientist/skills/jspace-research-operations/scripts"
)
sys.path.insert(0, str(_SCRIPTS))


def _load(name):
    spec = importlib.util.spec_from_file_location(name, _SCRIPTS / f"{name}.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


preflight = _load("stage2b_preflight")
manifest_mod = _load("stage2b_manifest")

_FIXTURE = json.loads(
    (
        pathlib.Path(__file__).parent / "fixtures/stage2_manifest_digests.json"
    ).read_text()
)
STAGE2_DIGESTS = _FIXTURE["digests"]
STAGE1_ANCHOR = _FIXTURE["stage1_anchor_sha256"]

CATEGORIES = list(manifest_mod.CATEGORIES)


def _stimuli(n_per_category=40, prefix="stage2b unique prompt"):
    return [
        (category, f"{prefix} {category} {i}")
        for category in CATEGORIES
        for i in range(n_per_category)
    ]


def _manifest(**kw):
    stimuli = kw.pop("stimuli", None) or _stimuli()
    counts = {text: 12 for _, text in stimuli}
    return manifest_mod.build_manifest(stimuli, counts)


def _check(manifest, **kw):
    kw.setdefault("stage1_anchor_sha256", STAGE1_ANCHOR)
    manifest_mod.check_manifest(manifest, STAGE2_DIGESTS, **kw)


class TestFixtureIntegrity:
    """The fixture is the referent for every disjointness claim."""

    def test_fixture_holds_all_fifty_stage2_digests(self):
        assert len(STAGE2_DIGESTS) == 50
        assert len(set(STAGE2_DIGESTS)) == 50

    def test_fixture_is_pinned_to_the_notebooks_own_canonicalization(self):
        """digests[0] equals STAGE1_PROMPT_SHA256, which is what proves the
        extraction reproduces the notebook rather than approximating it."""
        assert STAGE2_DIGESTS[0] == STAGE1_ANCHOR
        assert (
            STAGE1_ANCHOR
            == preflight.INITIAL_REGISTRY["STAGE1_PROMPT_SHA256"]["declared_value"]
        )


class TestBuildManifest:
    def test_ids_are_three_digits_so_two_hundred_does_not_collide(self):
        """Stage 2 used two digits for n=50; n=200 would roll over at s99 and
        silently give two prompts the same id."""
        built = _manifest()
        assert built["prompts"][0]["id"] == "s000"
        assert built["prompts"][199]["id"] == "s199"

    def test_digests_match_the_text(self):
        built = _manifest()
        for prompt in built["prompts"]:
            expected = hashlib.sha256(prompt["text"].encode("utf-8")).hexdigest()
            assert prompt["sha256"] == expected

    def test_canonicalization_matches_stage_twos_scheme(self):
        """Byte-identical, so the two manifests' digests are comparable objects."""
        doc = {"b": 2, "a": 1}
        expected = hashlib.sha256(
            (
                json.dumps(doc, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
            ).encode()
        ).hexdigest()
        assert manifest_mod.canonical_digest(doc) == expected


class TestCheckManifest:
    def test_a_valid_manifest_passes(self):
        _check(_manifest())

    def test_wrong_version_is_rejected(self):
        bad = {**_manifest(), "manifest_version": "jspace-stage2-stimulus/v1"}
        with pytest.raises(preflight.PreflightError) as exc:
            _check(bad)
        assert exc.value.code == "manifest_version"

    def test_wrong_size_is_rejected(self):
        with pytest.raises(preflight.PreflightError) as exc:
            _check(_manifest(stimuli=_stimuli(n_per_category=10)))
        assert exc.value.code == "manifest_size"

    def test_declared_count_disagreeing_with_contents_is_rejected(self):
        bad = {**_manifest(), "n_prompts": 999}
        with pytest.raises(preflight.PreflightError) as exc:
            _check(bad)
        assert exc.value.code == "manifest_size"

    def test_category_imbalance_is_rejected(self):
        stimuli = _stimuli(n_per_category=40)
        stimuli[0] = (CATEGORIES[1], stimuli[0][1])  # 41/39 split
        with pytest.raises(preflight.PreflightError) as exc:
            _check(_manifest(stimuli=stimuli))
        assert exc.value.code == "category_imbalance"

    def test_malformed_digest_is_rejected(self):
        built = _manifest()
        built["prompts"][3]["sha256"] = "abc"
        with pytest.raises(preflight.PreflightError) as exc:
            _check(built)
        assert exc.value.code == "malformed_digest"

    def test_digest_not_matching_its_own_text_is_rejected(self):
        """Catches a manifest edited after its digests were computed."""
        built = _manifest()
        built["prompts"][3]["text"] = "silently changed after digesting"
        with pytest.raises(preflight.PreflightError) as exc:
            _check(built)
        assert exc.value.code == "malformed_digest"

    def test_duplicate_prompt_is_rejected(self):
        stimuli = _stimuli()
        stimuli[7] = stimuli[6]
        with pytest.raises(preflight.PreflightError) as exc:
            _check(_manifest(stimuli=stimuli))
        assert exc.value.code == "duplicate_prompt"

    def test_over_long_prompt_is_rejected(self):
        built = _manifest()
        built["prompts"][11]["token_count"] = 500
        with pytest.raises(preflight.PreflightError) as exc:
            _check(built)
        assert exc.value.code == "prompt_too_long"

    def test_missing_token_count_is_rejected_rather_than_skipped(self):
        """An unmeasured length is not a passing length."""
        built = _manifest()
        built["prompts"][11]["token_count"] = None
        with pytest.raises(preflight.PreflightError) as exc:
            _check(built)
        assert exc.value.code == "prompt_too_long"


class TestHeldOutStatus:
    """FR-011. The load-bearing tests in this file."""

    def test_a_stage2_prompt_in_the_manifest_is_rejected(self):
        stimuli = _stimuli()
        stage2_text = "Fact: The currency used in the country shaped like a boot is"
        stimuli[5] = (CATEGORIES[0], stage2_text)
        # keep the category balanced so the overlap check is what fires
        built = _manifest(stimuli=stimuli)
        with pytest.raises(preflight.PreflightError) as exc:
            _check(built)
        assert exc.value.code in {"stage2_overlap", "anchor_contamination"}

    def test_the_stage1_anchor_gets_its_own_distinct_code(self):
        """Both are contamination, but the anchor is deliberately retained
        elsewhere as the reproduction kill check. Diagnosing it as an ordinary
        overlap bug would send someone looking in the wrong place."""
        stimuli = _stimuli()
        anchor_text = "Fact: The currency used in the country shaped like a boot is"
        stimuli[5] = (CATEGORIES[0], anchor_text)
        assert hashlib.sha256(anchor_text.encode()).hexdigest() == STAGE1_ANCHOR, (
            "fixture drifted from the anchor text"
        )
        with pytest.raises(preflight.PreflightError) as exc:
            _check(_manifest(stimuli=stimuli))
        assert exc.value.code == "anchor_contamination"

    def test_overlap_reports_how_many_prompts_collided(self):
        stimuli = _stimuli()
        with pytest.raises(preflight.PreflightError) as exc:
            manifest_mod.check_manifest(
                _manifest(stimuli=stimuli),
                [*STAGE2_DIGESTS, _manifest(stimuli=stimuli)["prompts"][0]["sha256"]],
            )
        assert exc.value.code == "stage2_overlap"
        assert exc.value.detail["overlap_count"] == 1


class TestManifestDigest:
    def test_matching_expected_digest_passes(self):
        built = _manifest()
        _check(built, expected_digest=manifest_mod.canonical_digest(built))

    def test_mismatched_expected_digest_is_rejected(self):
        with pytest.raises(preflight.PreflightError) as exc:
            _check(_manifest(), expected_digest="0" * 64)
        assert exc.value.code == "manifest_digest"

    def test_the_digest_is_not_read_back_out_of_the_manifest(self):
        """A document cannot contain its own hash. A check that finds its
        expected value inside the thing it is checking is a tautology."""
        built = _manifest()
        assert "sha256" not in built
        assert "digest" not in built
