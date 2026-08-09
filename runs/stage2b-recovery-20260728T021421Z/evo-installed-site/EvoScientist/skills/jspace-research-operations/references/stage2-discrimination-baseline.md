# Stage 2 discrimination reference (Qwen3-1.7B Jacobian Lens)

> **EXECUTED 2026-07-24 on a Colab T4 (ratified by Dr. Mani). DECISION:
> ambiguity.** The thresholds below are now locked (ratified), not provisional.
> See "First executed run — result" near the end for the measured decision and
> its reading. The thresholds table is retained as the preregistered record that
> was in force when the data was collected.

Use this dated reference when preparing, reviewing, or reproducing the Stage 2
observational-discrimination study. Re-resolve every remote resource at
execution time; this file is a design/provenance snapshot, not a floating source
of truth.

## Design notebook snapshot

- Prepared: 2026-07-22; float32-transport fix applied 2026-07-24 after the
  first Colab run (see "Runtime fix" below)
- Notebook name: `jspace_colab_stage2_discrimination.ipynb`
- Canonical source identity: 52,259 bytes; SHA-256
  `353479b0f0e959f2e207446b1383ebf632c05bf8c9a9656508cc91d98d4f28f5`
  (identities before the two runtime fixes: 52,245 / `4ec07894...`, then
  52,253 / `95fc7efe...`)
- Structure: nbformat 4, 22 cells, 10 code cells
- Stage: 2 (observational discrimination) per `SKILL.md`, "Experiment Stage Gates"
- Prerequisite: Stage 1 (measurement reproduction) partially completed by the
  pinned Qwen3-1.7B smoke test on one Tesla T4
- Boundary: observation only; no fitting, steering, ablation, activation edit,
  Sakshi/Elume mutation, transfer, or external publication
- Optional artifact download is an explicit authorization gate
- The measurement cell refuses to run unless `THRESHOLDS_RATIFIED` is True

## Pinned identities (copied verbatim from the Stage 1 smoke test)

- Jacobian Lens repository: `https://github.com/anthropics/jacobian-lens.git`
- Jacobian Lens commit: `581d398613e5602a5af361e1c34d3a92ea82ba8e`
- Model: `Qwen/Qwen3-1.7B`
- Model revision: `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`
- Expected model width: 2048
- Expected model layers: 28
- Lens repository: `neuronpedia/jacobian-lens`
- Lens revision: `a4114d7752d11eb546e6cf372213d7e75526d3a1`
- Lens file: `qwen3-1.7b/jlens/Salesforce-wikitext/Qwen3-1.7B_jacobian_lens.pt`
- Lens size (successful Stage 1 run): 226,501,315 bytes
- Lens SHA-256 (successful Stage 1 run):
  `6fcc79011bd921ffd87612255e2e99950a124fa519470ee44ebaf161c39be9d6`
- Lens fit metadata: 466 prompts recorded in the artifact
- Stage 1 anchor prompt SHA-256:
  `daeaa63881dc0f58be689307a81b1fbc347674424f1cae45819f82372804f5a6`

## Fixed measurement loci

- Layers: 6, 13, 20, 26 (the Stage 1 selection over the fitted source layers)
- Position: -2
- Top-k retained: 10; rank statistics computed over top-N = 50 (sparse summaries
  and scalar statistics only; full-vocabulary logits are never persisted)

## Capacity gate (carried forward unchanged)

- CUDA required
- Minimum total GPU VRAM: 14.0 GiB
- Abort before model/lens downloads if the gate fails
- Do not lower the threshold solely to force completion

## What a passing discrimination run must contain

A run is only interpretable if the kill criteria never fired: the capacity gate
passed, every pinned revision/size/SHA-256 resolved to the recorded identity,
and the Stage 1 anchor prompt (stimulus `s00`) reproduced its recorded top-k
token IDs with maximum Jacobian-logit difference 0.0.

Artifacts (all under schema `jspace-observation-discrimination/v1`):

- 50 per-prompt observation artifacts `jspace_observation_<sha256[:16]>.json`,
  each containing:
  - the pinned model/lens/instrumentation/runtime provenance blocks;
  - `input` with the prompt SHA-256, token/byte counts, and
    `raw_prompt_persisted=false`;
  - `stimulus` with `id`, `category`, and `stimulus_manifest_sha256`;
  - `measurement` with the six top-k readouts keyed by the four selected layers:
    `jacobian_lens`, `logit_lens_baseline`, `output_baseline`,
    `prompt_only_baseline`, `random_vector_baseline` (per seed), and
    `non_jspace_baseline` (shuffled-layer and mismatched-probe);
  - `measurement.repeatability_same_runtime` with same-runtime x2 repeat results;
  - a `discrimination` block with per-locus D, top-10 Jaccard, Spearman over
    top-50, output-argmax rank, and scalar logit-difference summaries;
  - `retention` with all three flags false.
- 1 aggregate run artifact `jspace_discrimination_<sha256[:16]>.json` containing
  the cross-prompt statistics, per-category medians, the stimulus-manifest
  digest, the preregistered thresholds as recorded before execution, the paired
  Wilcoxon result, and the pass/ambiguity/fail/kill decision.

Every artifact must pass
`validate_observation.py <file>` (the extended validator with
`jspace-observation-discrimination/v1` support). A passing per-prompt or
aggregate artifact re-hashes to its content-addressed filename prefix.

## PROVISIONAL preregistered thresholds

> Binding only after Dr. Mani ratifies them. No threshold may change after data
> collection begins.

| Criterion | Constant | Provisional value |
|---|---|---|
| Reproduction (kill anchor) | `STAGE1_RERUN_NOISE_MAX_ABS_LOGIT_DIFF` | 0.0 (anchor s00 top-k IDs identical) |
| Specificity: min prompt fraction | `SPECIFICITY_MIN_PROMPT_FRACTION` | 0.80 |
| Specificity: D margin over logit-lens | `SPECIFICITY_D_MARGIN` | 0.10 |
| Added information: max median top-10 Jaccard (Jacobian vs logit-lens) | `ADDED_INFO_MEDIAN_JACCARD_MAX` | 0.70 |
| Added information: paired Wilcoxon significance | `WILCOXON_ALPHA` | 0.01 |
| Same-runtime repeats | `SAME_RUNTIME_REPEATS` | 2 |
| Inference seeds (determinism) | `INFERENCE_SEEDS` | [0, 1] |
| Random-vector control seeds | `RANDOM_VECTOR_SEEDS` | [0, 1, 2] |

### Decision rule

- **Success:** reproduction holds AND specificity holds against both control
  families (random-vector and structure-broken) on at least 80% of prompts by
  the D margin AND added information holds (median top-10 Jaccard vs logit-lens
  ≤ 0.70 with paired Wilcoxon p < 0.01, and the Jacobian readout not within
  rerun noise of the output or prompt-only baselines).
- **Ambiguity:** conditions partially met; reported as a split result with the
  per-category table, no promotion of the readout.
- **Failure:** Jacobian within same-runtime rerun tolerance of the logit lens
  across every category and layer, OR indistinguishable from the random-vector
  control. Failure is a valid finding.
- **Kill:** capacity gate fails; OR any pinned revision/size/SHA-256 mismatches;
  OR the anchor prompt fails to reproduce. Stop and report the exact blocker.

## What this will not establish (even on success)

- cross-runtime or cross-hardware reproducibility (single T4 class only);
- calibrated probabilities or construct-level uncertainty;
- predictive or construct validity beyond these 50 synthetic prompts;
- causal mediation (Stage 3);
- functional global-workspace properties;
- subjective or phenomenal consciousness;
- readiness for Sakshi, Elume, or other observer integration.

## Open verification items before ratified execution

1. Confirm the jlens raw-vector transport primitive names at commit
   `581d398...`; the notebook's capability probe fails fast if the resolved names
   differ from the documented candidates. The random-vector and structure-broken
   baselines depend on this primitive.
2. Confirm the prompt-only baseline unembedding path (`hf_model.model.norm` +
   `hf_model.lm_head`) matches the logit-lens decode used inside `lens.apply`, so
   the six readouts share one vocabulary basis.
3. Verify batched/sequential application across 50 prompts stays within T4
   memory; if not, that is a measured capacity result, handled by sequential
   execution or a larger runtime, not by weakening the gate.

## Runtime fix (2026-07-24, first Colab T4 run)

All three verification items above were resolved at execution time on a Tesla
T4: the capability probe bound `lens.transport` (item 1); GPU memory after load
was ~3.2 GiB of ~14.5 (item 3); the prompt-only unembed path matched (item 2).

One runtime defect surfaced and was fixed. jlens stores its fitted Jacobians as
float32 and its own `lens.apply` casts residuals to float before transport, but
the notebook's baseline paths (`random_vector_readout` and the structure-broken
transports) fed the model's bfloat16 activations from `capture_layer_residuals`
straight into `lens.transport`, raising `RuntimeError: expected mat1 and mat2 to
have the same dtype (BFloat16 != float)` at `jlens/lens.py` `transport`. Fix:
capture residuals as float32 (`...detach().float()`), so every vector
transported through a Jacobian is float32, matching jlens; `decode_residual`
still casts back to the model dtype for the final norm+unembed. Reproduction
lesson: when transporting your own activations through a jlens `JacobianLens`
outside `lens.apply`, cast them to float32 first.

A second runtime defect surfaced on the next run: `RuntimeError: Expected all
tensors to be on the same device (cuda:0 and cpu)` at `logit_diff_summary`.
`lens.apply` returns its readouts on CPU (it calls `.cpu()` internally), but
`decode_residual` returned CUDA rows for the prompt-only/random-vector/
structure-broken baselines, so the first cross-row subtraction mismatched. Fix:
`decode_residual` now returns `.float().cpu()`, putting all six readouts on CPU.
Reproduction lesson: `lens.apply` returns CPU tensors; keep your own decoded
readouts on CPU too. Both fixes together give the notebook identity
`353479b0...` recorded above.

## First executed run — result (2026-07-24, Colab T4)

Ratified by Dr. Mani; executed on a Tesla T4 via browser automation, notebook
identity `353479b0...`. Measured decision (aggregate print):

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

Reading against the preregistered thresholds:

- Reproduction: PASS (decision is not "kill") — the Stage 1 anchor reproduced.
- Added information: PARTIAL PASS, implemented clause only — median top-10
  Jaccard vs the logit lens is 0.194 (<= 0.70) with the paired Wilcoxon below
  alpha. The fitted Jacobian readout is distinct from the plain logit lens, and
  fully distinct from the norm-matched random-vector control (fraction 1.0).
  **The second clause of the decision rule above — "the Jacobian readout not
  within rerun noise of the output or prompt-only baselines" — was not
  implemented in the notebook and was never evaluated.** The executed
  `added_info_pass` tests only the Jaccard ceiling and the Wilcoxon p-value.
  Both baselines were computed but neither entered the decision. What this run
  established is reported non-identity with the logit lens, not the full
  added-information condition. See the amendment note below.
- Specificity: FAIL — requires a D-margin over the logit lens of >= 0.10 on
  >= 80% of prompts for ALL three control families. random_vector clears it
  (1.0), but the structure-broken controls do not: shuffled-layer 0.22,
  mismatched-probe 0.40. Note the reported `random_vector_fraction` is a
  single-seed figure: all of `RANDOM_VECTOR_SEEDS = [0, 1, 2]` are computed, but
  only seed 0 reaches the decision path.
- DECISION: **ambiguity** (added information holds on its implemented clause;
  specificity does not). Unchanged by the findings above — the decision turned on
  the specificity failure, and a narrowed added-information leg can only weaken
  the case for the instrument.

Evidence artifacts written (content-addressed, schema
`jspace-observation-discrimination/v1`; kept in the ephemeral Colab runtime, not
transferred — download is a separate authorization gate that was not exercised):
50 per-prompt `jspace_observation_<sha16>.json` plus 1 aggregate
`jspace_discrimination_251967260907468a.json` with SHA-256
`251967260907468a7a0086446855db403cded0c4c1fe9ae889417472cc86e0dc`. The Stage 1
anchor (stimulus s00) artifact is `22ca288fdb493e33...`. Each filename prefix
equals the first 16 hex of its content SHA-256 (content-addressing verified).

Meaning: the fitted lens reports something a cheap logit lens does not and is not
random noise, but this run cannot separate that signal from generic
Jacobian-transport structure — the shuffled-layer and mismatched-probe controls
are not cleanly beaten. State the first half precisely: it is non-identity with
the logit lens, which is weaker than "carries information a logit lens does not".
A low top-10 overlap shows the two readouts disagree; it does not show the
disagreement is informative, accurate, or useful. Per the stage gates, ambiguity
does NOT promote the readout beyond evidence class 1 and does NOT authorize
Stage 3, publication, transfer, or Sakshi/Elume integration. Next iteration
should implement the gates as preregistered and strengthen the structure-broken
discrimination (more prompts; and/or revisit the D metric and the 0.10 margin;
and/or the controls themselves) before any promotion.

## Amendment, 2026-07-26 — preregistration/implementation divergences

Three divergences between the ratified design above and the executed notebook
(`353479b0f0e959f2e207446b1383ebf632c05bf8c9a9656508cc91d98d4f28f5`), found by an
independent audit and each re-verified directly against the notebook source:

1. **The added-information gate omits its second clause.** The decision rule
   requires separation from the output and prompt-only baselines beyond rerun
   noise; `added_info_pass` tests only `median_jaccard <= 0.70` and the Wilcoxon
   p-value. Never evaluated.
2. **`INFERENCE_SEEDS = [0, 1]` but only seed 0 ran.** The value is written into
   every artifact as `"inference_seeds"`, yet the only seeding calls are
   `torch.manual_seed(0)` / `torch.cuda.manual_seed_all(0)`. The artifacts
   overstate the run's seed coverage, and the seed-invariance check the second
   seed existed for did not happen.
3. **Specificity consumed one of three random-vector seeds.** All of
   `RANDOM_VECTOR_SEEDS` are computed; only `rv_seed_rows[RANDOM_VECTOR_SEEDS[0]]`
   feeds the decision.

The common failure mode: a constant is declared, recorded into artifacts, and
then not consumed on the decision path. **Any future stage must assert that each
declared threshold constant is actually used in the gate it names**, as part of
the preflight, rather than trusting the declaration. All three would have been
caught before execution by that one check.

These findings do not change the recorded decision (ambiguity). The omitted
statistics cannot be recovered from this run — the per-prompt artifacts lived
only in the ephemeral Colab runtime and were never transferred — so closing them
requires a fresh execution. The canonical notebook was deliberately left
unmodified: its SHA-256 is the provenance anchor for the executed bytes.

Performance note (not a correctness issue): the measurement took ~12 min on the
T4, dominated by `output_argmax_rank` doing a full-vocabulary (~151k) argsort
plus a Python int-list comprehension ~48x per prompt. A future optimization is
to compute the target token's rank directly, e.g. `(row > row[target]).sum()+1`.
