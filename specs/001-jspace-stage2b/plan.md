# Implementation Plan: Stage 2b J-space discrimination

**Branch**: `recover/jspace-stage2b-contract`
**Specification**: [spec.md](./spec.md)
**Scope**: ratified pilot-protocol implementation and CPU validation; no pilot,
confirmation, artifact transfer, commit, push, or publication

## Objective

Produce one auditable Stage 2b pilot instrument in which the ratified target,
two decoded floors, fully crossed 8×8 controls, two-stage denominator derivation,
coverage policy, crossed estimands, uncertainty engines, and threshold derivation
agree across producer, registry, artifact, validator, tests, and notebook.

The pilot emits measurements, estimates, intervals, and threshold-derivation
evidence. It does not emit a scientific pass/fail decision. The later confirmation
claim is specified so pilot outputs can be locked, but confirmation access and its
per-category coverage minimum remain outside this implementation phase.

Use status words independently:

- **RATIFIED**: approved protocol.
- **IMPLEMENTED**: source observed in this worktree.
- **VERIFIED**: fresh checks observed passing.
- **AUTHORIZED**: Dr. Mani approved one exact execution scope and source identity.

## Technical context

**Language/runtime**: Python 3.11 locally; pinned Colab runtime packages recorded by
the notebook and artifact
**Numerics**: NumPy with explicit `Generator(PCG64(seed))`; PyTorch only in the
runtime notebook path
**Instrument**: pinned Qwen model and Jacobian Lens revision already verified by
the excluded-input runtime smoke
**Persistence**: canonical content-addressed JSON; raw activations, maps, logits,
pilot artifact transfer, and confirmation inputs remain prohibited
**Testing**: `pytest`, Ruff, notebook ordinary-cell parsing, deterministic bundle
rebuild, and independent adversarial review
**Scale**: 20 prompts × 4 layers × 81 unique readouts = 6,480 unique readouts;
64 logical donor×map factorials per prompt-layer
**Constraints**: one model/lens pass per readout; retain raw normalized scores
before deriving NTA; no layer pooling; fixed floor-specific exclusion mask; no
implicit RNG selection; no decision block in a pilot artifact

**Numerical control construction**: one fitted-map SVD per selected layer, reused
for all eight Haar draws; one independent singular-value computation per realized
map; fixed implemented spectrum tolerances `rtol=1e-5`, `atol=1e-6`

**Source binding**: one external trusted launch preparer hashes exact notebook,
bundle, pilot-view, and authorization-record bytes into an exclusive directory;
the artifact validator receives those identities independently

No technical `NEEDS CLARIFICATION` remains for pilot implementation. Pilot GPU
authorization and the later confirmation category minimum are deliberate external
gates, not implementation unknowns.

## Constitution check

### Before design

- **Correctness before minimality**: PASS. The implementation must replace the
  obsolete single-stage denominator and unset-statistics paths rather than layer a
  second interpretation over them.
- **Evidence proportional to risk**: PASS. The exact model/lens compatibility and
  81-readout runtime path were checked in an excluded-input T4 smoke. Statistical
  implementation remains CPU-testable before any scientific input is accessed.
- **Never game verification**: PASS. Existing adversarial tests remain; new tests
  must cover each ratified rule and corrupted provenance.
- **Declared means consumed**: PASS BY DESIGN. Every protocol constant, derivation
  rule, seed identity, coverage threshold, and interval setting must have a named
  executable consumer and validator recomputation.
- **Record must not overstate work**: PASS BY DESIGN. Pilot output has no gate or
  decision, runtime extrapolation remains labelled, and raw-content digests remain
  runtime attestations rather than offline recomputations.
- **Preregister then execute**: PASS. Five statistical clarification decisions
  were ratified in `spec.md` before this implementation phase.
- **Execution boundary**: PASS. All execution flags remain false in canonical
  source; a separate content-addressed authorization is still required.

### After design

PASS with two intentional future gates:

1. the exact pilot authorization record and frozen notebook/bundle hashes; and
2. the confirmation sample's per-category coverage minimum.

Neither is required to implement or CPU-validate the pilot protocol.

## Phase 0: research decisions

The existing [research.md](./research.md) establishes the pinned Jacobian Lens
surface, transport semantics, tensor contracts, target rank, runtime package
boundary, and excluded-input Colab behavior. The 2026-07-30 addendum records:

- a two-stage fifth-percentile linear denominator derivation;
- category-balanced point estimates;
- category-stratified prompt resampling as primary uncertainty;
- prompt×donor×map product-weight sensitivity;
- fixed complete-case coverage rules;
- explicit NumPy `PCG64` and SHA-256-derived seeds;
- per-layer half-mean threshold derivation; and
- a later intersection-union confirmation claim.

The product-weight sensitivity is a diagnostic against crossed donor/map
dependence, not a replacement for the prompt-level primary analysis. The pilot has
only four prompts per category, so neither procedure is described as asymptotic
proof.

## Phase 1: design and contracts

### 1. Measurement and score retention

For each prompt-layer, persist or construct the lossless factorized score form:

```text
correct/fitted                          1
correct/broken by map draw             8
wrong/fitted by donor assignment       8
wrong/broken by donor × map           64
                                      --
unique readouts                        81
logical donor×map factorials           64
```

Both `input_embedding_decoded` and `layer0_residual_decoded` floor scores plus the
output score are retained before NTA is computed. The producer completes all 80
prompt-layer loci, derives one primary-floor denominator guard, then computes both
NTA trees from retained scores without another model/lens pass.

### 2. Deterministic crossing and bootstrap identities

The crossing registries are generated, not hand-authored:

```text
donor-0..donor-7:
  first8(SHA256("jspace-stage2b/v1|donor-assignment|<i>"))
map-0..map-7:
  first8(SHA256("jspace-stage2b/v1|broken-map|<i>"))
```

All integers are unsigned big-endian. The full digest, integer, namespace, index,
and `PCG64` identity are retained. Duplicate IDs or seeds fail closed.

Bootstrap seed:

```text
first8(SHA256("jspace-stage2b/v1|<run_mode>|bootstrap-v1"))
```

The implementation constructs `numpy.random.Generator(numpy.random.PCG64(seed))`
explicitly and records the pinned NumPy version.

### 3. Point estimates and exclusions

After exact 8×8 validation:

```text
correct_effect[p,l,m] = A[p,l] - B[p,l,m]
wrong_effect[p,l,d,m] = C[p,l,d] - D[p,l,d,m]
interaction[p,l,d,m]  = correct_effect[p,l,m] - wrong_effect[p,l,d,m]
```

Within each prompt-layer, correct effects average equally over eight maps;
wrong/interaction effects average equally over all 64 donor×map pairs. Layer
statistics are category-balanced: arithmetic mean inside each category, followed
by an equal mean of the five category means.

If a floor denominator is nonfinite or not greater than the derived guard, the
entire prompt-layer is excluded for that floor. The mask is fixed across bootstrap
replicates. A pilot layer-floor is defined only with at least 18/20 prompts and at
least 3/4 prompts in each category.

### 4. Uncertainty

Every defined floor-layer-estimand has:

- 20,000 category-stratified prompt-resampling replicates; and
- 20,000 prompt×donor×map product-weight replicates using independent mean-one
  `Exp(1)` weights.

Each reports the two-sided 99% percentile interval using linear quantiles at
0.005 and 0.995. All 20,000 statistics must be finite. Layers are never pooled.

### 5. Pilot threshold derivation

For each layer, derive:

```text
SPEC_MIN_EFFECT = 0.5 × primary-floor correct-effect mean
INTERACTION_MIN_EFFECT = 0.5 × primary-floor interaction mean
```

All eight source means must be defined, finite, and positive. Otherwise the pilot
emits no usable threshold vectors and confirmation remains blocked. The pilot does
not apply these thresholds or emit a decision.

### 6. Artifact and validator

The aggregate must be sufficient for independent recomputation of:

- the 80-denominator source vector and its digest;
- both NTA trees and named floor difference;
- coverage and exclusion masks;
- per-prompt/layer effects;
- category-balanced means;
- both deterministic interval procedures; and
- the two four-layer threshold vectors.

Explicit allowed-field sets remain fail closed at every normative level. A pilot
artifact rejects any gate, scientific decision, confirmatory access, alternate
policy, or unknown field.

### 7. Notebook and authorization

Canonical notebook source ships with all execution flags false and no embedded
authorization record. Pilot launch consumes a separately approved,
content-addressed external record that authorizes the exact pilot view and frozen
source identities. The record ratifies the already specified protocol and
execution scope; it does not supply data-derived denominator or threshold values.

## Phase 2: implementation sequence

1. Add failing pure-function tests for seed derivation, denominator derivation,
   coverage, point statistics, both interval engines, and threshold derivation.
2. Implement pure statistical helpers with no model, lens, CUDA, or file writes.
3. Reconcile preflight registry and external authorization semantics.
4. Extend schema and validator recomputation, then add corruption tests.
5. Rewire the notebook to retain scores, derive once, compute locally, and emit no
   pilot decision.
6. Run focused tests, full J-space, full repository, Ruff, formatting check,
   notebook parsing, deterministic bundle checks, and `git diff --check`.
7. Freeze one candidate and obtain independent adversarial review.
8. Only after review GO, prepare exact notebook/bundle hashes and request separate
   pilot GPU authorization from Dr. Mani.

## Test strategy

Targeted commands:

```bash
uv run pytest tests/jspace/test_stage2b_endpoint.py -v
uv run pytest tests/jspace/test_stage2b_statistics.py -v
uv run pytest tests/jspace/test_stage2b_preflight.py -v
uv run pytest tests/jspace/test_stage2b_pilot_harness.py -v
uv run pytest tests/jspace/test_stage2b_notebook.py -v
uv run pytest tests/jspace/test_stage2b_validator.py -v
```

Required adversarial cases include altered seed namespace/digest/integer,
nonlinear quantile method, missing denominator source, a second model-pass path,
category pooling, layer pooling, variable exclusion masks, low coverage,
nonfinite replicates, default RNG use, donor/map dimension loss, altered threshold
source, and any pilot gate/decision field.

A full-suite result is separate evidence and must not be inferred from targeted
results.

## Settled / pending / deferred

### Settled

- model-argmax target, dual decoded floors, 20-prompt pilot identity;
- 8×8 crossing, 81-readout compact representation, provenance;
- denominator, seed, aggregation, exclusion, coverage, interval, threshold, and
  later global-claim rules;
- successful excluded-input T4 compatibility smoke;
- statistically complete source freeze and independent adversarial GO;
- exact-hash pilot launch packet and Dr. Mani's one-time authorization;
- isolated 20-prompt dual-floor fully crossed 8×8 pilot and retained-artifact
  validation.

### Pending

- decide how the primary-floor arithmetic coverage failure changes the next
  preregistered design;
- determine whether Stage 2b should stop as instrument ambiguity or run a new,
  separately authorized pilot under a revised protocol;
- ratify a confirmation per-category coverage rule only if a future pilot yields
  usable primary-floor threshold vectors.

### Deferred

- confirmation sample per-category coverage minimum;
- 180-prompt confirmation access and execution;
- artifact transfer, Stage 3, or downstream scientific use.

## Observed pilot result

The 2026-07-31 pilot completed under the exact source and authorization identities
recorded in `spec.md`. The sensitivity floor showed positive correct effects and
positive correct-versus-wrong interactions at all four selected layers under both
ratified 99% interval procedures. The primary floor was undefined because only two
arithmetic-completion prompts remained eligible at each layer, below the minimum
of three. Threshold derivation was therefore unavailable and confirmation remains
blocked. Publication of this bounded result does not transfer the retained Colab
artifact or authorize another scientific run.
