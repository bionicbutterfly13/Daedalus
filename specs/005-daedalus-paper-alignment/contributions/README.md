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
| evoskills-pr-memory-path.md | EvoScientist/EvoSkills | fix PR | T001 |
| evoskills-pr-ese-trigger.md | EvoScientist/EvoSkills | fix PR | T008 |
| evoskills-pr-ideation-tree.md | EvoScientist/EvoSkills | fix PR | T009 |

Filing order when approved: engine-issue-memory-path first (the EvoSkills memory-path PR
should link it as the cross-repo motivation), then the three EvoSkills PRs, then the
docs issue.
