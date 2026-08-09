# Feature Specification: Ancestry Recovery Evaluation

**Feature Branch**: `[004-ancestry-recovery-eval]`

**Created**: 2026-08-07

**Status**: Draft

**Input**: User description: "Approve creation, but not execution, of an Archimedes Spec Kit for AR-01 that freezes a synthetic-only ancestry corpus, exact byte manifests, the five-way ancestry ontology, adversarial decoys, and independent acceptance gates."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Freeze a reviewable ancestry study (Priority: P1)

As Dr. Mani, I need a complete, bounded specification for AR-01 so I can decide whether its corpus, meanings, controls, evidence limits, and human gates are suitable for independent preregistration review without authorizing execution.

**Why this priority**: An ancestry experiment cannot produce interpretable evidence until its question, inputs, classifications, controls, and stop conditions are frozen independently of its results.

**Independent Test**: A reviewer can inspect the specification packet and account for every corpus item, relationship type, condition, outcome, failure criterion, stop condition, and approval gate without running an agent or accessing private memory.

**Acceptance Scenarios**:

1. **Given** the approved reconstruction review packet, **When** the AR-01 specification is assembled, **Then** it defines a synthetic-only corpus, exact-byte identity, atomic claim schema, five ancestry relationship types, controls, outcomes, leakage protections, and human-only gates.
2. **Given** that execution has not been authorized, **When** the packet reaches its terminal design state, **Then** its strongest positive status is "ready for independent preregistration review," never "ready to run."
3. **Given** a historical account from Dr. Mani, **When** it enters the corpus, **Then** it is labeled first-person historical provenance and is not treated as implementation proof.

---

### User Story 2 - Prevent self-confirmed ancestry (Priority: P2)

As an independent validator, I need recovery claims separated from validation and acceptance so a system cannot promote its own names, narratives, or reports into accepted ancestry.

**Why this priority**: The initiating audit found a concrete case where nine named components were reported as one executable loop even though primary-source tracing showed disconnected, mock-backed, broken, or unreachable surfaces.

**Independent Test**: On a frozen set of adversarial decoys, the validator must reject name-only relationships, disabled or unreachable features, mock-backed success, and unsupported direct-inheritance claims before any claim can enter the accepted ledger.

**Acceptance Scenarios**:

1. **Given** a recovery claim, **When** an independent validator reviews it, **Then** the validator cannot see the recovery agent's confidence, rationale, or proposed classification before recording an independent finding.
2. **Given** a component with a plausible name but no caller, **When** it is classified as implemented and reachable, **Then** the disablement or caller-removal counterexample fails the claim.
3. **Given** disagreement between independent source reviewers, **When** adjudication cannot resolve it, **Then** the claim remains `UNKNOWN` and cannot be counted as verified ancestry.

---

### User Story 3 - Preserve a complete evidence record (Priority: P3)

As Archimedes, I need every declaration, trial, exclusion, retry, failure, and decision retained under one frozen evidence identity so later review cannot select only favorable ancestry claims.

**Why this priority**: Same-snapshot evidence and complete history are required to distinguish recovery performance from post-hoc narrative repair.

**Independent Test**: A reviewer can start from the manifest and reconcile all declared inputs to their consumers, every trial to one terminal state, and every accepted claim to independent evidence without an orphan declaration or missing attempt.

**Acceptance Scenarios**:

1. **Given** any declared threshold, condition, corpus item, or scorer, **When** the evidence packet is validated, **Then** it has an identified consumer and no consumer reads an undeclared value.
2. **Given** a stopped, failed, retried, excluded, or unparseable trial, **When** history is reconciled, **Then** the trial remains present with its terminal reason.
3. **Given** any content-identity mismatch or unallowlisted access, **When** preflight detects it, **Then** work stops without repair, substitution, or partial evidence output.

### Edge Cases

- Two components share the same or mythologically related name but have no verified code relationship.
- A document correctly describes intended behavior while the implementation is unreachable, disabled, mocked, or broken.
- A component has a real implementation and meaningful tests but no current runtime result.
- A repository is dirty, so a commit identifier does not identify the bytes reviewed.
- An artifact exists only in a Git object or stash rather than the working tree.
- A named report is absent from every allowlisted root and Git-object search.
- Recovery and validation disagree because the underlying evidence is genuinely incomplete.
- A judge returns malformed output or fails calibration against frozen human labels.
- A corpus item contains or points toward private product-user memory.
- A feature changes a prompt but does not change behavior, or changes behavior without improving the preregistered outcome.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: AR-01 MUST remain a specification and independent-review feature until Dr. Mani separately authorizes execution.
- **FR-002**: The feature MUST define exactly five ancestry relationship types: conceptual lineage, direct code inheritance, third-party substrate ancestry, shared design motif, and name-only similarity.
- **FR-003**: Name-only similarity MUST never satisfy conceptual lineage, direct code inheritance, third-party substrate ancestry, or shared design motif.
- **FR-004**: The corpus MUST contain synthetic or repository-derived research evidence only and MUST exclude private product-user memory.
- **FR-005**: Every allowlisted corpus item MUST have an exact byte identity, source location, evidence category, and inclusion reason.
- **FR-006**: Dirty repositories MUST be identified by exact file bytes and a recorded status-enumeration mode; a commit identifier alone MUST NOT represent a dirty snapshot.
- **FR-007**: Historical accounts, agent reports, implementation source, tests, and runtime artifacts MUST remain distinct evidence categories.
- **FR-008**: Dr. Mani's first-person account MUST be eligible to establish historical meaning and priorities but MUST NOT establish implementation, reachability, test quality, or runtime behavior.
- **FR-009**: Existing Claude, AGY, Codex, Daedalus, Archimedes, and other agent reports MUST be treated as claim sources requiring primary-source validation.
- **FR-010**: Recovery output MUST consist of atomic claims with a stable claim identifier, ancestor, descendant, component, relationship type, implementation classification, qualifier flags, evidence references, and confidence.
- **FR-011**: Implementation classification MUST support overlapping evidence flags for implemented and reachable, implemented but unreachable, meaningfully tested, permissively or misleadingly tested, scaffolded, mock-backed, broken, historically described only, and unknown.
- **FR-012**: The treatment condition MUST receive the frozen source, test, documentation, and historical-provenance corpus allowed by its condition.
- **FR-013**: A documentation-only control, a source-without-history control, an adversarial-decoy control, and a self-validation control MUST be defined before the study can be reviewed as complete.
- **FR-014**: Recovery and independent validation MUST occur in separate contexts with no shared hidden memory.
- **FR-015**: The independent validator MUST record its source finding before seeing the recovery agent's confidence, rationale, or proposed classification.
- **FR-016**: Ground truth MUST be produced by two independent source reviewers, with disagreements sent to a third reviewer and unresolved claims retained as `UNKNOWN`.
- **FR-017**: `UNKNOWN` claims MUST remain in the complete history but MUST NOT enter accuracy denominators or the accepted ancestry ledger.
- **FR-018**: The feature MUST include adversarial counterexamples for name collisions, missing callers, disabled features, mock branches, broken persistence, narrative-only claims, and plausible but false direct inheritance.
- **FR-019**: A reachability claim MUST fail when its claimed caller is removed or the feature is disabled and the measured endpoint remains unchanged.
- **FR-020**: The primary outcomes MUST include ancestry-classification accuracy, invented-ancestry rate, and independent-validation catch rate.
- **FR-021**: Secondary outcomes MUST include evidence-reference precision, confidence calibration, valid-claim rejection rate, and review cost per accepted claim.
- **FR-022**: Numerical acceptance thresholds MUST be derived from a preregistered synthetic-decoy pilot and frozen before held-out ancestry scoring; this feature MUST NOT invent thresholds in advance of that pilot.
- **FR-023**: Every declared input, condition, threshold, scorer, and stop rule MUST have an identified consumer, and every consumer MUST read only declared values.
- **FR-024**: The evidence record MUST retain every trial, retry, exclusion, malformed judgment, failure, and stop reason without deletion or favorable selection.
- **FR-025**: The feature MUST stop without repair or substitution on content-identity mismatch, unallowlisted access, hidden-memory retrieval, role collision, missing trial history, scorer drift, judge-calibration failure, private-data exposure, or post-freeze changes.
- **FR-026**: The privacy boundary MUST deny all data and memory sources not explicitly allowlisted and MUST log every attempted access without recording secret or private values.
- **FR-027**: Canary evidence MUST detect contamination between recovery, control, validation, and historical-provenance conditions.
- **FR-028**: Accepted claims MUST pass an immutable transition requiring independent validation; recovery agents MUST NOT self-accept claims.
- **FR-029**: AR-01 outputs MUST be limited to evidence class 1 statements about ancestry-recovery and governance performance.
- **FR-030**: AR-01 MUST NOT produce claims of consciousness, phenomenal status, cognition, beneficial learning, or reconstruction superiority.
- **FR-031**: The feature MUST distinguish storage, retrieval, prompt replay, behavior change, and measurable improvement as separate evidence endpoints.
- **FR-032**: The evidence packet MUST identify missing source artifacts explicitly and MUST NOT reconstruct their contents from summaries.
- **FR-033**: The terminal design decision MUST be either "ready for independent preregistration review" or "stop and revise the estimand," with neither outcome authorizing execution.
- **FR-034**: Dr. Mani MUST retain sole approval over historical meaning, pilot-derived thresholds, provider or model spend, execution, publication, artifact transfer, and any change to the research framework's meaning.
- **FR-035**: The specification MUST preserve the existing Dionysus Hermes profile contract unchanged.
- **FR-036**: The specification MUST identify the frozen early seed and any later reconstruction as separate future evaluation subjects; AR-01 itself MUST NOT claim that either outperforms the other.

### Key Entities

- **Corpus Item**: One allowlisted source, test, document, runtime artifact, or historical-provenance item with exact identity and inclusion metadata.
- **Ancestry Claim**: One atomic assertion connecting an ancestor, descendant, component, relationship type, classification, qualifiers, evidence, and confidence.
- **Relationship Type**: One of the five frozen ancestry meanings used to prevent conceptual, code, substrate, motif, and name similarity from being conflated.
- **Implementation Classification**: The primary class and overlapping evidence flags assigned from code, caller, test, and runtime review.
- **Recovery Condition**: The frozen evidence exposure and instructions used to produce ancestry claims.
- **Independent Finding**: A validator's source-first classification recorded without access to recovery rationale or confidence.
- **Ground-Truth Decision**: The reconciled result of two source reviews, third-reviewer adjudication, or terminal `UNKNOWN`.
- **Trial Record**: The immutable record of one condition, claim, result, judgment, retry, exclusion, or stop.
- **Acceptance Decision**: The independent, human-governed transition that may admit a claim to the accepted ancestry ledger.
- **Stop Record**: The terminal evidence explaining why no repair, substitution, or partial promotion occurred.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Independent reviewers can account for 100% of allowlisted corpus items by exact identity, evidence category, and inclusion reason before any execution decision.
- **SC-002**: Every proposed ancestry claim can be represented as one atomic claim using exactly one relationship type and an explicit implementation classification with zero name-only promotions.
- **SC-003**: All four required control conditions and every adversarial-decoy family have frozen acceptance and rejection expectations before independent preregistration review.
- **SC-004**: Two independent reviewers can reproduce the ground-truth workflow, and 100% of unresolved disagreements terminate as `UNKNOWN` rather than forced agreement.
- **SC-005**: Every declared input and rule has a consumer, every consumer reads only declared values, and the reconciliation reports zero orphan declarations or undeclared reads.
- **SC-006**: The complete-history check accounts for 100% of trials, retries, exclusions, malformed judgments, failures, and stop records.
- **SC-007**: All feature-disablement, caller-removal, mock-branch, name-collision, and narrative-only counterexamples fail when their targeted evidence claim is falsely enabled.
- **SC-008**: Privacy review finds zero private product-user memory items in the corpus and zero permitted data sources outside the explicit allowlist.
- **SC-009**: Evidence review finds zero outputs above evidence class 1 and zero claims of consciousness, phenomenal status, beneficial learning, or reconstruction superiority.
- **SC-010**: The design reaches exactly one permitted terminal state, "ready for independent preregistration review" or "stop and revise the estimand," without executing AR-01.
- **SC-011**: An independent adversarial reviewer reports no unresolved blocker in the specification's scope, evidence separation, controls, leakage protections, stop rules, or human gates.
- **SC-012**: Dr. Mani can approve or decline the next phase from one decision packet without needing hidden conversation history or private memory.

## Assumptions

- AR-01 evaluates ancestry-recovery and independent-governance accuracy, not the functional quality of reconstructed components.
- The initial corpus is limited to the four already authorized roots and explicitly selected Git objects; adding another repository requires a new scope decision.
- Repository source and test files may be dirty. Exact-byte manifests, not commit identifiers alone, define the future frozen snapshot.
- Synthetic decoys are sufficient to derive preliminary thresholds without exposing held-out ancestry outcomes.
- Human reviewers can remain operationally separate from recovery agents and from each other until adjudication.
- No model, service, database, GPU, provider endpoint, or private memory store is needed to complete specification and independent preregistration review.
- Existing historical reports remain useful claim generators but never serve as ground truth.
- Any later comparison between a reconstructed component and its frozen seed will require a separate preregistration with equal resources and a held-out task corpus.

