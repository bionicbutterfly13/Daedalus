# Draft — EvoSkills PR

Branch: fix/evo-memory-ese-trigger
Title: fix(evo-memory): remove success precondition from ESE trigger

**What changed and why**
evo-memory triggers ESE only "after experiment-pipeline succeeds — all 4 stages complete
and gates met" (SKILL.md and references/ese-protocol.md). The paper defines
F_E = ESE(P, {H_E^s}) over all four stage histories with no success precondition,
distilling from best-performing codes AND full search trajectories (§3.5). The success
gate is self-defeating on the paper's own numbers: Stage-3 success is ~21%, so gated ESE
rarely fires, yet ESE produced the paper's +10.17pp execution improvement. It also
contradicts experiment-pipeline's rule 5 ("Failed attempts are data, not waste").

Change: trigger ESE after every completed pipeline run (success or failure) over whatever
trajectories exist; on failure runs, ESE complements IVE (IVE classifies the direction,
ESE still harvests reusable data/training strategies from the attempt logs). Wording
updated in SKILL.md trigger table, ese-protocol.md, and experiment-pipeline's handoff
section for consistency.
