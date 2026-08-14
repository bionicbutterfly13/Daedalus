# Parity report: 005-daedalus-paper-alignment

- Date: 2026-08-09
- Branch: `feat/005-paper-parity` (local only; nothing pushed, nothing filed)
- Base: `57e144e` (fork main, post-upstream-V0.2.6 merge)
- Evidence base: [`docs/daedalus-paper-alignment-review.md`](../../docs/daedalus-paper-alignment-review.md)
- Scope rule applied: remediation lives in layers upstream does not own. No engine
  source was modified. The installed skills were left byte-identical to pristine.

## Headline

The five parity criteria are met **as enforcement**, not as demonstration. Every gate
is implemented, tested, and mutation-checked, and the end-to-end tests show a
compliant run accepted and a do-nothing run rejected. What has *not* happened is a
live Daedalus cycle: no run was executed, so nothing here proves the real agent
produces these artifacts. That is the single biggest gap and it needs an API-backed
run to close.

One planned fix was implemented, tested, and **withdrawn** because the test proved it
would break the system. Details under T001 below.

## Task status

16 of 18 tasks closed. Two are open and both need Dr. Mani.

| Task | Finding | Status |
|---|---|---|
| T001 | F3 | Done, approach changed after evidence (see below) |
| T002 | F3 | Done |
| T003 | F12, F5 | Done |
| T004 | F6 | Done |
| T005 | F14 | Done |
| T006 | D1 | Done, bug found by running against the real repo |
| T007 | F1, D3 | Done |
| T008 | F2, F8 | Done |
| T009 | F5 | Done as a prompt addendum |
| T010 | F4 | Done (records the choice; does not make it deterministic) |
| T011 | F9 | **BLOCKED** — needs a decision, not code |
| T012 | F13 | Done |
| T013 | F10 | **No action, deliberately** — not a defect in this fork |
| T014 | F11 | Done, plus two dangling evidence citations found |
| T015 | D2 | Done, inverted from original intent |
| T016 | — | Done previously (drafts written) |
| T017 | — | **Open** — filing needs approval |
| T018 | new | **Open** — raised during implementation |

## What was built

A new skill, `skills/enforcing-daedalus-paper-parity/`, with six scripts and 141
tests. All checks share one rule: **absence of evidence is failure**. A gate that
passes because it found nothing to inspect is the bug the gates exist to prevent.

| Script | Purpose | Tasks |
|---|---|---|
| `skill_digest.py` | Content digests that make a run attributable | T007 |
| `memory_persistence.py` | Workspace pinning + shared-memory verification | T001, T002 |
| `parity_gates.py` | Four acceptance gates with a combined verdict | T002, T003, T005, T007 |
| `launch_record.py` | Pre-launch pinning; gate-narration audit | T004, T007, T010 |
| `evolution_enforcement.py` | Which of IDE/IVE/ESE the run owed vs performed | T008 |
| `check_upstream_drift.py` | Whether an upstream update invalidates the review | T006 |
| `patch_evolution_memory_paths.py` | Retained but unused — see T001 | T001 |

## Deviations from the plan

### T001 — the planned fix was wrong, and the test proved it

The task offered three options; the goal statement directed patching the installed
skills to repoint `/memory/` at `/memories/`. That was implemented, applied to the
real install, and then withdrawn.

Boundary capture against live engine code showed:

```
backend.write("/memories/ideation-memory.md", ...)
    -> error: "Raw writes to /memories are blocked."
backend.write("/memory/ideation-memory.md", ...)
    -> ok, lands at <workspace>/memory/ideation-memory.md
```

`MemoryFilesystemBackend.write()` refuses every raw write and permits edits only to
*existing* files under `/memories/profile/`. Repointing the skills would have turned
silent data loss into a hard write failure on every evolution step.

The installed skills were restored from pristine copies and digest-verified identical.
Mitigation instead comes from pinning `EVOSCIENTIST_WORKSPACE_DIR`, which is
configuration and carries no upstream merge surface. The regression is pinned by
`test_memories_mount_rejects_raw_writes`, so if upstream ever makes that mount
writable, the test fails and the simpler fix becomes available.

The upstream contribution drafts were rewritten accordingly: the finding is not "wrong
path" but "no path is both persistent and agent-writable", which is a sharper and more
actionable bug report. The withdrawn PR draft was replaced by a docs-only PR, and the
withdrawal is logged in `contributions/README.md`.

### T013 — no action taken

"Towards Self-Evolving AI Scientists" is upstream's consistent branding across
`pyproject.toml` and the README banner, not a mis-citation of the paper. Our own docs
cite the paper title correctly. Editing an upstream-owned file would buy permanent
merge friction for a cosmetic difference. F10 is downgraded to a style observation.

### T015 — inverted

The task said to mark the acceptance-gate section as design-not-implemented. By the
time it came up, T002/T003/T005 had implemented four of its checks, so the section now
carries per-check `[implemented]` status plus the instruction to treat an unmarked
check as unperformed rather than assumed.

### T009 — addendum, not skill edit

Shipped as `templates/ideation-width-addendum.md` for injection into the run packet,
rather than editing the installed skill, to keep the merge surface at zero. The
upstream fix remains drafted separately.

## Bugs found in my own work

Two, both found by testing against reality rather than fixtures:

1. **`check_upstream_drift.py` fired forever.** The first version diffed `HEAD`
   against `upstream/main`, which also surfaces the fork's permanent deliberate
   divergences, so it demanded a review immediately after a clean merge. All 14 unit
   tests passed against that bug; running it against the real repository exposed it.
   Fixed to compare against the merge base, and pinned by
   `test_permanent_fork_divergence_alone_needs_no_review`.
2. **A dead regex guard.** Mutation testing showed the `(?!ies)` lookahead in the
   memory-path patcher was unreachable: `/memories/` never contains `/memory/` as a
   substring, so no test could distinguish it. Removed rather than kept as untested
   complexity.

A third issue was procedural: `.gitignore`'s `skills/*` rule silently excluded the
entire new skill, so the T001 commit recorded its spec changes while dropping the
scripts and tests its message described. Fixed by allowlisting the skill and
re-excluding build artifacts; the omission is stated in the following commit message
rather than quietly amended.

## Found during implementation

`docs/cognitive-lab-architecture.md` cites two artifacts as the evidence for its July
16, 2026 episodic-memory account:

- `runs/cognitive-hypothesis-lab/context-intake-2026-07-16.md`
- `journals/archimedes/2026-07-16.md`

Neither exists in the working tree, and neither appears anywhere in git history
(earliest surviving journal is 2026-07-31). Per constitution V the passage is marked
UNRESOLVED in place rather than restated or deleted. Filed as **T018**: only Dr. Mani
can say whether the episode happened and where its record went. The architectural
point it illustrates does not depend on it.

## Verification

- 141 tests in the new skill; full repo suite green apart from the one pre-existing
  upstream failure (`test_timeout_bounds_drain_when_detached_descendant_holds_pipes`,
  which fails identically on pristine upstream v0.2.6 and is not merge-caused).
- `uv run ruff check` clean across the skill.
- Mutation-checked, not merely green:
  - forcing every gate to `passed=True` fails 15 of 28 gate tests;
  - reintroducing the F8 success gate on ESE fails 2 tests;
  - removing the patcher's write step fails 6 tests;
  - a rename-blind digest fails the attribution test;
  - reverting the drift check to `HEAD`-vs-upstream fails the regression test.
- Two tests exercise live engine backends rather than mocks, which is how the T001
  reversal was caught.

## What this does not establish

- **No Daedalus run was executed.** Every gate is verified against synthesized
  artifacts. Whether the real agent emits `direction-summary.md`, `stage-record.json`,
  and evolution reports in these shapes is untested. The likely outcome of a first
  live run is that the artifact contract needs adjusting to what Daedalus actually
  writes.
- Parity criterion 1 is demonstrated at the level of *routing* (a pinned workspace
  resolves to one memory directory and content carries across cycles), not by two live
  cycles.
- Retrieval remains LLM-judged and non-deterministic; T010 records the selection, it
  does not fix the mechanism.
- The upstream defects are unfixed. Nothing was filed.

## Remaining for a human

1. **T017** — approve and file the upstream contributions. Five drafts in
   `contributions/`, with a filing order; the engine memory-path issue is the blocking
   one and should go first.
2. **T011** — decide whether a per-role model split is wanted, knowing it is only
   half-achievable (async containers hardcode the main model, so the paper's
   Gemini-for-writing assignment is unreachable without an upstream change).
3. **T018** — re-source or remove the July 16 account.
4. **First live run** — the real validation. Suggested: one small cycle with
   `EVOSCIENTIST_WORKSPACE_DIR` pinned, then run the gates against it and adjust the
   artifact contract to what Daedalus actually produces.
