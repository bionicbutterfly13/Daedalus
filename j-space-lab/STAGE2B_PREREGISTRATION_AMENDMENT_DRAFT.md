# Stage 2b Preregistration Amendment

Status: **PILOT OBSERVED 2026-07-31; PRIMARY ANALYSIS UNDEFINED;
CONFIRMATION BLOCKED**

Decision ledger: Dr. Mani ratified the stratified 20-ID pilot subset, model-output
argmax target, primary-plus-sensitivity prompt-floor rule, and fully crossed 8×8
donor/map measurement structure on 2026-07-28. On 2026-07-30 he ratified the
two-stage denominator, deterministic donor/map/bootstrap identities,
floor-specific exclusion and coverage rules, category-balanced point estimator,
primary prompt bootstrap, crossed product-weight sensitivity, 20,000-replicate
99% interval engine, threshold derivation, and later intersection-union global
claim. Pilot GPU execution was later authorized once for exact reviewed source
identities and completed on 2026-07-31. Confirmation access remains a separate,
ungranted decision.

Date: 2026-07-28 UTC

## Provenance and scope

Primary sources accessed directly in this recovery session:

- `j-space-lab/jspace-stage2b-stimulus-v1.json`: direct JSON parsing; complete 200-record coverage; file and canonical SHA-256 `ba29c629c7b9601980b6c0bb9cd9730242d7cd6b7eacb1166c307837416d4bbf`.
- `j-space-lab/STAGE2B_OPEN_PARAMETERS.md`: direct text read/search. It proposes literal first-20 pilot selection.
- `j-space-lab/STAGE2B_DESIGN.md`, `specs/001-jspace-stage2b/research.md`, and the Stage 2b contracts: direct text read/search during the audit and recovery.
- Executable partition behavior: directly exercised through `stage2b_manifest.select_partition` and tests.

Derivative inputs: earlier EvoScientist reports and project-state summaries informed issue discovery but do not establish any source-dependent claim below.

Coverage gap: no model, lens, CUDA, Colab, real prompt measurement, pilot, or confirmation was executed.

## 1. Authorization modes

Implemented instrument boundary:

- `pilot`: requires a distinct pilot authorization; the three pilot-derived thresholds may be unset; only the pinned 20-ID view is returned; output contains estimates and provenance but no confirmatory gates or decision.
- `confirmatory`: requires a separate confirmation authorization and fixed finite values for all three pilot-derived thresholds; only the disjoint 180-ID complement is returned.
- `synthetic_smoke`: uses dedicated synthetic inputs excluded from the 200-record manifest and cannot emit a scientific decision.

Authorization signatures:

1. `PILOT_PROTOCOL_RATIFIED`: locks the pilot subset, target/floor semantics, donor and broken-map draws, bootstrap structure, and threshold-derivation methods.
2. `PILOT_AUTHORIZED`: separately authorizes only the pinned 20-record pilot and its ratified compute packet.
3. `CONFIRMATORY_THRESHOLDS_RATIFIED`: later authorizes the 180-record confirmation after threshold values and provenance are locked.

No authorization record ships in the repository. The protocol is ratified in
source, but the canonical notebook remains blocked until an independently
approved, exact-hash external pilot authorization record is supplied.

## 2. Exact pilot subset and inaccessible holdout — RATIFIED 2026-07-28

Observation: the manifest is category-blocked and contains no pilot/confirmation field. The prior proposal “first 20 prompts” would select only one category and is rejected by the executable partition guard.

Ratified correction: select the first four IDs within each of the five category
blocks, explicitly selected by Dr. Mani on 2026-07-28:

- `s000`, `s001`, `s002`, `s003`
- `s040`, `s041`, `s042`, `s043`
- `s080`, `s081`, `s082`, `s083`
- `s120`, `s121`, `s122`, `s123`
- `s160`, `s161`, `s162`, `s163`

Ratified pilot subset SHA-256: `8ed0a0092ec3989f6bd8005ae4360de86174764a946af75b35ea30932ca719b5`.

Direct executable verification:

- pilot: 20 records, 4/category;
- confirmation: 180 records, 36/category;
- sets are disjoint and exhaustive.

This subset identity is ratified. Ratification does not authorize runtime access
to the pilot view, GPU execution, or any access to the 180-prompt confirmation.

## 3. Target semantics — RATIFIED 2026-07-28

Ratified primary target: the model’s output-position argmax under the pinned
model revision, selected explicitly by Dr. Mani on 2026-07-28.

Narrow estimand: whether a readout tracks the model’s own eventual token trajectory. It does **not** establish task correctness, truth, or an independently audited answer. The stimulus has no audited answer key, so no “correct-answer” endpoint may be reported.

Artifacts must record target token ID, target derivation, output logits
identity/provenance, and any ties. This target decision is ratified; it does not
ratify the other protocol sections or authorize execution.

## 4. Prompt-floor sensitivity — RATIFIED 2026-07-28

Ratified primary floor: decoded input embedding at the final prompt position,
preserving Stage 2 comparability.

Ratified sensitivity: repeat endpoint construction using the layer-0 residual at
the same position. Report both NTA results and their difference; do not choose the
more favorable floor after observation. A confirmatory claim is robust only if
its required gates do not reverse under the sensitivity floor; otherwise report
prompt-floor dependence and do not describe the result as robust.

This floor rule was selected explicitly by Dr. Mani as option 3 on 2026-07-28.
Its producer, artifact, recomputation, and test paths are implemented and locally
verified. Frozen independent review remains required; ratification alone does not
authorize a run.

## 5. Wrong-activation donor dependence

Observation: deterministic donor selection can reuse one prompt as donor for several recipients, inducing cross-prompt dependence not represented by an ordinary prompt-only bootstrap.

Ratified rule:

- use eight deterministic donor assignments derived from
  `SHA256("jspace-stage2b/v1|donor-assignment|<i>")`;
- exclude self-donation and preserve recipient→donor provenance;
- record every assignment identity, seed derivation, recipient→donor digest, and
  realized residual hash;
- retain the full donor×map crossing;
- compute equal-weight donor/map effects within prompt-layer;
- use category-stratified prompt resampling as primary and independent
  prompt×donor×map product weights as sensitivity; and
- treat later disagreement between required procedures as `undefined`, not pass.

## 6. Broken-map randomness

A single fixed Haar draw supports only a claim conditional on that draw.

Ratified primary rule:

- use eight deterministically seeded Haar rotations per selected layer;
- verify singular-value preservation for every draw;
- record each full seed derivation and realized map hash;
- retain every draw through complete crossing validation;
- compute equal-weight effects only after validation; and
- include map variation in the ratified product-weight sensitivity interval.

### 6.1 Joint donor × broken-map design — RATIFIED 2026-07-28

Ratified measurement structure: use a **fully crossed** design, explicitly
approved by Dr. Mani on 2026-07-28.
Every one of the eight donor assignments is evaluated with every one of the eight
broken-map draws at each selected layer. This produces 64 donor/map combinations
per prompt/layer rather than pairing each donor assignment with only one map.

Plain-language rationale: donor choice and broken-map choice are two different
sources of variation. Testing every combination lets the analysis distinguish a
donor effect, a map effect, and a donor-by-map interaction. Pairing would use less
GPU compute but could make an easy or difficult donor inseparable from the map it
happened to receive. A hierarchical model remains a possible future analysis, but
it is not needed to define which measurements the pilot collects.

Artifact consequence: each sparse measurement must record donor-assignment ID,
recipient→donor digest, broken-map draw ID, seed, and map hash. Aggregation must
retain the complete crossing until dependence-aware prompt and draw uncertainty
has been computed; it must not average away either draw dimension first.

Status: **measurement and pilot inference structure ratified**. This does not
authorize GPU execution. The later confirmation per-category minimum remains
open.

## 7. Pilot derivations and intervals — RATIFIED 2026-07-30

1. `NTA_MIN_DENOMINATOR`: after all 80 raw prompt-layer score records exist,
   compute the 0.05 linear quantile of the 80 primary-floor denominators. Stop
   without NTA if it is nonfinite or nonpositive. Apply the same derived guard to
   both floors without another model/lens pass.
2. `SPEC_MIN_EFFECT[l]`: one half of the positive, defined primary-floor
   category-balanced correct-effect mean at layer `l`.
3. `INTERACTION_MIN_EFFECT[l]`: one half of the positive, defined primary-floor
   category-balanced interaction mean at layer `l`.

Pilot inference is complete-case under a fixed floor-layer exclusion mask. It
requires at least 18/20 eligible prompts and at least 3/4 in every category.
Point estimates are equal-weight means of the five eligible category means.
Primary uncertainty uses 20,000 category-stratified prompt-resampling replicates.
Sensitivity uses 20,000 independent prompt×donor×map mean-one `Exp(1)`
product-weight replicates. Both use explicit `Generator(PCG64(seed))` with the
ratified SHA-256 namespace, two-sided 99% linear percentile bounds, and require
all replicates to be finite.

The pilot preserves all source estimates, intervals, identities, code versions,
and threshold derivation evidence. It emits no pass/fail decision. All eight
threshold source means must be positive and defined; otherwise both vectors remain
unavailable and confirmation is blocked.

## 8. Decision semantics

- Pilot output: estimates and provenance only; no Stage 2b pass/fail.
- Confirmation output: all seven canonical required gates must be present and recomputable.
- Any measured failed required layer dominates an undefined layer in the all-layer conjunction.
- Any identity mismatch or capacity failure is a kill condition.
- Any contradictory recorded gate or decision invalidates the artifact.
- Evidence class remains 1 unless separate governance changes it.

## Ratification checklist

Decision ledger:

1. stratified 20-ID subset and digest — **RATIFIED 2026-07-28**;
2. model-argmax estimand — **RATIFIED 2026-07-28**;
3. prompt floor and layer-0 sensitivity rule — **RATIFIED 2026-07-28**;
4. donor draw count and deterministic identities — **RATIFIED**;
5. broken-map draw count and deterministic identities — **RATIFIED**;
6. fully crossed donor × broken-map measurement design — **RATIFIED 2026-07-28**;
7. denominator and both effect-threshold derivation rules — **RATIFIED 2026-07-30**;
8. point estimate, both interval methods, iterations, seed, coverage, and later
   intersection-union claim — **RATIFIED 2026-07-30**;
9. separate exact-hash pilot GPU launch packet — **AUTHORIZED ONCE AND CONSUMED**.

## Post-observation addendum — 2026-07-31

The pilot used canonical notebook SHA-256
`9564236a1f49d7ffe2bea44f8b04be5a584c0ff9740b11dd1e563c93b8dba2fe`,
code-bundle SHA-256
`aeec8a76a426fa82f3fb96dc6700289a689fcb92fd9952da681fe03fe12dbef4`,
pilot-view SHA-256
`5bef8316f72682a628fc1240bf6068a91aa7c8a330377206cbd9145434b797e4`,
and authorization-record SHA-256
`1af4ec95bf1c0f257fa5f559b7a91c939723cb7382eb0f5812ebc113d842b63c`.
It produced 80 prompt-layer records and a retained Colab artifact with SHA-256
`d138846e7a189ad42955a5990e6d1a5c00553ba768cd838c5b6bf0334095daef`.
The artifact was not transferred and the 180-prompt confirmation set was not
accessed.

The primary floor met 18/20 total coverage but failed the preregistered category
minimum because only two arithmetic-completion prompts remained eligible per
layer. Primary inference and both threshold vectors are therefore `undefined`.
The sensitivity floor was defined and positive at all selected layers under both
uncertainty procedures. Under the preregistered floor rule, this is prompt-floor
dependence rather than a robust result. No pilot pass/fail decision was emitted;
confirmation remains blocked.
