# EvoScientist Authorship Incident: Accurate Words, Incomplete Isolation

**Date:** 2026-07-31

**Status:** observed incident; journal accepted; prevention controls proposed

**Scientific inputs touched:** none

**Model, GPU, Colab, pilot artifact, or confirmation access:** none

## The short version

EvoScientist was given a narrow writing job: read four named sources and write one
journal entry explaining the blinded prompt-disjointness check. The finished
journal was accurate. It disclosed no prompt text, protected identity, individual
digest, category, or collision location.

The run itself did not obey the promised evidence boundary. Before reading the
packet, EvoScientist called its observation-search and memory-read tools. It also
first wrote the journal relative to the command-line working directory instead of
the intended repository path. A separate transport defect then stopped the first
attempt with:

```text
BaseChatModel._aiter_v2_events() got multiple values for keyword argument 'stream'
```

The wrong-path copy was removed, the transport defect was repaired, and the final
journal was read back and hash-verified. That gives us an accurate document. It
does not let us describe the authorship process as hermetic.

## What we asked the system to do

Codex prepared a packet that named four readable sources:

1. the closed disjointness certificate;
2. the certificate contract;
3. the preregistered exact-text-disjointness rationale;
4. the authorship prompt itself.

The only permitted output was `journals/evo/2026-07-31.md`. The purpose was to
let EvoScientist explain why we compared 600 proposed development prompts with
the sealed 200-prompt identities without revealing the protected prompts.

The final journal has SHA-256:

```text
716067a695b46c38645548d3873486481ffb4c4c9d2a02a3315cce81ae86a597
```

Its factual core is narrow: nine exact-text/hash overlaps were found, version 1
stopped, and no scientific measurement occurred.

## What actually happened

There were two different failures.

### 1. The evidence boundary existed only as an instruction

EvoScientist still had access to its ordinary memory tools. Its trace shows calls
to observation search and memory read before it opened the bounded packet. The
instruction said "read only these sources," but the runtime never removed the
other capabilities.

This is the same difference as putting a sign on a laboratory cabinet versus
locking the cabinet. The sign communicates intent. The lock enforces it.

No trace evidence shows access to the sealed prompt manifests, the Colab artifact,
or confirmation data. The accepted journal contains only facts available in the
authorized packet. The incident is therefore a provenance-control failure, not a
known scientific-data disclosure. We preserve that distinction.

### 2. The streaming repair used a keyword LangChain already owned

The EvoScientist middleware had been forcing streaming by adding a Boolean
`stream=True` call argument. LangChain Core 1.5.1 uses the same keyword internally
for its asynchronous stream object. Both values reached the same function, so
Python rejected the call before the provider request.

The focused repair creates a per-request model copy with streaming enabled and
removes the conflicting call argument. This leaves the shared model and the tool
selector unchanged. The complete runtime suite passed 3,337 tests with 12 skips,
and the repaired run produced the accepted journal. The repair remains local and
uncommitted pending review.

## Why an accurate final document is not enough

Scientific provenance describes how a result was produced, not only whether the
last paragraph sounds right. If an author can consult undeclared memory, we cannot
prove that every inference came from the reviewed evidence packet. Three risks
follow.

- **Hidden contamination:** prior observations may contain facts, interpretations,
  or errors unavailable to an independent author.
- **Poor reproducibility:** another clean run given the same four files may produce
  different reasoning because it lacks the undeclared memory state.
- **False assurance:** labeling the output "source-bound" would overstate the
  experiment even when every sentence happens to be correct.

This matters most when the inputs are blinded. A sealed-data protocol fails if we
rely on the agent's discretion not to use capabilities it still possesses.

## Prevention standard

Future bounded authorship should use a restricted execution mode. These controls
are requirements for that mode; except for the streaming repair and its tests,
they are **proposed and not yet implemented**.

### Before the run

1. Start a fresh thread with persistent memory retrieval disabled.
2. Create a clean authorship workspace containing only content-addressed copies of
   the approved sources.
3. Use absolute paths for every input and the single output.
4. Emit a preflight record containing the workspace identity, source paths, source
   hashes, allowed tools, output path, and run ceiling.
5. Refuse to start unless the available tool set exactly matches the allowlist.

For this class of job, the allowlist should normally contain only exact-file read
and single-file write operations. Observation search, memory read, web access,
shell execution, delegation, and unrestricted filesystem search should be absent,
not merely discouraged.

### During the run

1. Enforce allowed read paths in middleware or the filesystem backend.
2. Enforce one allowed write path and reject relative paths, symlinks, traversal,
   and additional writes.
3. Abort on the first undeclared tool call. Do not let the run finish and explain
   the deviation afterward.
4. Record the ordered tool trace, resolved paths, byte counts, and content hashes.

### After the run

Acceptance requires two independent checks:

1. **Content check:** every factual claim is supported by the approved packet.
2. **Execution check:** the trace contains only allowed tools and paths, with no
   hidden memory or network access.

The run should emit a small execution attestation containing the input hashes,
output hash, tool-call inventory, policy-violation count, and terminal decision.
Any violation makes the result rejected, even if the prose is accurate.

## Tests required before we trust restricted authorship

The implementation should prove that it fails closed when:

- an agent calls observation search or memory read;
- an input path is outside the allowlist;
- a permitted path resolves through a symlink;
- the working directory differs from the declared workspace;
- the agent attempts a second output or a relative output path;
- a source changes after preflight;
- an unexpected tool appears after startup;
- the streaming middleware receives a conflicting `stream` setting.

A successful test is not "the agent chose not to look." A successful test is
"the runtime made looking impossible and recorded that fact."

## Operational rule from now on

Until restricted authorship is implemented and adversarially reviewed,
EvoScientist-authored documents may be accepted as source-grounded only after
their content and complete trace are reviewed. They must not be labeled hermetic,
blinded, or read-isolated solely because the prompt requested those properties.

The incident record is
`journals/_sources/2026-07-31-primary-floor-disjointness-evo-execution.md`.
The accepted journal is `journals/evo/2026-07-31.md`. Neither record authorizes a
new development manifest, model run, pilot, artifact transfer, or confirmation
access.
