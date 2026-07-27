# Stage 2 proposal: observational discrimination of the Jacobian lens

- Status: Draft proposal for Dr. Mani's authorization. Design only.
- Authorizes: nothing to execute. No GPU work, no notebook authoring, no
  transfer, no publication.
- Stage: 2 (observational discrimination) per
  `EvoScientist/skills/jspace-research-operations/SKILL.md`, "Experiment Stage
  Gates".
- Prerequisite state: Stage 1 (measurement reproduction) partially completed by
  a pinned Qwen3-1.7B smoke test on one Tesla T4 (single synthetic prompt,
  same-runtime repeats only). See
  `sakshi notes/JSPACE_COLAB_SMOKE_TEST_PROVENANCE.md`.
- Evidence class of everything below: intended class 1 (direct runtime
  measurement) only. No readout is promoted to a functional or consciousness
  claim.

## 1. Objective as a falsifiable discrimination question

Stage 1 established that the pinned model/lens pair produces sparse Jacobian
readouts that are self-consistent within one T4 runtime (identical top-k token
IDs across repeats, maximum Jacobian-logit difference 0.0). Stage 1 recorded a
logit-lens baseline in the same cell but did **not** record how far the Jacobian
readout diverged from that baseline. Whether the Jacobian transport carries any
observable information beyond cheaper readouts is therefore genuinely open.

Discrimination question (falsifiable):

> At the pinned measurement loci, does the Jacobian-lens readout of an internal
> activation carry reproducible structure that is NOT recoverable from (a) the
> logit lens on the same activation, (b) the model's own output logits, (c) a
> prompt-surface baseline, (d) a norm-matched random vector transported by the
> same lens, or (e) a structure-broken (shuffled-layer / mismatched-Jacobian)
> transport?

Two conditions must both hold for a positive answer, and each is separately
falsifiable:

1. **Specificity.** The Jacobian readout on the real activation must diverge
   from the random-vector and structure-broken transports by more than those
   controls diverge from each other. If the Jacobian readout is
   indistinguishable from a random vector pushed through the same lens, the
   readout reflects transport/unembedding geometry, not activation content.
2. **Added information.** The Jacobian readout must diverge, reproducibly and in
   structured (non-noise) fashion, from the logit lens on the *same* activation,
   from the output logits, and from the prompt-surface baseline. If the Jacobian
   top-k is within same-runtime rerun tolerance of the logit lens across every
   stimulus category, the Jacobian transport is observationally silent at these
   loci and the lens adds nothing measurable here.

Falsification of the objective: condition 1 fails (readout not specific to the
activation) OR condition 2 fails (readout not separable from the logit lens).
Either outcome is a valid, reportable Stage 2 result and is not a defect to be
engineered away.

This is observational. It tests whether the lens *reads* something extra, not
whether that something is causal (Stage 3) or corresponds to any cognitive
construct (Stage 4+).

## 2. Exact pinned identities to reuse

Copied verbatim from `sakshi notes/JSPACE_COLAB_SMOKE_TEST_PROVENANCE.md` and
`references/known-good-smoke-test.md`. Stage 2 reuses these exactly; it resolves
and asserts them again at execution time and introduces no new model or lens.

- Jacobian Lens repository: `https://github.com/anthropics/jacobian-lens.git`
- Jacobian Lens commit: `581d398613e5602a5af361e1c34d3a92ea82ba8e`
- Model: `Qwen/Qwen3-1.7B`
- Model revision: `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`
- Expected model width: 2048
- Expected model layers: 28
- Lens repository: `neuronpedia/jacobian-lens`
- Lens revision: `a4114d7752d11eb546e6cf372213d7e75526d3a1`
- Lens file: `qwen3-1.7b/jlens/Salesforce-wikitext/Qwen3-1.7B_jacobian_lens.pt`
- Lens size (successful run): 226,501,315 bytes
- Lens SHA-256 (successful run):
  `6fcc79011bd921ffd87612255e2e99950a124fa519470ee44ebaf161c39be9d6`
- Lens fit metadata: 466 prompts recorded in the artifact

Reference successful runtime (target class, not a hard pin):

- GPU Tesla T4, total VRAM 14.563 GiB, compute capability 7.5, compute dtype
  `torch.bfloat16`, CUDA runtime 12.8, driver 580.82.07, Python 3.12.13,
  Torch 2.11.0+cu128, Transformers 5.13.1, Hugging Face Hub 1.23.0.

Capacity gate carried forward unchanged: CUDA required; minimum total GPU VRAM
14.0 GiB; abort before model/lens downloads if the gate fails; do not lower the
threshold to force completion.

## 3. Measurement loci (fixed before execution)

To avoid free-parameter search, Stage 2 fixes the loci to the Stage 1 loci:

- Layers: 6, 13, 20, 26 (the smoke test's selection over the fitted source
  layers).
- Position: -2.
- Top-k retained: 10 (matching the smoke test). Rank statistics computed over a
  wider top-N (proposed N = 50) but only sparse summaries and scalar statistics
  are retained; full-vocabulary logits are never persisted.

Expanding loci to all fitted source layers or multiple positions is a decision
point (Section 11, Q2), not a silent default.

## 4. Baselines

All five baselines are computed inside the same loaded runtime, on the same
loaded model and lens objects, at the same loci, for every stimulus. Each is a
top-k readout in the model's final-layer vocabulary basis so that all six
readouts (Jacobian plus five baselines) are directly comparable by rank and
logit. The Jacobian call `lens.apply(model, prompt, layers=, positions=,
max_seq_len=, use_jacobian=True)` and its `use_jacobian=False` companion already
exist in the Stage 1 notebook; the other baselines reuse the returned tensors or
the loaded weights.

### 4.1 Logit-lens baseline (skill: "logit")

- Definition: decode the same residual-stream activation directly through the
  model's unembedding without the Jacobian transport.
- Computation: `lens.apply(..., use_jacobian=False)` at the identical loci
  (already invoked in Stage 1 cell 12 as `baseline_logits`).
- Agreement means: at these loci the Jacobian transport does not change what the
  activation decodes to; the lens is observationally silent here (fails
  condition 2). Structured, reproducible disagreement is the necessary signal
  that the Jacobian reads something the direct decode does not.

### 4.2 Output baseline (skill: "output")

- Definition: the model's own next-token logits at the measured position (what
  the model is actually disposed to emit).
- Computation: the `model_logits` tensor already returned by `lens.apply`
  (`model_logits_1` in Stage 1); retain its sparse top-k.
- Agreement means: the Jacobian readout is re-describing the surface output
  distribution rather than an internal, not-yet-verbalized disposition.
  Divergence is what would distinguish an internal readout from an output
  readout.

### 4.3 Prompt-only baseline (skill: "prompt-only")

- Definition: a readout that depends only on the input surface, before deep
  computation. Proposed operationalization: decode the position's input token
  embedding (layer-0 residual) through the unembedding, i.e. the
  input-embedding logit lens. This isolates information present at the input
  from information computed across layers.
- Computation: same unembedding used by the logit-lens baseline, applied to the
  layer-0 embedding of the measured position, in the same runtime.
- Agreement means: the Jacobian readout is a trivial function of surface token
  identity. Divergence is required to claim the readout reflects computed
  internal state rather than the prompt tokens themselves.

### 4.4 Random-vector baseline (skill: "random-vector")

- Definition: transport a random residual-stream vector, matched to the observed
  per-layer activation norm, through the same fitted Jacobian at the same layer,
  and decode.
- Computation: sample standard-normal vectors scaled to the measured activation
  norm at each layer; apply the same lens transport; repeat across a small seed
  set (proposed 3 seeds) to characterize the control distribution. Retain only
  summary statistics per seed, not raw vectors or full logits.
- Disagreement means: the Jacobian output is specific to the real activation,
  not an artifact of the transport-plus-unembedding geometry (supports condition
  1). Agreement with the real readout would falsify specificity.

### 4.5 Non-J-space baseline (skill: "non-J-space")

- Definition: a structure-broken transport that holds the activation constant
  but destroys the fitted layer-matched Jacobian structure. Two variants,
  reported separately:
  - shuffled-layer: apply layer L's fitted Jacobian to the activation captured
    at a different fitted layer L' (the smoke test's named "shuffled-layer"
    control);
  - mismatched-probe: apply a permuted/rolled copy of the fitted Jacobian to the
    correct-layer activation (the smoke test's named "deliberately
    mismatched-probe" control).
- Computation: reuse the loaded lens weights with a layer or index permutation;
  no new download, no re-fit.
- Disagreement means: the specific fitted per-layer structure carries the
  signal (supports condition 1). Agreement would indicate the readout does not
  depend on the correct fit and is not J-space-specific.

## 5. Stimulus set design

### 5.1 Why a single synthetic prompt is insufficient

Stage 1 measured one prompt (`Fact: The currency used in the country shaped like
a boot is`, 13 tokens, position -2). With n = 1 there is no way to separate
lens-specific structure from a single-prompt coincidence, no category variance,
no paired statistic, and no power to detect whether Jacobian-vs-baseline
divergence is reproducible or accidental. The provenance doc lists this exactly:
"The synthetic prompt does not establish predictive or construct validity." A
discrimination test needs paired, per-prompt comparisons across categories.

### 5.2 Set

- Synthetic, non-sensitive, English, short (each ≤ `MAX_PROMPT_TOKENS` = 128,
  most far shorter), no personal or restricted content.
- Proposed size: 5 categories x 10 prompts = 50 prompts (sample size is Q1).
- Categories chosen so a downstream target token or distribution is
  well-defined and varies across items, and so surface and internal readouts can
  plausibly diverge:
  1. factual completion (the Stage 1 prompt's family: entity → attribute);
  2. category membership (instance → superordinate);
  3. simple arithmetic completion;
  4. antonym / negation (surface token and intended completion differ);
  5. multi-token entity continuation.
- The Stage 1 prompt is included as item 1 of category 1 so its exact
  reproduction is checked inside the same run (see kill criterion).

### 5.3 Retention rules

Two distinct retention surfaces, matching the existing digest-not-raw contract:

- Stimulus manifest: because these prompts are synthetic and non-sensitive,
  raw text is retained in one versioned stimulus manifest (per-prompt: id,
  category, raw text, SHA-256, token count) so the set is reproducible. Whether
  the raw manifest is committed in-repo is Q5.
- Observation artifacts: keep the Stage 1 contract exactly. Per-prompt exported
  observations store the prompt SHA-256 and token/byte counts, with
  `raw_prompt_persisted=false`, `raw_activations_persisted=false`,
  `full_logits_persisted=false`. Raw prompt text never enters an observation
  artifact regardless of the manifest decision.

## 6. Preregistered criteria (locked before any execution)

Thresholds below are proposed and become binding only after Dr. Mani approves
them (Q4). No threshold may be changed after data collection begins.

Primary per-prompt divergence metric D between two readouts at a locus: the
complement of top-10 Jaccard overlap combined with the rank displacement of the
shared tokens (exact statistic fixed in Section 7). Larger D means more
divergence.

- **Success:**
  1. Reproduction: the Stage 1 prompt reproduces its recorded top-k token IDs at
     all four layers and maximum Jacobian-logit difference 0.0 across
     same-runtime repeats (determinism preserved); AND
  2. Specificity: D(Jacobian, real) vs the random-vector and structure-broken
     controls exceeds D(Jacobian, logit-lens); i.e. the Jacobian readout is
     closer to the matched logit lens than to a random or structure-broken
     transport, by a predefined margin, across a preregistered majority of
     prompts (proposed: ≥ 80% of prompts, both control families); AND
  3. Added information: D(Jacobian, logit-lens) exceeds same-runtime rerun noise
     (which Stage 1 measured at 0.0) by a preregistered minimum effect
     (proposed: median top-10 Jaccard ≤ 0.7 between Jacobian and logit-lens,
     with a Wilcoxon signed-rank test over paired prompts at alpha = 0.01), and
     the Jacobian readout is not within rerun noise of the output or
     prompt-only baselines either.
- **Ambiguity:** conditions partially met, e.g. added information present in some
  categories/layers but within noise in others, or specificity holds against
  random vectors but not against the structure-broken control. Reported as a
  split result with the per-category table; no promotion of the readout.
- **Failure:** D(Jacobian, logit-lens) is within same-runtime rerun tolerance
  across every category and layer (the Jacobian transport is observationally
  silent), OR the Jacobian readout is statistically indistinguishable from the
  random-vector control (no specificity). Failure is a valid finding.
- **Kill (stop immediately, do not continue collecting):** capacity gate fails;
  OR any pinned revision/SHA-256 does not resolve to the recorded identity; OR
  the Stage 1 prompt fails to reproduce its recorded top-k token IDs and zero
  logit difference (indicates environment or determinism drift that invalidates
  every subsequent comparison). On kill, stop and report the exact blocker.

## 7. Metrics, repeats, and seeds

- Per (prompt, layer, readout-pair):
  - top-10 Jaccard overlap;
  - Spearman rank correlation over the union of the two top-N (N = 50);
  - rank of the model output's argmax token within each readout (does the
    Jacobian place the eventually-verbalized token differently than the logit
    lens?);
  - symmetric logit-difference summary: max and mean absolute logit difference
    over the vocabulary, computed transiently and reduced to scalars before the
    full logits are discarded (never persisted).
- Determinism / repeats: same-runtime repeat x2 per prompt as in Stage 1;
  expect maximum Jacobian-logit difference 0.0 and identical top-k IDs. Record
  any nonzero value as a determinism anomaly.
- Seeds: Torch seed fixed at 0 as in Stage 1 for the deterministic
  inference-mode path; a second seed confirms seed-invariance of that path
  (expected identical under `inference_mode`). The random-vector baseline uses
  its own declared seed set (proposed 3) because it is the only stochastic
  component.
- Cross-prompt aggregation: paired nonparametric tests (Wilcoxon signed-rank or
  sign test) on the per-prompt D values, reported with effect sizes and the full
  per-prompt / per-category tables. With n on the order of 50, effect size and
  the complete table are primary; p-values are secondary and reported with the
  preregistered alpha.

## 8. Artifact plan

- New schema id: `jspace-observation-discrimination/v1`.
- Backward compatibility with `scripts/validate_observation.py`: the current
  validator requires `scope == open_loop_observation_only`,
  `evidence_class == direct_runtime_measurement`, the three retention flags
  false, `input.sha256` present, model/lens/instrumentation/runtime blocks, and
  `measurement.jacobian_lens` / `measurement.logit_lens_baseline` keyed exactly
  by `measurement.selected_layers`. Stage 2 per-prompt observation artifacts
  keep every one of those fields unchanged, so the existing validator continues
  to accept them without modification. The added baselines and discrimination
  statistics live under new keys the validator ignores (it checks required-field
  presence, not the absence of extra keys):
  - `measurement.output_baseline`, `measurement.prompt_only_baseline`,
    `measurement.random_vector_baseline` (with seeds),
    `measurement.non_jspace_baseline` (shuffled-layer and mismatched-probe),
    each keyed by `selected_layers`;
  - `discrimination` block with the per-locus D metrics and rank statistics;
  - `stimulus` block extended with `category` and a `stimulus_manifest_sha256`
    reference.
- Content addressing: reuse the Stage 1 scheme exactly. Per-prompt artifacts are
  written as canonical JSON (`sort_keys`, trailing newline), filename
  `jspace_observation_<sha256[:16]>.json`, never overwriting a differing
  checksum, read back and re-hashed.
- One aggregate run artifact `jspace_discrimination_<sha256[:16]>.json` holds the
  cross-prompt statistics, the stimulus-manifest digest, the preregistered
  thresholds as recorded before execution, and the pass/ambiguity/fail decision.
  This aggregate uses the new schema id and is validated by an extended
  validator mode; adding that mode is Stage 2 execution work, not part of this
  proposal (Q7).
- Transfer remains a separate authorization with independent local hashing, per
  the skill. This proposal does not authorize transfer.

## 9. Resource estimate

- Runtime class: one Tesla T4 (or equal/greater) is expected to suffice. Stage 1
  loaded the full Qwen3-1.7B in bf16 plus the 226 MB fitted lens within the
  14.563 GiB T4 and printed allocated/reserved memory with headroom. The fitted
  lens is a stored average Jacobian, so `lens.apply` performs a forward pass plus
  transport matmuls rather than per-prompt gradient computation; the extra
  baselines are decodes of already-computed tensors or reuse of loaded weights.
  Assumption to verify at preflight, not asserted: that batched/sequential
  application across 50 short prompts stays within T4 memory. If it does not,
  that is a measured capacity result, handled by sequential execution or a
  larger runtime, not by weakening the gate.
- Wall-clock (rough): model + lens load 1-2 min (cached after first pull); each
  prompt is short (≤ 128 tokens, mostly far shorter) so a forward-plus-transport
  is well under a second; ~50 prompts x 4 layers x (Jacobian + 5 baselines) x 2
  repeats, plus 3 random-vector seeds, is on the order of a few thousand short
  decodes. Estimated total run under ~30 min wall-clock on one T4 including the
  first download. This is an estimate, not a measurement.
- Downloads: none beyond the three already-resolved pinned artifacts (jlens git
  commit, Qwen3-1.7B revision, the single lens `.pt`). No new models. Random and
  structure-broken baselines are derived from loaded objects.

## 10. Out of scope (explicit)

- No causal intervention of any kind: no steering, ablation, addition, swap, or
  activation edit. That is Stage 3 and requires separate authorization.
- No lens fitting or re-fitting; the fitted lens is used read-only.
- No new or non-pinned models, lenses, or tokenizers; no download beyond the
  pinned three.
- No consciousness, phenomenal, subjective-experience, or functional
  global-workspace claim. No promotion of any readout from class 1 to class 2 or
  3.
- No Sakshi, Elume, or other observer/architecture integration; no writing into
  any candidate cognitive substrate.
- No cross-runtime or cross-hardware reproducibility claim; Stage 2 as scoped
  runs on the single T4 class (adding a second runtime is Q6).
- No publication and no external transfer authorized by this document.
- No notebook authoring or GPU execution authorized by this document; those
  begin only after the open questions are settled and Dr. Mani authorizes them
  (Q8).

## 11. Open questions requiring Dr. Mani's decision

1. Sample size and categories: approve 5 categories x 10 = 50 synthetic prompts,
   or specify a different n and category set?
2. Measurement loci: keep the Stage 1 loci fixed (layers 6/13/20/26, position
   -2), or expand to all fitted source layers and/or additional positions?
3. Downstream criterion for "carries information": is the model's own next-token
   output an acceptable observational target, or do you want a held-out
   behavioral report task (which edges into the Stage 2 reportability study and
   needs additional design)?
4. Preregistered thresholds: approve and lock the specific effect-size and
   significance thresholds in Section 6 (Jaccard, rank displacement, control
   margin, alpha), or set your own before any execution?
5. Raw stimulus retention: may the raw synthetic prompt text be committed as a
   versioned in-repo stimulus manifest (observation artifacts stay digest-only),
   or should everything remain digest-only?
6. Runtime scope: single T4 class only (matching Stage 1), or add a second
   runtime/hardware class in this stage to begin cross-runtime reproducibility?
7. Validator: extend `scripts/validate_observation.py` with a
   `jspace-observation-discrimination/v1` mode as part of Stage 2 execution, or
   add a separate validator and leave the current one untouched?
8. Execution authorization: this proposal authorizes nothing to run. Do you
   authorize authoring the Stage 2 notebook and executing it on a GPU runtime
   once Q1-Q7 are settled?
