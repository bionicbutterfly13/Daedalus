# J-space Hypothesis Ledger

Updated: 2026-07-31

This ledger converts curiosity into refutable work. A row is not a result, and
priority is not evidence. Each hypothesis must survive three gates before it can
be used in a paper:

1. the measurement is implemented and independently recomputable;
2. the experiment distinguishes its hypothesis from a credible null;
3. the result survives the preregistered uncertainty and multiplicity rules.

Stage 2b is the upstream dependency. The 2026-07-31 pilot reached
publication-workflow stage E4, pilot observed, while remaining scientific
evidence class 1. It supplied
instrument evidence, including a positive sensitivity-floor signal, but the
preregistered robust result was undefined because the primary floor failed one
category-coverage minimum. The J-space variables below therefore remain candidate
measurements rather than validated scientific instruments.

## Evidence vocabulary

| Label | Meaning |
|---|---|
| `SOURCE` | Directly supported by a cited paper or inspected source file |
| `LOCAL-VALIDATION` | Executed locally with a recorded passing check |
| `IMPLEMENTED` | Code exists, but the relevant scientific runtime has not established the claim |
| `HYPOTHESIS` | Falsifiable proposal with an explicit null |
| `SPECULATION` | Possible relationship not yet operationalized |
| `MYTHOS` | Metaphor or imaginative framing; never evidence |

## Priority queue

### H-JS-INST-011: Cause of primary-floor arithmetic exclusion

**Claim.** The primary-floor arithmetic exclusions are reproducibly associated
with at least one preregistered mechanism class: prompt construction,
tokenization, target properties, output-to-floor geometry, or interaction with
the globally derived guard.

**Null.** The two pilot exclusions do not reproduce on a disjoint development
set, or no mechanism class predicts eligibility beyond chance and sampling
variation.

**Intervention and controls.** Freeze a newly generated development set outside
all 200 scientific prompts. Record every candidate before measuring eligibility.
Fit prompt-template, tokenizer, target, and denominator-geometry explanations
jointly, with simple held-out baselines. Do not inspect the confirmation set or
select individual prompts because they pass.

**Outcome.** Reproducible primary-floor eligibility and guard-margin prediction,
category coverage under a frozen template-level sampler, and agreement or
disagreement between the two floors.

**Current evidence.** The frozen retained-artifact diagnostic received
independent GO and merged through PR #10. Its first Colab run stopped before
artifact read because both exact inputs were absent from the active `/content`
runtime. That state is consistent with a reset or replacement, but the precise
lifecycle event is unknown. No mechanism association was observed. The five
alternatives and Options A through E are specified in
`j-space-lab/STAGE2B_PRIMARY_FLOOR_OPTIONS_PACKET.md`.

**Failure condition.** No association reproduces, the result requires
item-level pass selection, a guard is relaxed after observation, or any
confirmation input is accessed.

**Status.** `HYPOTHESIS`; immediate instrument gate, evidence path awaiting Dr.
Mani's decision.

### H-JS-TS-001: J-space information and Thoughtseed competition

**Claim.** A candidate's J-space alignment predicts which Thoughtseed wins local
competition after controlling for raw activation, Hamiltonian score, lineage,
and basin identity.

**Null.** J-space alignment adds no held-out predictive value beyond the
Thoughtseed Runtime's existing competition variables.

**Intervention and controls.**

- Compare the current deterministic competition rule with the same rule plus a
  preregistered J-space feature.
- Include activation-only, Hamiltonian-only, shuffled-J-space, and
  label-permuted controls.
- Evaluate out of sample and by prompt family. Do not tune the J-space weight on
  the confirmatory split.

**Outcome.** Difference in held-out log loss or Brier score for winner
prediction, plus calibration and selection stability.

**Available code.** `thoughtseed-runtime` supplies immutable seed records,
competition, Hebbian reinforcement, child spawning, and SOHM-complex
construction. Its existing test suite passed `93` tests locally on 2026-07-30.
The J-lab supplies candidate rank-based J-space scores. The Stage 2b pilot showed
floor-dependent behavior and did not validate the instrument.

**Failure condition.** No incremental predictive value, instability across
prompt families, or dependence on an unvalidated J-space floor.

**Status.** `HYPOTHESIS`; blocked by the unconfirmed Stage 2b instrument.

### H-JS-AB-002: Attractor basins and representational persistence

**Claim.** Basin membership predicts whether a J-space concept persists,
disappears, or re-enters across tokens and episodes better than rank and
activation alone.

**Null.** Basin labels are descriptive bookkeeping and add no predictive value.

**Intervention and controls.**

- Construct trajectories from repeated J-space measurements.
- Compare basin-aware transition models with rank-only, activation-only, and
  basin-label-shuffle controls.
- Hold the basin construction fixed before scoring the evaluation split.

**Outcome.** Held-out transition likelihood, re-entry accuracy, and calibration.

**Available code.** Thoughtseed Runtime exposes a protocol-only basin seam.
Elume contains deterministic attractor-basin and replay-oriented components.
Those sibling components are candidate infrastructure, not evidence that the
proposed relationship exists.

**Failure condition.** Basin labels fail to generalize or collapse into prompt
identity.

**Status.** `HYPOTHESIS`; requires an explicit trajectory artifact.

### H-JS-CUR-003: Curiosity as experiment selection

**Claim.** A curiosity policy that scores expected discrimination among live
J-space hypotheses reaches decisive evidence with fewer experiments than
random, salience-only, or coverage-only selection.

**Null.** The curiosity score does no better than the best simple baseline after
accounting for compute.

**Intervention and controls.**

- Freeze a set of synthetic hypotheses with known truth and a set of
  repository-grounded hypotheses whose truth is hidden from the selector.
- Compare random, uncertainty-only, coverage-only, current heuristic, and a
  formal expected-information-gain policy where feasible.
- Charge every policy the same compute and artifact budget.

**Outcome.** Experiments required to identify the correct hypothesis, cumulative
information gain, regret, and false-discovery rate.

**Available code.** Dionysus3 and Elume contain entropy-, ambiguity-, coverage-,
and difficulty-based curiosity heuristics. These are heuristic selection
functions, not validated expected-free-energy solvers. Elume also keeps a
separate optional formal active-inference provider.

**Failure condition.** The heuristic loses to a simple baseline, exploits
metadata leakage, or proposes experiments whose outcomes cannot distinguish
the hypotheses.

**Status.** `HYPOTHESIS`; synthetic benchmark can precede Stage 2b.

### H-JS-NEM-004: Prediction gaps and J-space transitions

**Claim.** Nemori episodes with larger prediction-correction deltas are enriched
for changes in J-space content relative to matched low-delta episodes.

**Null.** Delta magnitude and J-space transition magnitude are unrelated after
controlling for episode length, lexical novelty, and task change.

**Intervention and controls.**

- Compare Nemori's prediction-correction path with direct extraction,
  shuffled-episode, and lexical-novelty controls.
- Log exceptions and empty corrections as failures rather than evidence of no
  learning.
- Predefine episode alignment and exclude any run whose memory and J-space clocks
  cannot be matched.

**Outcome.** Conditional association, held-out transition prediction, and
ablation effects.

**Ownership boundary.** Nemori is a third-party, MIT-licensed project by Nan,
Ma, Wu, and Chen. This project may test an integration or local adaptation; it
must not claim Nemori's core architecture as an original contribution.

**Failure condition.** The effect vanishes under lexical-novelty controls or is
explained by silent extraction failures.

**Status.** `HYPOTHESIS`; third-party integration review required.

### H-JS-REL-005: Relations beyond a bag of concepts

**Claim.** A relation-aware representation of candidate workspace content
predicts behavior and interventions better than an unordered set of
single-token J-lens concepts.

**Null.** Relation structure adds no held-out predictive value over concept
identity and rank.

**Intervention and controls.**

- Use tasks where the same concepts occur in different roles, orders, or
  relations.
- Compare bag-of-concepts, ordered-token, role-labeled graph, and
  relation-shuffled models.
- Test counterfactual swaps that preserve concept membership while changing
  role binding.

**Outcome.** Behavioral prediction, intervention specificity, and recovery of
the preregistered relation.

**Rationale.** Anthropic explicitly identifies single-token coverage and
bag-of-concepts structure as limitations of the current Jacobian Lens. This
hypothesis turns that limitation into a discriminating experiment rather than
assuming a richer workspace exists.

**Failure condition.** Relation-aware models do not generalize or only memorize
surface order.

**Status.** `HYPOTHESIS`; high priority after instrument validation.

### H-JS-OFF-006: Offline maintenance and hypothesis quality

**Claim.** An offline maintenance cycle that consolidates, prunes, and resurfaces
research traces improves later hypothesis novelty and coverage without reducing
provenance accuracy.

**Null.** Maintenance provides no benefit over ordinary retrieval or harms
source fidelity.

**Intervention and controls.**

- Compare no maintenance, clustering only, pruning only, resurfacing only, and
  the combined cycle.
- Blind the evaluator to condition.
- Score provenance accuracy separately from novelty; a novel unsupported claim
  is a failure.

**Outcome.** Source-supported hypothesis yield, duplicate rate, coverage of the
active ledger, provenance error, and compute cost.

**Available interface.** Dionysus3 exposes an experimental offline
trace-maintenance interface. Its repository governs the implementation,
architecture, tests, and readiness claims. The "dream" name is project mythos
and does not imply sleep, subjective experience, or biological dreaming.

**Failure condition.** More unsupported novelty, provenance loss, or no
advantage over simple retrieval.

**Status.** `HYPOTHESIS`; architecture reconciliation required.

### H-JS-DYN-007: Abstract oscillator coordination

**Claim.** An abstract coupled-oscillator model predicts stable transitions
among candidate representations better than a non-dynamical baseline.

**Null.** Oscillator state adds no predictive value beyond the candidates'
static scores and recent history.

**Intervention and controls.**

- Fit damping and coupling on a training split, then freeze them.
- Compare LinOSS dynamics with autoregressive, exponential-decay, and
  phase-shuffled controls.
- Avoid mapping abstract oscillator channels to biological frequency bands
  unless independent evidence justifies that mapping.

**Outcome.** Held-out transition prediction, perturbation recovery, and
parameter stability.

**Ownership boundary.** `linoss-dynamics` exposes a deterministic oscillator
interface. Its repository governs the mathematics, implementation, citations,
and validation details; this ledger claims only the proposed J-space test.

**Failure condition.** No generalization, unstable parameters, or gains explained
by added model capacity.

**Status.** `HYPOTHESIS`; can begin with synthetic trajectories.

### H-JS-META-008: Meta-learning as proposal generation

**Claim.** A meta-learning proposal generator produces more testable,
source-supported J-space hypotheses than keyword counting at equal review cost.

**Null.** It is no better than keyword counting or merely repackages document
frequency.

**Intervention and controls.**

- Compare Dionysus3's present rule-based extractor, a keyword-count baseline,
  and a blinded human proposal set.
- Score testability, source correctness, novelty, duplication, and reviewer time.
- Keep proposal generation separate from evidence adjudication.

**Outcome.** Accepted hypotheses per review hour and provenance error rate.

**Available interface.** Dionysus3 exposes a proposal-generation interface. Its
repository governs the implementation and evaluation details. Any relevance
label is a proposal feature, not a measure of consciousness or scientific
importance.

**Failure condition.** No improvement over keyword counting or increased
unsupported claims.

**Status.** `HYPOTHESIS`; synthetic and document-only evaluation available.

### H-JS-SM-009: Modeled self-state and perspective-related motifs

**Claim.** Continuity in explicit self-model records predicts stability of
perspective-related J-space motifs under controlled persona perturbations.

**Null.** The records add no predictive value beyond prompt text and recent
tokens.

**Intervention and controls.**

- Manipulate persona instructions while holding task content fixed.
- Compare prompt-only, recent-token, self-record, and shuffled-self-record
  predictors.
- Do not use self-report as evidence of subjective experience.

**Outcome.** Held-out motif stability and causal response to record ablation.

**Available code.** Autonoesis defines host-neutral self-model records and
operators. Those are modeled data structures. Names such as
`PhenomenalState` do not establish phenomenality.

**Failure condition.** Effects reduce to prompt text or disappear under
record-shuffle controls.

**Status.** `HYPOTHESIS`; terminology review required.

### H-JS-BC-010: Broadcast topology as an observable

**Claim.** Selective event fanout provides a useful operational measure of
workspace-like broadcast when it predicts which consumers can use a selected
representation.

**Null.** Fanout is only routing configuration and does not predict downstream
use.

**Intervention and controls.**

- Instrument event publication, subscriber receipt, latency, and verified
  downstream state change.
- Compare fanout with matched events whose subscribers receive but ignore the
  content.
- Require causal use, not receipt alone.

**Outcome.** Downstream task change attributable to the event, with complete
delivery provenance.

**Available code.** `d4-eventbus` can provide typed async instrumentation.
An event named `ThoughtSeed` or `SOHM` is a schema label, not evidence of a
global workspace or a biological mechanism.

**Failure condition.** Receipt fails to predict use, or topology alone explains
the measurement.

**Status.** `HYPOTHESIS`; instrumentation design pending.

## Deferred curiosity

The following ideas are worth retaining but are not yet sharp enough to enter
the priority queue:

- whether counterfactual J-space perturbations can distinguish causal access
  from correlated readout;
- whether PageIndex plus Nemori can support a provenance-preserving literature
  memory whose retrieval quality measurably improves experiment selection;
- whether multi-scale basin geometry explains when workspace-like content is
  robust to paraphrase;
- whether a formal expected-information-gain policy can replace the current
  curiosity heuristics without exceeding the laboratory's compute budget.

These remain `SPECULATION` until each has a defined intervention, null, outcome,
and falsification condition.
