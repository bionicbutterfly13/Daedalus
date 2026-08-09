# Draft — EvoSkills PR (docs only; blocked on engine decision for the path itself)

Branch: docs/evo-memory-correct-persistence-claim
Title: docs(evo-memory): correct the claim that /memory/ maps to shared memory

**What changed and why**

`references/memory-schema.md` states: "All paths are relative to the workspace root. Memory
files persist across sessions because `/memory/` maps to the shared memory directory."
The second sentence is false against EvoScientist v0.2.6: the agent's CompositeBackend
routes `/skills/` and `/memories/` only, so `/memory/` falls through to the workspace
backend and resolves to `<workdir>/memory/` — per-run, not shared. Memory does not survive
a workdir change, and the skill's own "first cycle → skip" fallback hides the loss.

This PR corrects the claim and states the current behavior plainly. It deliberately does
**not** repoint the paths to `/memories/`: that mount rejects raw writes
(`MemoryFilesystemBackend.write` → "Raw writes to /memories are blocked"), so repointing
would turn silent loss into a hard failure. The path fix belongs with the engine decision
tracked in <engine issue #>.

Scope: one paragraph in `evo-memory/references/memory-schema.md`. No mechanism changes.

Commit:
- docs(evo-memory): state actual /memory/ persistence behavior
