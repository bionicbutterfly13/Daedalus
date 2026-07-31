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
(`jlens/lens.py:26-27`, `:40`). `__init__` casts every incoming tensor with
`.float()` regardless of the on-disk dtype, so fp32 in memory is guaranteed.

Device is CPU **in practice, not by construction**: `load()` uses
`torch.load(..., map_location="cpu")` (`jlens/lens.py:66-79`) and nothing in
`lens.py` or `fitting.py` moves the dict elsewhere, but `__init__` calls only
`.float()`, never `.cpu()`. A `JacobianLens` constructed directly from CUDA tensors
would hold CUDA tensors. Assert the device at preflight rather than relying on the
load path. Allocation is
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

For a single target token, the rank is a comparison count — O(V) time instead of
O(V log V), and one boolean temporary instead of a full int64 rank buffer. It is
**not** O(1) memory; `(logits > x)` materializes V bytes before the reduction. The
saving is the sort and the `[chunk, vocab]` scatter buffer, which is what actually
hurts at vocab 151936:

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

## R6 — Cluster bootstrap with BCa intervals (superseded historical proposal)

**Historical proposal, not current implementation authority:** use
`scipy.stats.bootstrap` with the index-array idiom, cross-check percentile
intervals, and reject non-finite BCa output. Dr. Mani superseded this proposal on
2026-07-30 by ratifying category-stratified prompt percentile intervals as primary
and prompt×donor×map product-weight percentile intervals as sensitivity, both
using 20,000 explicit `Generator(PCG64(seed))` replicates and linear 99% bounds.

`scipy.stats.bootstrap` accepts `method='BCa'` (the default; validated case-
insensitively against `{'percentile', 'basic', 'bca'}`). There is no first-class
cluster parameter, but cluster resampling is expressible: pass `data=(cluster_ids,)`
— one entry per prompt, not per observation — and supply a non-vectorized
`statistic(idx)` that looks each resampled cluster id up in a closure-captured
table and returns the median of the values it collects, with multiplicity. Because
scipy resamples the id array itself with replacement, whole prompts enter or leave
together. BCa's jackknife acceleration then leaves out one *cluster* at a time,
which is the correct cluster-level jackknife rather than an observation-level one.

**The table holds one value per prompt, at one layer.** The bootstrap runs once per
layer in `SELECTED_LAYERS`; the table for a given run maps prompt → that prompt's
paired difference *at that layer*. It does not map prompt → a vector across layers,
and the statistic never concatenates across layers. Doing so would pool depth into
the gate — the same defect the design forbids for absolute NTA, one level down and
harder to see, because each individual difference is already within-layer.

**Known weakness, must be handled not ignored**: BCa's acceleration term is
estimated from the skewness of leave-one-out replicates, and the median is
discontinuous under leave-one-out — dropping a cluster either jumps the median to a
different order statistic or moves it not at all. With few clusters or many ties
this destabilizes the acceleration estimate, and scipy's own degenerate-data check
emits `DegenerateDataWarning` and returns NaN bounds when the bootstrap
distribution collapses.

The historical proposal therefore required a non-finite interval to remain
undefined rather than collapse into a measured null. That principle survives:
the current interval implementation requires all 20,000 replicate statistics to
be finite or reports the layer-floor estimand as undefined.

**Statistic is per layer, not pooled.** The lookup table holds one prompt's paired
differences *at a single layer*, and the bootstrap runs once per layer in
`SELECTED_LAYERS`. Concatenating a prompt's differences across layers into one
median would pool depth into the gate — the same defect the design forbids for
absolute NTA, one level down, where it is harder to see because each individual
difference is already within-layer. An earlier draft of this section described
exactly that concatenation; it was wrong.

**Environment note**: scipy is not a dependency of this repo (`uv.lock` has no
scipy entry). The ratified interval engines are implemented with NumPy and do not
depend on scipy or BCa.

Earlier drafts claimed scipy-backed tests and implementation resolved this item.
That claim remains superseded. The current implementation and tests live in
`stage2b_statistics.py` and `tests/jspace/test_stage2b_statistics.py`; the exact
methods, units, iteration count, seed, confidence rule, and later global
intersection-union claim are now ratified in `spec.md`.

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
| R6 | BCa cluster bootstrap | **Superseded proposal** — no method or implementation ratified | blocks inference, not measurement authoring |
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

---

## R9 — What H1's statistic actually is *(design-document conflict, resolved for implementation, flagged for ratification)*

`STAGE2B_DESIGN.md` defines H1 two incompatible ways, and the difference is not
cosmetic — it changes the number the gate reads.

| Section | H1's statistic |
|---|---|
| §2, hypotheses | "the prompt-clustered median paired difference `NTA(jacobian) − NTA(fit_broken_same_layer)`" |
| §6, decision rule table | "cluster-bootstrap median of `NTA(jac) − NTA(fit_broken)`" |
| §4, factorial | "**Main effect of map** — averaging over activation correctness, does the fitted map beat the broken one? **This is H1.**" |

§2 and §6 describe the **simple effect at the correct activation**: one paired
difference per prompt between the top-left and top-right cells of the 2×2.

§4 describes the **main effect of map**: the average of both map-broken contrasts,
the one at the correct activation *and* the one at the wrong activation.

### These coincide only when the interaction is zero

```
simple effect  = NTA(correct, fitted) − NTA(correct, broken)
main effect    = ½[NTA(correct, fitted) − NTA(correct, broken)]
               + ½[NTA(wrong,   fitted) − NTA(wrong,   broken)]
```

The design does not merely permit an interaction, it **predicts one**. §4: "the
signature of a real instrument is that breaking the map costs more when the
activation is correct." If that holds, the second bracket is smaller than the
first, and the main effect is systematically *below* the simple effect.

So gating H1 on the main effect would dilute the very quantity the study is trying
to detect, using cells where the design expects the effect to be weakest. A real
instrument would be measured against a threshold partly determined by how it
behaves on activations it was never given. That is a worse test, and it would fail
for a reason unrelated to the instrument's quality.

### Decision for implementation

**Gate on the §2/§6 form** — the simple paired difference at the correct
activation. Reasons, in order:

1. Two of three sections say it, and one of those is the decision-rule table,
   which is the operative specification. §4's claim appears in a paragraph
   explaining what the factorial *yields*, not in a gate definition.
2. It is the form already carried into `spec.md`, `data-model.md` §4, and
   `contracts/constant-registry.md`.
3. The dilution argument above: under the design's own stated expectation, the
   main effect is the weaker and less interpretable of the two.

**Compute the main effect anyway and report it under `descriptive`**, alongside
the interaction estimate. It is genuinely informative — a large main effect with
no interaction would say something different about the instrument than a large
simple effect with a strong interaction — and computing it costs nothing once the
2×2 cells exist. It just does not gate.

### Not resolved here

Which definition Dr. Mani *intended* is his call, and it is a scientific question
about what H1 means rather than an implementation detail. If §4 is the intended
reading, `SPEC_MIN_EFFECT` will need to be ratified against a different quantity
than the one the decision table names, and the pilot in Q6 would have to estimate
the main effect's scale rather than the simple effect's.

Recorded as an open scientific item. **Superseded implementation note:** recovery
retains both descriptive quantities but ships no `gate_record` or decision rule.

---

## R10 — The design can pass while its own signature of a real instrument is absent

**Historical finding from T051, the pre-implementation adversarial design
cross-check.** It blocks scientific gate/decision authoring, not the recovered
measurement-only notebook.

`STAGE2B_DESIGN.md` §4 states the criterion plainly:

> the signature of a real instrument is that breaking the map costs more when
> the activation is correct. If breaking the map costs the same regardless of
> whether the input is the right one, the map is not doing input-specific work.

That quantity is the **interaction**. And the design then declines to gate it —
§4 says it is "reported and interpreted but **not** a gate in this stage",
because no pilot estimate exists and a third preregistered threshold on an
unmeasured quantity would be guessing. **Superseded implementation note:** controlled
recovery ships the descriptive interaction but no `compose_decision` function.

**Historical consequence under the draft rule**: Stage 2b could return `pass` — reproduction holds, H1's simple
effect clears `SPEC_MIN_EFFECT` with an interval excluding zero, H2 holds — while
the interaction is null, negative, or unresolved. Under the design's own words,
that is a result in which *the map is not doing input-specific work*. The study
would report a pass whose headline claim is the one thing it did not establish.

This is Stage 2's defect in a new form, and specifically it is a **Principle IV
violation at the design level**: a quantity the preregistration describes as
decision-relevant — "the signature of a real instrument" — that no gate reads.
The constant registry was built to make that impossible for constants and
computed fields. It cannot catch it here, because the omission is in the decision
rule itself. Controlled recovery removes that implementation hazard by shipping no
scientific gate composition or pass/fail/ambiguity rule; the scientific choice
remains open.

### Why deferring the threshold does not resolve it

The reason for not gating the interaction is sound in isolation: Stage 2 set a
margin without a pilot and then could not say whether its controls were
inseparable or merely under-resolved at that value. Repeating that in a new unit
would be the same mistake.

But the fix for "no pilot estimate" is the Q6 pilot, which the design already
proposes for `SPEC_MIN_EFFECT` and `NTA_MIN_DENOMINATOR`. There is no reason the
interaction cannot join them. Leaving it ungated is not the conservative choice —
it is the choice that lets a weaker result be reported under a stronger claim.

### Three options, none of which I should pick

1. **Gate the interaction**, with its threshold derived from the Q6 pilot
   alongside the other two. Makes the pass mean what §4 says it means. Costs a
   third preregistered constant and a stricter bar.
2. **Narrow the pass claim.** Keep the interaction descriptive, and state in the
   preregistration that a pass establishes the fitted map beats a spectrum-matched
   broken map *at the correct activation* and asserts nothing about input-specific
   work. Cheapest, and honest, but concedes the headline.
3. **Make H1 conjunctive over the simple effect and a nonzero interaction**,
   without a magnitude threshold on the latter — only that its interval excludes
   zero. A middle path that needs no pilot estimate for the interaction.

This is a decision about what H1 *means*, so it sits with Q3 and Q5 rather than
with implementation. Recorded as open item 7.

## R11 — Three smaller design gaps from the same review

**Historical gap, now superseded: `prompt_only` was operationally undefined.** It is the endpoint's floor and one
of the two anchors that make FR-002's omission unrepresentable, but nothing in
the spec tree says how the prompt-only logits are constructed. `nta()` simply
accepts `s_prompt_only` from its caller. Stage 2's notebook had an
`input_embedding_residual` helper; whether Stage 2b uses that, a zero-transport
readout, or something else was unspecified. The ratified recovery contract now uses
`input_embedding_decoded` as the primary floor and
`layer0_residual_decoded` as the sensitivity floor.

**The fit-broken map is narrower than the claim it supports.** `(QU)ΣVᵀ`
preserves the fitted *input* basis `V` and Haar-rotates the *output* basis
against a fixed unembedding. Beating it shows the fitted output orientation
matters relative to a random one; it does not show that the full specific fit
beats any layer-sized transport. A pass would not rule out generic
residual-stream/LM-head coordinate alignment, nor another model-structured but
unfitted operator. The design's secondary spectrum-matched Gaussian control
(§4.1) destroys both bases and would speak to this — worth promoting from
"reported alongside" to a named comparison.

**The wrong activation controls magnitude but not content.**
`select_wrong_activation` excludes the recipient and draws uniformly among the
rest, matching norm only. A donor sharing the recipient's target or category can
score well against the recipient's target, which inflates the wrong-activation
fitted cell and attenuates the interaction. Since the wrong-activation cells do
not gate, this contamination could survive an overall pass unnoticed — and it
attacks precisely the quantity R10 is about. A cheap mitigation is to exclude
donors whose own target token equals the recipient's, which is checkable at
preflight from data the run already has.

## R12 — Content hashes are runtime attestations, not offline recomputations

The retention contract forbids persisting raw activations and full broken-map
arrays. An offline validator that receives only `residual_sha256` or map `sha256`
cannot recompute those digests from absent bytes. Treating a 64-character string as
proof of tensor content would overstate what was validated.

The recovered boundary is explicit:

- the runtime producer hashes contiguous arrays with
  `dtype-shape-bytes-sha256-v1` before artifact construction;
- the offline validator recomputes recipient→donor hashes and all dual-floor
  score/NTA trees;
- it validates residual/map hash syntax, donor/map identity, run-wide seed
  consistency, and same-layer map-hash consistency across prompts; and
- the separately authorized real-runtime integration smoke must exercise live
  content-hash generation before pilot authorization.

Persisting raw tensors solely to make offline hash recomputation possible would
violate the stronger retention constraint. The correct evidence is runtime parity
plus an immutable sparse artifact, not fabricated offline certainty.

## R13 — Colab binary-package replacement requires a fresh Python process

The first authorized excluded-input smoke installed the exact pinned package set
successfully, then failed before model download at
`transformers.AutoTokenizer.from_pretrained`:

```text
ImportError: cannot import name '_center' from 'numpy._core.umath'
```

The live Colab process had already imported components from its preinstalled NumPy
before `%pip` replaced NumPy with `2.5.1`. The filesystem package identity was
correct, but the process module graph was mixed. Package-version checks alone
therefore cannot establish a coherent binary runtime.

The repaired contract uses a canonical install-specification digest and records
the installing process as `pid:/proc/self/stat-starttime`. Before any NumPy,
Torch, Transformers, or Jacobian Lens import, the notebook requires the current
process identity to differ. Re-running cells in the same process cannot satisfy
that check. The launch procedure uses Colab's explicit
**Runtime → Restart session** action and records
`fresh_process_after_install: true` in the runtime-only report.

This does not change package pins, scientific inputs, seeds, estimands, gates, or
retention. It closes a runtime-coherence gap exposed before any scientific
measurement.

## R14 — A text-only runtime must remove incompatible optional Torchvision

The second exact-hash-authorized smoke passed the fresh-process and immutable
identity gates, then stopped during `AutoModelForCausalLM` class resolution:

```text
RuntimeError: operator torchvision::nms does not exist
ModuleNotFoundError: Could not import module 'Qwen3ForCausalLM'.
```

The failure occurred before model-weight load. Colab retained Torchvision 0.26
while the smoke installed Torch 2.13. PyTorch's official compatibility matrix
pairs Torch 2.13 with Torchvision 0.28 and Torch 2.11 with Torchvision 0.26:
<https://github.com/pytorch/vision/blob/main/README.md#installation>.

The pinned Jacobian Lens commit declares dependencies on Torch, Hugging Face Hub,
Transformers, and NumPy, but not Torchvision:
<https://github.com/anthropics/jacobian-lens/blob/581d398613e5602a5af361e1c34d3a92ea82ba8e/pyproject.toml>.
Transformers scopes Torchvision to vision-specific import paths; the Stage 2b
smoke loads the text-only `Qwen/Qwen3-1.7B` causal language model.

**Decision, 2026-07-30:** Dr. Mani approved removing Torchvision rather than
adding the compatible 0.28 vision wheel or changing the pinned Torch version.
The install specification must bind the removal list, uninstall Torchvision
before installing the pinned stack, require a fresh process, and then fail unless
both distribution metadata and import resolution prove Torchvision absent before
Transformers is imported. The retained runtime report must record
`torchvision_state: "absent"`.

This is an engineering compatibility decision only. It does not change model,
lens, scientific inputs, seeds, estimands, thresholds, gates, retention, or pilot
authorization.

## R15 — Two-stage denominator calibration

**Decision:** derive one `NTA_MIN_DENOMINATOR` during the authorized pilot from the
0.05 linear quantile of the 80 primary-floor denominators, then compute both-floor
NTA from retained scores without another model/lens pass.

**Rationale:** Stage 2b needs a numeric guard against unstable normalization, but
choosing it without pilot scale information repeats Stage 2's arbitrary-margin
problem. The raw score tuple already contains everything needed after the guard is
derived. Separating measurement from normalization prevents the pilot from
silently selecting readable loci during collection and avoids a second stochastic
or hardware-dependent forward path.

**Alternatives considered:** a fixed author-chosen epsilon was rejected as
unscaled; a sensitivity-floor-derived guard was rejected because it would make the
two floors govern different inclusion populations; a second model pass was
rejected because retained scores are sufficient and should reproduce exactly.

## R16 — Crossed uncertainty without layer pooling

**Decision:** use category-stratified prompt resampling as the primary uncertainty
procedure and a prompt×donor×map product-weight bootstrap as required sensitivity,
independently for each layer.

**Rationale:** prompts are the scientific sampling unit, while donor assignments
and broken maps are repeated-control dimensions. Primary prompt resampling keeps
the claim anchored to prompt variation and preserves the five preregistered
categories. Product weights retain the crossed structure and expose conclusions
that depend on a small collection of donors or maps. This applies multiway and
crossed-array bootstrap ideas; it does not imply that eight draws make variance
components asymptotically well estimated.

**Alternatives considered:** treating all 64 cells as independent was rejected
because it creates pseudoreplication; pairing donors and maps was rejected because
it confounds their effects; pooling four layers was rejected because layer is a
required claim dimension; a single hierarchical interval was rejected because it
would hide disagreement between prompt-primary and crossed-sensitivity views.

References:

- Cameron, A. C., Gelbach, J. B., & Miller, D. L. (2011). Robust inference with
  multiway clustering. *Journal of Business & Economic Statistics, 29*(2),
  238–249. https://doi.org/10.1198/jbes.2010.07136
- Owen, A. B. (2007). The pigeonhole bootstrap. *The Annals of Applied
  Statistics, 1*(2), 386–411. https://doi.org/10.1214/07-AOAS122
- Owen, A. B., & Eckles, D. (2012). Bootstrapping data arrays of arbitrary order.
  *The Annals of Applied Statistics, 6*(3), 895–927.
  https://doi.org/10.1214/12-AOAS547

## R17 — Coverage and category-balanced estimands

**Decision:** exclude a whole prompt-layer for the affected floor, never impute,
fix the exclusion mask across replicates, require at least 18/20 eligible prompts
per layer and 3/4 in each category, and compute an equal mean of the five category
means.

**Rationale:** one denominator governs every readout within a
prompt-layer-floor. Selectively retaining cells would make the factorial
comparison depend on which condition happened to be numerically stable.
Category-balanced means preserve the original stratification when exclusions make
raw eligible counts unequal.

**Alternatives considered:** cellwise exclusion was rejected because it destroys
paired factorial structure; zero imputation was rejected because zero is a
scientific value; renormalizing across all eligible prompts was rejected because a
category with fewer retained prompts would lose influence after the design had
given categories equal weight.

## R18 — Reproducible interval engine and seeds

**Decision:** use 20,000 replicates, two-sided 99% percentile intervals with
linear quantiles, explicit NumPy `Generator(PCG64(seed))`, and SHA-256-derived
unsigned big-endian seeds for bootstrap, donors, and maps.

**Rationale:** the generator family must be explicit because `default_rng` selects
a library default rather than naming the protocol's bit generator. The namespace,
full digest, first-eight-byte integer, NumPy version, replicate count, and quantile
method together make the stochastic procedure inspectable and repeatable.
Requiring every replicate to be finite prevents a percentile interval from
silently dropping failed calculations.

**Alternatives considered:** integer literals were rejected as unaudited choices;
implicit `default_rng` was rejected because its selection is not the stated
contract; BCa was rejected for this pilot because the crossed product-weight
procedure already adds a separate sensitivity engine and the small
category-stratified sample makes further correction machinery harder to audit than
the fixed percentile rule.

## R19 — Pilot-derived thresholds and the later global claim

**Decision:** derive four-layer correct-effect and interaction threshold vectors
as one half of their positive primary-floor pilot means. The pilot reports and
locks these vectors but emits no scientific decision. A later confirmation claim
is one intersection-union conjunction across every layer, both floors, both
uncertainty methods, and both required effects.

**Rationale:** requiring the correct effect and interaction resolves the earlier
gap in which fitted-over-broken improvement could pass without input specificity.
Per-layer vectors avoid hiding a weak layer in a pooled average. Applying one
primary-floor-derived vector unchanged to both floors prevents post-observation
floor tuning. For one all-components-required claim, component tests at the
nominal level form a conservative intersection-union decision; an additional
familywise correction would answer a different union-of-successes question.

**Alternatives considered:** zero thresholds were rejected because statistical
nonzero alone does not establish a meaningful pilot-scaled effect; one pooled
threshold was rejected because layer scale may differ; floor-specific thresholds
were rejected because they make the easier floor easier to pass; allowing any
subset of components to pass was rejected because it contradicts the stated
robust global claim.
