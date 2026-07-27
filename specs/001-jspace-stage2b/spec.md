# Feature Specification: Stage 2b J-space discrimination

**Feature Branch**: `001-jspace-stage2b`

**Created**: 2026-07-26

**Status**: Draft — awaiting ratification of 10 open parameters

**Input**: Stage 2b J-space discrimination: target-relative endpoint and factorial controls

Full design: `sakshi notes/STAGE2B_DESIGN.md` (on branch
`docs/jspace-research-operations`, PR #2).
Open parameters: `sakshi notes/STAGE2B_OPEN_PARAMETERS.md`.
Current lab state: `sakshi notes/HANDOFF_2026-07-26.md`.

## Where we are

The J-space lab is trying to establish that Anthropic's Jacobian Lens is a real
measurement instrument, before anything downstream (Elume consuming
observations, Sakshi auditing lineage) is built on it.

- **Stage 1** proved self-consistency only — the same readout twice, max logit
  difference 0.0. That is reproducibility, not information.
- **Stage 2** executed 2026-07-24 on a Colab T4 (run
  `f9234a9c-6a2d-43da-9fbd-bf26b19ac18c`, n=50). Median Jacobian-vs-logit-lens
  top-10 Jaccard 0.194; specificity cleared the random-vector control (1.00) but
  failed both structure-broken controls (shuffled-layer 0.22, mismatched-probe
  0.40, against a 0.80 bar). **Decision: ambiguity.** No promotion.
- **2026-07-25** the completed study was processed through the real EvoScientist
  engine, which agreed with ambiguity and audited the notebook against its own
  preregistration. It found the implemented added-information gate omitted the
  preregistered output and prompt-only clause; declared inference seed `[1]` was
  never executed; and specificity used one random-vector seed of three computed.
- **2026-07-26** those findings were verified against the executed notebook and
  the record was amended (PR #2). The recorded decision remains ambiguity.

The open scientific question is unchanged and now sharper: **the readout is not
identical to a cheap baseline and not noise, but nothing yet separates it from
what any layer-sized Jacobian transport would produce.**

## Why Stage 2 could not have answered it

Two structural defects, not statistical ones. Neither would have been fixed by a
larger n.

1. **The endpoint had no ground truth.** The primary metric measured how much two
   readouts *differ*. A difference metric cannot distinguish an informative
   disagreement from an arbitrary one, so the strongest possible conclusion was
   always non-identity.
2. **The controls confounded two factors.** Shuffled-layer changes both the map
   and the layer; mismatched-probe changes the probe and the layer. When both
   fail, which factor caused it is unrecoverable.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Establish whether the specific fit matters (Priority: P1)

Dr. Mani needs to know whether the *correctly fitted map at the correct layer*
recovers more about the model's own next-token target than a same-layer map with
the fit destroyed but geometry preserved.

**Why this priority**: this is the question Stage 2 failed to answer, and every
downstream decision about the instrument depends on it.

**Independent Test**: runnable and interpretable alone — the specificity
comparison is a paired difference at matched prompt and layer, and yields a
verdict without any other story.

**Acceptance Scenarios**:

1. **Given** a held-out prompt manifest disjoint from Stage 2, **When** the
   fitted Jacobian and a same-layer fit-broken map are each applied to the same
   correct activation, **Then** the prompt-clustered median paired difference in
   normalized target attainment is reported with a bootstrap interval.
2. **Given** that interval, **When** the median paired difference exceeds
   `SPEC_MIN_EFFECT` **and** the interval excludes zero, **Then** H1 passes; when
   either clause fails, H1 fails. Either outcome is a valid result. Both clauses
   are evaluated per layer, and H1 passes only if they hold at every layer.

### User Story 2 - Establish non-redundancy with teeth (Priority: P2)

Show the Jacobian readout is not a re-encoding of the logit lens in a way that
shows up *on the target*, not merely in token overlap.

**Why this priority**: Stage 2's version of this passed while remaining
compatible with the readout being different and useless. It needs to survive
contact with a ground truth before it means anything.

**Independent Test**: the Jaccard statistic and the target-relative paired
difference are both computable from the same run without the specificity arm.

**Acceptance Scenarios**:

1. **Given** matched readouts, **When** median top-10 Jaccard is at most
   `NONREDUNDANCY_MAX_JACCARD` **and** the interval on the target-relative paired
   difference excludes zero, **Then** H2 passes.
2. **Given** low overlap but a target-relative difference whose interval includes
   zero, **Then** H2 fails — the readouts differ without differing usefully.

### User Story 3 - Make the recorded failure modes unrepeatable (Priority: P3)

Every defect this project has hit should fail at preflight rather than during or
after a run.

**Why this priority**: cheap and mechanical, but it protects the other two
stories from being wasted. Lower priority only because it produces no scientific
result by itself.

**Independent Test**: the preflight can be exercised against a deliberately
broken configuration with no GPU and no measurement.

**Acceptance Scenarios**:

1. **Given** a declared constant with no consuming gate, **When** preflight runs,
   **Then** it fails and names the orphaned constant.
2. **Given** a residual in the wrong dtype or on the wrong device, or a decode
   parity mismatch, **When** preflight runs, **Then** it fails before any
   measurement begins.
3. **Given** a stimulus manifest overlapping Stage 2's, **When** preflight runs,
   **Then** it fails on the digest check.

### Edge Cases

- `s(output) − s(prompt_only)` at or near zero makes the normalization
  meaningless. Cells below `NTA_MIN_DENOMINATOR` are excluded and the exclusion
  count is reported per layer, never silently dropped.
- Late layers score well trivially, since the residual is close to the output.
  All comparisons are within-layer; depth-pooled figures are descriptive only and
  never gate inputs.
- The Stage 1 anchor stays outside the analysis sample — it is the one prompt
  every prior stage has seen, and including it would contaminate held-out status.
- Rank computation must not change the statistic when optimized (FR-010).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Endpoint MUST be normalized target attainment — a rank statistic
  for the target token, normalized between the prompt-only floor and the output
  ceiling — replacing Stage 2's readout-difference metric.
- **FR-002**: The output and prompt-only baselines MUST be structural to the
  endpoint rather than a separate gate, so the Stage 2 omission is
  unrepresentable.
- **FR-003**: Controls MUST be a 2×2 crossing correct/wrong activation with
  correct/fit-broken map, enabling main effects and the interaction.
- **FR-004**: The fit-broken map MUST preserve singular value spectrum, operator
  norm, and conditioning while destroying correspondence (default: Haar random
  orthogonal rotation of the left singular basis).
- **FR-005**: The wrong activation MUST be a real norm-matched residual from a
  different prompt, not a random vector.
- **FR-006**: The sampling unit MUST be the prompt, with layers as repeated
  measures and a cluster bootstrap resampling whole prompts.
- **FR-007**: Specificity and non-redundancy MUST have separate statistics and
  thresholds; no shared coupled margin.
- **FR-008**: Wrong-layer controls MUST be balanced across preregistered layer
  distances and reported per band.
- **FR-009**: Preflight MUST assert tensor contracts (shape, dtype, device,
  decode parity) and constant consumption, and MUST abort before measurement.
- **FR-010**: Target rank MUST be computed directly rather than by
  full-vocabulary argsort, and the optimization MUST be verified against the old
  path on a fixed probe so it cannot silently change the statistic.
- **FR-011**: Stimuli MUST be new and disjoint from Stage 2, asserted by digest.
- **FR-012**: The aggregate artifact MUST record, per gate: constant name,
  declared value, observed statistic, interval, cluster count, exclusions with
  reasons, and outcome — sufficient to recompute every decision without the
  notebook.
- **FR-013**: Execution MUST refuse to run until `THRESHOLDS_RATIFIED` is set by
  Dr. Mani.

### Key Entities

- **Stimulus manifest** (`jspace-stage2b-stimulus/v1`) — held-out prompts,
  digest-verified disjoint from Stage 2; raw text in-repo, artifacts digest-only.
- **Readout** — a token ranking in the model's vocabulary basis, from one of:
  fitted Jacobian, logit lens, fit-broken map, wrong-layer map, random vector,
  prompt-only, output.
- **Observation artifact** — content-addressed per-prompt and aggregate records
  carrying measurements, gate reporting, and pinned identities.
- **Gate** — a named decision with a declared constant, observed statistic,
  interval, and outcome.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A decision of pass, ambiguity, or fail is produced under a
  preregistration locked before data collection and demonstrably implemented —
  every declared constant consumed by the gate that names it.
- **SC-002**: The specificity question is *answered* rather than left
  under-resolved: the bootstrap interval either excludes zero or is tight enough
  to say the effect is smaller than `SPEC_MIN_EFFECT`.
- **SC-003**: Every decision in the report is recomputable from the artifacts
  alone, without reading the notebook. Stage 2's was not.
- **SC-004**: No runtime defect surfaces after measurement begins; dtype, device,
  parity, and manifest-disjointness failures all occur at preflight.
- **SC-005**: The reported claim matches what was tested — no condition described
  as passing on a clause that was not evaluated.

## Assumptions

- Observation only. The wrong-activation and broken-map cells are readout
  manipulations computed offline from captured residuals; nothing is fed back
  into the model and no forward pass is altered. This is not Stage 3.
- The Stage 2 run is treated as **pilot data**. Its stimuli informed this design,
  so reusing them would test the design against the data that shaped it.
- Stage 2's per-prompt artifacts were never transferred off the ephemeral Colab
  runtime and cannot be recovered. Nothing here depends on them.
- Loci stay at layers 6, 13, 20, 26 at position -2, so the Stage 1 anchor
  reproduction remains a valid kill check.
- Single T4 runtime class; no cross-runtime reproducibility claim.
- A pass authorizes writing a Stage 3 proposal and nothing more — not
  publication, not artifact transfer, not Sakshi/Elume integration.

## Open parameters (blocking execution)

Ten questions in `sakshi notes/STAGE2B_OPEN_PARAMETERS.md`. Three are flagged as
not delegable:

- **Q3 — what counts as the target.** Defines what this study means by
  "information". The proposed default (the model's own argmax) makes the endpoint
  measure how far a mid-layer readout has travelled toward the model's own
  conclusion — coherent, but *not* "information about the world", and a pass must
  not be described as though it were.
- **Q5 — the specificity threshold.** The recommendation is deliberately **not**
  to set it now. Stage 2 set its margin without a pilot and then could not say
  whether the controls were inseparable or merely under-resolved at that value.
  Derive it from a preregistered pilot instead (Q6).
- **Q10 — execution authorization.** Dr. Mani's by definition.

## Dependencies

PRs #5 and #6 (runtime fixes) are unrelated to this feature and need not merge
first.

**PR #2 is an ordering constraint on part of the work.** `sakshi notes/` and the
`jspace-research-operations` skill are tracked on `docs/jspace-research-operations`,
not on `main`, so the notebook and the stimulus manifest cannot land until that
branch merges or the work branches from it. The preflight, endpoint, and manifest
modules and all their tests carry no such constraint.
