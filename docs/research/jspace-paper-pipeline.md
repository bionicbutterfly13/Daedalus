# EvoScientist Hypothesis and Paper Pipeline

Updated: 2026-07-31

The pipeline is designed to keep EvoScientist productive without turning prose
generation into evidence generation. It may propose, organize, calculate,
draft, and challenge. It may not promote a hypothesis because it sounds
coherent, because a test process exited successfully, or because a model wrote
a persuasive discussion.

## The loop

```mermaid
flowchart LR
    S[Sources and code] --> C[Curiosity queue]
    C --> H[Hypothesis packet]
    H --> A[Adversarial review]
    A --> X[Executable specification]
    X --> R[Authorized run]
    R --> V[Independent recomputation]
    V --> P[Paper draft]
    P --> A
```

Every arrow produces a durable artifact. No hidden chat state is part of the
scientific record.

## Evidence gates

| Gate | Minimum evidence | Permitted wording |
|---|---|---|
| E0: Idea | Source links and ownership notes | "We speculate..." |
| E1: Implemented | Inspected code and tests present | "The code implements..." |
| E2: Locally validated | Fresh unit/synthetic tests | "The local suite passed..." |
| E3: Integration validated | Excluded-input real runtime smoke | "The pinned runtime completed..." |
| E4: Pilot observed | Authorized pilot evaluated under its preregistered rules, including undefined outcomes | "In the pilot..." |
| E5: Confirmed | Publicly specified but runtime-sealed confirmation, authorized execution, and independent recomputation | "The confirmatory result..." |

E0–E5 describe publication-workflow maturity. They do not replace the governing
scientific evidence classes: a Stage 2b pilot at workflow stage E4 remains
observation-only scientific evidence class 1.

An E2 result cannot be written as an E4 result. An E3 smoke can establish API,
runtime, and memory compatibility; it cannot establish a scientific effect.

## Hypothesis packet

Each candidate must contain:

```yaml
hypothesis_id: H-JS-...
title: concise discriminating claim
status: proposed
source_basis:
  - APA reference or repository path with commit
ownership:
  external_foundation: []
  local_implementation: []
claim: ...
null: ...
alternative_explanations: []
intervention: ...
controls: []
outcomes: []
exclusions: []
falsification: ...
required_inputs: []
required_code_hashes: []
compute_bound: ...
analysis_status: unratified
execution_status: unauthorized
```

The `ownership` block is mandatory. It prevents an integration from being
reported as an invention and prevents a theoretical inspiration from being
mistaken for a tested implementation.

## Curiosity policy

EvoScientist should rank, not feel. The phrase "what the system is drawn to"
means a recorded selection function applied to the ledger.

A candidate priority score may combine:

- expected discrimination among live hypotheses;
- uncertainty that can actually be reduced by an available experiment;
- coverage of neglected concepts or failure modes;
- feasibility under current compute and authorization;
- provenance completeness;
- risk of producing a false positive or an unreviewable artifact.

The score and each component must be stored. The selector cannot use hidden
preferences, paper-ready language, or expected publicity. Random and simple
baseline policies must remain available so curiosity can be tested rather than
assumed useful.

## Paper queue

### P-JS-METHODS-001: Can the Jacobian Lens survive input-specific controls?

**Type:** instrument-validation methods and results.

**Dependency:** Stage 2b pilot and confirmation. An E4 pilot results section may
now report the positive sensitivity-floor signal and undefined primary-floor
result. It must not present an instrument pass or confirmed result before a
qualifying confirmation.

**Core contribution if supported:** the dual-floor, wrong-activation,
geometry-preserving broken-map, and fully crossed donor-by-map design.

**Current evidence:** publication-workflow E4, pilot observed, and scientific
evidence class 1. Operational execution succeeded, but
the primary floor failed category coverage, threshold derivation was unavailable,
and no pilot decision was emitted. Confirmation remains blocked.

### P-JS-TS-002: Thoughtseed competition meets measured J-space content

**Type:** computational experiment.

**Dependency:** H-JS-TS-001 and a successful Stage 2b instrument gate.

**Core question:** does J-space information improve prediction or control of
Thoughtseed selection beyond the existing competition state?

### P-JS-CUR-003: Curiosity policies for mechanistic experiment selection

**Type:** benchmark and methods paper.

**Dependency:** H-JS-CUR-003. A synthetic benchmark can proceed before the
J-space pilot because ground truth can be constructed without model claims.

**Core question:** which selection policy resolves competing mechanistic
hypotheses with the least compute and fewest false discoveries?

### P-JS-REL-004: Beyond a bag of verbalizable concepts

**Type:** mechanistic extension.

**Dependency:** H-JS-REL-005, relation-sensitive tasks, and validated
interventions.

**Core question:** can role and relation structure explain behavior that
single-token J-space coordinates cannot?

### P-JS-MEM-005: Prediction-correction memory and workspace transitions

**Type:** integration study.

**Dependency:** H-JS-NEM-004, explicit third-party attribution, complete failure
logging, and a clean temporal alignment contract.

## Drafting rules

Each draft carries a front-matter block:

```yaml
publication_stage: E0
results_available: false
scientific_execution_authorized: false
primary_artifact_sha256: null
independent_recomputation: false
```

The abstract must use the language allowed by that gate. A literature-driven
draft at E0 can describe a question and method. It cannot contain simulated
numbers in a results-shaped paragraph unless those numbers are visibly labeled
as a worked example and excluded from all conclusions.

References use APA 7 style and link to primary sources when available. Every
external algorithm, mathematical foundation, dataset, and codebase retains its
original attribution and license. Repository paths are cited with a commit hash
or immutable artifact hash when a claim depends on code.

## Independent review

Claude Opus or another independent model can be used effectively for:

- adversarial review of falsifiability and confounds;
- a primary-source bibliography and citation audit;
- an IP, license, and terminology audit;
- alternative paper structures and hostile-reader review.

The reviewer should not edit the active implementation branch. It returns an
evidence packet; Codex reconciles every accepted point against live source and
the specification.

## Stop conditions

EvoScientist stops and records the blocker when:

- an input or code identity differs from its authorization;
- a required dependency is absent or incompatible;
- a source cannot be verified;
- a result depends on an unratified analysis choice;
- a validator cannot independently reconstruct the reported statistic;
- a term such as "consciousness," "dream," "self," or "ignition" outruns the
  operational measurement.
