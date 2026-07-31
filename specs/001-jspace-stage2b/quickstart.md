# Quickstart: validate the recovered Stage 2b contract without running it

All executable scenarios are CPU-only. The validator checks the ratified pilot-view
file as identity/provenance input but does not run those prompts or access the
180-prompt holdout. Nothing here authorizes or accesses a model, lens, GPU, pilot
execution, or confirmation.

## Working tree

```bash
cd /Volumes/Asylum/archimedes-recovery-jspace-stage2b
```

Do not substitute `/Volumes/Asylum/archimedes`; the recovery changes are in the
worktree above.

## 1. Endpoint and lossless 8×8 materialization

```bash
uv run pytest tests/jspace/test_stage2b_endpoint.py -v
```

The test surface must establish:

- primary `input_embedding_decoded` NTA;
- sensitivity `layer0_residual_decoded` NTA;
- named `sensitivity_minus_primary` difference;
- floor-specific exclusion behavior;
- 8 donor IDs × 8 map IDs;
- exactly 81 unique readouts (`1 + 8 + 8 + 64`); and
- lossless reconstruction of 64 logical four-cell factorials.

A flat 64-record representation is not required.

## 2. Deterministic statistics and seeds

```bash
uv run pytest tests/jspace/test_stage2b_statistics.py -v
```

The pure statistical surface must establish:

- exact SHA-256 donor, map, and pilot-bootstrap seed identities;
- explicit `Generator(PCG64(seed))`, never implicit `default_rng`;
- one 0.05 linear guard from exactly 80 primary-floor denominators;
- no second model/lens pass after raw score retention;
- equal-weight per-prompt effects and category-balanced layer means;
- fixed exclusion masks, 18/20 layer coverage, and 3/4 per category;
- 20,000 finite primary and product-weight replicates with linear 99% bounds; and
- half-mean threshold vectors only from eight positive defined primary-floor
  source estimates.

## 3. Preflight fails closed without external authorization

```bash
uv run pytest tests/jspace/test_stage2b_preflight.py -v
```

Required failures include wrong crossing size, mismatched SHA-derived identities,
duplicate IDs/seeds, incomplete or tampered external authorization records,
unset protocol, and absent execution authorization.
The shipped vectors are deterministic:

```text
donor-0..donor-7 = first8(SHA256("jspace-stage2b/v1|donor-assignment|<i>"))
map-0..map-7     = first8(SHA256("jspace-stage2b/v1|broken-map|<i>"))
```

The canonical notebook never changes these values in source. A future authorized
launch must add the exact
`stage2b-pilot-authorization-<approved-sha256>.json` file named by a digest that
Dr. Mani approved independently of the file. The digest must match the filename
and exact bytes, the authority must be `Dr. Mani`, the pilot-view identity must be
exact, its notebook/bundle hashes must match, and the scope must keep confirmation
access and artifact transfer false. The notebook prompts for that approved digest
and opens only the corresponding path. The repository ships no such record.

Pilot preflight requires the ratified denominator derivation rule, not a numeric
guard. It rejects an authorization record that attempts to inject
`NTA_MIN_DENOMINATOR`, either effect-threshold vector, or
`THRESHOLDS_RATIFIED`.

Before any authorized upload, the trusted local launch preparer must hash the
canonical notebook itself and create a new exclusive launch directory:

```bash
uv run pytest tests/jspace/test_stage2b_pilot_launch.py -v
```

The test proves that a coordinated notebook-hash forgery is rejected, stale output
directories are refused, and only the exact notebook, bundle, pilot view,
authorization record, and generated launch manifest are copied. The runtime
notebook performs a second exclusive extraction and exact member/hash check before
importing any bundled code.

## 4. Dedicated synthetic harness

```bash
uv run pytest tests/jspace/test_stage2b_pilot_harness.py -v
```

The harness must use dedicated synthetic prompt digests disjoint from the real
manifest, exercise the same pure dual-floor and factorized crossing helpers, and
emit no scientific gate or decision.

## 5. Notebook source contract

```bash
uv run pytest tests/jspace/test_stage2b_notebook.py -v
```

This is a notebook CI/source-contract test. It must verify imports and calls to the
pure helpers, exact 81/64 guards, two-stage score retention, statistical
derivations, runtime provenance fields, deterministic crossing vectors, disabled
source authorization, and the external content-addressed record transition. Do not
claim notebook verification before observing this command's result.

## 6. Primary artifact validator

```bash
uv run pytest tests/jspace/test_stage2b_validator.py -v
```

The validator test must cover compact dual-floor records, exact key coverage,
81-readout counting, 64-combination reconstruction, exact 20×4 pilot-view coverage,
authorization/preflight/design envelopes, recomputed donor-pair digests, runtime
donor selection from the pinned population and ratified seeds, per-realized-map
spectrum evidence, independently supplied source identities, runtime content-hash
syntax/consistency, denominator derivation, exclusion/coverage,
category-balanced estimates, both deterministic interval procedures, threshold
derivation, and malformed variants. Raw residual/map bytes are not retained, so
their hash parity is a runtime attestation. Do not claim validator verification
before observing this command's result.

## 7. Documentation consistency

Search the specification directory for legacy count/condition claims, then confirm
that `81 unique`, `64 logical`, `input_embedding_decoded`, and
`layer0_residual_decoded` occur throughout the revised contract. Legacy claims
should be absent; the ratified terms should be present.

## 8. Excluded-input integration-smoke evidence

```bash
uv run pytest \
  tests/jspace/test_stage2b_integration_smoke.py \
  tests/jspace/test_stage2b_smoke_bundle.py \
  tests/jspace/test_stage2b_integration_smoke_notebook.py -v
```

These tests verify the fixed inputs are disjoint from scientific manifests, the
runtime-only report rejects scientific fields, the code bundle is deterministic,
and the canonical notebook is unexecuted, unauthorized, hash-bound, and unable to
transfer its report. They also execute the install-sentinel logic with a fake
installer, reject continuation in the installing process, and accept a distinct
post-restart process identity. They also require the install specification to
bind removal of optional Torchvision, execute that removal before the pinned
install, reject a post-restart runtime where Torchvision remains discoverable,
and retain `torchvision_state: "absent"` in the runtime-only report. Passing
these tests does not authorize opening Colab or allocating a GPU. The exact
authorization request is in
`contracts/integration-smoke-launch-packet.md`. The bounded smoke subsequently
completed on one Tesla T4: 81 readouts in 1.141 seconds and 4.074 GiB peak allocated
VRAM. Its 91.252-second full-pilot estimate is a projection. The report remains in
Colab, the transfer cell was not executed, and no pilot or confirmation input was
accessed.

## 9. Completed pilot evidence

The independently reviewed, exact-hash-authorized 20-prompt pilot completed on
2026-07-31. Its public summary is under
`runs/stage2b-pilot-public-record-20260731/`. The 5.43 MiB artifact was retained
in Colab at completion and is identified by SHA-256
`d138846e7a189ad42955a5990e6d1a5c00553ba768cd838c5b6bf0334095daef`.
It was never transferred. A later check found the artifact and pilot view absent
from the active `/content` runtime before the bounded mechanism audit could read
them. That state is consistent with a reset or replacement, but the precise
lifecycle event is unknown. The primary floor was undefined for insufficient
arithmetic-category coverage, while the sensitivity floor showed positive
effects at all layers. No threshold vectors or pilot decision were produced.

## What remains deliberately unavailable

No quickstart command authorizes a repeat pilot, reconstructs or transfers the
artifact, accesses confirmation inputs, or emits a scientific decision. The
completed pilot's one-time authorization is spent. Confirmation remains blocked
because the primary-floor threshold sources were undefined and the confirmation
per-category coverage minimum remains unratified.
