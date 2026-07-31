# Stage 2b Pilot Result

## Plain-language result

The 20-prompt Stage 2b pilot completed on 2026-07-31. The software and runtime
did what they were authorized to do, and one preregistered sensitivity analysis
showed a positive fitted-map-specific signal at all four layers. The experiment
still did not produce a robust Stage 2b result because its required primary
analysis lacked enough eligible arithmetic-completion prompts.

A positive sensitivity result can be scientifically useful without being a
pass. Here, changing the prompt floor changed whether the analysis was even
defined. That directly shows prompt-floor dependence under this protocol.
Generalized instrument fragility is a plausible interpretation for the mechanism
audit to test. It is not permission to choose the more favorable floor after
seeing the data.

## What ran

- one Google Colab Tesla T4 with 14.563 GiB VRAM;
- 20 pilot prompts at layers 6, 13, 20, and 26;
- 80 prompt-layer records;
- decoded input-embedding primary floor and decoded layer-0 residual sensitivity
  floor;
- eight wrong-activation donors crossed with eight broken-map draws; and
- 81 unique factorized readouts per locus reconstructing all 64 logical
  crossings.

The in-memory validator returned no errors. A final Colab-side audit independently
recomputed the artifact SHA-256 and confirmed 80 records. The fixed denominator
guard was `0.3388633415411974`.

## Coverage determined the outcome

| Floor | Eligible prompts per layer | Category coverage | Inferential status |
|---|---:|---|---|
| Primary: `input_embedding_decoded` | 18 | Arithmetic completion had 2; minimum was 3 | Undefined at all four layers |
| Sensitivity: `layer0_residual_decoded` | 19 | 4, 4, 4, 4, 3 | Defined at all four layers |

Because all eight required primary-floor source means were not simultaneously
defined, finite, and positive, threshold derivation was unavailable. No pilot
pass/fail decision was emitted.

## Defined sensitivity-floor estimates

All intervals are two-sided 99% intervals. The first two interval columns use
the category-stratified prompt bootstrap. The final column uses the
prompt-by-donor-by-map product-weight sensitivity interval.

| Layer | Correct effect, 99% CI | Interaction, 99% CI | Crossed interaction 99% CI |
|---:|---:|---:|---:|
| 6 | 0.227463 [0.115254, 0.348893] | 0.145338 [0.022161, 0.276533] | [0.028890, 0.268815] |
| 13 | 0.619655 [0.514904, 0.725212] | 0.357396 [0.230835, 0.485453] | [0.215001, 0.503494] |
| 20 | 1.079363 [0.940763, 1.214811] | 0.865902 [0.723859, 1.005829] | [0.686540, 1.024303] |
| 26 | 1.421609 [1.248721, 1.574974] | 0.771675 [0.653027, 0.880720] | [0.628573, 0.889450] |

These sensitivity-floor intervals exclude zero. They do not repair or replace
the undefined primary-floor result.

## Evidence and custody

| Source | SHA-256 |
|---|---|
| Canonical notebook | `9564236a1f49d7ffe2bea44f8b04be5a584c0ff9740b11dd1e563c93b8dba2fe` |
| Code bundle | `aeec8a76a426fa82f3fb96dc6700289a689fcb92fd9952da681fe03fe12dbef4` |
| Pilot view | `5bef8316f72682a628fc1240bf6068a91aa7c8a330377206cbd9145434b797e4` |
| Authorization record | `1af4ec95bf1c0f257fa5f559b7a91c939723cb7382eb0f5812ebc113d842b63c` |

The retained artifact,
`jspace_discrimination_s2b_pilot_d138846e7a189ad4.json`, has SHA-256
`d138846e7a189ad42955a5990e6d1a5c00553ba768cd838c5b6bf0334095daef`
and was 5.43 MiB. It remains in Colab and is not in this repository. The full
200-prompt manifest was already publicly specified, but the confirmation subset
remained runtime-sealed and unaccessed. The retained result artifact contains no
raw prompt text, activations, or full logits; the separately tracked stimulus and
pilot-view inputs remain part of the public protocol record.

The repository contains a curated [public aggregate record](https://github.com/bionicbutterfly13/EvoScientist/tree/main/runs/stage2b-pilot-public-record-20260731)
and its provenance note, alongside the separately tracked protocol inputs.

## Decision boundary

- **Observed:** operational completion and a positive sensitivity-floor signal.
- **Undefined:** the preregistered robust primary-floor result and threshold
  derivation.
- **Not decided:** Stage 2b pilot pass/fail.
- **Blocked:** confirmation and downstream use of J-space as a validated
  instrument.

This pilot is publication-workflow stage E4, pilot observed, while remaining
scientific evidence class 1. It is not a functional, cognitive, global-workspace,
or consciousness result.
