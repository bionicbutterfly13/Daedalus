# Stage 2b design baseline

Companion to `stage2-discrimination-baseline.md`. That file records what Stage 2
did; this one records what Stage 2b changes and why, so the skill can answer
questions about the current design without re-reading the spec tree.

Full specification: `specs/001-jspace-stage2b/`. Design document:
`j-space-lab/STAGE2B_DESIGN.md`. The pilot protocol is ratified and locally
implemented. The exact-hash-authorized 20-prompt pilot completed on 2026-07-31.
`THRESHOLDS_RATIFIED` correctly remains `False`: primary-floor category coverage
failed, threshold vectors were unavailable, and confirmation is blocked. The
consumed pilot authorization does not authorize a repeat.

## What changed from Stage 2, and why

Stage 2 returned ambiguity for two structural reasons, neither of which a larger
sample would have fixed.

**The endpoint had no ground truth.** Its primary metric measured how much two
readouts *differ*. A difference metric cannot separate an informative
disagreement from an arbitrary one, so the strongest available conclusion was
always non-identity. Stage 2b replaces it with normalized target attainment:

```
rank1(t, r) = (logits_r > logits_r[t]).sum() + 1
s(r)        = -log(rank1(t, r)) / log(V)
NTA_f(r)    = (s(r) - s(f)) / (s(output) - s(f))
```

The primary floor `f` is the decoded input embedding and the sensitivity floor is
the decoded layer-0 residual. Both are computed and retained; neither is selected
after observation. Stage 2's preregistration required separation from baselines
and the implemented gate omitted that clause. Defining the endpoint relative to
explicit floors makes that omission unrepresentable rather than merely forbidden.

**The controls confounded two factors.** Shuffled-layer moved the map and the
layer; mismatched-probe moved the probe and the layer. When both failed, the
cause was unrecoverable. Stage 2b crosses them:

| | fitted map | fit-broken map |
|---|---|---|
| **correct activation** | the instrument | does the fit matter? |
| **wrong activation** | does the input matter? | transport floor |

## Implementation notes worth carrying

- **The fit-broken map** is `(QU) S Vᵀ` with `Q` Haar-random orthogonal, which
  preserves the singular spectrum, operator norm, Frobenius norm, and
  conditioning while destroying correspondence. `numpy.linalg.qr` does **not**
  return a Haar-distributed `Q`; LAPACK fixes no sign convention on `R`'s
  diagonal, so the Mezzadri correction `q * sign(diag(r))` is required. It scales
  *columns*. A diagonal-sign test cannot detect a wrong-axis correction, because
  `q[i,i]` picks up `sign[i]` either way.
  The pilot decomposes each fitted map once, reuses that decomposition for its
  eight draws, and independently checks the full singular spectrum of every
  realized map. The artifact retains both spectrum digests and the maximum error
  under fixed implemented tolerances `rtol=1e-5`, `atol=1e-6`.
- **Wrong activations** are real residuals from different prompts, not random
  vectors. The pilot uses eight deterministic assignment identities
  `donor-0..donor-7`, each derived from its ratified SHA-256 namespace, and
  preserves every recipient→donor digest and realized residual hash.
- **Wrong-layer controls are not part of the executable pilot.** Their old
  distance, balancing, remainder, randomization, and sign rules remain deferred
  design history rather than dormant policy.
- **Target rank** is a comparison count, not a sort. `jlens.vis._ranks_of` chunks
  along the sequence dimension but still argsorts the full vocabulary per chunk,
  so it is the *reference* for FR-010's parity check, not the implementation.
- **Source identity is external evidence.** The trusted launch preparer hashes
  exact notebook and bundle bytes into a new exclusive directory. The artifact
  validator receives those identities separately; provenance strings carried by
  the artifact cannot authenticate themselves.

## Ratified pilot uncertainty

The primary interval resamples prompts with replacement within each of the five
categories and recomputes a category-balanced mean independently for each layer.
The sensitivity interval applies independent mean-one `Exp(1)` weights at prompt,
donor, and map levels. Both use 20,000 explicit
`Generator(PCG64(seed))` replicates and linear 0.005/0.995 quantiles. Neither
method pools layers, changes the floor-specific exclusion mask, or discards the
donor/map crossing before inference.

BCa/median/scipy text in older design notes is historical and not executable
authority. Non-finite replicate output remains `undefined`, never a measured
failure.

## Resolved estimand conflict

The ratified pilot reports both the correct-activation fitted-over-broken effect
and the correct-versus-wrong interaction. The pilot derives one four-layer
threshold vector from each positive primary-floor category-balanced mean but
emits no decision. Later confirmation requires both effects across every layer,
floor, and uncertainty method under one intersection-union conjunction.

## Pilot outcome carried forward

The layer-0 sensitivity floor produced positive correct effects and positive
correct-versus-wrong interactions at every selected layer under both ratified
99% interval methods. The decoded-input-embedding primary floor retained 18
prompts per layer but only two arithmetic-completion prompts, below the minimum
of three per category. Primary inference and threshold derivation are therefore
`undefined`.

The supported interpretation is prompt-floor dependence and instrument
fragility. It is not a robust Stage 2b pass, does not validate a consciousness
claim, and does not authorize confirmation. The content-addressed artifact
remains in Colab; public records cite its SHA-256 without transferring it.
