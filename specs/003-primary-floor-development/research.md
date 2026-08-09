# Research: Primary-Floor Development Study

## Status and boundary

This document resolves the technical planning questions for Option A. Its numeric
and scientific design choices are proposals for independent review and Dr. Mani's
ratification. They are not execution authorization.

The development study is separate from the completed Stage 2b pilot and all 200
scientific prompts. It may produce evidence class 1 mechanism diagnostics and a
stop-or-review recommendation only.

## Decision 1: Use complete development blocks

**Decision**: Generate 29 independent blocks of 20 prompts. Every block contains
exactly four candidates from each of the five Stage 2b categories and is evaluated
at the four selected layers. Freeze all 580 candidates before measurement.

**Rationale**: The existing guard is derived from 80 primary denominators, 20
prompts across four layers, and coverage is then evaluated at 18/20 overall plus
3/4 in every category. A standalone arithmetic pool cannot reproduce H5's global
guard and category-balance interaction. Complete blocks preserve the exact
estimand and allow direct evaluation of the generator's ability to produce a
valid future pilot population.

The 29 blocks contain 116 arithmetic candidates, which is larger than the current
40-prompt arithmetic category without touching the scientific set.

**Alternatives considered**:

- One arithmetic-only reservoir: rejected because it cannot reproduce the global
  fifth-percentile guard or the full coverage gate.
- The 180 confirmation prompts as controls: rejected because confirmation remains
  sealed.
- One large pooled guard across all development candidates: rejected because it
  changes the 20-prompt estimand and hides block-to-block reliability.

## Decision 2: Select generators, never measured items

**Decision**: Freeze generation rules, template families, block seeds, candidate
IDs, prompt bytes, parameters, and exact and normalized digests before any
eligibility measurement. Every frozen candidate remains in accounting.

The template-level sampling rule is the object under study. A future pilot may
use only a fresh, unused seed namespace from a ratified generator version and may
not reuse development candidates. A revised template family creates a new
generator version and requires a fresh development corpus.

**Rationale**: Selecting four prompts because their denominators pass would test
whether favorable items can be found, not whether a reproducible generation rule
can meet the coverage requirement. The repository's Option A explicitly forbids
item-level pass selection. More generally, repeated adaptation to evaluation data
can make apparent performance unreliable; see [Dwork et al., 2015](https://doi.org/10.1126/science.aaa9375).

**Alternatives considered**:

- Rank candidates by eligibility and select the best four: rejected as prompt
  laundering.
- Drop a failing family and reuse the same evidence for the remaining families:
  rejected because one corpus would both select and validate the generator.
- Balance on tokenizer or denominator results: rejected because balancing must
  be source-defined before outcomes exist.

## Decision 3: Justify 29 blocks with exact reliability

**Decision**: Treat one frozen 20-prompt block as the statistical unit. A block
succeeds only when both floors satisfy the unchanged 18/20 overall and 3/4 in
every category at every selected layer. Recommend review only when 29 of 29
blocks succeed.

For `n` independent successes from `n` blocks, the one-sided 95% exact binomial
lower confidence bound is `0.05^(1/n)`. At 29 blocks:

```text
0.05^(1/29) = 0.9018553723
```

Twenty-nine is the minimum integer count for which the bound exceeds 0.90 when
every block succeeds. The calculation uses an exact binomial limit rather than a
normal approximation. The method follows the exact binomial construction
documented by [NIST](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm)
and originates with [Clopper and Pearson, 1934](https://doi.org/10.1093/biomet/26.4.404).

**Rationale**: This powers the actual stop-or-review question without inventing a
mechanism-effect size. The H1-H5 analyses remain descriptive because neither the
missing artifact nor two exclusions provide a lawful effect-size basis.

**Alternatives considered**:

- Fewer than 29 blocks: permitted only if the study is relabelled descriptive and
  cannot make the proposed 0.90 reliability claim.
- Permit one failed block while retaining the same claim: rejected because the
  all-success exact calculation no longer applies.
- Power on marginal arithmetic eligibility: rejected because it discards shared
  guards, four layers, other categories, and both floors.

## Decision 4: Freeze the block and template schedule

**Decision**: Every block uses one deterministic seed identity from a fixed
namespace. The generator allocates exactly four candidates per category using a
balanced schedule declared in the manifest. Arithmetic generation crosses
predeclared operation and surface-template families without choosing items after
tokenization or measurement.

Collision handling occurs before the manifest freezes. Candidate exact and
normalized digests are compared with a digest-only registry of the 200 scientific
prompts. The comparison reports candidate rejection and aggregate counts only;
it never exposes pilot or confirmation text. Replacement, if required, follows a
predeclared deterministic next-seed rule and is logged before freeze.

**Rationale**: Independent block seeds support block-level reliability while the
balanced schedule prevents a favorable family mix from being chosen after
results. A digest-only exclusion registry allows disjointness validation without
placing scientific prompt text in the development runtime.

**Alternatives considered**:

- Read the full scientific manifest during development execution: rejected as an
  unnecessary custody risk.
- Replace post-measurement exclusions: rejected as outcome-driven mutation.
- Let the runtime invent new seeds on collision: rejected because the corpus
  would not be precommitted.

## Decision 5: Preserve the existing floor and guard estimand

**Decision**: For each block, retain all primary and sensitivity floor scores plus
output scores before eligibility. Derive one guard from exactly 80 primary-floor
denominators using the 0.05 linear quantile. Apply that guard to both floors
without another model or lens pass.

Primary floor remains `input_embedding_decoded`; sensitivity floor remains
`layer0_residual_decoded`. Floor disagreement is reported and never resolved by
selecting the favorable construction. Both floors must meet coverage in all 29
blocks for review readiness.

**Rationale**: Reusing the completed pilot's scalar guard would not reproduce how
a future 20-prompt population changes the global guard. Per-block derivation
retains the current estimand. Requiring both floors fixes the response to floor
disagreement before observation.

**Alternatives considered**:

- Reuse the observed pilot guard `0.3388633415411974`: rejected as a mechanism
  diagnostic surrogate that does not test the generator's full future path.
- Derive separate guards by floor: rejected because the ratified rule derives one
  primary-floor guard and applies it to both floors.
- Promote the sensitivity floor: rejected because that is Option C, not Option A.

## Decision 6: Analyze H1-H5 together and by block

**Decision**: Freeze one candidate-level analysis table containing block,
category, template family, operation, both floor denominators, both guard margins,
eligibility, tokenizer features, target features, and missingness.

The declared feature groups are:

| Hypothesis | Features | Comparison |
|---|---|---|
| H1 prompt construction | Surface-template family, operation, family-by-operation interaction | Full prespecified model versus H1-group ablation |
| H2 tokenization | Prompt token count, final-token ID and piece boundary, target-piece byte length, leading-space or boundary state | Full model versus H2-group ablation |
| H3 target properties | Argmax tie count, top-1 versus top-2 logit margin, normalized target logit, output entropy | Full model versus H3-group ablation |
| H4 floor geometry | Paired denominator difference, paired guard-margin difference, primary-ineligible/sensitivity-eligible discordance | Paired within-candidate summary |
| H5 global guard interaction | Arithmetic versus other-category lower-tail guard margins and block coverage | Block-aware category comparison plus exact block outcomes |

H1-H3 predict primary guard margin. They use one prespecified full model and
leave-one-block-out predictive loss, then remove one feature group at a time.
Records sharing one guard never cross training and evaluation folds. This uses
cross-validation for out-of-sample predictive assessment following
[Stone, 1974](https://doi.org/10.1111/j.2517-6161.1974.tb00994.x).

Each hypothesis has structural status `defined`, `undefined`, or `stopped` and a
descriptive interpretation `consistent`, `inconsistent`, or `unresolved`.
Interpretations do not choose a winning mechanism and do not create a scientific
gate. A two-prompt association cannot produce a defined hypothesis record.

**Rationale**: H1-H3 can confound one another, and item-level folds would leak a
shared block guard. H4 is intrinsically paired within candidates. H5 is a block
property because the guard and coverage decision are shared.

**Alternatives considered**:

- Five separate unadjusted analyses: rejected because overlapping explanations
  would be misattributed.
- Binary eligibility alone: rejected because thresholding discards denominator
  geometry.
- Item-level random cross-validation: rejected because records sharing a guard
  would appear in both training and evaluation data.
- Formal mechanism pass thresholds: rejected because no effect-size basis has
  been lawfully established.

## Decision 7: Use a separate schema and validator family

**Decision**: Define separate schema families:

```text
jspace-primary-floor-development-manifest/v1
jspace-primary-floor-development-evidence/v1
jspace-primary-floor-development-decision/v1
```

Expected manifest, exclusion-registry, notebook, code, model, tokenizer, lens,
decoding, and analysis identities enter validators independently. Objects cannot
authenticate their own claimed identity.

**Rationale**: `jspace-observation-stage2b/v1` is pilot-only, requires exactly 20
prompts and 4 layers, binds spent pilot authorization, and rejects unknown fields.
Generalizing it would weaken a proven contract. A separate validator can reuse
content-addressing and fail-closed patterns while preserving exact pilot behavior.

**Alternatives considered**:

- Add development fields to the pilot schema: rejected because it changes and
  weakens the completed pilot contract.
- Reuse the pilot authorization record: rejected because its scope and permitted
  registry updates are pilot-specific and already spent.
- Trust source hashes written inside the evidence object: rejected as
  self-attestation.

## Decision 8: Keep execution surfaces deferred and false by default

**Decision**: Plan a thin, unexecuted notebook with all authorization flags false,
but do not create bundle or launch-preparation writers until a separate execution
surface is approved. CPU-only implementation and synthetic validation may proceed
after planning and tasks review.

**Rationale**: Design work is authorized; data generation and GPU use are not.
The notebook boundary is needed to design imports, source binding, and failure
ordering, while executable launch artifacts would imply an authority surface that
does not yet exist.

Preregistration separates data-independent plans from data-contingent exploration;
see [Nosek et al., 2018](https://doi.org/10.1073/pnas.1708274114).

**Alternatives considered**:

- Notebook-only logic: rejected because declared rules must be consumed by tested
  modules and validators.
- Reuse the pilot notebook and launcher: rejected because their prompt view,
  authorization, schema, and source identities are pilot-specific.
- Build and execute a development launch now: rejected because no GPU or
  scientific-run authorization has been given.

## Decision 9: Freeze the final stop-or-review rule

**Decision**: Evaluate universal stops first. If none fires, return
`ready_for_independent_preregistration_review` only when:

1. all 580 candidates and source identities are accounted for;
2. no post-freeze candidate addition, removal, replacement, or promotion occurred;
3. all 29 blocks meet 18/20 total and 3/4 in every category at every selected
   layer under the primary floor;
4. the sensitivity floor meets the same rule in all 29 blocks;
5. all H1-H5 records are present or explicitly unresolved; and
6. no forbidden pilot, confirmation, threshold, gate, transfer, authorization, or
   evidence-promotion field exists.

Every other valid terminal result is `stop_estimand_before_revised_pilot`. A stop
means the current generator is not ready. It does not prove that every possible
generator is impossible.

**Rationale**: This is the smallest decision surface consistent with Option A,
the universal stops, and the spec's bounded positive outcome.

**Alternatives considered**:

- Allow failed blocks but lower the reliability target after observation:
  rejected as moving the gate.
- Make H1-H5 interpretations additional pass conditions: rejected because they
  are descriptive mechanism evidence, not powered gates.
- Automatically authorize a pilot after review readiness: rejected because
  independent review, ratification, source freezing, and GPU authorization remain
  separate gates.
