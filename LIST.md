# LIST

Single running list. Everything open lives here. One item at a time, top down.

Updated: 2026-08-09

## NOW

- [ ] U1 — File engine issue: evolution memory has no writable persistent path.
      Draft ready. Needs Dr. Mani's go-ahead to file.

## NEXT

- [ ] U3 — Comment on EvoSkills #33 (already filed by someone else 2026-08-03,
      no replies). Confirm independently, offer the fix. Do not open a new issue.
- [ ] U5 — Write + file EvoSkills PR: remove success precondition from ESE trigger.
- [ ] U2 — File engine docs issue: auto-mode removes ask_user, docs say otherwise.
- [ ] U4 — File EvoSkills docs PR: correct persistence claim. File AFTER U1 answers.

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

- [ ] Codex adversarial review of all five upstream drafts. Started, not finished.

## DONE

- [x] Upstream sync v0.2.3 -> V0.2.6, conflicts resolved, 3862 tests pass
- [x] Paper alignment review, 14 findings, twice Codex-verified
- [x] Spec 005 + 16 of 18 tasks implemented, 141 new tests
- [x] Duplicate check on both upstream repos

## DETAIL LIVES IN

- specs/005-daedalus-paper-alignment/upstream-filing-queue.md — U1-U5 full detail
- specs/005-daedalus-paper-alignment/PARITY-REPORT.md — what was built, deviations
- specs/005-daedalus-paper-alignment/tasks.md — T001-T018
- docs/daedalus-paper-alignment-review.md — the 14 findings
