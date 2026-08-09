# Contribution lane: upstream drafts

Status: DRAFTS ONLY. Nothing here is filed. Filing is outward-facing and requires
Dr. Mani's explicit approval per hard boundaries.

Protocol compliance:
- Engine (EvoScientist/EvoScientist): issue first for features; bug fixes PR-able with
  tests; branch names fix/... feat/...; must pass `uv run ruff check .` + `uv run pytest`;
  PR template checkboxes; core-functionality scope.
- Skills (EvoScientist/EvoSkills): Conventional Commits with skill-name scope; PR title
  <70 chars; skill anatomy preserved; eval scores if descriptions change.

| Draft | Target repo | Type | Backs task |
|---|---|---|---|
| engine-issue-memory-path.md | EvoScientist/EvoScientist | bug issue | T001 |
| engine-issue-streamjson-docs.md | EvoScientist/EvoScientist | documentation issue | T004 |
| evoskills-doc-memory-claim.md | EvoScientist/EvoSkills | docs PR | T001 |
| evoskills-pr-ese-trigger.md | EvoScientist/EvoSkills | fix PR | T008 |
| evoskills-pr-ideation-tree.md | EvoScientist/EvoSkills | fix PR | T009 |

Filing order when approved: engine-issue-memory-path first — it is the blocking decision;
the EvoSkills docs PR links it. Then the two EvoSkills fix PRs (ESE trigger, ideation tree),
which are independent of that decision. Then the stream-json docs issue.

Correction log:
- 2026-08-09: the original `evoskills-pr-memory-path.md` proposed repointing the skills from
  `/memory/` to `/memories/`. Boundary capture against v0.2.6 showed `/memories/` rejects
  raw writes, so that PR would have converted silent data loss into a hard write failure.
  It was withdrawn and replaced by a docs-only PR plus a sharper engine issue. Evidence:
  `skills/enforcing-daedalus-paper-parity/tests/test_memory_persistence.py::TestEngineWritePolicy`.
