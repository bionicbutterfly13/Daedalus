# Stage 2b: does the *specific fitted map* carry target-relevant information?

Design for a second Stage-2 iteration. Observation only. **Execution is not
authorized**; the open parameters in `STAGE2B_OPEN_PARAMETERS.md` require Dr.
Mani's ratification first, exactly as Stage 2 did.

This design supersedes nothing. Stage 2's result stands as recorded: ambiguity.
Stage 2b treats that run as **pilot data** and does not reuse its stimuli.

## 1. What Stage 2 actually left open

Stage 2 asked two questions and got a split answer.

- **Added information** passed on its implemented clause: median top-10 Jaccard
  between the Jacobian and logit-lens readouts was 0.194, far under the 0.70
  ceiling.
- **Specificity** failed: against structure-broken transports the Jacobian
  readout cleared the required margin on 22% (shuffled-layer) and 40%
  (mismatched-probe) of prompts, against a bar of 80%.

The honest reading is that the readout is *not identical* to a cheap baseline and
*not* random noise, but nothing separates it from what you would get by pushing a
residual through some layer-sized Jacobian. Two design defects made that
unavoidable, and both are structural rather than statistical.

**Defect 1: the endpoint had no ground truth.** The primary metric D measured how
much two readouts *differ*. A difference metric cannot distinguish an informative
disagreement from an arbitrary one. "The Jacobian readout differs from the logit
lens" is compatible with the Jacobian readout being worse, better, or unrelated.
Stage 2's conclusion could never have been stronger than non-identity, no matter
how the run came out, because the measurement did not have a notion of correct.

**Defect 2: the controls confounded two factors.** The shuffled-layer control
changes both *which map* is applied and *which layer* it belongs to. The
mismatched-probe control changes the probe and the layer. Neither isolates "the
specific fit at this layer matters" from "a layer-sized linear transport
matters". When both controls fail, you cannot tell which factor caused it.

Stage 2b addresses defect 1 with a target-relative endpoint (§3) and defect 2
with a factorial control structure (§4).

Two further findings from the 2026-07-26 audit shape the design: the
added-information gate silently omitted a preregistered clause, and two declared
seed constants were never consumed on the decision path. §7 and §8 make that
class of error structurally impossible rather than merely discouraged.

## 2. Question and hypotheses

**Question.** Does the fitted Jacobian map, applied to the correct activation at
the correct layer, recover more information about the model's own next-token
target than (a) the cheap logit lens and (b) a same-layer map with the fit
destroyed but the geometry preserved?

Decoupled into two conditions with **separate statistics and separate
thresholds**. Stage 2 coupled these through one shared D margin, which meant a
single constant governed two different scientific claims. They are independent
here, and either can pass or fail alone.

- **H1, specificity (the load-bearing one).** The correctly-fitted map at the
  correct layer attains a higher normalized target attainment than a same-layer
  fit-broken map. Prediction: the prompt-clustered median paired difference
  `NTA(jacobian) − NTA(fit_broken_same_layer)` is greater than `SPEC_MIN_EFFECT`,
  with a cluster-bootstrap confidence interval excluding zero.
- **H2, non-redundancy.** The Jacobian readout is not a re-encoding of the logit
  lens, in a way visible on the target and not merely in token overlap.
  Prediction: median top-10 Jaccard at most `NONREDUNDANCY_MAX_JACCARD`, **and**
  the prompt-clustered paired difference `NTA(jacobian) − NTA(logit_lens)` has a
  confidence interval excluding zero.

H2 now has teeth Stage 2's version did not. Low token overlap alone is satisfied
by a readout that is different *and useless*; requiring a nonzero target-relative
difference means the disagreement has to show up where there is a right answer.

**Null.** The fitted map buys nothing over the surface prompt, or nothing over a
spectrum-matched map with the fit destroyed. A null is a valid result and would
retire the instrument for lab purposes, which is the point of running it.

## 3. Endpoint: normalized target attainment

For prompt `p` and layer `l`, take the target token `t(p)` (see Q3 — the choice
of target is a ratification question, not a design assumption) and score any
readout `r` by how well it ranks that target:

```
s(r, p, l) = -log( rank_of(t(p), r, p, l) ) / log(V)      # V = vocab size
```

Rank 1 gives 0; the worst possible rank gives -1. This is bounded, monotone in
rank, and insensitive to the long tail of logit magnitudes — a rank statistic
rather than a scale-dependent one, so it cannot be moved by a readout's overall
temperature.

Then normalize each readout between the two anchors:

```
NTA(r, p, l) = ( s(r,p,l) - s(prompt_only,p,l) ) / ( s(output,p,l) - s(prompt_only,p,l) )
```

- `prompt_only` maps to 0 by construction: what is recoverable from the surface
  prompt alone, transporting nothing.
- `output` maps to 1 by construction: the model's own final-layer answer, the
  ceiling for any mid-layer readout.
- A readout at NTA ≈ 0 has added nothing to the prompt floor. One at NTA ≈ 1 is
  saying what the output says.

**Why this shape.** Stage 2's preregistration required, conjunctively, that the
Jacobian readout not be within rerun noise of the output or prompt-only
baselines. That clause was never implemented, and the audit found it. Rather than
reinstating it as a fourth gate that could be dropped again, the endpoint is
*defined* in terms of those two baselines: it is impossible to compute NTA
without both, and impossible for the gate to silently omit them. A design that
makes the omission unrepresentable is worth more than a checklist item.

**Layer stratification is mandatory.** NTA rises with depth for trivial reasons —
a late-layer residual is close to the output, so even the logit lens scores well
there. Comparisons are therefore always *within* layer, and the primary statistic
is a paired difference at matched `(p, l)`. Absolute NTA across layers is a
descriptive curve, never a gate input. Reporting a depth-pooled NTA would let
late layers carry the result.

**Denominator guard.** When `s(output) - s(prompt_only)` is at or below
`NTA_MIN_DENOMINATOR`, the prompt-layer cell is uninformative (the output is no
better placed than the prompt floor, so there is no range to be positioned
within) and is excluded, with the count of exclusions reported per layer. Silent
division into a near-zero denominator would manufacture enormous NTA values from
noise. Exclusions are a reported quantity, not a cleanup step.

## 4. Factorial control structure

Two factors, crossed, at each locus. This is the core change from Stage 2.

|  | **Map: correct fit** | **Map: fit broken, same layer** |
|---|---|---|
| **Activation: correct** | `J_correct ⋅ a_correct` — the instrument | `J_broken ⋅ a_correct` — does the *fit* matter? |
| **Activation: wrong** | `J_correct ⋅ a_wrong` — does the *activation* matter? | `J_broken ⋅ a_wrong` — floor for "some transport happened" |

The wrong activation is a norm-matched residual captured at the same layer from a
**different prompt** in the same manifest, not a random vector. Stage 2 already
showed a norm-matched random vector is easy to beat (fraction 1.00); that control
is retained only as a sanity floor, because passing it demonstrates very little.
A real activation from a real prompt is the honest hard case: it has the correct
distributional structure and the wrong content.

This 2×2 yields what Stage 2 could not:

- **Main effect of map** — averaging over activation correctness, does the fitted
  map beat the broken one? This is H1.
- **Main effect of activation** — does feeding the correct residual matter at
  all? If not, the readout is not a function of the input in any meaningful
  sense, which would be damning and was never testable in Stage 2.
- **Interaction** — the signature of a real instrument is that breaking the map
  costs more when the activation is correct. If breaking the map costs the same
  regardless of whether the input is the right one, the map is not doing
  input-specific work. Stage 2 could not estimate this because its controls moved
  more than one factor at a time.

The interaction is reported and interpreted but is **not** a gate in this stage.
Adding a third preregistered threshold on a quantity with no pilot estimate would
be guessing; it is recorded as a descriptive result to power the next iteration.

### 4.1 Constructing the fit-broken, same-layer map

The control must destroy the fitted correspondence while preserving everything
about the map that is *nuisance*: its scale, conditioning, spectrum, and the fact
that it is a layer-sized linear operator. Otherwise a difference could be
attributed to the control being an easier or harder object generally.

**Default (Q4): random orthogonal rotation of the left singular basis.** For the
fitted Jacobian `J = U Σ Vᵀ`, use `J_broken = (Q U) Σ Vᵀ` with `Q` a Haar-random
orthogonal matrix under a preregistered seed. This preserves the singular value
spectrum exactly — identical conditioning, identical operator norm, identical
Frobenius norm — while destroying which input direction maps to which output
direction. It is the tightest available "same object, wrong correspondence"
control.

Secondary, reported alongside: a **spectrum-matched Gaussian** map drawn to match
`Σ` but with random bases on both sides, which additionally destroys the input
geometry. If the orthogonal-rotation control is beaten but the Gaussian one is
not, that localizes the signal to the input basis specifically.

The Stage 2 controls are retained as secondary comparators, so results remain
commensurable with the pilot: shuffled-layer (map from a different layer) and
mismatched-probe. These are no longer primary, because each moves two factors.

### 4.2 Balancing the mismatched-layer control by distance

Where a wrong-layer map is used, layer distance is a confound: a map from an
adjacent layer is nearly correct, and one from the opposite end of the network is
trivially wrong. Stage 2 did not balance this, so its mismatched-probe fraction
(0.40) mixes both regimes and is hard to interpret.

Stage 2b samples wrong layers at **preregistered balanced distances** (Q7),
default `|Δ| ∈ {3, 7, 14}`, with sign balanced where the layer index permits, and
equal allocation across prompts. Results are reported per distance band. A signal
that decays with distance is evidence of layer-specific structure; a flat profile
means layer identity is not what the readout is tracking.

## 5. Sampling and uncertainty

**The sampling unit is the prompt.** Stage 2 computed per-prompt fractions but
pooled measurements across four layers, which are strongly dependent within a
prompt — the same activation, the same target, the same tokenization. Treating
`prompt × layer` cells as independent would overstate precision roughly by the
within-prompt correlation.

- Layers are **repeated measures within prompt**. Each prompt contributes one
  cluster of observations.
- The primary statistic at each layer is the **paired difference** between the
  instrument cell and a control cell at matched `(p, l)`.
- Uncertainty comes from a **cluster bootstrap resampling whole prompts**
  (`BOOTSTRAP_ITERATIONS`, default 10,000), never individual cells. Confidence
  intervals are BCa percentile intervals on the median paired difference.
- Gates are evaluated on the interval, not on a point estimate crossing a line.

**Sample size (Q1): 200 prompts, up from 50.** Stage 2's decision quantities were
per-prompt *fractions*, and a fraction near 0.80 estimated on n=50 carries a 95%
binomial half-width of roughly ±0.11 — wide enough that 0.22 versus 0.40 versus
0.80 are not being resolved as precisely as the single reported digit implies.
At n=200 that half-width falls to about ±0.055. The endpoint change also helps:
a paired continuous difference is far more efficient than a thresholded fraction,
because thresholding discards magnitude. n=200 is proposed, not derived from a
formal power analysis — no pilot estimate of the NTA difference's variance exists
yet, and inventing one would be false precision. **The pilot's own NTA variance
should be estimated from the first 20 prompts and reported before the full run
proceeds**, which is a design decision requiring ratification (Q6).

### 5.1 Held-out stimuli

Stage 2's 50 prompts have now informed design choices — the endpoint, the
controls, and the thresholds below were all chosen with knowledge of how that run
came out. Reusing them would make Stage 2b a test of a design fitted to its own
test set.

- New manifest `jspace-stage2b-stimulus/v1`, 200 prompts, **disjoint from the
  Stage 2 manifest**, with non-overlap asserted by per-prompt digest at preflight
  and the assertion recorded in the artifact. Not documented as a rule — checked.
- The Stage 1 anchor (`s00`) is retained **outside the analysis sample**, purely
  as the reproduction kill check. Including it in the analysis set would
  contaminate held-out status with the one prompt every prior stage has seen.
- Category structure is preserved from Stage 2 (five categories) so per-category
  reporting stays comparable, with 40 prompts per category.

## 6. Decision rule

Reproduction is a kill gate, as before. The two scientific conditions are
independent and each reports its own outcome.

| Gate | Statistic | Constant | Default |
|---|---|---|---|
| Reproduction (kill) | anchor top-k identity, max abs logit diff | `STAGE1_RERUN_NOISE_MAX_ABS_LOGIT_DIFF` | 0.0 |
| H1 specificity | cluster-bootstrap median of `NTA(jac) − NTA(fit_broken)` | `SPEC_MIN_EFFECT` | ratify (Q5) |
| H1 interval | BCa CI lower bound above zero | `BOOTSTRAP_CI_LEVEL` | 0.99 |
| H2 non-redundancy, overlap | median top-10 Jaccard vs logit lens | `NONREDUNDANCY_MAX_JACCARD` | 0.70 |
| H2 non-redundancy, target | CI on `NTA(jac) − NTA(logit_lens)` excludes 0 | `BOOTSTRAP_CI_LEVEL` | 0.99 |
| Sanity floor | `NTA(jac) − NTA(random_vector)` CI excludes 0 | — | must hold |

- **Pass:** reproduction holds AND H1 holds AND H2 holds (both clauses).
- **Ambiguity:** reproduction holds; exactly one of H1/H2 holds.
- **Fail:** reproduction holds; neither H1 nor H2 holds, or the sanity floor is
  not cleared.
- **Kill:** capacity gate fails, any pinned identity mismatches, or the anchor
  fails to reproduce. Stop; do not continue collecting.

`SPEC_MIN_EFFECT` is deliberately left unset (Q5). Stage 2's 0.10 D margin was
chosen without a pilot and the report itself flagged that the structure-broken
controls may be "genuinely inseparable or merely under-resolved at 0.10". Setting
a threshold on a new endpoint with no pilot estimate would repeat that mistake in
a new unit. The recommended path is the two-step in Q6: estimate the effect's
scale on a preregistered pilot subset, then lock the threshold before the
confirmatory run, with both steps recorded.

## 7. Preflight: tensor contracts and constant consumption

Two classes of failure cost this project a run each. Both become preflight
assertions that abort before any measurement.

**7.1 Tensor contracts.** Stage 2 lost an execution to a dtype mismatch and
another to a device mismatch, each surfacing only under live GPU execution and
each diagnosable only from a traceback mid-run. At every locus, before
measurement, assert and record:

- **shape** — residual is `(d_model,)`; the Jacobian is `(d_model, d_model)`.
- **dtype** — residuals cast to float32 before transport, because jlens stores
  fitted Jacobians as float32 and its own `lens.apply` casts.
- **device** — decoded readouts on CPU, because `lens.apply` returns CPU tensors
  and mixing raises on the first cross-readout subtraction.
- **decode parity** — `decode_residual(x)` equals `lens.unembed(x)` within
  `DECODE_PARITY_TOL` on a fixed probe vector, proving all readouts share one
  vocabulary basis. Without this, comparisons across readouts are meaningless
  regardless of the statistics.

**7.2 Constant consumption.** The 2026-07-26 audit found three constants that
were declared, written into artifacts, and never used on a decision path:
`INFERENCE_SEEDS` claimed two seeds while only seed 0 ran; `RANDOM_VECTOR_SEEDS`
computed three while one reached the decision; and the added-information gate
omitted a clause the preregistration required. All three were invisible because
the artifact faithfully recorded the *declaration*.

Stage 2b asserts the link. Every preregistered constant is registered with the
gate that consumes it, and the preflight fails if any declared constant has no
consumer, or if any gate reads a constant not in the registry. The run refuses to
start rather than producing artifacts that overstate what was tested. This is the
single highest-value change in the design: it is cheap, it is mechanical, and it
would have caught every one of the three findings before execution.

## 8. Reporting

Complete gate reporting is a requirement, not a courtesy. The aggregate artifact
records, for every gate: the constant name, its declared value, the observed
statistic, the bootstrap interval, the number of clusters, the number of excluded
cells with reasons, and the pass/fail outcome. A reader must be able to recompute
each decision from the artifact without the notebook. Stage 2's report could not
be independently certified from its own artifacts, which is why the audit had to
read the notebook source to establish what the gates actually did.

Additionally reported: per-layer NTA curves for every readout; the 2×2 cell means
with intervals; the interaction estimate; per-distance-band results for the
mismatched-layer control; and per-category breakdowns.

## 9. Scope and boundaries

Unchanged from Stage 2 and binding.

- Observation only. No lens fitting, steering, ablation, activation editing, or
  causal intervention. The wrong-activation and broken-map cells are *readout*
  manipulations computed offline from captured residuals; nothing is fed back
  into the model, and no forward pass is altered.
- All readouts are evidence class 1. Nothing here promotes to a functional or
  phenomenal claim.
- A pass authorizes **no** Stage 3, publication, artifact transfer, or
  Sakshi/Elume integration. It authorizes writing a Stage 3 proposal, which
  carries its own preregistration and its own ratification.
- Artifacts stay digest-only; raw stimulus text lives in the versioned manifest.
- Execution requires Dr. Mani's ratification of `STAGE2B_OPEN_PARAMETERS.md`. The
  notebook keeps `THRESHOLDS_RATIFIED = False` as the human go/no-go signature.

## 10. What a pass would and would not mean

Worth stating before the run, so the result is not oversold afterward.

**Would mean:** the specific fitted map, applied to the correct activation at the
correct layer, positions the model's own next-token target measurably better than
the surface prompt does, better than a cheap logit lens, and better than a
same-layer map with identical spectrum but destroyed correspondence. That is a
real observational claim about the instrument, and it is what Stage 2 tried and
failed to establish.

**Would not mean:** that the lens reads a representation, that its readouts
correspond to anything the model "uses", or that mid-layer token rankings have
any cognitive interpretation. NTA is a rank statistic about next-token targets
under one protocol at four loci and one token position. Every limit in Stage 2
§6.2 and §6.3 carries over unchanged.

The instrument would have earned the right to be called a measurement. It would
not have earned an interpretation.
