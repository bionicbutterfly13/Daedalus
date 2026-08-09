# Draft — EvoSkills PR

Branch: fix/research-ideation-tree-width
Title: fix(research-ideation): build the documented idea tree before the tournament

**What changed and why**
SKILL.md's workflow generates 3 initial ideas (Step 3) and refines them in 3 tracks
(Step 4), so the Step-5 Elo tournament ranks exactly 3 candidates and "presenting the
top-3" returns the entire field — the tournament selects nothing. The skill's own
references/tree-search-protocol.md specifies a 3-level tree (technique x domain x
formulation) targeting 15-21 leaves, matching the paper's N_I<=21 idea tree search, and
SKILL.md's rule 5 says "Quantity before quality in generation". This PR makes Step 3
build the documented tree (with the reference's pruning rules), carries the surviving
leaves into refinement, and lets the tournament do the selection its rubric describes.

Scope: Step 3/4 workflow text in SKILL.md aligned with the existing
tree-search-protocol.md; the reference itself is unchanged. No new mechanisms.
