# Draft — engine bug issue (template: bug_report, label: bug)

Title: Skills write memory to `/memory/` but the engine mounts `/memories/` — evolution
memory silently lands in the per-run workspace

**Describe the bug**
The EvoSkills evolution skills (`evo-memory`, `research-ideation`, `experiment-pipeline`)
read and write Ideation Memory and Experimentation Memory at `/memory/ideation-memory.md`
and `/memory/experiment-memory.md`. The engine's CompositeBackend routes only `/skills/`
and `/memories/` (plural); `/memory/` matches no route and falls through to the default
workspace backend rooted at the current workdir. Cross-cycle memory therefore never
reaches the persistent store: each run in a fresh workdir starts with empty M_I/M_E, and
the skills' own "If M_I doesn't exist yet (first cycle), skip this step" instruction makes
the loss indistinguishable from a genuine first cycle. No error is raised at any point.

Three-way contradiction:
- CONTRIBUTING.md architecture diagram: `/memory/ --> FilesystemBackend (persistent
  cross-session)` (documents the singular path as persistent)
- Engine code: mounts `/memories/` only (both agent constructors' route tables)
- EvoSkills: write `/memory/` (singular) throughout evo-memory/SKILL.md and the
  Step-0 sections of research-ideation and experiment-pipeline

**To Reproduce**
1. Install evo-memory + research-ideation; run any ideation cycle to completion in
   workspace A (IDE writes /memory/ideation-memory.md)
2. `ls ~/.evoscientist/memories/` → no ideation-memory.md; `ls <workspace-A>/memory/` → file is here
3. Run a second cycle in fresh workspace B → Step 0 reports first-cycle, no directions recalled

**Expected behavior**
M_I/M_E persist across runs and workspaces (the paper's core accumulation mechanism,
arXiv 2603.08127 §3.5), or a missing mount fails loudly instead of silently redirecting
writes to the workspace.

**Environment**
- EvoScientist v0.2.6, macOS 15 (Darwin 24.6.0), Python 3.11, default (safe) mode

**Additional context**
Because `/memory/` reaches the plain workspace backend, these files also bypass
MemoryFilesystemBackend's create/edit protections. Happy to PR whichever direction
maintainers prefer: route `/memory/` as an alias of `/memories/` in the engine, or fix the
path in EvoSkills (draft ready) — the CONTRIBUTING diagram should match the outcome either way.
