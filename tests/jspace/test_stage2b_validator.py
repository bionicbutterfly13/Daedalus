"""Validator tests: the aggregate must be recomputable from itself (SC-003).

The test is not "does it parse". Stage 2's artifacts parsed fine, and its audit
still had to read notebook source to establish what the gates actually did.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
from typing import ClassVar

import pytest

_SCRIPTS = (
    pathlib.Path(__file__).resolve().parents[2]
    / "EvoScientist/skills/jspace-research-operations/scripts"
)
_spec = importlib.util.spec_from_file_location(
    "validate_observation", _SCRIPTS / "validate_observation.py"
)
assert _spec is not None
assert _spec.loader is not None
validator = importlib.util.module_from_spec(_spec)
sys.modules["validate_observation"] = validator
_spec.loader.exec_module(validator)


def _gate(name="h1_specificity", outcome="pass", method="bca", low=0.1, high=0.4):
    gate = {
        "name": name,
        "constant_name": "SPEC_MIN_EFFECT",
        "declared_value": 0.1,
        "statistic": 0.25,
        "interval": {"method": method, "level": 0.99, "low": low, "high": high},
        "n_clusters": 193,
        "exclusions": [],
        "outcome": outcome,
    }
    if method == "bca":
        gate["interval_crosscheck"] = {"method": "percentile", "low": 0.1, "high": 0.4}
    return gate


class TestStage2bAggregate:
    BASE: ClassVar[dict] = {
        "schema": "jspace-observation-stage2b/v1",
        "artifact_type": "aggregate",
        "registry": {
            "entries": [{"name": "SPEC_MIN_EFFECT", "consumed_by": ["h1_specificity"]}]
        },
        "disjointness": {"checked": True, "overlap_count": 0, "anchor_present": False},
        "gates": [_gate()],
        "descriptive": {},
        "decision": {"result": "pass", "notes": ""},
    }

    def _errors(self, artifact, tmp_path):
        path = tmp_path / "a.json"
        path.write_text(json.dumps(artifact))
        errors: list[str] = []
        validator.validate_stage2b_aggregate(artifact, path, "0" * 64, errors)
        return errors

    def _relevant(self, artifact, tmp_path, needle):
        return [e for e in self._errors(artifact, tmp_path) if needle in e]

    def test_a_registry_entry_with_no_consumer_is_flagged(self, tmp_path):
        bad = {**self.BASE, "registry": {"entries": [{"name": "X", "consumed_by": []}]}}
        assert self._relevant(bad, tmp_path, "no consumer")

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

    def test_nonfinite_interval_reported_as_fail_is_flagged(self, tmp_path):
        """The rule that stops a failed computation reading as a measured null."""
        bad = {**self.BASE, "gates": [_gate(outcome="fail", low=float("nan"))]}
        # NaN survives json.dumps as literal NaN, which json.loads accepts.
        assert self._relevant(bad, tmp_path, "undefined, never fail")

    def test_nonfinite_interval_reported_as_undefined_is_accepted(self, tmp_path):
        ok = {**self.BASE, "gates": [_gate(outcome="undefined", low=float("nan"))]}
        assert not self._relevant(ok, tmp_path, "undefined, never fail")

    def test_bca_without_a_crosscheck_is_flagged(self, tmp_path):
        gate = _gate()
        del gate["interval_crosscheck"]
        assert self._relevant({**self.BASE, "gates": [gate]}, tmp_path, "cross-check")

    @pytest.mark.parametrize("field", ["statistic", "n_clusters", "exclusions"])
    def test_a_gate_missing_a_recomputability_field_is_flagged(self, field, tmp_path):
        """SC-003: every value the outcome depends on must be in the artifact."""
        gate = _gate()
        del gate[field]
        assert self._relevant({**self.BASE, "gates": [gate]}, tmp_path, field)

    def test_missing_descriptive_block_is_flagged(self, tmp_path):
        bad = {k: v for k, v in self.BASE.items() if k != "descriptive"}
        assert self._relevant(bad, tmp_path, "descriptive")

    def test_bad_decision_result_is_flagged(self, tmp_path):
        bad = {**self.BASE, "decision": {"result": "maybe"}}
        assert self._relevant(bad, tmp_path, "decision.result")

    def test_a_wellformed_aggregate_raises_none_of_these(self, tmp_path):
        errors = self._errors(self.BASE, tmp_path)
        for needle in (
            "no consumer",
            "overlap_count",
            "undefined, never fail",
            "cross-check",
            "descriptive",
            "decision.result",
        ):
            assert not [e for e in errors if needle in e], f"unexpected: {needle}"


def test_stage2b_schema_is_dispatched_separately(tmp_path):
    """A Stage 2b artifact must not be validated as a Stage 2 one."""
    artifact = dict(TestStage2bAggregate.BASE)
    path = tmp_path / "agg.json"
    path.write_text(json.dumps(artifact))
    summary, _ = validator.validate(path, None)
    assert summary.get("detected_contract") == "stage2b_aggregate"
