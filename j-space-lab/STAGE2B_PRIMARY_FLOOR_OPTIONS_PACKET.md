# Stage 2b primary-floor decision options

Status: **DRAFT OPTIONS — MECHANISM AUDIT NOT COMPLETED; NO RUN AUTHORIZED**

Date: 2026-07-31

## Decision boundary

The completed pilot directly established prompt-floor dependence under its
preregistered rules. It did not establish why the primary
`input_embedding_decoded` floor excluded two arithmetic-completion prompts, and
it did not produce a pilot pass/fail decision.

The retained-artifact diagnostic was frozen before inspecting prompt-level
mechanism data:

- diagnostic source commit: `3c26569b0d3fe4bb8a5fa79d311b231418cdb85c`;
- diagnostic source SHA-256:
  `f8bf8563ec8085ab0ca98bbf266aa93ee346ef7917abc7e5287d93d1b0edc32b`;
- independent adversarial verdict: GO;
- local validation: `495 passed` J-space and `3553 passed, 12 skipped`
  repository-wide;
- fork-internal PR #10 merged as
  `66fe6843854f380e5eec7bc17c46207c3c9c0544` after six green CI checks.

The first Colab execution failed closed before reading the artifact because the
exact artifact and pilot-view files were absent from the active `/content`
runtime. A filename-only probe found `.config` and `sample_data` and confirmed
both required files were absent. This state is consistent with a reset or
replacement, but the precise lifecycle event is unknown. The artifact was not
reconstructed, uploaded, downloaded, or transferred; confirmation was not
accessed. Consequently, this packet defines falsifiable alternatives but records
**no prompt-level mechanism association**.

## The five live explanations

These explanations can overlap. The next study must measure them together rather
than declaring a winner from two excluded prompts.

### H1 — Prompt construction

Arithmetic prompt forms may place the model-output target unusually close to the
decoded input-embedding reference.

Prediction: on a disjoint development set, preregistered arithmetic templates
will differ in primary-denominator distributions even after holding tokenizer
and target features fixed.

Falsifier: template identity adds no reproducible predictive information beyond
tokenization, target, and denominator variables.

### H2 — Tokenization

Prompt length, final-token boundaries, or the model target's token piece may be
associated with primary-floor exclusion.

Prediction: one or more preregistered tokenizer features will reproduce across
independently generated arithmetic prompts and explain exclusion better than
template identity alone.

Falsifier: tokenizer features show no stable association after prompt template
and target properties are accounted for.

### H3 — Target properties

The model-selected argmax target, tie structure, or output-score geometry may
make some arithmetic items poorly separated from the primary floor.

Prediction: exclusions will concentrate among prompts with preregistered target
features such as particular token pieces, ties, or small output-to-floor score
separation.

Falsifier: target features do not reproduce on a disjoint development set and
do not improve prediction beyond prompt and tokenizer variables.

### H4 — Floor geometry

The decoded input embedding may be a weak normalization reference for some
otherwise valid prompts even when the layer-0 residual reference remains
well-separated.

Prediction: the same prompts will repeatedly have small
`s(output) - s(input_embedding_decoded)` denominators but adequate
`s(output) - s(layer0_residual_decoded)` denominators across model reruns with
fixed source identities.

Falsifier: the apparent floor difference disappears on a disjoint development
set or is fully explained by prompt, tokenizer, or target variables.

### H5 — Global guard interaction

The globally derived fifth-percentile guard may interact with category balance:
a small number of valid low-denominator arithmetic prompts can leave overall
coverage at 18 of 20 while breaking the three-of-four category minimum.

Prediction: under the already-ratified guard derivation, arithmetic prompts will
show a reproducible excess of near-boundary denominators on a disjoint
development set.

Falsifier: arithmetic prompts are not unusually concentrated near the guard, or
the pattern fails to reproduce before any revised pilot is selected.

## Options for Dr. Mani

No option changes the completed pilot. Options B through D define new estimands
or primary claims and therefore require a new specification, review, and pilot.

### Option A — Keep the primary floor and redesign only the development process

Generate a larger, balanced arithmetic candidate pool on a disjoint development
set. Freeze template families and all candidates before measuring eligibility.
Estimate whether the current primary floor can meet category coverage without
selecting individual prompts because they pass.

Risk: a superficially larger pool can become post-hoc prompt laundering if
eligibility is used to choose the final items.

Stop condition: if a preregistered template-level sampling rule cannot meet the
coverage requirement without item-level pass selection, do not repilot this
estimand.

### Option B — Make both floors co-primary

Require a defined and directionally consistent result under both
`input_embedding_decoded` and `layer0_residual_decoded` rather than allowing one
to function only as sensitivity analysis.

Risk: this is stricter and may make the instrument unusable, but it directly
tests normalization robustness.

Stop condition: any required floor remains undefined or reverses a required
conclusion on the disjoint development design.

### Option C — Change the primary floor

Promote `layer0_residual_decoded` only if an independently justified theory of
measurement says it is the appropriate reference. The old primary result remains
undefined and cannot be reinterpreted as a pass.

Risk: choosing the floor that produced the favorable pilot result would be
outcome-driven unless the choice is justified and tested on data disjoint from
both the pilot and confirmation set.

Stop condition: the justification depends on the observed positive sensitivity
result, or the new primary floor fails independent specificity controls.

### Option D — Replace normalized target attainment

Define a denominator-free or otherwise stabilized estimand before viewing any
new scientific results. Validate it against fitted/broken and correct/wrong
controls on a disjoint development set.

Risk: this changes the scientific question and can hide rather than solve the
meaning of the weak baseline.

Stop condition: the new estimand cannot distinguish an informative map from a
geometry-matched broken map in synthetic and excluded-input controls.

### Option E — Stop this instrument path

Treat primary-floor dependence as a terminal ambiguity for this J-space use and
do not spend another pilot on it.

Risk: a repairable measurement problem may be abandoned.

Stop condition: this option is the stop condition; preserve the pilot as an
informative negative instrument-validation result.

## Disjoint development-set requirements

A mechanism-development set must be separate from all 200 currently specified
scientific prompts. In particular, it must not use the 20-prompt pilot or inspect
the 180-prompt confirmation set.

Before execution, freeze and hash:

1. prompt-generation rules and template families;
2. every candidate prompt, category, and stable ID;
3. tokenizer, model, lens, and decoding identities;
4. features to measure and their exact definitions;
5. exclusion, missingness, and category-coverage rules;
6. the analysis that compares H1 through H5;
7. sample-size justification or a statement that results are descriptive only;
8. stop conditions and the rule for choosing among Options A through E.

No candidate may be added, removed, or promoted because its measured denominator
passes. A template-level rule may be revised only on the development set and must
then be frozen before a new independently authorized pilot.

## Universal stop conditions

Stop without interpretation if any of these occurs:

- a source identity, input identity, or tokenizer/model/lens revision differs;
- the artifact or development manifest cannot be independently hash-verified;
- confirmation data are accessed;
- prompt candidates are selected after viewing eligibility or effects;
- an exclusion rule or guard is relaxed because the result is inconvenient;
- missing or excluded observations are silently dropped;
- a required category falls below its preregistered minimum;
- the two required floor constructions disagree and the protocol has no fixed
  rule for that disagreement;
- a runtime product contains a threshold, gate, or scientific decision that the
  authorized stage is not permitted to emit.

## Exact next decision

Do not authorize a revised pilot yet. First decide how to restore a lawful
mechanism-evidence path now that the transient Colab artifact is absent. A new
artifact-generating run would be a separate scientific and GPU authorization;
reconstructing or uploading the old artifact would violate the custody boundary
used for this audit unless Dr. Mani explicitly changes that boundary.

After a valid mechanism audit or disjoint development study, Dr. Mani should
choose one of Options A through E. Only then should the selected option be turned
into a complete preregistration and independently reviewed implementation.
