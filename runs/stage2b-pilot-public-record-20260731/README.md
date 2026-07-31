# Stage 2b pilot public record

On 2026-07-31 the exact-hash-authorized 20-prompt J-space Stage 2b pilot
completed on one Google Colab Tesla T4. Operationally, the run succeeded: it
produced 80 prompt-layer records across layers 6, 13, 20, and 26, completed both
prompt floors and the full 8-by-8 donor/map crossing, returned an empty validator
error list, and passed a final Colab-side SHA-256 and record-count audit.

Scientifically, the result is informative but inconclusive. The preregistered
primary floor retained 18 eligible prompts per layer, yet only two were in the
arithmetic-completion category. The protocol required at least three per
category, so every primary-floor inference was undefined. The sensitivity floor
retained 19 prompts with category counts 4, 4, 4, 4, and 3; its fitted-map
interaction was positive at every layer under both 99% interval methods.

| Layer | Correct effect, 99% CI | Interaction, 99% CI | Crossed interaction 99% CI |
|---:|---:|---:|---:|
| 6 | 0.227463 [0.115254, 0.348893] | 0.145338 [0.022161, 0.276533] | [0.028890, 0.268815] |
| 13 | 0.619655 [0.514904, 0.725212] | 0.357396 [0.230835, 0.485453] | [0.215001, 0.503494] |
| 20 | 1.079363 [0.940763, 1.214811] | 0.865902 [0.723859, 1.005829] | [0.686540, 1.024303] |
| 26 | 1.421609 [1.248721, 1.574974] | 0.771675 [0.653027, 0.880720] | [0.628573, 0.889450] |

The pilot therefore reaches publication-workflow stage E4 (pilot observed) while
remaining scientific evidence class 1. It directly establishes prompt-floor
dependence under this protocol; broader instrument fragility is an inference to
test, not an observed fact. It does not establish a robust Stage 2b result. Threshold
derivation was unavailable, no pilot pass/fail decision was emitted, and
confirmation remains blocked and unauthorized. This is not evidence of a global
workspace or consciousness.

The machine-readable aggregates are in
[`pilot-result-summary.json`](pilot-result-summary.json). The
source and custody boundary is recorded in [`PROVENANCE.md`](PROVENANCE.md).
