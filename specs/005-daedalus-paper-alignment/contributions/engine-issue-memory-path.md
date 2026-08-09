# Draft — engine bug issue (template: bug_report, label: bug)

Title: Evolution memory has no writable persistent path: skills write `/memory/` (unmounted,
per-workspace) and `/memories/` rejects raw writes

**Describe the bug**

The EvoSkills evolution skills (`evo-memory`, `research-ideation`, `experiment-pipeline`,
`experiment-iterative-coder`) read and write Ideation Memory and Experimentation Memory at
`/memory/ideation-memory.md` and `/memory/experiment-memory.md`. Neither of the two
candidate locations gives that mechanism what the paper (arXiv 2603.08127 §3.5) requires,
which is a store that is both persistent across runs and writable by the agent:

- `/memory/` (what the skills use) matches **no route** in the agent's `CompositeBackend`,
  so it falls through to the default workspace backend and resolves to
  `<workdir>/memory/`. Writes succeed; the data dies with the workdir.
- `/memories/` (the persistent mount) is served by `MemoryFilesystemBackend`, whose
  `write()` returns `"Raw writes to /memories are blocked."` unconditionally, and whose
  `edit()` is restricted to *existing* files under `/memories/profile/`. Creating
  `ideation-memory.md` there is impossible through the agent's file tools.

Net effect: cross-cycle memory never persists. Because the skills instruct "If M_I doesn't
exist yet (first cycle), skip this step", a wiped store is indistinguishable from a genuine
first cycle, so every run silently restarts from zero and still reports success. The
self-evolution mechanism — the project's headline contribution — cannot accumulate.

This also means simply repointing the skills at `/memories/` does **not** fix it; that
change converts a silent data-loss bug into a hard write failure. Any fix has to come from
the engine side (a writable persistent route, or memory tools that own these files).

**To Reproduce**

Boundary capture against the shipped backends (v0.2.6, default/safe mode):

```python
from deepagents.backends import CompositeBackend
from EvoScientist.backends import FilesystemBackend, MemoryFilesystemBackend

backend = CompositeBackend(
    default=FilesystemBackend(root_dir=str(workspace), virtual_mode=True),
    routes={"/memories/": MemoryFilesystemBackend(root_dir=str(memories), virtual_mode=True)},
)

backend.write("/memories/ideation-memory.md", "# M_I\n")
# -> error: 'Raw writes to /memories are blocked. Edit existing
#            /memories/profile/... files or use memory tools.'

backend.write("/memory/ideation-memory.md", "# M_I\n")
# -> error: None, file lands at <workspace>/memory/ideation-memory.md  (not persistent)
```

End to end: run any ideation cycle to completion in workspace A (IDE writes M_I), then run
a second cycle in a fresh workspace B. Step 0 reports "first cycle" and recalls nothing;
`~/.evoscientist/memories/` never receives the file.

**Expected behavior**

M_I/M_E persist across runs and workspaces, per the paper's accumulation mechanism, without
requiring the operator to pin a workspace directory.

**Additional context**

Three sources currently disagree about this path, which is probably how the gap survived:

- `CONTRIBUTING.md` architecture diagram: ``/memory/ --> FilesystemBackend (persistent
  cross-session)`` — documents the singular path as persistent
- Engine code: mounts `/memories/` only, and write-guards it
- EvoSkills `evo-memory/references/memory-schema.md`: "Memory files persist across sessions
  because `/memory/` maps to the shared memory directory" — states the same incorrect claim

Possible directions, maintainers' call:
1. Route `/memory/` to a writable persistent backend (matches CONTRIBUTING's diagram and
   needs no EvoSkills change);
2. Relax `MemoryFilesystemBackend` to permit a declared allowlist of evolution-memory
   filenames, then fix the paths in EvoSkills;
3. Expose evolution memory through memory tools instead of file paths.

Happy to PR whichever direction is preferred, plus the CONTRIBUTING/EvoSkills doc
corrections that follow from it.

**Environment**
EvoScientist v0.2.6, macOS 15 (Darwin 24.6.0), Python 3.11, default (safe) mode.
