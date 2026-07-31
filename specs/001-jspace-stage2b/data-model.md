# Data Model: Stage 2b 8×8 dual-floor measurement

Schema family: `jspace-observation-stage2b/v1`.

This document specifies the ratified pilot measurement, estimation, uncertainty,
and threshold-derivation data. A pilot artifact contains no scientific decision.

## 1. Identities

Every measurement binds:

- run, prompt ID, recipient prompt SHA-256, layer, and position;
- model ID/revision and output-logits content identity;
- lens repository/revision/file/hash and code identity;
- target token ID, target derivation `model_argmax`, and tie information; and
- vocabulary size and rank convention `strict_gt_1indexed`.

The target measures the model's own eventual token trajectory, not truth or task
correctness.

Each compact record carries `target_derivation` with the exact method,
`output_logits_sha256`, dtype and shape, finite maximum logit, the complete sorted
set of tied maximum token IDs, tie-break rule `lowest_token_id`, and
`runtime_verifier_id`, `runtime_verified`, and `target_decision_sha256`. Before
retention drops the full logits, the named runtime verifier independently
recomputes their dtype, shape, content digest, finite maximum, complete tie set,
lowest-token target, and decision digest. The offline validator then requires that
exact verifier attestation, recomputes the decision digest, requires `target_id` to
be the lowest tied token ID, and requires the complete derivation to remain
identical across all selected layers for one prompt. Raw full logits remain
unretained, so later offline validation verifies the retained runtime attestation
rather than reproducing the model forward pass.

## 2. Dual-floor endpoint

For each readout score `s_readout`, record two floor-specific results:

| Name | Floor identity |
|---|---|
| `primary` | `input_embedding_decoded` |
| `sensitivity` | `layer0_residual_decoded` |

Each result contains floor score, output score, denominator, NTA or an explicit
exclusion, and exclusion reason. The record also contains
`sensitivity_minus_primary`, numeric only when both NTA values are available.

```text
NTA_floor = (s_readout - s_floor) / (s_output - s_floor)
```

The pilot first retains all 80 primary denominators, derives the finite positive
0.05 linear quantile, and records it as the run-wide guard with the ordered source
vector digest. Both floor trees are then computed from retained scores without a
second model/lens pass. A denominator that is nonfinite or not greater than the
guard excludes the entire prompt-layer for that floor. No caller may select
whichever floor is more favorable.

## 3. Crossing identities

### Donor assignment

| Field | Rule |
|---|---|
| `donor_assignment_id` | exactly `donor-0` … `donor-7` |
| `seed` | first 8 bytes, unsigned big-endian, of the ratified namespace digest |
| `seed_namespace` | `jspace-stage2b/v1\|donor-assignment\|<i>` |
| `seed_sha256` | full namespace SHA-256 |
| `bit_generator` | `PCG64` |
| `recipient_prompt_sha256` | 64 lowercase hex |
| `source_prompt_sha256` | 64 lowercase hex; different from recipient and in the pinned pilot view |
| `recipient_to_donor_sha256` | recomputable SHA-256 of `"<recipient>-><source>"` |
| `residual_sha256` | runtime content attestation under `dtype-shape-bytes-sha256-v1` |

### Broken-map draw

| Field | Rule |
|---|---|
| `map_draw_id` | exactly `map-0` … `map-7` |
| `seed` | first 8 bytes, unsigned big-endian, of the ratified namespace digest |
| `seed_namespace` | `jspace-stage2b/v1\|broken-map\|<i>` |
| `seed_sha256` | full namespace SHA-256 |
| `bit_generator` | `PCG64` |
| `sha256` | runtime content attestation under `dtype-shape-bytes-sha256-v1` |
| `spectrum_check` | complete per-realization singular-spectrum evidence |

The full digest, derived integer, namespace, zero-based index, and bit-generator
identity are retained. Any collision or mismatch fails closed. Map-construction
evidence is shared by layer/map identity and repeated in each compact
prompt/layer record so every retained map reference remains self-contained. It
includes the full fitted and broken singular-value-vector digests, count,
implemented `rtol=1e-5`, `atol=1e-6`, maximum absolute and normalized error, and
true verification. The producer decomposes the fitted map once per layer, builds
all eight controls from that decomposition, and independently computes the
singular values of every realized control.

## 4. Factorized readouts

Per prompt/layer, `factorized_scores` uses:

```text
correct_act_fitted_map: Readout                         # scalar/shared
correct_act_broken_map[map_id]: Readout                 # 8
wrong_act_fitted_map[donor_id]: Readout                 # 8
wrong_act_broken_map[donor_id][map_id]: Readout         # 8 × 8
```

Each leaf is a finite normalized log-rank score. `floor_scores` records
`input_embedding_decoded`, `layer0_residual_decoded`, and `output_decoded`.
`factorized_nta` carries three parallel trees: the two floor-specific NTA trees
and `sensitivity_minus_primary`. An NTA leaf may be null only when the ratified
denominator rule excludes it. The exact key sets MUST equal the declared donor and
map ID sets. Therefore:

```text
unique_readout_count = 1 + 8 + 8 + 64 = 81
logical_combination_count = 8 × 8 = 64
```

## 5. Logical factorial view

For each `(donor_id, map_id)`, materialization yields:

```text
A = correct_act_fitted_map
B = correct_act_broken_map[map_id]
C = wrong_act_fitted_map[donor_id]
D = wrong_act_broken_map[donor_id][map_id]
```

The view also carries the donor assignment and broken-map provenance. All 64 pairs
must materialize exactly once. The compact representation is lossless; storing 64
flat records is optional.

Per floor:

```text
correct_effect[p,l,m] = A[p,l] - B[p,l,m]
wrong_effect[p,l,d,m] = C[p,l,d] - D[p,l,d,m]
interaction[p,l,d,m]  = correct_effect[p,l,m] - wrong_effect[p,l,d,m]
```

Each prompt-layer retains the eight correct effects and 64 wrong/interaction
effects plus their equal-weight arithmetic means. These are computed only after
the complete crossing passes validation.

## 6. Coverage, estimates, and intervals

Each floor-layer has a fixed exclusion mask with a reason for every excluded
prompt. It is inferentially defined only with at least 18/20 eligible prompts and
at least 3/4 eligible prompts in every category.

For each defined estimand:

1. compute the mean among eligible prompts within each category;
2. take the equal-weight mean of the five category means;
3. generate 20,000 category-stratified prompt-resampling statistics; and
4. generate 20,000 prompt×donor×map product-weight statistics with independent
   mean-one `Exp(1)` weights.

Both methods report linear 0.005 and 0.995 quantiles, forming a two-sided 99%
percentile interval. All replicates must be finite. The bootstrap RNG is an
explicit `Generator(PCG64(seed))`, where `seed` is the first eight bytes,
unsigned big-endian, of
`SHA256("jspace-stage2b/v1|<run_mode>|bootstrap-v1")`. The full digest, namespace,
derived integer, NumPy version, generator, methods, and iteration count are
retained.

## 7. Threshold derivation

For selected layer order `[6, 13, 20, 26]`, the pilot derives:

```text
SPEC_MIN_EFFECT[l] = 0.5 * primary-floor correct-effect mean[l]
INTERACTION_MIN_EFFECT[l] = 0.5 * primary-floor interaction mean[l]
```

All eight source means must be defined, finite, and positive. The record retains
the source estimates, factor, floor, layer order, artifact identity, and derivation
code identity. Failure leaves both vectors unavailable and confirmation blocked.
The pilot never applies these values as gates and never emits a decision.

## 8. Artifact envelope

### Per-prompt/layer measurement

Required blocks:

- `prompt_sha256`, `category`, `layer`, `target_id`,
  `target_source: model_argmax`, and cryptographically bound
  `target_derivation`;
- `floor_scores` with both ratified floors and the output score;
- `donor_assignments` and `map_draws`;
- `factorized_scores` and `factorized_nta`.

No optional secondary-control fields are currently admitted; unknown fields are
rejected. The unratified wrong-layer proposal is absent from the executable
producer and contract. For a given recipient and donor-assignment ID,
`source_prompt_sha256` is invariant across all four selected layers.
`residual_sha256` remains layer-specific.

### Aggregate

Required blocks:

- schema and immutable content-addressing metadata;
- manifest/disjointness and partition provenance;
- model/lens/code/runtime identities;
- explicit authorization and successful preflight evidence;
- independently trusted authorization-record, canonical-notebook, and code-bundle
  identities supplied to validation outside the artifact;
- the exact ratified design identifiers and counts;
- all 80 per-prompt/layer compact measurement records;
- the resolved constant registry; and
- denominator-guard derivation evidence and floor-specific exclusion masks;
- validation evidence that the compact representation reconstructs all 64 logical
  combinations;
- per-prompt effects, category-balanced estimates, both interval methods, and
  complete stochastic provenance; and
- pilot threshold-derivation evidence or a fail-closed unavailable state.

No `gates` or scientific `decision` is admitted in a pilot artifact.

## 9. Validation invariants

A valid measurement artifact proves:

1. both floor identities are exact and both results plus their named difference are
   present;
2. donor and map collections each have exactly eight unique IDs and seeds;
3. every recipient→donor digest is present and excludes self-donation;
4. every broken map has a draw ID, seed, and hash;
5. the canonical pilot view, source manifest, category, layer, and complete 20×4
   locus coverage are exact;
6. every selected layer is present in `lens.source_layers`;
7. each recipient/donor assignment resolves to one source prompt across layers;
8. factorized key sets are exact, with no missing or extra row/column;
9. the unique-readout count is 81;
10. materialization produces 64 unique donor×map factorials; and
11. no donor/map dimension was averaged away before persistence;
12. the denominator guard recomputes from exactly 80 primary denominators using
    the linear 0.05 quantile and its source-vector digest matches;
13. exclusion masks and 18/20 plus 3/4-per-category coverage recompute exactly;
14. category-balanced point estimates and both 20,000-replicate interval methods
    recompute under the retained `PCG64` identity without layer pooling; and
15. threshold vectors recompute only from the positive defined primary-floor
    source means and no pilot gate or decision exists.

The offline validator can recompute prompt-pair linkage and score/NTA trees. It
checks content-hash format and cross-record identity but cannot recompute residual
or map content hashes because raw arrays are deliberately not retained. Runtime
hash generation remains an integration-smoke obligation.

## 10. Status

**RATIFIED**: measurement, denominator, crossing seeds, exclusion, coverage,
aggregation, interval, and pilot threshold-derivation rules.

**IMPLEMENTED and LOCALLY VERIFIED**: dual-floor endpoint, factorized materializer,
two-stage denominator derivation, deterministic seed identities, fixed
floor-specific exclusions, coverage, category-balanced effects, both ratified
20,000-replicate interval engines, threshold derivation, source-score producer,
aggregate producer, recursive validator, synthetic 20×4 artifact, deterministic
pilot bundle, and canonical notebook source contract.

**PILOT OBSERVED**: the superseding source freeze received independent PASS/GO,
the exact notebook/bundle/view identities received one-time authorization, and
the 20-prompt pilot completed on 2026-07-31. The retained artifact validated in
Colab. Primary-floor inference and threshold vectors are `undefined` because the
arithmetic category retained only two eligible prompts per layer; sensitivity-floor
effects are positive at all four layers. Confirmation remains unauthorized and
blocked.
