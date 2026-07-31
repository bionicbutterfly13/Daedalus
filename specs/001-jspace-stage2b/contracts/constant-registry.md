# Contract: constant registry (`declared means consumed`)

The registry makes configuration and derived-field consumption auditable. Presence
in the registry means IMPLEMENTED bookkeeping, not scientific ratification.

## Entry shape

```python
{
    "name": str,
    "kind": "constant" | "derived_field",
    "declared_value": Any,       # None/[] means deliberately unset
    "status": "ratified" | "unratified" | "implemented" | "derived",
    "consumed_by": list[str],
}
```

Every in-memory entry has a status, and emission copies it without inference.
`implemented` means a historical pin/default exists in software; it does **not**
retroactively claim scientific ratification. `derived` is reserved for derived
fields, whose `declared_value` is naturally unset.

## Checks

1. **Forward**: every entry has at least one real consumer;
   `orphaned_constant` otherwise.
2. **Reverse**: every value read by a consumer is registered;
   `unregistered_constant` otherwise.
3. **Referential**: every `consumed_by` name resolves exactly in the gate,
   `preflight:`, or `endpoint:` namespace; `phantom_consumer` otherwise.
4. **Ratification**: an implemented default or example MUST NOT be reclassified as
   ratified. Unset execution-critical values fail closed.
5. **Status consistency**: missing/unknown statuses raise
   `invalid_registry_status`; a derived field with a non-`derived` status, a
   constant marked `derived`, a ratified unset value, or an unratified substantive
   value raises `inconsistent_registry_status`.

## Ratified measurement entries

| Name | Ratified value | Consumer |
|---|---:|---|
| `TARGET_SOURCE` | `model_argmax` | `endpoint:target_rank1` |
| `PRIMARY_FLOOR_ID` | `input_embedding_decoded` | `endpoint:dual_floor_nta` |
| `SENSITIVITY_FLOOR_ID` | `layer0_residual_decoded` | `endpoint:dual_floor_nta` |
| `WRONG_ACTIVATION_ASSIGNMENT_COUNT` | `8` | `preflight:crossing_registry`, `endpoint:materialize_crossed_factorials` |
| `BROKEN_MAP_DRAW_COUNT` | `8` | `preflight:crossing_registry`, `endpoint:materialize_crossed_factorials` |
| `UNIQUE_READOUT_COUNT` | `81` | `endpoint:materialize_crossed_factorials`, validator |
| `LOGICAL_COMBINATION_COUNT` | `64` | `endpoint:materialize_crossed_factorials`, validator |
| `NTA_GUARD_QUANTILE` | `0.05` | `endpoint:derive_nta_min_denominator`, validator |
| `NTA_GUARD_QUANTILE_METHOD` | `linear` | `endpoint:derive_nta_min_denominator`, validator |
| `PILOT_MIN_LAYER_PROMPTS` | `18` | `endpoint:check_floor_layer_coverage`, validator |
| `PILOT_MIN_CATEGORY_PROMPTS` | `3` | `endpoint:check_floor_layer_coverage`, validator |
| `POINT_ESTIMATOR` | `equal_category_mean` | `endpoint:category_balanced_mean`, validator |
| `PRIMARY_UNCERTAINTY_METHOD` | `category_stratified_prompt_percentile` | `endpoint:stage2b_intervals`, validator |
| `SENSITIVITY_UNCERTAINTY_METHOD` | `prompt_donor_map_product_weight_percentile` | `endpoint:stage2b_intervals`, validator |
| `BOOTSTRAP_CI_LEVEL` | `0.99` | `endpoint:stage2b_intervals`, validator |
| `BOOTSTRAP_ITERATIONS` | `20000` | `endpoint:stage2b_intervals`, validator |
| `BOOTSTRAP_QUANTILE_METHOD` | `linear` | `endpoint:stage2b_intervals`, validator |
| `BOOTSTRAP_BIT_GENERATOR` | `PCG64` | `endpoint:stage2b_intervals`, validator |
| `PRODUCT_WEIGHT_DISTRIBUTION` | `Exp(1)` | `endpoint:stage2b_intervals`, validator |
| `THRESHOLD_DERIVATION_FACTOR` | `0.5` | `endpoint:derive_pilot_thresholds`, validator |
| `THRESHOLD_SOURCE_FLOOR` | `input_embedding_decoded` | `endpoint:derive_pilot_thresholds`, validator |

These entries describe the approved structure. They do not authorize measurement.

## Implemented numerical safeguards

The realized-map spectrum check uses two software tolerances:

| Name | Implemented value | Consumer |
|---|---:|---|
| `BROKEN_MAP_SPECTRUM_RTOL` | `1e-5` | `endpoint:singular_spectrum_evidence`, validator |
| `BROKEN_MAP_SPECTRUM_ATOL` | `1e-6` | `endpoint:singular_spectrum_evidence`, validator |

Their registry status is `implemented`, not `ratified`. They check the already
ratified spectrum-preservation requirement. Every realized map must pass the
componentwise allowance `atol + rtol * abs(fitted_singular_value)`; changing
either value changes source identity and requires a new freeze and review.

## Deterministic crossing vectors

```python
WRONG_ACTIVATION_ASSIGNMENTS = derive_seed_vector(
    ids=("donor-0", ..., "donor-7"),
    namespace="jspace-stage2b/v1|donor-assignment|<i>",
)
BROKEN_MAP_DRAWS = derive_seed_vector(
    ids=("map-0", ..., "map-7"),
    namespace="jspace-stage2b/v1|broken-map|<i>",
)
```

The derivation retains each literal namespace, zero-based index, full SHA-256,
first-eight-byte unsigned big-endian integer, and `PCG64` identity. IDs and seeds
must be unique. Donor records later bind recipient→donor digests; map records bind
realized map hashes.

## Derived and deferred values

`NTA_MIN_DENOMINATOR` ships with no numeric value and status `derived`. In pilot
mode its ratified derivation rule is execution-critical; the numeric value appears
only after exactly 80 primary denominators are retained and the 0.05 linear
quantile is computed.

`BOOTSTRAP_SEED` also has status `derived`. Its run-mode namespace is
`jspace-stage2b/v1|<run_mode>|bootstrap-v1`; the registry records the namespace
rule while the run artifact records the full digest and derived integer.

`SPEC_MIN_EFFECT` and `INTERACTION_MIN_EFFECT` ship as four-value derived outputs,
not pilot inputs. Their status becomes `derived` only after all eight primary-floor
source means are defined, finite, and positive. A pilot authorization record must
not supply them.

`MULTIPLICITY_RULE` is ratified as
`single_intersection_union_all_components_required` for later confirmation. It has
no pilot decision consumer. The later confirmation category minimum and all
execution authorizations remain unratified.

## Unratified wrong-layer proposal

Q7 remains design history only. Its distance, balancing, remainder-allocation,
randomization, and sign rules are not ratified, so no wrong-layer constants,
endpoint helpers, notebook branches, or artifact fields ship on the executable
pilot path. They may be reintroduced only after an explicit scientific decision
and a corresponding contract/test update.

## Authorization entries

`PILOT_AUTHORIZED`, `PILOT_PROTOCOL_RATIFIED`, and `THRESHOLDS_RATIFIED` ship false
in canonical executable source. The protocol itself is ratified in the governing
specification; the first two flags may become true only through the exact external
authorization record. `THRESHOLDS_RATIFIED` remains false throughout the pilot
because numeric vectors do not exist until a valid pilot artifact is independently
reviewed and locked for confirmation.
Preflight runs before measurement and fails closed. A pilot transition is supplied
only by the complete content-addressed record defined in
[preflight-api.md](./preflight-api.md); no source constant is edited.

## Endpoint/validator inventory additions

The consumer inventory includes at least:

```python
ENDPOINT_FNS += (
    "dual_floor_nta",
    "materialize_crossed_factorials",
    "build_fit_broken_maps",
    "singular_spectrum_evidence",
    "derive_stage2b_seed",
    "derive_nta_min_denominator",
    "crossed_prompt_effects",
    "check_floor_layer_coverage",
    "category_balanced_mean",
    "stage2b_intervals",
    "derive_pilot_thresholds",
)
PREFLIGHT_CHECKS += ("crossing_registry",)
```

The primary validator is an artifact consumer and must check the same 8, 8, 81,
and 64 invariants even if it is represented outside the Python registry namespace.

## Artifact obligation

The aggregate artifact records the resolved registry, declared values, status, and
consumers. A reader must be able to distinguish:

- ratified measurement structure;
- ratified statistical rules and deterministic derivations;
- implemented but unverified software; and
- derived numeric pilot outputs; and
- unratified execution or later-confirmation values.
