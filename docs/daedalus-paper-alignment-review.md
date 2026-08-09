# Daedalus vs the EvoScientist paper: alignment review

- Date: 2026-08-08; re-verified 2026-08-09 after upstream sync
- Reviewed tree: originally `3339a11` (v0.2.3); re-verified on `57e144e` (post-merge, upstream V0.2.6)
- Also reviewed: installed skills at `~/.EvoScientist/skills` (source `EvoScientist/EvoSkills@skills`)
- Paper: [arXiv 2603.08127v1](https://arxiv.org/html/2603.08127v1), *Towards Multi-Agent Evolving AI Scientists for End-to-End Scientific Discovery*
- Independent verification: codex-cli 0.147.0, read-only, against the same tree
- Status: findings only. No code changed.

**Terminology.** "Daedalus" is our deployed fork plus its installed skills, wrapped and
CLI-driven by Hermes. "the paper" and "the reference implementation" mean upstream
EvoScientist.

---

## The 14 gaps at a glance

P0 = silently invalidates an unattended run. P1 = changes scientific behavior vs the paper. P2 = hygiene.

| # | Out of parity | Sev | Whose bug | Status |
|---|---|---|---|---|
| F1 | The paper's method is prompt files installed outside the repo; `skill_manager` can swap it mid-run, and nothing records which version produced a result | P1 | upstream (design) | mitigated: runs now pin skill digests (T007) |
| F2 | No Evolution Manager agent exists; IDE/IVE/ESE are optional prose nothing obliges the model to run | P1 | upstream engine | mitigated: post-run enforcement (T008) |
| F3 | **Evolution memory has no writable persistent path.** Skills write `/memory/` (unmounted, per-run); `/memories/` refuses all raw writes | **P0** | upstream engine | **unfixable by us** — queued as U1; we pin the workspace as a workaround (T001) |
| F4 | Retrieval is keyword/LLM-judged, not the paper's embedding cosine; `k_I=2`/`k_E=1` unreproducible | P1 | upstream engine | mitigated: selections recorded (T010) |
| F5 | The Elo tournament ranks 3 candidates, so "top-3" is the whole field and selects nothing. The skill's own reference specifies 15-21 | P1 | upstream skills | already reported upstream as EvoSkills #33; local addendum (T009) |
| F6 | Under `stream-json`, auto-mode **removes** `ask_user`. Human decision gates become inert text the model may narrate or ignore. Docs claim they're "auto-handled" | **P0** | upstream engine | mitigated: gate policy declared + narration audit (T004); queued as U2 |
| F7 | Attempt budgets match (20/12/12/18), but best-code selection uses pass/fail gates instead of argmax, and the paper's fixed 3+4 worker topology is absent | P1 | upstream | not addressed |
| F8 | ESE fires only if all 4 stages pass; the paper imposes no such condition. At the paper's own ~21% stage-3 rate it would almost never fire | P1 | upstream skills | fix written (T008); queued as U5 |
| F9 | No per-role model routing out of the box; async agents hardcode the main model, so the paper's Gemini-for-writing is unreachable | P1 | upstream | **blocked, needs your decision** (D-2) |
| F10 | Package tagline differs from the paper title | P2 | upstream branding | no action — not a defect in this fork |
| F11 | Two broken doc links in our architecture doc | P2 | **ours** | fixed (T014) |
| F12 | Nothing makes the pipeline mandatory; a run can emit `done` having skipped ideation, the tournament, and every memory update | **P0** | upstream engine | mitigated: artifact gate (T003) |
| F13 | M_I/M_E bypass the engine's memory write protections entirely | P1 | upstream | documented + hashed (T012) |
| F14 | Stage evidence is prose plus a checkbox; `C_best`, budget use, and gate status are unverifiable | **P0** | upstream skills | mitigated: structured stage records required (T005) |

Found during remediation, not in the original review:

| # | Issue | Status |
|---|---|---|
| — | The architecture doc's July 16 episodic-memory account cites two files that never existed in git history | **needs your call** (D-3 / T018) |

## Plain-language summary

The paper's contribution is accumulation: the system keeps two notebooks across projects
(research directions tried, technical strategies that worked) and reads them before each
new cycle, so cycle 10 starts smarter than cycle 1. Remove that and it is an ordinary
research agent.

Three things break that accumulation in the current deployment:

1. The notebooks are written to a per-job scratch directory instead of the system's
   permanent memory directory (F3).
2. Nothing in the runtime requires the notebooks to be updated at all (F12).
3. When a notebook is missing, the system's own instructions read that as "first cycle,
   skip this step" — so a wiped notebook is indistinguishable from a fresh start (F3).

Combined effect: Daedalus can run for months reporting clean cycles while starting from
zero every time. This is the silent-success failure mode already flagged in `CLAUDE.md`.

---

## What the paper specifies

3 agents (Researcher RA, Engineer EA, Evolution Manager EMA); 2 persistent memories
(Ideation `M_I`, Experimentation `M_E`); Idea Tree Search with `N_I=21` max candidates
feeding an Elo tournament, retaining Top-3, with proposal `P = Extend(Top-1)`; 4-stage
Experiment Tree Search with attempt budgets `N_E = 20/12/12/18` and best-code selection
`C_best^s = argmax` over attempt scores; 3 evolution mechanisms IDE / IVE / ESE, where ESE
distills from best codes **and** full search trajectories with no success precondition;
embedding retrieval (mxbai-embed-large via Ollama, cosine) with `k_I=2`, `k_E=1`;
3 parallel ideation workers and 4 parallel experimentation workers; Gemini-2.5-Pro for
literature review, ideation, and writing, Claude-4.5-Haiku for code generation.

---

## Findings

Severity: **P0** blocks or silently invalidates an unattended Hermes-driven run.
**P1** changes scientific behavior versus the paper. **P2** hygiene.

### F1 — The paper's method lives entirely in the skills layer, not the engine (P1)

Verdict: CONFIRMED.

A scan for 19 paper-specific terms (Evolution Manager, ideation memory, experimentation
memory, IdeaTreeSearch, ExperimentTreeSearch, EloRank, Researcher Agent, Engineer Agent,
SummarizeExecution, tournament, …) returns zero matches across the repository's Python,
YAML, JSON, TOML, and Markdown. The method exists only as procedural Markdown in
`~/.EvoScientist/skills/{research-ideation,experiment-pipeline,evo-memory}`, installed from
a separate source (`skills/.installed.yaml:1,13,40`) outside this repository.

Consequences: the scientific method Daedalus follows is not pinned by the repo, not covered
by its tests, and `skill_manager` can install or replace it mid-run. No run manifest records
which skill versions produced a given result.

Qualification found in verification: `.gitignore:43` excludes this repo's top-level
`skills/*`, but does not govern the home-directory installation. The skills are untracked
because they live outside the repo, not because of that ignore rule.

### F2 — No Evolution Manager agent exists (P1)

Verdict: CONFIRMED; my original count was wrong.

Paper §3.5 makes EMA a first-class agent. `EvoScientist/subagents/` ships **seven** agent
YAMLs — planner, research, code, debug, data_analysis, writing, scheduler
(`subagents/scheduler.yaml:1`) — plus a runtime general-purpose subagent
(`EvoScientist.py:368`). None is an evolution manager. IDE / IVE / ESE remain skill
instructions (`evo-memory/SKILL.md:73`) with no runtime enforcement.

### F3 — `M_I` / `M_E` are written to an unmounted path (P0)

Verdict: CONFIRMED in default (safe) mode. This is the highest-severity finding.

The agent sees a virtual path tree assembled by a `CompositeBackend` route table
(`EvoScientist.py:654`, and again at `:1035`). Two prefixes are routed:

| Virtual path | Backend | Real location | Lifetime |
|---|---|---|---|
| `/skills/` | `MergedSkillsBackend` | skills dirs | global + workspace |
| `/memories/` | `MemoryFilesystemBackend` | `~/.evoscientist/memories/` (`paths.py:51`) | global, survives every run |
| *(no match)* | `CustomSandboxBackend` | `WORKSPACE_ROOT` = cwd (`paths.py:26`, `EvoScientist.py:1019`) | one workspace |

The skills write to `/memory/ideation-memory.md` and `/memory/experiment-memory.md` — no
trailing `s`. `/memory/` has no route, so it falls through to the default backend and
resolves to `<workdir>/memory/…`. This is the classic unmounted-mount-point failure: every
write succeeds, nothing warns, and the bytes land on the wrong volume.

The repo's own test suite labels `/memory/` "Project-local"
(`tests/test_stream_utils.py:135`), confirming the intent is workspace scope.

Therefore any two runs with different workdirs do not share `M_I` or `M_E`. Compounding it,
`evo-memory/SKILL.md` instructs: *"If M_I doesn't exist yet (first cycle), skip this step"* —
so a lost memory and a genuine first run are indistinguishable to the agent.

Caveat: `dangerous_mode=True` repoints the default backend at real host paths
(`config/settings.py:430`), but it is off by default.

### F4 — Retrieval is not embedding-based (P1)

Verdict: CONFIRMED for memory retrieval.

The paper specifies cosine similarity over mxbai-embed-large embeddings served by Ollama,
selecting `k_I=2` and `k_E=1`. No package code instantiates an embedding model; Ollama
appears only as a chat-model provider (`llm/models.py:697`). `memory/search.py` tokenizes,
computes IDF, and scores token overlap (`:62`, `:212`). `evo-memory/SKILL.md` substitutes
LLM judgment: "read each entry's Summary and Retrieval Tags."

Consequences: top-k selection is not reproducible; memory must be read wholesale into
context, so quality degrades as it grows; the paper's ablation magnitudes do not transfer.

### F5 — The Elo tournament ranks 3 candidates, not up to 21 (P1)

Verdict: CONFIRMED.

`research-ideation/SKILL.md` Step 3 creates exactly three initial ideas (`:95`); Step 4
produces one champion per each of three tracks (`:127`); Step 5 tournaments those champions
(`:155`). The "Top-3" presented is therefore the entire field — the ranking selects nothing.

The skill's own reference prescribes a 3-level tree yielding 15–21 leaves
(`references/tree-search-protocol.md:69`), which the workflow never builds. `SKILL.md` also
lists "Quantity before quality in generation" as a governing rule it then violates. The
paper tournaments all `N_I` candidates before retaining three.

### F6 — Human selection gates become unenforceable under the Hermes driver (P0)

Verdict: CORRECTED after verification. The mechanism is not what I first reported, and the
real one is worse.

The paper extends the top-ranked idea automatically (`P = Extend(Top-1)`). The skill instead
asks the user to choose (`research-ideation/SKILL.md:215`).

`--output-format stream-json` defaults auto-mode on (`cli/commands.py:2013`). Auto-mode sets
`enable_ask_user = False` (`commands.py:2157`), and `EvoScientist.py:833` gates
`AskUserMiddleware` on `cfg.enable_ask_user and not cfg.auto_mode`. So the `ask_user` tool is
**removed entirely**, not auto-answered. Neither the Step 5 selection nor the Code Generation
Mode Selection — whose prompt says "Do not skip this step or assume a default silently"
(`prompts.py:105`, `:109`) — is resolved by anything. Both degrade to prompt text the model
may satisfy, narrate, or ignore. The outcome is model-dependent and not observable from the
event stream.

Documentation mismatch: `commands.py:2131` and `docs/guides/stream-json.md:28-31` both
describe these gates as "auto-handled", which does not match the implementation.

Related gap: with `--no-auto-mode` the CLI warns that the emitted interrupt ends the run and
is "not yet resumable" (`commands.py:2138`). An external driver cannot honor a human
checkpoint and then continue the same run.

### F7 — Budgets match; best-code selection and worker topology do not (P1)

Verdict: NARROWED after verification.

Attempt budgets `20/12/12/18` match the paper exactly
(`experiment-pipeline/SKILL.md:44`). The skill advances on pass/fail gate conditions and
contains no stage-level argmax (`:53`), where the paper selects `C_best^s = argmax`.

Correction: parallelism is not absent. `prompts.py:328` ("When to Parallelize") explicitly
permits concurrent subagents for independent methods, datasets, or concurrent literature
work. What is absent is the paper's *fixed topology* of 3 ideation and 4 experimentation
workers; the stated default is "Bias towards a single sub-agent" (`prompts.py:314`, `:359`).

### F8 — ESE is gated on full success; the paper's is not (P1)

Verdict: CONFIRMED.

`evo-memory/SKILL.md:123` and `references/ese-protocol.md:5` trigger ESE only after all four
stages complete with all gates met. Paper §3.5 defines ESE over all four stage histories with
no success precondition, distilling from best-performing code *and* full search trajectories.

This is self-defeating on the paper's own numbers: reported Stage 3 success is ~21%, so a
success-gated ESE would rarely fire — yet ESE is precisely what produced the reported
+10.17pp improvement (34.39% → 44.56%). It also contradicts the skill's own rule 5, "Failed
attempts are data, not waste."

### F9 — Per-role model routing exists but is unset and partly unavailable (P1)

Verdict: CORRECTED. My original claim ("no per-role routing exists") is wrong.

The subagent loader accepts a per-agent `model:` key from YAML (`utils.py:221-222`), so sync
subagents can be bound to different models. What actually holds:

- No shipped subagent YAML sets `model:` — all seven omit it — so out of the box every
  scientific role runs on the single main model (`config/settings.py:181`). The only other
  slot, `auxiliary_model`, serves memory workers, tool selector, and scheduler (`:150`).
- Async subagents hardcode the main model except scheduler (`subagents/_factory.py:111`).
  `writing-agent` and `data_analysis-agent` are `async: true`, so they cannot be routed while
  async subagents are enabled. The paper assigns Gemini-2.5-Pro to writing, which is
  therefore unreachable in that configuration.
- The `model:` key is undocumented in the shipped YAMLs.

### F10 — Self-description drift (P2)

Verdict: CONFIRMED. `pyproject.toml:4` reads "Towards Self-Evolving AI Scientists for
End-to-End Scientific Discovery"; the paper is titled "Towards Multi-Agent Evolving AI
Scientists for End-to-End Scientific Discovery". Cite the paper title, not the package
description.

### F11 — Broken documentation link (P2)

Verdict: CONFIRMED. `docs/cognitive-lab-architecture.md:122` and `:374` link `stream-json.md`
relative to `docs/`; the file is at `docs/guides/stream-json.md`.

### F12 — Nothing makes the paper's pipeline mandatory (P0)

Verdict: raised during verification, adopted.

The main prompt calls the skill sequence "recommended", states "Not every project needs all
steps", and delegates compliance to the model (`prompts.py:57`, `:59`, `:70`). An unattended
CLI run can complete and emit `done` having never executed Idea Tree Search, the Elo
tournament, ESE, or either memory update. Nothing in the event stream distinguishes that from
a full cycle.

### F13 — `M_I` / `M_E` bypass the engine's memory write protections (P1)

Verdict: raised during verification, adopted. Not independently re-derived by me.

`MemoryFilesystemBackend` blocks raw memory creation and restricts edits under `/memories/`
(`backends.py:822`). Because `/memory/` reaches the ordinary workspace backend, the paper's
two memories receive none of those controls.

### F14 — Experiment evidence is free-form Markdown, not machine-checkable (P0)

Verdict: raised during verification, adopted.

Attempt scores, code identity, and stage winners are not machine-bound. The stage template
records prose plus a checkbox (`experiment-pipeline/assets/stage-log-template.md:11`), and
"current best" carries no required code pointer or scoring function (`:21`). An external
orchestrator cannot verify `C_best^s`, budget consumption, or gate satisfaction from the
artifacts, which defeats the acceptance gate described in
`docs/cognitive-lab-architecture.md`.

---

## Verification status

Round 1: codex-cli 0.147.0, read-only, against `3339a11` (v0.2.3).

- CONFIRMED as originally written: F1, F3, F4, F5, F8, F10, F11
- CORRECTED after refutation: F2 (agent count), F6 (mechanism), F7 (scope), F9 (substance)
- Raised by verification and adopted: F12, F13, F14

Round 2 (2026-08-09): after merging upstream V0.2.6 (`57e144e`), Codex re-derived
every citation on the current tree. **All 14 findings hold.** Two are updated by the merge:

- **F7 (updated):** upstream `prompts.py` now explicitly supports concurrent in-eval
  `task()` fan-out "for expert panels, ELO-style tournaments" (`prompts.py:328-348`).
  The generic-parallelism gap is closed; still absent are the paper's fixed 3-ideation /
  4-experimentation worker topology and stage-level argmax code selection.
- **F9 (updated):** agent-teams expert containers add dynamic roles but no model routing:
  sync expert specs carry no model, async standard/expert containers hardcode the main
  model except scheduler (`expert_container.py:149-158`, `_factory.py:115-124`,
  `expert_container_async.py:358-364`). The per-agent `model:` YAML key survives
  (`utils.py:205-223`), still unset in every shipped YAML.
- **F2 (re-checked):** expert containers are generic skill wrappers, not an Evolution
  Manager; IDE/IVE/ESE remain unenforced skill prose.

The same round verified the 8 merge conflict resolutions (settings.py fork precedence,
runtime package relocation, models.py sanitizer predicate, webui dual features,
manager.py dual constants, test suites) — all confirmed, with the note that
`_inject_subagent_middleware`'s cfg fallback yields an equivalent config object, not the
identical instance. The one failing test on the merged tree
(`test_timeout_bounds_drain_when_detached_descendant_holds_pipes`) is byte-identical to
upstream/main and fails on pristine upstream v0.2.6: pre-existing, not merge-caused.

Not independently re-derived: the paper's own figures (`N_I=21`, `k_I`, `k_E`, attempt
budgets, reported success rates) come from arXiv 2603.08127v1 as fetched, not from a local
copy. F13 and F14 rest on Codex's citations (re-confirmed in round 2), not my own line-by-line
read.

Not yet tested at runtime: no Daedalus run was executed. F3's practical impact should be
confirmed empirically by running two consecutive jobs in different workdirs and checking
whether the second recalls the first.

---

## Related documents

- [Archimedes Cognitive Lab Architecture](cognitive-lab-architecture.md) — the Hermes /
  EvoScientist authority boundary this review tests against
- [stream-json protocol](guides/stream-json.md) — the documented Hermes driver surface
