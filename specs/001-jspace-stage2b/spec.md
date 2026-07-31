# Feature Specification: Stage 2b J-space discrimination

**Feature Branch**: `001-jspace-stage2b`
**Created**: 2026-07-26
**Status**: Pilot observed 2026-07-31; sensitivity-floor effect positive; robust
result undefined because the primary floor failed category coverage; confirmation
blocked

## Authority and status vocabulary

This specification is governed by this file plus only the explicitly ratified
parts of `j-space-lab/STAGE2B_PREREGISTRATION_AMENDMENT_DRAFT.md` and
`STAGE2B_OPEN_PARAMETERS.md`.

- **RATIFIED** means approved scientific protocol.
- **IMPLEMENTED** means source exists in the recovery worktree. It does not imply
  ratification, test passage, pilot readiness, or execution authorization.
- **VERIFIED** requires a fresh observed test result. Notebook source-contract and
  primary-validator structure are verified below; real-runtime behavior is not.

## Clarifications

### Session 2026-07-30

- Q: How should the 20-prompt pilot establish `NTA_MIN_DENOMINATOR`? → A:
  Two-stage pilot: ratify the fifth-percentile linear derivation rule, collect raw
  scores, derive the guard, then compute NTA locally without another model pass.
- Q: How should donor/map variation enter Stage 2b pilot estimates and
  uncertainty? → A: Equal-weight donor/map effects within each prompt-layer, a
  category-stratified prompt bootstrap as primary, and a prompt×donor×map
  product-weight bootstrap as sensitivity; disagreement is `undefined`.
- Q: How should denominator-excluded prompt-layer-floor loci enter inference? →
  A: Complete-case without imputation; require at least 90% prompt coverage per
  layer and at least three pilot prompts per category, otherwise the layer-floor
  is `undefined`.
- Q: Which point statistic and interval engine should Stage 2b use per layer? →
  A: Category-balanced mean with two-sided 99% percentile intervals, 20,000
  replicates, a deterministic SHA-256-derived seed, and independent `Exp(1)`
  product weights for crossed sensitivity.
- Q: Which remaining seed, threshold, and gate package should be preregistered
  before the pilot? → A: SHA-256-derived donor/map seeds; per-layer thresholds
  equal to half each positive primary-floor pilot mean; correct effect and
  interaction both required across every layer, floor, and uncertainty method
  using an intersection-union conjunction.

## Scientific purpose and boundary

Stage 2b asks whether the fitted Jacobian map carries target-relative structure
that survives controls for activation identity and map fit. The target is the
pinned model's own output-position argmax. This estimates progress toward the
model's eventual token, not truth or task correctness.

The study is observation-only. No activation is fed back into the model. This
specification did not itself authorize execution. The 20-prompt pilot later ran
under a separate hash-bound authorization record; that consumed authorization
does not authorize a repeat, confirmation access, or artifact transfer.

## Ratified measurement contract

### Pilot partition identity

The stratified 20-ID pilot view and ordered-view digest
`8ed0a0092ec3989f6bd8005ae4360de86174764a946af75b35ea30932ca719b5`
are RATIFIED. The view contains `s000`–`s003`, `s040`–`s043`, `s080`–`s083`,
`s120`–`s123`, and `s160`–`s163`. Partition ratification does not authorize access
to the model/lens or any pilot execution; the 180-ID complement remains
inaccessible.

### Target and two floors

- **RATIFIED** target source: `model_argmax`.
- **RATIFIED** primary floor: `input_embedding_decoded` at the measured position.
- **RATIFIED** sensitivity floor: `layer0_residual_decoded` at the same position.
- Every target-relative readout MUST record both NTA values and the named
  `sensitivity_minus_primary` difference. The more favorable floor MUST NOT be
  selected after observation.
- Any later required-gate reversal between floors MUST be reported as
  prompt-floor dependence; the result MUST NOT be described as robust.

For floor `f`:

```text
rank1(t, r) = count(logits_r > logits_r[t]) + 1
s(r)        = -log(rank1(t, r)) / log(vocab_size)
NTA_f(r)    = (s(r) - s(f)) / (s(output) - s(f))
```

**RATIFIED denominator strategy:** the pilot is a two-stage calculation within one
authorized run. Stage 1 retains `s(output)`, both floor scores, and every factorized
readout score for all 20 prompts × 4 layers before computing NTA. It then computes
the 0.05 quantile of the 80 primary-floor denominators
`s(output) - s(input_embedding_decoded)` using the fixed linear quantile estimator.
That finite result becomes `NTA_MIN_DENOMINATOR` only if it is strictly positive;
otherwise the pilot stops and emits no NTA result. Stage 2 computes both-floor NTA
and explicit floor-specific exclusions from the retained scores without another
model or lens pass. The derived value, estimator identity, source floor, source
count, and denominator vector digest MUST be retained. The same derived scalar
guard applies to both floor constructions.

The numeric guard is therefore derived, not selected, during the pilot. The
ratified complete-case exclusion and coverage policy appears below.

### Fully crossed 8×8 controls

For every prompt and selected layer, measurement MUST fully cross:

- eight wrong-activation donor assignments; and
- eight broken-map draws.

Each of the 64 donor×map logical combinations has four factorial cells:

| Cell | Activation | Map |
|---|---|---|
| `correct_act_fitted_map` | recipient/correct | fitted |
| `correct_act_broken_map` | recipient/correct | selected broken-map draw |
| `wrong_act_fitted_map` | selected donor/wrong | fitted |
| `wrong_act_broken_map` | selected donor/wrong | selected broken-map draw |

A lossless compact representation is permitted and preferred. It contains exactly
81 unique readouts per prompt/layer:

```text
1 shared correct/fitted
+ 8 map-indexed correct/broken
+ 8 donor-indexed wrong/fitted
+ 64 donor×map wrong/broken
= 81 unique readouts
```

It MUST losslessly reconstruct all 64 logical factorial combinations. A flat list
of 64 four-cell records is not mandatory and MUST NOT be mistaken for 64 unique
readouts.

### Required crossing provenance

The measurement artifact MUST preserve, for every relevant dimension:

- donor-assignment ID;
- recipient prompt digest and recipient→donor prompt digest;
- broken-map draw ID;
- donor and map seeds once ratified;
- broken-map hash; and
- complete per-realized-map singular-spectrum evidence under declared numerical
  tolerances; and
- prompt, layer, model, lens, and code identities.

The eight donor assignments and eight map draws MUST remain distinguishable. The
artifact MUST not average away donor, map, or donor×map identity.

### Ratified crossed estimands and uncertainty structure

For every prompt `p`, layer `l`, donor assignment `d`, map draw `m`, and floor,
define:

```text
correct_effect[p,l,m] = A[p,l] - B[p,l,m]
wrong_effect[p,l,d,m] = C[p,l,d] - D[p,l,d,m]
interaction[p,l,d,m]  = correct_effect[p,l,m] - wrong_effect[p,l,d,m]
```

Within each prompt-layer, the point estimates are the equal-weight arithmetic
means over every applicable declared draw: `correct_effect` over eight maps and
`wrong_effect` and `interaction` over all 64 donor×map pairs. Donor/map identities
remain intact in the retained artifact and are aggregated only after complete
crossing validation.

The primary uncertainty procedure resamples prompts with replacement separately
within each of the five preregistered categories, preserving the category counts,
and recomputes the statistic independently for each layer. It never pools layers.
The required sensitivity procedure independently product-weights prompt,
donor-assignment, and map-draw levels and recomputes the same per-layer statistic.
If a later required conclusion differs between the primary and crossed sensitivity
procedures, that conclusion is `undefined`, not pass.

### Ratified exclusion and coverage policy

The denominator is shared by every readout at one prompt-layer-floor. If it is
nonfinite or not greater than the derived guard, the whole locus is excluded for
that floor only. No missing NTA value is imputed, converted to zero, borrowed from
the other floor, or silently removed before its reason and identity are retained.

Pilot inference is complete-case within each floor and layer using a fixed
exclusion mask across every bootstrap replicate. A layer-floor requires at least
18 of 20 eligible prompts and at least three eligible prompts from each of the five
four-prompt categories. Below either bound, every inferential result for that
layer-floor is `undefined`. A later robust conclusion requires defined results
under both ratified floors. Confirmation retains the 90% per-layer rule; its
per-category minimum remains a separate pre-confirmation decision.

### Ratified point statistic and interval engine

For each defined floor, layer, and estimand, first compute the arithmetic mean of
eligible prompt-level effects within each category, then take the equal-weight
mean of the five category means. Categories therefore retain equal influence when
floor exclusions leave different eligible counts.

The primary interval uses 20,000 category-stratified prompt-resampling replicates.
The crossed sensitivity uses 20,000 replicates with mutually independent,
mean-one `Exp(1)` weights at the prompt, donor-assignment, and map-draw levels;
each logical observation receives the product of its applicable weights, and
weights are normalized within the relevant category/draw mean. Both procedures
report the two-sided 99% percentile interval using fixed linear quantiles at
`0.005` and `0.995`. An interval is `undefined` unless all 20,000 replicate
statistics are finite and the ratified coverage policy holds.

The pseudorandom generator seed is the unsigned big-endian integer represented by
the first eight bytes of:

```text
SHA256("jspace-stage2b/v1|<run_mode>|bootstrap-v1")
```

where `<run_mode>` is exactly `pilot` or `confirmatory`. The namespace string,
full digest, derived integer, generator family/version, replicate count, quantile
method, and interval level MUST be retained.

The exact bit generator is NumPy `PCG64` under the pinned NumPy runtime. Calls to
distribution helpers, including `Exp(1)`, MUST use an explicitly constructed
`numpy.random.Generator(numpy.random.PCG64(seed))`; `default_rng` is not an
acceptable implicit generator selection.

### Ratified donor and map seed vectors

The eight donor assignments use IDs `donor-0` through `donor-7`; the eight
broken-map draws use IDs `map-0` through `map-7`. For zero-based index `i`, each
seed is the unsigned big-endian integer represented by the first eight bytes of:

```text
donor seed = SHA256("jspace-stage2b/v1|donor-assignment|<i>")
map seed   = SHA256("jspace-stage2b/v1|broken-map|<i>")
```

The literal namespace, index, full digest, derived integer, and `PCG64` identity
MUST be retained. Any duplicate ID or seed is a preflight failure; no collision
may be repaired by choosing another value after the fact.

### Ratified threshold derivation and global claim

The pilot emits estimates and threshold-derivation evidence only, never a
scientific pass/fail decision. For each selected layer `l`, after all coverage and
finite-replicate checks:

```text
SPEC_MIN_EFFECT[l] =
    0.5 * primary_floor_correct_effect_mean[l]

INTERACTION_MIN_EFFECT[l] =
    0.5 * primary_floor_interaction_mean[l]
```

All eight source means must be defined, finite, and strictly positive. If any is
not, threshold derivation stops and confirmation is not authorized. The resulting
four-value vectors, their source estimates, factor `0.5`, floor identity, layer
order, pilot artifact identity, and derivation-code identity MUST be retained and
locked before confirmation access. The primary-floor-derived vectors are then
applied unchanged to both floors.

The later global confirmation claim is one intersection-union conjunction. For
every selected layer, both floors, and both the primary prompt bootstrap and
crossed sensitivity procedure, the two-sided 99% interval's lower bound must
exceed the corresponding locked threshold for:

1. the correct-activation fitted-over-broken effect; and
2. the correct-versus-wrong interaction.

No extra multiplicity adjustment is applied to this single all-components-required
claim. A defined component that does not clear its threshold makes the global
claim fail. If no component fails but at least one is undefined, the global claim
is `undefined`. Only when every component clears may it pass. Secondary and
descriptive analyses cannot alter this conjunction.

## Functional requirements

- **FR-001**: Compute direct 1-indexed strict-`>` target rank and verify parity
  against the reference convention on a fixed synthetic probe.
- **FR-002**: Compute the ratified primary and sensitivity NTA constructions and
  their named difference without post-observation floor selection.
- **FR-002a**: In pilot mode, retain all raw score components before NTA, derive
  `NTA_MIN_DENOMINATOR` exactly once with the ratified fifth-percentile linear
  rule, fail if the result is nonpositive or nonfinite, and compute NTA from the
  retained scores without a second model/lens pass.
- **FR-003**: Materialize the complete 8×8 logical factorial from either the compact
  81-readout form or an equivalent lossless representation.
- **FR-004**: Wrong activations MUST be real residuals from different prompts and
  MUST preserve recipient→donor provenance.
- **FR-005**: Broken maps MUST preserve the declared geometric invariants and MUST
  preserve draw ID, seed, and map hash.
- **FR-006**: Preflight MUST reject any crossing other than eight unique donor
  assignments and eight unique map draws, and MUST reject missing IDs or seeds.
- **FR-007**: Derive exactly eight donor and eight map IDs/seeds from the ratified
  SHA-256 namespaces, retain their complete derivation evidence, and reject any
  mismatch or collision.
- **FR-008**: Artifact validation MUST establish exactly 81 unique readouts and 64
  reconstructable logical combinations per prompt/layer, exact 20×4 locus coverage,
  recomputable prompt-pair linkage, and explicit runtime content-hash attestations.
- **FR-008a**: Compute equal-weight per-prompt/layer correct, wrong, and
  interaction effects only after validating the full crossing; run the primary
  prompt bootstrap within category and the product-weight prompt×donor×map
  sensitivity independently per layer.
- **FR-008b**: Preserve a floor-specific exclusion mask, never impute excluded
  loci, enforce 18/20 per-layer and 3/4 per-category pilot coverage, and emit only
  `undefined` inferential results when coverage fails.
- **FR-008c**: Compute the category-balanced mean and exact 20,000-replicate
  primary and crossed-sensitivity percentile intervals with the ratified weight,
  quantile, and deterministic seed rules.
- **FR-008d**: Derive and retain the two four-layer threshold vectors without a
  confirmatory decision; later evaluate the locked correct-effect and interaction
  conjunction without layer pooling or post-pilot gate changes.
- **FR-009**: The aggregate record MUST remain sufficient to recompute every
  eventually ratified estimate or decision without notebook source.
- **FR-010**: The held-out manifest and Stage 1 anchor exclusions remain preflight
  checks. Ratification of a subset does not authorize access or execution.

## Acceptance scenarios

1. Given valid synthetic factorized inputs with 8 donor IDs and 8 map IDs, the
   materializer returns 81 unique readouts and 64 logical four-cell combinations.
2. Removing, duplicating, or mis-keying any donor, map, matrix row, matrix column,
   seed, prompt-pair digest, prompt/layer locus, or runtime hash identity causes
   preflight or validation failure.
3. Given the complete pilot score table, the producer derives one positive finite
   denominator guard from exactly 80 primary-floor denominators, retains its
   derivation evidence, and computes primary NTA, sensitivity NTA, and
   `sensitivity_minus_primary` without another model/lens pass; an excluded floor
   cannot silently produce a numeric difference.
4. The dedicated synthetic harness exercises the two-floor 8×8 path without using
   any real pilot or confirmatory prompt and cannot emit a scientific decision.
5. Notebook source-contract and primary-validator structure are described as
   verified only after their dedicated tests have been run and observed.
6. A bootstrap replicate that pools layers, changes category counts, drops a
   donor/map level before weighting, or reports pass when primary and sensitivity
   disagree is invalid.
7. An excluded locus remains present with its floor and reason, contributes to no
   point estimate or bootstrap replicate, and cannot leave a defined layer-floor
   result when either pilot coverage bound fails.
8. Changing the category weights, interval quantiles, replicate count,
   product-weight distribution, seed namespace, derived seed, or generator
   identity causes validation failure.
9. A pilot with any nonpositive/undefined source effect emits no threshold vector,
   and a confirmation artifact cannot pass unless every layer/floor/method
   correct-effect and interaction lower bound clears its locked layer threshold.

## Explicitly unratified and blocking

The following MUST remain open and MUST NOT be inferred from implementation,
examples, old defaults, or draft prose:

- confirmatory execution authorization; and
- the later confirmation sample's per-category coverage minimum.

The completed pilot emitted no scientific pass/fail decision by design. Its
one-time authorization is spent and does not authorize another pilot execution.

## Recovery status

**IMPLEMENTED and CPU-VERIFIED:** the two-stage denominator derivation, dual-floor
NTA, lossless 81-readout/64-factorial crossing, deterministic donor/map/bootstrap
identities, fixed exclusion masks, coverage rules, category-balanced estimates,
both 20,000-replicate interval engines, threshold derivation, external
authorization transition, aggregate producer, recursive validator, canonical
notebook source contract, deterministic pilot bundle, and synthetic 20×4 pilot
artifact.

Fresh verification counts and commands are retained in `tasks.md`. The
excluded-input Colab smoke separately established pinned model/lens compatibility
on one T4 before the pilot.

## Pilot observation — 2026-07-31

The independently reviewed, hash-authorized pilot completed on one Google Colab
Tesla T4 using:

- canonical notebook SHA-256
  `9564236a1f49d7ffe2bea44f8b04be5a584c0ff9740b11dd1e563c93b8dba2fe`;
- code-bundle SHA-256
  `aeec8a76a426fa82f3fb96dc6700289a689fcb92fd9952da681fe03fe12dbef4`;
- pilot-view SHA-256
  `5bef8316f72682a628fc1240bf6068a91aa7c8a330377206cbd9145434b797e4`;
- authorization-record SHA-256
  `1af4ec95bf1c0f257fa5f559b7a91c939723cb7382eb0f5812ebc113d842b63c`.

The run produced 80 prompt-layer records under the dual-floor fully crossed 8×8
design. The in-memory validator returned no errors. A final Colab-side audit
matched artifact SHA-256
`d138846e7a189ad42955a5990e6d1a5c00553ba768cd838c5b6bf0334095daef`
and the 80-record cardinality. The 5.43 MiB artifact remains in Colab and was not
transferred. The 180-prompt holdout was not accessed. The retained result artifact
contains no raw prompt text, activations, or full logits; the separately tracked
stimulus and pilot-view inputs remain part of the protocol record.

The derived denominator guard was `0.3388633415411974`. The primary
`input_embedding_decoded` floor retained 18 prompts per layer but only two
arithmetic-completion prompts, below the ratified minimum of three per category.
Every primary-floor inferential result is therefore `undefined`. The
`layer0_residual_decoded` sensitivity floor retained 19 prompts per layer with
category counts `4, 4, 4, 4, 3`; its correct-effect and interaction 99% intervals
were positive at all four layers under both uncertainty methods.

This is an operationally successful and scientifically informative pilot, but it
is not a Stage 2b pass. The positive sensitivity-floor pattern cannot replace the
failed primary analysis. Threshold vectors were unavailable, no pilot decision
was emitted, and confirmation remains blocked. The supported conclusion is
prompt-floor dependence. Broader instrument fragility is an inference for a
mechanism audit to test, requiring a new decision before any confirmatory design
or execution.
