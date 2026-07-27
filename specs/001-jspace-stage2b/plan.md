# Implementation Plan: Stage 2b J-space discrimination

**Branch**: `001-jspace-stage2b` | **Date**: 2026-07-26 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-jspace-stage2b/spec.md`

## Summary

Author — but do not run — the Stage 2b discrimination study: a held-out stimulus
manifest, a preflight module that fails closed, and a Colab notebook implementing
a target-relative endpoint (normalized target attainment) under a 2×2 factorial
control structure.

The scope of this feature is **authoring only**. Every deliverable is a file. No
GPU executes, no measurement is taken, and no artifact is produced, until Dr.
Mani ratifies the ten open parameters and sets `THRESHOLDS_RATIFIED = True`
(FR-013, Q10). That boundary is not a convention here; it is enforced by a gate
in the notebook and asserted by a test in the preflight suite.

The technical approach has three parts, in dependency order:

1. **Preflight as a real Python module, not notebook cells.** US3 requires the
   preflight be exercisable against a deliberately broken configuration with no
   GPU. Notebook cells cannot be unit-tested; a module in the existing
   `jspace-research-operations` skill can, and joins `validate_observation.py`
   already there. It carries FR-009's constant-consumption registry — the change
   the design calls its highest-value one. The endpoint and manifest modules get
   the same treatment and the same test suite; what stays untested is the
   notebook, which is why it is kept as thin as possible.
2. **Stimulus manifest as data, generated and digest-verified.** 200 held-out
   prompts, disjoint from Stage 2 by per-prompt digest, asserted at preflight
   rather than documented as a rule.
3. **Notebook as the thin execution shell.** It imports the preflight module,
   declares constants, and runs the measurement loop. Keeping the logic outside
   the notebook is what makes FR-009 and FR-010 testable at all.

## Technical Context

**Language/Version**: Python 3.11+ — the repo targets `>=3.11` (`pyproject.toml`)
and Colab currently ships 3.11/3.12. Stage 2's notebook pinned no Python version
and only recorded `sys.version` into its artifact; Stage 2b asserts a floor at
preflight instead.

**Primary Dependencies**:

- `jlens` (from `git+https://github.com/anthropics/jacobian-lens.git`, pinned at
  commit `581d398613e5602a5af361e1c34d3a92ea82ba8e`) — the fitted Jacobian lens.
- `transformers>=5.5`, `huggingface_hub>=0.30`, `safetensors`, `torch` (Colab
  CUDA build), `scipy>=1.10`.
- Repo-side: `pytest`, `pytest-asyncio`, `ruff` — for the preflight module only.
  The preflight module MUST NOT import `torch` or `jlens` at module import time,
  so the repo suite can exercise it on a machine with neither.

**Storage**: Content-addressed JSON artifacts written by the notebook at run
time, using Stage 2's `write_content_addressed()` scheme (canonical
`json.dumps(sort_keys=True, indent=2, ensure_ascii=False) + "\n"`, SHA-256,
filename `{prefix}_{digest[:16]}.json`, exclusive-create with an immutability
re-check). Artifacts stay on the ephemeral runtime; transfer is a separate
authorization gate. Raw stimulus text lives only in the versioned in-repo
manifest (Q8).

**Testing**: `uv run pytest` for the preflight, endpoint, and manifest modules
(`tests/jspace/`). Tests needing `scipy` are guarded with
`pytest.importorskip("scipy")` so they run where it exists and skip here. The
notebook itself is not executed by CI and is not executed by this feature at all.
Coverage target is the preflight's failure paths, not its happy path — a
preflight that only passes has not been tested.

**Target Platform**: Google Colab, single Tesla T4 class (Q9), CUDA required,
`MIN_VRAM_GIB = 14.0`. Model `Qwen/Qwen3-1.7B` at revision
`70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`, `d_model` 2048, 28 layers. No
cross-runtime reproducibility claim is made.

**Project Type**: Research notebook plus a supporting Python module inside an
existing agent-skill directory. Not a service, not a library release.

**Performance Goals**: The run must fit a single T4 session at n=200 across 4
layers. Stage 2's full-vocabulary `argsort` per readout is the known hotspot and
Q9 makes replacing it a precondition of any 200-prompt run; FR-010 additionally
requires the replacement be verified against the old path on a fixed probe so the
optimization cannot silently change the statistic. No wall-clock target is set —
none was measured on Stage 2, and inventing one would be false precision.

**Constraints**:

- Observation only. No lens fitting, steering, ablation, activation editing, or
  causal intervention. The wrong-activation and fit-broken-map cells are readout
  manipulations computed offline from captured residuals.
- Evidence class 1 ceiling. A pass authorizes writing a Stage 3 proposal and
  nothing else.
- `THRESHOLDS_RATIFIED = False` is the shipped state and MUST remain so in the
  committed notebook.
- Three parameters (Q3 target definition, Q5 specificity threshold, Q10
  execution authorization) are not delegable and are not resolved by this plan.

**Scale/Scope**: 200 prompts × 4 layers × 1 position × ~9 readout conditions.
Five stimulus categories at 40 prompts each. Cluster bootstrap at 10,000
iterations over prompts.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

Gates derived from `.specify/memory/constitution.md` v1.0.1.

| Principle | Gate for this feature | Initial | Post-design |
|---|---|---|---|
| I. Correctness before minimality | The endpoint change is larger than a patch to Stage 2's gate. Taking the larger, correct rewrite over the smaller edit is the required direction, not a violation. | PASS | PASS |
| II. Evidence proportional to risk (NON-NEGOTIABLE) | This is an infrastructure-and-measurement change, so the execution path must be traced before authoring. Two load-bearing facts about `jlens` are assumed rather than verified in Stage 2's source. Resolved in Phase 0 as blocking research items R1 and R2. | **FAIL — unresolved unknowns** | PASS (R1/R2 recorded as verification tasks that must complete before the notebook is authored) |
| III. Never game verification | Preflight tests must assert failure paths, not just the happy path. A preflight suite that only proves "valid config passes" would be the exact coverage-narrowing this principle forbids. Encoded as an explicit tasks constraint. | PASS | PASS |
| IV. Declared means consumed | FR-009's constant registry *is* this principle mechanized. Every declared constant must resolve to a consuming gate and every gate must read only registered constants, checked at preflight, failing closed. | PASS | PASS |
| V. The record must not overstate | FR-012 requires per-gate reporting sufficient to recompute each decision without the notebook. Content-addressed artifacts stay immutable and excluded from formatters. | PASS | PASS |
| Scientific Protocol — stage gates | Observation only; evidence class 1; a pass authorizes a Stage 3 *proposal* only. Stated in spec Assumptions and re-asserted in the notebook header. | PASS | PASS |
| Scientific Protocol — preregister then execute | `SPEC_MIN_EFFECT` and `NTA_MIN_DENOMINATOR` are deliberately unset, to be derived from the Q6 pilot rather than guessed. Setting them now would repeat Stage 2's error in a new unit. | PASS | PASS |
| Scientific Protocol — measure against ground truth | The whole point of the NTA endpoint. Stage 2's difference metric had no notion of correct. | PASS | PASS |
| Scientific Protocol — Dr. Mani ratifies | FR-013. Authoring proceeds; execution waits for `THRESHOLDS_RATIFIED`. | PASS | PASS |
| Scientific Protocol — artifacts stay put | No transfer task exists in this feature. Stage 2's opt-in download cell is carried over defaulted off. | PASS | PASS |
| Safety — no upstream push, no outward actions | Feature is local authoring. No issues filed, nothing published. | PASS | PASS |
| Runtime Invariants | The preflight module must not shadow or import the runtime; it lives under `EvoScientist/skills/` and is imported by path in the notebook, not installed. | PASS | PASS |
| Development Workflow — branch per concern, verify standing alone | The preflight module's tests must pass standing alone on this branch, not only combined with PRs #5/#6. | PASS | PASS |

**Initial gate result: FAIL on Principle II**, with two named unknowns. This is
the correct outcome for a first pass — the design document itself flags the
`jlens` transport primitive as "a documented ASSUMPTION to confirm against jlens
commit 581d398 before ratified execution," and Stage 2's notebook raises
`NotImplementedError` if it cannot resolve one. Phase 0 converts both into
verification tasks that gate notebook authoring. See [research.md](./research.md).

## Project Structure

### Documentation (this feature)

```text
specs/001-jspace-stage2b/
├── spec.md              # Feature specification (already written)
├── plan.md              # This file
├── research.md          # Phase 0 output — resolved unknowns and open risks
├── data-model.md        # Phase 1 output — entities, artifact schemas, registry
├── quickstart.md        # Phase 1 output — how to validate without a GPU
├── contracts/
│   ├── preflight-api.md         # The preflight module's public contract
│   ├── artifact-schema.md       # jspace-observation-stage2b/v1 record shapes
│   └── constant-registry.md     # Declared-means-consumed registry contract
└── tasks.md             # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
EvoScientist/skills/jspace-research-operations/
├── SKILL.md                          # existing; extended with a Stage 2b section
├── references/
│   ├── stage2-discrimination-baseline.md   # existing
│   └── stage2b-design-baseline.md          # new: the design, as a skill reference
└── scripts/
    ├── validate_observation.py       # existing
    ├── stage2b_preflight.py          # NEW — tensor contracts + constant registry
    ├── stage2b_endpoint.py           # NEW — NTA statistic + direct rank
    └── stage2b_manifest.py           # NEW — manifest build, digest, disjointness

sakshi notes/
├── jspace_colab_stage2_discrimination.ipynb   # existing (Stage 2, closed)
├── jspace_colab_stage2b_discrimination.ipynb  # NEW — the execution shell
└── jspace-stage2b-stimulus-v1.json            # NEW — 200 held-out prompts

tests/jspace/
├── test_stage2b_preflight.py         # NEW — failure paths, no GPU, no jlens
├── test_stage2b_endpoint.py          # NEW — NTA, rank parity, denominator guard
└── test_stage2b_manifest.py          # NEW — digest, disjointness, category balance
```

**Structure Decision**: The testable logic moves out of the notebook and into
`EvoScientist/skills/jspace-research-operations/scripts/`, which already holds
`validate_observation.py` and is the directory the constitution names as binding
J-space work. The notebook keeps only constant declarations, the ratification
gate, and the measurement loop. Stage 2 put everything in one 18 KB cell, which
is precisely why its three declared-but-unconsumed constants were invisible until
an audit read the source — nothing about that cell was reachable by a test.

Tests live under `tests/jspace/` to match the repo's existing `tests/` layout and
run under the standard `uv run pytest`. The preflight module must import cleanly
without `torch` or `jlens` present, so tensor-contract assertions take already-
extracted metadata (shape, dtype string, device string) rather than live tensors.

**Branch dependency (stated assumption)**: `sakshi notes/` and the
`jspace-research-operations` skill are tracked on `docs/jspace-research-operations`
(PR #2), not on `main` — verified with `git ls-tree main`, which returns nothing
for either path. The Stage 2b deliverables therefore branch from that branch, or
from `main` after #2 merges. This gates **the whole feature**, not only the
notebook: the modules are written into that skill directory, so it must exist
first. PRs #5 and #6 remain genuinely unrelated.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Logic split across a Python module and a notebook, rather than one self-contained notebook as in Stage 2 | US3 and FR-009 require the preflight be exercisable against a broken configuration with no GPU and no measurement. That is only possible if it is importable and testable. | Keeping everything in the notebook is simpler to read in one sitting and is what Stage 2 did. It is also the direct cause of the audit finding: three declared constants were never consumed, and no test could have caught it because no code was reachable from a test. |
| Three new modules rather than one | Each has a different test surface: the manifest module needs no numerics, the endpoint module needs no I/O, the preflight module needs neither. Merging them would force every test to carry the union of their fixtures. | One `stage2b.py` would be fewer files, but the preflight's whole value is that it runs in a bare environment; folding the endpoint's numerical code into it would pull `numpy`/`scipy` into that import path. |
