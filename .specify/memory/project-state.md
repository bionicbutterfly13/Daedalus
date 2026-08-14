# Project state — Archimedes / EvoScientist

Durable grounding for any agent or human picking this up. Companion to
`constitution.md` (which holds the rules; this holds the situation).

Last updated: 2026-07-31.

> This file is the **tracked** durable copy. `.gitignore:50` ignores
> `.specify/memory/*` except the explicit entries retained for project governance;
> verify with `git ls-files .specify/memory/` rather than trusting ignore behavior.
>
> Root `AGENTS.md` and `CLAUDE.md` are gitignored (`.gitignore:57-58`) local
> mirrors that summarize this file and load automatically into agent sessions.
> When the situation changes, update this file first.

## What this repo is

The EvoScientist agent runtime, plus the **J-space cognitive lab** built on it.
The lab's entire current purpose is to decide whether Anthropic's Jacobian Lens
is a real measurement instrument, *before* anything downstream (Elume consuming
observations, Sakshi auditing lineage) is built on that assumption.

This is a fork (`bionicbutterfly13/Daedalus`) of a public upstream. Nothing
goes upstream.

## Where the science is

- **Stage 1** proved self-consistency only — the same readout twice, max logit
  difference 0.0. Reproducibility, not information.
- **Stage 2** ran 2026-07-24 on a Colab T4 (run
  `f9234a9c-6a2d-43da-9fbd-bf26b19ac18c`, n=50). Median Jacobian-vs-logit-lens
  top-10 Jaccard 0.194. Specificity cleared the random-vector control (1.00) but
  failed both structure-broken controls (shuffled-layer 0.22, mismatched-probe
  0.40, against a 0.80 bar). **Decision: ambiguity.**
- **2026-07-25** the completed study was processed through the real EvoScientist
  engine (thread `019f9a2a-5b5a-7d13-80ea-11622e8de7a3`, four observations
  written to `~/.evoscientist/memories/observations/projects/P-a60fb67e40fc59be/`).
  It agreed with ambiguity and audited the notebook against its own
  preregistration.
- **2026-07-26** its three findings were verified against the executed notebook
  and the record was amended: the implemented added-information gate omitted the
  preregistered output and prompt-only clause; declared inference seed `[1]` was
  never executed; specificity used one random-vector seed of the three computed.
  Decision remains ambiguity.
- **2026-07-31 Stage 2b pilot** completed on an authorized Colab T4 with the
  ratified dual-floor fully crossed 8×8 design. The sensitivity-floor correct
  effect and interaction were positive at all four layers under both 99%
  interval methods. The primary floor retained only two eligible arithmetic
  prompts per layer, below the preregistered minimum of three, so every required
  primary-floor inference and threshold derivation is undefined. **Result:
  operational success, scientifically informative prompt-floor dependence, no
  robust Stage 2b pass, and no confirmation readiness.**

**Current standing: the pilot is direct runtime evidence, but nothing is promoted
to a functional, cognitive, or phenomenal claim. No Stage 3, confirmation,
artifact transfer, or downstream integration is authorized. Public documentation
may report the bounded pilot result and its limitations.**

The open question is now narrower: the fitted map showed input-specific advantage
under the layer-0 sensitivity floor, but the primary decoded-embedding floor could
not support the preregistered analysis. The next design must explain or resolve
that floor dependence before confirmation.

## The plan

`specs/001-jspace-stage2b/` defines the recovered Stage 2b measurement contract.
The repaired integration-smoke hashes were authorized once and completed on
2026-07-30. That authorization is spent and does not authorize a pilot, a repeat
smoke, artifact transfer, or any later source identity.

Ratified structure:

1. Target: the model's own argmax token.
2. Floors: `input_embedding_decoded` primary and
   `layer0_residual_decoded` sensitivity, with `sensitivity_minus_primary`.
3. Full 8 donor-assignment by 8 broken-map crossing per prompt/layer.
4. Compact storage of 81 unique readouts with lossless reconstruction of 64
   logical factorial combinations and complete donor/map provenance.
5. SHA-256-derived donor, map, and bootstrap identities using explicit `PCG64`.
6. One 0.05 linear denominator guard derived from all 80 primary denominators,
   followed by both-floor NTA without another model/lens pass.
7. Fixed floor-layer exclusions, 18/20 and 3/4-per-category pilot coverage, and
   category-balanced means.
8. A 20,000-replicate category-stratified prompt interval as primary and a
   prompt×donor×map product-weight interval as sensitivity, both two-sided 99%
   linear percentile intervals.
9. Half-positive-primary-means pilot threshold derivation and a later
   all-components-required confirmation claim.

The denominator guard was derived during the pilot as `0.3388633415411974`.
Effect-threshold vectors remain unset because the primary-floor source means were
undefined. The pilot authorization is consumed; confirmation execution remains
unauthorized. Wrong-layer policy is deferred and absent from the executable
pilot. The confirmation sample's per-category coverage minimum remains unratified.

## Repo state

Controlled recovery is isolated in:

- branch: `recover/jspace-stage2b-contract`
- worktree: `/Volumes/Asylum/archimedes-recovery-jspace-stage2b`
- historical base: `fa7980b56a091d9bbd6e32d4136ddcfccbc6d867`

The historical commit is provenance, not implementation authority. The original
worktree `/Volumes/Asylum/Daedalus` remains dirty and preserved; it was used only
as a file-by-file salvage source. No commit, push, or PR operation occurred during
recovery.

Current recovered implementation includes the compact dual-floor endpoint,
two-stage score/NTA producer, fail-closed preflight and external authorization
record, deterministic crossing and bootstrap identities, both ratified interval
engines, threshold derivation, canonical static notebook producer, deterministic
pilot code bundle, synthetic 20×4×81 statistical harness, and recursively
recomputing aggregate validator. Pilot artifacts cannot carry gates or a decision.
Wrong-layer policy remains absent rather than dormant.

Fresh CPU/static verification on 2026-07-30 after the statistical implementation:

- focused statistics/preflight/notebook/harness/bundle/validator suite:
  317 passed in 175.11 seconds;
- complete J-space suite: 464 passed in 81.72 seconds on the final
  post-reconciliation rerun;
- complete repository suite: 3,522 passed, 12 skipped, with two unrelated
  deprecation warnings, in 162.35 seconds on the final rerun;
- repository-wide Ruff: all checks passed, 417 files formatted;
- all four retained notebooks: 31 ordinary code cells parsed;
- deterministic bundle tests and `git diff --check`: passed.

On 2026-07-29 the first exact-hash-authorized excluded-input integration smoke
uploaded only its notebook and code bundle, allocated one Tesla T4 with 15,360 MiB,
and passed bundle, package, commit, model-revision, lens-revision, CUDA, and
excluded-input checks. It stopped before model download with a mixed live NumPy
module `ImportError`. No pilot/confirmation input was accessed, no runtime report
was generated, and no artifact was transferred. The repaired notebook now requires
a fresh Python process after the pinned install.

On 2026-07-30 Dr. Mani authorized the repaired notebook
`9c31cfa540c5feccfb664e1c21cc0bcdf07d09628c4655caaf10ff08da95e07a`
and bundle
`226152be91708c438a7a96b3bf46d8ddd80760a1c920013db71c16743a05d3e6`.
The disposable launch copy and bundle were uploaded to a new Colab execution,
and the exact bundle/capacity gate passed on one Tesla T4 with 15,360 MiB. The
pinned install completed, the same session restarted, the fresh-process sentinel
passed, and package/source/commit/revision/excluded-input checks passed. Cell 9
then stopped before model-weight load: Transformers class resolution triggered
`RuntimeError: operator torchvision::nms does not exist`, followed by
`ModuleNotFoundError: Could not import module 'Qwen3ForCausalLM'`. No lens,
pilot input, confirmation input, runtime report, or artifact transfer ran. The
control interruption and final failure boundaries are recorded in
`runs/stage2b-integration-smoke-repair-20260729/second-authorized-attempt-control-interruption.json`
and
`runs/stage2b-integration-smoke-repair-20260729/second-authorized-attempt-failure.json`.
Real model/lens integration, pilot readiness, confirmatory readiness, and
scientific readiness remain unverified.

Dr. Mani approved the smallest dependency repair: remove optional Torchvision
instead of adding a vision wheel or changing the pinned Torch version. The
canonical notebook binds that removal into install schema
`stage2b-colab-runtime-install/v2`, requires Torchvision to be absent before
Transformers import, and records the result under runtime-report schema
`jspace-stage2b-integration-smoke/v3`. Authorized identities were:

- notebook:
  `e3e0cdcfa73732138dcfaf374f9946a7993f1647cb424f8acbed91cf3ae9b5fc`;
- code bundle:
  `4f18c96303d1451941ca050e3159e12b31b5d8d8dba4d8981a1a03e118f4cbfb`.

The exact-hash-authorized third attempt completed on one Tesla T4 with 15,360 MiB
VRAM. It verified the pinned package, model, Jacobian Lens, and fitted-lens
identities; captured nine excluded inputs; probed all four selected layers; and
completed one 81-readout/64-logical-crossing measurement at layer 13 in
1.14064654 seconds. Peak CUDA allocation was 4.074223 GiB and peak reservation
was 4.095703 GiB. Model load took 166.485052 seconds, lens load 4.259576
seconds, nine-input capture 4.914328 seconds, and selected-layer parity probes
0.041844 seconds.

The runtime-only report was retained in Colab at
`/content/jspace_stage2b_integration_smoke/stage2b_integration_smoke_71b58ce846d319c6.json`;
its SHA-256 is
`71b58ce846d319c6c26562a7765c67ab3a3468609f67306d8a767ea8f73a477c`
and its recorded size is 5,172 bytes. The transfer cell remained unexecuted, so
the report was not downloaded or copied into this repository. No pilot or
confirmation input was accessed. The report's 91.251723-second extrapolation to
6,480 readouts is labelled an engineering projection, not measured pilot
runtime. A later check found this transient report absent from the active
`/content` runtime. That state is consistent with a reset or replacement, but
the precise lifecycle event is unknown; its verified identity and bounded public
record remain.

This success establishes bounded runtime compatibility only. The subsequent
adversarial findings in target derivation, excluded-floor propagation, recursive
schema closure, authorization transition, tensor contracts, and dormant
unratified policy were repaired and covered by focused corruption tests. The
ratified statistical amendment has now been implemented and locally verified.

The first statistical freeze
`5ff349974f704dc6d4f92da511987353fab4ae318d3ab256e73bbbf24213be8a`
received an independent NO-GO. Its four findings were exact source identity
asserted by operator input, donor realization not recomputed from its seed,
missing per-realized-map spectrum evidence, and bundle extraction into a reusable
directory. The recovery now uses an external exact-byte launch preparer, requires
trusted source identities outside the artifact, recomputes deterministic donor
selection, retains and validates full spectrum evidence for every map, and
extracts into a verified exclusive directory. Control construction reuses one
fitted-map decomposition per layer and independently checks all eight realized
map spectra under implemented `rtol=1e-5`, `atol=1e-6`.

Fresh final-source validation after the repairs returned `409 passed` focused,
`487 passed` J-space, and `3545 passed, 12 skipped` repository-wide with two
unrelated deprecation warnings. Seven deterministic bundle/launch tests passed;
Ruff was clean; all 419 files were formatted; 54 ordinary code cells parsed
across seven notebooks; and `git diff --check` passed. The superseding freeze then
received independent PASS/GO, the exact source identities received one-time pilot
authorization, and the 2026-07-31 pilot completed as recorded above.

## Publication and post-pilot diagnostic status — 2026-07-31

The recovery and curated public record merged through fork-internal PR #9 as
`e2a20c49a2a719d85bf54f71f73f074ef831058a` after all seven CI checks passed.
Historical PR #8 was closed as superseded. The GitHub Wiki was initialized and
published at commit `f81e8d3`; all 12 tracked `docs/wiki/*.md` pages matched a
fresh clone byte-for-byte and the rendered Home page, Mermaid diagram,
navigation, and sidebar were verified in GitHub.

The primary-floor diagnostic was frozen before prompt-level inspection. Source
commit `3c26569b0d3fe4bb8a5fa79d311b231418cdb85c`, source SHA-256
`f8bf8563ec8085ab0ca98bbf266aa93ee346ef7917abc7e5287d93d1b0edc32b`,
independent verdict GO, `495 passed` J-space, `3553 passed, 12 skipped`
repository-wide, and six green CI checks. Fork-internal PR #10 merged as
`66fe6843854f380e5eec7bc17c46207c3c9c0544`.

The first bounded Colab diagnostic attempt then stopped before reading either
input. The active `/content` runtime no longer contained the artifact or pilot
view; a filename-only probe found only `.config` and `sample_data`. This is
consistent with a Colab runtime reset or replacement, but the precise lifecycle
event is unknown. The artifact was not reconstructed, uploaded, downloaded, or
transferred, and confirmation was not accessed. The pilot artifact had been
retained at run completion, but it is no longer present in the active Colab
runtime. No prompt-level mechanism association has therefore been established.

## Open items

1. Decide how to obtain lawful mechanism evidence now that the transient Colab
   artifact is absent. Do not reconstruct, upload, or rerun without a separate
   explicit decision and, where applicable, new authorization.
2. Use `j-space-lab/STAGE2B_PRIMARY_FLOOR_OPTIONS_PACKET.md` to decide whether
   the decoded-input-embedding ambiguity motivates Options A through D or the
   terminal stop in Option E. No option is yet selected.
3. Keep the 180-prompt confirmation runtime-sealed. Do not derive or ratify
   confirmation thresholds unless a future primary-floor pilot analysis is
   defined.
4. Repair the EvoScientist headless direct-authorship path separately: the
   2026-07-31 publication attempt was stopped because workspace identity could
   not be proven, and `notebooklm-mcp` failed while loading tools. No Evo-authored
   journal entry was accepted from that attempt.

## Runtime facts

- **Verifying a branch in a git worktree against the shared editable install is
  unreliable in two distinct ways, and both produce false failures.** First, run
  it with the venv on `PATH` — tests that shell out to `python` (not `python3`)
  otherwise fail with `command not found`. Second, set
  `PYTHONPATH=<worktree>` — tests that spawn a subprocess with a different `cwd`
  resolve `EvoScientist` through the editable install, which points at the *main
  tree*, so they silently test the wrong branch. Both bit during the #5/#6
  verification and both looked like real defects in the branch under test.
- Stack: ccproxy `:8000`, langgraph `:6174`, WebUI `:4716`.
- Model `gpt-5.6-sol`, provider openai, reasoning effort high, via ccproxy Codex.
- Start: `cd "<workdir>" && EvoSci --ui webui --workdir "<workdir>"`, using
  the `j-space-lab` subdirectory in the selected worktree. It contains no
  `EvoScientist/` package. Cold start was previously measured at 70–120s.
- `dangerous_mode: true` and `auto_approve: true` in
  `~/.config/evoscientist/config.yaml`, left on deliberately so long autonomous
  runs work. The upstream push path is hard-disabled instead, which is what
  closes the irreversible risk.

## Spec Kit template drift — decision, 2026-07-26

**Decision: do not refresh the shared templates and scripts. Correct the version
label instead.** Recorded here rather than acted on silently, because Codex reads
those files.

The situation: `.specify/integrations/speckit.manifest.json` and
`claude.manifest.json` both declare version `0.13.3.dev0`, matching the installed
CLI. `codex.manifest.json` still declares `0.11.10`. But the shared files under
`.specify/scripts/` and `.specify/templates/` are 0.11.10 *content* — the version
field was bumped when Claude was installed; the files were not.

Measured, not assumed. Installing 0.13.3.dev0 into a scratch directory and diffing
the ten shared files against ours:

| File | Status |
|---|---|
| `scripts/bash/common.sh` | **differs** — 115 changed lines |
| `scripts/bash/create-new-feature.sh` | **differs** — 87 changed lines |
| `scripts/bash/check-prerequisites.sh` | **differs** — 20 changed lines |
| `scripts/bash/setup-plan.sh` | **differs** — 15 changed lines |
| `templates/checklist-template.md` | **differs** — 6 changed lines |
| `templates/plan-template.md` | **differs** — 2 changed lines |
| `scripts/bash/setup-tasks.sh`, `templates/{constitution,tasks,spec}-template.md` | identical |

The CLI surface changed too: `specify init --ai claude` is gone in 0.13.3.dev0,
replaced by `--integration claude`.

**Why not refresh.** The 0.11.10 scripts are what produced `specs/001-jspace-stage2b/`,
and they work — `setup-plan.sh`, `setup-tasks.sh`, and `check-prerequisites.sh` all
ran correctly this session. `create-new-feature.sh` and `common.sh` are the two
most-changed files and are exactly the ones Codex invokes for feature creation and
branch resolution. Swapping 200 lines of shell underneath a working setup, for no
observed defect, inverts the priority order: correctness and evidence outrank
consistency, and there is no evidence of a problem to fix.

**What is actually wrong** is narrower and worth fixing: two manifests assert
0.13.3.dev0 over 0.11.10 content. That is a record overstating what it describes
(Principle V) in miniature — the file hashes are all intact and self-consistent, so
nothing is corrupt, but the version label is not true of the files it labels.

**Recommended fix, deferred to Dr. Mani** because it touches Codex's files: either
set `speckit.manifest.json`'s version back to `0.11.10` to match its content, or
run `specify integration upgrade --force` to make the content match the label — and
if the latter, re-run the Spec Kit flow afterwards to confirm the newer scripts
still resolve this repo's feature layout. Not both, and not neither.

## Authoritative documents

| Document | Role |
|---|---|
| `.specify/memory/constitution.md` | governing rules |
| `specs/001-jspace-stage2b/spec.md` | current feature spec |
| `j-space-lab/HANDOFF_2026-07-26.md` | full lab state *(docs branch)* |
| `j-space-lab/STAGE2B_DESIGN.md` | Stage 2b design in full *(docs branch)* |
| `j-space-lab/STAGE2B_OPEN_PARAMETERS.md` | the ten questions *(docs branch)* |
| `j-space-lab/STAGE2_DISCRIMINATION_REPORT.md` | the study, as amended *(docs branch)* |
| `j-space-lab/CCPROXY_UPSTREAM_ISSUE_DRAFT.md` | drafted, unfiled *(docs branch)* |

*(docs branch)* = `docs/jspace-research-operations`, checked out at
`/Volumes/Asylum/archimedes-wt-jspace`.
