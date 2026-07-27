"""Preflight tests: every check must be proven to FAIL, not only to pass.

Per constitution Principle III, a preflight suite that only demonstrates valid
configurations pass has not tested the preflight.  Each test below constructs a
configuration built to trip one specific failure code, and asserts on ``code``
rather than on message text so the messages stay free to change.
"""

from __future__ import annotations

import importlib.util
import pathlib

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


def test_module_imports_without_torch_jlens_or_scipy():
    """The binding constraint from plan.md's Structure Decision.

    If this ever fails, the whole preflight becomes untestable on any machine
    without a GPU stack -- which is the exact condition that made Stage 2's
    equivalent logic unreachable by any test.
    """
    import sys

    assert "torch" not in sys.modules
    assert "jlens" not in sys.modules
    assert "scipy" not in sys.modules


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
        assert unset == {"SPEC_MIN_EFFECT", "NTA_MIN_DENOMINATOR"}

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
