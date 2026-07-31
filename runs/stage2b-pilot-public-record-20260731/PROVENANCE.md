# Provenance and custody

This directory is a curated public record, not a copy or transformation of the
retained pilot artifact. Its values are limited to the verified execution facts,
coverage results, aggregate estimates, intervals, and decision state reviewed on
2026-07-31.

## Authorized source chain

| Source | SHA-256 |
|---|---|
| Canonical notebook | `9564236a1f49d7ffe2bea44f8b04be5a584c0ff9740b11dd1e563c93b8dba2fe` |
| Code bundle | `aeec8a76a426fa82f3fb96dc6700289a689fcb92fd9952da681fe03fe12dbef4` |
| Pilot view | `5bef8316f72682a628fc1240bf6068a91aa7c8a330377206cbd9145434b797e4` |
| Authorization record | `1af4ec95bf1c0f257fa5f559b7a91c939723cb7382eb0f5812ebc113d842b63c` |

The retained Colab artifact is named
`jspace_discrimination_s2b_pilot_d138846e7a189ad4.json`, has SHA-256
`d138846e7a189ad42955a5990e6d1a5c00553ba768cd838c5b6bf0334095daef`,
and was 5.43 MiB. It remains in Colab. Artifact transfer was not authorized or
performed, and the artifact is not present in this repository.

The in-memory validator returned no errors. A separate final Colab-side audit
recomputed the artifact hash and confirmed exactly 80 prompt-layer records.
`holdout_accessed` remained false. The retained result artifact contains no raw
prompt text, raw activations, or full logits, and confirmation thresholds were
not ratified. The separately tracked stimulus and pilot-view inputs remain part
of the public protocol record.

Because the primary-floor category-coverage gate failed, the public aggregates
must not be used to reconstruct a pilot pass, derive confirmation thresholds, or
claim a robust instrument. They record an operationally successful pilot with a
positive sensitivity-floor signal and an undefined preregistered robust result.
