---
name: enforcing-daedalus-paper-parity
description: Verify whether Daedalus and EvoScientist implement the method promised in arXiv 2603.08127, and prepare maintainer-aligned upstream contributions. Use when auditing paper parity, checking cross-task evolution memory, reviewing IDE/IVE/ESE behavior, validating a Daedalus run, searching for duplicate upstream reports, assigning Claude Fable a bounded parity task, or deciding what issue or pull request should come next.
---

# Enforcing Daedalus Paper Parity

Keep three questions separate:

1. What does the paper promise?
2. What does the current engine and current EvoSkills code actually do?
3. What local evidence checks exist around a run?

Local checks can expose missing work. They do not implement a missing paper promise.

## Current verified baseline

Use these facts unless newer primary-source evidence changes them:

- The paper promises retrieval and improvement across different research tasks, using
  Ideation Memory, Experimentation Memory, an Evolution Manager, and embedding-based
  retrieval.
- EvoSkills writes the two paper memories under `/memory/`. Upstream deliberately treats
  that location as project-local. It survives sessions that reuse one workspace, but a new
  workspace does not receive the earlier project's paper memory.
- EvoScientist separately provides shared profile memory and global observations under
  `/memories/`. EvoSkills does not connect IDE, IVE, or ESE to that shared system.
- Current global observation search uses token overlap and IDF. It is not the paper's
  embedding-cosine retrieval.
- No released version or visible upstream branch found in the 2026-08-09 audit implements
  the complete bridge between the paper memories and shared EvoMemory.
- Rewriting `/memory/` to `/memories/` is not a fix. Raw writes to `/memories/` are blocked,
  and upstream pull request 161 deliberately separated the two locations.
- F8 is withdrawn. The available paper prompt asks ESE to analyze the final
  high-performance or winning implementation, so the existing success precondition is not
  established as a paper defect.
- The three-candidate ideation tournament mismatch is already reported as EvoSkills issue
  33. Do not file a duplicate.

The correction block near the top of
`docs/daedalus-paper-alignment-review.md` overrides stale wording retained later in that
historical review.

## Upstream contribution procedure

Read `LIST.md` first. It is the active control list. Work on one contribution at a time.

Before repeating a current-state claim, recheck the paper, current upstream code, visible
branches, releases, issues, pull requests, and discussions. Record negative searches as the
scope searched, never as proof that nobody has discussed the subject anywhere.

For the cross-project memory gap:

1. Prepare an issue-quality reproduction. Record an ideation lesson in workspace A, start
   workspace B, and show that the paper-specific lesson is unavailable there while global
   observations remain available.
2. Ask maintainers which shared representation they want. Plausible choices include typed
   entries in global EvoMemory or a distinct global evolution-memory store. Do not choose
   the architecture on their behalf.
3. After maintainer agreement, make the first code contribution small: connect IDE to the
   agreed shared store and prove retrieval from a new workspace. Treat IVE, ESE, and exact
   embedding retrieval as later focused changes.

This sequence matches upstream practice:

- Engine design changes require an issue or discussion before code.
- EvoSkills prefers small pull requests and executable scripts for fragile control flow.
- Specialized actors use a sibling `AGENTS.md`; portable knowledge remains in `SKILL.md`.

Nothing is filed, commented, pushed, or sent without Dr. Mani's explicit approval.

## Claude Fable assignment

When Dr. Mani asks how to use Claude Fable for this work, give it this bounded task:

> Prepare, but do not file, a maintainer-ready reproduction of the cross-project
> evolution-memory disconnect. Demonstrate learning recorded in one project and unavailable
> in another, identify the exact engine and EvoSkills code paths, design a failing automated
> test, and propose the smallest first patch connecting IDE to shared EvoMemory. Do not
> investigate other paper gaps or modify public issues.

Independently validate Fable's source claims before accepting its packet.

## Local run evidence

Use the bundled scripts only for their stated evidence purpose:

| Purpose | Script |
|---|---|
| Record skill versions and the declared decision policy | `scripts/launch_record.py` |
| Check stable reuse of one selected workspace | `scripts/memory_persistence.py` |
| Require expected run artifacts | `scripts/parity_gates.py` |
| Check which evolution mechanisms the run owed | `scripts/evolution_enforcement.py` |
| Detect changes to upstream files cited by the review | `scripts/check_upstream_drift.py` |

`memory_persistence.py` demonstrates same-workspace continuity only. Never report its pass
as evidence that the paper's cross-project learning promise is implemented.

`scripts/patch_evolution_memory_paths.py` is an obsolete historical experiment. Do not run
it and do not use its tests as current implementation guidance.

## Primary references

- Paper: <https://arxiv.org/abs/2603.08127>
- Deliberate memory-scope change: <https://github.com/EvoScientist/EvoScientist/pull/161>
- Shared observation memory: <https://github.com/EvoScientist/EvoScientist/pull/281>
- Existing ideation mismatch: <https://github.com/EvoScientist/EvoSkills/issues/33>
- EvoSkills implementation direction: <https://github.com/EvoScientist/EvoSkills/issues/30>
- Engine actor direction: <https://github.com/EvoScientist/EvoScientist/issues/361>
- Engine contribution rules: <https://github.com/EvoScientist/EvoScientist/blob/main/CONTRIBUTING.md>
- EvoSkills contribution rules: <https://github.com/EvoScientist/EvoSkills/blob/main/CONTRIBUTING.md>
- Local active list: `LIST.md`
- Local evidence review: `docs/daedalus-paper-alignment-review.md`
- Unfiled drafts: `specs/005-daedalus-paper-alignment/contributions/`
