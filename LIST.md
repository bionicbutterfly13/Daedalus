# LIST

Single running list. Everything open lives here. One item at a time, top down.

Updated: 2026-08-09

## NOW

- [ ] U1 — REWRITE the engine issue before filing. Codex refuted the "no writable
      persistent path" framing: upstream HAS persistent agent-writable storage
      (profile files, global observations); EvoSkills just doesn't use it. Reframe
      as an integration mismatch. Also fix the non-runnable repro snippet.

## NEXT

- [ ] U3 — Comment on EvoSkills #33 (already filed by someone else 2026-08-03,
      no replies). Confirm independently, offer the fix. Do not open a new issue.
- [ ] U5 — WITHHELD. Codex: DO-NOT-FILE. The installed paper prompt asks ESE for
      "the final high-performance code", so the success gate may be faithful to the
      paper. My claim rested on a fetched summary, not the primary source. Needs the
      actual paper text to settle, or reframe as a design proposal.
- [ ] U2 — Edit then file: core claim verified, but drop "inert"/"silently dropped"
      and the --no-auto-mode resume suggestion (CLI says not resumable). Add a
      deterministic repro.
- [ ] U4 — Edit then file after U1: say "per-workdir" not "per-run"; PR title is 71
      chars, must be under 70.

## DECISIONS WAITING ON DR. MANI

- [ ] D-1 — Approve upstream filing (unblocks U1-U5).
- [ ] D-2 — Per-role model split: want it? Only half-achievable; async agents
      hardcode the main model, so paper's Gemini-for-writing is unreachable.
- [ ] D-3 — July 16 episodic-memory account in docs/cognitive-lab-architecture.md
      cites two files that never existed in git history. Re-source or delete?

## AFTER THAT

- [ ] Run one live Daedalus cycle with EVOSCIENTIST_WORKSPACE_DIR pinned, then run
      the parity gates against it. Everything built so far is tested against
      artifacts I made up. This is the real validation.

## RUNNING

- (nothing)

## CORRECTED AFTER REVIEW

- F3 downgraded P0 -> P1: default daemon mode reuses cwd, so memory does persist
  across same-directory sessions. Only run mode / changing --workdir resets it.
- F3 reframed: upstream is not missing the capability, EvoSkills isn't using it.
- F8 WITHDRAWN entirely. Not established.

## DONE

- [x] Upstream sync v0.2.3 -> V0.2.6, conflicts resolved, 3862 tests pass
- [x] Paper alignment review, 14 findings, twice Codex-verified
- [x] Spec 005 + 16 of 18 tasks implemented, 141 new tests
- [x] Duplicate check on both upstream repos (found EvoSkills #33 = our U3)
- [x] Codex adversarial review of all five drafts: 4 NEEDS-EDIT, 1 DO-NOT-FILE

## DETAIL LIVES IN

- specs/005-daedalus-paper-alignment/upstream-filing-queue.md — U1-U5 full detail
- specs/005-daedalus-paper-alignment/PARITY-REPORT.md — what was built, deviations
- specs/005-daedalus-paper-alignment/tasks.md — T001-T018
- docs/daedalus-paper-alignment-review.md — the 14 findings
