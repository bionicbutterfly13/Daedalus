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
    return manifest_mod.build_manifest(stimuli)


def _counts(manifest, value=12):
    return {p["text"]: value for p in manifest["prompts"]}


def _check(manifest, **kw):
    kw.setdefault("stage1_anchor_sha256", STAGE1_ANCHOR)
    manifest_mod.check_manifest(manifest, STAGE2_DIGESTS, **kw)


def _pilot_ids():
    """Four preregistered IDs from each category block."""
    return [
        f"s{base + offset:03d}" for base in range(0, 200, 40) for offset in range(4)
    ]


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
        counts = _counts(built)
        counts[built["prompts"][11]["text"]] = 500
        with pytest.raises(preflight.PreflightError) as exc:
            _check(built, token_counts=counts)
        assert exc.value.code == "prompt_too_long"

    def test_a_prompt_with_no_measured_count_is_rejected(self):
        """An unmeasured length is not a passing length."""
        built = _manifest()
        counts = _counts(built)
        del counts[built["prompts"][11]["text"]]
        with pytest.raises(preflight.PreflightError) as exc:
            _check(built, token_counts=counts)
        assert exc.value.code == "prompt_too_long"

    def test_token_counts_are_not_stored_in_the_manifest(self):
        """Tokenizing needs the model. Writing an estimate into a
        content-addressed document would put a fabricated number in the record,
        and filling it in later would change the digest the repo committed."""
        assert "token_count" not in _manifest()["prompts"][0]

    def test_counts_within_the_limit_pass(self):
        built = _manifest()
        _check(built, token_counts=_counts(built, value=11))


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


class TestRunPartition:
    """The pilot process must have no path to the 180-prompt holdout."""

    def test_pilot_returns_exactly_the_pinned_twenty_in_original_order(self):
        built = _manifest()
        selected = manifest_mod.select_partition(
            built,
            mode="pilot",
            pilot_ids=_pilot_ids(),
        )
        assert [prompt["id"] for prompt in selected["prompts"]] == _pilot_ids()
        assert selected["n_prompts"] == 20
        assert set(selected["category_counts"].values()) == {4}

    def test_confirmatory_partition_is_the_disjoint_remaining_180(self):
        built = _manifest()
        pilot = manifest_mod.select_partition(
            built, mode="pilot", pilot_ids=_pilot_ids()
        )
        confirmatory = manifest_mod.select_partition(
            built,
            mode="confirmatory",
            pilot_ids=_pilot_ids(),
        )
        pilot_ids = {prompt["id"] for prompt in pilot["prompts"]}
        confirmatory_ids = {prompt["id"] for prompt in confirmatory["prompts"]}
        assert len(confirmatory_ids) == 180
        assert pilot_ids.isdisjoint(confirmatory_ids)
        assert pilot_ids | confirmatory_ids == {
            prompt["id"] for prompt in built["prompts"]
        }

    def test_independently_pinned_subset_digest_is_checked(self):
        built = _manifest()
        selected = manifest_mod.select_partition(
            built,
            mode="pilot",
            pilot_ids=_pilot_ids(),
        )
        assert selected["pilot_subset_sha256"]
        with pytest.raises(preflight.PreflightError) as exc:
            manifest_mod.select_partition(
                built,
                mode="pilot",
                pilot_ids=_pilot_ids(),
                expected_pilot_subset_sha256="0" * 64,
            )
        assert exc.value.code == "pilot_subset_digest"

    def test_unknown_pilot_id_is_rejected(self):
        with pytest.raises(preflight.PreflightError) as exc:
            manifest_mod.select_partition(
                _manifest(),
                mode="pilot",
                pilot_ids=[*_pilot_ids()[:-1], "s999"],
            )
        assert exc.value.code == "unknown_pilot_prompt"

    def test_duplicate_pilot_id_is_rejected(self):
        ids = _pilot_ids()
        ids[-1] = ids[0]
        with pytest.raises(preflight.PreflightError) as exc:
            manifest_mod.select_partition(_manifest(), mode="pilot", pilot_ids=ids)
        assert exc.value.code == "pilot_subset_size"

    def test_single_category_first_twenty_is_rejected(self):
        """The shipped manifest is category-blocked, so literal first-20 is biased."""
        with pytest.raises(preflight.PreflightError) as exc:
            manifest_mod.select_partition(
                _manifest(),
                mode="pilot",
                pilot_ids=[f"s{index:03d}" for index in range(20)],
            )
        assert exc.value.code == "pilot_category_imbalance"

    @pytest.mark.parametrize("mode", ["", "exploratory", "PILOT"])
    def test_unknown_partition_mode_is_rejected(self, mode):
        with pytest.raises(preflight.PreflightError) as exc:
            manifest_mod.select_partition(
                _manifest(),
                mode=mode,
                pilot_ids=_pilot_ids(),
            )
        assert exc.value.code == "invalid_run_mode"


class TestShippedManifest:
    """Tests the file that will actually be used, not just the generator.

    A generator that produces a valid manifest and a committed manifest that is
    valid are different claims. Only the second one matters at run time.
    """

    SHIPPED = pathlib.Path(__file__).resolve().parents[2] / (
        "j-space-lab/jspace-stage2b-stimulus-v1.json"
    )

    def _shipped(self):
        if not self.SHIPPED.exists():
            pytest.skip("stimulus manifest not present on this branch")
        return json.loads(self.SHIPPED.read_text())

    def test_shipped_manifest_passes_every_check(self):
        _check(self._shipped())

    def test_shipped_manifest_is_disjoint_from_stage_two(self):
        """FR-011, against the real file. Building this manifest turned up 11
        accidental collisions with Stage 2 — the check is what caught them."""
        digests = {p["sha256"] for p in self._shipped()["prompts"]}
        assert digests.isdisjoint(STAGE2_DIGESTS)

    def test_shipped_manifest_excludes_the_stage_one_anchor(self):
        digests = {p["sha256"] for p in self._shipped()["prompts"]}
        assert STAGE1_ANCHOR not in digests

    def test_shipped_manifest_has_two_hundred_prompts_in_five_categories(self):
        shipped = self._shipped()
        assert shipped["n_prompts"] == 200
        counts: dict[str, int] = {}
        for prompt in shipped["prompts"]:
            counts[prompt["category"]] = counts.get(prompt["category"], 0) + 1
        assert set(counts.values()) == {40}
        assert set(counts) == set(CATEGORIES)

    def test_generator_reproduces_the_shipped_file_exactly(self):
        """If these drift, the committed digest describes something that is no
        longer what the generator makes."""
        stimuli = _load("stage2b_stimuli").RAW_STIMULI
        assert manifest_mod.canonical_digest(
            manifest_mod.build_manifest(stimuli)
        ) == manifest_mod.canonical_digest(self._shipped())


class TestSyntheticPilotViewContract:
    """Exercise an isolated view without opening the real pilot-view file."""

    SOURCE_DIGEST = "a" * 64

    def _pilot(self):
        categories = [f"category-{index}" for index in range(5)]
        prompts = []
        for index in range(20):
            text = f"synthetic pilot fixture {index}"
            prompts.append(
                {
                    "id": f"fixture-{index:03d}",
                    "text": text,
                    "sha256": hashlib.sha256(text.encode()).hexdigest(),
                    "utf8_byte_count": len(text.encode()),
                    "category": categories[index // 4],
                }
            )
        subset = {
            "manifest_sha256": self.SOURCE_DIGEST,
            "pilot_prompts": [
                {"id": prompt["id"], "sha256": prompt["sha256"]} for prompt in prompts
            ],
        }
        return {
            "manifest_version": "jspace-stage2b-pilot-view/v1",
            "source_manifest_sha256": self.SOURCE_DIGEST,
            "source_n_prompts": 200,
            "n_prompts": 20,
            "categories": categories,
            "pilot_subset_sha256": manifest_mod.canonical_digest(subset),
            "prompts": prompts,
        }

    def _check(self, view):
        expected = self._pilot()
        manifest_mod.check_pilot_view(
            view,
            STAGE2_DIGESTS,
            expected_view_digest=manifest_mod.canonical_digest(expected),
            expected_source_manifest_digest=self.SOURCE_DIGEST,
            expected_source_n_prompts=200,
            expected_n_categories=5,
            expected_pilot_subset_digest=expected["pilot_subset_sha256"],
            expected_pilot_ids=[prompt["id"] for prompt in expected["prompts"]],
            token_counts=_counts(view),
            stage1_anchor_sha256=STAGE1_ANCHOR,
        )

    def test_synthetic_pilot_view_passes_without_the_full_manifest(self):
        self._check(self._pilot())

    def test_source_manifest_identity_is_not_self_asserting(self):
        bad = {**self._pilot(), "source_manifest_sha256": "0" * 64}
        with pytest.raises(preflight.PreflightError) as exc:
            self._check(bad)
        assert exc.value.code == "pilot_source_manifest_digest"

    def test_prompt_text_tampering_is_rejected(self):
        bad = self._pilot()
        bad["prompts"][0]["text"] = "tampered after partitioning"
        with pytest.raises(preflight.PreflightError) as exc:
            self._check(bad)
        assert exc.value.code in {"pilot_prompt_digest", "pilot_view_digest"}
