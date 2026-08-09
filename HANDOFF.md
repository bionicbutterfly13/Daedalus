# HANDOFF — Daedalus paper-parity work

Written 2026-08-09, end of the session that ran the upstream sync and spec 005.
Repo moved from `/Volumes/Asylum/archimedes` to `/Volumes/Asylum/Daedalus` during
that session; all work survived the move, verified.

## State

- Branch: `feat/005-paper-parity`, 9 commits, **nothing pushed anywhere**
- Base: fork main merged with upstream **V0.2.6** (was 3 releases behind at v0.2.3)
- Tests: 3,862 repo + 141 in the new parity skill, all passing. One deselected
  test (`test_timeout_bounds_drain_when_detached_descendant_holds_pipes`) fails
  identically on pristine upstream, so it is not ours.
- Installed skills at `~/.EvoScientist/skills` are **byte-identical to pristine**,
  digest-verified. Nothing was left patched.

## Start here

1. `LIST.md` — the single running list, everything open
2. `specs/005-daedalus-paper-alignment/PARITY-REPORT.md` — what was built and what it does NOT establish
3. `docs/daedalus-paper-alignment-review.md` — the 14 findings, table at the top

## The one idea worth acting on

**Archimedes should own the evolution memory, not Daedalus.**

Daedalus's memory is workspace-local while its docs claim it is shared, and the
mounted persistent route refuses raw writes, so it cannot simply be repointed.
Rather than wait on upstream, invert it: Archimedes keeps the durable store,
injects relevant priors into the run packet before launch, and extracts IDE/IVE/ESE
from the run's artifacts afterwards. Daedalus's `/memory/` becomes scratch.

This is what `docs/cognitive-lab-architecture.md` already assigns to Archimedes.
It fixes F3, F2, F12, F13 and most of F4 at once, touches no engine code, and
survives every upstream update. Most machinery exists already
(`evolution_enforcement.py`, `launch_record.py`, `parity_gates.py`); what is
missing is the store plus the inject/extract steps. Roughly a day.

Dr. Mani has NOT approved this. It was offered as "spec 006, one page, read before
building". Do not build it unsolicited.

## Open decisions (Dr. Mani only)

1. Upstream filing. Four drafts in `specs/005-daedalus-paper-alignment/contributions/`.
   After two Codex rounds: one SAFE-TO-FILE (`evoskills-doc-memory-claim.md`), three
   still NEEDS-EDIT, one parked. Nothing filed. Grinding; low priority.
2. Per-role model split (T011). Only half-achievable; async subagents hardcode the
   main model, so the paper's Gemini-for-writing is unreachable without upstream.
3. The July 16, 2026 episodic-memory account in `docs/cognitive-lab-architecture.md`
   cites two files that never existed in git history. Re-source or delete (T018).

## Traps that cost time in this session

- **`skills/*` is gitignored** with a per-skill allowlist (`.gitignore:43-60`). A new
  skill directory is silently untracked; one commit recorded its message while
  dropping the files it described. Allowlist first, and re-exclude `__pycache__`
  because the `**` negation outranks the generic rule.
- **The branch got switched out from under the session** (reflog showed
  `checkout: moving from feat/005-paper-parity to main`). Two commits landed on the
  wrong branch and files looked reverted. Check `git branch --show-current` before
  concluding work vanished.
- **Verify fixes against the live boundary before applying them.** The planned F3
  fix (repoint `/memory/` to `/memories/`) was applied, then proven to break writes,
  then reverted. See the `verify-the-fix-against-live-boundaries` skill.
- **Codex refuted three of my claims across two rounds**, including one I had the
  primary source for locally and never read. Get drafts reviewed before filing.

## Migration repair done in this session

The move from `/Volumes/Asylum/archimedes` broke the toolchain: every script in
`.venv/bin/` kept a shebang pointing at the old absolute path, and
`.git/hooks/pre-commit` hardcoded `INSTALL_PYTHON` to the old venv, so **every
commit failed**. Repaired with `uv sync --dev`, then
`uv pip install --force-reinstall pre-commit`, then `pre-commit install`. The hook
now points at `/Volumes/Asylum/Daedalus/.venv/bin/python3`.

If other tooling misbehaves, suspect the same cause: `grep -rl
"/Volumes/Asylum/archimedes" .venv/bin .git/hooks` finds stale absolute paths.
Note `~/.EvoScientist/skills` is unaffected; it lives outside the repo.

## Do not

- Push, file issues, or open PRs without explicit approval.
- Patch `~/.EvoScientist/skills` and leave it patched.
- Trust a green unit suite as proof a checker works; run it against real data.
