# Stage 2b open parameters (the 10 questions)

Open questions arising from `STAGE2B_DESIGN.md`. Each carries a proposed default.
**None is locked.** Stage 2b execution is not authorized until Dr. Mani ratifies
these, following the Stage 2 pattern: the canonical notebook keeps
`THRESHOLDS_RATIFIED = False` as the human go/no-go signature.

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

## Q3: What counts as the target — DECIDE DELIBERATELY

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

**Recommendation:** A for this iteration, with the weakness stated in the report's
conclusion as a named limit, and C flagged as the natural Stage 2c. Take B or C
only if you want the external-truth claim now — it is a real upgrade, not
scope creep, but it changes the study's cost and its stimulus story.

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

---

## Q5: Specificity threshold — RECOMMEND NOT SETTING THIS NOW

**Proposed: leave `SPEC_MIN_EFFECT` unset and adopt the two-step in Q6.**

Stage 2 set `SPECIFICITY_D_MARGIN = 0.10` with no pilot estimate, and its own
report then could not say whether the controls were "genuinely inseparable or
merely under-resolved at 0.10". Choosing a number now, on a brand-new endpoint in
a brand-new unit, would reproduce that exact failure with less excuse — at least
D was a familiar quantity by then.

The other constants can be locked now:

| Constant | Proposed | Note |
|---|---|---|
| `NONREDUNDANCY_MAX_JACCARD` | 0.70 | unchanged from Stage 2, for comparability |
| `BOOTSTRAP_CI_LEVEL` | 0.99 | matches Stage 2's alpha 0.01 |
| `BOOTSTRAP_ITERATIONS` | 10,000 | cluster bootstrap over prompts |
| `NTA_MIN_DENOMINATOR` | ratify with Q6 | needs the same pilot |
| `DECODE_PARITY_TOL` | 1e-5 | float32 decode parity |
| `STAGE1_RERUN_NOISE_MAX_ABS_LOGIT_DIFF` | 0.0 | unchanged kill anchor |

---

## Q6: Two-step pilot, or single confirmatory run?

**Proposed (two-step):**

1. **Pilot.** Run the first 20 prompts of the manifest, preregistered as pilot and
   marked as such in the artifacts. Report the NTA difference's location and
   spread, the within-prompt correlation across layers, and the rate of
   denominator-guard exclusions.
2. **Lock.** Set `SPEC_MIN_EFFECT` and `NTA_MIN_DENOMINATOR` from the pilot, in
   writing, with the reasoning recorded and ratified.
3. **Confirm.** Run the remaining 180 prompts as the confirmatory sample. The
   decision is computed on the confirmatory sample only.

The pilot prompts are **excluded** from the confirmatory decision. Including them
would mean the threshold was tuned on data that then helped decide the gate.

**Alternative (single run):** set thresholds by judgment now and run all 200 at
once. Cheaper and simpler, and it is what Stage 2 did. It also has no defense
against an ambiguous result being unreadable for exactly the reason Stage 2's was.

**Recommendation:** two-step. The extra cost is one short run; the alternative
risks spending the whole run to land in ambiguity again.

---

## Q7: Layer-distance balancing for the mismatched-layer control

**Proposed:** sample wrong layers at balanced distances `|Δ| ∈ {3, 7, 14}`, sign
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

**Proposed:** authoring the Stage 2b notebook and manifest is permitted. GPU
execution remains **unauthorized** until Q1–Q9 are ratified. The notebook's
measurement cell refuses to run while `THRESHOLDS_RATIFIED` is False, and the
stage-gate cell states execution is not authorized.

Under the Q6 two-step, ratification is naturally two signatures: one authorizing
the 20-prompt pilot, and a second — after the thresholds are set from the pilot
and recorded — authorizing the 180-prompt confirmatory run. The second signature
is what locks the preregistration.

---

## Summary of what needs a decision

| Q | Needs | Delegable? |
|---|---|---|
| Q1 | 200 prompts, new disjoint manifest | yes |
| Q2 | loci unchanged | yes |
| **Q3** | **what counts as the target** | **no — defines the claim** |
| Q4 | orthogonal-rotation fit-broken map | yes |
| **Q5** | **specificity threshold** | **no — recommend deferring to pilot** |
| Q6 | two-step pilot vs single run | prefer your call |
| Q7 | distance bands {3, 7, 14} | yes |
| Q8 | retention unchanged | yes, unless Q3 changes |
| Q9 | T4 only; rank-computation fix as precondition | yes |
| **Q10** | **execution authorization** | **no — yours by definition** |
