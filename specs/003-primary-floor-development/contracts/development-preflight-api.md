# Contract: Development Preflight API

Public surface planned for
`EvoScientist/skills/jspace-research-operations/scripts/stage2b_development_preflight.py`.

The module imports without Torch, Jacobian Lens, a model, network access, or a
GPU. It validates extracted metadata and exact bytes before any measurement input
opens.

## Failure model

```python
class DevelopmentPreflightError(Exception):
    code: str
    detail: dict
```

The first failure raises. A warning cannot replace an enforceable check. Codes are
stable and tested.

## `check_development_manifest`

```python
check_development_manifest(
    manifest,
    *,
    expected_manifest_sha256,
    expected_scientific_exclusion_registry_sha256,
    scientific_prompt_digests,
) -> None
```

Checks:

- exact schema and recursive allowed fields;
- canonical manifest bytes against the independently supplied digest;
- exact 29-block, 580-candidate, and per-category counts;
- deterministic block and candidate identities;
- exact and normalized disjointness against 200 digest-only exclusions;
- generation-rule and template-family closure;
- no outcome fields in generation inputs;
- exact H1-H5 definitions; and
- immutable design boundaries.

Representative codes:

```text
manifest_schema
manifest_digest
manifest_unknown_field
manifest_count
block_identity
block_balance
candidate_identity
duplicate_candidate
scientific_overlap
exclusion_registry_identity
generation_rule_identity
template_family_identity
sampling_rule_uses_outcome
post_freeze_mutation
```

## `check_development_boundaries`

```python
check_development_boundaries(manifest) -> None
```

Requires model access, GPU execution, pilot access, confirmation access, pilot
artifact access, and artifact transfer to be false in canonical source. It also
rejects pilot thresholds, pilot authorization, confirmation authorization, and
scientific decision fields.

Codes:

```text
boundary_violation
pilot_scope
confirmation_scope
artifact_scope
forbidden_output
```

## `check_development_identities`

```python
check_development_identities(observed, expected) -> None
```

Compares exact model, tokenizer, lens repository, lens revision, lens file and
digest, decoding method, selected layers, code, analysis, runtime, manifest, and
exclusion-registry identities. Expected values come from the trusted launch
surface, not the evidence object.

Codes:

```text
identity_required
identity_mismatch
model_identity
tokenizer_identity
lens_identity
decoding_identity
layer_identity
code_identity
analysis_identity
runtime_identity
```

## `check_template_sampling_contract`

```python
check_template_sampling_contract(manifest) -> None
```

Requires:

- exactly 29 independent block seeds;
- exactly 20 candidates per block;
- four candidates in each of five categories;
- template slots fixed before candidate measurement;
- deterministic collision handling before freeze;
- all generated candidates retained; and
- no denominator, eligibility, effect, tokenization outcome, target outcome, or
  prior block result as a generation input.

Codes:

```text
sampling_rule_identity
sampling_rule_balance
sampling_rule_seed
sampling_rule_outcome_input
collision_rule_identity
candidate_accounting
```

## `check_development_authorization`

The API is specified for a later separately approved execution surface:

```python
check_development_authorization(
    record,
    *,
    approved_record_sha256,
    expected_manifest_sha256,
    expected_code_bundle_sha256,
    expected_notebook_sha256,
) -> None
```

No authorization record ships under the current plan. A future record must be
content-addressed, name Dr. Mani as authority, bind exact manifest, notebook, and
bundle bytes, authorize development mode only, keep pilot and confirmation access
false, and keep artifact transfer false unless separately approved.

Pilot authorization records are invalid on this surface.

Codes:

```text
authorization_required
authorization_digest
authorization_authority
authorization_scope
authorization_source
authorization_manifest
authorization_transfer
pilot_authorization_reuse
```

## Guard and coverage preflight

Before measurement, preflight verifies the declared rule only:

- four selected layers;
- primary and sensitivity floor identities;
- 0.05 linear guard derivation from exactly 80 primary denominators per block;
- 18/20 overall and 3/4 category coverage;
- both floors required; and
- 29-of-29 success for review readiness.

No numeric guard is accepted as an authorization input. Guards derive after raw
score retention within each block.

## Failure ordering

The runtime fails in this order:

1. exact source-byte and manifest identity;
2. scientific exclusion registry and disjointness;
3. canonical false boundaries;
4. separate authorization, if an execution surface exists;
5. model, tokenizer, lens, decoding, and layer identities;
6. generation and block structure;
7. environment and capacity; and
8. measurement.

No model import, weight load, GPU allocation, prompt measurement, or evidence
write occurs before the applicable checks pass.

## Test obligations

CPU-only tests make every stable code fire and prove:

- a self-consistent manifest cannot authenticate itself;
- full scientific prompt text is not required for disjointness;
- post-freeze mutation fails;
- sampling cannot accept outcome inputs;
- false boundaries are mandatory;
- pilot authorization cannot be reused; and
- a passed preflight authorizes nothing without a separately approved record.
