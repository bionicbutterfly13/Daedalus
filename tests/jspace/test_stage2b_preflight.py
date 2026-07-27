"""Preflight tests: every check must be proven to FAIL, not only to pass.

Per constitution Principle III, a preflight suite that only demonstrates valid
configurations pass has not tested the preflight.  Each test below constructs a
configuration built to trip one specific failure code, and asserts on ``code``
rather than on message text so the messages stay free to change.
"""

from __future__ import annotations

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
                "consumed_by": [],
            }
        }
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_constant_registry(registry, preflight.GATES)
        assert exc.value.code == "orphaned_constant"
        assert exc.value.detail["constant"] == "INFERENCE_SEEDS"

    def test_missing_consumed_by_key_is_also_orphaned(self):
        registry = {"SOME_CONSTANT": {"kind": "constant", "declared_value": 1}}
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
                "endpoint:allocate_wrong_layers": [
                    "WRONG_LAYER_DISTANCES",
                    "WRONG_LAYER_SEED",
                ],
            },
        )

    def test_phantom_gate_consumer_is_rejected(self):
        registry = {
            "X": {
                "kind": "constant",
                "declared_value": 1,
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
                "consumed_by": ["H1 specificity"],
            }
        }
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_constant_registry(registry, preflight.GATES)
        assert exc.value.code == "phantom_consumer"


class TestRegistryCompleteness:
    """Properties of the shipped registry itself, not of the checker."""

    def test_deferred_constants_are_exactly_the_two_pilot_derived_ones(self):
        """Q5 and Q6 are deliberately unset; nothing else may be.

        A ``None`` anywhere else is a forgotten value masquerading as a
        deliberate deferral.
        """
        unset = {
            name
            for name, entry in preflight.INITIAL_REGISTRY.items()
            if entry["kind"] == "constant" and entry["declared_value"] is None
        }
        assert unset == {
            "SPEC_MIN_EFFECT",
            "NTA_MIN_DENOMINATOR",
            # The two decisions T051 surfaced. Declared-but-unset so the run
            # refuses until they are made, rather than running with the
            # questions open.
            "INTERACTION_GATED",
            "PROMPT_ONLY_CONSTRUCTION",
        }

    def test_every_gate_has_at_least_one_registered_constant_or_field(self):
        consumed = {
            c
            for entry in preflight.INITIAL_REGISTRY.values()
            for c in entry["consumed_by"]
        }
        for gate in preflight.GATES:
            assert gate in consumed, f"gate {gate!r} reads nothing registered"

    def test_registry_covers_both_kinds(self):
        """The derived_field kind is why Stage 2's fourth orphan is catchable.

        ``output_argmax_rank_*`` was computed, stored, and read by no gate while
        the ratification checklist called that downstream criterion ratified.  A
        constants-only registry would pass it.
        """
        kinds = {e["kind"] for e in preflight.INITIAL_REGISTRY.values()}
        assert kinds == {"constant", "derived_field"}


class TestRegistryRecord:
    def test_record_is_pure_and_carries_consumers(self):
        record = preflight.emit_registry_record(
            preflight.INITIAL_REGISTRY, preflight.GATES
        )
        names = [e["name"] for e in record["entries"]]
        assert names == sorted(names), "entries must be deterministically ordered"
        assert len(names) == len(preflight.INITIAL_REGISTRY)
        spec_min = next(e for e in record["entries"] if e["name"] == "SPEC_MIN_EFFECT")
        assert spec_min["consumed_by"] == ["h1_specificity"]
        assert spec_min["declared_value"] is None

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

    def test_active_softcapping_is_rejected(self):
        """It would silently change every rank statistic."""
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_tensor_contracts({**self.VALID, "logit_softcapping": 30.0})
        assert exc.value.code == "unexpected_softcapping"


class TestRatification:
    def test_unratified_configuration_refuses(self):
        """The shipped state. FR-013 and Q10."""
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_ratification({"THRESHOLDS_RATIFIED": False})
        assert exc.value.code == "not_ratified"

    def test_missing_flag_is_treated_as_unratified(self):
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_ratification({})
        assert exc.value.code == "not_ratified"

    def test_the_two_open_design_decisions_block_ratification(self):
        """Open items 7 and 8 cannot be signed past by accident.

        The notebook can be authored while they are open precisely because they
        are unset constants: the run refuses rather than proceeding under a
        decision rule nobody chose.
        """
        for name in ("INTERACTION_GATED", "PROMPT_ONLY_CONSTRUCTION"):
            registry = {
                k: (
                    {**v, "declared_value": 0.1}
                    if v["declared_value"] is None and k != name
                    else v
                )
                for k, v in preflight.INITIAL_REGISTRY.items()
            }
            with pytest.raises(preflight.PreflightError) as exc:
                preflight.check_ratification({"THRESHOLDS_RATIFIED": True}, registry)
            assert exc.value.code == "unset_constant"
            assert exc.value.detail["constant"] == name

    def test_ratifying_with_an_unset_threshold_is_refused(self):
        """Deferring a threshold and signing the ratification are mutually
        exclusive. Stage 2 set a margin without a pilot and then could not say
        whether its controls were inseparable or merely under-resolved."""
        with pytest.raises(preflight.PreflightError) as exc:
            preflight.check_ratification(
                {"THRESHOLDS_RATIFIED": True}, preflight.INITIAL_REGISTRY
            )
        assert exc.value.code == "unset_constant"
        assert exc.value.detail["constant"] in {
            "SPEC_MIN_EFFECT",
            "NTA_MIN_DENOMINATOR",
        }

    def test_ratifying_with_every_threshold_set_passes(self):
        registry = {
            name: {**entry, "declared_value": 0.1}
            if entry["declared_value"] is None
            else entry
            for name, entry in preflight.INITIAL_REGISTRY.items()
        }
        preflight.check_ratification({"THRESHOLDS_RATIFIED": True}, registry)

    def test_derived_fields_do_not_block_ratification(self):
        """They have no declared value by nature; only constants must be set."""
        registry = {"nta_jacobian": {"kind": "derived_field", "declared_value": None}}
        preflight.check_ratification({"THRESHOLDS_RATIFIED": True}, registry)


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
