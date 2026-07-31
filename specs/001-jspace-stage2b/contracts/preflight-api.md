# Contract: `stage2b_preflight`

Public surface of
`EvoScientist/skills/jspace-research-operations/scripts/stage2b_preflight.py`.

The module imports without `torch`, `jlens`, or a GPU. It accepts extracted metadata
and fails before measurement.

## Failure model

```python
class PreflightError(Exception):
    code: str
    detail: dict
```

Codes are stable and tests assert on `code`. The first failure raises; no warning
may substitute for an enforceable check.

## `check_tensor_contracts(observed) -> None`

Checks residual/Jacobian shape and dtype, readout device, decode parity, rank parity,
and unexpected softcapping from plain metadata. It also requires the two floor
identities to be exactly:

```text
primary     = input_embedding_decoded
sensitivity = layer0_residual_decoded
```

Representative codes: `shape_mismatch`, `dtype_mismatch`, `device_mismatch`,
`decode_parity`, `rank_parity`, `unexpected_softcapping`, `floor_identity`.

## `check_constant_registry(...) -> None`

Enforces forward, reverse, and referential registry checks from
[constant-registry.md](./constant-registry.md). Consumer names match exactly.
Implemented presence never promotes an unratified value.

Codes: `orphaned_constant`, `unregistered_constant`, `phantom_consumer`.

## `check_crossing_registry(donor_assignments, map_draws) -> None`

Requires:

- exactly 8 donor-assignment entries;
- exactly 8 broken-map-draw entries;
- non-empty unique string IDs in each collection; and
- unique integer seeds in each collection.

Codes:

| Failure | Code |
|---|---|
| count is not exactly 8 and 8 | `crossing_registry_size` |
| missing/empty/non-string ID | `crossing_registry_identity` |
| missing or non-integer seed | `crossing_registry_seed` |
| duplicate ID or seed | `crossing_registry_duplicate` |

This check validates a ratified structure; it does not choose IDs or seeds. The
shipped vectors are deterministically derived from the ratified namespaces and
must equal `donor-0` through `donor-7` and `map-0` through `map-7`. The check
recomputes every namespace digest and unsigned big-endian seed before accepting
the vectors.

## External pilot authorization record

`load_pilot_authorization_record(path, approved_record_sha256=...,
expected_pilot_view_sha256=..., observed_code_bundle_sha256=...)` accepts exactly
the file named by an independently supplied approved SHA-256:
`stage2b-pilot-authorization-<64-lowercase-hex>.json`. The approved digest must
equal both the filename digest and the exact file bytes. The record's authority
must be exactly `Dr. Mani`. Duplicate JSON keys, unknown fields, a different pilot
view, confirmation access, and artifact transfer all fail closed. A self-consistent
hash-named record that was not independently approved is insufficient.

The record has five exact top-level fields:

```jsonc
{
  "schema": "jspace-stage2b-pilot-authorization/v1",
  "run_mode": "pilot",
  "decision": {
    "authority": "Dr. Mani",
    "authorized_at_utc": "<second-resolution UTC RFC 3339>",
    "instruction": "<exact approval text>",
    "instruction_sha256": "<sha256 of instruction plus newline>"
  },
  "scope": {
    "pilot_view_sha256": "<canonical 20-prompt view digest>",
    "confirmation_access_authorized": false,
    "artifact_transfer_authorized": false
  },
  "source": {
    "notebook_sha256": "<independently approved canonical notebook SHA-256>",
    "code_bundle_sha256": "<independently approved code bundle SHA-256>"
  },
  "registry_updates": {
    "PILOT_PROTOCOL_RATIFIED": {
      "declared_value": true,
      "status": "ratified"
    },
    "PILOT_AUTHORIZED": {
      "declared_value": true,
      "status": "ratified"
    }
  }
}
```

`materialize_pilot_authorization(record, registry)` first verifies that every
pilot protocol rule and deterministic crossing vector in the shipped registry is
already ratified and exact. The external record may update only
`PILOT_PROTOCOL_RATIFIED` and `PILOT_AUTHORIZED`; it must not supply the
data-derived denominator guard, either effect-threshold vector, or
`THRESHOLDS_RATIFIED`. It copies rather than mutates the shipped registry and
returns the configuration consumed by `check_ratification`. The canonical
notebook contains no authorization record and remains blocked. Launch requires
adding one separately approved record and supplying its approved digest through
the notebook prompt. The loader verifies the authorization-record bytes, pilot
view, and observed code-bundle bytes. It does not accept a notebook hash typed by
the operator as evidence of the running notebook.

## Trusted pilot launch preparation

`prepare_stage2b_pilot_launch.py` is the external trusted source-binding surface.
It takes the canonical notebook, deterministic code bundle, exact pilot view, and
already approved authorization record. Before creating anything it:

1. hashes the exact notebook, bundle, pilot-view, and authorization-record bytes;
2. proves the notebook is valid unexecuted JSON with all shipped authorization
   and transfer flags false;
3. runs the authorization loader against the observed bundle and pilot view;
4. independently compares the record's notebook identity with the exact notebook
   bytes; and
5. refuses any output directory that already exists.

On success it copies only those four exact inputs plus a launch manifest into a
new exclusive directory and verifies every copied byte. The notebook extracts the
authorized bundle into a fresh `mkdtemp` directory, rejects unsafe or undeclared
archive members, verifies the exact extracted file set and hashes, and only then
adds its scripts directory to `sys.path`.

Artifact validation receives the three trusted source identities separately from
the artifact through `expected_source`. An artifact cannot authenticate itself by
coordinately rewriting its own provenance fields.

Representative codes: `authorization_record_approval`,
`authorization_record_authority`, `authorization_record_name`,
`authorization_record_unreadable`, `authorization_record_digest`,
`authorization_record_json`, `authorization_record_schema`,
`authorization_record_scope`, `authorization_record_decision`,
`authorization_record_pilot_view`, `authorization_record_boundary`,
`authorization_record_incomplete`, `authorization_record_registry`, and
`authorization_record_unratified`.

## Factorized measurement validation obligation

The preflight/validator boundary MUST establish:

- donor and map key sets exactly equal their registries;
- 1 shared + 8 map-indexed + 8 donor-indexed + 64 donor×map readouts;
- `unique_readout_count == 81`;
- lossless materialization of 64 unique `(donor_id, map_id)` factorials;
- recipient→donor digest on every donor assignment; and
- map hash on every broken-map draw.

This may be implemented in the primary validator rather than the import-light
preflight module, but the obligation cannot be omitted.

## `check_ratification(configuration, registry, mode) -> None`

Runs after structural checks and before measurement. `registry` is mandatory for
both modes; omission raises `registry_required` rather than falling back to an empty
or built-in registry. It fails if:

- the mode lacks explicit authorization;
- any required protocol section remains unratified;
- any execution-critical protocol rule remains unset;
- either crossing vector is empty or malformed;
- authorization vectors differ from their explicitly ratified registry entries; or
- the external authorization record is incomplete or out of scope.

In pilot mode, `NTA_MIN_DENOMINATOR`, `SPEC_MIN_EFFECT`, and
`INTERACTION_MIN_EFFECT` are valid only as unset derived values before measurement.
The denominator becomes numeric after the raw-score stage; the two effect vectors
become numeric only after valid pilot estimation. In confirmatory mode all three
must already be content-addressed and locked.

Both pilot and confirmatory modes pass the authorization/configuration's
`WRONG_ACTIVATION_ASSIGNMENTS` and `BROKEN_MAP_DRAWS` through
`check_crossing_registry`. Confirmatory authorization therefore cannot bypass the
8×8 vector check. Valid values in tests are real eight-entry vectors, never scalar
stand-ins.

The current canonical source remains intentionally blocked because authorization
flags are false and no external record ships with it. No GPU/model/lens/pilot or
confirmation path is authorized by the deterministic protocol registry.

Codes include `registry_required`, `pilot_not_authorized`,
`pilot_protocol_not_ratified`, `not_ratified`, `unset_constant`,
`unratified_constant`, `registry_value_mismatch`, and `invalid_constant`. Code names
do not imply that any particular inference method is approved.

## Manifest and environment checks

Manifest checks retain held-out digest disjointness, Stage 1 anchor exclusion,
manifest identity, prompt limits, and partition identity. Environment checks retain
pinned model/lens/code identities, installed lens provenance, Python/CUDA/device
requirements, and fail closed before measurement.

These checks are implementation safeguards, not execution authorization.

## Test obligations

CPU-only tests must make every failure code fire. Dedicated tests additionally
cover:

- pure dual-floor endpoint behavior;
- deterministic donor/map/bootstrap seed derivation;
- two-stage denominator derivation without a second model/lens pass;
- malformed 8×8 registries;
- incomplete factorized matrices;
- 81 unique readouts and 64 logical combinations;
- coverage, category-balanced estimation, both interval engines, and pilot
  threshold derivation;
- the synthetic harness;
- notebook source integration; and
- primary validator reconstruction.

Notebook and primary validator verification may be claimed only after their
respective tests have been freshly run and observed. No inference or execution
claim follows from these structural tests.
