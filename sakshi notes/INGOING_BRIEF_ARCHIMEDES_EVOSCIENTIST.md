# Ingoing brief: Archimedes to EvoScientist, J-space Stage 2

The single authoritative input for Archimedes to start a well-informed
EvoScientist run on the completed J-space Stage 2 discrimination study. Read this
first; it embeds the full picture and indexes every source document. Prepared by
the Claude Code session that conducted the study, 2026-07-24.

## 0. One-line task

Process the already-completed J-space Stage 2 observational-discrimination
experiment through EvoScientist's own pipeline (plan, hypothesis, methods,
analysis, skeptical evaluation, reflection, memory), producing EvoScientist's
native scientific artifacts and writing observations to EvoScientist memory. The
experiment has already been executed; EvoScientist is not re-running it, it is
scientifically processing and reasoning about the completed run.

## 1. Exact task to give EvoScientist

Copy the block below into a new EvoScientist thread as the task. It references the
repository documents that are the study materials.

> You are processing a completed interpretability experiment as an AI scientist.
> Do not re-run the experiment; it is finished. Read these repository documents in
> full, then produce your own scientific treatment of the study and record
> observations to memory:
>
> - `sakshi notes/STAGE2_DISCRIMINATION_REPORT.md` (the full report)
> - `sakshi notes/STAGE2_DISCRIMINATION_PROPOSAL.md` (the preregistered design)
> - `sakshi notes/STAGE2_PROVISIONAL_DEFAULTS.md` (the ratified parameter answers)
> - `sakshi notes/CLAUDE_CODE_SESSION_HISTORY.md` (the operational journey and the
>   two runtime bugs)
> - `EvoScientist/skills/jspace-research-operations/references/stage2-discrimination-baseline.md`
>   (design, thresholds, runtime fixes, executed-run result, artifact hashes)
> - `EvoScientist/skills/jspace-research-operations/SKILL.md` (the bounded protocol
>   and stage gates)
>
> Deliver: (1) an independent restatement of the hypothesis and predictions;
> (2) a methods critique; (3) an analysis of the result (decision was ambiguity)
> including whether you agree with the reading; (4) a skeptical/adversarial pass
> that tries to break the conclusion; (5) the ideas and lessons you take from the
> two runtime bugs and the specificity failure; (6) a recommended next iteration.
> Load the `jspace-research-operations` skill and stay inside its stage gates:
> this is observation-only evidence class 1, no promotion to functional or
> consciousness claims, no authorization for Stage 3, transfer, publication, or
> Sakshi/Elume integration.

## 2. Authorization and boundaries (already settled)

- Dr. Mani ratified all eight Stage 2 open questions on 2026-07-24, including GPU
  execution. The thresholds are locked, not provisional.
- Scope is observation only. No lens fitting, steering, ablation, activation edit,
  artifact transfer, publication, or Sakshi/Elume mutation.
- All readouts are evidence class 1 (directly measured). Nothing is promoted to a
  functional or phenomenal claim. Ambiguity does not authorize Stage 3.
- Repository work stays on the fork; nothing goes to the public upstream.
- EvoScientist's job here is scientific processing and memory, not new execution.

## 3. The study in full (so EvoScientist has the science even before opening files)

### Idea
Archimedes intends to run a cognitive lab with Anthropic's Jacobian Lens as the
instrument. Everything downstream (Elume consuming observations, Sakshi auditing
lineage) rests on one unproven assumption: that the fitted Jacobian lens reports
something a cheaper tool would miss. Stage 1 proved only self-consistency (same
readout twice, max logit diff 0.0), which is reproducibility, not information. The
cheapest honest competitor is the logit lens (push a mid-layer residual straight
through the final norm and unembedding). Stage 2 asks whether the Jacobian lens
adds anything over that, and whether any signal survives structure-broken controls.

### Hypothesis (two falsifiable conditions, both required to pass)
- H1 specificity: the Jacobian readout is more distinct from structure-broken
  transports (norm-matched random vector, shuffled-layer, mismatched-probe) than
  from the logit lens, on at least 80% of prompts by a D margin of 0.10.
- H2 added information: the median top-10 token overlap (Jaccard) between the
  Jacobian and logit-lens readouts is at most 0.70, with paired Wilcoxon p < 0.01.

### Methods (condensed; full detail in the report)
- Pinned identities: jlens `581d398...`, Qwen3-1.7B rev `70d244cc...`, lens rev
  `a4114d77...` (SHA `6fcc7901...`, 226,501,315 bytes). Runtime Tesla T4, ~3.2 GiB
  after load.
- 50 synthetic prompts, 5 categories x 10; item 1 is the Stage 1 anchor (kill
  criterion). Raw text only in a versioned manifest; artifacts are digest-only.
- Loci: layers 6, 13, 20, 26 at position -2; top-k 10; rank stats over top-50.
- Six readouts per locus: Jacobian, logit-lens, output, prompt-only,
  random-vector, structure-broken (shuffled-layer and mismatched-probe), all
  decoded through the identical final norm and unembedding (one vocabulary basis).
- Primary metric D in [0,1] = 0.5(1 - top10 Jaccard) + 0.5(normalized shared-rank
  displacement). Preregistered thresholds and a pass/kill/ambiguity/fail decision
  rule locked before data collection.

### Result (measured; run_id f9234a9c-6a2d-43da-9fbd-bf26b19ac18c, n=50)
```json
{
  "median_jaccard_jacobian_vs_logit_lens": 0.19444444444444442,
  "specificity": {
    "random_vector_fraction": 1.0,
    "non_jspace_shuffled_fraction": 0.22,
    "non_jspace_mismatched_fraction": 0.4
  },
  "decision": "ambiguity"
}
```
Reproduction passed. Added information passed (median Jaccard 0.194, well below
0.70; the Jacobian lens is not a repackaged logit lens). Specificity failed:
random-vector cleared at 1.0, but the structure-broken controls did not
(shuffled-layer 0.22, mismatched-probe 0.40, far under 0.80). Decision: ambiguity.

### Reading
The fitted lens carries information a logit lens does not and is not random noise,
but this run cannot separate that signal from generic Jacobian-transport
structure. The most parsimonious account is that much of the Jacobian readout's
distinctness from the logit lens is generic to transporting a residual through
some layer-sized Jacobian, not specific to the correct fitted map at the correct
layer. Promising, not conclusive. Next iteration should strengthen the
structure-broken discrimination (pilot the D metric and 0.10 margin; reconsider
the controls; raise n and power) before any promotion.

### Evidence artifacts
50 per-prompt + 1 aggregate content-addressed JSON (schema
`jspace-observation-discrimination/v1`), retained in the ephemeral Colab runtime,
not transferred. Aggregate SHA-256
`251967260907468a7a0086446855db403cded0c4c1fe9ae889417472cc86e0dc`; Stage 1 anchor
artifact `22ca288fdb493e33...`.

## 4. Operational journey and lessons (the valuable part)

Two runtime defects surfaced only under live GPU execution, both the same family
(the notebook's own baseline paths not matching jlens conventions):

1. dtype: jlens jacobians are float32 and its `lens.apply` casts residuals to
   float, but the notebook fed bfloat16 activations to `lens.transport`. Fix:
   capture residuals as float32.
2. device: `lens.apply` returns CPU tensors but `decode_residual` returned CUDA.
   Fix: return decoded readouts on CPU.

Each was diagnosed from the traceback, fixed live in the hot kernel and identically
in the canonical notebook, with the notebook identity re-hashed. Offline API
reconnaissance against the pinned commit removed most first-run risk but could not
catch these seams; budget one iteration for live dtype/device issues.

Other durable lessons: content-addressed evidence must be excluded from
formatters/linters and re-hashed after commit; `gh pr create` defaults to upstream,
so pin `--repo` and `--base` for fork-internal PRs; a ratified-but-immutable
canonical notebook plus a disposable run copy preserves provenance while allowing
execution. Full narrative in `CLAUDE_CODE_SESSION_HISTORY.md`.

## 5. Source index (repository paths and commit identities)

Fork `bionicbutterfly13/EvoScientist`, branch `docs/jspace-research-operations`
(fork-internal PR #2). Notebook identity after both runtime fixes:
`353479b0f0e959f2e207446b1383ebf632c05bf8c9a9656508cc91d98d4f28f5`.

| Document | Path | Role |
|---|---|---|
| Scientific report | `sakshi notes/STAGE2_DISCRIMINATION_REPORT.md` | idea to discussion |
| Session history | `sakshi notes/CLAUDE_CODE_SESSION_HISTORY.md` | operational journey |
| Proposal | `sakshi notes/STAGE2_DISCRIMINATION_PROPOSAL.md` | preregistered design |
| Ratified defaults | `sakshi notes/STAGE2_PROVISIONAL_DEFAULTS.md` | the eight answers |
| Baseline reference | `EvoScientist/skills/jspace-research-operations/references/stage2-discrimination-baseline.md` | thresholds, fixes, result, hashes |
| Skill | `EvoScientist/skills/jspace-research-operations/SKILL.md` | bounded protocol, stage gates |
| Notebook | `sakshi notes/jspace_colab_stage2_discrimination.ipynb` | executed design (immutable) |
| Validator | `EvoScientist/skills/jspace-research-operations/scripts/validate_observation.py` | artifact validation |

Commit trail: `d0a7596` ratify, `eb69193` float32 fix, `b7a69ba` cpu fix,
`36c6656` result, `8cf02a5` artifact hashes, `c90b05f` report, `4b25df1` session
history.

## 6. Runtime facts and how Archimedes starts the run (verified 2026-07-24)

- EvoScientist backend: langgraph dev on `127.0.0.1:6174` (running). Main graph id
  `EvoScientist` (`EvoScientist.langgraph_dev.main_graph:EvoScientist_agent`).
  Specialized graphs also present (writing-agent, data-analysis-agent, scheduler,
  evomemory workers).
- Model routing: provider `openai`, model `gpt-5.6-sol`, reasoning effort high,
  routed through ccproxy on `127.0.0.1:8000` (healthy). ccproxy config at
  `~/.config/evoscientist/ccproxy.toml`.
- Memory: observations enabled (`memory_observations_enabled: true`,
  `memory_observation_writer: all`, profile enabled). EvoScientist memory lives in
  `~/.evoscientist/memories/observations/{global,projects}`; threads in
  `~/.evoscientist/sessions.db`. Running the task through EvoScientist writes
  observations here natively; this is what makes EvoScientist aware.
- UI backend: `webui`. WebUI process was stopped during this session.
- Config: `~/.config/evoscientist/config.yaml`, MCP at `~/.config/evoscientist/mcp.yaml`.

Start options (Archimedes / Dr. Mani chooses):
1. WebUI (human-facing, recommended): start it (for example `EvoSci --ui webui`),
   open `http://127.0.0.1:4716/?assistantId=EvoScientist`, new thread, paste the
   task in section 1. This surfaces the multi-agent work and writes to memory.
2. Langgraph API (programmatic): create a thread and run against graph_id
   `EvoScientist` on `http://127.0.0.1:6174` with the section-1 task as input.
   `POST /threads`, then `POST /threads/{id}/runs` (or `/runs/stream`).
3. CLI: `EvoSci` (note: `--help` launches the app rather than printing help;
   confirm the task-passing flag interactively).

## 7. Acceptance criteria for a well-informed run

- EvoScientist loaded the `jspace-research-operations` skill and stayed inside its
  stage gates (no promotion beyond evidence class 1).
- It read the source documents and restated the hypothesis and methods accurately.
- It analyzed the ambiguity decision and either agreed or gave a reasoned
  disagreement, with a genuine skeptical/adversarial pass.
- It captured the two runtime bugs and the specificity failure as lessons.
- It recommended a concrete next iteration.
- It wrote observations to `~/.evoscientist/memories/observations/` so future
  EvoScientist sessions and Archimedes recall this study.

## 8. Do not

- Do not re-run the Colab experiment; it is complete.
- Do not transfer or download the evidence artifacts (separate authorization gate,
  not exercised).
- Do not push to the public upstream; fork-internal only.
- Do not promote any readout beyond evidence class 1 or authorize Stage 3,
  publication, or Sakshi/Elume integration; the decision was ambiguity.
