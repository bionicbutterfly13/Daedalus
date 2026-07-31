# Archimedes / EvoScientist Constitution

Governs work in this repository: the EvoScientist agent runtime and the J-space
cognitive lab that runs on top of it. Every `speckit.plan` and `speckit.analyze`
run checks against this document.

This is a **fork** (`bionicbutterfly13/EvoScientist`) of a public upstream
(`EvoScientist/EvoScientist`). That fact constrains several principles below.

## Core Principles

### I. Correctness before minimality

The standing priority order is: **correctness, evidence, safety, minimal change,
consistency, performance.** When two conflict, the lower number wins. A smaller
diff that is not clearly correct loses to a larger one that is.

Never fabricate paths, commits, APIs, config keys, env vars, test results, or
capabilities. State gaps explicitly. An unverified claim must be labelled
unverified in the same breath it is made.

### II. Evidence proportional to risk (NON-NEGOTIABLE)

Trivial edits need the target file and its neighbours. Behavioural, API,
dependency, or infrastructure changes need the execution path, call sites,
constraints, and regression surface traced *before* editing.

Prefer external verification to self-review: a fresh test beats re-reading your
own code. Where a system spans process or network boundaries, **capture what
actually crosses the boundary before reasoning about what might.** Replaying a
captured payload with one variable toggled outranks any amount of deduction.

### III. Never game verification

Do not weaken assertions, narrow scope, reduce coverage, or skip checks to get a
pass. Preserve existing tests; update them when behaviour changes, and say so
explicitly.

Be alert to tests that assert *absence* — they can silently codify a bug as a
contract. If a test and the comment above it disagree about intent, one of them
is wrong and the code is probably wrong too.

### IV. Declared means consumed

Any preregistered threshold, constant, flag, or config value must be **consumed
on the path it claims to govern**, not merely declared and recorded. A constant
written into an artifact but never read is worse than a missing one: the artifact
testifies that it was used.

Where a run emits provenance, assert the linkage — every declared constant has a
consuming gate, every gate reads only declared constants — and fail the run
rather than produce artifacts that overstate what was tested.

### V. The record must not overstate the work

Reports, artifacts, and provenance state precisely what was evaluated, including
what was *not*. When an audit finds the record claimed more than was tested, the
remediation is to amend the record, not to quietly restate the claim.

Content-addressed evidence is immutable. Its hash is the anchor other documents
cite; never reformat, lint, or "fix" such an artifact after the fact. Exclude it
from formatters and linters before committing, and re-verify the digest after.

## Scientific Protocol (J-space lab)

Binds all work under `j-space-lab/` and
`EvoScientist/skills/jspace-research-operations/`.

- **Stage gates are hard.** Observation-only stages produce evidence class 1.
  Nothing promotes to a functional, cognitive, or phenomenal claim without a
  Stage 3 preregistration and its own ratification. An ambiguous result
  authorizes no promotion.
- **Preregister, then execute.** Thresholds lock before data collection and do
  not move after. Where no pilot estimate exists, derive the threshold from a
  preregistered pilot rather than inventing a number — a threshold set by guess
  produces results nobody can interpret.
- **Measure against a ground truth.** A difference metric cannot answer an
  information question. If the endpoint has no notion of correct, the strongest
  available conclusion is non-identity, whatever the sample size.
- **Dr. Mani ratifies.** Execution of any GPU run, and any parameter that changes
  what gets measured, is his decision. Design work proceeds; execution waits for
  an explicit signature (`THRESHOLDS_RATIFIED`).
- **Artifacts stay put.** Transfer or download of evidence artifacts is a
  separate authorization gate.

## Safety and Boundaries

- **Never push to the public upstream.** The push URL is hard-disabled
  (`git remote set-url --push upstream DISABLED`); a failure there is expected,
  not a credentials problem. All PRs are fork-internal: `gh pr create` defaults
  to the parent repo, so always pin
  `--repo bionicbutterfly13/EvoScientist --base main`.
- **Outward-facing actions need explicit permission**: filing public issues,
  publishing, sending messages, or anything else that leaves this machine.
  Drafting is fine; sending is not.
- **Commit only when asked.** No force-push to main, no `--no-verify`, no
  `--no-gpg-sign`, no history rewriting.
- **Secrets are never logged, quoted, echoed, or committed.** If a
  credential-shaped value appears, note the location and stop handling that
  surface. `ccproxy --log-level debug` prints upstream bearer tokens.
- **Stay inside the project root** unless a path is explicitly named.
  `/Volumes/Asylum/Sync` requires per-request confirmation regardless.
- **Before deleting or overwriting, look at the target.**

## Runtime Invariants

Non-obvious properties of this environment, each of which has cost real debugging
time. Violating one produces a misleading error, not a clear failure.

- The EvoScientist runtime is an **editable install** from
  `/Volumes/Asylum/archimedes`. Never point `EvoSci --workdir` at a directory
  that is itself a checkout of this repo — `cwd` precedes site-packages on
  `sys.path`, so the checkout's `EvoScientist/` package shadows the install and
  the server silently runs another branch's code. Use a subdirectory holding the
  data but no same-named package. Verify with
  `python -c "import EvoScientist; print(EvoScientist.__file__)"`.
- `langgraph dev` runs `--no-reload`. **Restart the stack after any code change**
  or it keeps serving the resident module.
- `ccproxy` runs as a **separate OS process**. Client-side monkey-patches of
  ccproxy internals cannot reach it; patches written that way are dead code.
- `.env` loads with `override=False` **deliberately**. The live process
  environment outranks a file on disk, because startup installs the ccproxy OAuth
  route there before workers reload config. Do not flip this back.
- Silent success is this stack's characteristic failure mode. A run that reports
  success while producing nothing is a bug, not a no-op.

## Development Workflow

- **Branch per concern; PRs fork-internal and small.** Verify each branch green
  *standing alone*, not only combined with other pending work — a reviewer sees
  it alone.
- **Discover validation commands from local tooling**, then run the narrowest
  relevant check, widening as risk justifies. If checks already fail before your
  change, say so; do not attribute them to your work.
- **Stop conditions:** if the expected path fails, report what failed, what
  changed, and one or two concrete options. Do not silently substitute a
  different approach, and never substitute a manual scaffold for a requested
  official path without approval.
- **Adversarial review for non-trivial fixes.** Cross-check design decisions with
  a second agent (Codex) before implementing. Treat its output as evidence, not
  authority — verify its claims against the source, and expect to correct it as
  often as it corrects you.
- **Capture reusable knowledge.** Non-obvious debugging outcomes become skills;
  durable project facts become memory entries.

## Governance

This constitution supersedes ad-hoc practice. It does not supersede Dr. Mani's
explicit instruction in the moment; when he reaffirms a request after a concern
is raised, that is his decision and the work proceeds.

Amendments require a rationale recorded alongside the change and a version bump.
Principles marked NON-NEGOTIABLE may be amended but never waived silently.

The Spec Kit tooling here serves two agents. Codex skills live in `.agents/` and
are tracked; Claude Code skills live in `.claude/skills/`, which `.gitignore`
excludes. Installed-integration state itself is tracked in
`.specify/integration.json`.

Restore the Claude skills on a fresh clone with **`specify integration upgrade
claude`**, not `install`. Because `.specify/integration.json` is tracked and
already lists `claude`, `install` reports "Integration 'claude' is already
installed / No files were changed" and creates nothing — the clone is left with no
skills and no error. `upgrade` writes all eleven and leaves the shared templates
and scripts alone; refreshing those needs an explicit `--force`, which is a
separate decision (see `project-state.md` § Spec Kit template drift).

**Version**: 1.0.1 | **Ratified**: 2026-07-26 | **Last Amended**: 2026-07-26

*Amendment 1.0.1 (2026-07-26)*: corrected the Claude skills restore command from
`install` to `upgrade`. The original was an inference from the CLI's help text,
not a tested claim. Verified by cloning the repo to a scratch directory and
running both: `install` produced zero skills, `upgrade` produced eleven and left
`.specify/scripts/` and `.specify/templates/` byte-identical. The same check found
that the repo's own Claude install was missing `speckit-agent-context-update`,
leaving the armed `after_specify`/`after_plan` hooks unrunnable from Claude Code;
`upgrade` installed it.
