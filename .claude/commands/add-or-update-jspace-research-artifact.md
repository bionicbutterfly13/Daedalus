---
name: add-or-update-jspace-research-artifact
description: Workflow command scaffold for add-or-update-jspace-research-artifact in EvoScientist.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /add-or-update-jspace-research-artifact

Use this workflow when working on **add-or-update-jspace-research-artifact** in `EvoScientist`.

## Goal

Adds or updates a J-space research skill or experiment, including documentation, Colab notebooks, validation scripts, and provenance records.

## Common Files

- `EvoScientist/skills/jspace-research-operations/SKILL.md`
- `EvoScientist/skills/jspace-research-operations/references/*.md`
- `EvoScientist/skills/jspace-research-operations/scripts/*.py`
- `EvoScientist/skills/jspace-research-operations/templates/*.md`
- `sakshi notes/*.ipynb`
- `sakshi notes/*.md`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Create or update SKILL.md in EvoScientist/skills/jspace-research-operations/
- Add or update reference documentation in EvoScientist/skills/jspace-research-operations/references/
- Add or update validation scripts in EvoScientist/skills/jspace-research-operations/scripts/
- Add or update evidence report templates in EvoScientist/skills/jspace-research-operations/templates/
- Add or update Colab notebooks and provenance records in sakshi notes/

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.