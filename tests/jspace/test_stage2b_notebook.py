"""The notebook must refuse to run in the state it ships in.

This is the boundary between authoring, which this feature covers, and
execution, which it does not (FR-013, Q10). Worth re-running after any edit to
the notebook.
"""

from __future__ import annotations

import json
import pathlib

import pytest

NOTEBOOK = (
    pathlib.Path(__file__).resolve().parents[2]
    / "sakshi notes/jspace_colab_stage2b_discrimination.ipynb"
)


@pytest.fixture(scope="module")
def notebook():
    if not NOTEBOOK.exists():
        pytest.skip("notebook not present on this branch")
    return json.loads(NOTEBOOK.read_text())


@pytest.fixture(scope="module")
def source(notebook):
    return "\n".join(
        "".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code"
    )


def test_notebook_is_valid_nbformat(notebook):
    assert notebook["nbformat"] == 4
    assert notebook["cells"]


def test_ships_unratified(source):
    """FR-013. Whatever else is true, the committed notebook must refuse."""
    assert "THRESHOLDS_RATIFIED = False" in source
    assert "THRESHOLDS_RATIFIED = True" not in source


def test_the_ratification_gate_precedes_the_measurement_loop(notebook):
    """A guard after the loop is not a guard."""
    code = ["".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code"]
    gate = next(i for i, c in enumerate(code) if "check_ratification" in c)
    loop = next(i for i, c in enumerate(code) if "measurement loop" in c.lower())
    assert gate < loop


def test_the_four_deferred_values_ship_unset(source):
    """Including the two decisions T051 surfaced. Declared-but-unset is what
    lets the notebook exist while the questions are open: check_ratification
    refuses a signature while any of them is None."""
    for name in (
        "SPEC_MIN_EFFECT",
        "NTA_MIN_DENOMINATOR",
        "INTERACTION_GATED",
        "PROMPT_ONLY_CONSTRUCTION",
    ):
        assert f"{name} = None" in source, f"{name} must ship unset"


def test_stage_twos_five_name_transport_probe_is_gone(source):
    """R1 and R3 confirmed the names against the pinned commit, so a probe that
    accepts whichever of five happens to exist is no longer auditable."""
    for probed in (
        "resolve_transport_fn",
        "resolve_jacobian_accessor",
        "apply_jacobian",
    ):
        assert probed not in source
    assert 'hasattr(lens, "jacobians")' in source
    assert 'getattr(lens, "transport"' in source


def test_stage_twos_loose_constants_are_resolved(source):
    """Each must drive the loop that bears its name, or not exist (T038)."""
    assert "SAME_RUNTIME_REPEATS = 2" in source
    assert "INFERENCE_SEEDS = [0]" in source, "Stage 2 declared two and ran one"
    assert "RANDOM_VECTOR_SEEDS = [0, 1, 2]" in source


def test_aggregate_export_carries_all_five_blocks(source):
    """descriptive stays a sibling of gates so a reported quantity cannot be
    mistaken for a decision input."""
    for block in (
        '"registry"',
        '"disjointness"',
        '"gates"',
        '"descriptive"',
        '"decision"',
    ):
        assert block in source


def test_content_addressing_matches_stage_twos_scheme(source):
    """Byte-identical, so the two stages' artifacts are comparable objects."""
    assert "sort_keys=True, indent=2, ensure_ascii=False" in source
    assert '"xb"' in source


def test_token_counts_are_measured_not_read_from_the_manifest(source):
    assert "token_counts=token_counts" in source
    assert "tokenizer(" in source


def test_the_measurement_loop_refuses_pending_the_open_decisions(source):
    """It is unwritten on purpose: authoring it now would hardcode a decision
    rule nobody chose and a baseline nobody defined."""
    assert "NotImplementedError" in source
    assert "open items 7 and 8" in source
