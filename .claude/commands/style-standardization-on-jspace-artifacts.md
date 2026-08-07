---
name: style-standardization-on-jspace-artifacts
description: Workflow command scaffold for style-standardization-on-jspace-artifacts in EvoScientist.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /style-standardization-on-jspace-artifacts

Use this workflow when working on **style-standardization-on-jspace-artifacts** in `EvoScientist`.

## Goal

Performs style-only changes (e.g., punctuation normalization) across J-space skill docs and provenance records.

## Common Files

- `EvoScientist/skills/jspace-research-operations/SKILL.md`
- `EvoScientist/skills/jspace-research-operations/references/*.md`
- `sakshi notes/*.md`
- `sakshi notes/*.ipynb`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Identify style inconsistencies (e.g., em dashes, colons) in SKILL.md, provenance, or experiment docs
- Edit affected files to standardize style
- Commit changes with a 'style:' prefix

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.