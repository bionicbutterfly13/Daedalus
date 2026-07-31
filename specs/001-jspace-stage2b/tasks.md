# Tasks: Stage 2b J-space discrimination recovery

**Inputs**: [spec.md](./spec.md), [plan.md](./plan.md),
[data-model.md](./data-model.md), and [contracts/](./contracts/)

**Boundary**: the explicitly authorized excluded-input model/lens smoke is complete.
No pilot, confirmation, artifact transfer, commit, or scientific decision.

## Status legend

- `[x]` source/doc change observed in the recovery worktree; not automatically
  VERIFIED.
- `[ ]` pending or not yet evidenced by a fresh test result.
- RATIFIED and IMPLEMENTED are tracked independently.

## A. Ratified endpoint and crossing core

- [x] T057 Implement pure `dual_floor_nta` with
  `input_embedding_decoded`, `layer0_residual_decoded`, and the named
  `sensitivity_minus_primary` result.
- [x] T058 Add synthetic endpoint tests for both floors and floor-specific
  exclusion behavior.
- [x] T059 Implement `materialize_crossed_factorials` over the compact factorization:
  1 shared + 8 map-indexed + 8 donor-indexed + 64 donor×map = 81 unique readouts.
- [x] T060 Add synthetic tests that materialize all 64 logical four-cell factorials
  and reject incomplete, extra, or mis-keyed dimensions.
- [x] T061 Preserve donor assignment ID/digest and broken-map draw ID/seed/hash in
  the factorized contract.

## B. Guarded preflight and authorization

- [x] T062 Add `check_crossing_registry` for exactly eight unique donor assignments
  and eight unique map draws with non-empty IDs and unique integer seeds.
- [x] T063 Ship `WRONG_ACTIVATION_ASSIGNMENTS = []` and
  `BROKEN_MAP_DRAWS = []`; do not author seed vectors.
- [x] T064 Keep inference constants unset and execution signatures false while their
  methods and values remain unratified.
- [x] T065 Add failure-path tests for missing, duplicate, malformed, or wrong-sized
  crossing registries.

## C. Synthetic harness

- [x] T066 Implement a CPU-only synthetic 8×8 harness using prompts disjoint from
  the real manifest.
- [x] T067 Exercise transport, control construction, both floors, compact 81-readout
  persistence, and 64-combination reconstruction.
- [x] T068 Ensure the smoke artifact cannot contain confirmatory gates or a
  scientific decision.
- [x] T069 Observe the dedicated harness test result before describing the harness
  as VERIFIED (`8 passed`).

## D. Notebook recovery

- [x] T070 Recovery edits wire the notebook source to `dual_floor_nta`,
  `materialize_crossed_factorials`, and guarded crossing vectors.
- [x] T071 Run and observe `tests/jspace/test_stage2b_notebook.py` before claiming
  notebook source-contract verification (`28 passed`).
- [x] T072 Confirm through the static notebook tests that it contains no
  author-chosen donor/map seed vectors and no enabled execution signature.

## E. Primary validator recovery

- [x] T073 Recovery edits add compact dual-floor and 8×8 artifact validation paths.
- [x] T074 Run and observe `tests/jspace/test_stage2b_validator.py` before claiming
  validator verification (`44 passed`).
- [x] T075 Confirm validator reconstruction checks 81 unique readouts, 64 logical
  combinations, both floor results, named difference, prompt-pair linkage, and
  persisted provenance identity. Raw tensor/map content-hash parity remains a
  runtime-smoke obligation.
- [x] T076 Confirm no validator branch elevates an unratified inference proposal to
  a required scientific rule.

## F. Documentation contract

- [x] T077 Replace stale legacy count, condition-count, and notebook-CI claims.
- [x] T078 Align spec, plan, quickstart, data model, artifact schema, constant
  registry, and preflight API on the 81-readout/64-combination dual-floor contract.
- [x] T079 Label RATIFIED, IMPLEMENTED, and VERIFIED independently.
- [x] T080 State exact uncertainty, bootstrap, intervals, thresholds, multiplicity,
  seed vectors, and execution as unratified.
- [x] T081 Run final consistency searches and inspect the exact eight-file diff.

## G. Independent-review contract repair

- [x] T082 Reproduce Archimedes' finding that the prior validator accepted an
  incomplete execution envelope and arbitrary well-formed content hashes.
- [x] T083 Require the pinned model/lens/runtime, authorization, preflight, design,
  source-manifest, and canonical pilot-view envelope.
- [x] T084 Require exact 20-prompt × 4-layer locus coverage with category/layer
  binding and run-wide donor/map identity consistency.
- [x] T085 Add the ratified pilot-view file to the recovery worktree and verify its
  SHA-256 is
  `5bef8316f72682a628fc1240bf6068a91aa7c8a330377206cbd9145434b797e4`.
- [x] T086 Add adversarial validator tests for omitted envelope fields, false
  authorization/preflight checks, unpinned views, mismatched loci/categories,
  out-of-view donors, and cross-record seed/hash conflicts.
- [x] T087 Observe the repaired validator/notebook surface passing (`100 passed`).
- [x] T088 Run the complete J-space suite, Ruff, format, diff, and full repository
  suite after the documentation repair: `325 passed`; `3383 passed, 12 skipped`;
  Ruff passed; 405 files formatted; `git diff --check` passed.
- [x] T089 Obtain a fresh independent Archimedes correspondence review. Verdict:
  CONDITIONAL ACCEPT with three bounded correspondence repairs.
- [x] T090 Reproduce and repair missing `lens.source_layers` binding, cross-layer
  donor-source drift, and unknown compact-field acceptance.
- [x] T091 Run fresh adversarial, J-space, full-repository, formatting, and diff
  verification after T090: all three probes rejected; `332 passed`; `3390 passed,
  12 skipped`; Ruff passed; 405 files formatted; `git diff --check` passed.
- [x] T092 Obtain Archimedes' closure verdict before preparing the Colab
  integration-smoke packet. Verdict: ACCEPT; no scientific/GPU gate changed.

## H. Excluded-input Colab integration-smoke preparation

- [x] T093 Define a runtime-only smoke schema with nine hash-bound excluded inputs,
  smoke-only donor/map seeds, runtime/VRAM measurements, 81/64 counts, retention,
  and rejection of scientific fields.
- [x] T094 Build a deterministic code-only bundle containing the endpoint,
  preflight, and integration-smoke modules; exclude all prompts, credentials,
  model/lens weights, and runtime artifacts.
- [x] T095 Generate a canonical unexecuted Colab notebook that fails before
  downloads while unauthorized, binds the bundle hash, probes all selected layers,
  runs one full excluded-input crossing, and refuses artifact transfer.
- [x] T096 Add CPU/static tests for disjoint inputs, smoke-only donor coverage,
  content hashes, report boundaries, deterministic packaging, ordinary-cell
  parsing, canonical false authorization, scientific-input absence, 81/64 calls,
  runtime/VRAM capture, immutable report writing, and transfer refusal (`25
  passed`).
- [x] T097 Record the exact source identities and launch/stop/acceptance conditions
  in `contracts/integration-smoke-launch-packet.md`.
- [x] T098 Run complete post-preparation verification and an independent
  Archimedes launch-packet review: `357 passed`; `3415 passed, 12 skipped`; Ruff
  and format clean; diff clean; deterministic rebuilds matched; verdict ACCEPT.
- [x] T100 Add a canonical-hash-bound disposable launch-copy tool that requires an
  authorization-record SHA-256, changes only smoke authorization plus metadata,
  preserves transfer=false, rejects executed or altered canonical source, and
  refuses overwrite (`14 passed` across launch-copy/notebook tests).
- [x] T101 Run complete post-launch-copy-tool verification: `364 passed`; `3422
  passed, 12 skipped`; Ruff passed; 413 files formatted; `git diff --check`
  passed; canonical notebook and bundle hashes unchanged.
- [x] T102 Obtain a bounded Archimedes review of the launch-copy tool and revised
  packet before requesting authorization. Verdict: ACCEPT; blockers: none.
- [x] T099 Ask Dr. Mani for the exact separate authorization quoted in the launch
  packet. Do not open Colab or allocate a GPU before it is granted.

## I. First authorized integration-smoke attempt and restart repair

- [x] T103 Execute only the hash-authorized notebook/bundle on one Colab T4 and
  stop without live repair when model loading fails with a mixed NumPy module
  state after the pinned install.
- [x] T104 Add a process-identity-bound install sentinel and require a fresh
  Colab Python process before importing NumPy, Torch, Transformers, or Jacobian
  Lens.
- [x] T105 Record and validate the install-specification digest and fresh-process
  proof in the runtime-only compatibility report.
- [x] T106 Regenerate the deterministic bundle and canonical notebook; observe
  `37 passed` focused, `369 passed` J-space, `3427 passed, 12 skipped`
  repository-wide, Ruff/format/diff clean, deterministic rebuild identity, and
  independent Archimedes verdict ACCEPT with no blockers.
- [x] T107 Replace the launch packet identities and request a new exact
  hash-specific GPU authorization. The request was issued with the repaired
  notebook and bundle identities; the earlier authorization does not cover them.
- [x] T108 Obtain Dr. Mani's exact repaired-source authorization, create the
  hash-bound launch copy, upload only that notebook and bundle, and pass the
  one-T4 15,360 MiB bundle/capacity gate without accessing scientific inputs.
- [x] T109 Reattach to the same Colab notebook/runtime, observe the completed
  install, restart the same session, prove a fresh Python process, and pass the
  package/source/commit/revision/excluded-input checks without re-uploading or
  allocating a second runtime.
- [x] T110 Resolve the exact Torch/Torchvision compatibility contract in
  `j-space-lab/jspace_colab_stage2b_integration_smoke.ipynb` and the smoke test
  packet, obtain fresh exact-hash authorization, and complete the bounded
  excluded-input runtime smoke. The authorized run used one Tesla T4 with
  15,360 MiB, verified the pinned model/lens runtime, completed the 81-readout
  crossing in 1.141 seconds with 4.074 GiB peak allocated VRAM, retained report
  SHA-256
  `71b58ce846d319c6c26562a7765c67ab3a3468609f67306d8a767ea8f73a477c`
  in Colab, and left the transfer cell unexecuted. No pilot or confirmation
  input was accessed.

## J. Pilot-readiness adversarial contract repair

- [x] T111 Record the successful runtime-only smoke and its strict limits in
  `.specify/memory/project-state.md`,
  `specs/001-jspace-stage2b/contracts/integration-smoke-launch-packet.md`, and
  `docs/wiki/Runtime-Failure-Lab-Notes.md` without transferring the Colab report.
- [x] T112 Add adversarial target-binding tests in
  `tests/jspace/test_stage2b_validator.py` and notebook source-contract tests in
  `tests/jspace/test_stage2b_notebook.py` that fail when only `target_id`,
  output-logits identity, or tie evidence is corrupted.
- [x] T113 Implement cryptographically bound model-argmax derivation evidence in
  `j-space-lab/jspace_colab_stage2b_discrimination.ipynb`,
  `specs/001-jspace-stage2b/contracts/artifact-schema.md`,
  `specs/001-jspace-stage2b/data-model.md`, and
  `EvoScientist/skills/jspace-research-operations/scripts/validate_observation.py`.
- [x] T114 Add excluded-floor reconstruction tests in
  `tests/jspace/test_stage2b_endpoint.py` and
  `tests/jspace/test_stage2b_validator.py` for fully and partially null
  floor-specific NTA trees.
- [x] T115 Distinguish absent factorized components from present excluded/null
  results in
  `EvoScientist/skills/jspace-research-operations/scripts/stage2b_endpoint.py`
  and preserve complete logical 8×8 coverage through validator recomputation.
- [x] T116 Add recursive fail-closed schema tests in
  `tests/jspace/test_stage2b_validator.py` for unknown top-level and nested
  fields, including synonymous threshold, inference, gate, and decision names.
- [x] T117 Enforce explicit allowed-field sets at every normative artifact object
  level in
  `EvoScientist/skills/jspace-research-operations/scripts/validate_observation.py`
  and align `specs/001-jspace-stage2b/contracts/artifact-schema.md`.
- [x] T118 Add and implement one complete external ratification/authorization
  record consumed by
  `j-space-lab/jspace_colab_stage2b_discrimination.ipynb` and
  `EvoScientist/skills/jspace-research-operations/scripts/stage2b_preflight.py`,
  with failure-path coverage in `tests/jspace/test_stage2b_notebook.py` and
  `tests/jspace/test_stage2b_preflight.py`.
- [x] T119 Add `rank_parity_verified` and exact floor-identity enforcement to
  `check_tensor_contracts()` in
  `EvoScientist/skills/jspace-research-operations/scripts/stage2b_preflight.py`
  and cover both failure codes in `tests/jspace/test_stage2b_preflight.py`.
- [x] T120 Remove or mechanically quarantine unratified exclusion aggregation and
  wrong-layer allocation policy from executable pilot paths in
  `EvoScientist/skills/jspace-research-operations/scripts/stage2b_endpoint.py`,
  `j-space-lab/jspace_colab_stage2b_discrimination.ipynb`, and their focused
  tests without selecting replacement scientific policy.
- [x] T121 Reconcile `specs/001-jspace-stage2b/plan.md`,
  `specs/001-jspace-stage2b/quickstart.md`,
  `specs/001-jspace-stage2b/contracts/preflight-api.md`, and this ledger with
  the repaired producer/validator behavior.
- [x] T122 Run focused adversarial tests, the complete J-space suite, full
  repository suite, Ruff lint/format, notebook parsing, and `git diff --check`
  from `/Volumes/Asylum/archimedes-recovery-jspace-stage2b`: `408 passed`
  J-space; `3466 passed, 12 skipped` repository-wide on the final clean rerun; Ruff
  clean; 413 files formatted; 53 ordinary cells parsed across seven retained
  notebooks; diff check clean. One unrelated TUI teardown race appeared once in
  the first full run, passed twice in isolation, and did not recur in the clean
  full-suite rerun.
- [x] T123 Freeze the repaired source state and obtain an independent adversarial
  review before preparing any statistical ratification or pilot authorization
  request. The 69-file, 7,823-byte review manifest had SHA-256
  `033d61168839650ba2f28f0fe8fec9daf721abf2597da6e502b0dbc9feabe7e0`;
  every identity matched and the independent verdict was PASS/GO for the
  statistical-ratification packet only. Subsequent ratified specification edits
  intentionally supersede that freeze.

## K. Ratified pilot statistics and deterministic derivations

- [x] T124 Obtain Dr. Mani's explicit decisions for the two-stage denominator,
  crossed aggregation and uncertainty, exclusions/coverage, interval engine,
  deterministic seeds, threshold derivation, and later global confirmation claim;
  record all five clarifications in `spec.md`.
- [x] T125 Reconcile `plan.md`, `research.md`, `data-model.md`, `quickstart.md`,
  `contracts/constant-registry.md`, `contracts/artifact-schema.md`, and
  `contracts/preflight-api.md` with the ratified rules before changing executable
  behavior.
- [x] T126 Add failing pure-function tests for donor/map/bootstrap seed derivation,
  explicit `PCG64`, and collision/mismatch rejection.
- [x] T127 Add failing tests for the 80-denominator 0.05 linear derivation,
  source-vector digest, positive-finite guard, and score-only second stage.
- [x] T128 Add failing tests for exact 8×8 per-prompt effects, fixed floor-specific
  exclusion masks, 18/20 layer coverage, 3/4 per-category coverage, and
  category-balanced means without layer pooling.
- [x] T129 Add failing deterministic tests for 20,000 category-stratified prompt
  replicates, 20,000 prompt×donor×map product-weight replicates, finite-replicate
  enforcement, and linear 99% percentile bounds.
- [x] T130 Add failing tests for four-layer half-mean threshold vectors, unavailable
  vectors from any nonpositive/undefined source, and absence of a pilot
  pass/fail decision.
- [x] T131 Implement the pure statistical and deterministic-seed helpers and make
  T126–T130 pass without importing model, lens, CUDA, or notebook code.
- [x] T132 Reconcile preflight and external authorization so protocol rules and
  crossing vectors are ratified in source, pilot-derived numerics remain unset,
  only the two pilot authorization flags may transition externally, and
  `THRESHOLDS_RATIFIED` stays false.
- [x] T133 Extend the aggregate producer/schema and recursive validator to
  recompute denominator, exclusion, coverage, effects, estimates, intervals, RNG
  provenance, and threshold derivation while rejecting any pilot gate/decision.
- [x] T134 Rewire the canonical notebook to retain raw scores, derive one guard
  after all 80 loci, compute both floors without a second model/lens pass, execute
  both interval methods, and emit threshold evidence only.
- [x] T135 Update the synthetic 8×8 harness and corruption tests for the complete
  pilot statistical artifact.
- [x] T136 Run focused tests, complete J-space, full repository, Ruff,
  formatting check, all-retained-notebook parsing, deterministic bundle checks,
  and `git diff --check`. Fresh final-source verification on 2026-07-30:
  `317 passed` focused in 175.11s; final post-reconciliation rerun `464 passed`
  J-space in 81.72s; final repository rerun `3522 passed, 12 skipped` in 162.35s
  with two unrelated deprecation warnings; Ruff clean; 417 files formatted; 31
  ordinary cells parsed across all four retained notebooks; deterministic
  pilot-bundle tests and diff check passed.
- [x] T137 Freeze the statistically complete candidate and obtain an independent
  adversarial correspondence review. The first frozen candidate received NO-GO
  and was superseded by phase L.
- [x] T138 After review GO only, generate exact canonical notebook/code-bundle
  identities and a pilot authorization packet. Completed after the superseding
  freeze in T147: notebook
  `9564236a1f49d7ffe2bea44f8b04be5a584c0ff9740b11dd1e563c93b8dba2fe`,
  bundle
  `aeec8a76a426fa82f3fb96dc6700289a689fcb92fd9952da681fe03fe12dbef4`,
  authorization record
  `1af4ec95bf1c0f257fa5f559b7a91c939723cb7382eb0f5812ebc113d842b63c`.

## L. Superseding freeze after adversarial NO-GO

- [x] T139 Record the first frozen candidate and independent NO-GO without
  treating its green suites as pilot readiness. Freeze manifest SHA-256:
  `5ff349974f704dc6d4f92da511987353fab4ae318d3ab256e73bbbf24213be8a`.
- [x] T140 Move notebook identity proof to an external trusted launch preparer,
  require independently supplied source identities during artifact validation,
  reject coordinated provenance rewrites, and refuse stale launch directories.
- [x] T141 Extract donor selection into a pure helper and make the validator
  recompute every recipient × assignment source from the pinned pilot population
  and SHA-derived seed.
- [x] T142 Retain and validate full per-realized-map singular-spectrum evidence
  under declared implemented tolerances.
- [x] T143 Extract the authorized code bundle into a new exclusive directory,
  reject unsafe or undeclared members, and verify the exact post-extraction file
  set and hashes before import.
- [x] T144 Reuse one fitted-map decomposition for all eight layer draws so the
  runtime performs one fitted SVD plus eight independent realized-map spectrum
  checks per layer rather than repeating the fitted decomposition.
- [x] T145 Reconcile T140–T144 across the registry, artifact schema, data model,
  preflight contract, plan, quickstart, design baseline, and project state.
- [x] T146 Run focused, complete J-space, complete repository, Ruff, formatting,
  notebook-parse, deterministic-bundle, and diff checks on the repaired state.
  Fresh final-source results on 2026-07-30: `409 passed` focused in 86.61s;
  `487 passed` J-space in 476.35s; `3545 passed, 12 skipped` repository-wide in
  669.06s with two unrelated deprecation warnings; seven deterministic
  bundle/launch tests passed; Ruff clean; 419 files formatted; 54 ordinary code
  cells parsed across seven notebooks; `git diff --check` passed.
- [x] T147 Create a new content-addressed freeze and obtain an independent
  adversarial GO that explicitly replays all four first-freeze findings. Freeze
  manifest:
  `runs/stage2b-statistical-freeze-v2-20260730/stage2b-statistical-freeze-45a138e5829c1e5d.json`;
  independent verdict: PASS/GO.
- [x] T148 After T147 GO only, complete T138 for the exact reviewed source.

## M. Authorized pilot observation and public record

- [x] T149 Run only the exact-hash-authorized isolated 20-prompt dual-floor fully
  crossed 8×8 pilot on one Colab T4. The run completed 80 prompt-layer records;
  confirmation and artifact-transfer boundaries stayed false.
- [x] T150 Validate the in-memory aggregate, write the content-addressed artifact
  in Colab, and perform a final Colab-side SHA/cardinality audit. Artifact
  SHA-256:
  `d138846e7a189ad42955a5990e6d1a5c00553ba768cd838c5b6bf0334095daef`;
  validator errors: none; artifact retained in Colab.
- [x] T151 Reconcile the post-pilot result across Spec Kit, project state, the
  companion result notebook, public docs, wiki source, and journals without
  transferring the retained artifact or claiming a robust result.
- [ ] T152 Run final validation and independent review, commit the scoped recovery
  and public record, supersede historical PR #8, merge the reviewed recovery PR,
  and publish/verify the GitHub wiki.

## Observed recovery verification

```bash
uv run pytest tests/jspace/test_stage2b_endpoint.py -v
uv run pytest tests/jspace/test_stage2b_preflight.py -v
uv run pytest tests/jspace/test_stage2b_pilot_harness.py -v
uv run pytest tests/jspace/test_stage2b_notebook.py -v
uv run pytest tests/jspace/test_stage2b_validator.py -v
```

The earlier complete CPU-only J-space suite was observed passing (`297 passed`).
Post-review verification is recorded in T088 and supersedes that count for that
contract state. The excluded-input runtime smoke later verified model/lens
compatibility only. T149–T150 now record the separately authorized pilot
execution, its successful operational validation, and its scientifically
undefined preregistered robust result. Confirmation and downstream use remain
unverified and unauthorized.
