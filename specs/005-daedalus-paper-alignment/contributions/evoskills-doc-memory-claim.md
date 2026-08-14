# Draft: EvoSkills PR (docs only)

Status: verified, but blocked until the EvoScientist memory-path issue is answered.

Branch: docs/evo-memory-workspace-local-paths
Title: docs(evo-memory): clarify workspace-local memory paths

**What changed and why**

`references/memory-schema.md` currently says: "All paths are relative to the workspace root.
Memory files persist across sessions because `/memory/` maps to the shared memory directory."

The second sentence does not match EvoScientist v0.2.6. The agent's `CompositeBackend` routes
`/skills/` and `/memories/`; singular `/memory/` matches no route and resolves through the
default workspace backend, so these files live under the selected workdir rather than in the
shared memory directory. In default `daemon` mode the workspace is the current directory, so
they do persist across sessions started from the same place — but a session using `run` mode
or a different `--workdir` will not see them, and the skill's "first cycle → skip" branch
makes that look like a fresh start.

This PR states the actual behavior. It deliberately does **not** repoint the paths to
`/memories/`: `MemoryFilesystemBackend` rejects raw writes there, so that change would break
memory writes outright. Where the paths should ultimately point is an engine question,
tracked in <engine issue #>.

Scope: one paragraph in `evo-memory/references/memory-schema.md`. No mechanism or
frontmatter changes, so no description eval applies.

Commit:
- docs(evo-memory): state actual /memory/ persistence behavior
