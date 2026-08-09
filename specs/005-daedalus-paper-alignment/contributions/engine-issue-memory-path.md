# Draft — engine bug issue (template: bug_report, label: bug)

Title: Evolution-memory files are workspace-local, but documented as shared

**Describe the bug**

The EvoSkills evolution skills store Ideation and Experimentation Memory at
`/memory/ideation-memory.md` and `/memory/experiment-memory.md` (`evo-memory`,
`research-ideation`, `experiment-pipeline`, `experiment-iterative-coder`). The agent's
`CompositeBackend` routes `/skills/` and `/memories/` only, so singular `/memory/` falls
through to the default workspace backend and resolves under the selected workdir. Two
documented statements disagree with that behavior:

- `CONTRIBUTING.md` architecture diagram lists `/memory/ --> FilesystemBackend (persistent
  cross-session)`.
- `evo-memory/references/memory-schema.md` states "Memory files persist across sessions
  because `/memory/` maps to the shared memory directory."

In practice the files are per-workdir. A session that changes its workdir — `run` mode, or
`--workdir` pointing somewhere new — sees an empty M_I/M_E and, because the skills instruct
"If M_I doesn't exist yet (first cycle), skip this step", proceeds as though it were a first
cycle rather than reporting anything missing. In the default `daemon` mode, where the
workspace is the current directory, the files do persist across sessions launched from the
same place, which is probably why this has gone unnoticed.

Repointing the skills at `/memories/` is not a workaround: `MemoryFilesystemBackend` rejects
raw writes and permits edits only to existing files under `/memories/profile/`, so that
change would replace a silent visibility gap with a hard write failure.

This looks like an integration gap rather than a missing capability. The engine already
offers persistent, agent-writable storage — editable profile files under
`/memories/profile/` and `record_observation(scope="global")` under
`/memories/observations/global/` — but the shipped evolution skills use neither, and target
a path the router does not serve.

**To Reproduce**

Direct backend reproduction, runnable as written against v0.2.6:

```python
import tempfile
from pathlib import Path

from deepagents.backends import CompositeBackend
from EvoScientist.backends import FilesystemBackend, MemoryFilesystemBackend

with tempfile.TemporaryDirectory() as tmp:
    workspace = Path(tmp) / "workspace-A"
    memories = Path(tmp) / "memories"
    workspace.mkdir()
    memories.mkdir()

    backend = CompositeBackend(
        default=FilesystemBackend(root_dir=str(workspace), virtual_mode=True),
        routes={"/memories/": MemoryFilesystemBackend(root_dir=str(memories),
                                                      virtual_mode=True)},
    )

    singular = backend.write("/memory/ideation-memory.md", "# M_I\n")
    print("write /memory/   ->", "OK" if singular.error is None else singular.error)
    print("   landed at     ->",
          [str(p.relative_to(tmp)) for p in Path(tmp).rglob("ideation-memory.md")])

    plural = backend.write("/memories/ideation-memory.md", "# M_I\n")
    print("write /memories/ ->", plural.error)
```

Observed output:

```
write /memory/   -> OK
   landed at     -> ['workspace-A/memory/ideation-memory.md']
write /memories/ -> Raw writes to /memories are blocked. Edit existing /memories/profile/... files or use memory tools.
```

End to end: run an ideation cycle to completion with `--workdir /tmp/ws-a`, confirm
`/tmp/ws-a/memory/ideation-memory.md` exists while `~/.evoscientist/memories/` does not
contain it, then run a second cycle with `--workdir /tmp/ws-b`. Step 0 reports a first cycle
and recalls nothing. Default `daemon` mode with an unchanged directory will not show the
reset.

**Expected behavior**

Either evolution memory is reachable across workdirs, matching what `CONTRIBUTING.md` and
`memory-schema.md` describe, or the documentation is corrected to say the files are
workspace-local.

**Environment**

EvoScientist v0.2.6, macOS 15 (Darwin 24.6.0), Python 3.11, default (safe) mode.

**Additional context**

Because these files sit on the workspace backend, they also receive none of
`MemoryFilesystemBackend`'s create/edit/delete guards.

Happy to send a PR in whichever direction is preferred — routing `/memory/` to a persistent
writable backend, allowing a named set of evolution-memory files under `/memories/`,
migrating the skills onto the existing observation tools, or correcting the two
documentation statements. The choice affects EvoSkills as well, so it seemed better to ask
before proposing a patch.
