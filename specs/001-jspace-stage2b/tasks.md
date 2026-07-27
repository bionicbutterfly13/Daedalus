# Tasks: Stage 2b J-space discrimination

**Input**: Design documents from `/specs/001-jspace-stage2b/`
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Scope is authoring only.** Every task below produces a file. No task runs a
measurement, allocates a GPU, or produces an observation artifact. Execution
requires Dr. Mani's ratification of the ten open parameters and
`THRESHOLDS_RATIFIED = True` (FR-013, Q10), and is out of scope for this feature.

**Tests are required, not optional.** US3's acceptance scenarios are assertions
about preflight failure behaviour, and constitution Principle III forbids a suite
that only exercises happy paths. Test tasks precede the implementation they cover.

---

## Phase 1: Setup

- [x] T001 Create the test package directory `tests/jspace/` with an empty `tests/jspace/__init__.py`, matching the layout of the existing subpackages under `tests/`
- [x] T002 [P] Record the Stage 2 per-prompt digest list as a fixture at `tests/jspace/fixtures/stage2_manifest_digests.json`, extracted from cell 14 of the **tracked** notebook `sakshi notes/jspace_colab_stage2_discrimination.ipynb`, for the FR-011 disjointness check. Do not source it from `jspace-study/` in the main tree — that copy is untracked and local to one machine, which would make the fixture unreproducible
- [x] T003 [P] Add `stage2b-design-baseline.md` to `EvoScientist/skills/jspace-research-operations/references/` summarizing the design and pointing at `specs/001-jspace-stage2b/`, alongside the existing `stage2-discrimination-baseline.md`

---

## Phase 2: Foundational (blocking prerequisites)

Shared by every user story. Nothing in Phase 3+ can start until these land.

**Import constraint, binding on every module in this phase**: no `torch`, no
`jlens`, no `scipy` at import time. Checks take extracted metadata — shape tuples,
dtype *strings*, device *strings*, digests, floats. This is what makes the whole
suite runnable on a machine with no GPU, and it is the reason Stage 2's equivalent
logic could not be tested at all (plan.md Structure Decision).

- [x] T004 Create `EvoScientist/skills/jspace-research-operations/scripts/stage2b_preflight.py` with the `PreflightError` exception carrying `code: str` and `detail: dict`, per [contracts/preflight-api.md](./contracts/preflight-api.md)
- [x] T005 [P] Write failing tests for the constant registry in `tests/jspace/test_stage2b_preflight.py`: assert `orphaned_constant` for an entry with an empty `consumed_by`, `unregistered_constant` for a gate reading a name absent from the registry, and `phantom_consumer` for an entry whose `consumed_by` names a gate or check that does not exist
- [x] T006 Implement `check_constant_registry(registry, gates, preflight_checks, endpoint_fns, consumer_reads)` in `stage2b_preflight.py` — all three checks, per [contracts/constant-registry.md](./contracts/constant-registry.md). The referential check is not redundant: without it, a typo in a `consumed_by` entry passes and then writes a `registry` block into the artifact asserting a linkage that was never built, which is the false assurance the registry exists to prevent. `consumer_reads` carries what each preflight check and endpoint function actually reads, so the reverse check covers all three namespaces — most registered constants here are read by preflight, not by a gate, and a gates-only sweep would leave the larger surface unguarded
- [x] T007 [P] Encode the initial registry from [contracts/constant-registry.md](./contracts/constant-registry.md) as a module-level constant in `stage2b_preflight.py`, including both `constant` and `derived_field` entries. The `derived_field` kind exists because research.md R7's orphan was a computed field, not a declared constant, and a constants-only registry would miss it
- [x] T008 [P] Implement `emit_registry_record(registry, gates) -> dict` in `stage2b_preflight.py`, pure and I/O-free, returning the `registry` block for the aggregate artifact
- [x] T009 [P] Write failing tests in `tests/jspace/test_stage2b_endpoint.py` for the rank convention: the top token ranks 1 (never 0), ties resolve to the best rank under strict `>`, and rank is 1-indexed so `log(rank)` is defined
- [x] T010 Create `EvoScientist/skills/jspace-research-operations/scripts/stage2b_endpoint.py` implementing `target_rank1(logits, target_id)` as a comparison count `(logits > logits[target_id]).sum(-1) + 1`, per research.md R4. Do not call `jlens.vis._ranks_of` — it still performs a full-vocabulary `argsort` per chunk and is the reference, not the implementation
- [x] T011 [P] Implement `nta(s_readout, s_prompt_only, s_output, min_denominator)` in `stage2b_endpoint.py` returning the normalized value or an exclusion marker, per data-model.md §3

---

## Phase 3: User Story 1 — Establish whether the specific fit matters (P1) 🎯 MVP

**Goal**: author everything needed to answer whether the correctly fitted map at
the correct layer recovers more about the model's own next-token target than a
same-layer map with the fit destroyed but geometry preserved.

**Independent test**: the H1 statistic is a paired difference at matched prompt and
layer. Its construction, its exclusion accounting, and its fit-broken control are
verifiable with fixed arrays and no model — Scenario 2 of [quickstart.md](./quickstart.md).

- [x] T012 [P] [US1] Write failing tests in `tests/jspace/test_stage2b_endpoint.py` for the anchors: `NTA(prompt_only) == 0.0` and `NTA(output) == 1.0` exactly, by construction. FR-002 makes Stage 2's omitted-baseline defect unrepresentable rather than re-adding it as a gate, so these must hold identically, not approximately
- [x] T013 [P] [US1] Write failing tests in `tests/jspace/test_stage2b_endpoint.py` for the denominator guard: a cell with `s(output) − s(prompt_only)` at or below `NTA_MIN_DENOMINATOR` is excluded with a recorded reason and is never divided; exclusions are counted per layer, never pooled to a bare total
- [x] T014 [US1] Implement the rank-parity verification `verify_rank_parity(logits, target_id)` in `stage2b_endpoint.py` (FR-010), comparing the comparison-count rank against a naive `argsort` reference with the same documented convention, and returning a boolean for the artifact's `contracts.rank_parity_verified`
- [x] T015 [P] [US1] Implement `build_fit_broken_map(J, seed)` in `stage2b_endpoint.py`: SVD `J = U Σ Vᵀ`, draw a Haar-random orthogonal `Q` under the preregistered seed, return `(Q @ U) @ diag(S) @ Vh` (FR-004). Assert the returned map preserves the singular value spectrum, operator norm, and Frobenius norm of `J` — that preservation is what makes it a control rather than a different object
- [x] T016 [P] [US1] Write tests in `tests/jspace/test_stage2b_endpoint.py` asserting `build_fit_broken_map` preserves the spectrum to within float tolerance and that `Q` is orthogonal (`QᵀQ ≈ I`), using a small fixed-seed matrix rather than a real Jacobian
- [x] T017 [US1] Implement `transport_with(residual, J)` in `stage2b_endpoint.py` as `residual @ J.T`, reimplementing `JacobianLens.transport`'s single-line body rather than mutating `lens.jacobians[layer]` in place (research.md R3). Mutating the lens would make later reads of `lens.jacobians[layer]` silently return the broken map — the same invisible-when-wrong class as Stage 2's dead constants
- [x] T018 [US1] Implement `paired_difference_by_cluster(cells, layer)` in `stage2b_endpoint.py` returning per-prompt vectors of paired within-layer differences, with the prompt as the cluster unit and layers as repeated measures (FR-006). Depth-pooled values are descriptive only and must not be returned from this function
- [x] T019 [P] [US1] Write tests asserting `paired_difference_by_cluster` pairs strictly within layer and returns one cluster per prompt, so a caller cannot accidentally treat `prompt × layer` cells as independent
- [x] T045 [US1] Implement `select_wrong_activation(residuals_by_prompt, exclude_prompt_sha256, layer, seed)` in `stage2b_endpoint.py` (FR-005): pick a real residual captured at the same layer from a *different* prompt in the same manifest, rescale it to the norm of the activation it replaces, and return it alongside its source prompt digest for `factorial.wrong_activation_source_prompt_sha256`. A random vector is explicitly not acceptable here — Stage 2 already showed a norm-matched random vector is easy to beat (fraction 1.00), and it is retained only as the sanity floor
- [x] T046 [P] [US1] Write tests in `tests/jspace/test_stage2b_endpoint.py` asserting `select_wrong_activation` never returns the excluded prompt's own residual, matches the target norm to within float tolerance, and is deterministic under a fixed seed
- [x] T047 [P] [US1] Implement `allocate_wrong_layers(selected_layers, distances, n_prompts, seed)` in `stage2b_endpoint.py` (FR-008, `WRONG_LAYER_DISTANCES` default `[3, 7, 14]`): **near-equal** allocation across prompts, sign balanced where the layer index permits, returning the per-prompt band assignment so results can be reported per distance band. Exact balance is impossible — 200 prompts across 3 bands is 66.67 — so the rule is `floor(n/k)` per band with the remainder distributed to the lowest-indexed bands under the preregistered seed, and the realized counts recorded in the artifact. Stage 2 did not balance this at all, which is why its mismatched-probe fraction of 0.40 mixes near and far regimes and cannot be interpreted
- [x] T048 [P] [US1] Write tests asserting `allocate_wrong_layers` produces counts differing by at most 1 across bands (not exact equality — that is unsatisfiable at n=200, k=3), balances sign where the layer index allows, never assigns a wrong layer outside the model's layer range, and is deterministic under a fixed seed

---

## Phase 4: User Story 2 — Establish non-redundancy with teeth (P2)

**Goal**: show the Jacobian readout is not a re-encoding of the logit lens in a way
that shows up on the target, not merely in token overlap.

**Independent test**: the Jaccard statistic and the target-relative paired
difference are both computable from the same fixed arrays without the specificity
arm.

- [x] T020 [P] [US2] Implement `jaccard_top_k(readout_a, readout_b, k)` in `stage2b_endpoint.py`, carried over from Stage 2's `jaccard_top10` so the H2 overlap clause stays commensurable with the pilot
- [x] T021 [P] [US2] Write tests in `tests/jspace/test_stage2b_endpoint.py` for `jaccard_top_k` on disjoint, identical, and partially overlapping fixed rankings
- [x] T022 [US2] Implement `gate_record(name, constant_name, declared_value, statistic, interval, crosscheck, n_clusters, exclusions) -> dict` in `stage2b_endpoint.py`, producing the Gate shape from [contracts/artifact-schema.md](./contracts/artifact-schema.md)
- [x] T023 [US2] Implement the outcome rule inside `gate_record`: a non-finite interval bound yields `outcome = "undefined"`, never `"fail"` (research.md R6). An absent measurement and a measured null are different results; BCa acceleration is unstable for a median under leave-one-out and scipy returns NaN bounds on a degenerate bootstrap
- [x] T024 [P] [US2] Write tests asserting `gate_record` returns `undefined` for a NaN interval bound and `fail` for a finite interval that includes zero — the distinction is the point, so both cases need a test
- [x] T025 [US2] Document the cluster-bootstrap idiom in `EvoScientist/skills/jspace-research-operations/references/stage2b-design-baseline.md`: `scipy.stats.bootstrap` with `data=(cluster_ids,)` and a non-vectorized statistic closing over a per-prompt lookup table, so BCa's jackknife leaves out whole clusters (research.md R6)
- [x] T049 [US2] Implement `cluster_bootstrap_median(cluster_values, level, iterations)` in `stage2b_endpoint.py` (FR-006), with `scipy` imported **inside the function** rather than at module scope so the module still imports on a machine without it. Return both the BCa interval and the percentile cross-check that `contracts/artifact-schema.md` requires whenever the gating method is BCa. This is the resampler H1, H2-target, and the sanity floor all gate on; leaving it documented-only would put the most load-bearing statistic in the feature outside every task
- [x] T050 [P] [US2] Write tests in `tests/jspace/test_stage2b_endpoint.py` for `cluster_bootstrap_median`, skipped via `pytest.importorskip("scipy")` so the suite stays green in this repo's scipy-free environment: assert whole clusters enter or leave together (a cluster's observations are never split across a resample), that the statistic is computed within a single layer rather than over a concatenation of all layers, and that a degenerate input yielding NaN bounds propagates as non-finite rather than being silently coerced
- [x] T053 [US2] Implement `compose_decision(gate_records)` in `stage2b_endpoint.py` returning `pass` | `ambiguity` | `fail` | `kill` per [../data-model.md](./data-model.md) §4 (FR-007): pass = reproduction ∧ H1 ∧ H2(both clauses); ambiguity = reproduction ∧ exactly one of H1/H2; fail = reproduction ∧ neither, or sanity floor not cleared; kill = reproduction fails or any pinned identity mismatches. H1 is itself conjunctive over `h1_specificity` and `h1_interval`, evaluated per layer
- [x] T054 [P] [US2] Write tests for `compose_decision` covering all four outcomes plus the two rules easiest to get wrong: a gate with `outcome = "undefined"` must never be counted as a pass, and H1 passing at three of four layers must not count as H1 passing
- [x] T055 [US2] Implement `assemble_factorial_cells(...)` in `stage2b_endpoint.py` (FR-003) producing the four named 2×2 cells per `(prompt, layer)` from the fitted map, the broken map, the correct activation, and the wrong activation, plus the main effects and the interaction estimate. The interaction is computed and reported but is **not** a gate — no pilot estimate exists for it, and a third preregistered threshold on an unmeasured quantity would be a guess
- [x] T056 [P] [US2] Write tests asserting `assemble_factorial_cells` emits exactly the four cells with the naming from `contracts/artifact-schema.md`, and that the interaction estimate never reaches `compose_decision`

---

## Phase 5: User Story 3 — Make the recorded failure modes unrepeatable (P3)

**Goal**: every defect this project has hit fails at preflight rather than during or
after a run.

**Independent test**: exercised against a deliberately broken configuration with no
GPU and no measurement — Scenario 1 of [quickstart.md](./quickstart.md).

- [x] T026 [P] [US3] Write failing tests in `tests/jspace/test_stage2b_preflight.py` for the tensor contracts: `dtype_mismatch` for a residual that is not `"torch.float32"`, `device_mismatch` for a readout not on `"cpu"`, `decode_parity` beyond `DECODE_PARITY_TOL`, and `unexpected_softcapping` for a non-null softcap value
- [x] T027 [US3] Implement `check_tensor_contracts(observed)` in `stage2b_preflight.py` per [contracts/preflight-api.md](./contracts/preflight-api.md). The dtype check is load-bearing rather than hygienic: `JacobianLens.transport` moves the Jacobian to the residual's device but does not cast its dtype, and Stage 2b bypasses `lens.apply` for three of four factorial cells, losing the `.float()` that path provided (research.md R5)
- [x] T028 [P] [US3] Write failing tests in `tests/jspace/test_stage2b_manifest.py` for every manifest failure code: `manifest_version`, `manifest_size`, `category_imbalance`, `malformed_digest`, `duplicate_prompt`, `stage2_overlap`, `anchor_contamination`, `prompt_too_long`, `manifest_digest`
- [x] T029 [US3] Create `EvoScientist/skills/jspace-research-operations/scripts/stage2b_manifest.py` implementing manifest construction, canonical digesting byte-identical to Stage 2's scheme, and `check_manifest(manifest, stage2_digests, expected_digest)`. `expected_digest` is a parameter, not a field read back out of `manifest` — a document cannot contain its own hash, and a digest check that finds its expected value inside the thing it is checking is a tautology
- [x] T030 [US3] Keep `stage2_overlap` and `anchor_contamination` as distinct codes in `check_manifest`. Both are contamination, but the anchor is deliberately retained elsewhere in the protocol as the reproduction kill check and must not be diagnosed as an ordinary overlap bug
- [x] T031 [P] [US3] Write failing tests in `tests/jspace/test_stage2b_preflight.py` for `check_ratification`: `not_ratified` when the flag is false, and `unset_constant` when the flag is true while any registered constant's `declared_value` is `None`
- [x] T032 [US3] Implement `check_ratification(thresholds)` in `stage2b_preflight.py`, running last so every other check is exercisable against the unratified configuration the notebook ships in. The `unset_constant` rule makes deferring a threshold and signing the ratification mutually exclusive rather than merely discouraged — Stage 2's failure mode was setting a margin without a pilot, and this makes the inverse mistake impossible too
- [x] T033 [P] [US3] Implement `check_environment(env)` in `stage2b_preflight.py`, asserting `python_version >= (3, 11)`, CUDA availability, `vram_gib >= MIN_VRAM_GIB`, the pinned model/lens identities, and `jlens_commit == JLENS_COMMIT` read back from the *installed* package. R2 established that `%pip` does interpolate the pin, but from upstream IPython source on a machine with no IPython — the read-back converts that inference into a measurement for one line
- [x] T034 [P] [US3] Write tests asserting `check_environment` raises `jlens_commit` when the installed commit differs from the pin, using a synthetic env dict

---

## Phase 6: Notebook shell

> **BLOCKED — on a design decision, not on tooling.** T051's cross-check found
> that a Stage 2b `pass` can coexist with a null interaction, which the design
> calls the signature of a real instrument (research.md R10, open item 7). And
> `prompt_only`, one of the two anchors the endpoint is defined against, has no
> construction spec anywhere (R11, open item 8). Authoring the notebook before
> either is settled would bake in a decision rule nobody chose and a baseline
> nobody defined. This is exactly what putting T051 before Phase 6 was for.

**Also gated on PR #2**, like every phase above it — see Dependencies. This phase
adds one further prerequisite of its own: T051's adversarial cross-check must
complete before T035, because cross-checking a design after implementing it
inspects a decision already made.

- [ ] T035 **After T051 completes.** Author `sakshi notes/jspace_colab_stage2b_discrimination.ipynb` as a shell over the tested modules: boundaries header, pinned identities, constant declarations, install, environment preflight, module import by path, measurement loop, artifact export. Do not reproduce Stage 2's single 18 KB measurement cell — it is the direct cause of four declared-but-unconsumed quantities surviving to an audit
- [ ] T036 [P] Ship the notebook with `THRESHOLDS_RATIFIED = False` and a guard that raises before the measurement loop (FR-013). This is the boundary between this feature and execution
- [ ] T037 Replace Stage 2's five-name transport probe (cell 12) with direct assertions on `lens.jacobians[layer]` and `lens.transport`, both confirmed present at the pinned commit (research.md R1, R3). A probe that accepts whichever of five names resolves cannot be audited against a pin
- [ ] T038 Resolve Stage 2's three loose constants in the notebook's declarations: `SAME_RUNTIME_REPEATS`, `INFERENCE_SEEDS`, `RANDOM_VECTOR_SEEDS`. Each must either drive the loop that bears its name and be registered, or be deleted (research.md R8). Carrying them forward as declarations that happen to match hardcoded behaviour is exactly what the registry exists to stop
- [x] T039 [P] Generate `sakshi notes/jspace-stage2b-stimulus-v1.json` — 200 held-out prompts, 5 categories of 40, disjoint from Stage 2 by digest, Stage 1 anchor excluded, every `token_count <= 128`
- [ ] T052 Before committing the notebook — on request, per the constitution's "commit only when asked" — confirm it is actually stageable. `.gitignore:57` ignores `*.ipynb` repo-wide, but PR #2 adds `!sakshi notes/*.ipynb` re-including that directory, so a plain `git add` works **there and only there**. A notebook written anywhere else needs `git add -f` or it is silently skipped and the commit looks clean while the deliverable is missing. Verify with `git ls-files "sakshi notes/*.ipynb"`, not a green `git status`
- [ ] T040 Wire the aggregate artifact export to include `registry`, `disjointness`, `gates`, `descriptive`, and `decision` as separate blocks per [contracts/artifact-schema.md](./contracts/artifact-schema.md). Keeping `descriptive` a sibling of `gates` is deliberate: the 2×2 interaction is reported but not gated, and the structure should make that impossible to misread

---

## Phase 7: Polish & cross-cutting

- [x] T041 [P] Extend `EvoScientist/skills/jspace-research-operations/scripts/validate_observation.py` with a `jspace-observation-stage2b/v1` branch whose test is not that the artifact parses but that every value a gate's outcome depends on is present in the aggregate (FR-012, SC-003)
- [x] T042 [P] Add a Stage 2b section to `EvoScientist/skills/jspace-research-operations/SKILL.md` pointing at the spec directory and the new scripts
- [x] T043 Run `uv run ruff check .` and `uv run pytest`, and confirm the suite is green standing alone on this branch — not only combined with PRs #5 and #6. Baseline on `main` is 3036 passed, 12 skipped
- [x] T044 Verify every failure code in [contracts/preflight-api.md](./contracts/preflight-api.md) has at least one test that makes it fire. A preflight suite that only proves valid configurations pass has not tested the preflight (Principle III)
- [x] T051 Cross-check the endpoint definition and the 2×2 factorial with Codex before Phase 6, per the constitution's "adversarial review for non-trivial fixes". Treat its output as evidence, not authority — verify each claim against source, and expect to correct it about as often as it corrects you. Record the exchange's conclusions in `specs/001-jspace-stage2b/research.md`

---

## Dependencies

```text
PR #2 merged  [gates everything below]
    └─> Phase 1 Setup
            └─> Phase 2 Foundational  (PreflightError, registry, rank, NTA)
                    ├─> Phase 3 US1 (P1)  ─┐
                    ├─> Phase 4 US2 (P2)  ─┼─> T051 Codex cross-check ─> Phase 6 Notebook
                    └─> Phase 5 US3 (P3)  ─┘                             │
                                                                         v
                                                              Phase 7 remaining polish
```

**PR #2 gates the whole feature, not just Phase 6.** Verified:
`git ls-tree main -- EvoScientist/skills/jspace-research-operations` is empty, as is
`git ls-tree main -- jspace-study`. Neither the skill directory that every module
task writes into nor the Stage 2 notebook that T002 reads exists on `main` — both
live only on `docs/jspace-research-operations`. An earlier draft of this section
claimed only Phase 6 was blocked; that was wrong, and it was wrong in the direction
that would have been discovered by a failing path halfway through Phase 2.

Work therefore branches from `docs/jspace-research-operations`, or from `main`
after PR #2 merges. PRs #5 and #6 remain genuinely unrelated.

**T002's source must be the tracked copy.** `jspace-study/…ipynb` in the main tree
is untracked and exists only on this machine; read the digests from
`sakshi notes/jspace_colab_stage2_discrimination.ipynb` on the docs branch instead,
or the fixture is unreproducible for anyone else.

**T051 runs before Phase 6, not after.** It is numbered into Phase 7 for grouping,
but the constitution requires the adversarial cross-check happen *before*
implementing — cross-checking the endpoint design after the notebook is written
inspects a decision already made. It is an explicit prerequisite of T035.

**Story independence**: US1, US2, and US3 touch different functions and can proceed
in parallel once Phase 2 lands. US3 is ranked P3 because it produces no scientific
result by itself, but the ordering subtlety is worth stating — US3's preflight is a
*quality gate on the run*, not a prerequisite for authoring US1 and US2. Nothing in
US1 or US2 imports it.

---

## Parallel execution

> **Numbering note**: T045–T051 were added by `/speckit-analyze` to close coverage
> gaps on FR-005, FR-006, FR-008, and the constitution's adversarial-review
> obligation. T053–T056 were added after a Codex review found FR-003, FR-007, and
> the final decision composition had no covering task at all. Tasks sit in the
> phase where they execute, not at the end; execution order comes from this
> section and Dependencies above, never from ID order.

Within Phase 2, after T004: T005, T007, T008, T009 are independent.

Within Phase 3, after T011: T012, T013, T016, T019, T046, T047, T048 are
independent; T014, T015, T017, T018, T045 all touch `stage2b_endpoint.py` and
should be serialized against each other.

Within Phase 4: T021, T024, T050, T054, T056 are test-only and independent. T020,
T022, T023, T049, T053, T055 all write `stage2b_endpoint.py` and must serialize.
T053 (`compose_decision`) depends on T022/T023 (`gate_record`), since it consumes
gate records — including the `undefined` outcome it must never count as a pass.

Across phases, after Phase 2: one agent per user story is a clean split — US1 in
`stage2b_endpoint.py` + `test_stage2b_endpoint.py`, US3 in `stage2b_preflight.py` +
`stage2b_manifest.py` + their tests. US2 shares `stage2b_endpoint.py` with US1 and
should follow it rather than run beside it.

---

## Implementation strategy

**MVP is Phase 1 + Phase 2 + Phase 3 (US1).** That delivers the fit-broken map, the
NTA endpoint with verified rank parity, and the clustered paired difference — the
question Stage 2 failed to answer, in testable form, with nothing executed.

**Increment 2** adds US2, which reuses the endpoint and adds only the overlap
statistic and the gate record.

**Increment 3** adds US3, which is where the audit findings become mechanically
unrepeatable. Cheapest phase in the feature and the highest value per line, since
the constant registry alone would have caught every finding of the 2026-07-26 audit
before execution rather than after.

**Phase 6 waits on PR #2, like everything else, plus T051.** It is the only phase
with a prerequisite beyond the shared one.

**Nothing here authorizes a run.** Ten parameters need ratification, three of them
not delegable: Q3 (what counts as the target — it defines what the study means by
"information"), Q5 (the specificity threshold, deliberately left unset so it can be
derived from a pilot rather than guessed), and Q10 (execution authorization).
