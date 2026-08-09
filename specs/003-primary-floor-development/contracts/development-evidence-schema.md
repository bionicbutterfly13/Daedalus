# Contract: Development Evidence

Schema: `jspace-primary-floor-development-evidence/v1`

This schema records one separately authorized development study. It is not the
Stage 2b pilot schema and contains no pilot threshold or scientific decision.

## Aggregate envelope

```jsonc
{
  "schema": "jspace-primary-floor-development-evidence/v1",
  "artifact_type": "aggregate",
  "study_id": "jspace-primary-floor-development-v1",
  "generator_version": "v1",
  "evidence_class": 1,
  "state": "evidence_validated",
  "run": {},
  "source": {},
  "runtime": {},
  "model": {},
  "tokenizer": {},
  "lens": {},
  "decoding": {},
  "authorization": {},
  "boundaries": {},
  "development_manifest": {},
  "scientific_exclusion_registry": {},
  "candidate_accounting": {},
  "measurements": [],
  "block_guards": [],
  "coverage": [],
  "hypotheses": [],
  "floor_dependence": {},
  "stop_conditions": [],
  "decision_input_sha256": "<digest>"
}
```

Unknown fields are rejected recursively. Expected source identities are supplied
to the validator independently.

## Source and boundary requirements

The evidence binds exact manifest, exclusion registry, notebook, code bundle,
analysis source, runtime specification, model, tokenizer, lens, decoding, and
selected-layer identities.

Development authorization, if present, is separate from pilot authorization and
must retain:

```text
pilot access: false
confirmation access: false
pilot artifact access: false
artifact transfer: false unless separately authorized
```

The artifact cannot establish authorization by containing matching strings.

## Candidate accounting

```jsonc
{
  "manifest_candidate_count": 580,
  "measured_candidate_count": 0,
  "excluded_candidate_count": 0,
  "missing_candidate_count": 0,
  "accounted_candidate_count": 580,
  "post_freeze_additions": 0,
  "post_freeze_removals": 0,
  "post_freeze_replacements": 0,
  "post_freeze_promotions": 0,
  "candidate_ids_sha256": "<ordered identity digest>"
}
```

Terminal counts must sum to 580. Every candidate ID must match the frozen
manifest exactly.

## Candidate-layer record

The `measurements` list contains exactly 2,320 records when measurement completes.
Each record contains:

```jsonc
{
  "candidate_id": "dev-0000",
  "prompt_sha256": "<manifest digest>",
  "block_id": "block-000",
  "category": "arithmetic_completion",
  "template_family_id": "<family>",
  "layer": "<selected layer>",
  "target_derivation": {},
  "tokenization": {},
  "target_features": {},
  "floor_scores": {
    "input_embedding_decoded": -0.5,
    "layer0_residual_decoded": -0.4,
    "output_decoded": 0.0
  },
  "floor_status": {
    "input_embedding_decoded": {},
    "layer0_residual_decoded": {}
  },
  "identity_attestation": {},
  "missingness": {
    "status": "observed",
    "reason": null
  },
  "record_sha256": "<canonical record digest>"
}
```

Target derivation reuses the retained Stage 2b fields for output-logits identity,
tie handling, runtime verification, and target-decision digest.

Tokenization contains only frozen H2 fields. Target features contain only frozen
H3 fields. Undeclared exploratory fields require a separate non-normative
attachment and cannot enter H1-H5 or the decision.

## Block guards

There are exactly 29 guard records:

```jsonc
{
  "block_id": "block-000",
  "source_floor": "input_embedding_decoded",
  "source_count": 80,
  "source_denominators_sha256": "<ordered vector digest>",
  "quantile": 0.05,
  "quantile_method": "linear",
  "derived_value": 0.1,
  "finite": true,
  "positive": true,
  "derivation_code_sha256": "<analysis source>"
}
```

The validator recomputes each ordered vector from retained floor scores and
output scores, then recomputes the linear quantile. The same derived scalar is
used for both floors in that block.

## Floor status

For each floor, the denominator is:

```text
s(output_decoded) - s(floor)
```

The status records denominator, block guard, guard margin, finite state,
eligibility, and exclusion reason. Eligibility requires a finite denominator
strictly greater than the block guard. Equality is excluded.

Missingness, nonfinite values, and denominator exclusions remain explicit. No
value is imputed, converted to zero, borrowed from the other floor, or silently
dropped.

## Coverage

Coverage contains one record per block, floor, and selected layer. Every record
retains:

- ordered 20-candidate eligibility mask;
- total eligible count;
- five category counts;
- `defined` Boolean; and
- exact reason code.

Defined requires at least 18 of 20 overall and at least 3 of 4 in every category.
A block succeeds only when all primary and sensitivity floor-layer records are
defined.

## H1-H5 records

Exactly five records are required. Every record contains:

```jsonc
{
  "hypothesis_id": "H1",
  "prediction": "<frozen text identity>",
  "feature_names": [],
  "comparison_method": "<frozen method ID>",
  "comparison_adjustments": [],
  "falsifier": "<frozen text identity>",
  "candidate_count": 580,
  "missing_count": 0,
  "status": "defined",
  "interpretation": "consistent",
  "metrics": {},
  "result_summary": "<bounded summary>",
  "evidence_digest": "<normative input digest>"
}
```

Allowed status values are `defined`, `undefined`, and `stopped`. Allowed
interpretations are `consistent`, `inconsistent`, and `unresolved`.

H1-H3 retain all 29 leave-one-block-out fold identities and predictive losses.
H4 retains paired floor differences and discordance. H5 retains category
lower-tail summaries and all 29 exact block outcomes.

## Floor dependence

The floor-dependence block reports:

- primary and sensitivity eligible counts by block, category, and layer;
- paired guard-margin differences;
- primary-ineligible/sensitivity-eligible discordance;
- sensitivity-ineligible/primary-eligible discordance; and
- any coverage disagreement.

It cannot choose a preferred floor or label a floor-dependent result robust.

## Stop conditions

Every universal stop has one explicit record with `triggered`, evidence identity,
and reason code. Missing stop records invalidate the artifact.

Triggered conditions include identity mismatch, unverifiable manifest,
scientific-set access, post-freeze item selection, relaxed guard, silently dropped
observations, coverage failure, forbidden floor handling, and unauthorized output.

## Forbidden fields and claims

The schema rejects, at any nesting level:

- `SPEC_MIN_EFFECT` or `INTERACTION_MIN_EFFECT` vectors;
- pilot or confirmation pass/fail;
- `THRESHOLDS_RATIFIED`;
- confirmation measurements or access;
- scientific gates or decisions;
- evidence class greater than 1;
- artifact-transfer claims beyond a separately supplied authorization; and
- any field that treats review readiness as execution authorization.

## Validation closure

The offline validator recomputes:

1. source and manifest linkage;
2. exact candidate and locus accounting;
3. all 29 guards;
4. both-floor denominators, margins, and eligibility;
5. all floor-layer coverage and block outcomes;
6. H1-H5 structural completeness and normative-input digests;
7. floor-dependence summaries;
8. stop-condition closure; and
9. the decision-input digest.

Artifact identity and source identity remain separate. Validation does not
authorize execution or transfer.
