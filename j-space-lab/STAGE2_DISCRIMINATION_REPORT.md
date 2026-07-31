# J-space Stage 2: Does the Jacobian lens see anything a cheap baseline cannot?

An observational-discrimination study of the fitted Qwen3-1.7B Jacobian lens.

- Study ID (run): `f9234a9c-6a2d-43da-9fbd-bf26b19ac18c`
- Date executed: 2026-07-24 (Google Colab, single Tesla T4)
- Stage: 2 of the jspace-research-operations stage gates (observational discrimination)
- Ratified by: Dr. Mani (all eight open questions, including GPU execution)
- Design notebook identity: 52,259 bytes, SHA-256
  `353479b0f0e959f2e207446b1383ebf632c05bf8c9a9656508cc91d98d4f28f5`
- Decision: **ambiguity**
- Evidence class of every readout below: 1 (directly measured). Nothing here is
  promoted to a functional or phenomenal claim.

This report is the scientific record for EvoScientist and Archimedes. It reads
top to bottom as idea, hypothesis, methods, results, conclusion, and discussion.
The bounded protocol, the pinned identities, and the preregistered thresholds
live in `EvoScientist/skills/jspace-research-operations/`; this document
interprets one execution of that protocol.

## 1. Idea and motivation

Archimedes is meant to operate as a cognitive laboratory in which Anthropic's
Jacobian Lens (J-lens) is the instrument for reading and perturbing a model's
internal representations. Everything downstream, an Elume substrate consuming
typed observations, a Sakshi audit layer checking lineage, any claim that the
lab measures something about model-internal cognition, rests on one unproven
assumption: that the fitted Jacobian lens actually reports something about the
model's internals that a cheaper, dumber tool would miss.

Stage 1 (the smoke test) established only that the instrument is self-consistent.
On a pinned Qwen3-1.7B with the Neuronpedia fitted lens, a single synthetic
prompt produced the same sparse top-k readout twice in the same runtime, with a
maximum Jacobian-logit difference of 0.0. That is reproducibility of a
measurement, not evidence that the measurement carries information. A broken
thermometer that always reads 20 degrees is perfectly reproducible.

The cheapest honest competitor to the Jacobian lens is the **logit lens**: take a
mid-layer residual vector and push it straight through the model's final norm and
unembedding, reading off "what the model would guess now." It costs one matrix
multiply the model already has. The Jacobian lens is the more expensive
instrument that, instead of assuming a mid-layer vector lives in the final-layer
coordinate system, transports it through a fitted linear map first. Stage 2 asks
whether that added machinery buys anything, and whether any apparent signal
survives against controls that share the Jacobian's structure but not its fit.

Building Elume or Sakshi on an instrument that is indistinguishable from a logit
lens, or from random noise dressed up the same way, would be the most expensive
kind of mistake: a whole architecture resting on a measurement of nothing. Stage
2 is the cheap gate that catches that before the investment.

## 2. Research question and hypothesis

**Question.** Does the fitted Jacobian readout, at the Stage 1 loci, carry
reproducible structure that is not recoverable from five cheaper or
structure-broken baselines?

The question is decomposed into two separately falsifiable conditions. Both must
hold for the instrument to earn the right to be treated as a real measurement.

- **H1, specificity.** The Jacobian readout is more distinct from
  structure-broken transports (a norm-matched random vector, a shuffled-layer
  transport, a mismatched-probe transport) than it is from the plain logit lens.
  Prediction: on at least 80% of prompts, the divergence between the Jacobian
  readout and each control family exceeds its divergence from the logit lens by a
  preregistered margin. If the readout looks the same whether you feed it the
  real fitted map or a scrambled one, its "signal" was never about the specific
  fit.
- **H2, added information.** The Jacobian readout differs from the logit lens on
  the same activation. Prediction: the median top-10 token overlap between the
  Jacobian and logit-lens readouts is at most 0.70, with a paired significance
  test below alpha. If the two always agree, the expensive transport is
  decoration. The proposal attached a second, conjunctive clause to this
  condition: the Jacobian readout must also not be within rerun noise of the
  output or prompt-only baselines (`STAGE2_DISCRIMINATION_PROPOSAL.md`, success
  condition 3). **That clause was never implemented and never evaluated** — see
  §3.8 item 3 and the qualification in §4.

The null across both: the Jacobian lens is observationally silent, its readouts
explained entirely by the logit lens (H2 fails) or by generic transport structure
(H1 fails). A null is a valid, publishable result under this protocol; it would
stop the lab from building on a lens that measures nothing distinctive.

## 3. Methods

### 3.1 Instruments and pinned identities

Every artifact was pinned to the exact identity used in Stage 1; Stage 2 adds no
new model or lens and re-resolves and asserts each identity at execution time.

| Component | Identity |
|---|---|
| Instrumentation | `github.com/anthropics/jacobian-lens` @ `581d398613e5602a5af361e1c34d3a92ea82ba8e` |
| Model | `Qwen/Qwen3-1.7B` rev `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e` (28 layers, d_model 2048, bf16) |
| Fitted lens | `neuronpedia/jacobian-lens` rev `a4114d7752d11eb546e6cf372213d7e75526d3a1`, file `Qwen3-1.7B_jacobian_lens.pt` |
| Lens bytes / SHA-256 | 226,501,315 / `6fcc79011bd921ffd87612255e2e99950a124fa519470ee44ebaf161c39be9d6` |

### 3.2 Runtime and capacity gate

CUDA required, minimum 14.0 GiB VRAM, abort before downloads if unmet. Measured
runtime: one Tesla T4; approximately 3.2 GiB allocated after loading the model
and lens, well inside the gate. The capacity gate is a measured pass, not a
weakened threshold.

### 3.3 Stimuli

Fifty synthetic, non-sensitive English prompts, five categories of ten: factual
completion, category membership, arithmetic completion, antonym/negation, and
multi-token entity continuation. Item one of category one is the exact Stage 1
prompt, whose reproduction is the kill criterion. A single prompt is n=1 with no
statistical power; fifty gives the paired tests real power. Raw text lives only in
a versioned in-repo manifest; every exported observation stores digests and token
counts, not raw prompt text.

### 3.4 Measurement loci

Layers 6, 13, 20, and 26 at token position -2, fixed to the Stage 1 selection so
the anchor reproduces. Top-k retained is 10; rank statistics are computed over the
top-50 union. Full-vocabulary logits are computed transiently and reduced to
sparse summaries before being discarded; raw activations, raw prompts, and full
logits are never persisted.

### 3.5 Readouts and baselines

At each locus the notebook computes six directly comparable readouts in the
model's vocabulary basis:

1. **Jacobian lens** (`lens.apply`, `use_jacobian=True`): the instrument under test.
2. **Logit lens** (`lens.apply`, `use_jacobian=False`): the cheap competitor.
3. **Output**: the model's own final-layer next-token logits.
4. **Prompt-only**: the input embedding decoded through the final norm and
   unembedding, a floor for "what is recoverable from the surface prompt alone."
5. **Random-vector**: a norm-matched, seeded random residual transported through
   the same source-layer Jacobian. Specificity control.
6. **Structure-broken**: two variants, a shuffled-layer transport (a different
   layer's activation through this layer's Jacobian) and a mismatched-probe
   transport (this layer's activation through a different layer's Jacobian).

Each transported baseline is decoded through the identical final norm and
unembedding used for the Jacobian and logit readouts, so all six share one
vocabulary basis (verified: the notebook's `decode_residual` is byte-identical in
effect to jlens's own `model.unembed`).

### 3.6 Metrics

- Primary per-pair divergence D, in [0,1]: half the complement of top-10 Jaccard
  plus half the normalized mean rank displacement of shared tokens. Larger D means
  more divergence.
- Added-information effect size: median top-10 Jaccard between Jacobian and logit
  lens, with a paired Wilcoxon signed-rank test against the null of identity.
- Supporting: Spearman correlation over the top-50 union, output-argmax rank, and
  scalar logit-difference summaries.
- Stability: two same-runtime repeats per prompt under fixed seed 0, plus control
  seeds; the random-vector baseline uses its own seed set.

### 3.7 Preregistered thresholds and decision rule

Locked before data collection (ratified, no longer provisional):

| Criterion | Constant | Value |
|---|---|---|
| Reproduction (kill anchor) | `STAGE1_RERUN_NOISE_MAX_ABS_LOGIT_DIFF` | 0.0 |
| Specificity: min prompt fraction | `SPECIFICITY_MIN_PROMPT_FRACTION` | 0.80 |
| Specificity: D margin over logit lens | `SPECIFICITY_D_MARGIN` | 0.10 |
| Added info: max median top-10 Jaccard | `ADDED_INFO_MEDIAN_JACCARD_MAX` | 0.70 |
| Added info: paired Wilcoxon alpha | `WILCOXON_ALPHA` | 0.01 |
| Same-runtime repeats | `SAME_RUNTIME_REPEATS` | 2 |
| Inference seeds | `INFERENCE_SEEDS` | [0, 1] |
| Random-vector seeds | `RANDOM_VECTOR_SEEDS` | [0, 1, 2] |

Decision rule: **pass** if reproduction and specificity and added information all
hold; **kill** if the anchor fails to reproduce or any pinned identity mismatches;
**ambiguity** if some but not all pass conditions hold; **fail** if the Jacobian is
within rerun tolerance of the logit lens across every category and layer, or
indistinguishable from the random-vector control.

### 3.8 Deviations and runtime fixes

Items 1 and 2 are runtime defects found and fixed during execution. Items 3 to 5
are divergences between the preregistration and what the notebook actually
evaluated. They were found on 2026-07-26 by an independent audit and are recorded
here because the earlier version of this report did not disclose them; each is
verified against the executed notebook
(`353479b0f0e959f2e207446b1383ebf632c05bf8c9a9656508cc91d98d4f28f5`). Items 1 and
2 altered no threshold or measurement definition. Items 3 to 5 do not change the
recorded decision, which was ambiguity on the specificity failure alone, but they
narrow what the added-information leg is entitled to claim.

1. **dtype.** jlens stores its fitted Jacobians as float32 and its own
   `lens.apply` casts residuals to float before transport, but the notebook's
   baseline paths fed the model's bfloat16 activations straight into
   `lens.transport`, raising a dtype mismatch. Fix: capture residuals as float32.
2. **device.** `lens.apply` returns readouts on CPU, but `decode_residual`
   returned them on CUDA, so the first cross-readout subtraction mismatched
   devices. Fix: `decode_residual` returns to CPU.

Both fixes made the notebook's own baseline path match jlens's conventions. The
run reaching and completing the measurement is itself the verification that the
capability probe bound `lens.transport` and the six readouts share one basis.

3. **The added-information gate underimplements its preregistration.** The
   proposal required, conjunctively, that the Jacobian readout also not be within
   rerun noise of the output or prompt-only baselines. The executed gate is:

   ```python
   added_info_pass = (
       median_jaccard_jac_vs_logit <= ADDED_INFO_MEDIAN_JACCARD_MAX
       and added_info_wilcoxon["wilcoxon_p"] == added_info_wilcoxon["wilcoxon_p"]  # not NaN
       and added_info_wilcoxon["wilcoxon_p"] < WILCOXON_ALPHA
   )
   ```

   There is no output-baseline or prompt-only term. Both readouts were computed
   (§3.5 items 3 and 4) but neither entered the decision. The separation the
   proposal asked for was therefore never tested.
4. **Declared inference seed 1 was never executed.** `INFERENCE_SEEDS = [0, 1]`
   is recorded into every exported artifact as `"inference_seeds"`, but the only
   seeding calls in the notebook are `torch.manual_seed(0)` and
   `torch.cuda.manual_seed_all(0)`. No result in this study was produced under
   seed 1, so the artifacts overstate the seed coverage of the run. The
   seed-invariance check the second seed was added for did not happen.
5. **Specificity used one random-vector seed of the three computed.** The loop
   `for seed in RANDOM_VECTOR_SEEDS:` computes all of `[0, 1, 2]`, but the
   decision path consumes `rv_seed_rows[RANDOM_VECTOR_SEEDS[0]]` only. The
   reported `random_vector_fraction` of 1.00 is a single-seed result. This is the
   control that passed most decisively, so the narrower basis matters less than
   it would for a marginal call, but the reported figure is not the three-seed
   aggregate a reader would reasonably assume.

## 4. Results

Aggregate output (n=50):

```json
{
  "run_id": "f9234a9c-6a2d-43da-9fbd-bf26b19ac18c",
  "n_prompts": 50,
  "median_jaccard_jacobian_vs_logit_lens": 0.19444444444444442,
  "specificity": {
    "random_vector_fraction": 1.0,
    "non_jspace_shuffled_fraction": 0.22,
    "non_jspace_mismatched_fraction": 0.4
  },
  "decision": "ambiguity"
}
```

Condition by condition:

- **Reproduction: pass.** The decision is not "kill", so the Stage 1 anchor
  reproduced its pinned top-k under the 0.0 tolerance.
- **Added information (H2): partial pass, on the implemented clause only.** The
  median top-10 Jaccard between the Jacobian and logit-lens readouts is 0.194,
  far below the 0.70 ceiling. On a typical prompt the two share only about two of
  their top ten tokens. The Jacobian lens is not a repackaged logit lens. But the
  preregistration's second clause — separation from the output and prompt-only
  baselines beyond rerun noise — was never implemented and never evaluated
  (§3.8 item 3). What this run established is **reported non-identity with the
  logit lens**, not the full added-information condition as preregistered. The
  earlier version of this report called this an unqualified pass; that was an
  overstatement.
- **Specificity (H1): fail.** The rule requires a D margin of at least 0.10 over
  the logit lens on at least 80% of prompts for all three control families. The
  random-vector control is cleared decisively (fraction 1.00): the Jacobian
  readout is nothing like a norm-matched random vector pushed through the same
  map. But the two structure-broken controls are not cleared: shuffled-layer 0.22
  and mismatched-probe 0.40, both far under 0.80.

Because H2 holds on its implemented clause and H1 does not, the decision is
**ambiguity**. The decision is unchanged by the §3.8 findings: it turned on the
specificity failure, and the added-information leg being narrower than
preregistered can only weaken the case for the instrument, never strengthen it.
An audit that narrows a partially-passing condition cannot convert an ambiguity
into a pass.

Evidence artifacts (content-addressed, schema
`jspace-observation-discrimination/v1`, retained in the ephemeral runtime, not
transferred): 50 per-prompt `jspace_observation_<sha16>.json` and one aggregate
`jspace_discrimination_251967260907468a.json`, aggregate SHA-256
`251967260907468a7a0086446855db403cded0c4c1fe9ae889417472cc86e0dc`. The Stage 1
anchor artifact is `22ca288fdb493e33...`. Each filename prefix equals the first
16 hex of its content hash.

## 5. Conclusion

The fitted Qwen3-1.7B Jacobian lens reports something a plain logit lens does not,
and its readouts are not random noise. Both of those are real, measured, and
reproducible under the anchor check. That is more than Stage 1 established.

Stated precisely, the first of those is *non-identity with the logit lens*, which
is weaker than "carries information a logit lens does not". A low top-10 overlap
shows the two readouts disagree; it does not show the disagreement is
informative, accurate, or useful. The preregistered clause that would have
started to separate those — non-identity with the output and prompt-only
baselines — was never evaluated (§3.8 item 3).

But the study cannot conclude that the Jacobian lens is measuring the specific
thing it is fitted to measure. The readout survives the easy control (random
vectors) and clearly fails to survive the hard ones (transports that keep the
Jacobian machinery but scramble which layer it applies to). On the preregistered
decision rule this is an **ambiguity**: promising, not conclusive.

Per the stage gates, an ambiguity does not promote any readout beyond evidence
class 1 and does not authorize causal intervention (Stage 3), publication,
artifact transfer, or integration into Sakshi or Elume. The lab does not build on
this instrument yet.

## 6. Discussion

### 6.1 What the result most likely means

The gap between the two conditions is the interesting part. H2 says the Jacobian
readout is far from the logit lens. H1 says it is roughly as far from the logit
lens as a shuffled-layer or mismatched-probe transport is. Read together, the most
parsimonious account is that a large fraction of what makes the Jacobian readout
"different from the logit lens" is generic to transporting a residual through
some layer-sized Jacobian, rather than specific to the correct fitted map at the
correct layer. The transport operation itself moves the readout; whether it is the
right transport is exactly what this run could not confirm.

That is not a refutation of the lens. It is a statement that this discrimination
design, at these thresholds, on these fifty prompts, lacks the resolution to
separate "the fitted lens at layer L" from "a Jacobian-shaped map at some layer."

### 6.2 Threats to validity and limits of the design

- **The D metric and margin.** D blends top-10 Jaccard with rank displacement, and
  the 0.10 specificity margin was set a priori without pilot data (it was the one
  threshold with no empirical anchor). The structure-broken controls are, by
  construction, close to the real transport; a metric or margin tuned to that
  regime might separate them, or might confirm they are genuinely inseparable.
  Either outcome is informative, but the current setting cannot distinguish them.
- **Structure-broken controls may be too strong.** A shuffled-layer transport
  still uses a real fitted Jacobian, just the wrong one. If adjacent layers'
  Jacobians are similar, the control is nearly the treatment, and no metric will
  cleanly separate them. This is a design question, not a lens failure.
- **Single runtime, single hardware, single seed regime.** No cross-runtime or
  cross-hardware reproducibility is claimed. Same-runtime repeatability is not
  external reproducibility.
- **Fifty synthetic prompts.** No construct or predictive validity beyond this
  stimulus set. The categories are deliberately simple next-token tasks.
- **Position and layers fixed to Stage 1.** Coverage is four layers at one
  position, not full-sequence or full-layer.

### 6.3 What is explicitly not established

Nothing here speaks to functional global-workspace properties, subjective
experience, phenomenal consciousness, or any cognitive interpretation of the
readouts. The readouts are activation-derived token rankings under a specified
protocol. Promotion to any functional claim would require Stage 3 causal
intervention with its own preregistration, and none of that is authorized by this
result.

### 6.4 Next iteration

The result points at one clear target: strengthen the structure-broken
discrimination before any promotion. Concrete moves, in rough order of value:

0. Implement the gates as preregistered, and assert that correspondence in the
   notebook rather than trusting it. Every §3.8 item 3 to 5 finding is a case of
   a constant being declared, recorded into artifacts, and then not used. A
   preflight that asserts each declared constant is actually consumed on the
   decision path would have caught all three before execution.
1. Pilot the D metric and the specificity margin against the structure-broken
   controls to learn whether they are genuinely inseparable or merely
   under-resolved at 0.10.
2. Reconsider the controls: a mismatched-probe using a distant layer, or a control
   that breaks the fit while preserving layer identity, may be a fairer test of
   "the specific fit matters."
3. Increase n and add prompt categories to raise power on the per-prompt fraction.
4. Only after specificity is resolved, consider a second hardware class to begin
   cross-runtime reproducibility.

### 6.5 Operational note (reproducibility)

The measurement took about twelve minutes on the T4, dominated not by the model
forward passes but by `output_argmax_rank` performing a full-vocabulary
(approximately 151k) argsort plus a Python integer comprehension roughly 48 times
per prompt. This is a performance issue, not a correctness one; a future version
should compute the target token's rank directly. The reproducible recipe, the two
runtime gotchas (float32 transport, CPU readouts), and the full run log are
recorded alongside this report and in the skill's reference doc.

## 7. Provenance

- Design and thresholds: `EvoScientist/skills/jspace-research-operations/`
  (SKILL.md, `references/stage2-discrimination-baseline.md`).
- Proposal and ratified defaults: `j-space-lab/STAGE2_DISCRIMINATION_PROPOSAL.md`,
  `j-space-lab/STAGE2_PROVISIONAL_DEFAULTS.md`.
- Executed notebook identity: `353479b0f0e959f2e207446b1383ebf632c05bf8c9a9656508cc91d98d4f28f5`.
- Fork PR (fork-internal, not upstream): `bionicbutterfly13/EvoScientist#2`,
  branch `docs/jspace-research-operations`. Ratification `d0a7596`, fixes
  `eb69193` and `b7a69ba`, result `36c6656`, artifact hashes `8cf02a5`.
- Boundaries held throughout: observation only, no fitting, steering, ablation,
  activation edit, artifact transfer, or Sakshi/Elume mutation.

### Amendment, 2026-07-26

§2, §3.8 (items 3 to 5), §4, §5, and §6.4 item 0 were amended to disclose three
divergences between the preregistration and the executed notebook: the
added-information gate omits the proposal's output and prompt-only clause;
declared inference seed 1 was never executed; and specificity used one
random-vector seed of the three computed. The findings originate from an
independent audit run through the EvoScientist engine (thread
`019f9a2a-5b5a-7d13-80ea-11622e8de7a3`, observation `O-9cfefddee56cd863`) and were
each re-verified directly against the executed notebook before being recorded.

The recorded decision remains **ambiguity**, unchanged. No measurement was
recomputed: the per-prompt artifacts were retained only in the ephemeral Colab
runtime and never transferred, so the omitted statistics cannot be recovered from
this run and would require a fresh execution. The canonical notebook was
deliberately not modified — its SHA-256 is the provenance anchor for the executed
bytes, and amending it would break the identity this report cites.
