# Contract: Development Manifest

Schema: `jspace-primary-floor-development-manifest/v1`

This manifest freezes the complete development corpus and analysis contract
before eligibility measurement. It is not an authorization record.

## Canonical identity

Canonical JSON uses sorted keys, two-space indentation, UTF-8, and one trailing
newline. The manifest SHA-256 is computed over the exact canonical bytes with the
top-level `manifest_sha256` field omitted. Writers use exclusive creation and
verify the on-disk digest after writing.

## Exact envelope

```jsonc
{
  "schema": "jspace-primary-floor-development-manifest/v1",
  "study_id": "jspace-primary-floor-development-v1",
  "generator_version": "v1",
  "state": "frozen",
  "created_at_utc": "<RFC3339 UTC>",
  "frozen_at_utc": "<RFC3339 UTC>",
  "manifest_sha256": "<canonical digest>",
  "boundaries": {},
  "design": {},
  "scientific_exclusion_registry": {},
  "generation_rules": [],
  "template_families": [],
  "blocks": [],
  "candidates": [],
  "measurement_identities": {},
  "feature_definitions": {},
  "hypotheses": [],
  "guard_contract": {},
  "missingness_contract": {},
  "coverage_contract": {},
  "decision_contract": {},
  "stop_conditions": [],
  "source": {}
}
```

Unknown fields are rejected recursively.

## Boundaries

Canonical source requires every field below to be false:

```jsonc
{
  "model_access_authorized": false,
  "gpu_execution_authorized": false,
  "pilot_access_authorized": false,
  "confirmation_access_authorized": false,
  "pilot_artifact_access_authorized": false,
  "artifact_transfer_authorized": false
}
```

No field in the manifest can supersede an external authorization.

## Design constants

The design block requires:

```jsonc
{
  "block_count": 29,
  "candidates_per_block": 20,
  "candidate_count": 580,
  "categories": [
    "antonym_negation",
    "arithmetic_completion",
    "category_membership",
    "factual_completion",
    "multi_token_entity"
  ],
  "candidates_per_category_per_block": 4,
  "selected_layers": [6, 13, 20, 26],
  "reliability": {
    "method": "one_sided_exact_binomial_all_successes",
    "confidence": 0.95,
    "minimum_success_probability": 0.90,
    "required_successful_blocks": 29,
    "derived_lower_bound": 0.9018553723
  }
}
```

The layer IDs must match the retained Stage 2b design before ratification. The
reliability bound must recompute from `0.05^(1/29)` within the declared numeric
tolerance.

## Scientific exclusion registry binding

The manifest names, but does not embed, the digest-only registry:

```jsonc
{
  "schema": "jspace-stage2b-scientific-prompt-digests/v1",
  "source_manifest_sha256": "<pinned 200-prompt manifest digest>",
  "source_prompt_count": 200,
  "normalization_method": "<frozen method ID>",
  "registry_sha256": "<independently supplied digest>"
}
```

The validator receives the expected registry digest independently. Scientific
prompt text and category labels do not enter the development runtime through this
registry.

## Generation rules and template families

Every generation rule records:

- stable ID and version;
- category;
- parameter schema and allowed ranges;
- deterministic seed namespace;
- canonical rendering method;
- exact and normalized digest methods;
- collision-resolution rule; and
- rule digest.

Every template family records:

- stable ID and version;
- generation-rule ID;
- category;
- operation or semantic family;
- surface-template identity and digest; and
- ordered block-slot schedule.

Generation inputs cannot include tokenizer results, target features, floor
scores, denominators, eligibility, effects, or prior block outcomes.

## Blocks

The manifest contains exactly 29 blocks with IDs `block-000` through `block-028`.
Each block records:

- block index;
- seed namespace, full SHA-256, unsigned derived seed, byte order, and generator;
- exactly 20 ordered candidate IDs;
- exactly four candidate IDs for every category; and
- canonical block digest.

Block IDs, seeds, and candidate IDs are unique. Every candidate appears in one
block only.

## Candidates

Every candidate records:

```jsonc
{
  "candidate_id": "dev-0000",
  "ordinal": 0,
  "block_id": "block-000",
  "category": "arithmetic_completion",
  "template_family_id": "<frozen family>",
  "generation_rule_id": "<frozen rule>",
  "generation_parameters": {},
  "generation_parameters_sha256": "<digest>",
  "text": "<exact frozen prompt>",
  "utf8_bytes": 0,
  "sha256": "<exact text digest>",
  "normalized_sha256": "<normalized comparison digest>",
  "collision_check": {
    "exact_overlap": false,
    "normalized_overlap": false,
    "registry_sha256": "<bound registry>"
  }
}
```

All 580 IDs, exact digests, and normalized digests are unique. Prompt bytes match
their exact digest. Generation parameters match their digest and frozen rule.

## Measurement identities and features

The manifest freezes exact model, revision, tokenizer, lens repository, lens
revision, lens file and digest, decoding method, selected layers, source code,
analysis code, and runtime specification identities.

Feature definitions name only the H1-H5 fields approved in `research.md`. A
runtime may emit no undeclared feature.

## Guard, missingness, and coverage

The guard contract is exact:

```text
source floor: input_embedding_decoded
sensitivity floor: layer0_residual_decoded
source count per block: 80
quantile: 0.05
method: linear
one derived guard applied to both floors
```

Missing and excluded loci remain in accounting with stable reason codes.
Coverage is evaluated for every block, floor, and layer using 18/20 overall and
3/4 in every category.

## Hypotheses and decision

The manifest contains exactly H1 through H5. Each freezes its prediction,
features, comparison method, adjustments, falsifier, missingness behavior, and
undefined policy.

The decision contract permits exactly:

```text
ready_for_independent_preregistration_review
stop_estimand_before_revised_pilot
```

Review readiness requires 29 of 29 block successes under both floors. Hypothesis
interpretation cannot override block coverage or a universal stop.

## Freeze validation

Freeze succeeds only when:

1. the exact schema and recursive field closure pass;
2. all 29 blocks and 580 candidates are complete;
3. category, block, family, seed, and candidate identities recompute;
4. exact and normalized disjointness pass against the independent registry;
5. all measurement and analysis identities are present;
6. boundaries are false; and
7. the canonical manifest digest matches independently supplied bytes.

After freeze, candidate or rule mutation creates a new generator version. It
cannot alter this manifest.
