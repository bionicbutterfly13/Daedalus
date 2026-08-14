# Contribution lane: upstream drafts

Status: DRAFTS ONLY. Nothing here is filed. Filing is outward-facing and requires
Dr. Mani's explicit approval per hard boundaries.

Protocol compliance:
- Engine (EvoScientist/EvoScientist): pull requests address an open issue; design changes
  start in an issue or discussion; keep changes focused; run `uv run ruff check .` and
  `uv run pytest`.
- Skills (EvoScientist/EvoSkills): Conventional Commits with skill-name scope; PR title
  <70 chars; skill anatomy preserved; eval scores if descriptions change.

| Draft | Target repo | Type | Backs task | Status |
|---|---|---|---|---|
| engine-issue-memory-path.md | EvoScientist/EvoScientist | bug issue | T001 | ready, not filed |
| engine-issue-streamjson-docs.md | EvoScientist/EvoScientist | documentation issue | T004 | ready, not filed |
| evoskills-doc-memory-claim.md | EvoScientist/EvoSkills | docs PR | T001 | verified, blocked on U1 |
| evoskills-issue-33-comment.md | EvoScientist/EvoSkills | comment on existing #33 | T009 | ready, not posted |
| PARKED-evoskills-ese-trigger.md | — | withheld | T008 | premise unverified |

Outward-action order when each item is approved: file the memory-path issue, then post the
comment on EvoSkills #33. The stream-json draft still needs revision. The memory docs change
waits for the memory-path decision. The ESE trigger change is withheld because its premise
is unverified.

Correction log:
- 2026-08-09: the original `evoskills-pr-memory-path.md` proposed repointing the skills from
  `/memory/` to `/memories/`. Boundary capture against v0.2.6 showed `/memories/` rejects
  raw writes, so that PR would have converted silent data loss into a hard write failure.
  It was withdrawn and replaced by a docs-only PR plus a sharper engine issue. Evidence:
  `skills/enforcing-daedalus-paper-parity/tests/test_memory_persistence.py::TestEngineWritePolicy`.
