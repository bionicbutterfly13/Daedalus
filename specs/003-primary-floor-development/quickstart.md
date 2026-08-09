# Quickstart: Validate the Primary-Floor Development Design

This guide is for CPU-only implementation validation after the feature is built.
It does not run a model, allocate a GPU, access pilot or confirmation prompts,
create scientific evidence, or authorize execution.

## Prerequisites

- Work from repository root on branch `003-primary-floor-development`.
- Use the repository's `uv` environment.
- Keep the full 200-prompt scientific manifest out of runtime fixtures. Tests use
  a digest-only exclusion registry or synthetic prompts.
- Do not create or supply a development authorization record.
- Do not execute the development notebook.

Verify the import path before tests:

```bash
uv run python -c "import EvoScientist; print(EvoScientist.__file__)"
```

Expected path:

```text
/Volumes/Asylum/archimedes/EvoScientist/__init__.py
```

## 1. Manifest and freeze validation

```bash
uv run pytest tests/jspace/test_stage2b_development_manifest.py -v
```

Expected evidence:

- exactly 29 blocks, 20 candidates per block, and 580 candidates;
- exactly four candidates from each category in every block;
- deterministic block seeds, generation parameters, candidate IDs, and digests;
- exact and normalized overlap rejection against a digest-only 200-prompt
  registry;
- no denominator, eligibility, tokenization outcome, target outcome, or effect
  input to generation; and
- any post-freeze mutation changes identity and fails validation.

## 2. Analysis and decision validation

```bash
uv run pytest tests/jspace/test_stage2b_development_analysis.py -v
```

Expected evidence:

- one 0.05 linear guard recomputes from exactly 80 primary denominators per
  block;
- the same block guard applies to primary and sensitivity floors;
- all 2,320 candidate-layer loci remain accounted for;
- 18/20 and 3/4 coverage recomputes per block, floor, and layer;
- H1-H3 folds hold out complete blocks;
- H4 remains paired by candidate;
- H5 retains per-block guard and coverage structure;
- 29 of 29 successes recompute the one-sided 95% lower bound
  `0.9018553723`; and
- one failed block returns `stop_estimand_before_revised_pilot`.

## 3. Preflight boundary validation

```bash
uv run pytest tests/jspace/test_stage2b_development_preflight.py -v
```

Expected evidence:

- expected manifest and exclusion-registry digests are mandatory and external;
- self-attested source identities fail;
- all canonical authorization and transfer flags remain false;
- pilot authorization cannot be reused;
- wrong model, tokenizer, lens, decoding, layer, code, or analysis identity fails
  before measurement; and
- importing preflight requires no model, Torch, Jacobian Lens, network, or GPU.

## 4. Recursive evidence validation

```bash
uv run pytest tests/jspace/test_stage2b_development_validator.py -v
```

Expected evidence:

- recursive unknown fields fail;
- every guard, denominator, margin, eligibility state, coverage record, and
  candidate total recomputes;
- missing and excluded candidates remain explicit;
- floor disagreement remains visible;
- exact H1-H5 closure is required;
- decision input and packet outcome recompute; and
- pilot thresholds, confirmation results, scientific gates, transfer claims,
  and evidence above class 1 are rejected.

## 5. Notebook source validation

```bash
uv run pytest tests/jspace/test_stage2b_development_notebook.py -v
```

Expected evidence:

- the notebook is valid unexecuted JSON;
- all authorization flags ship false;
- preflight precedes model import, weight load, and GPU allocation;
- tested modules hold manifest, analysis, and validation logic;
- the notebook receives only the frozen development manifest and digest-only
  scientific exclusion registry;
- no pilot or confirmation view is referenced;
- no pilot threshold, scientific decision, transfer cell, or automatic launch
  path exists; and
- all ordinary code cells parse.

## 6. Focused feature gate

```bash
uv run pytest \
  tests/jspace/test_stage2b_development_manifest.py \
  tests/jspace/test_stage2b_development_analysis.py \
  tests/jspace/test_stage2b_development_preflight.py \
  tests/jspace/test_stage2b_development_validator.py \
  tests/jspace/test_stage2b_development_notebook.py -v
```

Passing this gate means the development design is implemented and CPU-validated.
It does not mean the generator works on real model data.

## 7. Existing Stage 2b regression gate

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

This proves feature 003 did not weaken the completed pilot's manifest, endpoint,
statistics, authorization, schema, notebook, bundle, launch, or harness contracts.

## 8. Widened repository checks

Run only after focused checks pass:

```bash
uv run pytest tests/jspace -v
uv run ruff check .
uv run ruff format --check .
git diff --check
```

Report each result separately. Do not infer a full-suite pass from focused tests.

## 9. Required negative scenarios

The synthetic test suite must include:

1. one exact scientific-prompt digest collision;
2. one normalization-equivalent collision;
3. duplicate candidate ID, digest, block seed, and template slot;
4. one 19-candidate or category-imbalanced block;
5. one post-freeze replacement;
6. one nonfinite primary denominator;
7. one guard derived from 79 or 81 values;
8. one separate sensitivity-floor guard;
9. one primary-only block success with sensitivity failure;
10. one of 29 blocks failing 3/4 arithmetic coverage;
11. one missing H1-H5 record;
12. one item-level cross-validation fold leaking a block;
13. one forbidden pilot threshold or confirmation field;
14. one self-attested source identity; and
15. one attempted pilot-authorization reuse.

Every case fails closed with a stable reason code.

## 10. Stop after validation

Do not proceed from CPU validation to a real run. The next lawful sequence is:

1. independent adversarial review;
2. Dr. Mani's ratification of the generator and numeric design;
3. exact source freeze;
4. separate development-run and GPU authorization; and
5. only then, a bounded runtime attempt with artifact transfer still false.
