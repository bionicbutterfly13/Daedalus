# PARKED — do not file

Was: "fix(evo-memory): remove success precondition from ESE trigger"

**Why parked (2026-08-09)**

The draft claimed the paper imposes no success precondition on ESE while the skill requires
all four stages to pass. Independent review found the premise unsupported:

- `evo-memory/references/paper-prompts.md:133` — which the skill presents as the paper's own
  ESE prompt — says "I will provide you with ... the final high-performance code" and asks to
  "summarize the technical essence of the winning implementation". That is consistent with a
  success precondition, not against it.
- The paper text itself was not available to this review; the original claim rested on a
  fetched summary of §3.5.
- The skill's own rule "Failed attempts are data, not waste" does not by itself require ESE
  after failure — IVE plus trajectory retention could satisfy it.

**What is verified and unchanged**

The success gate exists in all three surfaces: `evo-memory/SKILL.md:123`,
`references/ese-protocol.md:5`, `experiment-pipeline/SKILL.md:225`.

**To unpark**

Either (a) read arXiv 2603.08127 §3.5 directly and confirm the formal ESE definition takes
full trajectories with no success condition, in which case this becomes a genuine alignment
fix; or (b) reframe it as a design proposal — "also extract strategies from failed
trajectories" — which needs maintainer agreement before any PR.

Our local `evolution_enforcement.py` requires ESE after failed pipelines. That is now
recorded as a deliberate lab policy choice, not paper alignment.
