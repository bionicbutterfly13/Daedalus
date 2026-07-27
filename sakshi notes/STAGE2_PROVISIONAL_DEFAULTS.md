# Stage 2 provisional defaults (the 8 open questions)

These are the adopted answers to the open questions in Section 11 of the Stage 2
discrimination proposal. They are embedded as the notebook's defaults and
preregistered thresholds.

## RATIFIED 2026-07-23 by Dr. Mani

Dr. Mani ratified all eight open questions on 2026-07-23, including Q8:
**Stage 2 GPU execution is authorized.** The thresholds in the review below are
now locked and binding; none may change after data collection begins.

Execution follows the Stage 1 pattern: the canonical notebook stays immutable
(gate `THRESHOLDS_RATIFIED = False` left in the design artifact by design); the
run is performed on a disposable Colab copy where `THRESHOLDS_RATIFIED` is set to
True in cell 4. A single Tesla T4 run, observation only, per the locked
parameters. Results (per-prompt + aggregate `jspace-observation-discrimination/v1`
artifacts) are validated with `scripts/validate_observation.py` and the aggregate
decision (pass / ambiguity / fail / kill) is reported back for interpretation.

## Ratification review (2026-07-23, set on Dr. Mani's delegation)

Dr. Mani delegated the parameter choices ("set reasonable settings, I don't
know"). All eight were reviewed against the design. Q1 to Q7 are confirmed
reasonable and locked as the preregistered set; the notebook already holds these
values, so no numbers changed. Q8 (execution authorization) is deliberately left
to Dr. Mani and the notebook gate stays closed.

- Q1 (50 prompts, 5x10): confirmed. n=50 gives the paired Wilcoxon real power; a
  single prompt is n=1 with none.
- Q2 (loci 6/13/20/26, position -2): confirmed. Must match Stage 1 so the s00
  anchor reproduces, which is the kill check.
- Q3 (model's own next-token output as target): confirmed for an observational
  stage; no held-out task added yet.
- Q4 thresholds: confirmed as set. Specificity margin 0.10 on at least 80% of
  prompts against both control families; added-information median top-10 Jaccard
  vs logit-lens at most 0.70 with paired Wilcoxon p < 0.01; kill if the s00
  anchor's max Jacobian-logit rerun difference exceeds 0.0. These lean
  conservative in the safe direction: they resist concluding the lens is special
  when it is not. The 0.70 added-information bar is the most lenient constant;
  left as is, because tightening a preregistered threshold without data risks a
  false negative.
- Q5 (raw text in a versioned in-repo manifest; artifacts digest-only):
  confirmed.
- Q6 (single T4 class): confirmed for this stage; no cross-runtime claim.
- Q7 (extend the existing validator): confirmed; already implemented and tested.
- Q8 (execution authorization): **RATIFIED by Dr. Mani 2026-07-23.** GPU
  execution is authorized. The canonical notebook keeps
  `THRESHOLDS_RATIFIED = False` (immutable design artifact); the run copy sets it
  True in cell 4. That flag remains the human go/no-go signature, now given.

The provisional answers below are retained verbatim for the record.

## Q1: Sample size and categories

**Default:** 5 categories x 10 prompts = 50 synthetic, non-sensitive prompts.
Categories: factual completion, category membership, arithmetic completion,
antonym/negation, multi-token entity continuation. The Stage 1 prompt is item 1
of category 1.

Provisional; requires Dr. Mani's ratification before GPU execution.

## Q2: Measurement loci

**Default:** keep the Stage 1 loci fixed: layers 6, 13, 20, 26 at position -2,
with no expansion to all fitted source layers or additional positions.

Provisional; requires Dr. Mani's ratification before GPU execution.

## Q3: Downstream criterion for "carries information"

**Default:** the model's own next-token output (the `output_baseline`) is the
observational target. No held-out behavioral report task is added in this stage.

Provisional; requires Dr. Mani's ratification before GPU execution.

## Q4: Preregistered thresholds

**Default:** lock the Section 6 thresholds as embedded in the notebook:
specificity margin `SPECIFICITY_D_MARGIN` = 0.10 on ≥ 80% of prompts
(`SPECIFICITY_MIN_PROMPT_FRACTION` = 0.80) against both control families; added
information `ADDED_INFO_MEDIAN_JACCARD_MAX` = 0.70 median top-10 Jaccard
(Jacobian vs logit-lens) with paired Wilcoxon at `WILCOXON_ALPHA` = 0.01;
same-runtime repeats = 2; inference seeds [0, 1]; random-vector seeds [0, 1, 2].

Provisional; requires Dr. Mani's ratification before GPU execution.

## Q5: Raw stimulus retention

**Default:** the raw synthetic prompt text is retained in one versioned in-repo
stimulus manifest (`jspace-stage2-stimulus/v1`), while observation artifacts
stay digest-only (`raw_prompt_persisted=false`).

Provisional; requires Dr. Mani's ratification before GPU execution.

## Q6: Runtime scope

**Default:** single Tesla T4 class only, matching Stage 1. No second
runtime/hardware class is added in this stage; no cross-runtime reproducibility
claim is made.

Provisional; requires Dr. Mani's ratification before GPU execution.

## Q7: Validator

**Default:** extend `scripts/validate_observation.py` with a
`jspace-observation-discrimination/v1` mode (per-prompt and aggregate) via schema
auto-detection, preserving all existing smoke-test behavior and the stdlib-only
constraint, rather than adding a separate validator.

Provisional; requires Dr. Mani's ratification before GPU execution.

## Q8: Execution authorization

**Default:** authoring the Stage 2 notebook is permitted; GPU execution remains
unauthorized. The notebook's measurement cell refuses to run while
`THRESHOLDS_RATIFIED` is False, and the final stage-gate cell states execution is
not authorized until ratification.

Provisional; requires Dr. Mani's ratification before GPU execution.
