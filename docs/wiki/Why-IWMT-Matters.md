# Why IWMT Matters

The J-space project uses two sources for two different jobs. Anthropic's
Jacobian Lens gives us a candidate measurement of verbalizable internal
representations. Adam Safron's Integrated World Modeling Theory (IWMT) gives us
questions about what a richer workspace would need to do: integrate a generative
self/world model, guide action through active inference, carry information
through a reduced-dimensional bottleneck, support recurrent message passing, and
maintain spatial, temporal, and causal coherence.

Putting these sources next to each other does not make them equivalent. A
verbalizable transformer representation is not automatically an integrated world
model. A workspace-like function is not automatically the recurrent biological
architecture discussed by IWMT. Neither source, and no experiment in this
project, establishes phenomenal consciousness.

## What Anthropic contributes

The [Transformer Circuits paper](https://transformer-circuits.pub/2026/workspace/index.html)
defines the J-lens as a context-averaged Jacobian map. At each layer it estimates
the first-order effect of an activation on the model's likelihood of producing a
vocabulary token at the present or a future position. Applying that map to an
activation produces a ranked, verbalizable token readout.

Anthropic reports that the associated J-space supports verbal report, directed
modulation, internal reasoning, flexible use, and selective engagement. Its
[research summary](https://www.anthropic.com/research/global-workspace) also
describes causal interventions and a contrast between flexible J-space-dependent
tasks and automatic processing that continues under J-space ablation. The
[open-source Jacobian Lens](https://github.com/anthropics/jacobian-lens) is the
third-party instrument foundation. This project can test and extend that
instrument; it does not claim the method or Anthropic's findings as its own.

## What IWMT contributes

[Safron (2020)](https://doi.org/10.3389/frai.2020.00030) treats consciousness as
a question about embodied, integrated generative modeling rather than readout
alone. IWMT combines ideas from active inference, integrated information, and
global neuronal workspace theory. Its proposed mechanisms include
reduced-dimensional representational bottlenecks, recurrent or loopy message
passing, Bayesian model selection, and models that preserve spatial, temporal,
and causal coherence for self and world.

We use those ideas as hypothesis generators. IWMT's biological and phenomenal
claims are not implementation specifications for a feedforward transformer. A
software variable named `workspace`, `self`, `ignition`, or `active inference`
does not verify the theory.

## What Stage 2b actually established

The 2026-07-31 Stage 2b pilot tested instrument specificity only. It asked
whether the fitted Jacobian map advances the model's own target more than a
geometry-matched broken map, and whether that advantage is specific to the
correct activation rather than a wrong one.

The pilot completed operationally. Its sensitivity floor showed a positive
fitted-map-specific interaction at layers 6, 13, 20, and 26 under both 99%
interval methods. The required primary-floor result was undefined because only
two arithmetic-completion prompts remained eligible against a preregistered
minimum of three. Threshold derivation was unavailable and no pilot pass/fail
decision was emitted.

That result is evidence of prompt-floor-dependent instrument behavior. It does
not validate the J-lens as a robust measurement, Anthropic's broader global
workspace interpretation, IWMT, or consciousness. Confirmation remains blocked.
See [[Stage 2b Pilot Result]] for the data and custody record.

## Falsifiable bridge experiments

These mappings turn theoretical resemblance into experiments that can fail.
Every row assumes the instrument-specificity problem is resolved first.

| Question | Test | Null or failure condition |
|---|---|---|
| **Broadcast versus matched non-J-space directions** | Intervene on one preregistered J-space feature and equally sized, geometry-matched non-J-space directions; measure causal use by several independent downstream tasks. | J-space affects no more consumers than matched directions, or effects reduce to activation magnitude. |
| **Flexible versus automatic access** | Use the same content in practiced continuation and novel reasoning tasks; ablate or swap its J-space coordinate while holding surface input fixed. | Both task types change equally, or neither depends specifically on J-space. |
| **Ignition under ambiguity** | Present graded ambiguous evidence, preregister an entry measure, and test whether one representation enters abruptly and suppresses competitors near a decision point. | Access changes smoothly, depends on an arbitrary threshold, or matched non-J-space features show the same transition. |
| **Limited capacity** | Increase the number of independently relevant concepts while holding prompt length and activation budget fixed; measure competition, displacement, and downstream use. | No selective capacity limit appears, or degradation is fully explained by context length or general task difficulty. |
| **Relational synergy** | Compare relation-aware J-space representations with bags of the same token concepts, role permutations, and relation-shuffled controls on tasks where roles determine the answer. | Token identity alone predicts behavior, or relation interventions do not generalize to held-out structures. |
| **Spatiotemporal and causal coherence** | Track preregistered J-space trajectories in worlds with controlled spatial, temporal, and causal constraints; compare relation-aware trajectory models with rank-only and shuffled-trajectory baselines. | Coherence scores do not predict violations or future states beyond lexical and recency controls. |
| **Information-seeking active inference** | In a bounded action-perception task, test whether J-space uncertainty and expected discrimination predict which observation the model requests; intervene on the candidate belief before query choice. | Query choice is explained by output entropy or prompt cues, and belief intervention does not redirect information seeking. |
| **Counterfactual plans** | Use branching tasks where an unspoken intermediate plan predicts later actions; swap the plan before the branch and compare with answer-vector and matched-direction controls. | The plan appears only after the action is determined, or interventions do not change the later action selectively. |
| **Self-model/access dissociation** | Compare base, post-trained, and controlled persona conditions on identical access tasks; manipulate explicit self-model records separately from J-space content. | Self markers and access cannot be dissociated, or all changes reduce to prompt wording and recent tokens. Self-report is never the ground truth for experience. |
| **Multimodal action generalization** | In a model with non-text input or action outputs, test whether one measured representation transfers across verbal report, visual choice, and action while vocabulary-specific controls fail. | Effects remain confined to token output, or apparent transfer is explained by a shared verbal label. |

## Order of work

1. Resolve Stage 2b's primary-floor category-coverage failure without tuning the
   rule to the observed sensitivity result.
2. Obtain a robust, separately authorized instrument result before treating
   J-space values as validated observations.
3. Preregister one bridge hypothesis at a time with matched controls, holdouts,
   and an explicit failure rule.
4. Keep functional access, world-model organization, and phenomenal
   consciousness as separate claim levels.

The practical reason IWMT matters is that it prevents a readable representation
from becoming the end of the story. It directs attention toward integration,
coherence, action, recurrence, and counterfactual control. The reason Stage 2b
matters is that none of those questions are interpretable until the measurement
itself survives specificity controls.

## References

Gurnee, W., Sofroniew, N., Pearce, A., Piotrowski, M., Kauvar, I., Chen, R.,
Soligo, A., Bogdan, P., Ong, E., Wang, R., Thompson, B., Abrahams, D.,
Kantamneni, S., Ameisen, E., Batson, J., & Lindsey, J. (2026). Verbalizable
representations form a global workspace in language models. *Transformer
Circuits Thread*. https://transformer-circuits.pub/2026/workspace/index.html

Anthropic. (2026, July 6). *A global workspace in language models*.
https://www.anthropic.com/research/global-workspace

Anthropic. (2026). *Jacobian Lens: Companion code for the global workspace
interpretability paper* [Computer software]. GitHub.
https://github.com/anthropics/jacobian-lens

Safron, A. (2020). An integrated world modeling theory (IWMT) of consciousness:
Combining integrated information and global neuronal workspace theories with
the free energy principle and active inference framework; toward solving the
hard problem and characterizing agentic causation. *Frontiers in Artificial
Intelligence, 3*, Article 30. https://doi.org/10.3389/frai.2020.00030
