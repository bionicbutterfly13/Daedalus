# Draft: comment on EvoSkills issue #33 (NOT a new issue)

Existing issue: https://github.com/EvoScientist/EvoSkills/issues/33
"Inconsistency between the 3-track ideation workflow and the 15–21-candidate Elo tournament"
Opened 2026-08-03, still open, no replies. It makes this point already; do not file a duplicate.

---

I independently hit this and confirmed it still exists on current `main` at `2e47411`.
One practical test consequence is that Step 5's Top-3 can contain every entrant, so the
finalist output alone does not prove that candidate selection occurred.

I can prepare the consistency patch after the intended flow is chosen. I would update
`SKILL.md`, `tree-search-protocol.md`, and `elo-ranking-guide.md` together so they state one
candidate count and one tournament input. If the 15-21-leaf flow is intended, I can feed
those leaves into Step 5. If three track champions are intended, I can simplify the two
references to match.
