"""CPU-only tests for Stage 2b descriptive measurement validation."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import sys
from copy import deepcopy
from typing import ClassVar

import pytest

_SCRIPTS = (
    pathlib.Path(__file__).resolve().parents[2]
    / "EvoScientist/skills/jspace-research-operations/scripts"
)
sys.path.insert(0, str(_SCRIPTS))
_spec = importlib.util.spec_from_file_location(
    "validate_observation", _SCRIPTS / "validate_observation.py"
)
assert _spec is not None
assert _spec.loader is not None
validator = importlib.util.module_from_spec(_spec)
sys.modules["validate_observation"] = validator
_spec.loader.exec_module(validator)


def _map_factorized(tree, transform):
    if isinstance(tree, dict):
        return {key: _map_factorized(value, transform) for key, value in tree.items()}
    return transform(tree)


def _canonical_digest(document):
    payload = json.dumps(document, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    return hashlib.sha256(payload.encode()).hexdigest()


def _target_decision_digest(target_id, derivation):
    bound = {
        "target_id": target_id,
        **{
            key: value
            for key, value in derivation.items()
            if key != "target_decision_sha256"
        },
    }
    payload = json.dumps(
        bound, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    return hashlib.sha256((payload + "\n").encode("ascii")).hexdigest()


def _target_derivation(target_id=7):
    derivation = {
        "method": "model_argmax",
        "output_logits_sha256": hashlib.sha256(b"fixture-output-logits").hexdigest(),
        "output_logits_dtype": "float32",
        "output_logits_shape": [151936],
        "max_logit": 3.25,
        "argmax_tie_token_ids": [target_id],
        "tie_break_rule": "lowest_token_id",
        "runtime_verifier_id": validator.STAGE2B_TARGET_RUNTIME_VERIFIER,
        "runtime_verified": True,
    }
    derivation["target_decision_sha256"] = _target_decision_digest(
        target_id, derivation
    )
    return derivation


def _spectrum_check(layer, map_id):
    return {
        "schema": "stage2b-map-spectrum-check/v1",
        "method": "numpy.linalg.svd-allclose/v1",
        "singular_value_count": 2048,
        "fitted_singular_values_sha256": hashlib.sha256(
            f"fitted-spectrum:{layer}".encode()
        ).hexdigest(),
        "broken_singular_values_sha256": hashlib.sha256(
            f"broken-spectrum:{layer}:{map_id}".encode()
        ).hexdigest(),
        "rtol": validator.SINGULAR_SPECTRUM_RTOL,
        "atol": validator.SINGULAR_SPECTRUM_ATOL,
        "max_abs_diff": 0.0,
        "max_normalized_error": 0.0,
        "verified": True,
    }


def _recompute_factorized_nta(record, min_denominator=0.25):
    floors = record["floor_scores"]
    dual = _map_factorized(
        record["factorized_scores"],
        lambda score: validator.dual_floor_nta(
            s_readout=score,
            s_input_embedding=floors["input_embedding_decoded"],
            s_layer0_residual=floors["layer0_residual_decoded"],
            s_output=floors["output_decoded"],
            min_denominator=min_denominator,
        ),
    )

    def select(value, floor):
        if isinstance(value, dict) and set(value) == {
            "input_embedding_decoded",
            "layer0_residual_decoded",
            "sensitivity_minus_primary",
        }:
            selected = value[floor]
            return None if isinstance(selected, validator.NTAExcluded) else selected
        return {key: select(child, floor) for key, child in value.items()}

    record["factorized_nta"] = {
        floor: select(dual, floor)
        for floor in (
            "input_embedding_decoded",
            "layer0_residual_decoded",
            "sensitivity_minus_primary",
        )
    }


_SELECTED_LAYERS = (6, 13, 20, 26)
_UNSET = object()
_PILOT_VIEW_PATH = (
    pathlib.Path(__file__).resolve().parents[2]
    / "j-space-lab/jspace-stage2b-pilot-v1.json"
)


def _pilot_view():
    return json.loads(_PILOT_VIEW_PATH.read_text(encoding="utf-8"))


def _compact_dual_floor_record(recipient_index=0, layer=6):
    view = _pilot_view()
    recipient_record = view["prompts"][recipient_index]
    recipient = recipient_record["sha256"]
    donor_ids = [f"donor-{index}" for index in range(8)]
    map_ids = [f"map-{index}" for index in range(8)]
    seed_vectors = validator.derive_crossing_seed_vectors()
    donor_seed_by_id = {entry["id"]: entry for entry in seed_vectors["donors"]}
    map_seed_by_id = {entry["id"]: entry for entry in seed_vectors["maps"]}
    scores = {
        "correct_act_fitted_map": 0.8,
        "correct_act_broken_map": {
            map_id: 0.4 + index / 100 for index, map_id in enumerate(map_ids)
        },
        "wrong_act_fitted_map": {
            donor_id: 0.3 + index / 100 for index, donor_id in enumerate(donor_ids)
        },
        "wrong_act_broken_map": {
            donor_id: {
                map_id: 0.1 + (donor_index + map_index) / 100
                for map_index, map_id in enumerate(map_ids)
            }
            for donor_index, donor_id in enumerate(donor_ids)
        },
    }
    primary = _map_factorized(scores, lambda score: score)
    sensitivity = _map_factorized(scores, lambda score: (score + 0.2) / 1.2)

    def subtract(primary_value, sensitivity_value):
        if isinstance(primary_value, dict):
            return {
                key: subtract(primary_value[key], sensitivity_value[key])
                for key in primary_value
            }
        return sensitivity_value - primary_value

    donor_assignments = []
    for _index, donor_id in enumerate(donor_ids):
        source = validator.select_wrong_activation_source(
            [prompt["sha256"] for prompt in view["prompts"]],
            recipient,
            donor_seed_by_id[donor_id]["seed"],
        )
        donor_assignments.append(
            {
                "donor_assignment_id": donor_id,
                "seed_index": donor_seed_by_id[donor_id]["index"],
                "seed_namespace": donor_seed_by_id[donor_id]["namespace"],
                "seed_sha256": donor_seed_by_id[donor_id]["sha256"],
                "seed": donor_seed_by_id[donor_id]["seed"],
                "bit_generator": donor_seed_by_id[donor_id]["bit_generator"],
                "recipient_prompt_sha256": recipient,
                "source_prompt_sha256": source,
                "recipient_to_donor_sha256": hashlib.sha256(
                    f"{recipient}->{source}".encode()
                ).hexdigest(),
                "residual_sha256": hashlib.sha256(
                    f"residual:{recipient}:{layer}:{donor_id}".encode()
                ).hexdigest(),
            }
        )
    return {
        "prompt_sha256": recipient,
        "category": recipient_record["category"],
        "layer": layer,
        "target_id": 7,
        "target_source": "model_argmax",
        "target_derivation": _target_derivation(),
        "donor_assignments": donor_assignments,
        "map_draws": [
            {
                "map_draw_id": map_id,
                "seed_index": map_seed_by_id[map_id]["index"],
                "seed_namespace": map_seed_by_id[map_id]["namespace"],
                "seed_sha256": map_seed_by_id[map_id]["sha256"],
                "seed": map_seed_by_id[map_id]["seed"],
                "bit_generator": map_seed_by_id[map_id]["bit_generator"],
                "sha256": hashlib.sha256(f"map:{layer}:{map_id}".encode()).hexdigest(),
                "spectrum_check": _spectrum_check(layer, map_id),
            }
            for index, map_id in enumerate(map_ids)
        ],
        "floor_scores": {
            "input_embedding_decoded": (
                -0.2 - (recipient_index * 4 + _SELECTED_LAYERS.index(layer)) / 100
            ),
            "layer0_residual_decoded": -0.5,
            "output_decoded": 0.0,
        },
        "factorized_scores": scores,
        "factorized_nta": {
            "input_embedding_decoded": primary,
            "layer0_residual_decoded": sensitivity,
            "sensitivity_minus_primary": subtract(primary, sensitivity),
        },
    }


class TestStage2bAggregate:
    _COMPACT_CACHE: ClassVar[dict | None] = None
    BASE: ClassVar[dict] = {
        "schema": "jspace-observation-stage2b/v1",
        "artifact_type": "aggregate",
        "run_mode": "pilot",
        "run_id": "synthetic-stage2b-validator-fixture",
        "created_at_utc": "2026-07-29T00:00:00+00:00",
        "evidence_class": "direct_runtime_measurement",
        "scope": "open_loop_observation_only",
        "model": {
            "repo_id": "Qwen/Qwen3-1.7B",
            "revision": "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e",
            "n_layers": 28,
            "d_model": 2048,
        },
        "lens": {
            "repo_id": "neuronpedia/jacobian-lens",
            "revision": "a4114d7752d11eb546e6cf372213d7e75526d3a1",
            "filename": "qwen3-1.7b/jlens/Salesforce-wikitext/Qwen3-1.7B_jacobian_lens.pt",
            "sha256": "6fcc79011bd921ffd87612255e2e99950a124fa519470ee44ebaf161c39be9d6",
            "source_layers": list(_SELECTED_LAYERS),
            "d_model": 2048,
        },
        "instrumentation": {
            "repo": "https://github.com/anthropics/jacobian-lens.git",
            "commit": "581d398613e5602a5af361e1c34d3a92ea82ba8e",
        },
        "runtime": {
            "python": "fixture",
            "torch": "2.13.0",
            "cuda_runtime": "fixture",
            "gpu_name": "fixture",
            "gpu_total_vram_gib": 16,
            "install_schema": validator.STAGE2B_RUNTIME_INSTALL_SCHEMA,
            "install_spec_sha256": validator.STAGE2B_RUNTIME_INSTALL_SPEC_SHA256,
            "fresh_process_after_install": True,
            "torchvision_state": "absent",
            "packages": {
                "transformers": "5.5.4",
                "huggingface_hub": "1.24.0",
                "numpy": "2.5.1",
                "scipy": "1.18.0",
                "safetensors": "0.8.0",
                "accelerate": "1.14.0",
                "torch": "2.13.0",
            },
        },
        "retention": {
            "raw_activations_persisted": False,
            "full_logits_persisted": False,
            "raw_prompt_persisted": False,
        },
        "disjointness": {
            "checked": True,
            "stage2b_manifest_sha256": _pilot_view()["source_manifest_sha256"],
            "overlap_count": 0,
            "anchor_present": False,
        },
        "stimulus_manifest": {
            "sha256": _pilot_view()["source_manifest_sha256"],
            "n_prompts": 200,
        },
        "authorization": {
            "pilot_authorized": True,
            "pilot_protocol_ratified": True,
            "confirmatory_thresholds_ratified": False,
            "authorization_record_sha256": "a" * 64,
            "authority": "Dr. Mani",
            "authorized_at_utc": "2026-07-30T09:00:00Z",
            "instruction_sha256": "b" * 64,
            "notebook_sha256": "c" * 64,
            "code_bundle_sha256": "d" * 64,
        },
        "preflight": {
            "pinned_identities_matched": True,
            "capacity_ok": True,
            "tensor_contracts_passed": True,
            "crossing_registry_checked": True,
        },
        "partition": {
            "n_prompts": 20,
            "pilot_subset_sha256": _pilot_view()["pilot_subset_sha256"],
            "pilot_view_sha256": _canonical_digest(_pilot_view()),
            "pilot_prompt_ids": [prompt["id"] for prompt in _pilot_view()["prompts"]],
            "pilot_prompt_sha256s": [
                prompt["sha256"] for prompt in _pilot_view()["prompts"]
            ],
            "holdout_prompt_count": 180,
            "holdout_accessed": False,
        },
        "design": {
            "selected_layers": list(_SELECTED_LAYERS),
            "positions": [-2],
            "top_k": 10,
            "vocab_size": 151936,
            "model_n_layers": 28,
            "primary_floor_id": "input_embedding_decoded",
            "sensitivity_floor_id": "layer0_residual_decoded",
            "donor_assignment_count": 8,
            "broken_map_draw_count": 8,
            "unique_readouts_per_prompt_layer": 81,
            "logical_crossings_per_prompt_layer": 64,
            "content_hash_method": "dtype-shape-bytes-sha256-v1",
        },
        "descriptive": {},
    }

    def _errors(
        self,
        artifact,
        tmp_path,
        *,
        expected_pilot_view=_UNSET,
        expected_source=_UNSET,
    ):
        path = tmp_path / "a.json"
        path.write_text(json.dumps(artifact))
        errors: list[str] = []
        if expected_pilot_view is _UNSET:
            expected_pilot_view = _pilot_view()
        if expected_source is _UNSET:
            expected_source = {
                "authorization_record_sha256": self.BASE["authorization"][
                    "authorization_record_sha256"
                ],
                "notebook_sha256": self.BASE["authorization"]["notebook_sha256"],
                "code_bundle_sha256": self.BASE["authorization"]["code_bundle_sha256"],
            }
        validator.validate_stage2b_aggregate(
            artifact,
            path,
            "0" * 64,
            errors,
            expected_pilot_view=expected_pilot_view,
            expected_source=expected_source,
        )
        return errors

    def _relevant(self, artifact, tmp_path, needle):
        return [e for e in self._errors(artifact, tmp_path) if needle in e]

    def test_unchecked_disjointness_is_flagged(self, tmp_path):
        bad = {
            **self.BASE,
            "disjointness": {
                "checked": False,
                "overlap_count": 0,
                "anchor_present": False,
            },
        }
        assert self._relevant(bad, tmp_path, "checked")

    def test_nonzero_overlap_is_flagged(self, tmp_path):
        bad = {
            **self.BASE,
            "disjointness": {
                "checked": True,
                "overlap_count": 3,
                "anchor_present": False,
            },
        }
        assert self._relevant(bad, tmp_path, "overlap_count")

    def test_anchor_inside_the_sample_is_flagged(self, tmp_path):
        bad = {
            **self.BASE,
            "disjointness": {
                "checked": True,
                "overlap_count": 0,
                "anchor_present": True,
            },
        }
        assert self._relevant(bad, tmp_path, "anchor")

    def test_missing_descriptive_block_is_flagged(self, tmp_path):
        bad = {k: v for k, v in self.BASE.items() if k != "descriptive"}
        assert self._relevant(bad, tmp_path, "descriptive")

    def _compact_artifact(self):
        if self.__class__._COMPACT_CACHE is not None:
            return deepcopy(self.__class__._COMPACT_CACHE)
        artifact = json.loads(json.dumps(self.BASE))
        raw_records = [
            _compact_dual_floor_record(prompt_index, layer)
            for prompt_index in range(20)
            for layer in _SELECTED_LAYERS
        ]
        records, denominator = validator.materialize_pilot_nta(raw_records)
        inference = validator.build_pilot_inference(
            records,
            denominator,
            derivation_code_sha256=validator.STAGE2B_STATISTICS_SHA256,
            numpy_version="2.5.1",
        )
        artifact["constants"] = {
            "min_denominator": denominator["derived_value"],
            "guard_quantile": 0.05,
            "guard_quantile_method": "linear",
            "bootstrap_iterations": 20_000,
            "bootstrap_ci_level": 0.99,
            "bootstrap_quantile_method": "linear",
            "bootstrap_bit_generator": "PCG64",
        }
        artifact["denominator_derivation"] = denominator
        artifact["registry"] = {
            "entries": [
                {
                    "name": "NTA_MIN_DENOMINATOR",
                    "declared_value": denominator["derived_value"],
                    "status": "derived",
                }
            ]
        }
        artifact["descriptive"] = {
            "records": records,
            "factorization": {
                "unique_readouts_per_prompt_layer": 81,
                "logical_crossings_per_prompt_layer": 64,
                "donor_assignment_count": 8,
                "broken_map_draw_count": 8,
            },
        }
        artifact["inference"] = inference
        self.__class__._COMPACT_CACHE = artifact
        return deepcopy(artifact)

    @staticmethod
    def _rematerialize(artifact):
        records, denominator = validator.materialize_pilot_nta(
            artifact["descriptive"]["records"]
        )
        artifact["descriptive"]["records"] = records
        artifact["constants"]["min_denominator"] = denominator["derived_value"]
        artifact["denominator_derivation"] = denominator
        artifact["registry"]["entries"][0]["declared_value"] = denominator[
            "derived_value"
        ]
        artifact["registry"]["entries"][0]["status"] = "derived"
        artifact["inference"] = validator.build_pilot_inference(
            records,
            denominator,
            derivation_code_sha256=validator.STAGE2B_STATISTICS_SHA256,
            numpy_version="2.5.1",
        )

    def test_wellformed_compact_dual_floor_record_recomputes(self, tmp_path):
        errors = self._errors(self._compact_artifact(), tmp_path)
        assert errors == []

    @pytest.mark.parametrize(
        "field",
        [
            "authorization",
            "preflight",
            "stimulus_manifest",
            "design",
            "partition",
        ],
    )
    def test_direct_pilot_requires_complete_execution_envelope(self, field, tmp_path):
        artifact = self._compact_artifact()
        del artifact[field]
        assert self._relevant(artifact, tmp_path, field)

    @pytest.mark.parametrize(
        ("section", "field"),
        [
            ("authorization", "pilot_authorized"),
            ("authorization", "pilot_protocol_ratified"),
            ("preflight", "pinned_identities_matched"),
            ("preflight", "capacity_ok"),
            ("preflight", "tensor_contracts_passed"),
            ("preflight", "crossing_registry_checked"),
        ],
    )
    def test_direct_pilot_requires_true_authorization_and_preflight_evidence(
        self, section, field, tmp_path
    ):
        artifact = self._compact_artifact()
        artifact[section][field] = False
        assert self._relevant(artifact, tmp_path, section)

    @pytest.mark.parametrize(
        ("field", "bad_value"),
        [
            ("install_schema", "invented"),
            ("install_spec_sha256", "f" * 64),
            ("fresh_process_after_install", False),
            ("torchvision_state", "present"),
        ],
    )
    def test_runtime_install_contract_is_bound(self, field, bad_value, tmp_path):
        artifact = self._compact_artifact()
        artifact["runtime"][field] = bad_value
        assert self._relevant(artifact, tmp_path, "fresh-process text-only")

    @pytest.mark.parametrize(
        ("field", "needle"),
        [("notebook_sha256", "notebook"), ("code_bundle_sha256", "code-bundle")],
    )
    def test_authorized_source_identities_are_required(self, field, needle, tmp_path):
        artifact = self._compact_artifact()
        artifact["authorization"][field] = "not-a-digest"
        assert self._relevant(artifact, tmp_path, needle)

    def test_trusted_source_identities_must_be_supplied_outside_artifact(
        self, tmp_path
    ):
        artifact = self._compact_artifact()
        errors = self._errors(artifact, tmp_path, expected_source=None)
        assert any("independently" in error for error in errors)

    def test_coordinated_forgery_of_all_retained_source_hashes_is_rejected(
        self, tmp_path
    ):
        artifact = self._compact_artifact()
        artifact["authorization"]["authorization_record_sha256"] = "e" * 64
        artifact["authorization"]["notebook_sha256"] = "f" * 64
        artifact["authorization"]["code_bundle_sha256"] = "0" * 64
        errors = self._errors(artifact, tmp_path)
        assert (
            sum("independently supplied source identity" in error for error in errors)
            == 3
        )

    @pytest.mark.parametrize("field", ["model", "lens", "instrumentation"])
    def test_direct_pilot_requires_pinned_identities(self, field, tmp_path):
        artifact = self._compact_artifact()
        first_key = next(iter(artifact[field]))
        artifact[field][first_key] = "invented"
        assert self._relevant(artifact, tmp_path, field)

    @pytest.mark.parametrize(
        "source_layers",
        [
            [],
            [6, 13, 20],
            [6, 13, 20, 26, 26],
            [6, 13, 20, "26"],
            [6, 13, 20, True],
        ],
    )
    def test_lens_source_layers_cover_selected_layers_exactly_once(
        self, source_layers, tmp_path
    ):
        artifact = self._compact_artifact()
        artifact["lens"]["source_layers"] = source_layers
        assert self._relevant(artifact, tmp_path, "lens.source_layers")

    def test_stage2b_schema_is_exact(self, tmp_path):
        artifact = self._compact_artifact()
        artifact["schema"] = "jspace-observation-stage2b/v2"
        assert self._relevant(artifact, tmp_path, "schema")

    def test_current_measurement_contract_rejects_confirmatory_mode(self, tmp_path):
        artifact = self._compact_artifact()
        artifact["run_mode"] = "confirmatory"
        assert self._relevant(artifact, tmp_path, "pilot-only")

    def test_disjointness_manifest_identity_is_bound(self, tmp_path):
        artifact = self._compact_artifact()
        artifact["disjointness"]["stage2b_manifest_sha256"] = "f" * 64
        assert self._relevant(artifact, tmp_path, "manifest identity")

    @pytest.mark.parametrize("field", ["layer", "category"])
    def test_compact_records_require_locus_identity(self, field, tmp_path):
        artifact = self._compact_artifact()
        del artifact["descriptive"]["records"][0][field]
        assert self._relevant(artifact, tmp_path, "compact records require fields")

    def test_compact_layer_must_be_selected(self, tmp_path):
        artifact = self._compact_artifact()
        artifact["descriptive"]["records"][0]["layer"] = 5
        assert self._relevant(artifact, tmp_path, "unselected layer")

    def test_compact_category_is_bound_to_expected_view(self, tmp_path):
        artifact = self._compact_artifact()
        artifact["descriptive"]["records"][0]["category"] = "invented"
        assert self._relevant(artifact, tmp_path, "category")

    def test_compact_locus_coverage_is_exact(self, tmp_path):
        artifact = self._compact_artifact()
        artifact["descriptive"]["records"].pop()
        assert self._relevant(artifact, tmp_path, "coverage")

    def test_donor_source_must_belong_to_expected_view(self, tmp_path):
        artifact = self._compact_artifact()
        assignment = artifact["descriptive"]["records"][0]["donor_assignments"][0]
        assignment["source_prompt_sha256"] = "f" * 64
        recipient = assignment["recipient_prompt_sha256"]
        assignment["recipient_to_donor_sha256"] = hashlib.sha256(
            f"{recipient}->{'f' * 64}".encode()
        ).hexdigest()
        assert self._relevant(artifact, tmp_path, "outside the expected pilot view")

    def test_donor_seed_registry_is_consistent_across_loci(self, tmp_path):
        artifact = self._compact_artifact()
        artifact["descriptive"]["records"][1]["donor_assignments"][0]["seed"] = 999
        assert self._relevant(artifact, tmp_path, "ratified derivation")

    def test_donor_source_is_consistent_across_layers_for_one_recipient(self, tmp_path):
        artifact = self._compact_artifact()
        records = artifact["descriptive"]["records"]
        first = records[0]
        same_recipient = next(
            record
            for record in records[1:]
            if record["prompt_sha256"] == first["prompt_sha256"]
        )
        assignment = same_recipient["donor_assignments"][0]
        original_source = assignment["source_prompt_sha256"]
        alternate_source = next(
            prompt["sha256"]
            for prompt in _pilot_view()["prompts"]
            if prompt["sha256"]
            not in {same_recipient["prompt_sha256"], original_source}
        )
        assignment["source_prompt_sha256"] = alternate_source
        assignment["recipient_to_donor_sha256"] = hashlib.sha256(
            f"{same_recipient['prompt_sha256']}->{alternate_source}".encode()
        ).hexdigest()
        assignment["residual_sha256"] = "f" * 64
        assert self._relevant(artifact, tmp_path, "source disagrees across layers")

    def test_map_seed_registry_is_consistent_across_loci(self, tmp_path):
        artifact = self._compact_artifact()
        artifact["descriptive"]["records"][1]["map_draws"][0]["seed"] = 999
        assert self._relevant(artifact, tmp_path, "ratified derivation")

    def test_map_hash_is_consistent_across_prompts_at_one_layer(self, tmp_path):
        artifact = self._compact_artifact()
        same_layer_record = artifact["descriptive"]["records"][4]
        assert (
            same_layer_record["layer"] == artifact["descriptive"]["records"][0]["layer"]
        )
        same_layer_record["map_draws"][0]["sha256"] = "f" * 64
        assert self._relevant(artifact, tmp_path, "hash disagrees across prompts")

    def test_coordinated_valid_pilot_donor_rewrite_is_rejected(self, tmp_path):
        artifact = self._compact_artifact()
        records = artifact["descriptive"]["records"]
        recipient = records[0]["prompt_sha256"]
        affected = [
            record for record in records if record["prompt_sha256"] == recipient
        ]
        original = affected[0]["donor_assignments"][0]["source_prompt_sha256"]
        alternate = next(
            prompt["sha256"]
            for prompt in _pilot_view()["prompts"]
            if prompt["sha256"] not in {recipient, original}
        )
        for record in affected:
            assignment = record["donor_assignments"][0]
            assignment["source_prompt_sha256"] = alternate
            assignment["recipient_to_donor_sha256"] = hashlib.sha256(
                f"{recipient}->{alternate}".encode()
            ).hexdigest()
            assignment["residual_sha256"] = hashlib.sha256(
                f"coordinated:{recipient}:{record['layer']}:{alternate}".encode()
            ).hexdigest()
        assert self._relevant(artifact, tmp_path, "recipient-and-seed selection")

    @pytest.mark.parametrize(
        ("field", "bad_value"),
        [
            ("verified", False),
            ("singular_value_count", 2047),
            ("rtol", 0.5),
            ("atol", 0.5),
            ("max_normalized_error", 1.0001),
            ("fitted_singular_values_sha256", "not-a-digest"),
        ],
    )
    def test_each_realized_map_requires_valid_spectrum_evidence(
        self, field, bad_value, tmp_path
    ):
        artifact = self._compact_artifact()
        artifact["descriptive"]["records"][0]["map_draws"][0]["spectrum_check"][
            field
        ] = bad_value
        assert self._relevant(artifact, tmp_path, "spectrum")

    def test_missing_realized_map_spectrum_evidence_is_rejected(self, tmp_path):
        artifact = self._compact_artifact()
        del artifact["descriptive"]["records"][0]["map_draws"][0]["spectrum_check"]
        assert self._relevant(artifact, tmp_path, "spectrum")

    @pytest.mark.parametrize(
        "descriptive",
        [
            {},
            {"factorization": {}},
            {"records": []},
            {"records": [{"legacy_summary": 1}]},
        ],
    )
    def test_aggregate_requires_nonempty_compact_records(self, descriptive, tmp_path):
        artifact = self._compact_artifact()
        artifact["descriptive"] = descriptive
        assert self._relevant(artifact, tmp_path, "compact records")

    @pytest.mark.parametrize(
        ("field", "bad_value"),
        [
            ("unique_readouts_per_prompt_layer", 80),
            ("logical_crossings_per_prompt_layer", 63),
            ("donor_assignment_count", 7),
            ("broken_map_draw_count", 7),
        ],
    )
    def test_aggregate_requires_exact_factorization_contract(
        self, field, bad_value, tmp_path
    ):
        artifact = self._compact_artifact()
        artifact["descriptive"]["factorization"][field] = bad_value
        assert self._relevant(artifact, tmp_path, "factorization")

    def test_compact_target_source_is_exact(self, tmp_path):
        artifact = self._compact_artifact()
        artifact["descriptive"]["records"][0]["target_source"] = "ground_truth"
        assert self._relevant(artifact, tmp_path, "target_source")

    def test_compact_target_id_is_cryptographically_bound(self, tmp_path):
        artifact = self._compact_artifact()
        artifact["descriptive"]["records"][0]["target_id"] = 8
        assert self._relevant(artifact, tmp_path, "target decision")

    def test_compact_output_logits_identity_is_cryptographically_bound(self, tmp_path):
        artifact = self._compact_artifact()
        artifact["descriptive"]["records"][0]["target_derivation"][
            "output_logits_sha256"
        ] = "f" * 64
        assert self._relevant(artifact, tmp_path, "target decision")

    def test_compact_argmax_tie_evidence_is_required(self, tmp_path):
        artifact = self._compact_artifact()
        del artifact["descriptive"]["records"][0]["target_derivation"][
            "argmax_tie_token_ids"
        ]
        assert self._relevant(artifact, tmp_path, "target_derivation")

    def test_compact_target_must_follow_recorded_tie_break(self, tmp_path):
        artifact = self._compact_artifact()
        record = artifact["descriptive"]["records"][0]
        derivation = record["target_derivation"]
        derivation["argmax_tie_token_ids"] = [7, 8]
        record["target_id"] = 8
        derivation["target_decision_sha256"] = _target_decision_digest(8, derivation)
        assert self._relevant(artifact, tmp_path, "tie-break")

    def test_runtime_verifier_rejects_self_consistent_target_forgery(self):
        np = pytest.importorskip("numpy")
        logits = np.asarray([0.25, 1.5, -0.5], dtype=np.float32)
        metadata = f"{logits.dtype}:{logits.shape}:".encode("ascii")
        derivation = {
            "method": "model_argmax",
            "output_logits_sha256": hashlib.sha256(
                metadata + logits.tobytes()
            ).hexdigest(),
            "output_logits_dtype": "float32",
            "output_logits_shape": [3],
            "max_logit": 1.5,
            "argmax_tie_token_ids": [1],
            "tie_break_rule": "lowest_token_id",
            "runtime_verifier_id": validator.STAGE2B_TARGET_RUNTIME_VERIFIER,
            "runtime_verified": True,
        }
        derivation["target_decision_sha256"] = _target_decision_digest(1, derivation)
        assert (
            validator.verify_target_derivation_against_logits(logits, 1, derivation)
            == []
        )

        forged = {**derivation, "argmax_tie_token_ids": [0]}
        forged["target_decision_sha256"] = _target_decision_digest(0, forged)
        errors = validator.verify_target_derivation_against_logits(logits, 0, forged)
        assert any("runtime target_id" in error for error in errors)
        assert any("runtime argmax tie set" in error for error in errors)

    def test_target_derivation_is_stable_across_layers(self, tmp_path):
        artifact = self._compact_artifact()
        record = artifact["descriptive"]["records"][1]
        derivation = record["target_derivation"]
        derivation["output_logits_sha256"] = "f" * 64
        derivation["target_decision_sha256"] = _target_decision_digest(
            record["target_id"], derivation
        )
        assert self._relevant(artifact, tmp_path, "disagrees across layers")

    def test_unknown_compact_record_field_is_rejected(self, tmp_path):
        artifact = self._compact_artifact()
        artifact["descriptive"]["records"][0]["invented_extra_field"] = True
        assert self._relevant(artifact, tmp_path, "unknown compact fields")

    def test_compact_floor_identities_are_exact(self, tmp_path):
        artifact = self._compact_artifact()
        scores = artifact["descriptive"]["records"][0]["floor_scores"]
        scores["invented_floor"] = scores.pop("layer0_residual_decoded")
        assert self._relevant(artifact, tmp_path, "floor_scores")

    def test_compact_records_require_explicitly_derived_denominator(self, tmp_path):
        artifact = self._compact_artifact()
        artifact["registry"]["entries"][0]["status"] = "unratified"
        assert self._relevant(artifact, tmp_path, "derived min_denominator")

    def test_recorded_denominator_must_match_derived_registry_value(self, tmp_path):
        artifact = self._compact_artifact()
        artifact["registry"]["entries"][0]["declared_value"] = 0.5
        assert self._relevant(artifact, tmp_path, "derived min_denominator")

    def _pilot_artifact(self):
        return self._compact_artifact()

    def test_invalid_expected_pilot_view_is_rejected_in_pilot_mode(self, tmp_path):
        errors = self._errors(self._pilot_artifact(), tmp_path, expected_pilot_view={})
        assert any("expected pilot view" in error for error in errors)

    def test_balanced_but_unpinned_pilot_view_is_rejected(self, tmp_path):
        alternate = _pilot_view()
        alternate["prompts"][0]["text"] = "different prompt"
        errors = self._errors(
            self._pilot_artifact(), tmp_path, expected_pilot_view=alternate
        )
        assert any("pinned Stage 2b view" in error for error in errors)

    def test_mismatched_expected_pilot_view_is_rejected_in_pilot_mode(self, tmp_path):
        artifact = self._pilot_artifact()
        artifact["partition"]["pilot_prompt_ids"] = ["other-id"]
        errors = self._errors(artifact, tmp_path, expected_pilot_view=_pilot_view())
        assert any("pilot partition" in error for error in errors)

    def test_matching_expected_pilot_view_is_accepted_in_pilot_mode(self, tmp_path):
        errors = self._errors(
            self._pilot_artifact(), tmp_path, expected_pilot_view=_pilot_view()
        )
        assert errors == []

    def test_duplicate_compact_donor_assignment_id_is_rejected(self, tmp_path):
        artifact = self._compact_artifact()
        artifact["descriptive"]["records"][0]["donor_assignments"][1][
            "donor_assignment_id"
        ] = "donor-0"
        assert self._relevant(artifact, tmp_path, "donor assignment IDs")

    def test_duplicate_compact_map_draw_id_is_rejected(self, tmp_path):
        artifact = self._compact_artifact()
        artifact["descriptive"]["records"][0]["map_draws"][1]["map_draw_id"] = "map-0"
        assert self._relevant(artifact, tmp_path, "map draw IDs")

    def test_duplicate_compact_donor_seed_is_rejected(self, tmp_path):
        artifact = self._compact_artifact()
        assignments = artifact["descriptive"]["records"][0]["donor_assignments"]
        assignments[1]["seed"] = assignments[0]["seed"]
        assert self._relevant(artifact, tmp_path, "donor seeds")

    def test_duplicate_compact_map_seed_is_rejected(self, tmp_path):
        artifact = self._compact_artifact()
        draws = artifact["descriptive"]["records"][0]["map_draws"]
        draws[1]["seed"] = draws[0]["seed"]
        assert self._relevant(artifact, tmp_path, "map seeds")

    def test_compact_donor_recipient_must_match_record(self, tmp_path):
        artifact = self._compact_artifact()
        assignment = artifact["descriptive"]["records"][0]["donor_assignments"][0]
        assignment["recipient_prompt_sha256"] = "f" * 64
        assert self._relevant(artifact, tmp_path, "recipient prompt hash")

    def test_compact_recipient_to_donor_hash_is_recomputed(self, tmp_path):
        artifact = self._compact_artifact()
        assignment = artifact["descriptive"]["records"][0]["donor_assignments"][0]
        assignment["recipient_to_donor_sha256"] = "f" * 64
        assert self._relevant(artifact, tmp_path, "recipient-to-donor hash")

    @pytest.mark.parametrize(
        ("field", "bad_value", "needle"),
        [
            (
                "source_prompt_sha256",
                "not-a-digest",
                "invalid/self recipient-to-donor digest",
            ),
            ("residual_sha256", "not-a-digest", "residual hash"),
            ("seed", True, "invalid seed"),
        ],
    )
    def test_compact_donor_provenance_is_validated(
        self, field, bad_value, needle, tmp_path
    ):
        artifact = self._compact_artifact()
        artifact["descriptive"]["records"][0]["donor_assignments"][0][field] = bad_value
        assert self._relevant(artifact, tmp_path, needle)

    @pytest.mark.parametrize(
        ("field", "bad_value", "needle"),
        [
            ("map_draw_id", "", "map_draw_id"),
            ("seed", True, "invalid seed"),
            ("sha256", "not-a-digest", "map hash"),
        ],
    )
    def test_compact_map_provenance_is_validated(
        self, field, bad_value, needle, tmp_path
    ):
        artifact = self._compact_artifact()
        artifact["descriptive"]["records"][0]["map_draws"][0][field] = bad_value
        assert self._relevant(artifact, tmp_path, needle)

    def test_compact_factorized_scores_reject_incomplete_crossing(self, tmp_path):
        artifact = self._compact_artifact()
        del artifact["descriptive"]["records"][0]["factorized_scores"][
            "wrong_act_broken_map"
        ]["donor-0"]["map-0"]
        assert self._relevant(artifact, tmp_path, "cannot materialize")

    def test_compact_factorized_scores_reject_extra_component(self, tmp_path):
        artifact = self._compact_artifact()
        artifact["descriptive"]["records"][0]["factorized_scores"]["invented"] = 0.0
        assert self._relevant(artifact, tmp_path, "missing, extra, or mislabeled")

    def test_compact_factor_labels_must_match_provenance(self, tmp_path):
        artifact = self._compact_artifact()
        record = artifact["descriptive"]["records"][0]
        record["donor_assignments"][0]["donor_assignment_id"] = "donor-other"
        assert self._relevant(artifact, tmp_path, "donor labels disagree")

    def test_compact_primary_floor_corruption_is_rejected(self, tmp_path):
        artifact = self._compact_artifact()
        artifact["descriptive"]["records"][0]["factorized_nta"][
            "input_embedding_decoded"
        ]["wrong_act_broken_map"]["donor-0"]["map-0"] = 999.0
        assert self._relevant(artifact, tmp_path, "disagrees with recomputed value")

    def test_compact_sensitivity_floor_corruption_is_rejected(self, tmp_path):
        artifact = self._compact_artifact()
        artifact["descriptive"]["records"][0]["factorized_nta"][
            "layer0_residual_decoded"
        ]["correct_act_broken_map"]["map-0"] = 999.0
        assert self._relevant(artifact, tmp_path, "disagrees with recomputed value")

    def test_compact_sensitivity_minus_primary_is_recomputed(self, tmp_path):
        artifact = self._compact_artifact()
        artifact["descriptive"]["records"][0]["factorized_nta"][
            "sensitivity_minus_primary"
        ]["correct_act_fitted_map"] = 999.0
        assert self._relevant(artifact, tmp_path, "disagrees with recomputed value")

    @pytest.mark.parametrize(
        ("path", "bad_value"),
        [
            (("denominator_derivation", "source_denominators_sha256"), "f" * 64),
            (
                (
                    "descriptive",
                    "records",
                    0,
                    "floor_status",
                    "input_embedding_decoded",
                    "eligible",
                ),
                True,
            ),
            (("inference", "coverage", 0, "eligible_prompt_count"), 0),
            (
                (
                    "inference",
                    "prompt_layer_effects",
                    0,
                    "correct_effect_mean",
                ),
                999.0,
            ),
            (("inference", "layer_estimates", 0, "lower"), 999.0),
            (("inference", "rng", "namespace"), "invented-bootstrap"),
            (
                (
                    "inference",
                    "threshold_derivation",
                    "SPEC_MIN_EFFECT",
                    0,
                ),
                999.0,
            ),
            (("inference", "pilot_measurement_sha256"), "f" * 64),
        ],
    )
    def test_pilot_statistical_packet_is_recomputed(self, path, bad_value, tmp_path):
        artifact = self._compact_artifact()
        target = artifact
        for component in path[:-1]:
            target = target[component]
        target[path[-1]] = bad_value
        errors = self._errors(artifact, tmp_path)
        assert any(
            "denominator_derivation" in error
            or "descriptive.records" in error
            or "floor_status" in error
            or "inference" in error
            for error in errors
        )

    def test_primary_floor_exclusion_is_a_valid_complete_tree(self, tmp_path):
        artifact = self._compact_artifact()
        for record in artifact["descriptive"]["records"]:
            record["floor_scores"]["input_embedding_decoded"] = -0.2
        self._rematerialize(artifact)
        errors = self._errors(artifact, tmp_path)
        assert errors == []
        first = artifact["descriptive"]["records"][0]["factorized_nta"]
        assert first["input_embedding_decoded"]["correct_act_fitted_map"] is None
        assert first["layer0_residual_decoded"]["correct_act_fitted_map"] is not None
        assert first["sensitivity_minus_primary"]["correct_act_fitted_map"] is None

    def test_both_floor_exclusions_are_valid_complete_trees(self, tmp_path):
        artifact = self._compact_artifact()
        for record in artifact["descriptive"]["records"]:
            record["floor_scores"]["input_embedding_decoded"] = -0.2
            record["floor_scores"]["layer0_residual_decoded"] = -0.1
        self._rematerialize(artifact)
        assert self._errors(artifact, tmp_path) == []

    def test_compact_nta_rejects_missing_or_mislabeled_component(self, tmp_path):
        artifact = self._compact_artifact()
        nta = artifact["descriptive"]["records"][0]["factorized_nta"]
        nta["invented_floor"] = nta.pop("layer0_residual_decoded")
        assert self._relevant(artifact, tmp_path, "missing, extra, or mislabeled")

    @pytest.mark.parametrize("field", ["threshold_estimates", "gates", "decision"])
    def test_current_measurement_schema_rejects_unratified_fields(
        self, field, tmp_path
    ):
        artifact = self._compact_artifact()
        artifact[field] = {"invented": True}
        assert self._relevant(artifact, tmp_path, f"unratified field {field!r}")

    @pytest.mark.parametrize(
        ("path", "field"),
        [
            ((), "thresholds"),
            ((), "scientific_decision"),
            (("descriptive",), "inference"),
            (("descriptive",), "limitations"),
            (("authorization",), "decision"),
            (("runtime",), "threshold_policy"),
            (("descriptive", "factorization"), "multiplicity"),
            (("descriptive", "records", 0, "target_derivation"), "confidence"),
            (("descriptive", "records", 0, "donor_assignments", 0), "policy"),
            (("descriptive", "records", 0, "map_draws", 0), "gate"),
            (("inference",), "decision"),
            (("inference", "rng"), "seed_policy"),
            (("inference", "coverage", 0), "imputation"),
            (("inference", "prompt_layer_effects", 0), "gate"),
            (("inference", "layer_estimates", 0), "multiplicity"),
            (("inference", "threshold_derivation"), "scientific_decision"),
        ],
    )
    def test_stage2b_schema_rejects_unknown_fields_recursively(
        self, path, field, tmp_path
    ):
        artifact = self._compact_artifact()
        target = artifact
        for component in path:
            target = target[component]
        target[field] = {"invented": True}
        assert self._relevant(artifact, tmp_path, "unknown fields")

    def test_a_wellformed_descriptive_aggregate_has_no_schema_errors(self, tmp_path):
        errors = self._errors(self._compact_artifact(), tmp_path)
        assert errors == []


def test_stage2b_schema_is_dispatched_separately(tmp_path):
    """A Stage 2b artifact must not be validated as a Stage 2 one."""
    artifact = dict(TestStage2bAggregate.BASE)
    path = tmp_path / "agg.json"
    path.write_text(json.dumps(artifact))
    summary, _ = validator.validate(path, None)
    assert summary.get("detected_contract") == "stage2b_aggregate"
