# Stage 2b controlled-recovery handoff

Timestamp: 2026-07-29 10:46:44 -0400

## Immediate status

**NO-GO. Do not commit, push, open a PR, run the notebook, access pilot or
confirmatory data, or allocate model/lens/GPU resources.**

The implementation and static/CPU tests are green, but the final independent Codex
review timed out after identifying a potentially real pilot-denominator contract
circularity. That finding is not yet verified or repaired.

## Worktrees and immutable reference

- Historical authoring snapshot/base:
  `fa7980b56a091d9bbd6e32d4136ddcfccbc6d867`
- Recovery branch: `recover/jspace-stage2b-contract`
- Recovery worktree:
  `/Volumes/Asylum/archimedes-recovery-jspace-stage2b`
- Protected original dirty checkout: `/Volumes/Asylum/archimedes`
- Original branch: `feat/jspace-stage2b-modules`
- Original HEAD remains:
  `fa7980b56a091d9bbd6e32d4136ddcfccbc6d867`
- Environment:
  - `UV_PROJECT_ENVIRONMENT=.venv`
  - `UV_CACHE_DIR=.uv-cache`

`fa7980b` is historical provenance only, not scientific or implementation
authority.

## Governing scientific contract

Authority order:

1. `specs/001-jspace-stage2b/spec.md`
2. explicitly ratified sections of
   `sakshi notes/STAGE2B_PREREGISTRATION_AMENDMENT_DRAFT.md`
3. explicitly ratified decisions in
   `sakshi notes/STAGE2B_OPEN_PARAMETERS.md`

Implemented measurement mechanics:

- exact 8 donor assignments × 8 broken-map draws;
- lossless compact representation with 81 unique readouts and 64 logical cells;
- `input_embedding_decoded` primary floor;
- `layer0_residual_decoded` sensitivity floor;
- `sensitivity_minus_primary` retained explicitly;
- complete donor/map IDs, seeds, pair digests, realized residual hashes, and map
  hashes;
- registry-derived fail-closed authorization;
- descriptive measurement only—no scientific gates or decision producer.

Still unratified/unset:

- bootstrap method/unit/iterations/seed;
- confidence interval rule;
- multiplicity and dependence-aware inference;
- effect thresholds and threshold derivation;
- exact donor seed vector;
- exact map seed vector;
- wrong-layer distances and seed;
- pilot and confirmatory execution authorization.

## Fresh verification evidence

After all current writes and Ruff formatting:

```text
uv sync --dev
Resolved 213 packages; audited 170 packages

uv run pytest tests/jspace -q
297 passed in 4.53s

uv run pytest -v --timeout=30
3355 passed, 12 skipped, 2 warnings in 190.89s

uv run ruff check .
All checks passed!

uv run ruff format --check .
405 files already formatted

git diff --check
passed
```

The two pytest warnings are existing class-scoped-fixture deprecation warnings.

Notebook static verification after the final producer edit:

```text
29 passed in tests/jspace/test_stage2b_notebook.py
JSON valid
ordinary code cells AST-parse
all code execution_count values are null
all code outputs are empty
```

Focused six-surface Stage 2b suite before the final formatter pass:

```text
297 passed
```

The post-format complete J-space and full repository passes supersede it.

## Current diff inventory

Before this handoff was created, recovery had 21 tracked modified files plus 3
expected untracked implementation files. This handoff is now a fourth untracked
file.

Tracked:

- `.specify/memory/project-state.md`
- `EvoScientist/skills/jspace-research-operations/scripts/stage2b_endpoint.py`
- `EvoScientist/skills/jspace-research-operations/scripts/stage2b_manifest.py`
- `EvoScientist/skills/jspace-research-operations/scripts/stage2b_preflight.py`
- `EvoScientist/skills/jspace-research-operations/scripts/validate_observation.py`
- `sakshi notes/STAGE2B_OPEN_PARAMETERS.md`
- `sakshi notes/jspace_colab_stage2b_discrimination.ipynb`
- `specs/001-jspace-stage2b/contracts/artifact-schema.md`
- `specs/001-jspace-stage2b/contracts/constant-registry.md`
- `specs/001-jspace-stage2b/contracts/preflight-api.md`
- `specs/001-jspace-stage2b/data-model.md`
- `specs/001-jspace-stage2b/plan.md`
- `specs/001-jspace-stage2b/quickstart.md`
- `specs/001-jspace-stage2b/research.md`
- `specs/001-jspace-stage2b/spec.md`
- `specs/001-jspace-stage2b/tasks.md`
- `tests/jspace/test_stage2b_endpoint.py`
- `tests/jspace/test_stage2b_manifest.py`
- `tests/jspace/test_stage2b_notebook.py`
- `tests/jspace/test_stage2b_preflight.py`
- `tests/jspace/test_stage2b_validator.py`

Untracked and expected:

- `EvoScientist/skills/jspace-research-operations/scripts/stage2b_pilot_harness.py`
- `sakshi notes/STAGE2B_PREREGISTRATION_AMENDMENT_DRAFT.md`
- `tests/jspace/test_stage2b_pilot_harness.py`
- `runs/stage2b-recovery-handoff-20260729/HANDOFF.md` (this handoff)

No `jspace_discrimination_s2b_*.json` or `*confirm*.json` exists in recovery.

## Repairs completed in the final cycle

1. `stage2b_preflight.py`
   - caller `PILOT_AUTHORIZED`/`THRESHOLDS_RATIFIED` values cannot override registry
     false or unratified truth;
   - removed unratified uniqueness/range policy while retaining mathematical type
     and domain checks;
   - focused delegated result was 99 passed; later full suites are green.

2. `validate_observation.py`
   - rejects missing/empty/non-compact `descriptive.records`;
   - validates expected pilot view rather than accepting it unused;
   - enforces exact target, floors, 81/64 crossing, and 8×8 provenance;
   - requires artifact denominator to match one explicit ratified registry entry;
   - validator-only final result: 44 passed.

3. Notebook/schema/tests
   - notebook aggregate builder no longer accepts or emits gates/decision;
   - schema now matches actual `descriptive.records`, `floor_scores`,
     `factorized_scores`, `factorized_nta`, donor assignments, and map draws;
   - historical R6 bootstrap/BCa proposal is explicitly superseded and not claimed
     implemented;
   - notebook static suite: 29 passed.

4. Documentation test counts updated to:
   - notebook: 29;
   - validator: 44;
   - J-space: 297.

## Protected-source incident and repair

Delegation batch `deleg_c57d433f`, task 3, ignored its recovery-worktree scope and
edited four files in `/Volumes/Asylum/archimedes`:

- `sakshi notes/jspace_colab_stage2b_discrimination.ipynb`
- `tests/jspace/test_stage2b_notebook.py`
- `specs/001-jspace-stage2b/contracts/artifact-schema.md`
- `specs/001-jspace-stage2b/research.md`

Dr. Mani explicitly authorized restoration. Pre-write bytes were reconstructed from
Hermes SQLite messages and captured diff/blob hashes—not from `git restore`, reset,
or HEAD replacement. Final verified hashes are:

```text
notebook  f631538e11d86b6b9d8d91b5c34ba66999dd4b6f
notebook test  f95f749663f1c2d0dd9b8591b935f9879bac83de
artifact schema  a7c5e0ad96fb9b96be861a1f2ed0a138d217868a
research memo  b80c66c994b507113a77b064e2903395c1fc8cc5
```

After restoration, source status returned to the session-start counts:

- 17 tracked changes;
- 28 untracked entries;
- original HEAD and branch unchanged.

Do not delegate another write without first requiring the child to assert exact
`pwd`, `git rev-parse --show-toplevel`, branch, and HEAD, and to use absolute paths
under the recovery root.

## Final Codex review state

A read-only final review was launched with Codex CLI session:

```text
019fae4e-373a-7842-b7bf-65aee9f6423a
```

Command timed out after 600 seconds. Codex did not complete a final findings list.
It raised one provisional concern that must be independently verified:

> The notebook ships `NTA_MIN_DENOMINATOR = None`; pilot preflight may exempt it,
> but the notebook measurement/validator requires an externally ratified finite
> denominator before producing/accepting a compact artifact. This may conflict with
> draft prose/tests saying the pilot is intended to produce the denominator.

Do not accept this as established merely because Codex stated it. Trace the exact
call path and governing ratified text. The likely question is whether:

- the current Stage 2b pilot is a measurement run requiring a denominator ratified
  before execution; or
- the pilot is intended to derive `NTA_MIN_DENOMINATOR`, in which case normalized
  compact NTA cannot be required before that derivation without a separate raw-score
  artifact phase.

No engineering choice may invent the denominator or select a derivation rule.
Resolve contract semantics from ratified sources or stop for Dr. Mani’s scientific
decision.

Codex also attempted a read-only J-space run but its sandbox could not initialize
`.uv-cache`; that failure is not a product-test failure. Parent-run tests above are
the valid execution evidence.

## Exact next actions

1. Verify the pilot-denominator circularity from source:
   - notebook constants/ratification cell;
   - notebook measurement and aggregate cells;
   - `stage2b_preflight.py` pilot exemptions;
   - `validate_observation.py` denominator enforcement;
   - amendment draft §§1 and 7;
   - spec/quickstart/preflight API language.
2. Decide whether Codex found a real contradiction or misread a deliberately
   pre-ratified denominator requirement. Do not choose scientific policy.
3. If real, write a failing regression/contract test first and make the smallest
   recovery-only repair. If it requires deciding how the pilot derives the floor,
   stop and ask Dr. Mani one bounded scientific question.
4. Rerun J-space, full pytest, Ruff lint/format, and `git diff --check` after any
   write.
5. Run or complete a final independent read-only diff review.
6. Recheck source hashes/status and recovery inventory.
7. Only then mark `recovery-8` and `recovery-10` complete.
8. Do not commit unless Dr. Mani explicitly asks after all findings are closed.

## Task state

- `recovery-8` — independent Codex review and finding verification: **IN PROGRESS**
- `recovery-9` — final authorization/validator/schema repairs: **COMPLETED**
- `recovery-10` — full gates and final scope/source audit: **IN PROGRESS**
  (gates and source audit passed, but final review closure is pending)

## Prohibited actions still in force

- no notebook cell execution;
- no model/lens/CUDA/GPU/Colab runtime;
- no pilot or confirmatory data access;
- no opening pilot/confirmatory JSON artifacts;
- no selection of thresholds, seeds, bootstrap, confidence, multiplicity, or
  wrong-layer values;
- no source checkout/reset/restore/clean/stash;
- no commit, push, PR, or readiness claim;
- no access to `/Volumes/Asylum/Sync`.
