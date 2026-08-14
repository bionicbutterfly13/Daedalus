# Tasks: Primary-Floor Development Study

**Input**: Design documents from `specs/003-primary-floor-development/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/`, and `quickstart.md`

**Tests**: Required. The specification, plan, contracts, and quickstart require
CPU-only contract, corruption, regression, and notebook-source tests. Write each
story's tests first and observe the intended failures before implementation.

**Organization**: Tasks are grouped by user story so each story can be completed
and tested with synthetic data independently. No task authorizes real prompt
measurement, model access, GPU execution, artifact transfer, a revised pilot, or
confirmation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it changes different files and has no
  dependency on another incomplete task in the same group.
- **[Story]**: Maps the task to User Story 1, 2, or 3.
- Every task names its exact file or validation path.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm routing and establish the separate development-only source
and test surfaces without changing the completed pilot contracts.

- [ ] T001 Verify `.specify/feature.json` resolves `specs/003-primary-floor-development`, confirm branch `003-primary-floor-development`, and verify the editable import resolves `/Volumes/Asylum/Daedalus/EvoScientist/__init__.py`
- [ ] T002 [P] Create development-only module scaffolds with scope docstrings and no Torch, model, network, or GPU imports in `EvoScientist/skills/jspace-research-operations/scripts/stage2b_development_manifest.py`, `EvoScientist/skills/jspace-research-operations/scripts/stage2b_development_analysis.py`, `EvoScientist/skills/jspace-research-operations/scripts/stage2b_development_preflight.py`, and `EvoScientist/skills/jspace-research-operations/scripts/validate_stage2b_development.py`
- [ ] T003 [P] Create test module scaffolds and shared synthetic factories in `tests/jspace/test_stage2b_development_manifest.py`, `tests/jspace/test_stage2b_development_analysis.py`, `tests/jspace/test_stage2b_development_preflight.py`, `tests/jspace/test_stage2b_development_validator.py`, `tests/jspace/test_stage2b_development_decision.py`, `tests/jspace/test_stage2b_development_notebook.py`, and `tests/jspace/stage2b_development_fixtures.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish canonical identity, stable failures, false-by-default
boundaries, and recursive schema validation shared by every story.

**Critical**: Complete this phase before any user-story implementation.

### Tests first

- [ ] T004 [P] Add failing tests for canonical JSON, self-digest exclusion, exclusive immutable writes, and stable schema constants in `tests/jspace/test_stage2b_development_manifest.py`
- [ ] T005 [P] Add failing import-light tests for `DevelopmentPreflightError`, false-by-default boundaries, forbidden pilot/confirmation/transfer fields, and stable first-failure codes in `tests/jspace/test_stage2b_development_preflight.py`
- [ ] T006 [P] Add failing tests for recursive unknown-field rejection, mandatory external expected identities, and rejection of self-authentication in `tests/jspace/test_stage2b_development_validator.py`

### Shared implementation

- [ ] T007 Implement canonical JSON, SHA-256, immutable exclusive-write, and development schema constants in `EvoScientist/skills/jspace-research-operations/scripts/stage2b_development_manifest.py` until T004 passes
- [ ] T008 Implement the stable error type, exact false-boundary checks, forbidden-field checks, and import-light identity comparison primitives in `EvoScientist/skills/jspace-research-operations/scripts/stage2b_development_preflight.py` until T005 passes
- [ ] T009 Implement recursive allowed-field helpers and externally supplied source-identity validation in `EvoScientist/skills/jspace-research-operations/scripts/validate_stage2b_development.py` until T006 passes

**Checkpoint**: Canonical identity, boundary enforcement, and validator foundations
are CPU-tested without scientific prompt text or runtime execution.

---

## Phase 3: User Story 1 - Freeze a Lawful Development Corpus (Priority: P1) MVP

**Goal**: Produce and validate a synthetic frozen 29-block manifest whose 580
candidates are balanced, content-addressed, disjoint through digest-only checks,
and impossible to select or mutate from measured outcomes.

**Independent Test**: `tests/jspace/test_stage2b_development_manifest.py` builds a
synthetic 29×20 manifest against a synthetic 200-digest sealed registry, verifies
zero exact and normalized overlap, and proves post-freeze or outcome-driven
mutation fails. It does not materialize the real scientific registry or corpus.

### Tests first

- [ ] T010 [P] [US1] Create a clearly synthetic, text-free 200-entry exact-and-normalized digest registry fixture in `tests/jspace/fixtures/stage2b_scientific_prompt_digests.json`
- [ ] T011 [US1] Add failing positive contract tests for 29 blocks, 20 candidates per block, four candidates per category, 580 unique candidates, deterministic seeds, stable IDs, and canonical block and manifest digests in `tests/jspace/test_stage2b_development_manifest.py`
- [ ] T012 [US1] Add failing corruption tests for exact overlap, normalized overlap, duplicate IDs or digests, block imbalance, duplicate seeds, outcome inputs, unfrozen rules, collision-rule drift, and post-freeze mutation in `tests/jspace/test_stage2b_development_manifest.py`

### Implementation

- [ ] T013 [US1] Implement proposed-status study constants, deterministic block seed derivation, generation-rule records, template-family records, and balanced slot schedules in `EvoScientist/skills/jspace-research-operations/scripts/stage2b_development_manifest.py`
- [ ] T014 [US1] Implement candidate and block builders with exact IDs, parameter digests, UTF-8 byte counts, exact digests, normalized digests, category closure, and 29×20 accounting in `EvoScientist/skills/jspace-research-operations/scripts/stage2b_development_manifest.py`
- [ ] T015 [US1] Implement digest-only exclusion-registry binding, exact and normalized collision checks, and the frozen deterministic pre-freeze next-seed rule in `EvoScientist/skills/jspace-research-operations/scripts/stage2b_development_manifest.py`
- [ ] T016 [US1] Implement `check_development_manifest` and `check_template_sampling_contract` with independent expected digests, recursive field closure, outcome-input rejection, and stable failure codes in `EvoScientist/skills/jspace-research-operations/scripts/stage2b_development_preflight.py`
- [ ] T017 [US1] Implement frozen-manifest validation and exclusive content-addressed persistence that refuses byte-different path reuse in `EvoScientist/skills/jspace-research-operations/scripts/stage2b_development_manifest.py`
- [ ] T018 [US1] Add an end-to-end synthetic freeze and disjointness audit covering every US1 acceptance scenario and edge case in `tests/jspace/test_stage2b_development_manifest.py`
- [ ] T019 [US1] Run `uv run pytest tests/jspace/test_stage2b_development_manifest.py -v` and confirm the independent US1 criteria without reading `j-space-lab/jspace-stage2b-stimulus-v1.json`

**Checkpoint**: User Story 1 is independently functional with synthetic data. No
real development corpus, scientific digest registry, authorization record, or
runtime artifact exists.

---

## Phase 4: User Story 2 - Compare the Five Live Explanations (Priority: P2)

**Goal**: Recompute per-block dual-floor guard geometry, complete candidate
accounting, and the frozen block-aware H1-H5 descriptive analyses without
selecting a winner or favorable floor.

**Independent Test**: Synthetic evidence containing all 580 candidates and 2,320
candidate-layer loci reproduces 29 guards, both-floor eligibility, per-layer
coverage, leave-one-block-out H1-H3 analyses, paired H4, block-aware H5, explicit
missingness, and floor dependence.

### Tests first

- [ ] T020 [P] [US2] Add failing tests for 80-denominator per-block guard derivation, one guard applied to both floors, strict-greater-than eligibility, 18/20 and 3/4 coverage, and exact 29-block reliability in `tests/jspace/test_stage2b_development_analysis.py`
- [ ] T021 [P] [US2] Add failing evidence-schema tests for 580-candidate and 2,320-locus accounting, explicit missingness, recursive unknown fields, external identities, forbidden scientific outputs, and floor-dependence closure in `tests/jspace/test_stage2b_development_validator.py`
- [ ] T022 [US2] Add failing tests for H1-H3 leave-one-block-out group ablations, H4 paired floor differences and discordance, H5 category lower tails and block outcomes, exact feature closure, and defined/undefined/stopped states in `tests/jspace/test_stage2b_development_analysis.py`

### Implementation

- [ ] T023 [US2] Implement per-block 0.05 linear guard derivation from exactly 80 retained primary denominators and dual-floor denominator, margin, eligibility, and exclusion records in `EvoScientist/skills/jspace-research-operations/scripts/stage2b_development_analysis.py`
- [ ] T024 [US2] Implement per-floor, per-layer 18/20 and 3/4 coverage, block success, complete 580-candidate accounting, 2,320-locus accounting, and explicit missingness propagation in `EvoScientist/skills/jspace-research-operations/scripts/stage2b_development_analysis.py`
- [ ] T025 [US2] Implement the prespecified H1-H3 full model, feature-group ablations, leave-one-block-out folds, predictive-loss records, and bounded descriptive interpretations in `EvoScientist/skills/jspace-research-operations/scripts/stage2b_development_analysis.py`
- [ ] T026 [US2] Implement H4 paired denominator and guard-margin summaries, both discordance directions, H5 arithmetic-versus-other lower-tail summaries, and retained block outcomes in `EvoScientist/skills/jspace-research-operations/scripts/stage2b_development_analysis.py`
- [ ] T027 [US2] Implement the `jspace-primary-floor-development-evidence/v1` aggregate builder with exact source blocks, candidate records, 29 guards, coverage, H1-H5, floor dependence, stop records, and evidence-class-1 boundaries in `EvoScientist/skills/jspace-research-operations/scripts/stage2b_development_analysis.py`
- [ ] T028 [US2] Implement independent recomputation of manifest linkage, candidate and locus accounting, all guards, both-floor statuses, coverage, H1-H5 closure, floor dependence, stop conditions, and decision-input identity in `EvoScientist/skills/jspace-research-operations/scripts/validate_stage2b_development.py`
- [ ] T029 [US2] Extend manifest and preflight validation for exact H1-H5 predictions, feature names, comparison methods, falsifiers, missingness policy, and prohibition on undeclared runtime features in `EvoScientist/skills/jspace-research-operations/scripts/stage2b_development_preflight.py`
- [ ] T030 [US2] Add an end-to-end synthetic 580×4 analysis test covering every US2 acceptance scenario, including primary/sensitivity disagreement and retained exclusions, in `tests/jspace/test_stage2b_development_analysis.py`
- [ ] T031 [US2] Run `uv run pytest tests/jspace/test_stage2b_development_analysis.py tests/jspace/test_stage2b_development_validator.py -v` and confirm the independent US2 criteria

**Checkpoint**: User Story 2 is independently functional on synthetic evidence.
No H1-H5 result is treated as a scientific gate or mechanism winner.

---

## Phase 5: User Story 3 - Make a Bounded Next-Study Decision (Priority: P3)

**Goal**: Produce exactly one validated outcome, review readiness or stop, while
keeping all execution, pilot, confirmation, threshold, transfer, and evidence
promotion boundaries false.

**Independent Test**: A synthetic all-success packet returns review readiness
only; one failed block, incomplete accounting, floor disagreement, identity
failure, forbidden field, or universal stop returns the correct stop class. The
unexecuted notebook fails before model or GPU access.

### Tests first

- [ ] T032 [P] [US3] Add failing all-success, one-block-failure, primary-only-success, incomplete-accounting, unresolved-H1-H5, and stop-without-interpretation decision tests in `tests/jspace/test_stage2b_development_decision.py`
- [ ] T033 [P] [US3] Add failing tests for complete external source identities, sampling-contract enforcement, absence of a shipped authorization record, and rejection of pilot-authorization reuse in `tests/jspace/test_stage2b_development_preflight.py`
- [ ] T034 [P] [US3] Add failing notebook-source tests for valid unexecuted JSON, false authorization flags, preflight-before-model ordering, digest-only exclusion input, no pilot or confirmation view, no transfer cell, and no scientific decision in `tests/jspace/test_stage2b_development_notebook.py`

### Implementation

- [ ] T035 [US3] Implement exact reliability recomputation, universal-stop precedence, the two permitted outcomes, bounded reason classes, and the `jspace-primary-floor-development-decision/v1` packet builder in `EvoScientist/skills/jspace-research-operations/scripts/stage2b_development_analysis.py`
- [ ] T036 [US3] Complete development identity, sampling, boundary, and future-authorization contract validators while shipping no authorization record or automatic launch path in `EvoScientist/skills/jspace-research-operations/scripts/stage2b_development_preflight.py`
- [ ] T037 [US3] Implement recursive decision-packet validation, external manifest/evidence identities, all-success reliability recomputation, forbidden-field rejection, and review-only semantics in `EvoScientist/skills/jspace-research-operations/scripts/validate_stage2b_development.py`
- [ ] T038 [US3] Add only the narrow development-schema dispatch needed to call the separate validator without changing existing Stage 2b validation behavior in `EvoScientist/skills/jspace-research-operations/scripts/validate_observation.py`
- [ ] T039 [US3] Create the thin, unexecuted, authorization-false runtime source with tested-module imports and fail-before-model ordering in `j-space-lab/jspace_colab_stage2b_primary_floor_development.ipynb`
- [ ] T040 [US3] Add integrated corruption cases for forbidden pilot thresholds, confirmation fields, transfer claims, self-attested identities, missing H1-H5 records, and attempted pilot-authorization reuse in `tests/jspace/test_stage2b_development_decision.py` and `tests/jspace/test_stage2b_development_notebook.py`
- [ ] T041 [US3] Run `uv run pytest tests/jspace/test_stage2b_development_preflight.py tests/jspace/test_stage2b_development_decision.py tests/jspace/test_stage2b_development_notebook.py tests/jspace/test_stage2b_development_validator.py -v` and confirm the independent US3 criteria

**Checkpoint**: All three stories are independently CPU-testable. The positive
outcome authorizes independent preregistration review only.

---

## Phase 6: Polish & Cross-Cutting Verification

**Purpose**: Prove feature integration, preserve completed Stage 2b behavior,
obtain adversarial review, update durable status, and stop before execution.

- [ ] T042 Run the existing Stage 2b regression gate over `tests/jspace/test_stage2b_manifest.py`, `tests/jspace/test_stage2b_endpoint.py`, `tests/jspace/test_stage2b_statistics.py`, `tests/jspace/test_stage2b_preflight.py`, `tests/jspace/test_stage2b_validator.py`, `tests/jspace/test_stage2b_notebook.py`, `tests/jspace/test_stage2b_pilot_bundle.py`, `tests/jspace/test_stage2b_pilot_launch.py`, and `tests/jspace/test_stage2b_pilot_harness.py`
- [ ] T043 Run `uv run ruff check` and `uv run ruff format --check` over `EvoScientist/skills/jspace-research-operations/scripts/` and `tests/jspace/`, preserving content-addressed files under `j-space-lab/`
- [ ] T044 Run the focused feature gate over `tests/jspace/test_stage2b_development_manifest.py`, `tests/jspace/test_stage2b_development_analysis.py`, `tests/jspace/test_stage2b_development_preflight.py`, `tests/jspace/test_stage2b_development_validator.py`, `tests/jspace/test_stage2b_development_decision.py`, and `tests/jspace/test_stage2b_development_notebook.py`
- [ ] T045 Run `uv run pytest tests/jspace -v` and report this full J-space result separately from the focused and regression gates in `specs/003-primary-floor-development/implementation-review.md`
- [ ] T046 Execute every CPU-only validation step in `specs/003-primary-floor-development/quickstart.md`, verify Markdown links and ordinary notebook-cell parsing, and run `git diff --check`
- [ ] T047 Obtain an independent adversarial review of the exact implementation against `specs/003-primary-floor-development/spec.md`, `specs/003-primary-floor-development/plan.md`, `specs/003-primary-floor-development/contracts/`, and the changed source, then record claim-by-claim PASS/FAIL findings in `specs/003-primary-floor-development/implementation-review.md`
- [ ] T048 Resolve every actionable review finding in the named source or test file, rerun T042-T046, and record the superseding evidence in `specs/003-primary-floor-development/implementation-review.md`; if no finding exists, record that no remediation was required
- [ ] T049 Update `.specify/memory/project-state.md` with the verified feature-003 implementation status, exact checks, and remaining ratification and execution gates without claiming a real corpus or run
- [ ] T050 Perform the final boundary audit and record in `specs/003-primary-floor-development/implementation-review.md` that no real scientific prompt registry, frozen corpus, authorization record, model/GPU run, bundle, launch packet, artifact transfer, revised pilot, confirmation access, threshold, or evidence promotion was created

---

## Dependencies & Execution Order

### Phase dependencies

- **Phase 1 Setup**: Starts immediately. T001 precedes T002 and T003; T002 and
  T003 can then run in parallel.
- **Phase 2 Foundational**: Depends on Phase 1. T004-T006 can run in parallel;
  each corresponding implementation task T007-T009 follows its failing test.
- **Phase 3 US1**: Depends on Phase 2. This is the MVP and may complete without
  US2 or US3.
- **Phase 4 US2**: Depends on Phase 2. It is independently testable with the
  synthetic factories, although normal priority order places it after US1.
- **Phase 5 US3**: Depends on Phase 2. Its isolated decision tests use synthetic
  validated evidence; end-to-end integration depends on completed US1 and US2.
- **Phase 6 Polish**: Depends on all three stories.

### User-story dependency graph

```text
Setup -> Foundation -> US1 (frozen synthetic manifest)
                    -> US2 (synthetic H1-H5 evidence)
                    -> US3 (synthetic bounded decision)

US1 + US2 + US3 -> integrated validation -> adversarial review -> boundary stop
```

### Within User Story 1

1. T010 creates the synthetic digest-only fixture.
2. T011-T012 must fail for the intended reasons before T013.
3. T013-T017 implement the manifest and preflight path in dependency order.
4. T018 supplies end-to-end acceptance coverage.
5. T019 is the independent checkpoint.

### Within User Story 2

1. T020 and T021 can run in parallel; T022 follows T020 in the same test file.
2. T023-T027 build guard, coverage, hypotheses, and evidence in order.
3. T028-T029 independently close validator and preflight contracts.
4. T030 integrates the full synthetic population.
5. T031 is the independent checkpoint.

### Within User Story 3

1. T032-T034 can run in parallel and must fail before implementation.
2. T035-T039 implement decision, preflight, validator, dispatch, and notebook in
   dependency order.
3. T040 closes corruption coverage.
4. T041 is the independent checkpoint.

## Parallel Opportunities

- T002 and T003 operate on separate source and test trees after T001.
- T004, T005, and T006 add foundational tests in separate files.
- T010 can prepare the synthetic digest registry while US1 test cases are being
  designed, but T011 must not assume it exists until T010 completes.
- T020 and T021 cover analysis and validator contracts in separate files.
- T028 and T029 can proceed in parallel after the analysis record shape is fixed.
- T032, T033, and T034 cover decision, preflight, and notebook surfaces in
  separate files.
- US1, US2, and the isolated portion of US3 can be assigned independently after
  Foundation, with final integration deferred until all three complete.

## Parallel Example: User Story 1

```text
Task T010: Create tests/jspace/fixtures/stage2b_scientific_prompt_digests.json
Task T011: Draft positive manifest cases in tests/jspace/test_stage2b_development_manifest.py after T010
```

The fixture task can be assigned separately, but the manifest tests consume its
finished schema and therefore start after it.

## Parallel Example: User Story 2

```text
Task T020: Guard, eligibility, coverage, and reliability tests in test_stage2b_development_analysis.py
Task T021: Evidence schema and recursive validator tests in test_stage2b_development_validator.py
```

## Parallel Example: User Story 3

```text
Task T032: Decision tests in test_stage2b_development_decision.py
Task T033: Preflight and authorization-boundary tests in test_stage2b_development_preflight.py
Task T034: Notebook source-boundary tests in test_stage2b_development_notebook.py
```

## Implementation Strategy

### MVP first: User Story 1 only

1. Complete Setup and Foundation.
2. Complete T010-T019.
3. Stop and validate the synthetic frozen-manifest path independently.
4. Do not materialize the real 200-prompt digest registry or development corpus.

The MVP proves a lawful corpus can be represented, frozen, and audited without
measuring or selecting prompts.

### Incremental delivery

1. **US1**: Synthetic manifest freezing and disjointness.
2. **US2**: Synthetic dual-floor H1-H5 evidence and complete accounting.
3. **US3**: Synthetic stop-or-review decision and authorization-false notebook.
4. **Integration**: Existing Stage 2b regressions, full J-space tests, adversarial
   review, project-state update, and final boundary audit.

### Ratification boundary

These tasks may implement and CPU-test the proposed design. Before any real
development corpus is generated or measured, Dr. Mani must separately ratify the
29-block generator families, seed namespace, feature definitions, block count,
decision rule, and exact source identities. Model or GPU execution requires a
separate authorization after that ratification.

## Deferred Work, Not Tasks in This Feature

- Materializing the real digest registry from the 200 scientific prompts.
- Generating or freezing the real 580-candidate development corpus.
- Creating development bundle or launch-preparation writers.
- Creating or approving an authorization record.
- Loading the model or lens, allocating a GPU, or executing the notebook.
- Writing, transferring, or downloading a real development evidence artifact.
- Revising a generator after seeing results.
- Running a revised Stage 2b pilot or accessing confirmation.
- Deriving thresholds, promoting evidence, or beginning Stage 3.

## Notes

- `[P]` tasks change different files and have no incomplete dependency in the
  same group.
- Story tests must be written and observed failing before implementation.
- Existing Stage 2b tests are preserved and run separately from feature tests.
- Content-addressed evidence under `j-space-lab/` is never reformatted.
- Commit only if Dr. Mani explicitly requests it. Do not push or open a pull
  request under this task list.
