# LIST

Single running list. Everything open lives here. One item at a time, top down.

Updated: 2026-08-14

## RE-AUDIT 2026-08-14 (upstream sync + parity recheck)

- Merged upstream/main (6 commits past V0.2.6, no new release tag) as `ece1b3d`;
  fork divergences verified intact (settings.py process-env-wins graft + inverted
  test, ccproxy Responses routing in llm/models.py, runtime/ package layout).
- `check_upstream_drift.py`: zero cited files touched, review_required false.
- EvoSkills updated 2e47411 → 6d92ea5 (16/16 skills byte-identical to upstream
  head); the 4 new commits touch paper-navigator/paper-review/script-paths only,
  not evo-memory. The dangling `enforcing-daedalus-paper-parity` symlink (old
  archimedes path) was repointed to /Volumes/Asylum/Daedalus.
- Verdict: all 14 findings in docs/daedalus-paper-alignment-review.md stand
  unchanged. #381 (subagent tool resolution) does not touch F9's model
  hardcoding; no ask_user/auto changes, F6 stands.

## NOW

- [ ] Learn basic Daedalus runs, starting with one prompt in one study folder.

## NEXT

- (nothing)

## DEFERRED

- [ ] Revisit cross-project memory after the basic-run evaluation. Decide then
      whether learned strategies should transfer between study folders.
- [ ] U5: WITHHELD. Codex verdict is DO-NOT-FILE. The installed paper prompt asks
      ESE for "the final high-performance code", so the success gate may match the
      paper. This needs the primary paper text or a design-proposal reframing.

## DECISIONS WAITING ON DR. MANI

- [ ] D-2 — Per-role model split: want it? Only half-achievable; async agents
      hardcode the main model, so paper's Gemini-for-writing is unreachable.
- [ ] D-3 — July 16 episodic-memory account in docs/cognitive-lab-architecture.md
      cites two files that never existed in git history. Re-source or delete?

## AFTER THAT

- [ ] Run one live Daedalus cycle with EVOSCIENTIST_WORKSPACE_DIR pinned, then run
      the parity gates against it. A smaller upstream-feasibility study now proves
      the engine can answer, execute code, write verified artifacts, and recall an
      explicitly written evolution memory from a fresh session. It did NOT run
      ideation or the four experiment stages, so it is not the paper-parity cycle.

## RUNNING

- (nothing)

## CORRECTED AFTER REVIEW

- F3 downgraded P0 -> P1: default daemon mode reuses cwd, so memory does persist
  across same-directory sessions. Only run mode / changing --workdir resets it.
- F3 reframed: upstream is not missing the capability, EvoSkills isn't using it.
- F8 WITHDRAWN entirely. Not established.

## DONE

- [x] U4: Verified the docs draft uses "per-workdir" and its title is 54
      characters. No duplicate issue or pull request was found. BLOCKED on U1's
      answer, not filed.
- [x] U2: Reframed the stream-json mismatch to the exact behavior: tool approvals
      are skipped, but `ask_user` is disabled rather than answered. Two current
      upstream tests reproduce it. READY, not filed.
- [x] U3: Confirmed EvoSkills #33 still has no replies and still matches current
      `main`. A short comment offers a three-file consistency patch after the
      maintainers choose the intended workflow. READY, not posted.
- [x] U1: Reframed as an engine/EvoSkills integration mismatch. The direct
      reproduction runs against current upstream, the draft follows the bug
      template, and the current source claims were rechecked. READY, not filed.
- [x] Upstream sync v0.2.3 -> V0.2.6, conflicts resolved, 3862 tests pass
- [x] Paper alignment review, 14 findings, twice Codex-verified
- [x] Spec 005 + 16 of 18 tasks implemented, 141 new tests
- [x] Duplicate check on both upstream repos (found EvoSkills #33 = our U3)
- [x] Codex adversarial review of all five drafts: 4 NEEDS-EDIT, 1 DO-NOT-FILE
- [x] Minimal upstream-feasibility lane isolated on `codex/upstream-feasibility`.
      Live connection, synthetic experiment, artifact verification, explicit
      evolution-memory write, and fresh-session recall passed. Five narrow local
      repairs have 241 focused tests passing. The full suite has 3,498 passing,
      12 skipped, and one timeout-test failure reproduced unchanged on untouched
      upstream. The full paper cycle remains open. No commit, push, issue, or
      pull request was made.

## DETAIL LIVES IN

- specs/005-daedalus-paper-alignment/upstream-filing-queue.md — U1-U5 full detail
- specs/005-daedalus-paper-alignment/PARITY-REPORT.md — what was built, deviations
- specs/005-daedalus-paper-alignment/tasks.md — T001-T018
- docs/daedalus-paper-alignment-review.md — the 14 findings
