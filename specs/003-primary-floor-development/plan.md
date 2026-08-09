# Implementation Plan: Primary-Floor Development Study

**Branch**: `003-primary-floor-development` | **Date**: 2026-08-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/003-primary-floor-development/spec.md`

## Summary

Build a separate, development-only instrument that evaluates the frozen prompt
generator behind Option A without inspecting or selecting favorable scientific
prompts. The design uses 29 independently seeded 20-prompt blocks, each balanced
at four prompts across the five Stage 2b categories. All 580 candidates, including
116 arithmetic candidates, are generated, identified, deduplicated, and hashed
before any eligibility measurement.

Each block reuses the existing four-layer, dual-floor, fifth-percentile guard and
18/20 plus 3/4-per-category coverage rules. A generator version is ready only for
independent preregistration review when all 29 blocks meet coverage under both
floors, every candidate is accounted for, and all H1-H5 analyses are present or
explicitly unresolved. Any failed block stops that generator version before a
revised pilot. The plan authorizes implementation and CPU-only synthetic
validation only. It does not authorize model access, GPU execution, a revised
pilot, confirmation access, artifact transfer, thresholds, or a scientific pass.

## Technical Context

**Language/Version**: Python 3.12.11 in the live local environment; project
compatibility remains Python 3.11 or newer

**Primary Dependencies**: Existing standard library, NumPy 2.5.1, and SciPy
1.18.0; reuse the Stage 2b endpoint rank and dual-floor primitives; no new
dependency planned. The future runtime remains bound to Qwen/Qwen3-1.7B revision
`70d244cc86ccca08cf5af4e1e306ecf908b1ad5e` and the existing pinned Jacobian
Lens identities

**Storage**: Canonical, content-addressed JSON manifests, development evidence,
and decision packets; an unexecuted notebook may define a later runtime surface

**Testing**: `pytest`, Ruff lint and format checks, ordinary notebook-cell parse,
recursive schema corruption tests, deterministic digest checks, and
`git diff --check`

**Target Platform**: Local macOS CPU for implementation and synthetic validation;
a separately authorized Colab GPU runtime is a future execution surface only

**Project Type**: Scientific research instrument implemented as import-light
Python modules, validators, contracts, and a thin notebook boundary

**Performance Goals**: CPU validators recompute all 29 block guards, 2,320
prompt-layer loci, dual-floor eligibility, H1-H5 summaries, and the final decision
without model or GPU access; no silent or partial success is permitted

**Constraints**: Zero access to pilot or confirmation prompt text at development
runtime; zero item-level selection after measurement; exactly 80 primary-floor
denominators per block guard; both floors retained; complete missingness
accounting; no 8×8 fitted/broken-map transport because it does not answer H1-H5;
no executable launch packet under the current authorization

**Scale/Scope**: 29 blocks × 20 candidates = 580 candidates; five categories ×
four prompts per block; 116 arithmetic candidates; layers 6, 13, 20, and 26; two
required floors; five mechanism hypotheses; one binary stop-or-review packet

## Constitution Check

*GATE: Passed before Phase 0 research and re-checked after Phase 1 design.*

### Before research

- **Correctness before minimality**: PASS. The design reproduces the complete
  20-prompt guard and coverage path rather than replacing it with a favorable
  arithmetic-only proxy.
- **Evidence proportional to risk**: PASS. The 29-block count follows an exact
  binomial reliability calculation. H1-H5 remain descriptive because no lawful
  mechanism effect size exists for power.
- **Never game verification**: PASS. All candidates are frozen before
  measurement, and any of the 29 blocks failing coverage stops the generator
  version.
- **Declared means consumed**: PASS BY DESIGN. Every generation rule, identity,
  floor, guard rule, coverage constant, hypothesis feature, and decision rule has
  a named validator or analysis consumer.
- **The record must not overstate the work**: PASS. The only positive output is
  readiness for independent preregistration review. The schema rejects pilot
  passes, thresholds, confirmation claims, scientific gates, and evidence above
  class 1.
- **Preregister, then execute**: PASS. The complete corpus, analysis, identities,
  missingness policy, and stop rule must freeze before measurement. The 29-block
  design is proposed here for independent review and ratification before any run.
- **Dr. Mani ratifies execution**: PASS. Model access, GPU use, and any parameter
  that changes measurement remain blocked pending a separate exact-scope
  authorization.
- **Artifacts stay put**: PASS. No evidence transfer or download is included.
- **Branch per concern**: PASS. Planning is isolated on local branch
  `003-primary-floor-development`; no commit or push is implied.

### After design

PASS. Phase 1 keeps the development schema separate from the spent pilot schema,
binds source identities externally, preserves every candidate through terminal
accounting, and defines fail-closed stop transitions. The following are explicit
future gates, not unresolved technical clarifications:

1. independent review and Dr. Mani's ratification of the 29-block generator,
   feature definitions, and decision rule;
2. exact content identities for an implemented notebook and code bundle;
3. separate development-run and GPU authorization;
4. separate artifact-transfer authorization, if ever requested; and
5. a new preregistration and authorization before any revised pilot.

## Project Structure

### Documentation (this feature)

```text
specs/003-primary-floor-development/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/
│   └── requirements.md
├── contracts/
│   ├── development-manifest.md
│   ├── development-preflight-api.md
│   ├── development-evidence-schema.md
│   └── decision-packet.md
└── tasks.md                              # Created only by /speckit-tasks
```

### Source Code (repository root)

```text
EvoScientist/skills/jspace-research-operations/scripts/
├── stage2b_endpoint.py                   # Reuse rank and dual-floor primitives
├── stage2b_development_manifest.py       # New frozen corpus and block identity
├── stage2b_development_analysis.py       # New guard, H1-H5, and decision logic
├── stage2b_development_preflight.py      # New import-light boundary checks
├── validate_stage2b_development.py       # New recursive offline validator
└── validate_observation.py               # Narrow dispatch only, if required

j-space-lab/
└── jspace_colab_stage2b_primary_floor_development.ipynb
                                             # New, unexecuted and authorization-false

tests/jspace/
├── fixtures/
│   └── stage2b_scientific_prompt_digests.json
├── test_stage2b_development_manifest.py
├── test_stage2b_development_analysis.py
├── test_stage2b_development_preflight.py
├── test_stage2b_development_validator.py
└── test_stage2b_development_notebook.py
```

**Structure Decision**: Extend the existing J-space research-operations script
and test surfaces with a separate development schema family. Reuse only stable
Stage 2b primitives. Do not broaden `jspace-observation-stage2b/v1`,
`stage2b_statistics.py`, the pilot authorization record, the pilot notebook, or
the pilot bundle and launch writers, because each is intentionally bound to the
completed 20-prompt pilot.

## Phase 0: Research Decisions

The detailed decisions and alternatives are recorded in [research.md](./research.md).
The planning baseline is:

1. Use 29 complete 20-prompt blocks, not a standalone arithmetic reservoir.
2. Make a frozen generator version and block seed the unit of evaluation.
3. Treat each block as successful only when both floors meet 18/20 total and 3/4
   in every category at every selected layer.
4. Require 29 of 29 successes. The one-sided 95% exact lower bound for block
   success is `0.05^(1/29) = 0.9018553723`, making 29 the minimum count that
   clears a 0.90 reliability target when every block succeeds.
5. Keep H1-H5 descriptive and block-aware. No mechanism threshold is invented
   from the missing pilot artifact or the two observed exclusions.
6. Use a separate development manifest, evidence schema, preflight, validator,
   and decision packet. Expected identities enter validators independently.
7. Defer executable bundle and launch writers until Dr. Mani separately approves
   a development execution surface.

All technical clarifications are resolved. Scientific ratification and execution
approval are authority gates rather than technical unknowns.

## Phase 1: Design and Contracts

### 1. Frozen generator and manifest

The manifest defines exactly 29 ordered blocks. Each block receives an independent
seed from a fixed namespace and contains exactly four candidates from each of the
five Stage 2b categories. Arithmetic candidates are produced by a balanced,
predeclared schedule of template surface and operation families. All generation
parameters, prompt bytes, stable IDs, exact and normalized digests, candidate
ordinals, categories, blocks, and template families freeze before measurement.

Disjointness uses a digest-only registry committed from the 200 scientific prompt
identities. The development runtime receives no pilot or confirmation prompt
text. Exact or normalization-equivalent collisions follow one frozen rejection
and replacement rule before the manifest freezes. No collision discovered after
measurement may alter the corpus.

Contract: [development-manifest.md](./contracts/development-manifest.md)

### 2. Measurement and block guard

For every candidate and each of the four selected layers, retain the model target
attestation, tokenizer features, output score, primary floor score, sensitivity
floor score, and declared H1-H5 features. Each block derives one primary-floor
guard from its 80 retained primary denominators using the unchanged 0.05 linear
quantile rule, then applies that scalar to both floor constructions without
another model or lens pass.

The new analysis module may reuse target-rank, normalized-rank, and dual-floor
helpers from `stage2b_endpoint.py`. It must not call pilot inference or threshold
derivation. Every missing or excluded locus remains in the artifact with its
reason and candidate identity.

Contract: [development-evidence-schema.md](./contracts/development-evidence-schema.md)

### 3. H1-H5 analysis

One frozen candidate-level table contains block, category, template family,
operation, both floor denominators and guard margins, eligibility, tokenizer
features, target features, and missingness.

- **H1 prompt construction**: compare the full prespecified predictive model
  with surface-template, operation, and interaction features ablated.
- **H2 tokenization**: compare the same full model with prompt length, final-token
  boundary, target-piece length, and leading-space or piece-boundary features
  ablated.
- **H3 target properties**: compare the full model with argmax tie count, top-1
  versus top-2 margin, normalized target logit, and output entropy ablated.
- **H4 floor geometry**: report paired sensitivity-minus-primary denominator and
  guard-margin differences plus primary-ineligible and sensitivity-eligible
  discordance.
- **H5 global guard interaction**: compare arithmetic and other-category
  lower-tail guard margins and retain each block's exact coverage result.

H1-H3 use leave-one-block-out predictive loss so records sharing one derived guard
never cross training and evaluation folds. Each hypothesis has structural status
`defined`, `undefined`, or `stopped`, plus interpretation `consistent`,
`inconsistent`, or `unresolved`. These are descriptive mechanism diagnostics,
not separate scientific gates and not a winner-selection procedure.

### 4. Preflight and source binding

An import-light preflight validates the exact manifest and digest-only exclusion
registry before any measurement input opens. It requires all pilot, confirmation,
artifact-transfer, and GPU authorization fields to remain false in canonical
source. Model, tokenizer, lens, decoding, code, manifest, and analysis identities
must match independently supplied expectations.

The future execution authorization schema is documented but not materialized.
Pilot authorization cannot be reused or reinterpreted.

Contract: [development-preflight-api.md](./contracts/development-preflight-api.md)

### 5. Evidence validation and decision

The offline validator recursively rejects unknown fields and independently
recomputes manifest linkage, all 29 block guards, both-floor eligibility, coverage,
candidate accounting, H1-H5 record closure, stop conditions, and the final
outcome. The packet has exactly two outcomes:

```text
ready_for_independent_preregistration_review
stop_estimand_before_revised_pilot
```

Universal stops run first. Otherwise review readiness requires all 580 candidates
accounted, no post-freeze item selection, 29 of 29 blocks passing under both
floors, complete H1-H5 outputs, and no forbidden scientific or execution claim.

Contract: [decision-packet.md](./contracts/decision-packet.md)

### 6. Notebook boundary

The notebook is thin: environment and model plumbing only. It imports tested
modules, ships with every authorization flag false, and refuses before model or
GPU access unless a future content-addressed development authorization is
independently supplied. It receives only the frozen development manifest and
digest-only scientific exclusion registry. It validates evidence before any
content-addressed write and contains no transfer cell, pilot threshold, pilot
gate, confirmation path, or scientific decision.

Bundle and launch writers are contract-deferred. Their source is not created by
this feature until Dr. Mani explicitly approves an execution-surface task.

### 7. Agent context

The managed Spec Kit section in `AGENTS.md` points to this plan. Content outside
the managed markers remains unchanged.

## Test Strategy

Targeted CPU-only validation after implementation:

```bash
uv run pytest \
  tests/jspace/test_stage2b_development_manifest.py \
  tests/jspace/test_stage2b_development_analysis.py \
  tests/jspace/test_stage2b_development_preflight.py \
  tests/jspace/test_stage2b_development_validator.py \
  tests/jspace/test_stage2b_development_notebook.py -v
```

Existing Stage 2b regression surface:

```bash
uv run pytest \
  tests/jspace/test_stage2b_manifest.py \
  tests/jspace/test_stage2b_endpoint.py \
  tests/jspace/test_stage2b_statistics.py \
  tests/jspace/test_stage2b_preflight.py \
  tests/jspace/test_stage2b_validator.py \
  tests/jspace/test_stage2b_notebook.py \
  tests/jspace/test_stage2b_pilot_bundle.py \
  tests/jspace/test_stage2b_pilot_launch.py \
  tests/jspace/test_stage2b_pilot_harness.py -v
```

Widen only after focused checks pass:

```bash
uv run pytest tests/jspace -v
uv run ruff check .
uv run ruff format --check .
git diff --check
```

Passing these checks verifies design and implementation behavior only. It does
not authorize model loading, GPU use, prompt access, artifact transfer, or study
execution.

## Settled / Pending / Deferred

### Settled by this plan

- separate development schema and pipeline;
- 29 frozen, balanced 20-prompt blocks and 580 total candidates;
- generator and block as units of evaluation, never measured items;
- unchanged four-layer, two-floor, per-block guard and coverage rules;
- 29-of-29 block success for a review recommendation;
- block-aware descriptive H1-H5 analysis;
- exact two-outcome packet and fail-closed universal stops;
- local CPU implementation and synthetic validation only.

### Pending ratification or implementation

- independent adversarial review of the proposed 29-block design;
- Dr. Mani's ratification of generator families, seed namespace, feature
  definitions, block count, and decision rule;
- `/speckit-tasks` decomposition;
- implementation of manifest, analysis, preflight, validator, notebook source,
  and tests;
- exact frozen corpus and source identities.

### Deferred behind explicit authorization

- executable bundle and launch-preparation source;
- model or GPU execution;
- development evidence artifact creation or transfer;
- any generator revision after observed evidence;
- a revised Stage 2b pilot, confirmation access, thresholds, Stage 3, or
  downstream use.

## Complexity Tracking

No constitution violation or exception is required. The separate schema family
adds surface area to preserve the stricter pilot contracts rather than weakening
them.
