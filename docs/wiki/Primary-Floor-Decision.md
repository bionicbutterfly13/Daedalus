# Primary-Floor Decision

The Stage 2b pilot left one concrete question: why did the required
`input_embedding_decoded` floor retain only two of four arithmetic-completion
prompts when the protocol required three?

The answer is not yet known.

## What happened after the pilot

The lab froze a read-only diagnostic before inspecting prompt-level mechanism
data. It verifies the exact artifact and pilot-view hashes, recomputes the global
guard and both floor-status trees, and reports bounded prompt, tokenizer, target,
and denominator evidence. It contains no write, confirmation-input,
threshold-derivation, or prompt-selection path.

The diagnostic received independent GO, passed `495` J-space tests and `3553
passed, 12 skipped` repository-wide, passed six CI checks, and merged through
[PR #10](https://github.com/bionicbutterfly13/EvoScientist/pull/10).

Its first Colab execution stopped before reading the artifact. The current
runtime contained only `.config` and `sample_data`; both exact `/content` inputs
were absent. That state is consistent with a reset or replacement, but the
precise lifecycle event is unknown. The artifact was never transferred and was
not reconstructed or uploaded. Confirmation remained untouched.

That means we have a custody result, not a mechanism result.

## Five explanations still alive

| Explanation | Testable prediction |
|---|---|
| Prompt construction | Frozen arithmetic template families reproduce different primary-denominator distributions. |
| Tokenization | Preregistered length, boundary, or token-piece features predict exclusion on held-out prompts. |
| Target properties | Argmax identity, ties, or output-score geometry reproducibly predict small denominators. |
| Floor geometry | The same prompts remain close to the input-embedding floor but separated from the layer-0 residual floor. |
| Global guard interaction | Arithmetic prompts reproducibly concentrate near the fixed fifth-percentile boundary. |

Two excluded prompts cannot settle these explanations. A valid test needs a
new development set outside all 200 scientific prompts.

## The options

1. **Keep the primary floor and redesign only the development process.** Freeze
   template families and every candidate before eligibility measurement.
2. **Make both floors co-primary.** Require a defined, consistent result under
   both normalizations.
3. **Change the primary floor.** Do this only from an independent measurement
   argument, never because the sensitivity result was favorable.
4. **Replace normalized target attainment.** Define and validate a new estimand
   before viewing new scientific data.
5. **Stop this instrument path.** Preserve Stage 2b as an informative negative
   instrument-validation result.

The complete falsifiers, risks, disjoint-development requirements, and stop
conditions live in
`j-space-lab/STAGE2B_PRIMARY_FLOOR_OPTIONS_PACKET.md`.

## Boundary

No option is selected. No revised pilot, GPU run, artifact reconstruction,
threshold derivation, or confirmation access is authorized. The next action is a
scientific decision by Dr. Mani about the lawful evidence path, followed by a
choice among the five options only after that evidence exists.
