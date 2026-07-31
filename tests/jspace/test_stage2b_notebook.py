"""The notebook must refuse to run in the state it ships in.

This is the boundary between authoring, which this feature covers, and
execution, which it does not (FR-013, Q10). Worth re-running after any edit to
the notebook.
"""

from __future__ import annotations

import ast
import hashlib
import json
import pathlib

import pytest

NOTEBOOK = (
    pathlib.Path(__file__).resolve().parents[2]
    / "j-space-lab/jspace_colab_stage2b_discrimination.ipynb"
)
ARTIFACT_SCHEMA = (
    pathlib.Path(__file__).resolve().parents[2]
    / "specs/001-jspace-stage2b/contracts/artifact-schema.md"
)
PILOT_VIEW = (
    pathlib.Path(__file__).resolve().parents[2]
    / "j-space-lab/jspace-stage2b-pilot-v1.json"
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


def test_canonical_pilot_view_is_present_and_hash_bound():
    assert PILOT_VIEW.is_file()
    assert (
        hashlib.sha256(PILOT_VIEW.read_bytes()).hexdigest()
        == "5bef8316f72682a628fc1240bf6068a91aa7c8a330377206cbd9145434b797e4"
    )


def test_every_ordinary_code_cell_parses(notebook):
    """A valid notebook container is not evidence that its Python can execute."""
    failures = []
    for index, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] != "code":
            continue
        code = "".join(cell["source"])
        if code.lstrip().startswith(("%", "!")):
            continue
        try:
            ast.parse(code)
        except SyntaxError as exc:
            failures.append(f"cell {index}: {exc.msg} at line {exc.lineno}")
    assert failures == []


def test_ships_unratified(source):
    """FR-013. Whatever else is true, the committed notebook must refuse."""
    assert "PILOT_AUTHORIZED = False" in source
    assert "PILOT_AUTHORIZED = True" not in source
    assert "THRESHOLDS_RATIFIED = False" in source
    assert "THRESHOLDS_RATIFIED = True" not in source
    assert "PILOT_PROTOCOL_RATIFIED = False" in source
    assert "PILOT_PROTOCOL_RATIFIED = True" not in source
    assert "ARTIFACT_TRANSFER_AUTHORIZED = False" in source
    assert "ARTIFACT_TRANSFER_AUTHORIZED = True" not in source


def test_pilot_transition_consumes_one_external_content_addressed_record(source):
    assert "APPROVED_AUTHORIZATION_RECORD_SHA256 = input(" in source
    assert "OBSERVED_NOTEBOOK_SHA256" not in source
    assert "PILOT_CODE_BUNDLE.read_bytes()" in source
    assert (
        'f"stage2b-pilot-authorization-{APPROVED_AUTHORIZATION_RECORD_SHA256}.json"'
        in source
    )
    assert "pf.load_pilot_authorization_record(" in source
    assert "approved_record_sha256=APPROVED_AUTHORIZATION_RECORD_SHA256" in source
    assert "observed_code_bundle_sha256=OBSERVED_CODE_BUNDLE_SHA256" in source
    assert (
        'AUTHORIZATION_RECORD_SHA256 = AUTHORIZATION_RECORD["_record_sha256"]' in source
    )
    assert "pf.materialize_pilot_authorization(" in source
    assert 'PILOT_AUTHORIZED = AUTHORIZATION["PILOT_AUTHORIZED"]' in source
    assert (
        'PILOT_PROTOCOL_RATIFIED = AUTHORIZATION["PILOT_PROTOCOL_RATIFIED"]' in source
    )
    assert 'REGISTRY["NTA_MIN_DENOMINATOR"]["declared_value"] is not None' in source
    assert 'glob("stage2b-pilot-authorization-*.json")' not in source


def test_code_bundle_and_pilot_view_are_separately_hash_bound(source):
    for required in (
        'PILOT_CODE_BUNDLE = pathlib.Path("stage2b-pilot-code-bundle.zip")',
        "OBSERVED_CODE_BUNDLE_SHA256 = hashlib.sha256(PILOT_CODE_BUNDLE.read_bytes()).hexdigest()",
        "pathlib.PurePosixPath(member.filename).is_absolute()",
        'tempfile.mkdtemp(prefix="stage2b-pilot-code-")',
        'archive.read("bundle-manifest.json")',
        "archive.namelist() != expected_members",
        "actual_files != sorted(expected_members)",
        'hashlib.sha256(payload).hexdigest() != entry.get("sha256")',
        'MANIFEST_PATH = pathlib.Path("jspace-stage2b-pilot-v1.json")',
        "hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest()",
        'BUNDLE_ROOT / "tests/jspace/fixtures/stage2_manifest_digests.json"',
    ):
        assert required in source
    assert source.index("pf.check_ratification(") < source.index(
        'MANIFEST_PATH = pathlib.Path("jspace-stage2b-pilot-v1.json")'
    )


def test_the_ratification_gate_precedes_the_measurement_loop(notebook):
    """A guard after the loop is not a guard.

    The loop is located by what it *does* -- iterating the authorized manifest and
    capturing residuals -- not by a comment. Matching on prose would let a rename move
    this boundary silently, and it is the boundary between authoring and
    execution.
    """
    code = ["".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code"]
    gate = next(i for i, c in enumerate(code) if "pf.check_ratification(" in c)
    loop = next(
        i
        for i, c in enumerate(code)
        if 'for meta in manifest["prompts"]' in c and "capture_prompt(" in c
    )
    assert gate < loop, "the ratification gate must come before the measurement loop"


def test_authorization_precedes_every_heavy_or_data_path(notebook):
    code = ["".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code"]
    gate = next(i for i, cell in enumerate(code) if "pf.check_ratification(" in cell)
    for marker in (
        "subprocess.run(runtime_install_command",
        "MANIFEST_PATH =",
        "torch.cuda",
        "import jlens",
        "AutoModelForCausalLM.from_pretrained",
        "hf_hub_download",
        "capture_prompt(",
    ):
        path = next(i for i, cell in enumerate(code) if marker in cell)
        assert gate < path, f"authorization must precede {marker}"
    assert "pf.check_crossing_registry(" in code[gate]


def test_the_three_pilot_thresholds_ship_unset(source):
    """All three come from the Q6 pilot, none is guessed.

    check_ratification refuses a signature while any is None, which makes
    deferring a threshold and signing the ratification mutually exclusive --
    the inverse of Stage 2's mistake of setting a margin with no pilot.
    """
    for name in ("SPEC_MIN_EFFECT", "NTA_MIN_DENOMINATOR", "INTERACTION_MIN_EFFECT"):
        assert f"{name} = None" in source, f"{name} must ship unset"


def test_prompt_only_construction_is_pinned(source):
    """Open item 8, decided: Stage 2's construction unchanged."""
    assert 'PROMPT_ONLY_CONSTRUCTION = "input_embedding_decoded"' in source
    assert "get_input_embeddings()" in source, "must decode the token embedding"


def test_colab_runtime_dependencies_are_exactly_pinned(source):
    assert "git+{JLENS_REPO_URL}@{JLENS_COMMIT}" in source
    for name, version in {
        "transformers": "5.5.4",
        "huggingface_hub": "1.24.0",
        "numpy": "2.5.1",
        "scipy": "1.18.0",
        "safetensors": "0.8.0",
        "accelerate": "1.14.0",
        "torch": "2.13.0",
    }.items():
        assert f'"{name}": "{version}"' in source
        assert f'f"{name}=={{EXPECTED_RUNTIME_VERSIONS[' in source
    assert "transformers>=" not in source
    assert "EXPECTED_RUNTIME_VERSIONS" in source
    assert "RUNTIME_INSTALL_REQUIREMENTS" in source


def test_colab_binary_install_requires_restart_and_text_only_runtime(source):
    for required in (
        'RUNTIME_INSTALL_SCHEMA = "stage2b-colab-runtime-install/v2"',
        'RUNTIME_REMOVE_PACKAGES = ("torchvision",)',
        "subprocess.run(runtime_remove_command, check=True)",
        "subprocess.run(runtime_install_command, check=True)",
        "install_process_identity",
        "fresh_process_after_install",
        'raise RuntimeError("runtime restart required before package imports")',
        'importlib.util.find_spec("torchvision")',
        'torchvision_state = "absent"',
    ):
        assert required in source
    assert source.index(
        "runtime restart required before package imports"
    ) < source.index("import transformers")


def test_ratified_statistics_are_executable_but_cannot_emit_a_pilot_decision(notebook):
    document = "\n".join("".join(cell["source"]) for cell in notebook["cells"])
    for required in (
        "import stage2b_statistics as st",
        "st.materialize_pilot_nta(",
        "st.build_pilot_inference(",
        '"denominator_derivation"',
        '"inference"',
        '"guard_quantile": 0.05',
        '"bootstrap_iterations": 20_000',
        '"bootstrap_ci_level": 0.99',
        '"bootstrap_quantile_method": "linear"',
        '"bootstrap_bit_generator": "PCG64"',
    ):
        assert required in document
    for forbidden in (
        "cluster_bootstrap_median",
        "threshold_estimates",
        'artifact["gates"]',
        'artifact["decision"]',
    ):
        assert forbidden not in document


def test_the_flattering_floor_is_flagged_in_the_notebook(source):
    """A weak prompt_only makes absolute NTA read high. That has to be stated
    where someone reading results will see it, not only in the spec."""
    assert "DESCRIPTIVE ONLY" in source


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
    for loose_name in (
        "SAME_RUNTIME_REPEATS",
        "INFERENCE_SEEDS",
        "RANDOM_VECTOR_SEEDS",
    ):
        assert loose_name not in source


def test_aggregate_builder_has_no_scientific_gate_or_decision_api(source):
    assert '"registry"' in source
    assert '"disjointness"' in source
    assert '"descriptive"' in source
    assert "gates=None" not in source
    assert "decision=None" not in source
    assert 'artifact["gates"]' not in source
    assert 'artifact["decision"]' not in source
    assert 'if run_mode == "confirmatory"' not in source


def test_artifact_schema_matches_the_compact_producer():
    schema = ARTIFACT_SCHEMA.read_text()
    for required in (
        "descriptive.records",
        "floor_scores",
        "factorized_scores",
        "factorized_nta",
        "donor_assignments",
        "map_draws",
        "recipient_to_donor_sha256",
        "residual_sha256",
        "min_denominator",
        "unique_readout_count",
        "logical_cell_count",
    ):
        assert required in schema
    for stale in ("factorized_readouts", '"identity"', '"target"', '"floors"'):
        assert stale not in schema


def test_content_addressing_matches_stage_twos_scheme(source):
    """Byte-identical, so the two stages' artifacts are comparable objects."""
    assert "sort_keys=True, indent=2, ensure_ascii=False" in source
    assert '"xb"' in source


def test_token_counts_are_measured_not_read_from_the_manifest(source):
    assert "token_counts=token_counts" in source
    assert "tokenizer(" in source


def test_pilot_notebook_never_loads_the_confirmatory_manifest(source):
    """A pilot cannot claim holdout_accessed=false after reading all 200 texts."""
    assert "jspace-stage2b-pilot-v1.json" in source
    assert "jspace-stage2b-stimulus-v1.json" not in source
    assert "mf.select_partition(" not in source


def test_the_measurement_loop_exists_and_scores_against_the_target(source):
    """Writable now that both open decisions are made."""
    assert 'for meta in manifest["prompts"]' in source
    assert "ep.target_rank1" in source
    assert "ep.rank_score" in source
    assert "ep.allocate_wrong_layers" not in source
    assert "paired_difference_by_cluster" not in source


def test_model_argmax_target_is_bound_to_live_output_logits(source):
    for required in (
        '"target_derivation"',
        '"output_logits_sha256"',
        '"output_logits_dtype"',
        '"output_logits_shape"',
        '"max_logit"',
        '"argmax_tie_token_ids"',
        '"tie_break_rule": "lowest_token_id"',
        '"runtime_verifier_id"',
        '"runtime_verified": True',
        '"target_decision_sha256"',
        "ep.target_decision_sha256(",
        "validate_observation.verify_target_derivation_against_logits(",
    ):
        assert required in source
    assert "output_logits.numpy()" in source
    assert "torch.nonzero(" in source
    assert "output_logits == max_logit" in source


def test_measurement_executes_every_factorial_control(source):
    assert "ep.build_fit_broken_maps" in source
    assert "ep.select_wrong_activation" in source
    assert "ep.transport_with" in source
    assert "ep.materialize_crossed_factorials" in source
    assert "st.materialize_pilot_nta" in source
    assert "st.build_pilot_inference" in source


def test_crossing_registry_is_authorized_from_ratified_derivations(source):
    assert "BROKEN_MAP_DRAWS = []" not in source
    assert "WRONG_ACTIVATION_ASSIGNMENTS = []" not in source
    assert "BROKEN_MAP_DRAWS = None" in source
    assert "WRONG_ACTIVATION_ASSIGNMENTS = None" in source
    assert "BROKEN_MAP_SEED" not in source
    assert "WRONG_ACTIVATION_SEED" not in source
    assert "pf.check_crossing_registry(" in source


def test_layer_zero_and_input_embedding_floors_are_both_decoded(source):
    assert "record_at = sorted(set(SELECTED_LAYERS) | {0, final_layer})" in source
    assert "layer0_residual" in source
    assert "prompt_embedding" in source
    assert '"input_embedding_decoded"' in source
    assert '"layer0_residual_decoded"' in source
    assert '"sensitivity_minus_primary"' in source


def test_exact_eight_by_eight_crossing_is_factorized_losslessly(source):
    assert "for donor_entry in WRONG_ACTIVATION_ASSIGNMENTS" in source
    assert (
        "for map_entry, broken_map in zip(BROKEN_MAP_DRAWS, realized_maps, strict=True)"
        in source
    )
    assert '"correct_act_fitted_map"' in source
    assert '"correct_act_broken_map"' in source
    assert '"wrong_act_fitted_map"' in source
    assert '"wrong_act_broken_map"' in source
    assert 'crossed["unique_readout_count"] != 81' in source
    assert 'crossed["logical_cell_count"] != 64' in source


def test_crossing_records_all_ratified_provenance(source):
    for field in (
        '"donor_assignment_id"',
        '"seed_index"',
        '"seed_namespace"',
        '"seed_sha256"',
        '"bit_generator"',
        '"recipient_prompt_sha256"',
        '"source_prompt_sha256"',
        '"map_draw_id"',
        '"seed"',
        '"sha256"',
    ):
        assert field in source


def test_compact_producer_matches_validator_contract(notebook):
    """Inspect producer structure without executing notebook or experimental paths."""
    trees = [
        ast.parse("".join(cell["source"]))
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
        and not "".join(cell["source"]).lstrip().startswith(("%", "!"))
    ]
    nodes = [node for tree in trees for node in ast.walk(tree)]

    assignments = {
        target.id: node.value
        for node in nodes
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    donor_dict = next(
        arg
        for node in nodes
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "donor_assignments"
        and node.func.attr == "append"
        for arg in node.args
        if isinstance(arg, ast.Dict)
    )
    donor_fields = {
        key.value: value
        for key, value in zip(donor_dict.keys, donor_dict.values, strict=True)
        if isinstance(key, ast.Constant)
    }
    assert set(donor_fields) == {
        "donor_assignment_id",
        "seed_index",
        "seed_namespace",
        "seed_sha256",
        "seed",
        "bit_generator",
        "recipient_prompt_sha256",
        "source_prompt_sha256",
        "recipient_to_donor_sha256",
        "residual_sha256",
    }
    residual_hash = donor_fields["residual_sha256"]
    assert isinstance(residual_hash, ast.Call)
    assert isinstance(residual_hash.func, ast.Name)
    assert residual_hash.func.id == "array_sha256"
    assert len(residual_hash.args) == 1
    assert isinstance(residual_hash.args[0], ast.Name)
    assert residual_hash.args[0].id == "wrong"

    factorized_assignment = assignments["factorized_scores"]
    assert isinstance(factorized_assignment, ast.Call)
    score_transform = factorized_assignment.args[1]
    assert isinstance(score_transform, ast.Lambda)
    assert isinstance(score_transform.body, ast.Subscript)
    assert isinstance(score_transform.body.slice, ast.Constant)
    assert score_transform.body.slice.value == "s"

    record_dict = next(
        arg
        for node in nodes
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "raw_records"
        and node.func.attr == "append"
        for arg in node.args
        if isinstance(arg, ast.Dict)
    )
    record_fields = {
        key.value: value
        for key, value in zip(record_dict.keys, record_dict.values, strict=True)
        if isinstance(key, ast.Constant)
    }
    assert "floor_readouts" not in record_fields
    assert "factorized_readouts" not in record_fields
    assert {"floor_scores", "factorized_scores"} <= set(record_fields)
    assert "factorized_nta" not in record_fields

    floor_scores = record_fields["floor_scores"]
    assert isinstance(floor_scores, ast.Dict)
    floor_fields = {
        key.value: value
        for key, value in zip(floor_scores.keys, floor_scores.values, strict=True)
        if isinstance(key, ast.Constant)
    }
    assert set(floor_fields) == {
        "input_embedding_decoded",
        "layer0_residual_decoded",
        "output_decoded",
    }
    assert all(
        isinstance(value, ast.Subscript)
        and isinstance(value.slice, ast.Constant)
        and value.slice.value == "s"
        for value in floor_fields.values()
    )
    assert isinstance(record_fields["factorized_scores"], ast.Name)
    assert record_fields["factorized_scores"].id == "factorized_scores"

    build_aggregate = next(
        node
        for node in nodes
        if isinstance(node, ast.FunctionDef) and node.name == "build_aggregate"
    )
    artifact_dict = next(
        node.value
        for node in ast.walk(build_aggregate)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "artifact"
            for target in node.targets
        )
        and isinstance(node.value, ast.Dict)
    )
    artifact_fields = {
        key.value: value
        for key, value in zip(artifact_dict.keys, artifact_dict.values, strict=True)
        if isinstance(key, ast.Constant)
    }
    assert {"denominator_derivation", "inference", "descriptive"} <= set(
        artifact_fields
    )
    constants = artifact_fields["constants"]
    assert isinstance(constants, ast.Dict)
    assert [key.value for key in constants.keys] == [
        "min_denominator",
        "guard_quantile",
        "guard_quantile_method",
        "bootstrap_iterations",
        "bootstrap_ci_level",
        "bootstrap_quantile_method",
        "bootstrap_bit_generator",
    ]


def test_raw_scores_precede_one_two_stage_statistical_materialization(source):
    raw_append = source.index("raw_records.append(")
    materialize = source.index("st.materialize_pilot_nta(")
    inference = source.index("st.build_pilot_inference(")
    assert raw_append < materialize < inference
    assert source.count("st.materialize_pilot_nta(") == 1
    assert source.count("st.build_pilot_inference(") == 1
    assert source.rfind("capture_prompt(") < materialize
    assert '"factorized_nta"' not in source[raw_append:materialize]


def test_statistical_derivation_is_bound_to_code_and_runtime_numpy(source):
    assert "pathlib.Path(st.__file__).read_bytes()" in source
    assert "derivation_code_sha256=STATISTICS_CODE_SHA256" in source
    assert 'numpy_version=observed_runtime_versions["numpy"]' in source
    assert (
        'REGISTRY["NTA_MIN_DENOMINATOR"]["declared_value"] = NTA_MIN_DENOMINATOR'
        in source
    )
    assert 'REGISTRY["SPEC_MIN_EFFECT"]["declared_value"] = SPEC_MIN_EFFECT' in source
    assert (
        'REGISTRY["INTERACTION_MIN_EFFECT"]["declared_value"] = INTERACTION_MIN_EFFECT'
    ) in source


def test_tensor_contract_is_measured_and_checked(source):
    assert "pf.check_tensor_contracts(" in source
    assert '"residual_dtype": str(' in source
    assert '"jacobian_dtype": str(' in source
    assert '"decode_parity_max_abs"' in source
    assert '"rank_parity_verified": rank_parity_verified' in source
    assert '"primary_floor_id": "input_embedding_decoded"' in source
    assert '"sensitivity_floor_id": "layer0_residual_decoded"' in source


def test_every_realized_broken_map_carries_runtime_spectrum_evidence(source):
    assert "fitted_singular_values = ep.build_fit_broken_maps(" in source
    assert "fitted_singular_values=fitted_singular_values" in source
    assert 'if not spectrum_check["verified"]' in source
    assert '"spectrum_check": spectrum_check' in source


def test_rank_parity_calls_the_pinned_jlens_reference(source):
    assert "from jlens.vis import _ranks_of" in source
    assert "_ranks_of(rank_probe_logits, rank_probe_targets)" in source
    assert "ep.target_rank1(" in source
    assert '"rank_parity_verified": rank_parity_verified' in source


def test_pilot_is_explicit_and_confirmation_cannot_reuse_its_view(source):
    assert 'RUN_MODE = "pilot"' in source
    assert "PILOT_AUTHORIZED = False" in source
    assert "pf.check_ratification(" in source
    assert 'if RUN_MODE != "pilot"' in source
    assert "confirmation needs its own holdout view" in source


def test_aggregate_is_built_written_and_validated(source):
    assert "aggregate = build_aggregate(" in source
    assert "write_content_addressed(aggregate" in source
    assert "validate_observation.validate_stage2b_aggregate(" in source
    assert "expected_pilot_view=manifest" in source
    assert "expected_source=TRUSTED_SOURCE_IDENTITIES" in source
    assert "validation_errors" in source
    assert '"pilot_view_sha256": EXPECTED_PILOT_VIEW_SHA256' in source
    assert '"pilot_prompt_ids"' in source
    assert '"pilot_prompt_sha256s"' in source
    assert '"vocab_size": V' in source
    assert '"pinned_identities_matched": True' in source
    assert '"tensor_contracts_passed": True' in source
    assert '"crossing_registry_checked": True' in source
    assert '"primary_floor_id": "input_embedding_decoded"' in source
    assert '"sensitivity_floor_id": "layer0_residual_decoded"' in source
    assert '"content_hash_method": "dtype-shape-bytes-sha256-v1"' in source
    assert '"denominator_derivation": denominator_derivation' in source
    assert '"inference": inference' in source
    assert '"install_spec_sha256": install_spec_sha256' in source
    assert '"fresh_process_after_install": fresh_process_after_install' in source
    assert '"torchvision_state": torchvision_state' in source
    assert (
        '"notebook_sha256": AUTHORIZATION_RECORD["source"]["notebook_sha256"]' in source
    )
    assert (
        '"code_bundle_sha256": AUTHORIZATION_RECORD["source"]["code_bundle_sha256"]'
        in source
    )
    assert '"authorization_record_sha256": AUTHORIZATION_RECORD_SHA256' in source


def test_the_target_choice_is_marked_not_delegable(source):
    """Q3 defines what this study means by information. A pass under the argmax
    target must not be described as though it were information about the world."""
    assert "NOT delegable" in source
    assert "argmax" in source
