# Draft — comment on EvoSkills issue #33 (NOT a new issue)

Existing issue: https://github.com/EvoScientist/EvoSkills/issues/33
"Inconsistency between the 3-track ideation workflow and the 15–21-candidate Elo tournament"
Opened 2026-08-03, still open, no replies. It makes this point already; do not file a duplicate.

---

Independently ran into the same inconsistency and can confirm the file-level details, in case
it helps narrow the question.

Reading `research-ideation/SKILL.md` as written: Step 3 produces three initial ideas, Step 4
runs three refinement tracks and keeps one champion each, and Step 5 ranks those three
champions. So the tournament field is three and the reported Top-3 is the whole field —
the ranking does not reduce the candidate set. `references/tree-search-protocol.md` instead
describes a technique/domain/formulation tree targeting 15–21 leaves, and as #33 notes,
`elo-ranking-guide.md` is written for a multi-round Swiss format that needs a larger field
to be meaningful.

One practical consequence worth adding: for anyone checking a run's artifacts afterwards,
a tournament whose entrants equal its winners is indistinguishable from one that was skipped.
There is no signal in the output that selection occurred.

If it would help, happy to send a PR making Step 3/4 build the tree the reference already
specifies and feeding its leaves into the ranking — but that presumes an answer to the
question in #33, so it seemed better to ask first. If the three-champion workflow is the
intended design, the fix is presumably the other direction: adjust
`tree-search-protocol.md` and `elo-ranking-guide.md` to match.
