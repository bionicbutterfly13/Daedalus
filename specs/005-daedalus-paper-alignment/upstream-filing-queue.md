# Upstream filing queue (T017)

One item at a time, in order. Nothing here is filed. Each item needs Dr. Mani's
explicit go-ahead before any outward-facing action; drafting and local patching
are fine without it.

Status legend: `QUEUED` not started · `DRAFTED` text written, unverified ·
`VERIFIED` checked by Codex against upstream · `READY` awaiting go-ahead ·
`FILED` submitted · `BLOCKED` needs a decision or an upstream answer first.

Duplicate check performed 2026-08-09 against both repos' open and closed issues.
Result: one of the five is already reported (U3). The rest are novel.

---

## U1 — Engine bug: evolution memory has no writable persistent path

- Repo: `EvoScientist/EvoScientist` · Type: bug issue · Finding: F3 · Task: T001
- Draft: `contributions/engine-issue-memory-path.md`
- Duplicate check: none found (searched "memory", "memories persist")
- Status: **DRAFTED**, pending Codex verification
- Fix available from us: **no, by design.** The skills' `/memory/` is unmounted;
  the mounted `/memories/` refuses raw writes. Repairing it requires an engine
  decision (route `/memory/` somewhere writable, relax the write guard for named
  evolution files, or expose memory tools for them). Picking one for them would
  be presumptuous, which is why this is an issue and not a PR.
- Strength: reproducible in ~10 lines against shipped backends; three upstream
  sources contradict each other (CONTRIBUTING diagram, engine code, EvoSkills
  docs), so the report needs no inference.
- Blocks: U2 is independent, but U4's docs wording should follow whatever the
  maintainers decide here.

## U2 — Engine docs: auto-mode removes `ask_user` rather than auto-handling it

- Repo: `EvoScientist/EvoScientist` · Type: documentation issue · Finding: F6 · Task: T004
- Draft: `contributions/engine-issue-streamjson-docs.md`
- Duplicate check: none found (searched "ask_user", "stream-json", "auto-mode";
  the nearest, #387 HITL sub-agent approval, is a different mechanism and closed)
- Status: **DRAFTED**, pending Codex verification
- Fix available from us: **yes, trivial** — a wording change in
  `docs/guides/stream-json.md` plus the matching comment in `cli/commands.py`.
  Offer it in the issue; it is small enough to attach as a PR immediately.

## U3 — EvoSkills: ideation width vs the Elo tournament

- Repo: `EvoScientist/EvoSkills` · Finding: F5 · Task: T009
- Draft: `contributions/evoskills-pr-ideation-tree.md`
- Duplicate check: **DUPLICATE.** Issue
  [#33](https://github.com/EvoScientist/EvoSkills/issues/33), opened 2026-08-03,
  open with zero replies. It makes the same point and adds one this review
  missed: `elo-ranking-guide.md` specifies a 4-5 round Swiss tournament, which is
  degenerate with three entrants.
- Status: **BLOCKED** on the maintainers' answer to #33
- Revised action: do **not** open a new issue. Comment on #33 with independent
  confirmation and the concrete consequence (a tournament whose field equals its
  winners performs no selection, so an acceptance gate cannot distinguish a real
  ranking from a formality), and offer the PR. #33 explicitly asks which workflow
  is intended; shipping a PR that picks an answer before they respond presumes it.
- Fix available from us: designed, not written. Our local mitigation is
  `skills/enforcing-daedalus-paper-parity/templates/ideation-width-addendum.md`,
  which changes our runs only.

## U4 — EvoSkills docs: correct the persistence claim in `memory-schema.md`

- Repo: `EvoScientist/EvoSkills` · Type: docs PR · Finding: F3 · Task: T001
- Draft: `contributions/evoskills-doc-memory-claim.md`
- Duplicate check: none found
- Status: **DRAFTED**, pending Codex verification
- Sequencing: file **after** U1 gets a response. The correct wording depends on
  what the engine decides; writing it now risks documenting behavior that is
  about to change.
- Fix available from us: **yes, trivial** — one paragraph. Deliberately does not
  repoint the paths, because that change would break writes (see U1).

## U5 — EvoSkills: remove the success precondition from the ESE trigger

- Repo: `EvoScientist/EvoSkills` · Type: fix PR · Finding: F8 · Task: T008
- Draft: `contributions/evoskills-pr-ese-trigger.md`
- Duplicate check: none found
- Status: **DRAFTED**, pending Codex verification
- Fix available from us: **yes, genuinely fixable.** A small edit to the trigger
  text in `evo-memory/SKILL.md` plus `references/ese-protocol.md`, and the
  matching handoff line in `experiment-pipeline/SKILL.md`.
- Caveat to state plainly in the PR: the claim that the paper imposes no success
  precondition is taken from arXiv 2603.08127 §3.5 as read, and Codex could not
  verify the paper itself. The PR should quote the skill's own contradicting rule
  ("Failed attempts are data, not waste") as the argument that does not depend on
  the paper.

---

## Working order

1. **U1** — highest value, no duplicate, reproducible, and unblocks U4.
2. **U3** — a comment, not a filing; cheap and courteous while U1 is open.
3. **U5** — independent of everything else; the one real code fix we can offer.
4. **U2** — small, self-contained.
5. **U4** — last, once U1 has an answer.

## Standing constraints

- Nothing is filed without Dr. Mani saying so, per repository hard boundaries.
- Filing identity is `bionicbutterfly13`.
- PRs are cut from a clean EvoSkills clone, never from `~/.EvoScientist/skills`,
  which stays byte-identical to pristine.
- Engine protocol: bug fixes may PR directly; features need an issue first.
  EvoSkills protocol: Conventional Commits scoped to the skill name, PR titles
  under 70 characters.
