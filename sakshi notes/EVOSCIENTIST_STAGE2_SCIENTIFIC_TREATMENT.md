# Independent scientific treatment of J-space Stage 2

## Scope and evidence status

This is an independent, document-based review of the completed Stage 2 observational-discrimination study. It does not re-run the experiment. It uses the preregistered proposal, ratified defaults, scientific report, operational history, ingoing brief, J-space operations skill, Stage 2 baseline reference, and—only to resolve ambiguities in the written record—the local canonical notebook source.

The primary JSON evidence artifacts remained in the ephemeral Colab runtime and were not transferred. Their reported content-addressed identities are therefore part of the documentary record, but their numerical contents cannot be independently re-hashed or reanalyzed here. Every empirical statement below is kept at evidence class 1. Nothing in this treatment authorizes Stage 3, artifact transfer, publication, or Sakshi/Elume integration, and nothing is interpreted as evidence for a functional cognitive construct or consciousness.

## 1. Independent hypothesis and predictions

The central question is not merely whether the fitted Jacobian lens produces a different token ranking from a direct logit lens. A complicated transformation can generate a different ranking without being specifically informative. The stronger Stage 2 question is:

> At the fixed Qwen3-1.7B loci, is the readout produced by the correctly matched activation–Jacobian pairing both non-redundant with cheaper readouts and specifically attributable to the fitted, layer-matched transport rather than to generic transport geometry?

That question yields three predictions.

1. **Reproduction prerequisite.** The Stage 1 anchor must reproduce exactly at the fixed loci. Failure invalidates the comparisons rather than counting as evidence for or against the scientific hypothesis.
2. **Non-redundancy prediction.** The Jacobian and logit-lens readouts should be detectably different on the same activation. Under the locked rule, median top-10 Jaccard must be at most 0.70 and the paired Wilcoxon test must satisfy `p < 0.01`. The proposal also required separation from output and prompt-only baselines beyond rerun noise.
3. **Matched-fit specificity prediction.** The real Jacobian readout should be more distinguishable from each random or structure-broken transport than it is from the logit lens: `D(J, control) - D(J, logit) >= 0.10` for at least 80% of prompts, separately for the random-vector, shuffled-activation, and mismatched-Jacobian families.

A positive Stage 2 result required all three. Non-redundancy without matched-fit specificity was preregistered as ambiguity, not success.

## 2. Methods critique

### Strengths

- The model, tokenizer context, instrumentation commit, fitted-lens revision, lens bytes, and lens checksum were pinned. The Stage 1 anchor served as a kill check rather than a result to be explained away.
- Thresholds and the decision rule were ratified before data collection. The immutable canonical notebook plus disposable execution copy is a strong provenance pattern.
- The design included a cheap competitor, surface/output baselines, a norm-matched random-vector control, and two controls that retained Jacobian machinery while breaking layer matching.
- Prompt was used as the cross-item aggregation unit after averaging over the four fixed loci, which is more defensible than treating all prompt-layer rows as independent observations.
- The retention boundary was appropriate: sparse summaries and scalar statistics were retained; raw activations, raw prompts in observation files, and full-vocabulary logits were not.
- Content-addressed exports, an extended validator, and explicit separation of runtime retention from transfer were scientifically disciplined.

### Limitations and implementation/reporting gaps

1. **The available report does not expose all locked gate statistics.** It gives median Jaccard and three specificity fractions, but not the Wilcoxon statistic or p-value, direct anchor difference, output/prompt-only comparisons, per-category table, per-layer distributions, repeat diagnostics, or seed diagnostics. The aggregate artifact reportedly contains some of these, but it was not transferred. The run decision can be reported, but it cannot be independently certified from the accessible evidence.
2. **The implemented H2 gate is narrower than the proposal.** Notebook inspection shows `added_info_pass` uses only Jacobian-versus-logit median Jaccard and its Wilcoxon p-value. The proposal's additional requirement that the Jacobian not be within rerun noise of the output and prompt-only baselines is measured but not included in the Boolean gate. Thus “H2 passed” means the implemented logit-lens subcriterion passed, not every clause in the prose preregistration.
3. **Declared seed controls were not fully operationalized.** The notebook declares inference seeds `[0, 1]`, but sets seed 0 once and does not execute a second inference-seed pass. It computes three random-vector seeds, yet the primary pairwise specificity aggregation uses only the first random-vector seed. This weakens the stated seed-invariance and control-distribution claims.
4. **The mismatched-probe implementation differs from one proposal definition.** The proposal describes a permuted/rolled fitted Jacobian, while the notebook applies a different selected layer's fitted Jacobian to the correct-layer activation. The latter is a legitimate control, but it is not the same perturbation and should have been registered and named consistently.
5. **The structure-broken controls are confounded rather than clean nulls.** A shuffled-activation control changes activation depth while retaining a real semantic activation and a real fitted Jacobian. A mismatched-map control keeps the real activation and uses another real fitted Jacobian. Residual spaces and fitted maps may be correlated across layers, so similarity to the treatment could reflect cross-layer transferability, weak layer specificity, or an insufficiently broken control. It does not uniquely identify “generic Jacobian transport.”
6. **Control assignment is fixed and unbalanced.** For each locus, the notebook picks the first or last alternative from the selected-layer list rather than balancing all map/activation mismatches or stratifying by layer distance. One arbitrary pairing can dominate the result.
7. **The D rule couples the two hypotheses.** The specificity margin is measured relative to `D(J, logit)`. As the Jacobian becomes more different from the logit lens, controls must become still more different to clear the fixed margin. Because D is bounded, strong H2 divergence reduces available headroom for H1. Without the D distributions and ceiling analysis, low specificity fractions may reflect real non-specificity, a saturated metric, or both.
8. **“Difference” is not yet “added information.”** Low top-10 overlap proves non-identity of readouts. It does not show that the Jacobian readout is more accurate, predictive, calibrated, useful, or conditionally informative given the logit lens. A target-relative endpoint is required for that stronger language.
9. **The Wilcoxon null is weakly informative.** Testing prompt-level mean Jaccard against identity (`1.0`) will become significant whenever most readouts are non-identical. The preregistered effect-size ceiling carries more scientific content. Confidence intervals on the median and on paired target-relative improvements would be more useful.
10. **External validity is deliberately narrow.** The result covers one model, one fitted lens, one T4 runtime, one position, four layers, and 50 simple synthetic prompts. Same-runtime determinism is not cross-runtime reproducibility.

## 3. Result analysis and decision

The reported aggregate result was:

- median Jacobian-versus-logit top-10 Jaccard: `0.19444444444444442`;
- random-vector specificity fraction: `1.00`;
- shuffled-activation specificity fraction: `0.22`;
- mismatched-Jacobian specificity fraction: `0.40`;
- decision: `ambiguity`.

I agree with **ambiguity** as the correct conservative decision under the locked rule. The structure-broken specificity criteria clearly did not reach 0.80, so success is unavailable. The reported Jacobian/logit separation and random-vector result also make the preregistered failure label inapplicable. Ambiguity is the proper remaining branch.

I would, however, narrow the report's interpretation. The strongest defensible reading is:

> In this run, the fitted Jacobian readout was substantially different from the direct logit-lens readout and was distinguishable under the registered D rule from the seed-0 norm-matched Gaussian-vector control. It did not demonstrate specificity to the correctly matched activation–Jacobian pairing against the two implemented cross-layer controls.

The phrases “carries information a logit lens does not” and “is not random noise” are stronger than the documented endpoint warrants. The first conflates readout difference with information relative to a target; the second generalizes from one random-control family, with the primary gate using one of its three seeds. The class-1 result establishes observable difference under this protocol, not usefulness, accuracy, construct validity, or a general rejection of noise.

The report's suggested “generic Jacobian transport” explanation is plausible but not uniquely supported. At least four live explanations remain:

1. generic transport geometry dominates;
2. fitted Jacobians are similar or transferable across the selected layers;
3. residual activations retain enough shared structure across layers that the shuffled controls preserve signal;
4. the D-plus-margin design lacks headroom or resolution in the high-divergence regime.

The current data summary cannot distinguish these explanations.

## 4. Skeptical/adversarial pass

The following attacks are sufficient to prevent a stronger conclusion.

- **Artifact-access attack:** the primary JSON files are not local. Reported hashes demonstrate claimed runtime identities, not independent possession, validation, or complete review of the numerical evidence.
- **Gate-completeness attack:** H2 was reported as passed without publishing its p-value or the output/prompt-only clauses, and the implemented Boolean omits those clauses. The safest statement is “the implemented Jacobian/logit non-identity gate reportedly passed.”
- **Metric attack:** if `D(J, logit)` is already near D's ceiling, the required additional 0.10 separation may be mathematically rare even for meaningfully different controls. Specificity fractions without D distributions and headroom diagnostics are underinterpretable.
- **Null-control attack:** wrong-layer fitted Jacobians are not null maps. They may encode highly correlated average transformations. Failure to beat them could mean the fit generalizes across layers rather than that the signal is generic.
- **Assignment attack:** choosing one deterministic alternative layer per locus makes specificity sensitive to four unbalanced pairings. All pairwise layer mismatches or a preregistered balanced sample would be more credible.
- **Randomness attack:** three random seeds were generated, but the primary gate uses seed 0 only. A fraction of 1.00 therefore does not summarize the declared random-control distribution.
- **Target attack:** two arbitrary token rankings can have low Jaccard. Without a target-relative advantage, low overlap does not show that the additional difference is informative.
- **Reproducibility attack:** runtime fixes were applied in a hot kernel and then mirrored into the canonical notebook. The record gives a strong equivalence account, but not a clean cold-kernel execution beginning from the final `353479b0...` notebook bytes. This is a provenance limitation, not evidence that the reported values are wrong.
- **Sampling attack:** five hand-designed categories with ten items each do not establish generality, and category/layer distributions were not included in the report even though ambiguity was supposed to be reported as a split result.

None of these attacks converts the result into a negative finding about the lens. Together they block promotion beyond a reported observational ambiguity.

## 5. Lessons from the runtime bugs and specificity failure

### Runtime bugs

The dtype and device failures are one scientific-computing lesson: third-party method calls have tensor contracts that are part of the instrument, even when the public API does not make them explicit.

- Outside `lens.apply`, transport inputs must be normalized to the Jacobian's float32 compute contract.
- Readouts entering cross-method comparisons must be normalized to one device; in this implementation `lens.apply` returns CPU tensors, so custom decoded rows should also return CPU float tensors.
- Shape, dtype, device, vocabulary size, and decode basis should be asserted at every instrumentation/baseline boundary before the full prompt loop.
- A one-prompt parity test should compare the custom transport/decode adapter to the library path before data collection. Static API reconnaissance cannot reveal runtime tensor-placement behavior.
- After a live fix, the cleanest provenance is a cold-kernel replay from the final immutable notebook identity. Hot-kernel repair is efficient, but source/run equivalence otherwise rests on a documented claim of identical edits.

### Specificity failure

The failure is useful because it identifies the experimental estimand as the next problem. “Different from a broken readout” is weaker than “the correct pairing is better at an observational target.” Future controls should isolate one factor at a time and preserve nuisance properties such as layer identity, activation norm, map spectrum, and output scale. The result also shows why control families must be treated as distributions rather than single deterministic alternatives.

## 6. Recommended next iteration

This recommendation is a proposal for a new Stage 2 observational study only. It does not authorize execution or any later stage.

### Design objective

Test whether the correctly matched activation–Jacobian pair has a preregistered, target-relative observational advantage over the logit lens and over controls that separately break activation identity, map identity, and fitted structure.

### Proposed design

1. **Freeze the completed run as pilot evidence.** Do not tune a revised metric or threshold on the 50 prompts and then claim confirmation on the same prompts.
2. **Create a new held-out manifest.** Use at least 200 prompts (40 per existing category) as a planning floor, then finalize n using a pilot-based precision or power calculation. Keep prompt as the primary sampling unit.
3. **Use a factorial control matrix.** For every selected layer L, compare:
   - correct activation `A_L` through correct fitted map `J_L`;
   - `A_L` through every other selected fitted map `J_M`, stratified by layer distance;
   - every other selected activation `A_M` through `J_L`;
   - `A_L` through a same-layer fit-broken map that preserves preregistered nuisance properties such as norm and singular-value spectrum;
   - norm-matched random activations through `J_L`, aggregating all declared seeds rather than selecting one.
4. **Make the primary endpoint target-relative.** Predefine an observational target such as final-output token rank, cross-entropy to the model's final next-token distribution, or rank of a preregistered completion token. The primary claim should concern paired improvement of the correct transport over logit and control transports. Keep Jaccard/D as secondary distinctness diagnostics, not as proof of information.
5. **Remove metric coupling.** Test matched-fit advantage directly against each control distribution. Do not require controls to be farther from the treatment than the logit lens is, which makes specificity depend on the size of the non-redundancy effect and on D's ceiling.
6. **Predefine aggregation and uncertainty.** Average or model loci within prompt; report prompt-cluster bootstrap confidence intervals, category and layer distributions, all pairwise control effects, and a multiplicity plan. Define exclusions and missing-data handling before execution.
7. **Enforce the tensor contract before collection.** Add a preflight that asserts float32 transport, CPU comparison rows, shapes, and decode parity. Execute the finally ratified notebook from a fresh kernel so the run is tied directly to one immutable source identity.
8. **Report every gate directly.** Publish within the authorized internal record the anchor top-k equality and max difference, repeat and seed diagnostics, effect sizes and confidence intervals, exact test statistics, category/layer tables, and every Boolean component of the decision.

### Decision policy

Retain pass, ambiguity, fail, and kill branches, but define success as a target-relative advantage of the correctly matched fit that survives all factorized controls on held-out prompts. Any result short of that remains class-1 observational evidence and cannot authorize Stage 3 or integration.

## Final judgment

The study is a valuable negative-control gate and its **ambiguity** decision is scientifically appropriate. It establishes a reported readout difference, not matched-fit specificity. The next contribution should not be a larger repetition of the same D-margin test; it should be a held-out, target-relative, factorial discrimination study with explicit tensor contracts and complete gate reporting.
