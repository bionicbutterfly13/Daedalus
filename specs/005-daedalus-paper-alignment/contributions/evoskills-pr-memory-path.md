# Draft — EvoSkills PR

Branch: fix/evo-memory-memories-mount
Title: fix(evo-memory): write M_I/M_E under /memories/ so they persist

**What changed and why**
Every M_I/M_E path in evo-memory, research-ideation (Step 0/6), and experiment-pipeline
(Before Starting / handoff) moves from `/memory/...` to `/memories/...`. The engine mounts
persistent cross-workspace storage at `/memories/` only; `/memory/` falls through to the
per-run workspace backend, so evolution memory never survives a workdir change and every
cycle silently restarts from zero (the skills' own "first cycle → skip" fallback masks the
loss). Fixes the accumulation mechanism the skills implement from the EvoScientist paper
(§3.5).

Scope: path strings and their surrounding prose only; no protocol/mechanism changes.
Cross-link: engine issue "<memory-path issue #>" (three-way docs/code/skills contradiction).

Commits:
- fix(evo-memory): point M_I/M_E at /memories/
- fix(research-ideation): read/write ideation memory under /memories/
- fix(experiment-pipeline): read/write experiment memory under /memories/
