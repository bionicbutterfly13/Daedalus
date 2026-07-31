# Stage 2b pilot source note: 2026-07-31

## Source identities

| Source | SHA-256 |
|---|---|
| Canonical notebook | `9564236a1f49d7ffe2bea44f8b04be5a584c0ff9740b11dd1e563c93b8dba2fe` |
| Code bundle | `aeec8a76a426fa82f3fb96dc6700289a689fcb92fd9952da681fe03fe12dbef4` |
| Pilot view | `5bef8316f72682a628fc1240bf6068a91aa7c8a330377206cbd9145434b797e4` |
| Authorization record | `1af4ec95bf1c0f257fa5f559b7a91c939723cb7382eb0f5812ebc113d842b63c` |

## Verified execution record

The exact-hash-authorized 20-prompt pilot completed on one Tesla T4 with 14.563
GiB VRAM. It produced 80 prompt-layer records across four selected layers, both
prompt floors, and the complete 8-by-8 donor/map crossing. The in-memory validator
returned no errors. A final Colab-side audit independently recomputed the retained
artifact SHA-256 and confirmed 80 records. The denominator guard was
`0.3388633415411974`.

The primary `input_embedding_decoded` floor retained 18 eligible prompts per
layer but only two arithmetic-completion prompts, below the preregistered minimum
of three. Every required primary inference was therefore undefined. The
`layer0_residual_decoded` sensitivity floor retained 19 prompts with category
counts 4, 4, 4, 4, and 3. Its correct effects and fitted-map interactions were
positive at layers 6, 13, 20, and 26 under both two-sided 99% interval methods.

Threshold derivation was unavailable, no pilot pass/fail decision was emitted,
and confirmation remains blocked. The record supports operational success and
prompt-floor-dependent instrument behavior, not a robust Stage 2b result.

## Custody boundary

The retained artifact is
`jspace_discrimination_s2b_pilot_d138846e7a189ad4.json`, SHA-256
`d138846e7a189ad42955a5990e6d1a5c00553ba768cd838c5b6bf0334095daef`,
size 5.43 MiB. It remains in Colab and was not transferred. The full 200-prompt
manifest was already public, but the confirmation subset remained runtime-sealed
and unaccessed. The retained result artifact contains no raw prompt text,
activations, or full logits; the separately tracked stimulus and pilot-view inputs
remain part of the protocol record.

Repository publication is limited to the curated aggregates and provenance in
[`runs/stage2b-pilot-public-record-20260731/`](../../runs/stage2b-pilot-public-record-20260731/README.md).
