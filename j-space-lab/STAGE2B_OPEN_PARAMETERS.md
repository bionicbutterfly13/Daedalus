# Stage 2b open parameters (the 10 questions)

Questions arising from `STAGE2B_DESIGN.md`; each began with a proposed default.
The target, pilot identity, two floors, full 8×8 crossing, deterministic seeds,
two-stage denominator, exclusion/coverage rules, estimators, intervals, pilot
threshold derivation, and later global confirmation claim were ratified by
Dr. Mani across 2026-07-28 and 2026-07-30. The exact-hash-authorized Stage 2b
pilot completed on 2026-07-31. The canonical notebook keeps
`THRESHOLDS_RATIFIED = False` because the primary-floor category-coverage failure
made the numeric threshold vectors unavailable; confirmation remains blocked.

Two questions differ in kind from the rest and should not be delegated on the
"set reasonable settings" basis that covered Stage 2's Q1–Q7:

- **Q3** (what counts as the target) determines what "carries information" means
  in this study. Choose it deliberately; the design's interpretation depends on
  it.
- **Q5** (the specificity threshold) is the constant Stage 2 set without a pilot
  and then could not interpret. The recommendation is to *not* set it now.

---

## Q1: Sample size and stimulus manifest

**Proposed:** 200 new prompts in `jspace-stage2b-stimulus/v1`, five categories of
40, disjoint from the Stage 2 manifest with non-overlap asserted by per-prompt
digest at preflight. The Stage 1 anchor `s00` is retained outside the analysis
sample as the reproduction kill check only.

**Why 200.** Stage 2 decided on per-prompt fractions at n=50, where a fraction
near the 0.80 bar carries a 95% binomial half-width of about ±0.11 — wide enough
that its reported 0.22 and 0.40 are less resolved than one digit suggests. n=200
brings that to about ±0.055, and the move to a paired continuous endpoint is
itself a larger efficiency gain than the sample increase.

**Why disjoint.** Stage 2b's endpoint, controls, and thresholds were all chosen
knowing how Stage 2 came out. Reusing those stimuli would test a design against
the data that shaped it.

**Cost:** roughly 4× Stage 2's measurement time before the §Q10 optimization;
see Q9.

---

## Q2: Measurement loci

**Proposed:** unchanged from Stage 1 and 2 — layers 6, 13, 20, 26 at token
position -2.

Keeping the loci fixed is what makes the `s00` anchor reproduction meaningful as
a kill check, and keeps Stage 2b commensurable with the pilot. Expanding loci is
a separate question best asked after the endpoint is validated; adding layers now
would confound "new endpoint" with "new loci" in any comparison to Stage 2.

---

## Q3: What counts as the target — DECIDED 2026-07-28

This defines what the study means by "information", and it is the question Stage 2
deferred (its Q3 chose the model's own output and explicitly added no held-out
task).

**Option A (proposed default): the model's own next-token argmax.** Purely
observational, requires no external corpus, and keeps `output` as a principled
ceiling for the NTA normalization.

*Known weakness, stated plainly:* the target is then defined by the output
baseline itself, so a readout scores well precisely by resembling the model's
final answer. NTA measures how far a mid-layer readout has travelled toward the
model's own conclusion. That is a coherent and meaningful quantity — but it is
*not* the same as "informative about the world", and a pass must not be
described as though it were.

**Option B: the true continuation token from a held-out corpus.** Gives an
external ground truth independent of the model, so "carries information" means
information about the actual text. Costs the synthetic-manifest property (raw
text control, non-sensitive guarantee) and introduces a corpus-licensing question.
It also weakens the NTA normalization, because the model's own output is no longer
a ceiling — the model can be wrong, and a mid-layer readout could in principle
beat it, putting NTA above 1.

**Option C: both, reported side by side.** Strictly more informative and the
scientifically strongest choice. Costs a second full measurement pass and a
corpus decision, and doubles the reporting surface.

**Ratified decision:** Option A for Stage 2b, selected explicitly by Dr. Mani on
2026-07-28. The report must state the weakness as a named limit: this measures
progress toward the model's own eventual token, not truth or task correctness.
Option C remains the natural Stage 2c extension.

### Prompt-floor rule — DECIDED 2026-07-28

**Ratified decision:** use the decoded input embedding as the primary floor and
repeat the endpoint with the decoded layer-0 residual as a preregistered
sensitivity analysis. Report both; do not select the more favorable floor after
observation. If any required gate reverses, report prompt-floor dependence rather
than a robust result. The completed pilot followed this rule: the sensitivity
floor was positive while the primary floor was undefined, so the result is
prompt-floor dependent and not robust.

---

## Q4: Construction of the fit-broken, same-layer map

**Proposed:** Haar-random orthogonal rotation of the left singular basis,
`J_broken = (Q U) Σ Vᵀ`, under a preregistered seed. Preserves the singular value
spectrum, operator norm, Frobenius norm, and conditioning exactly, while
destroying which input direction maps to which output direction.

Reported alongside as a secondary control: a spectrum-matched Gaussian map with
random bases on both sides. If the orthogonal control is beaten but the Gaussian
is not, the signal localizes to the input basis.

Stage 2's shuffled-layer and mismatched-probe controls are retained as secondary
comparators so results stay commensurable with the pilot, but they are no longer
primary — each moves more than one factor at a time, which is what made Stage 2's
specificity failure uninterpretable.

### Repeated-control structure — DECIDED 2026-07-28

**Ratified decision:** fully cross eight wrong-activation donor assignments with
eight broken-map draws at every selected layer. Retain all 64 donor/map
combinations per prompt/layer, including donor-assignment ID, recipient→donor
digest, broken-map draw ID, seed, and map hash, until dependence-aware inference
is computed.

On 2026-07-30 Dr. Mani additionally ratified equal-weight donor/map effects within
prompt-layer, category-stratified prompt resampling as primary, and independent
prompt×donor×map product-weight resampling as sensitivity. Both methods remain
separate by layer and floor. This protocol decision does not authorize GPU
execution.

---

## Q5: Specificity threshold — DERIVATION RULE DECIDED 2026-07-30

`SPEC_MIN_EFFECT` and `INTERACTION_MIN_EFFECT` remain numerically unset before the
pilot. Their derivation rule is ratified: for each selected layer, take one half
of the corresponding positive, defined primary-floor category-balanced pilot
mean. If any of the eight source means is nonpositive or undefined, neither
threshold vector is available and confirmation remains blocked.

Stage 2 set `SPECIFICITY_D_MARGIN = 0.10` with no pilot estimate, and its own
report then could not say whether the controls were "genuinely inseparable or
merely under-resolved at 0.10". Choosing a number now, on a brand-new endpoint in
a brand-new unit, would reproduce that exact failure with less excuse — at least
D was a familiar quantity by then.

The ratified pilot constants are:

| Constant | Ratified rule/value |
|---|---|
| `BOOTSTRAP_CI_LEVEL` | `0.99` |
| `BOOTSTRAP_ITERATIONS` | `20,000` |
| `BOOTSTRAP_QUANTILE_METHOD` | `linear` |
| `BOOTSTRAP_BIT_GENERATOR` | explicit `PCG64` |
| `NTA_MIN_DENOMINATOR` | 0.05 linear quantile of the 80 primary denominators |
| `SPEC_MIN_EFFECT[l]` | 0.5 × positive primary correct-effect mean at layer `l` |
| `INTERACTION_MIN_EFFECT[l]` | 0.5 × positive primary interaction mean at layer `l` |

---

## Q6: Two-step pilot, or single confirmatory run? — DECIDED 2026-07-30

**Proposed (two-step):**

1. **Pilot.** Use the ratified stratified 20-ID view: `s000`–`s003`,
   `s040`–`s043`, `s080`–`s083`, `s120`–`s123`, and `s160`–`s163`, with ordered
   subset digest `8ed0a0092ec3989f6bd8005ae4360de86174764a946af75b35ea30932ca719b5`.
   Report the NTA difference's location and spread, the within-prompt correlation
   across layers, and the rate of denominator-guard exclusions.
2. **Derive and lock.** Derive the one run-wide denominator guard from all 80
   retained primary denominators, then derive the two four-layer effect vectors
   from valid primary-floor pilot means. Preserve all derivation inputs, methods,
   code identities, and artifact identity.
3. **Confirm.** Run the remaining 180 prompts as the confirmatory sample. The
   decision is computed on the confirmatory sample only.

The pilot prompts are **excluded** from the confirmatory decision. Including them
would mean the threshold was tuned on data that then helped decide the gate.

**Alternative (single run):** set thresholds by judgment now and run all 200 at
once. Cheaper and simpler, and it is what Stage 2 did. It also has no defense
against an ambiguous result being unreadable for exactly the reason Stage 2's was.

**Decision status:** the balanced pilot subset, two-stage denominator,
category-balanced mean, both uncertainty engines, coverage rules, and threshold
derivations are ratified. The separately authorized pilot completed; that
authorization is consumed and does not authorize a repeat or confirmation.

## Post-pilot outcome — OBSERVED 2026-07-31

- Derived denominator guard: `0.3388633415411974`.
- Primary decoded-input-embedding floor: 18 eligible prompts per layer, but only
  two arithmetic-completion prompts. All primary inference is `undefined` under
  the ratified three-per-category minimum.
- Layer-0 sensitivity floor: 19 eligible prompts per layer with category counts
  `4, 4, 4, 4, 3`; correct effects and interactions were positive at all four
  layers under both 99% interval methods.
- Threshold vectors: unavailable because all required primary-floor source means
  were not defined.
- Pilot decision: none, by design. Confirmation: blocked and unauthorized.

The result is operational success plus evidence of prompt-floor dependence. It
does not validate the primary instrument, authorize confirmation, or establish a
functional, cognitive, or consciousness claim.

---

## Q7: Layer-distance balancing for the mismatched-layer control

**Status: DEFERRED SECONDARY CONTROL.** No distance vector or seed is authorized.
Wrong-layer policy and fields are absent from the executable pilot contract, so
this proposal does not block the ratified primary pilot. Reintroducing it would
require a separate protocol and contract decision.

**Proposed only:** sample wrong layers at balanced distances `|Δ| ∈ {3, 7, 14}`, sign
balanced where the layer index permits, allocated equally across prompts, and
reported per distance band.

Stage 2 did not balance distance, so its mismatched-probe fraction of 0.40 mixes
near-miss and far-miss regimes into one uninterpretable number. Per-band results
also give a decay profile: a signal that weakens with distance is evidence of
layer-specific structure, while a flat profile says layer identity is not what
the readout tracks.

---

## Q8: Stimulus retention

**Proposed:** unchanged from Stage 2 — raw synthetic prompt text lives in one
versioned in-repo manifest; observation artifacts stay digest-only
(`raw_prompt_persisted=false`).

If Q3 selects Option B or C, this question reopens: held-out corpus text carries
licensing and retention constraints that the synthetic manifest does not.

---

## Q9: Runtime scope and the known hotspot

**Proposed:** single Tesla T4 class, as Stage 2. No cross-runtime reproducibility
claim.

**Prerequisite before a 200-prompt run.** Stage 2 took ~12 minutes for 50 prompts,
dominated by `output_argmax_rank` performing a full-vocabulary (~151k) argsort
plus a Python integer comprehension roughly 48 times per prompt. Naively scaling
to 200 prompts and a 2×2 factorial multiplies that cost several-fold.

The fix is known and small: compute the target's rank directly as
`(row > row[target]).sum() + 1` instead of a full argsort. Stage 2b's endpoint is
*entirely* rank-based, so this is on the critical path rather than an
optimization — the whole measurement is target ranks now.

**Recommend making this a precondition of execution**, verified in the preflight
against the old path on a fixed probe so the optimization cannot silently change
the statistic.

---

## Q10: Execution authorization

Authoring and local verification are permitted. GPU execution remains
**unauthorized** until Dr. Mani approves one exact canonical notebook SHA-256,
one exact code-bundle SHA-256, the pinned pilot-view digest, and the no-confirmation
and no-transfer boundaries in an external authorization record.

The pilot authorization record may transition only `PILOT_PROTOCOL_RATIFIED` and
`PILOT_AUTHORIZED`. It must not supply the derived denominator or threshold
vectors, and `THRESHOLDS_RATIFIED` remains false throughout the pilot. A later,
separate authorization is required for the 180-prompt confirmation.

---

## Summary of what needs a decision

| Q | Needs | Delegable? |
|---|---|---|
| Q1 | 200-prompt manifest; exact stratified 20-prompt pilot view | **ratified** |
| Q2 | loci 6, 13, 20, 26 at position -2 | **ratified** |
| **Q3** | **DECIDED: model's next-token argmax; narrow claim required** | **ratified 2026-07-28** |
| Q4 | eight deterministic donor assignments × eight deterministic broken maps | **ratified** |
| **Q5** | half-positive-primary-means threshold derivation | **ratified 2026-07-30** |
| Q6 | two-stage pilot, fixed coverage, two interval engines | **ratified 2026-07-30** |
| Q7 | wrong-layer secondary proposal | **deferred; absent from pilot** |
| Q8 | digest-only retained artifact; no raw activation/map/logit persistence | **ratified** |
| Q9 | pinned T4 runtime and direct-rank implementation | **runtime smoke verified** |
| **Q10** | **exact-hash pilot execution authorization** | **pending Dr. Mani** |
