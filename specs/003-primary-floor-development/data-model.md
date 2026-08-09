# Data Model: Primary-Floor Development Study

Schema family:

```text
jspace-primary-floor-development-manifest/v1
jspace-primary-floor-development-evidence/v1
jspace-primary-floor-development-decision/v1
```

The development model is separate from `jspace-observation-stage2b/v1`. It
preserves the completed pilot schema and authorization as immutable historical
contracts.

## 1. Study definition

The study definition binds the complete development design before measurement.

Required fields:

- `study_id`: stable identifier for this development study;
- `generator_version`: immutable generator revision;
- `created_at_utc` and `frozen_at_utc`;
- `state`: lifecycle state;
- `manifest_sha256`: canonical manifest identity;
- `block_count`: exactly `29`;
- `candidates_per_block`: exactly `20`;
- `candidate_count`: exactly `580`;
- `selected_layers`: exactly `[6, 13, 20, 26]`;
- `primary_floor_id`: `input_embedding_decoded`;
- `sensitivity_floor_id`: `layer0_residual_decoded`;
- `guard_quantile`: `0.05`;
- `guard_quantile_method`: `linear`;
- `minimum_total_eligible`: `18`;
- `minimum_category_eligible`: `3` of `4`;
- `reliability_confidence`: one-sided `0.95`;
- `minimum_generator_success_probability`: `0.90`;
- `required_successful_blocks`: `29` of `29`; and
- explicit authorization and custody boundaries, all false in canonical source.

Validation rules:

- Counts and identifiers are exact, not lower bounds.
- The manifest digest is computed from canonical JSON with its self-digest field
  excluded.
- No execution boundary may be true in a design-only manifest.
- Numeric design values are proposed until independently reviewed and ratified.

## 2. Scientific exclusion registry

The exclusion registry is a digest-only commitment to the 200 sealed scientific
prompts.

Required fields:

- schema and registry version;
- source scientific-manifest SHA-256;
- source prompt count `200`;
- ordered exact prompt SHA-256 values;
- ordered normalized-comparison SHA-256 values;
- normalization method identity;
- canonical registry SHA-256; and
- creation source identity.

Validation rules:

- Development runtime receives no scientific prompt text or category labels from
  this registry.
- Exact and normalized digest sets contain 200 unique entries.
- The registry identity is independently supplied to preflight.
- A development candidate matching either set cannot enter a frozen manifest.

## 3. Generation rule

A generation rule defines how candidates are created without reference to
measured outcomes.

Fields:

- `generation_rule_id` and version;
- category;
- parameter names, types, ranges, and exclusions;
- deterministic seed namespace;
- canonicalization and rendering rules;
- collision-resolution rule;
- stable rule SHA-256; and
- allowed template-family IDs.

Validation rules:

- A rule cannot accept denominator, eligibility, effect, floor, or target outcome
  fields as inputs.
- Parameter domains freeze before candidate generation.
- Collision resolution advances only through the frozen next-seed procedure.

## 4. Template family

A template family is the unit of prompt-construction design.

Fields:

- `template_family_id` and version;
- generation-rule ID;
- category;
- operation or semantic family;
- surface-template identity;
- canonical template SHA-256;
- planned slot schedule by block;
- active generator version; and
- status `proposed`, `ratified`, or `retired`.

Relationships:

- One generation rule has one or more template families.
- Every candidate belongs to exactly one template family.
- Every block's family schedule is determined before candidate content exists.

## 5. Development block

The block is the statistical unit for guard derivation, coverage, and generator
reliability.

Fields:

- `block_id`: `block-000` through `block-028`;
- `block_index`: zero-based integer;
- seed namespace, full digest, derived integer, byte order, and generator family;
- ordered candidate IDs;
- exactly four candidate IDs per category;
- block content SHA-256;
- state;
- derived guard record;
- both-floor coverage records; and
- block outcome.

Validation rules:

- Every block has exactly 20 unique candidates.
- Category counts are exactly four each.
- A candidate belongs to exactly one block.
- Block seeds and IDs are unique and reproduce from the frozen namespace.
- Coverage is evaluated independently per floor and layer.

## 6. Development candidate

The candidate is frozen before any model, tokenizer-outcome, or floor measurement.

Fields:

- `candidate_id` and ordinal;
- block ID;
- category;
- template-family ID and generation-rule ID;
- generation parameters and their canonical digest;
- exact prompt text and UTF-8 byte count;
- exact prompt SHA-256;
- normalized-comparison SHA-256;
- collision-check result;
- freeze identity; and
- lifecycle state.

Validation rules:

- IDs, exact digests, and normalized digests are unique across all 580 candidates.
- No exact or normalized digest overlaps the scientific exclusion registry.
- All required generation parameters are present and within the frozen domain.
- There is no removed, replaced, selected, or promoted post-freeze state.

## 7. Candidate-layer measurement

There are exactly 2,320 expected loci: 580 candidates × 4 selected layers.

Fields:

- candidate ID, prompt digest, block ID, category, template-family ID, and layer;
- target ID and target derivation attestation;
- output-logits identity, shape, dtype, finite maximum, tie IDs, and tie rule;
- tokenizer identity and declared tokenization features;
- target-property features;
- floor scores for `input_embedding_decoded`,
  `layer0_residual_decoded`, and `output_decoded`;
- floor-specific denominator, guard margin, eligibility, and exclusion reason;
- identity attestation;
- missingness status and reason; and
- record SHA-256.

Validation rules:

- Target derivation remains identical across layers for one candidate.
- Floor scores are retained before denominator or eligibility computation.
- Missing or excluded loci remain explicit and cannot be silently removed.
- Floor identity is exact; no alias or favorable-floor substitution is accepted.

## 8. Block guard

Each block derives one guard after all 80 primary denominators are retained.

Fields:

- block ID;
- source floor `input_embedding_decoded`;
- ordered 80-value source vector and its SHA-256;
- quantile `0.05`;
- quantile method `linear`;
- derived guard value;
- finite and positive checks; and
- derivation-code identity.

Validation rules:

- Exactly 80 finite primary denominators are required.
- The guard is derived once and applied unchanged to both floors.
- A nonfinite or nonpositive guard stops the block before interpretation.
- A second model or lens pass cannot be used to repair a denominator.

## 9. Floor-layer coverage

Each block has one coverage record per floor and selected layer.

Fields:

- block, floor, and layer;
- 20 ordered candidate eligibility states;
- total eligible count;
- eligible count for each of five categories;
- `defined` Boolean;
- reason code; and
- coverage-record SHA-256.

Validation rules:

- Defined requires at least 18 of 20 eligible and at least 3 of 4 in every
  category.
- Primary and sensitivity records are retained separately.
- A block succeeds only when all floor-layer coverage records are defined.

## 10. Hypothesis evaluation

There are exactly five hypothesis records, H1 through H5.

Fields:

- hypothesis ID;
- frozen prediction and falsifier;
- declared feature names;
- comparison method and adjustments;
- block-fold identities where applicable;
- candidate and missing counts;
- metrics and uncertainty summaries;
- structural status `defined`, `undefined`, or `stopped`;
- interpretation `consistent`, `inconsistent`, or `unresolved`;
- bounded result summary; and
- evidence digest.

Validation rules:

- H1-H3 folds are leave-one-block-out and include all 29 blocks once as the held
  out block.
- H4 comparisons are paired within candidate.
- H5 uses per-block guards and block outcomes.
- Undefined and stopped records retain exact reasons.
- Hypothesis interpretation cannot alter the binary decision rule.

## 11. Development evidence aggregate

The aggregate binds:

- immutable source, model, tokenizer, lens, decoding, code, runtime, manifest,
  exclusion-registry, and analysis identities;
- authorization boundaries;
- all 2,320 candidate-layer records;
- 29 guard records;
- all floor-layer coverage records;
- complete candidate accounting;
- H1-H5 records;
- stop-condition results; and
- decision input identity.

Validation rules:

- Unknown fields are rejected recursively.
- Expected source identities are supplied independently to the validator.
- The aggregate contains no pilot threshold, pilot pass, confirmation result,
  scientific gate, transfer authorization, or claim above evidence class 1.

## 12. Decision packet

Fields:

- schema, study ID, generator version, and packet identity;
- manifest, exclusion-registry, evidence, and source identities;
- candidate accounting totals;
- 29 block outcomes;
- exact reliability calculation;
- H1-H5 summaries;
- floor-dependence summary;
- universal stop results;
- outcome;
- reason codes;
- boundaries; and
- `evidence_class: 1`.

The only outcomes are:

```text
ready_for_independent_preregistration_review
stop_estimand_before_revised_pilot
```

## 13. State transitions

### Design lifecycle under current authorization

```text
draft
  -> frozen
  -> structurally_validated
  -> awaiting_separate_execution_authorization
```

No real measurement transition is available under this feature's current
authorization.

### Later separately authorized study

```text
authorized
  -> running
  -> evidence_validated
  -> ready_for_independent_preregistration_review
  -> or stop_estimand_before_revised_pilot
```

Any identity mismatch, contamination, post-freeze mutation, guard relaxation,
missing-accounting failure, coverage failure, or forbidden output transitions to
terminal `stopped`.

### Candidate lifecycle

```text
generated -> frozen -> measured | excluded | missing
```

Every terminal candidate remains in accounting.

### Block lifecycle

```text
generated
  -> frozen
  -> measurements_complete
  -> guard_derived
  -> coverage_evaluated
  -> success | failure | stopped
```

There is no retry or replacement transition after `frozen`.
