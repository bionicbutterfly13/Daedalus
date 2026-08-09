# Contract: Development Decision Packet

Schema: `jspace-primary-floor-development-decision/v1`

The packet answers one question: may the current generator version proceed to
independent preregistration review, or must it stop before a revised pilot?

It is not a pilot decision, scientific pass, threshold lock, execution
authorization, or confirmation result.

## Exact envelope

```jsonc
{
  "schema": "jspace-primary-floor-development-decision/v1",
  "study_id": "jspace-primary-floor-development-v1",
  "generator_version": "v1",
  "created_at_utc": "<RFC3339 UTC>",
  "packet_sha256": "<canonical digest>",
  "manifest_sha256": "<independently validated manifest>",
  "evidence_sha256": "<independently validated evidence>",
  "candidate_accounting": {},
  "block_assessment": {},
  "reliability": {},
  "hypothesis_results": [],
  "floor_dependence": {},
  "stop_condition_results": [],
  "outcome": "<one exact value>",
  "reason_codes": [],
  "boundaries": {},
  "evidence_class": 1
}
```

Unknown fields are rejected recursively.

## Inputs

The decision function accepts only:

- one independently validated development manifest;
- one independently validated evidence aggregate;
- independently supplied expected manifest and evidence SHA-256 values; and
- the frozen decision contract.

It does not accept operator overrides, alternate thresholds, favorable-floor
selection, dropped candidates, or a replacement coverage rule.

## Universal stops

Universal stops are evaluated first. A triggered stop forces
`stop_estimand_before_revised_pilot` and retains the exact reason.

Stops include:

```text
identity_mismatch
manifest_unverifiable
scientific_set_access
post_freeze_candidate_mutation
outcome_driven_selection
guard_relaxed
missing_observation_dropped
candidate_accounting_incomplete
coverage_failure
floor_rule_violation
forbidden_output
unauthorized_execution_claim
```

Coverage failure is a valid scientific-development stop, not a malformed packet.
Identity, custody, or forbidden-output failures stop without interpretation.

## Candidate accounting gate

Review readiness requires:

```text
manifest candidates: 580
accounted candidates: 580
post-freeze additions: 0
post-freeze removals: 0
post-freeze replacements: 0
post-freeze promotions: 0
```

Measured, excluded, and missing counts must sum to 580. All 2,320 expected
candidate-layer identities must be present or explicitly missing with reason.

## Block assessment

There are exactly 29 ordered block records. A block succeeds only if every
selected layer meets:

```text
primary floor: at least 18/20 total and 3/4 in every category
sensitivity floor: at least 18/20 total and 3/4 in every category
```

Review readiness requires 29 successful blocks and zero failed or stopped blocks.

## Reliability calculation

For 29 successes in 29 independent blocks, retain:

```jsonc
{
  "method": "one_sided_exact_binomial_all_successes",
  "confidence": 0.95,
  "successes": 29,
  "trials": 29,
  "lower_bound": 0.9018553723,
  "required_lower_bound": 0.90,
  "defined": true
}
```

The validator recomputes `0.05^(1/29)`. If any block fails, this all-success
calculation is unavailable and the outcome is stop. The rule is not replaced
after observation.

## Hypothesis closure

Exactly H1 through H5 must be present. Each is either defined with a descriptive
interpretation or explicitly unresolved. A missing record, undeclared feature, or
changed method stops the packet.

Hypothesis interpretation cannot compensate for failed block coverage and cannot
promote review readiness into a scientific claim.

## Outcomes

Exactly two values are allowed:

### `ready_for_independent_preregistration_review`

Requires all of the following:

1. source, manifest, exclusion-registry, and evidence identities validate;
2. candidate accounting is complete and unchanged after freeze;
3. 29 of 29 blocks succeed under both floors;
4. the exact reliability lower bound exceeds 0.90;
5. H1-H5 closure passes;
6. no universal stop is triggered; and
7. boundaries and evidence class remain exact.

This outcome authorizes review only.

### `stop_estimand_before_revised_pilot`

Applies whenever a universal stop, coverage failure, incomplete accounting,
identity failure, floor-rule violation, or H1-H5 closure failure occurs.

The packet must distinguish:

- `current_generator_not_ready`: valid evidence shows this generator version
  fails the rule; and
- `stop_without_interpretation`: identity, custody, schema, or authorization
  failure prevents a scientific reading.

A stop does not prove that every possible generator is impossible. A revised
generator needs a new version, fresh disjoint corpus, independent review, and
separate authorization.

## Boundaries

Every decision packet requires:

```jsonc
{
  "pilot_authorized": false,
  "confirmation_authorized": false,
  "gpu_execution_authorized": false,
  "artifact_transfer_authorized": false,
  "thresholds_ratified": false,
  "scientific_pass": false
}
```

The packet cannot alter these values. A later authority record is a separate
artifact and cannot be inferred from review readiness.

## Validation obligations

CPU-only tests prove:

- the all-success packet yields review readiness only;
- one failed block yields stop;
- a primary-only success with sensitivity failure yields stop;
- missing candidates yield stop;
- H1-H5 may be unresolved but cannot be absent;
- forbidden pilot, threshold, confirmation, transfer, or scientific fields fail
  schema validation; and
- no packet authenticates its own manifest or evidence inputs.
