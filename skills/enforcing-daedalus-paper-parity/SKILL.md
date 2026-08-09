---
name: enforcing-daedalus-paper-parity
description: "Enforce that a Daedalus (EvoScientist) run actually performed the method its paper claims, instead of reporting success having done nothing. Use when: (1) launching a Daedalus run under Hermes and needing a launch record that pins skill versions and gate policy, (2) deciding whether to accept a finished run's evidence, (3) checking whether evolution memory persisted or silently reset, (4) auditing a stream-json transcript for decision gates that dissolved under auto-mode, (5) checking whether an upstream update invalidates the alignment review. Covers findings F1-F14 of docs/daedalus-paper-alignment-review.md."
allowed-tools: "read_file write_file execute think_tool"
metadata:
  author: Archimedes
  version: '1.0.0'
  tags: [parity, acceptance, provenance, daedalus]
---

# Enforcing Daedalus Paper Parity

Daedalus's characteristic failure is not an error. It is a clean `done` event
covering a cycle that evolved nothing, ranked nothing, and left no checkable
evidence. This skill makes each of those silent outcomes loud.

Every check here treats **absence of evidence as failure**. A gate that passes
because it found nothing to inspect is the exact bug the gates exist to prevent.

## When to use

| Moment | Script |
|---|---|
| Before launch | `launch_record.py build` |
| Before launch (config check) | `memory_persistence.py --require-pinned` |
| After the run | `parity_gates.py` |
| After the run | `evolution_enforcement.py` |
| After the run | `launch_record.py audit` |
| Before trusting the review | `check_upstream_drift.py` |

## The two facts that shape everything else

**Evolution memory has no writable persistent home.** The skills write M_I/M_E
to `/memory/`, which matches no backend route and resolves into the per-run
workspace. The persistent mount `/memories/` rejects raw writes outright. So
repointing the skills is not a fix; it converts silent loss into hard failure.
Persistence comes from pinning `EVOSCIENTIST_WORKSPACE_DIR` to one durable
directory, and the gate refuses to pass on an empty store because "empty" is
exactly what the skills read as "first cycle".

**Under `stream-json`, `ask_user` does not exist.** Auto-mode sets
`enable_ask_user=False`, which drops `AskUserMiddleware` entirely. Prompts that
tell the agent to consult a human are not auto-answered; they become inert text
the model may satisfy, narrate, or ignore. The replacement policy must therefore
be declared before the run, and the transcript audited for gates that were
narrated rather than resolved.

## Procedure

### 1. Before launch

```bash
python scripts/memory_persistence.py --workspace "$WS" --require-pinned
python scripts/launch_record.py build \
    --run-id "$RUN_ID" --workspace "$WS" \
    --gate-policy auto_select_top1 \
    --prompt "$PROMPT" --out "$RUN_DIR/launch-record.json"
```

Choose the gate policy deliberately: `auto_select_top1` follows the paper
(`P = Extend(Top-1)`); `surface_to_hermes` requires `--no-auto-mode` plus the
resume driver in `supervising-daedalus-mock-study-runs`. There is no third
option, and leaving it undeclared is the F6 failure itself.

Inject `templates/ideation-width-addendum.md` into the packet so the tournament
ranks the 15-21 leaves the skill's own reference specifies rather than three.

### 2. After the run

```bash
python scripts/parity_gates.py --workspace "$WS" \
    --launch-record "$RUN_DIR/launch-record.json" \
    --memory-baseline "$RUN_DIR/memory-baseline.json" \
    --report "$RUN_DIR/acceptance.json"
python scripts/evolution_enforcement.py --workspace "$WS"
python scripts/launch_record.py audit \
    --events "$RUN_DIR/native-events.jsonl" \
    --launch-record "$RUN_DIR/launch-record.json"
```

Any nonzero exit means do not accept the run. Each failure names the finding it
belongs to, so the rejection can be reported in the lab's own terms.

### 3. Periodically

```bash
git fetch upstream && python scripts/check_upstream_drift.py --repo .
```

Nonzero means upstream touched either a file carrying a deliberate fork
divergence (merge needs graft-not-pick) or a file the findings cite (the review
needs re-running before you act on it).

## What these checks do not do

They verify that the method's *artifacts* exist and are internally consistent.
They cannot verify that the science is good, that the Elo judgments were sound,
or that retrieval picked the right memories — retrieval is LLM-judged upstream,
and the launch record only records which entries were chosen.

They also do not fix the upstream defects. Drafts for those live in
`specs/005-daedalus-paper-alignment/contributions/`, unfiled.

## References

| Topic | File |
|---|---|
| The 14 findings, twice verified | `docs/daedalus-paper-alignment-review.md` |
| Remediation tasks and their status | `specs/005-daedalus-paper-alignment/tasks.md` |
| Upstream contribution drafts | `specs/005-daedalus-paper-alignment/contributions/` |
| Authority boundary this enforces | `docs/cognitive-lab-architecture.md` |
| Stage evidence contract | `templates/stage-record.json` |
| Ideation width addendum | `templates/ideation-width-addendum.md` |
