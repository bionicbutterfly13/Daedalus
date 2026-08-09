# Stage 2b design baseline

Companion to `stage2-discrimination-baseline.md`. That file records what Stage 2
did; this one records what Stage 2b changes and why, so the skill can answer
questions about the current design without re-reading the spec tree.

Full specification: `specs/001-jspace-stage2b/`. Design document:
`sakshi notes/STAGE2B_DESIGN.md`. **Execution is not authorized** — ten
parameters await ratification and `THRESHOLDS_RATIFIED` ships as `False`.

## What changed from Stage 2, and why

Stage 2 returned ambiguity for two structural reasons, neither of which a larger
sample would have fixed.

**The endpoint had no ground truth.** Its primary metric measured how much two
readouts *differ*. A difference metric cannot separate an informative
disagreement from an arbitrary one, so the strongest available conclusion was
always non-identity. Stage 2b replaces it with normalized target attainment:

```
rank1(t, r) = (logits_r > logits_r[t]).sum() + 1     # strict >, 1-indexed
s(r)        = -log(rank1(t, r)) / log(V)
NTA(r)      = (s(r) - s(prompt_only)) / (s(output) - s(prompt_only))
```

`prompt_only` is 0 and `output` is 1 by construction. Stage 2's preregistration
required separation from both baselines and the implemented gate omitted that
clause; defining the endpoint in terms of them makes the omission
unrepresentable rather than merely forbidden.

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
- **The wrong activation** is a real norm-matched residual from a different
  prompt, not a random vector — Stage 2 showed a norm-matched random vector is
  beaten on every prompt, so it survives only as the sanity floor. The donor seed
  is derived per prompt from the full digest; a bare `default_rng(seed)` reset
  per call returns the same draw every time and concentrates every wrong
  activation on one donor.
- **Wrong-layer distances** are balanced within each `(layer, distance)` cell.
  Deriving the sign from a positional index couples direction to layer, because
  with four loci and two directions `index % 4` determines `index % 2`.
- **Target rank** is a comparison count, not a sort. `jlens.vis._ranks_of` chunks
  along the sequence dimension but still argsorts the full vocabulary per chunk,
  so it is the *reference* for FR-010's parity check, not the implementation.

## The cluster bootstrap

`scipy.stats.bootstrap` has no cluster parameter. The idiom:

```python
indices = np.arange(len(prompt_keys))          # one entry PER PROMPT
def statistic(idx):                             # non-vectorized
    return float(np.median(table[idx.astype(int)]))
bootstrap((indices,), statistic, method="bca", ...)
```

Resampling the index array draws whole prompts with replacement, and BCa's
jackknife then leaves out one *cluster* at a time rather than one observation.

**The table holds one value per prompt at one layer.** The bootstrap runs once
per layer; it never concatenates across layers, which would pool depth into the
gate — the defect the design forbids for absolute NTA, one level down and harder
to see because each individual difference is already within-layer.

**BCa is unstable for a median.** The acceleration term comes from the skewness
of leave-one-out replicates, and a median jumps discontinuously under
leave-one-out. scipy returns NaN bounds on a degenerate bootstrap. A gate reading
a NaN bound must report `undefined`, never `fail`: an absent measurement and a
measured null are different results, and collapsing them lets a failed
computation be published as evidence of no effect. Every BCa interval is recorded
alongside a percentile cross-check for exactly this reason.

## The one open design conflict

`STAGE2B_DESIGN.md` defines H1's statistic two incompatible ways. §2 and §6 say
the simple paired difference at the correct activation; §4 says the 2×2 main
effect of map. They coincide only if the interaction is zero, and §4 predicts a
nonzero one.

The implementation gates on the §2/§6 form and reports the main effect as
descriptive. Reasoning and the open question are in
`specs/001-jspace-stage2b/research.md` R9 and open item 6 of
`.specify/memory/project-state.md`. Which reading was intended is Dr. Mani's
call, not an implementation detail.
