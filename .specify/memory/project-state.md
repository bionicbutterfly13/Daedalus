# Project state — Archimedes / EvoScientist

Durable grounding for any agent or human picking this up. Companion to
`constitution.md` (which holds the rules; this holds the situation).

Last updated: 2026-07-26.

> This file is the **tracked** copy — but only as of 2026-07-26. `.gitignore:50`
> ignores all of `.specify/memory/*` with a single exception for
> `constitution.md`, added by the Spec Kit init before this file existed, so this
> file was invisible to git when written. A matching `!` exception was added; verify
> with `git ls-files .specify/memory/` rather than trusting `git status`, which
> shows nothing either way for an ignored file.
>
> Root `AGENTS.md` and `CLAUDE.md` are gitignored (`.gitignore:57-58`) local
> mirrors that summarize this file and load automatically into agent sessions.
> When the situation changes, update this file first.

## What this repo is

The EvoScientist agent runtime, plus the **J-space cognitive lab** built on it.
The lab's entire current purpose is to decide whether Anthropic's Jacobian Lens
is a real measurement instrument, *before* anything downstream (Elume consuming
observations, Sakshi auditing lineage) is built on that assumption.

This is a fork (`bionicbutterfly13/EvoScientist`) of a public upstream. Nothing
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

**Current standing: nothing is promoted beyond evidence class 1. No Stage 3,
publication, artifact transfer, or Sakshi/Elume integration is authorized.**

The open question, sharpened: the readout is not identical to a cheap baseline
and is not noise, but nothing yet separates it from what *any* layer-sized
Jacobian transport would produce.

## The plan

`specs/001-jspace-stage2b/` — **Stage 2b, designed and planned, not authorized to
run.** The spec is joined by `plan.md`, `research.md`, `data-model.md`,
`contracts/`, `quickstart.md`, and a 56-task `tasks.md`. All 56 tasks produce
files; none runs a measurement.

It fixes two structural defects that made Stage 2 unanswerable:

1. Stage 2's endpoint measured how much two readouts *differ*, with no notion of
   correct — so the strongest possible conclusion was always non-identity,
   whatever the sample size. Replaced with a target-relative endpoint normalized
   between the prompt-only floor and the output ceiling.
2. Stage 2's controls each moved two factors at once, so when they failed, the
   cause was unrecoverable. Replaced with a 2×2 factorial crossing
   correct/wrong activation against correct/fit-broken map.

Ten open parameters need ratification before execution. Three are flagged not
delegable: **Q3** (what counts as the target — it defines what the study means by
"information"), **Q5** (the specificity threshold — the recommendation is
deliberately *not* to set it now, but to derive it from a pilot), and **Q10**
(execution authorization).

## Repo state

Four open fork-internal PRs, all green, none merged:

| PR | Branch | Contents | Suite, standing alone |
|---|---|---|---|
| #5 | `fix/ccproxy-codex-streaming` | per-call streaming middleware + 16 tests | 3052 passed, 12 skipped |
| #6 | `fix/oauth-startup-robustness` | dotenv precedence + langgraph health budget | 3042 passed, 12 skipped |
| #2 | `docs/jspace-research-operations` | provenance amendment + Stage 2b design | docs only |

Suite sizes: main alone 3036; #5 adds 16; #6 adds 6; all together 3058. Each
branch was verified green *standing alone*, not only in combination — the counts
above are the standing-alone figures, which is what a reviewer sees.

| #7 | `chore/speckit-claude-integration` | Spec Kit setup + the full Stage 2b plan | 3036 passed, 12 skipped |

PR #7 branches from `main` and is docs/config only, so its suite result is the
`main` baseline unchanged — expected for a branch that touches no source.

**One commit exists locally and is deliberately not pushed.** `66d03ab` on
`docs/jspace-research-operations`, in the worktree at
`/Volumes/Asylum/archimedes-wt-jspace`, reduces `HANDOFF_2026-07-26.md` to
lab-specific detail plus a pointer at this file, and corrects its Bug B suite
figure from 3058 to the standing-alone 3052. It was left unpushed because pushing
would amend PR #2 while it is under review. Push it whenever that is convenient:

```sh
git -C /Volumes/Asylum/archimedes-wt-jspace push origin docs/jspace-research-operations
```

**The main tree is deliberately left checked out on `fix/ccproxy-codex-streaming`.**
The runtime is an editable install from it, so returning to `main` and restarting
the stack would silently reintroduce the empty-answer bug. Merge #5 first.

Docs-branch worktree: `/Volumes/Asylum/archimedes-wt-jspace`.

## Open items

1. Review and merge PRs #5, #6, #2, #7. Merge #5 before returning the main tree to
   `main` and restarting the stack. Push `66d03ab` on the docs branch when
   convenient (see Repo state) — it is the only work not on GitHub.
2. Ratify or revise `sakshi notes/STAGE2B_OPEN_PARAMETERS.md` (ten questions).
   Q3, Q5, and Q10 are flagged not delegable.
3. File the upstream ccproxy issue if wanted — drafted at
   `sakshi notes/CCPROXY_UPSTREAM_ISSUE_DRAFT.md`, deliberately not filed.
4. Optionally disconnect the Colab T4 if still attached.
5. **Decide whether the Stage 2 record needs a second amendment.** The
   2026-07-26 audit recorded three preregistration/implementation divergences.
   Reading the notebook against its own ratification checklist while planning
   Stage 2b surfaced a fourth of the same class:
   `output_argmax_rank_in_jacobian` / `output_argmax_rank_in_other` are computed
   per-locus and written into every per-prompt artifact, but no gate reads them —
   while the notebook's ratification checklist lists "downstream criterion: the
   model's own next-token output" as ratified. So a downstream criterion was
   declared, computed, stored, and never allowed to touch a decision.

   Detail and evidence: `specs/001-jspace-stage2b/research.md` R7. Amending a
   content-addressed scientific record is a ratification-class action, so this is
   flagged, not actioned. It does not change the recorded decision — ambiguity
   stands either way — but the provenance still slightly overstates what was
   tested.

## Runtime facts

- Stack: ccproxy `:8000`, langgraph `:6174`, WebUI `:4716`.
- Model `gpt-5.6-sol`, provider openai, reasoning effort high, via ccproxy Codex.
- Start: `cd "<workdir>" && EvoSci --ui webui --workdir "<workdir>"` where
  `<workdir>` is `/Volumes/Asylum/archimedes-wt-jspace/sakshi notes` — a
  subdirectory *without* an `EvoScientist/` package. Cold start 70–120s.
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
| `sakshi notes/HANDOFF_2026-07-26.md` | full lab state *(docs branch)* |
| `sakshi notes/STAGE2B_DESIGN.md` | Stage 2b design in full *(docs branch)* |
| `sakshi notes/STAGE2B_OPEN_PARAMETERS.md` | the ten questions *(docs branch)* |
| `sakshi notes/STAGE2_DISCRIMINATION_REPORT.md` | the study, as amended *(docs branch)* |
| `sakshi notes/CCPROXY_UPSTREAM_ISSUE_DRAFT.md` | drafted, unfiled *(docs branch)* |

*(docs branch)* = `docs/jspace-research-operations`, checked out at
`/Volumes/Asylum/archimedes-wt-jspace`.
