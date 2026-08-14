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

## U1: Engine/EvoSkills mismatch, evolution memory is workspace-local but documented as shared

- Repo: `EvoScientist/EvoScientist` · Type: bug issue · Finding: F3 · Task: T001
- Draft: `contributions/engine-issue-memory-path.md`
- Duplicate check: none found (searched "memory", "memories persist")
- Status: **READY**, awaiting Dr. Mani's go-ahead to file.
- Fix available from us: **not until maintainers choose the contract.** Singular
  `/memory/` falls through to the workspace; mounted `/memories/` refuses raw
  writes. The engine already has persistent profile files and global observations,
  but EvoSkills uses neither. The draft asks whether to add routing, use the
  existing memory tools, or correct the documentation before we write a patch.
- Strength: the direct backend reproduction ran successfully against current
  upstream `main`; the `CONTRIBUTING.md` diagram, engine routing, and current
  EvoSkills docs disagree in a way the issue demonstrates directly.
- Blocks: U2 is independent, but U4's docs wording should follow whatever the
  maintainers decide here.

## U2: Engine docs say auto-mode handles `ask_user`, but it disables it

- Repo: `EvoScientist/EvoScientist` · Type: documentation issue · Finding: F6 · Task: T004
- Draft: `contributions/engine-issue-streamjson-docs.md`
- Duplicate check: none found (searched "ask_user", "stream-json", "auto-mode";
  the nearest, #387 HITL sub-agent approval, is a different mechanism and closed)
- Status: **READY**, awaiting Dr. Mani's go-ahead to file.
- Fix available from us: **yes, trivial** — a wording change in
  `docs/guides/stream-json.md` plus the matching comment in `cli/commands.py`.
  Offer it in the issue; it is small enough to attach as a PR immediately.

## U3: EvoSkills ideation width vs the Elo tournament

- Repo: `EvoScientist/EvoSkills` · Finding: F5 · Task: T009
- Draft: `contributions/evoskills-issue-33-comment.md`
- Duplicate check: **DUPLICATE.** Issue
  [#33](https://github.com/EvoScientist/EvoSkills/issues/33), opened 2026-08-03,
  open with zero replies. It makes the same point and adds one this review
  missed: `elo-ranking-guide.md` specifies a 4-5 round Swiss tournament, which is
  degenerate with three entrants.
- Status: **READY**, awaiting Dr. Mani's go-ahead to post the comment. Any code
  change remains blocked on the maintainers' answer to #33.
- Revised action: do **not** open a new issue. Comment on #33 with independent
  confirmation and the concrete consequence: a Top-3 drawn from three entrants
  does not narrow the candidate set, so finalist count alone cannot establish
  that selection changed which ideas continue. Offer the PR after maintainers
  answer which workflow is intended.
- Fix available from us: designed, not written. Our local mitigation is
  `skills/enforcing-daedalus-paper-parity/templates/ideation-width-addendum.md`,
  which changes our runs only.

## U4: EvoSkills docs, correct the persistence claim in `memory-schema.md`

- Repo: `EvoScientist/EvoSkills` · Type: docs PR · Finding: F3 · Task: T001
- Draft: `contributions/evoskills-doc-memory-claim.md`
- Duplicate check: none found
- Status: **BLOCKED** on U1's answer. The draft itself is verified.
- Sequencing: file **after** U1 gets a response. The correct wording depends on
  what the engine decides; writing it now risks documenting behavior that is
  about to change.
- Fix available from us: **yes, trivial** — one paragraph. Deliberately does not
  repoint the paths, because that change would break writes (see U1).

## U5 — EvoSkills: remove the success precondition from the ESE trigger

- Repo: `EvoScientist/EvoSkills` · Type: fix PR · Finding: F8 · Task: T008
- Draft: `contributions/PARKED-evoskills-ese-trigger.md`
- Duplicate check: none found
- Status: **DO-NOT-FILE.** The paper-side premise is not verified.
- Fix available from us: **no justified fix yet.** The installed prompt asks for
  the final high-performance or winning implementation, which can support the
  current success gate. This stays withheld unless the primary paper text proves
  a mismatch or the change is reframed as a design proposal.

---

## Codex verdicts (2026-08-09)

| Item | Verdict | What must change |
|---|---|---|
| U1 | **READY** | Reframed as an integration mismatch, limited the reset claim to changed workdirs, and replaced the broken snippet with a reproduction executed against current upstream. |
| U2 | **READY** | Limited the claim to `ask_user`, removed the invalid resume path, and added two current upstream tests as the deterministic reproduction. |
| U3 | **READY COMMENT** | Confirmed against current `main`, shortened to avoid repeating the issue body, and offered a three-file consistency patch after maintainers choose the intended flow. |
| U4 | **BLOCKED** | The draft now says "per-workdir," and its 54-character title meets the repository limit. Do not finalize the wording until U1 is answered. |
| U5 | **DO-NOT-FILE** | The installed paper prompt asks for "the final high-performance code" / "the winning implementation", which is consistent with a success precondition. The paper-side premise is unverified. |

Full verdict: `scratchpad/codex-drafts-verdict.md` (session-local).

## Working order

1. **U1** — highest value, no duplicate, reproducible, and unblocks U4.
2. **U3** — a comment, not a filing; ready but not posted.
3. **U2** — ready but not filed.
4. **U4** — last, once U1 has an answer.

U5 is withheld unless the primary paper text establishes the claimed mismatch.

## Standing constraints

- Nothing is filed without Dr. Mani saying so, per repository hard boundaries.
- Filing identity is `bionicbutterfly13`.
- PRs are cut from a clean EvoSkills clone, never from `~/.EvoScientist/skills`,
  which stays byte-identical to pristine.
- Engine protocol: pull requests address an open issue; propose design changes in
  an issue or discussion before implementation.
  EvoSkills protocol: Conventional Commits scoped to the skill name, PR titles
  under 70 characters.
