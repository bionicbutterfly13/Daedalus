# Contract: `jspace-observation-stage2b/v1`

This contract covers the ratified dual-floor, fully crossed 8×8 pilot measurement,
estimation, uncertainty, and threshold derivation. It does not authorize execution
or permit a pilot scientific gate or decision.

## Content addressing

```python
canonical = json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
filename = f"{prefix}_{digest[:16]}.json"
```

Writers use exclusive creation, compare bytes when a content-addressed path already
exists, and verify the on-disk SHA-256 after writing. Evidence files are immutable.

## Aggregate envelope

The aggregate carries immutable run/model/lens/code/runtime provenance, the checked
manifest and partition, disjointness evidence, preflight state, the explicit
registry, design constants, retention declarations, and descriptive measurements.

The current schema is pilot-only. It requires:

- exact schema `jspace-observation-stage2b/v1`, `artifact_type: aggregate`, and
  `run_mode: pilot`;
- pinned model, lens, Jacobian Lens commit, and package versions;
- explicit true pilot-protocol, pilot-authorization, identity, capacity, tensor,
  and crossing checks, while confirmatory authorization remains false;
- the pinned 200-prompt source-manifest identity and canonical 20-prompt pilot-view
  identity;
- exact 20 prompts × 4 selected layers = 80 unique compact records; and
- the ratified floor, crossing, count, and content-hash-method identifiers.

The pilot producer MUST NOT accept or emit scientific gates or a final decision.
The schema uses explicit allowed-field sets for the aggregate and every normative
nested object; undeclared fields are rejected regardless of their name.

The runtime block also binds the exact
`stage2b-colab-runtime-install/v2` specification digest, proves that package
imports occurred in a fresh Python process, and records
`torchvision_state: "absent"`. The authorization block retains the independently
approved canonical notebook and code-bundle SHA-256 identities. These are required
provenance, not scientific inputs.
The offline validator accepts those three source identities only through an
independent trusted input supplied by the launch surface. Matching strings inside
the artifact do not establish source identity.

Required compact content:

```jsonc
{
  "constants": {
    "min_denominator": 0.125,
    "guard_quantile": 0.05,
    "guard_quantile_method": "linear",
    "bootstrap_iterations": 20000,
    "bootstrap_ci_level": 0.99,
    "bootstrap_quantile_method": "linear",
    "bootstrap_bit_generator": "PCG64"
  },
  "registry": {
    "entries": [
      {
        "name": "NTA_MIN_DENOMINATOR",
        "declared_value": 0.125,
        "status": "derived"
      }
    ]
  },
  "denominator_derivation": {
    "source_floor": "input_embedding_decoded",
    "source_count": 80,
    "source_denominators_sha256": "<canonical ordered vector SHA-256>",
    "quantile": 0.05,
    "quantile_method": "linear",
    "derived_value": 0.125
  },
  "descriptive": {
    "records": [],
    "factorization": {
      "unique_readouts_per_prompt_layer": 81,
      "logical_crossings_per_prompt_layer": 64,
      "donor_assignment_count": 8,
      "broken_map_draw_count": 8
    }
  },
  "inference": {
    "coverage": {},
    "prompt_layer_effects": [],
    "layer_estimates": [],
    "rng": {},
    "threshold_derivation": {}
  }
}
```

`constants.min_denominator` is a derived pilot value, not an authorization input.
A real artifact is valid only when it exactly recomputes from the retained 80-value
primary-floor source vector and equals the registry's derived
`NTA_MIN_DENOMINATOR` entry.

## Compact prompt/layer record

`descriptive.records` is a non-empty prompt × selected-layer table. Every record
uses the required core schema below. No optional secondary-control fields are
admitted while their scientific policy is unratified; unknown fields are rejected.

```jsonc
{
  "prompt_sha256": "<64 lowercase hex>",
  "category": "factual_recall",
  "layer": 6,
  "target_id": 12345,
  "target_source": "model_argmax",
  "target_derivation": {
    "method": "model_argmax",
    "output_logits_sha256": "<dtype-shape-bytes SHA-256>",
    "output_logits_dtype": "float32",
    "output_logits_shape": [151936],
    "max_logit": 12.5,
    "argmax_tie_token_ids": [12345],
    "tie_break_rule": "lowest_token_id",
    "runtime_verifier_id": "validate_observation.verify_target_derivation_against_logits/v1",
    "runtime_verified": true,
    "target_decision_sha256": "<canonical decision SHA-256>"
  },

  "floor_scores": {
    "input_embedding_decoded": -0.72,
    "layer0_residual_decoded": -0.64,
    "output_decoded": 0.0
  },

  "donor_assignments": [
    {
      "donor_assignment_id": "donor-0",
      "seed_index": 0,
      "seed_namespace": "jspace-stage2b/v1|donor-assignment|0",
      "seed_sha256": "<full namespace SHA-256>",
      "seed": 100,
      "bit_generator": "PCG64",
      "recipient_prompt_sha256": "<record prompt digest>",
      "source_prompt_sha256": "<different prompt digest>",
      "recipient_to_donor_sha256": "<SHA-256 of recipient->source>",
      "residual_sha256": "<realized residual content hash>"
    }
  ],

  "map_draws": [
    {
      "map_draw_id": "map-0",
      "seed_index": 0,
      "seed_namespace": "jspace-stage2b/v1|broken-map|0",
      "seed_sha256": "<full namespace SHA-256>",
      "seed": 200,
      "bit_generator": "PCG64",
      "sha256": "<realized map content hash>",
      "spectrum_check": {
        "schema": "stage2b-map-spectrum-check/v1",
        "method": "numpy.linalg.svd-allclose/v1",
        "singular_value_count": 2048,
        "fitted_singular_values_sha256": "<all fitted singular values>",
        "broken_singular_values_sha256": "<all realized singular values>",
        "rtol": 0.00001,
        "atol": 0.000001,
        "max_abs_diff": 0.00001,
        "max_normalized_error": 0.25,
        "verified": true
      }
    }
  ],

  "factorized_scores": {
    "correct_act_fitted_map": -0.21,
    "correct_act_broken_map": {"map-0": -0.43},
    "wrong_act_fitted_map": {"donor-0": -0.39},
    "wrong_act_broken_map": {
      "donor-0": {"map-0": -0.46}
    }
  },

  "factorized_nta": {
    "input_embedding_decoded": {
      "correct_act_fitted_map": 0.71,
      "correct_act_broken_map": {"map-0": 0.40},
      "wrong_act_fitted_map": {"donor-0": 0.46},
      "wrong_act_broken_map": {"donor-0": {"map-0": 0.36}}
    },
    "layer0_residual_decoded": {
      "correct_act_fitted_map": 0.67,
      "correct_act_broken_map": {"map-0": 0.33},
      "wrong_act_fitted_map": {"donor-0": 0.39},
      "wrong_act_broken_map": {"donor-0": {"map-0": 0.28}}
    },
    "sensitivity_minus_primary": {
      "correct_act_fitted_map": -0.04,
      "correct_act_broken_map": {"map-0": -0.07},
      "wrong_act_fitted_map": {"donor-0": -0.07},
      "wrong_act_broken_map": {"donor-0": {"map-0": -0.08}}
    }
  }
}
```

The examples abbreviate the arrays and maps. A valid record contains exactly eight
`donor_assignments` and eight `map_draws`, each with unique IDs and seeds. Their IDs
must exactly equal the row and column keys in both factorized trees.

## Inference and threshold blocks

`inference.prompt_layer_effects` retains, for each prompt-layer-floor:

- the eight map-indexed correct effects;
- the 64 donor×map wrong effects and interactions;
- their equal-weight means;
- eligibility and any denominator-exclusion reason; and
- category plus prompt/layer identities.

`inference.coverage` retains the fixed floor-layer exclusion masks, eligible
counts, per-category counts, and defined/undefined status. Pilot coverage requires
at least 18/20 prompts and 3/4 prompts in each category.

`inference.layer_estimates` contains one record per floor × layer × estimand ×
method. Each contains the category-balanced mean, 20,000-replicate count,
two-sided 99% linear-percentile bounds, finite-replicate count, and defined status.
Methods are exactly:

```text
category_stratified_prompt_percentile
prompt_donor_map_product_weight_percentile
```

The RNG block records:

```jsonc
{
  "namespace": "jspace-stage2b/v1|pilot|bootstrap-v1",
  "sha256": "<full namespace SHA-256>",
  "seed": "<unsigned first-eight-byte integer>",
  "byte_order": "big",
  "bit_generator": "PCG64",
  "numpy_version": "<pinned runtime version>",
  "iterations": 20000,
  "weight_distribution": "Exp(1)"
}
```

`threshold_derivation` is either unavailable with an exact reason or contains the
four-layer `SPEC_MIN_EFFECT` and `INTERACTION_MIN_EFFECT` vectors. Available
vectors must equal one half of the corresponding defined positive primary-floor
point estimates. The block retains the eight source estimates, factor `0.5`,
source floor, layer order, pilot artifact identity, and derivation-code identity.
It is evidence for a later lock, not a pilot gate.

## Scalar and factorization rules

- Every `floor_scores` value is a finite scalar normalized log-rank score.
- Every leaf in `factorized_scores` is a finite scalar, not a rank/score object.
- Each `factorized_nta` leaf is a scalar or null only when the ratified denominator
  excludes that normalized calculation.
- A present null leaf is an exclusion. An absent factor key is malformed; the
  materializer distinguishes those states and preserves all 64 logical crossings
  even when one or both floor trees are wholly excluded.
- Both named decoding floors are complete parallel trees.
- `sensitivity_minus_primary` is recomputed from those trees and is not a selected
  third floor.
- Factorization reconstructs exactly 64 donor/map pairs from 81 unique readouts:
  `1 + 8 + 8 + 64`.

## Provenance rules

For every donor assignment:

1. `recipient_prompt_sha256` equals the record prompt digest.
2. `source_prompt_sha256` is a different valid prompt digest.
3. `recipient_to_donor_sha256` is SHA-256 of the ASCII payload
   `"<recipient>-><source>"`.
4. `residual_sha256` identifies the realized residual content under
   `dtype-shape-bytes-sha256-v1`.

For every map draw, `map_draw_id`, integer `seed`, realized map `sha256`, and
complete `spectrum_check` are required. The producer computes one fitted-map SVD
per layer, reuses it to build all eight maps, and computes the singular values of
each realized map independently. The check retains both singular-value-vector
digests and proves every component falls within `atol + rtol * abs(fitted)` using
implemented tolerances `1e-6` and `1e-5`. Exactly eight unique donor IDs/seeds and
eight unique map IDs/seeds must be present. Each seed's ID, zero-based index,
namespace, full digest, unsigned big-endian integer, and `PCG64` identity must
recompute exactly.

`target_decision_sha256` is SHA-256 of canonical compact JSON containing
`target_id` plus every other `target_derivation` field, followed by one newline.
Before full logits are discarded, the producer calls the named runtime verifier
with the live full-vocabulary vector. That verifier independently recomputes the
vector's dtype, shape, content digest, finite maximum, complete sorted maximum-tie
set, lowest-token tie break, target ID, and canonical target-decision digest.
Production stops if any field disagrees. The retained offline validator requires
the exact verifier identity and true attestation, recomputes the decision digest,
requires the target to be the lowest recorded tied token ID, and requires one
prompt's derivation to be identical across layers. It cannot independently
reconstruct discarded logits; it verifies the retained attestation and
content-addressed artifact. The output-logits digest uses
`dtype-shape-bytes-sha256-v1`; full logits remain unretained.

The retained artifact does not include raw residuals or broken maps. The offline
validator therefore recomputes the donor selected by every recipient/assignment
seed from the exact pilot population, recipient→donor hashes, all score/NTA trees,
and the normalized-error spectrum decision. It also checks residual/map hashes
for exact syntax, run-wide seed consistency, same-layer map-hash consistency,
same-layer fitted-spectrum identity, and map-specific spectrum evidence
consistency across prompts. It cannot recompute tensor-content hashes from
bytes that the retention policy forbids persisting. The runtime producer computes
those hashes directly from contiguous live arrays before writing the artifact; the
bounded real-runtime integration smoke must independently exercise that producer
path.

## Pilot-view binding

Pilot validation consumes an independently checked pilot view. The aggregate
partition IDs, prompt digests, canonical pilot-view SHA-256
`5bef8316f72682a628fc1240bf6068a91aa7c8a330377206cbd9145434b797e4`,
source-manifest SHA-256
`ba29c629c7b9601980b6c0bb9cd9730242d7cd6b7eacb1166c307837416d4bbf`,
and compact-record coverage must agree exactly. A different balanced 20-prompt
view is rejected.

## Validator obligations

The validator rejects:

- missing, empty, or non-compact `descriptive.records`;
- a missing or inconsistent authorization, preflight, design, manifest, partition,
  model, lens, instrumentation, or runtime envelope;
- missing compact fields or non-finite scalar leaves;
- a missing, duplicate, extra, or miscategorized prompt-layer locus;
- a target source other than `model_argmax`;
- missing, malformed, cross-layer-inconsistent, or cryptographically unbound
  model-argmax derivation evidence;
- either wrong decoding-floor name or missing `sensitivity_minus_primary`;
- donor/map cardinality, identity, seed, digest, or factor-key mismatches;
- any donor source that differs from deterministic recomputation over the pinned
  pilot population, recipient digest, and ratified donor seed;
- a donor source that changes across layers for the same recipient/assignment ID;
- absent, malformed, inconsistent, or failed realized-map spectrum evidence;
- `lens.source_layers` that omits, duplicates, or mis-types a selected layer;
- unknown aggregate or nested fields, including compact-record and provenance
  fields;
- any factorization whose `unique_readout_count` is not 81 or whose
  `logical_cell_count` is not 64;
- a `min_denominator` absent from, unratified in, or unequal to the registry;
- a denominator guard that does not recompute from exactly 80 primary denominators
  with the fixed 0.05 linear quantile or whose source-vector digest differs;
- an exclusion mask, coverage count, prompt-layer effect, category-balanced mean,
  interval, RNG identity, or threshold vector that does not recompute;
- any interval with other than 20,000 finite replicates, fixed 99% linear
  percentiles, explicit `PCG64`, or the exact SHA-derived pilot seed;
- layer pooling, category pooling, donor/map loss, imputation, or a changing
  bootstrap exclusion mask;
- a malformed or mismatched expected pilot view; and
- absent or mismatched independently supplied authorization-record, canonical
  notebook, or code-bundle identities; and
- scientific gate or decision content under any field name.

Static notebook checks do not execute cells. Real model/lens behavior, GPU behavior,
runtime tensor-content hash parity, pilot execution, confirmatory execution,
and scientific readiness remain unverified by this contract.
