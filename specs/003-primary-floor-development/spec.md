# Feature Specification: Primary-Floor Development Study

**Feature Branch**: Not created; no `before_specify` branch hook is registered

**Created**: 2026-08-02

**Status**: Draft; local CPU software-instrument validation authorized; real
corpus construction and study execution not authorized

**Input**: User description: "Approved Option A: keep the primary floor and design a disjoint development study before considering any revised pilot."

## Clarifications

### Session 2026-08-04

- Q: Which completion scope should Feature 003 use? → A: Complete when the
  instrument passes synthetic CPU validation; the real digest registry, corpus,
  and study are separately authorized future work.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Validate a Lawful Manifest Instrument (Priority: P1)

As the study owner, Dr. Mani needs a local CPU instrument that can deterministically
construct, freeze, and validate a synthetic development manifest before any real
corpus construction or eligibility measurement is authorized.

**Why this priority**: The software must prove corpus separation,
pre-measurement freezing, and outcome-independent selection behavior without
accessing the sealed Stage 2b scientific set.

**Independent Test**: An auditor can build a synthetic 29-block manifest against
a synthetic, text-free 200-entry digest registry and verify deterministic
identity, zero exact or normalized overlap, complete candidate accounting,
declared template families, a template-level sampling rule, and rejection of
post-freeze or outcome-driven mutation.

**Acceptance Scenarios**:

1. **Given** a synthetic 200-entry digest registry, **When** a synthetic
   development manifest is frozen, **Then** every candidate has a stable ID,
   category, template family, source rule, and verifiable content identity, with
   no exact or normalized overlap with the registry.
2. **Given** no synthetic eligibility values have been supplied, **When** the
   manifest is frozen, **Then** every candidate and the template-level sampling
   rule are fixed before the analysis interface accepts evidence.
3. **Given** synthetic eligibility has been supplied, **When** a candidate passes
   or fails, **Then** the instrument rejects any attempt to add, remove, replace,
   or promote an individual candidate.

---

### User Story 2 - Compare the Five Live Explanations (Priority: P2)

As a measurement researcher, Dr. Mani needs the instrument to assess H1 through
H5 together on synthetic evidence so two arithmetic exclusions are not used to
declare a mechanism.

**Why this priority**: Prompt construction, tokenization, target properties,
floor geometry, and the global guard can overlap. Measuring only one explanation
would not resolve the primary-floor ambiguity.

**Independent Test**: A reviewer can inspect the frozen analysis contract and
confirm that each hypothesis has declared features, a prediction, a comparison,
and a falsifier, and that every frozen candidate is included in the accounting.

**Acceptance Scenarios**:

1. **Given** a frozen synthetic manifest and complete synthetic evidence,
   **When** the evidence is analyzed, **Then** H1 through H5 are evaluated using
   only predeclared definitions and comparisons.
2. **Given** primary and sensitivity floor measurements disagree, **When** the
   result is reported, **Then** the disagreement is retained as floor dependence
   and is not resolved by selecting the favorable floor.
3. **Given** a measurement is missing or excluded, **When** results are
   summarized, **Then** its candidate identity, floor, reason, and effect on
   coverage remain visible.

---

### User Story 3 - Make a Bounded Next-Study Decision (Priority: P3)

As the study approver, Dr. Mani needs a decision-packet instrument that accepts
synthetic evidence and supports only a bounded decision: either the proposed
Option A design is ready for independent preregistration review, or this estimand
stops before another pilot.

**Why this priority**: The development study is an instrument-design step. It
must not silently become a revised pilot, a confirmation analysis, or a
scientific pass claim.

**Independent Test**: An approver can determine from the packet whether a frozen
template-level sampling rule can meet the existing category-coverage requirement
without item-level pass selection, and can trace every decision to a predeclared
rule.

**Acceptance Scenarios**:

1. **Given** a frozen template-level sampling rule, **When** synthetic evidence
   shows it cannot meet existing coverage without item-level selection, **Then**
   the outcome is stop and no revised pilot is proposed for this estimand.
2. **Given** the rule can meet coverage without item-level selection, **When** a
   synthetic packet is complete, **Then** the only positive outcome is readiness
   for independent preregistration review, not authorization to run.
3. **Given** any universal stop condition occurs, **When** the study is assessed,
   **Then** interpretation stops and the failure is reported without relaxing a
   guard, identity, or coverage rule.

### Edge Cases

- A synthetic candidate duplicates an entry in the supplied synthetic digest
  registry under a different ID or harmless formatting variation. It is rejected
  before the manifest is frozen, and the collision is recorded.
- A candidate's tokenization or model-selected target is undefined, nonfinite,
  or inconsistent with the frozen identities. The candidate remains accounted
  for as missing or excluded under the predeclared rule.
- One template family supplies fewer valid candidates than planned. The family
  is not backfilled after eligibility is known; the frozen coverage and stop
  rules decide the outcome.
- The primary-floor denominator is near the global guard while the sensitivity
  floor is adequate. Both values and the floor difference remain visible.
- Template-level revisions appear promising only after development results are
  viewed. They may define a later frozen design, but cannot retroactively change
  this study or promote individual candidates.
- A source, model, tokenizer, lens, decoding, prompt, or analysis identity cannot
  be verified. The study stops before interpretation.
- Any process exposes a pilot prompt, confirmation prompt, or confirmation
  result. The study stops and records contamination.
- A runtime reset removes an artifact. The artifact is not reconstructed from
  partial evidence and the missing custody chain is reported.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The instrument MUST retain `input_embedding_decoded` as the primary
  floor and `layer0_residual_decoded` as the sensitivity floor. It MUST NOT
  promote the favorable floor based on the completed pilot or development
  results.
- **FR-002**: The instrument MUST accept an externally supplied, digest-only
  exclusion registry and reject exact or normalization-equivalent candidate
  overlap. Feature 003 validation MUST use a clearly synthetic, text-free
  200-entry registry and MUST NOT materialize the real scientific registry.
- **FR-003**: The instrument MUST freeze and independently verify generation
  rules, arithmetic template families, every candidate, stable IDs, categories,
  and the template-level sampling rule before its analysis interface accepts any
  synthetic evidence.
- **FR-004**: The instrument MUST validate that the candidate pool is balanced
  according to categories and template families declared before evidence input.
  The plan MUST justify the candidate count before implementation or mark the
  synthetic validation descriptive only.
- **FR-005**: The instrument MUST reject any attempt to add, remove, replace, or
  promote a candidate because of its denominator, eligibility, floor difference,
  or effect.
- **FR-006**: The instrument MUST retain the existing primary-floor estimand,
  fifth-percentile guard derivation rule, exclusion policy, missingness policy,
  and category-coverage requirement without outcome-driven relaxation.
- **FR-007**: Before accepting evidence, the instrument MUST require externally
  supplied model, tokenizer, lens, decoding, prompt-corpus, feature, analysis,
  and source identities needed to reproduce and audit every result.
- **FR-008**: The synthetic analysis MUST compare all five live explanations:
  prompt construction (H1), tokenization (H2), target properties (H3), floor
  geometry (H4), and global guard interaction (H5).
- **FR-009**: Each hypothesis MUST have predeclared features, an exact prediction,
  a comparison that accounts for the other declared explanations, and a
  falsifier. No two-prompt association MAY be treated as a mechanism finding.
- **FR-010**: Every synthetic candidate MUST remain in the result accounting with its
  identity, floor-specific denominator status, eligibility status, exclusion or
  missingness reason, template family, category, and declared features.
- **FR-011**: The study MUST report primary and sensitivity floor results
  together, including disagreement, and MUST NOT describe a floor-dependent
  result as robust.
- **FR-012**: Before accepting evidence, the instrument MUST freeze a decision rule that
  determines whether a template-level sampling rule can satisfy the existing
  category-coverage requirement without selecting individual passing prompts.
- **FR-013**: If synthetic evidence shows that no frozen template-level sampling
  rule can meet coverage without item-level pass selection, the instrument MUST
  return `stop_estimand_before_revised_pilot`.
- **FR-014**: The development output MUST be limited to synthetic mechanism
  records, design diagnostics, and a stop-or-review recommendation. It MUST NOT
  emit a Stage 2b pilot pass, confirmation result, threshold, scientific gate,
  or claim above evidence class 1.
- **FR-015**: The real 200-prompt Stage 2b set MUST remain sealed throughout this
  feature. Feature 003 MUST NOT read scientific prompt text, materialize the real
  digest registry or development corpus, reconstruct an artifact, or use the
  missing pilot artifact.
- **FR-016**: Materializing the real digest registry, constructing a real
  development corpus, any data-generating or model run, GPU use, revised pilot,
  confirmation access, artifact transfer, or execution outside local synthetic
  validation MUST require separate explicit authorization after independent
  review.
- **FR-017**: The instrument MUST stop without interpretation on an identity mismatch,
  unverifiable manifest, scientific-set access, outcome-driven candidate
  selection, relaxed guard, silently dropped observation, coverage failure,
  unresolved floor disagreement, or unauthorized decision product.

### Key Entities

- **Synthetic development candidate**: A test prompt identified by stable ID,
  category, template family, frozen content identity, and declared features. It
  exercises exclusion logic without reproducing scientific prompt text.
- **Template family**: A preregistered arithmetic prompt-construction rule used
  for balanced generation and template-level sampling, never for post-measurement
  item selection.
- **Synthetic development manifest**: The complete frozen test inventory of
  rules, candidates, identities, features, exclusions, coverage rules, analysis
  rules, and stop conditions.
- **Synthetic floor measurement**: Test evidence for the retained primary floor
  and sensitivity floor, including denominator status and explicit disagreement.
- **Hypothesis record**: The prediction, features, comparison, falsifier, and
  result for one of H1 through H5.
- **Synthetic decision packet**: The auditable test output that recommends either
  independent preregistration review of the proposed Option A design or stopping
  this estimand before another pilot. It is not study evidence or authorization.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Synthetic tests demonstrate zero exact and normalization-equivalent
  overlap between a frozen 580-candidate manifest and a synthetic, text-free
  200-entry digest registry, including positive collision controls.
- **SC-002**: One hundred percent of synthetic candidates, generation rules,
  template families, and sampling rules have verifiable identities fixed before
  the analysis interface accepts evidence.
- **SC-003**: One hundred percent of frozen synthetic candidates appear in the
  final accounting, including every excluded or missing candidate and its reason.
- **SC-004**: All five hypotheses have a frozen prediction, declared feature
  set, comparison, falsifier, and reported result or explicit undefined status.
- **SC-005**: The audit finds zero item-level additions, removals, replacements,
  or promotions made after eligibility or effect measurements are available.
- **SC-006**: Every valid synthetic decision packet resolves to exactly one permitted outcome:
  ready for independent preregistration review under Option A, or stop this
  estimand before a revised pilot.
- **SC-007**: The packet contains zero pilot pass claims, confirmation results,
  newly selected thresholds, scientific gates, or claims above evidence class 1.
- **SC-008**: No real digest registry, real development corpus, model or GPU run,
  revised pilot, confirmation access, artifact transfer, or missing-artifact
  reconstruction occurs under Feature 003 authorization.

## Assumptions

- The completed Stage 2b pilot remains an undefined primary-floor result with a
  positive sensitivity-floor effect; this feature does not reinterpret it.
- The current 200 Stage 2b prompt identities remain the authoritative sealed
  exclusion set for development-corpus construction.
- Option A retains the existing scientific estimand and measurement rules. A
  different primary claim or floor belongs in a separate specification.
- Candidate count, template-family count, and the quantitative decision rule are
  planning outputs that must be justified, frozen, and independently reviewed
  before any execution authorization.
- Feature 003 completes when the software instrument passes local CPU validation
  with synthetic data. A real digest registry, real corpus, and development study
  require separately authorized future work.
- Development evidence may support template-level redesign only. Any resulting
  design must be frozen before a separately authorized, independent pilot and
  cannot reuse individual development candidates as scientific prompts.
- Loss of the transient Colab artifact does not authorize reconstruction,
  transfer, or a replacement GPU run.
