# Phase 0 Research: Stage 2b J-space discrimination

Resolves the unknowns that failed the initial Constitution Check on Principle II
(evidence proportional to risk). Every finding below was verified against source
at a pinned revision, not inferred from documentation or memory.

**Verification substrate**: `jacobian-lens` is checked out locally at
`/Volumes/Asylum/repos/jacobian-lens`, and `git rev-parse HEAD` there returns
`581d398613e5602a5af361e1c34d3a92ea82ba8e` — byte-identical to `JLENS_COMMIT` as
pinned in Stage 2's notebook. Findings R1, R3, R5, and R6 are therefore statements
about the exact code that would run, not about the library in general.

---

## R1 — Is the fitted Jacobian accessible as a dense matrix? *(was blocking)*

**Decision: Yes. The SVD-rotation control in FR-004 is constructible as designed.**

`JacobianLens.jacobians` is a public attribute, `dict[int, torch.Tensor]`, mapping
source layer to a dense `[d_model, d_model]` tensor
(`jlens/lens.py:26-27`, `:40`). It is stored fp32 on CPU — `__init__` casts every
incoming tensor with `.float()` regardless of the on-disk dtype. Allocation is
explicitly dense (`torch.zeros(d_model, d_model, dtype=torch.float32)`,
`jlens/fitting.py:149`, `:309`); nothing is factored, low-rank, or sparse.

So `J = lens.jacobians[layer]` passes straight to `torch.linalg.svd`, and
`J_broken = (Q @ U) @ diag(S) @ Vh` is a direct construction.

**Rationale for treating this as blocking**: Stage 2's notebook does not know this.
Cell 12 *probes* for an accessor across five candidate names and raises
`NotImplementedError` if none resolve, with a comment calling it "a documented
ASSUMPTION to confirm against jlens commit 581d398 before ratified execution."
Stage 2b's entire fit-broken arm depends on the answer, so authoring the notebook
before confirming it would have been building on the assumption the design
document itself flagged.

**Alternatives considered**: had the Jacobian been stored factored or been
inaccessible, FR-004's Haar-rotation control would have had to be replaced by the
secondary spectrum-matched Gaussian map (design §4.1), which is a weaker control
because it destroys input geometry as well as correspondence. Not needed.

**Consequence for the plan**: the probe-and-raise scaffolding from Stage 2 cell 12
should be replaced with a direct assertion on `lens.jacobians`, plus shape/dtype
checks. Probing for five names and taking whichever resolves is exactly the kind
of construct that makes a notebook unauditable.

---

## R2 — Is the `%pip` commit pin real, or a literal string? *(was blocking)*

**Decision: The pin is real. `{JLENS_COMMIT}` is interpolated before pip sees it.**

`%pip` is implemented by `PackagingMagics.pip` in
`IPython/core/magics/packaging.py`, and it carries no `@no_var_expand` decorator.
`InteractiveShell.run_line_magic` therefore applies `self.var_expand(line, ...)`
before dispatch, and `var_expand` uses `DollarFormatter`, a `string.Formatter`
subclass that performs standard `{foo}` substitution against the user namespace.
A second, redundant expansion happens inside `pip()` via `shell.system` →
`system_piped` → `var_expand`.

`!pip` expands identically; the difference between the two forms is which
interpreter runs pip (`%pip` uses `sys.executable -m pip`), not interpolation.

**Rationale for treating this as blocking**: if the pin had been literal, every
Stage 2 artifact recording `instrumentation.commit = 581d398...` would have been
recording a declaration that the install did not honour — a Principle V problem
in the *existing* record, not just a Stage 2b risk. It is not.

**Caveat**: this was verified from IPython's upstream source rather than from a
local install (IPython is not installed on this machine). The mechanism is
structural and stable, but the empirical confirmation is not available here. Stage
2b should not depend on the inference: **the preflight must assert the installed
`jlens` version at runtime**, reading it back from the environment rather than
trusting the install line. That converts an inference into a measurement and costs
one line. Recorded as a preflight requirement below.

---

## R3 — How is a Jacobian applied to a hand-supplied activation?

**Decision: `JacobianLens.transport(residual, layer)`, and reimplement its one-line
body for the broken map.**

```python
def transport(self, residual: torch.Tensor, layer: int) -> torch.Tensor:
    J_bar = self.jacobians[layer].to(residual.device)
    return residual @ J_bar.T
```
(`jlens/lens.py:135-143`)

It takes an arbitrary `[..., d_model]` tensor — no model, no prompt — which is
exactly what the 2×2 factorial needs, since three of the four cells apply a map to
an activation that did not come from the prompt being scored. `lens.apply`
internally calls it (`jlens/lens.py:212`), confirming it is the real primitive and
`apply` is prompt-running sugar over it.

`transport` takes no override-matrix argument. Two ways to use `J_broken`:
reimplement the single line (`residual @ J_broken.T`), or mutate
`lens.jacobians[layer]` before calling. **Choose reimplementation.** Mutating the
lens in place makes the object's state depend on execution order, and a later cell
reading `lens.jacobians[layer]` would silently get the broken map. That is the
same class of defect as Stage 2's dead constants: correct today, invisible when
wrong.

---

## R4 — Direct target rank without a full-vocabulary sort (FR-010)

**Decision: write it. `(logits > logits[target]).sum(-1)`. No library primitive does this.**

`jlens.vis._ranks_of` (`jlens/vis.py:98-125`) is the closest candidate and is the
one `tests/test_ranks_of.py` exercises, but it does **not** avoid the sort. It
chunks along the sequence dimension only (`jlens/vis.py:117`) and still calls
`logits[sl].argsort(dim=-1, descending=True)` over the full vocab per chunk
(`jlens/vis.py:119`), materializing a `[chunk_size, vocab]` rank tensor before
gathering the target columns. That is a memory optimization, not an algorithmic
one.

For a single target token, the rank is a comparison count, which is O(V) time and
O(1) extra memory instead of O(V log V) and a full rank buffer:

```python
rank0 = (logits > logits[target_id]).sum(-1)   # 0-indexed, strict
```

**Convention**: `_ranks_of` documents 0-indexed with rank 0 = top
(`jlens/vis.py:110`). Match it, then add 1 where the endpoint needs a 1-indexed
rank, since the design's `s(r,p,l) = -log(rank) / log(V)` requires rank ≥ 1 —
`log(0)` is undefined and a 0-indexed top token would produce it.

**Ties**: `_ranks_of` inherits whatever `torch.argsort` does with equal logits and
defines no tie rule. A strict `>` comparison count gives the *best* rank among
tied tokens; `>=` would give the worst. Ties at the top of a vocab-sized float
distribution are rare but not impossible after fp16 round-tripping. **Preregister
strict `>`** and record the convention in the artifact, so the choice is not
silently re-decided later.

**FR-010's verification requirement is now concrete**: assert the comparison-count
rank equals `_ranks_of`'s rank on a fixed probe vector. Both are cheap and one is
the reference implementation the library ships tests for. If they disagree, the
optimization changed the statistic, which is exactly what FR-010 exists to catch.

---

## R5 — dtype and device contracts (FR-009 §7.1)

**Decision: the design's dtype requirement is confirmed necessary, and the reason is
narrower than "good hygiene".**

`transport` moves the Jacobian to the residual's *device* but does **not** cast its
*dtype* (`jlens/lens.py:142`). Stored Jacobians are fp32. So a residual that is
bf16 or fp16 — which is what a model loaded in half precision produces — hits a
dtype-mismatched matmul. In the intended `apply` path this never surfaces, because
`select()` calls `.float()` first (`jlens/lens.py:206`). Stage 2b's factorial
bypasses `apply` for three of four cells and captures residuals directly, so the
guard `apply` provides is gone.

Confirmed contracts to assert at preflight:

| Contract | Value | Source |
|---|---|---|
| Jacobian shape | `[d_model, d_model]` dense | `jlens/lens.py:26-27`, `fitting.py:149` |
| Jacobian dtype in memory | `float32` (always, `.float()` in `__init__`) | `jlens/lens.py:40` |
| Jacobian device | CPU as stored; moved per-call by `transport` | `jlens/lens.py:142` |
| Jacobian dtype on disk | `float16` by default | `jlens/lens.py:52-58` |
| Residual before transport | MUST be cast `float32` | derived from `lens.py:142`, `:206` |
| `apply` return dtype/device | `float32`, CPU, forced | `jlens/lens.py:213`, `:215` |
| `unembed` return dtype/device | follows LM-head weight (e.g. bf16 on GPU) | `jlens/hf.py:166-174` |

Note the last two rows differ, and that difference is a live trap: `apply` forces
`.float().cpu()` on its outputs, but `unembed` called directly does not. Any
readout built by calling `unembed` on a transported residual comes back in the
model's native dtype on GPU, while readouts from `apply` come back fp32 on CPU.
Subtracting one from the other raises. This is the same class as Stage 2's lost
device-mismatch run, and it is why FR-009 requires decode parity be asserted on a
fixed probe rather than assumed.

**Also asserted**: `unembed` applies Gemma-style final logit softcapping when the
model config sets it (`jlens/hf.py:128-130`, `:172-173`). Qwen3-1.7B does not, but
the preflight should record whether softcapping is active rather than assume it is
off, since it would silently change every rank statistic.

---

## R6 — Cluster bootstrap with BCa intervals (design §5)

**Decision: `scipy.stats.bootstrap` with the index-array idiom. Cross-check with
percentile intervals. Do not treat a BCa interval as trustworthy without checking
it is finite.**

`scipy.stats.bootstrap` accepts `method='BCa'` (the default; validated case-
insensitively against `{'percentile', 'basic', 'bca'}`). There is no first-class
cluster parameter, but cluster resampling is expressible: pass `data=(cluster_ids,)`
— one entry per prompt, not per observation — and supply a non-vectorized
`statistic(idx)` that looks each resampled cluster id up in a closure-captured
table of that prompt's per-layer paired differences, concatenates with multiplicity,
and returns the median. Because scipy resamples the id array itself with
replacement, whole prompts enter or leave together with all their layer
observations. BCa's jackknife acceleration then leaves out one *cluster* at a time,
which is the correct cluster-level jackknife rather than an observation-level one.

**Known weakness, must be handled not ignored**: BCa's acceleration term is
estimated from the skewness of leave-one-out replicates, and the median is
discontinuous under leave-one-out — dropping a cluster either jumps the median to a
different order statistic or moves it not at all. With few clusters or many ties
this destabilizes the acceleration estimate, and scipy's own degenerate-data check
emits `DegenerateDataWarning` and returns NaN bounds when the bootstrap
distribution collapses.

Therefore: **the gate must fail closed on a non-finite interval.** A NaN lower
bound must never be read as "does not exclude zero" and quietly become a fail — it
is an undefined measurement and a different outcome from a measured null. Report
the percentile interval alongside BCa as a cross-check, and record both in the
artifact.

**Environment note**: scipy is not a dependency of this repo (`uv.lock` has no
scipy entry) and is not installed in `.venv`. It is a Colab-side dependency only.
Consequence for the plan: **the endpoint module's tests must not import scipy.**
Split the pure statistic (NTA, rank, denominator guard — testable in the repo
suite) from the interval machinery (scipy, exercised only in Colab). If the
bootstrap logic must be unit-tested, it needs a hand-rolled resampler over numpy,
which would then need its own equivalence check against scipy. Defer that: the
statistic is where the correctness risk lives, and the interval is where the
library is doing standard work.

---

## R7 — A fourth declared-but-unconsumed quantity in Stage 2, not in the audit

**Finding, not a decision. Flagged for Dr. Mani; no record amended here.**

The 2026-07-26 audit recorded three preregistration/implementation divergences:
the added-information gate's omitted clause, `INFERENCE_SEEDS` declaring seed `[1]`
that never ran, and specificity consuming one of three computed random-vector
seeds. Reading Stage 2's notebook against its own ratification checklist surfaces
a fourth of the same class:

`output_argmax_rank_in_jacobian` and `output_argmax_rank_in_other` are computed
per-locus and written into every per-prompt artifact, but **no gate reads them** —
not `reproduction_pass`, not `specificity_pass`, not `added_info_pass`, and not the
per-category aggregation. The only gate inputs are readout-versus-readout
quantities (`D`, `jaccard_top10`); nothing readout-versus-true-output reaches a
decision. Meanwhile the ratification checklist in the notebook's final markdown
cell lists "Downstream criterion: the model's own next-token output" as a ratified
item.

So Stage 2 recorded a downstream criterion as ratified, computed it, stored it, and
never let it touch a decision. This is precisely Principle IV ("declared means
consumed") and it is the same defect class the audit found three instances of.

**Two consequences, and they point in opposite directions:**

1. *Against the record*: the audit's count of three is an undercount, and the
   provenance still slightly overstates what was tested. Whether this warrants a
   second amendment to `STAGE2_DISCRIMINATION_REPORT.md` is Dr. Mani's call, not
   mine — amending a content-addressed scientific record is a ratification-class
   action and the constitution puts it with him. **Open item, not actioned.**
2. *For the design*: it is unusually strong support for the NTA endpoint. The
   machinery for scoring a readout against the model's own next-token target
   already exists in Stage 2's code and already runs. Stage 2b is not introducing a
   speculative new measurement; it is promoting a quantity Stage 2 already computed
   into the gate position its own checklist claimed it occupied.

It also raises the bar for FR-009's registry. A registry that only checks
*constants* would not have caught this, because the orphan here is a computed
*field*, not a declared constant. **The registry must cover both**: every declared
constant resolves to a consuming gate, and every artifact field that the
preregistration describes as decision-relevant resolves to a consuming gate.
Recorded as a contract requirement in `contracts/constant-registry.md`.

---

## R8 — Stage 2 constructs that must not be carried forward

Verified against Stage 2's notebook source, cell indices cited.

| Construct | Cell | Why it must change |
|---|---|---|
| Five-name probe for a transport primitive, `NotImplementedError` if none resolve | 12 | R1/R3 settle the names. Assert `lens.jacobians` and `lens.transport` directly. A probe that accepts whichever of five names exists cannot be audited against a pinned commit. |
| `SAME_RUNTIME_REPEATS = 2` | 4, 16 | Declared, echoed into the artifact, never used as a loop bound — the two repeats are hardcoded `lens.apply` call sites. Either drive the loop from it or delete it. |
| `INFERENCE_SEEDS = [0, 1]` | 4 | Seed 1 never ran. Either execute both or declare one. |
| `RANDOM_VECTOR_SEEDS`, three computed, one consumed | 4, 16 | Aggregate over all declared seeds or declare one. |
| `output_argmax_rank_*` computed, never gated | 16 | R7. In Stage 2b this becomes the endpoint rather than a stored orphan. |
| Single 18 KB measurement cell | 16 | Not reachable by any test. The direct cause of the four findings above being invisible until source review. Split per the plan's Structure Decision. |
| Manifest raw text never written to disk, only digested | 14 | Retained deliberately (Q8), but Stage 2b's manifest becomes a versioned in-repo JSON file so the digest has a checkable referent outside the notebook source. |

---

## Resolved-unknown summary

| ID | Unknown | Status | Blocking? |
|---|---|---|---|
| R1 | Dense Jacobian accessible for SVD | **Resolved — yes**, `lens.jacobians[layer]` | was blocking |
| R2 | `%pip` commit pin real | **Resolved — yes**, plus a runtime assert requirement | was blocking |
| R3 | Transport primitive for arbitrary vectors | **Resolved** — `transport(residual, layer)`; reimplement for broken map | no |
| R4 | Direct target rank | **Resolved — must be written**; verify against `_ranks_of` | no |
| R5 | dtype/device contracts | **Resolved** — table above; `unembed` ≠ `apply` in return convention | no |
| R6 | BCa cluster bootstrap | **Resolved** — scipy idiom; fail closed on non-finite interval; scipy is Colab-only | no |
| R7 | Fourth unconsumed quantity in Stage 2 | **Finding — open item for Dr. Mani**; widens the registry contract | no |
| R8 | Constructs not to carry forward | **Resolved** — table above | no |

**No NEEDS CLARIFICATION remain that block authoring.** The three non-delegable
parameters (Q3 target definition, Q5 specificity threshold, Q10 execution
authorization) are unresolved *by design* and block execution, not authoring.

**Constitution Check re-evaluation**: Principle II now passes. The two assumptions
that failed the initial gate were verified against the pinned commit rather than
deferred, and the one inference that could not be confirmed locally (R2, IPython
not installed) was converted into a runtime assertion instead of being carried as
an assumption.
