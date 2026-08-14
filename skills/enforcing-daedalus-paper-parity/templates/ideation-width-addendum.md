# Ideation width addendum (T009, finding F5)

Inject this verbatim into the run packet ahead of any `research-ideation` cycle.

It exists because the installed skill's workflow generates 3 initial ideas and
refines them in 3 tracks, so the Elo tournament ranks exactly 3 champions and the
"top-3" it presents is the entire field: the ranking selects nothing. The skill's
own `references/tree-search-protocol.md` specifies a 3-level tree targeting 15-21
leaves (the paper's `N_I <= 21`), which the workflow never builds. This addendum
directs the run to follow the reference the skill already ships.

---

## Required ideation width

Before ranking, build the idea tree described in
`research-ideation/references/tree-search-protocol.md`, not the three-idea
shortcut in the SKILL.md walkthrough:

1. **Level 1 (technique):** 3 fundamentally different technical approaches.
2. **Level 2 (domain):** 2-3 application contexts per Level 1 node, each imposing
   different constraints.
3. **Level 3 (formulation):** 1-2 concrete problem formulations per Level 2 node.
4. Apply the reference's pruning rules (clearly infeasible, duplicate, or matching
   a *fundamental* failure in M_I; implementation failures are retryable and must
   not be pruned).
5. **Target 15-21 surviving leaves.** Fewer than 10 makes the tournament
   unreliable; more than 21 exceeds the paper's `N_I`.

Run the Elo tournament over **all surviving leaves**, then retain the top 3.

Record the full field in `direction-summary.md` as a markdown table with one row
per entrant, including its Elo score. The acceptance gate reads that table: a
field of 3 or fewer is rejected, because a tournament whose entrants equal its
winners has performed no selection.

## Why this is not merely a bigger number

The paper's ranking earns its place by discarding candidates. With three
entrants, Elo ordering is decorative and the "surprises" the skill's own
counterintuitive rule 7 promises ("the tournament finds surprises") cannot occur.
Width is what makes the selection real.
