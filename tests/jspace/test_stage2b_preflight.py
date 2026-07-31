"""Preflight tests: every check must be proven to FAIL, not only to pass.

Per constitution Principle III, a preflight suite that only demonstrates valid
configurations pass has not tested the preflight.  Each test below constructs a
configuration built to trip one specific failure code, and asserts on ``code``
rather than on message text so the messages stay free to change.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
from typing import ClassVar

import pytest

_MODULE_PATH = (
    pathlib.Path(__file__).resolve().parents[2]
    / "EvoScientist/skills/jspace-research-operations/scripts/stage2b_preflight.py"
)
_spec = importlib.util.spec_from_file_location("stage2b_preflight", _MODULE_PATH)
assert _spec is not None
assert _spec.loader is not None
preflight = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(preflight)


@pytest.mark.parametrize("module_name", ["stage2b_preflight", "stage2b_endpoint"])
def test_module_imports_without_torch_jlens_or_scipy(module_name):
    """The binding constraint from plan.md's Structure Decision.

    If this ever fails, the modules become unusable on any machine without a GPU
    stack -- the exact condition that made Stage 2's equivalent logic unreachable
    by any test.

    Checked in a *subprocess*, because asserting on this process's ``sys.modules``
    would only measure whether some earlier test happened to import scipy. That
    tests the test run, not the module.
    """
    import subprocess
    import sys

    source = (
        "import importlib.util as u, sys, json;"
        f"s=u.spec_from_file_location('m', {str(_MODULE_PATH.parent / (module_name + '.py'))!r});"
        "m=u.module_from_spec(s); sys.modules['m']=m; s.loader.exec_module(m);"
        "print(json.dumps([n for n in ('torch','jlens','scipy','numpy')"
        " if n in sys.modules]))"
    )
    result = subprocess.run(
        [sys.executable, "-c", source],
        capture_output=True,
        text=True,
        check=True,
        cwd=_MODULE_PATH.parent,
    )
    leaked = json.loads(result.stdout)
    assert leaked == [], f"{module_name} imports {leaked} at module scope"


class TestConstantRegistry:
    """The three checks of the declared-means-consumed contract."""

    def test_shipped_registry_passes_its_own_checks(self):
        """The regression test for the review that caught this.

        An earlier draft of the registry named ``preflight:denominator_guard``
        (a check that does not exist) and the wildcard ``every nta_*``.  Shipping
        it would have raised ``phantom_consumer`` on the project's own table --
        the check added to close one gap firing on the very registry it shipped
        with.
        """
        preflight.check_constant_registry(preflight.INITIAL_REGISTRY, preflight.GATES)

    def test_orphaned_constant_is_rejected(self):
        """Direct regression test for the 2026-07-26 audit finding.

        Stage 2 declared ``INFERENCE_SEEDS = [0, 1]`` "for seed-invariance" and
        ran only seed 0.  The artifact faithfully recorded the declaration, so
        the record testified the constant was used.
        """
        registry = {
            "INFERENCE_SEEDS": {
                "kind": "constant",
                "declared_value": [0, 1],
                "status": "implemented",
                "consumed_by": [],
            }
        }
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_constant_registry(registry, preflight.GATES)
        assert exc.value.code == "orphaned_constant"
        assert exc.value.detail["constant"] == "INFERENCE_SEEDS"

    def test_missing_consumed_by_key_is_also_orphaned(self):
        registry = {
            "SOME_CONSTANT": {
                "kind": "constant",
                "declared_value": 1,
                "status": "implemented",
            }
        }
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_constant_registry(registry, preflight.GATES)
        assert exc.value.code == "orphaned_constant"

    def test_unregistered_constant_read_by_a_gate_is_rejected(self):
        """A gate reading a threshold nobody preregistered."""
        gates = {"h1_specificity": {"constant_name": "UNDECLARED_MARGIN"}}
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_constant_registry({}, gates)
        assert exc.value.code == "unregistered_constant"
        assert exc.value.detail["constant"] == "UNDECLARED_MARGIN"

    def test_unregistered_constant_read_by_a_preflight_check_is_rejected(self):
        """The reverse check must not stop at gates.

        Most registered constants here are read by preflight, not by a gate, so
        a gates-only sweep would leave the larger surface unguarded.
        """
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_constant_registry(
                preflight.INITIAL_REGISTRY,
                preflight.GATES,
                consumer_reads={"preflight:environment": ["UNDECLARED_VRAM_FLOOR"]},
            )
        assert exc.value.code == "unregistered_constant"
        assert exc.value.detail["consumer"] == "preflight:environment"

    def test_unregistered_constant_read_by_an_endpoint_fn_is_rejected(self):
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_constant_registry(
                preflight.INITIAL_REGISTRY,
                preflight.GATES,
                consumer_reads={"endpoint:nta": ["UNDECLARED_FLOOR"]},
            )
        assert exc.value.code == "unregistered_constant"

    def test_declared_reads_that_are_all_registered_pass(self):
        preflight.check_constant_registry(
            preflight.INITIAL_REGISTRY,
            preflight.GATES,
            consumer_reads={
                "preflight:environment": ["MIN_VRAM_GIB", "JLENS_COMMIT", "LENS_FILE"],
                "endpoint:nta": ["NTA_MIN_DENOMINATOR"],
            },
        )

    def test_phantom_gate_consumer_is_rejected(self):
        registry = {
            "X": {
                "kind": "constant",
                "declared_value": 1,
                "status": "implemented",
                "consumed_by": ["h3_nonexistent"],
            }
        }
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_constant_registry(registry, preflight.GATES)
        assert exc.value.code == "phantom_consumer"

    def test_phantom_preflight_consumer_is_rejected(self):
        registry = {
            "X": {
                "kind": "constant",
                "declared_value": 1,
                "status": "implemented",
                "consumed_by": ["preflight:denominator_guard"],
            }
        }
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_constant_registry(registry, preflight.GATES)
        assert exc.value.code == "phantom_consumer"
        assert exc.value.detail["consumer"] == "preflight:denominator_guard"

    def test_phantom_endpoint_consumer_is_rejected(self):
        registry = {
            "X": {
                "kind": "constant",
                "declared_value": 1,
                "status": "implemented",
                "consumed_by": ["endpoint:no_such_function"],
            }
        }
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_constant_registry(registry, preflight.GATES)
        assert exc.value.code == "phantom_consumer"

    def test_unknown_namespace_is_rejected(self):
        registry = {
            "X": {
                "kind": "constant",
                "declared_value": 1,
                "status": "implemented",
                "consumed_by": ["notebook:cell_16"],
            }
        }
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_constant_registry(registry, preflight.GATES)
        assert exc.value.code == "phantom_consumer"

    def test_matching_is_exact_not_fuzzy(self):
        """A display name must not resolve to its canonical ID.

        A check that accepts "H1 specificity" for "h1_specificity" cannot tell a
        real linkage from a typo, which is the whole thing it is for.
        """
        registry = {
            "X": {
                "kind": "constant",
                "declared_value": 1,
                "status": "implemented",
                "consumed_by": ["H1 specificity"],
            }
        }
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_constant_registry(registry, preflight.GATES)
        assert exc.value.code == "phantom_consumer"

    @pytest.mark.parametrize("status", [None, "approved", ""])
    def test_missing_or_unknown_registry_status_is_rejected(self, status):
        registry = {
            "X": {
                "kind": "constant",
                "declared_value": 1,
                "status": status,
                "consumed_by": ["preflight:ratification"],
            }
        }
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_constant_registry(registry, preflight.GATES)
        assert exc.value.code == "invalid_registry_status"

    @pytest.mark.parametrize(
        ("kind", "value", "status"),
        [
            ("derived_field", None, "ratified"),
            ("constant", 1, "derived"),
            ("constant", 1, "unratified"),
            ("constant", None, "ratified"),
        ],
    )
    def test_inconsistent_registry_status_is_rejected(self, kind, value, status):
        registry = {
            "X": {
                "kind": kind,
                "declared_value": value,
                "status": status,
                "consumed_by": ["preflight:ratification"],
            }
        }
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_constant_registry(registry, preflight.GATES)
        assert exc.value.code == "inconsistent_registry_status"


class TestRegistryCompleteness:
    """Properties of the shipped registry itself, not of the checker."""

    def test_deferred_constants_are_exactly_the_unratified_rules(self):
        """Only explicitly unratified threshold, inference, and crossing inputs are unset.

        A ``None`` anywhere else is a forgotten value masquerading as a
        deliberate deferral.
        """
        unset = {
            name
            for name, entry in preflight.INITIAL_REGISTRY.items()
            if entry["kind"] == "constant" and entry["declared_value"] is None
        }
        assert unset == set()

    def test_registry_statuses_distinguish_ratification_from_implementation(self):
        ratified = {
            "TARGET_SOURCE",
            "PROMPT_ONLY_CONSTRUCTION",
            "PRIMARY_FLOOR_ID",
            "SENSITIVITY_FLOOR_ID",
            "WRONG_ACTIVATION_ASSIGNMENT_COUNT",
            "BROKEN_MAP_DRAW_COUNT",
            "UNIQUE_READOUT_COUNT",
            "LOGICAL_COMBINATION_COUNT",
            "BOOTSTRAP_CI_LEVEL",
            "UNCERTAINTY_METHOD",
            "RESAMPLING_UNIT",
            "INTERVAL_METHOD",
            "BOOTSTRAP_ITERATIONS",
            "BOOTSTRAP_SEED",
            "AGGREGATION_RULE",
            "THRESHOLD_DERIVATION_RULES",
            "MULTIPLICITY_RULE",
            "NTA_GUARD_QUANTILE",
            "NTA_GUARD_QUANTILE_METHOD",
            "PILOT_MIN_LAYER_PROMPTS",
            "PILOT_MIN_CATEGORY_PROMPTS",
            "BROKEN_MAP_DRAWS",
            "WRONG_ACTIVATION_ASSIGNMENTS",
        }
        unratified = {
            "PILOT_AUTHORIZED",
            "PILOT_PROTOCOL_RATIFIED",
            "THRESHOLDS_RATIFIED",
        }
        assert {preflight.INITIAL_REGISTRY[name]["status"] for name in ratified} == {
            "ratified"
        }
        assert {preflight.INITIAL_REGISTRY[name]["status"] for name in unratified} == {
            "unratified"
        }
        assert {
            entry["status"]
            for entry in preflight.INITIAL_REGISTRY.values()
            if entry["kind"] == "derived_field"
        } == {"derived"}
        assert preflight.INITIAL_REGISTRY["JLENS_COMMIT"]["status"] == "implemented"
        assert {
            preflight.INITIAL_REGISTRY[name]["status"]
            for name in ("BROKEN_MAP_SPECTRUM_RTOL", "BROKEN_MAP_SPECTRUM_ATOL")
        } == {"implemented"}

    def test_spectrum_tolerances_are_declared_and_consumed(self):
        assert preflight.INITIAL_REGISTRY["BROKEN_MAP_SPECTRUM_RTOL"] == {
            "kind": "constant",
            "declared_value": 1e-5,
            "consumed_by": ["endpoint:singular_spectrum_evidence"],
            "status": "implemented",
        }
        assert preflight.INITIAL_REGISTRY["BROKEN_MAP_SPECTRUM_ATOL"] == {
            "kind": "constant",
            "declared_value": 1e-6,
            "consumed_by": ["endpoint:singular_spectrum_evidence"],
            "status": "implemented",
        }
        assert "singular_spectrum_evidence" in preflight.ENDPOINT_FNS

    def test_crossing_uses_ratified_sha_derived_vectors(self):
        assert "BROKEN_MAP_SEED" not in preflight.INITIAL_REGISTRY
        assert "WRONG_ACTIVATION_SEED" not in preflight.INITIAL_REGISTRY
        donors, maps = _crossing_vectors()
        assert preflight.INITIAL_REGISTRY["BROKEN_MAP_DRAWS"]["declared_value"] == maps
        assert (
            preflight.INITIAL_REGISTRY["WRONG_ACTIVATION_ASSIGNMENTS"]["declared_value"]
            == donors
        )

    def test_ratified_measurement_structure_is_registered_separately(self):
        expected = {
            "TARGET_SOURCE": "model_argmax",
            "PRIMARY_FLOOR_ID": "input_embedding_decoded",
            "SENSITIVITY_FLOOR_ID": "layer0_residual_decoded",
            "WRONG_ACTIVATION_ASSIGNMENT_COUNT": 8,
            "BROKEN_MAP_DRAW_COUNT": 8,
            "UNIQUE_READOUT_COUNT": 81,
            "LOGICAL_COMBINATION_COUNT": 64,
        }
        assert {
            name: preflight.INITIAL_REGISTRY[name]["declared_value"]
            for name in expected
        } == expected
        assert "dual_floor_nta" in preflight.ENDPOINT_FNS
        assert "materialize_crossed_factorials" in preflight.ENDPOINT_FNS

    def test_no_scientific_gates_are_declared_before_rules_are_ratified(self):
        assert preflight.GATES == ()
        assert preflight.GATE_READS == {}

    def test_removed_inference_helpers_are_not_advertised_as_endpoints(self):
        for name in (
            "allocate_wrong_layers",
            "cluster_bootstrap_median",
            "compose_decision",
            "gate_record",
            "jaccard_top_k",
            "paired_difference_by_cluster",
        ):
            assert name not in preflight.ENDPOINT_FNS

    def test_registry_covers_both_kinds(self):
        kinds = {entry["kind"] for entry in preflight.INITIAL_REGISTRY.values()}
        assert kinds == {"constant", "derived_field"}


class TestCrossingRegistry:
    @staticmethod
    def _entries(prefix):
        donors, maps = _crossing_vectors()
        return donors if prefix == "donor" else maps

    def test_exact_unique_eight_by_eight_registry_passes(self):
        preflight.check_crossing_registry(self._entries("donor"), self._entries("map"))

    @pytest.mark.parametrize("kind", ["donor", "map"])
    def test_missing_entry_refuses(self, kind):
        donors, maps = self._entries("donor"), self._entries("map")
        (donors if kind == "donor" else maps).pop()
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_crossing_registry(donors, maps)
        assert exc.value.code == "crossing_registry_size"

    def test_duplicate_identity_refuses(self):
        donors, maps = self._entries("donor"), self._entries("map")
        maps[-1]["id"] = maps[0]["id"]
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_crossing_registry(donors, maps)
        assert exc.value.code == "crossing_registry_duplicate"

    @pytest.mark.parametrize(
        ("field", "value", "code"),
        [
            ("id", "", "crossing_registry_identity"),
            ("id", 7, "crossing_registry_identity"),
            ("seed", True, "crossing_registry_seed"),
            ("seed", "7", "crossing_registry_seed"),
        ],
    )
    def test_malformed_vector_entry_refuses(self, field, value, code):
        donors, maps = self._entries("donor"), self._entries("map")
        donors[0][field] = value
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_crossing_registry(donors, maps)
        assert exc.value.code == code

    def test_well_formed_but_noncanonical_seed_refuses(self):
        donors, maps = self._entries("donor"), self._entries("map")
        donors[0]["seed"] += 1
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_crossing_registry(donors, maps)
        assert exc.value.code == "crossing_registry_derivation"


class TestRegistryRecord:
    def test_record_is_pure_and_carries_consumers(self):
        record = preflight.emit_registry_record(
            preflight.INITIAL_REGISTRY, preflight.GATES
        )
        names = [e["name"] for e in record["entries"]]
        assert names == sorted(names), "entries must be deterministically ordered"
        assert len(names) == len(preflight.INITIAL_REGISTRY)
        spec_min = next(e for e in record["entries"] if e["name"] == "SPEC_MIN_EFFECT")
        assert spec_min["consumed_by"] == ["endpoint:derive_pilot_thresholds"]
        assert spec_min["declared_value"] is None
        assert spec_min["status"] == "derived"

    def test_record_declares_all_three_namespaces(self):
        """So a later reader can re-run the referential check from the artifact."""
        record = preflight.emit_registry_record(
            preflight.INITIAL_REGISTRY, preflight.GATES
        )
        assert set(record["gates_declared"]) == set(preflight.GATES)
        assert set(record["preflight_checks_declared"]) == set(
            preflight.PREFLIGHT_CHECKS
        )
        assert set(record["endpoint_fns_declared"]) == set(preflight.ENDPOINT_FNS)


class TestTensorContracts:
    VALID: ClassVar[dict] = {
        "residual_shape": (2048,),
        "residual_dtype": "torch.float32",
        "jacobian_shape": (2048, 2048),
        "jacobian_dtype": "torch.float32",
        "readout_device": "cpu",
        "decode_parity_max_abs": 3.1e-6,
        "decode_parity_tol": 1e-5,
        "rank_parity_verified": True,
        "primary_floor_id": "input_embedding_decoded",
        "sensitivity_floor_id": "layer0_residual_decoded",
        "logit_softcapping": None,
    }

    def test_a_valid_configuration_passes(self):
        preflight.check_tensor_contracts(self.VALID)

    def test_lists_and_tuples_are_treated_alike(self):
        """Shapes arrive from JSON as lists and from torch as tuples."""
        preflight.check_tensor_contracts({**self.VALID, "residual_shape": [2048]})

    def test_wrong_residual_dtype_is_rejected(self):
        """Load-bearing, not hygiene: transport moves the Jacobian to the
        residual's device but does not cast dtype, and Stage 2b bypasses
        lens.apply for three of four cells, losing the .float() that path did."""
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_tensor_contracts(
                {**self.VALID, "residual_dtype": "torch.bfloat16"}
            )
        assert exc.value.code == "dtype_mismatch"

    def test_wrong_readout_device_is_rejected(self):
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_tensor_contracts({**self.VALID, "readout_device": "cuda:0"})
        assert exc.value.code == "device_mismatch"

    def test_wrong_residual_shape_is_rejected(self):
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_tensor_contracts({**self.VALID, "residual_shape": (768,)})
        assert exc.value.code == "shape_mismatch"

    def test_wrong_jacobian_shape_is_rejected(self):
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_tensor_contracts(
                {**self.VALID, "jacobian_shape": (2048, 1024)}
            )
        assert exc.value.code == "shape_mismatch"

    def test_decode_parity_beyond_tolerance_is_rejected(self):
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_tensor_contracts(
                {**self.VALID, "decode_parity_max_abs": 1e-2}
            )
        assert exc.value.code == "decode_parity"

    def test_missing_decode_parity_is_rejected_rather_than_skipped(self):
        """An unmeasured parity is not a passing parity."""
        observed = {**self.VALID}
        observed["decode_parity_max_abs"] = None
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_tensor_contracts(observed)
        assert exc.value.code == "decode_parity"

    @pytest.mark.parametrize("rank_parity_verified", [False, None, "true"])
    def test_rank_parity_must_be_explicitly_verified(self, rank_parity_verified):
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_tensor_contracts(
                {**self.VALID, "rank_parity_verified": rank_parity_verified}
            )
        assert exc.value.code == "rank_parity"

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("primary_floor_id", "layer0_residual_decoded"),
            ("primary_floor_id", None),
            ("sensitivity_floor_id", "input_embedding_decoded"),
            ("sensitivity_floor_id", "invented"),
        ],
    )
    def test_floor_identities_are_exact(self, field, value):
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_tensor_contracts({**self.VALID, field: value})
        assert exc.value.code == "floor_identity"

    def test_active_softcapping_is_rejected(self):
        """It would silently change every rank statistic."""
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_tensor_contracts({**self.VALID, "logit_softcapping": 30.0})
        assert exc.value.code == "unexpected_softcapping"


def _crossing_vectors():
    donors = [
        dict(entry)
        for entry in preflight.INITIAL_REGISTRY["WRONG_ACTIVATION_ASSIGNMENTS"][
            "declared_value"
        ]
    ]
    maps = [
        dict(entry)
        for entry in preflight.INITIAL_REGISTRY["BROKEN_MAP_DRAWS"]["declared_value"]
    ]
    return donors, maps


def _resolved_registry(*, mode="confirmatory"):
    donors, maps = _crossing_vectors()
    values = {
        "BROKEN_MAP_DRAWS": maps,
        "WRONG_ACTIVATION_ASSIGNMENTS": donors,
    }
    if mode == "pilot":
        values.update(
            {
                "PILOT_AUTHORIZED": True,
                "PILOT_PROTOCOL_RATIFIED": True,
            }
        )
    else:
        confirm_seed = preflight.bootstrap_rng_identity(
            "confirmatory", numpy_version="runtime-recorded"
        )
        values.update(
            {
                "BOOTSTRAP_SEED": {
                    key: value
                    for key, value in confirm_seed.items()
                    if key != "numpy_version"
                },
                "SPEC_MIN_EFFECT": [0.1, 0.1, 0.1, 0.1],
                "NTA_MIN_DENOMINATOR": 0.1,
                "INTERACTION_MIN_EFFECT": [0.1, 0.1, 0.1, 0.1],
                "THRESHOLDS_RATIFIED": True,
            }
        )
    registry = {name: dict(entry) for name, entry in preflight.INITIAL_REGISTRY.items()}
    for name, value in values.items():
        status = "derived" if registry[name]["kind"] == "derived_field" else "ratified"
        registry[name] = {
            **registry[name],
            "declared_value": value,
            "status": status,
        }
    return registry


def _authorization(mode="confirmatory"):
    donors, maps = _crossing_vectors()
    flags: dict[str, object] = {
        "WRONG_ACTIVATION_ASSIGNMENTS": donors,
        "BROKEN_MAP_DRAWS": maps,
    }
    if mode == "pilot":
        flags.update({"PILOT_AUTHORIZED": True, "PILOT_PROTOCOL_RATIFIED": True})
    else:
        flags["THRESHOLDS_RATIFIED"] = True
    return flags


def _pilot_authorization_record():
    instruction = "Authorize the bounded Stage 2b pilot fixture."
    values = {
        "PILOT_AUTHORIZED": True,
        "PILOT_PROTOCOL_RATIFIED": True,
    }
    return {
        "schema": preflight.PILOT_AUTHORIZATION_SCHEMA,
        "run_mode": "pilot",
        "decision": {
            "authority": "Dr. Mani",
            "authorized_at_utc": "2026-07-30T09:00:00Z",
            "instruction": instruction,
            "instruction_sha256": hashlib.sha256(
                (instruction + "\n").encode()
            ).hexdigest(),
        },
        "scope": {
            "pilot_view_sha256": "a" * 64,
            "confirmation_access_authorized": False,
            "artifact_transfer_authorized": False,
        },
        "source": {
            "notebook_sha256": "b" * 64,
            "code_bundle_sha256": "c" * 64,
        },
        "registry_updates": {
            name: {"declared_value": value, "status": "ratified"}
            for name, value in values.items()
        },
    }


def _write_authorization_record(tmp_path, record, *, filename_digest=None):
    payload = (json.dumps(record, sort_keys=True, indent=2) + "\n").encode()
    digest = filename_digest or hashlib.sha256(payload).hexdigest()
    path = tmp_path / f"stage2b-pilot-authorization-{digest}.json"
    path.write_bytes(payload)
    return path


def _record_digest(path):
    return path.stem.removeprefix("stage2b-pilot-authorization-")


def _load_authorization_record(
    path,
    *,
    approved_record_sha256,
    expected_pilot_view_sha256,
    observed_code_bundle_sha256="c" * 64,
):
    return preflight.load_pilot_authorization_record(
        path,
        approved_record_sha256=approved_record_sha256,
        expected_pilot_view_sha256=expected_pilot_view_sha256,
        observed_code_bundle_sha256=observed_code_bundle_sha256,
    )


class TestPilotAuthorizationRecord:
    def test_complete_content_addressed_record_materializes_and_passes(self, tmp_path):
        record = _pilot_authorization_record()
        path = _write_authorization_record(tmp_path, record)
        loaded = _load_authorization_record(
            path,
            approved_record_sha256=_record_digest(path),
            expected_pilot_view_sha256="a" * 64,
        )
        configuration, registry = preflight.materialize_pilot_authorization(
            loaded, preflight.INITIAL_REGISTRY
        )
        preflight.check_ratification(configuration, registry, mode="pilot")
        assert configuration["THRESHOLDS_RATIFIED"] is False
        assert registry["NTA_MIN_DENOMINATOR"]["declared_value"] is None
        assert registry["NTA_MIN_DENOMINATOR"]["status"] == "derived"

    def test_filename_digest_mismatch_refuses(self, tmp_path):
        record = _pilot_authorization_record()
        path = _write_authorization_record(tmp_path, record, filename_digest="b" * 64)
        with pytest.raises(preflight.PreflightError) as exc:
            _load_authorization_record(
                path,
                approved_record_sha256="b" * 64,
                expected_pilot_view_sha256="a" * 64,
            )
        assert exc.value.code == "authorization_record_digest"

    def test_unknown_top_level_field_refuses(self, tmp_path):
        record = {**_pilot_authorization_record(), "scientific_decision": "pass"}
        path = _write_authorization_record(tmp_path, record)
        with pytest.raises(preflight.PreflightError) as exc:
            _load_authorization_record(
                path,
                approved_record_sha256=_record_digest(path),
                expected_pilot_view_sha256="a" * 64,
            )
        assert exc.value.code == "authorization_record_schema"

    def test_wrong_pilot_view_refuses(self, tmp_path):
        path = _write_authorization_record(tmp_path, _pilot_authorization_record())
        with pytest.raises(preflight.PreflightError) as exc:
            _load_authorization_record(
                path,
                approved_record_sha256=_record_digest(path),
                expected_pilot_view_sha256="b" * 64,
            )
        assert exc.value.code == "authorization_record_pilot_view"

    def test_observed_code_bundle_hash_mismatch_refuses(self, tmp_path):
        path = _write_authorization_record(tmp_path, _pilot_authorization_record())
        with pytest.raises(preflight.PreflightError) as exc:
            _load_authorization_record(
                path,
                approved_record_sha256=_record_digest(path),
                expected_pilot_view_sha256="a" * 64,
                observed_code_bundle_sha256="d" * 64,
            )
        assert exc.value.code == "authorization_record_source"
        assert exc.value.detail["field"] == "code_bundle_sha256"

    def test_notebook_source_identity_must_be_a_digest(self, tmp_path):
        record = _pilot_authorization_record()
        record["source"]["notebook_sha256"] = "claimed-notebook"
        path = _write_authorization_record(tmp_path, record)
        with pytest.raises(preflight.PreflightError) as exc:
            _load_authorization_record(
                path,
                approved_record_sha256=_record_digest(path),
                expected_pilot_view_sha256="a" * 64,
            )
        assert exc.value.code == "authorization_record_source"
        assert exc.value.detail["field"] == "notebook_sha256"

    @pytest.mark.parametrize(
        "field",
        ["confirmation_access_authorized", "artifact_transfer_authorized"],
    )
    def test_scope_cannot_expand_to_confirmation_or_transfer(self, tmp_path, field):
        record = _pilot_authorization_record()
        record["scope"][field] = True
        path = _write_authorization_record(tmp_path, record)
        with pytest.raises(preflight.PreflightError) as exc:
            _load_authorization_record(
                path,
                approved_record_sha256=_record_digest(path),
                expected_pilot_view_sha256="a" * 64,
            )
        assert exc.value.code == "authorization_record_boundary"

    def test_instruction_digest_mismatch_refuses(self, tmp_path):
        record = _pilot_authorization_record()
        record["decision"]["instruction"] = "Changed after approval."
        path = _write_authorization_record(tmp_path, record)
        with pytest.raises(preflight.PreflightError) as exc:
            _load_authorization_record(
                path,
                approved_record_sha256=_record_digest(path),
                expected_pilot_view_sha256="a" * 64,
            )
        assert exc.value.code == "authorization_record_decision"

    def test_duplicate_json_key_refuses(self, tmp_path):
        payload = b'{"schema":"one","schema":"two"}\n'
        digest = hashlib.sha256(payload).hexdigest()
        path = tmp_path / f"stage2b-pilot-authorization-{digest}.json"
        path.write_bytes(payload)
        with pytest.raises(preflight.PreflightError) as exc:
            _load_authorization_record(
                path,
                approved_record_sha256=digest,
                expected_pilot_view_sha256="a" * 64,
            )
        assert exc.value.code == "authorization_record_json"

    def test_unapproved_but_self_consistent_record_refuses(self, tmp_path):
        path = _write_authorization_record(tmp_path, _pilot_authorization_record())
        with pytest.raises(preflight.PreflightError) as exc:
            _load_authorization_record(
                path,
                approved_record_sha256="c" * 64,
                expected_pilot_view_sha256="a" * 64,
            )
        assert exc.value.code == "authorization_record_approval"

    def test_forged_authority_refuses_even_with_approved_digest(self, tmp_path):
        record = _pilot_authorization_record()
        record["decision"]["authority"] = "attacker"
        path = _write_authorization_record(tmp_path, record)
        with pytest.raises(preflight.PreflightError) as exc:
            _load_authorization_record(
                path,
                approved_record_sha256=_record_digest(path),
                expected_pilot_view_sha256="a" * 64,
            )
        assert exc.value.code == "authorization_record_authority"

    def test_invalid_authorization_timestamp_refuses(self, tmp_path):
        record = _pilot_authorization_record()
        record["decision"]["authorized_at_utc"] = "2026-99-30T09:00:00Z"
        path = _write_authorization_record(tmp_path, record)
        with pytest.raises(preflight.PreflightError) as exc:
            _load_authorization_record(
                path,
                approved_record_sha256=_record_digest(path),
                expected_pilot_view_sha256="a" * 64,
            )
        assert exc.value.code == "authorization_record_decision"

    def test_incomplete_registry_update_refuses(self):
        record = _pilot_authorization_record()
        del record["registry_updates"]["PILOT_AUTHORIZED"]
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.materialize_pilot_authorization(
                record, preflight.INITIAL_REGISTRY
            )
        assert exc.value.code == "authorization_record_incomplete"
        assert exc.value.detail["missing"] == ["PILOT_AUTHORIZED"]

    def test_unratified_registry_update_refuses(self):
        record = _pilot_authorization_record()
        record["registry_updates"]["PILOT_PROTOCOL_RATIFIED"]["status"] = "proposed"
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.materialize_pilot_authorization(
                record, preflight.INITIAL_REGISTRY
            )
        assert exc.value.code == "authorization_record_unratified"


class TestRatification:
    @pytest.mark.parametrize(
        ("mode", "name", "code"),
        [
            ("pilot", "PILOT_AUTHORIZED", "pilot_not_authorized"),
            ("confirmatory", "THRESHOLDS_RATIFIED", "not_ratified"),
        ],
    )
    @pytest.mark.parametrize("status", ["ratified", "unratified"])
    def test_caller_authorization_cannot_override_false_registry_truth(
        self, mode, name, code, status
    ):
        registry = _resolved_registry(mode=mode)
        registry[name] = {
            **registry[name],
            "declared_value": False,
            "status": status,
        }

        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_ratification(_authorization(mode), registry, mode=mode)

        assert exc.value.code == code

    @pytest.mark.parametrize("mode", ["pilot", "confirmatory"])
    def test_registry_must_be_explicitly_supplied(self, mode):
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_ratification(_authorization(mode), mode=mode)
        assert exc.value.code == "registry_required"

    def test_confirmatory_run_validates_crossing_vectors_from_authorization(self):
        authorization = _authorization()
        authorization["BROKEN_MAP_DRAWS"] = [{"id": "not-eight", "seed": 1}]
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_ratification(
                authorization, _resolved_registry(), mode="confirmatory"
            )
        assert exc.value.code == "crossing_registry_size"

    def test_unratified_configuration_refuses(self):
        """The shipped state. FR-013 and Q10."""
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_ratification(
                {"THRESHOLDS_RATIFIED": False}, preflight.INITIAL_REGISTRY
            )
        assert exc.value.code == "not_ratified"

    def test_missing_flag_is_treated_as_unratified(self):
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_ratification({}, preflight.INITIAL_REGISTRY)
        assert exc.value.code == "not_ratified"

    def test_pilot_derived_values_block_confirmatory_ratification(self):
        """None of the three can be signed past by accident.

        The pilot is what sets them; a signature before the pilot has run would
        be Stage 2's mistake, which set a margin with no pilot and then could
        not say whether its controls were inseparable or under-resolved.
        """
        for name in (
            "SPEC_MIN_EFFECT",
            "NTA_MIN_DENOMINATOR",
            "INTERACTION_MIN_EFFECT",
        ):
            registry = _resolved_registry()
            registry[name] = {
                **registry[name],
                "declared_value": None,
                "status": "derived",
            }
            with pytest.raises(preflight.PreflightError) as exc:
                preflight.check_ratification(_authorization(), registry)
            assert exc.value.code == "invalid_constant"
            assert exc.value.detail["constant"] == name

    def test_ratifying_with_an_unset_threshold_is_refused(self):
        """Deferring a threshold and signing the ratification are mutually
        exclusive. Stage 2 set a margin without a pilot and then could not say
        whether its controls were inseparable or merely under-resolved."""
        registry = _resolved_registry()
        registry["SPEC_MIN_EFFECT"] = {
            **registry["SPEC_MIN_EFFECT"],
            "declared_value": None,
            "status": "derived",
        }
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_ratification(_authorization(), registry)
        assert exc.value.code == "invalid_constant"
        assert exc.value.detail["constant"] == "SPEC_MIN_EFFECT"

    def test_ratifying_with_every_threshold_set_passes(self):
        preflight.check_ratification(_authorization(), _resolved_registry())

    def test_derived_fields_do_not_block_authorized_pilot(self):
        registry = _resolved_registry(mode="pilot")
        assert registry["nta_jacobian"]["declared_value"] is None
        preflight.check_ratification(_authorization("pilot"), registry, mode="pilot")

    def test_authorized_pilot_allows_all_three_derived_outputs_to_remain_unset(self):
        preflight.check_ratification(
            _authorization("pilot"),
            _resolved_registry(mode="pilot"),
            mode="pilot",
        )

    def test_authorized_pilot_requires_unset_denominator_guard(self):
        registry = _resolved_registry(mode="pilot")
        preflight.check_ratification(
            _authorization("pilot"),
            registry,
            mode="pilot",
        )

    @pytest.mark.parametrize(
        "value",
        ["garbage", True, 0.0, -1.0, float("nan"), float("inf")],
    )
    def test_authorized_pilot_refuses_invalid_denominator_guard(self, value):
        registry = _resolved_registry(mode="pilot")
        registry["NTA_MIN_DENOMINATOR"] = {
            **registry["NTA_MIN_DENOMINATOR"],
            "declared_value": value,
            "status": "derived",
        }
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_ratification(
                _authorization("pilot"),
                registry,
                mode="pilot",
            )
        assert exc.value.code == "pilot_derived_input"
        assert exc.value.detail["constant"] == "NTA_MIN_DENOMINATOR"

    def test_pilot_protocol_flag_cannot_bypass_unset_inference_rules(self):
        registry = _resolved_registry(mode="pilot")
        registry["MULTIPLICITY_RULE"] = {
            **registry["MULTIPLICITY_RULE"],
            "declared_value": None,
            "status": "unratified",
        }
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_ratification(
                _authorization("pilot"), registry, mode="pilot"
            )
        assert exc.value.code == "pilot_protocol_incomplete"
        assert exc.value.detail["constant"] == "MULTIPLICITY_RULE"

    def test_authorization_cannot_bypass_unratified_pilot_protocol(self):
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_ratification(
                {"PILOT_AUTHORIZED": True, "PILOT_PROTOCOL_RATIFIED": False},
                _resolved_registry(mode="pilot"),
                mode="pilot",
            )
        assert exc.value.code == "pilot_protocol_not_ratified"

    def test_pilot_without_its_separate_authorization_refuses(self):
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_ratification(
                {}, _resolved_registry(mode="pilot"), mode="pilot"
            )
        assert exc.value.code == "pilot_not_authorized"

    @pytest.mark.parametrize("mode", ["", "exploratory", "PILOT"])
    def test_unknown_run_mode_refuses(self, mode):
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_ratification({}, preflight.INITIAL_REGISTRY, mode=mode)
        assert exc.value.code == "invalid_run_mode"

    @pytest.mark.parametrize(
        ("name", "value"),
        [
            ("SPEC_MIN_EFFECT", "0.1"),
            ("SPEC_MIN_EFFECT", True),
            ("SPEC_MIN_EFFECT", float("nan")),
            ("NTA_MIN_DENOMINATOR", 0.0),
            ("BOOTSTRAP_CI_LEVEL", 1.0),
            ("UNCERTAINTY_METHOD", ""),
            ("RESAMPLING_UNIT", " "),
            ("INTERVAL_METHOD", 95),
            ("BOOTSTRAP_ITERATIONS", 0),
            ("BOOTSTRAP_SEED", True),
            ("AGGREGATION_RULE", ""),
            ("THRESHOLD_DERIVATION_RULES", {"SPEC_MIN_EFFECT": "only-one"}),
            ("MULTIPLICITY_RULE", ""),
        ],
    )
    def test_confirmatory_thresholds_must_be_finite_numeric_and_in_range(
        self, name, value
    ):
        registry = _resolved_registry()
        registry[name] = {
            **registry[name],
            "declared_value": value,
            "status": (
                "derived" if registry[name]["kind"] == "derived_field" else "ratified"
            ),
        }
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_ratification(
                _authorization(), registry, mode="confirmatory"
            )
        assert exc.value.code == "invalid_constant"
        assert exc.value.detail["constant"] == name

    @pytest.mark.parametrize("name", ["SPEC_MIN_EFFECT", "INTERACTION_MIN_EFFECT"])
    def test_confirmatory_effect_thresholds_must_be_positive_vectors(self, name):
        registry = _resolved_registry()
        registry[name] = {
            **registry[name],
            "declared_value": [-0.01, 0.1, 0.1, 0.1],
            "status": "derived",
        }

        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_ratification(_authorization(), registry)
        assert exc.value.code == "invalid_constant"


class TestEnvironment:
    PINS: ClassVar[dict] = {
        k: v["declared_value"] for k, v in preflight.INITIAL_REGISTRY.items()
    }
    VALID: ClassVar[dict] = {
        "python_version": (3, 12, 1),
        "cuda_available": True,
        "vram_gib": 15.0,
        "jlens_commit": PINS["JLENS_COMMIT"],
        "model_id": PINS["MODEL_ID"],
        "model_revision": PINS["MODEL_REVISION"],
        "lens_repo": PINS["LENS_REPO"],
        "lens_revision": PINS["LENS_REVISION"],
        "lens_file": PINS["LENS_FILE"],
        "expected_lens_sha256": PINS["EXPECTED_LENS_SHA256"],
        "expected_model_d_model": PINS["EXPECTED_MODEL_D_MODEL"],
        "expected_model_n_layers": PINS["EXPECTED_MODEL_N_LAYERS"],
    }

    def test_a_valid_environment_passes(self):
        preflight.check_environment(self.VALID, self.PINS)

    def test_old_python_is_rejected(self):
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_environment(
                {**self.VALID, "python_version": (3, 9, 0)}, self.PINS
            )
        assert exc.value.code == "python_version"

    def test_no_cuda_is_rejected(self):
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_environment(
                {**self.VALID, "cuda_available": False}, self.PINS
            )
        assert exc.value.code == "no_cuda"

    def test_insufficient_vram_is_rejected(self):
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_environment({**self.VALID, "vram_gib": 8.0}, self.PINS)
        assert exc.value.code == "insufficient_vram"

    def test_wrong_jlens_commit_is_rejected(self):
        """Read back from the installed package, not trusted from the install
        line — that converts an inference into a measurement."""
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_environment(
                {**self.VALID, "jlens_commit": "deadbeef"}, self.PINS
            )
        assert exc.value.code == "jlens_commit"

    @pytest.mark.parametrize(
        "field", ["model_revision", "lens_revision", "expected_lens_sha256"]
    )
    def test_identity_mismatches_are_rejected(self, field):
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_environment({**self.VALID, field: "wrong"}, self.PINS)
        assert exc.value.code == "identity_mismatch"


class TestInstalledVcsIdentity:
    def test_commit_is_measured_from_direct_url_metadata(self):
        record = json.dumps(
            {
                "url": "https://github.com/anthropics/jacobian-lens.git",
                "vcs_info": {
                    "vcs": "git",
                    "commit_id": "581d398613e5602a5af361e1c34d3a92ea82ba8e",
                },
            }
        )
        assert (
            preflight.installed_vcs_commit(
                record,
                expected_repo_url="https://github.com/anthropics/jacobian-lens.git",
            )
            == "581d398613e5602a5af361e1c34d3a92ea82ba8e"
        )

    @pytest.mark.parametrize(
        "record",
        [
            None,
            "{}",
            json.dumps({"vcs_info": {"vcs": "git"}}),
            json.dumps({"vcs_info": {"vcs": "git", "commit_id": "expected fallback"}}),
            "not json",
        ],
    )
    def test_missing_or_malformed_metadata_fails_closed(self, record):
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.installed_vcs_commit(
                record,
                expected_repo_url="https://github.com/anthropics/jacobian-lens.git",
            )
        assert exc.value.code == "jlens_identity_unverifiable"

    def test_metadata_for_a_different_repository_is_rejected(self):
        record = json.dumps(
            {
                "url": "https://example.invalid/lookalike.git",
                "vcs_info": {
                    "vcs": "git",
                    "commit_id": "581d398613e5602a5af361e1c34d3a92ea82ba8e",
                },
            }
        )
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.installed_vcs_commit(
                record,
                expected_repo_url="https://github.com/anthropics/jacobian-lens.git",
            )
        assert exc.value.code == "jlens_identity_unverifiable"


def test_prompt_only_construction_is_pinned():
    """Open item 8: Stage 2's construction, so the two stages' NTA values stay
    comparable and 'transporting nothing' stays literally true."""
    entry = preflight.INITIAL_REGISTRY["PROMPT_ONLY_CONSTRUCTION"]
    assert entry["declared_value"] == "input_embedding_decoded"
    assert entry["consumed_by"] == ["endpoint:nta"]
