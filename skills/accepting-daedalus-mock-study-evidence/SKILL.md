---
name: accepting-daedalus-mock-study-evidence
description: Use when independently accepting Daedalus study evidence.
version: 0.1.0
author: Dr. Mani, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [research, evidence, validation, daedalus]
    related_skills: [supervising-daedalus-mock-study-runs, publishing-daedalus-study-journals]
---

# Accepting Daedalus Mock Study Evidence

Independently compare the frozen expected inventory with directly accessed Daedalus outputs. The Daedalus primary study report and the Archimedes independent evidence report are distinct artifacts with distinct authorship.

## When to Use

Use after supervision has preserved every attempt and declared the evidence ready for independent review. Do not use service health, narration, prior-agent summaries, or repository tests as substitutes for run evidence.

## Prerequisites

- Frozen packet, authorization, attempt manifest, native events, status, and run ledger.
- Evidence manifest with expected and observed artifacts.
- Daedalus-authored primary report, or an explicit missing/incomplete state.
- Direct read access to every artifact being certified.
- The supervised attempt root, with control evidence under
  `supervisor-evidence/` and Daedalus outputs under `workspace/`.

## How to Run

Use `terminal` with:

```text
python3 skills/accepting-daedalus-mock-study-evidence/scripts/validate_mock_study.py ATTEMPT_DIRECTORY
```

This validator is read-only and stdlib-only. Its default mode accepts only the
supervised split layout. The explicit `--legacy-fixture-only` option exists for
deterministic package fixtures and can return only `fixture_valid`, never
`accepted`. It must not be used for production evidence. Exit zero means the
selected synthetic evidence contract passed. Nonzero means fail closed and the
JSON output lists exact reasons.

## Procedure

1. Read the packet and authorization directly. Confirm the study is synthetic and execution matched the frozen scope.
2. Read control records from `supervisor-evidence/` and the Daedalus primary
   report from `workspace/`. Logical artifact names remain stable across the
   split layout.
3. Recompute the immutable attempt-manifest digest, frozen-input digests, state
   chain, ledger chain, pending-request digests, per-cycle request and worker
   identities, decision-to-resume payload linkage, aggregate native stdout/stderr,
   and every artifact size and SHA-256. Reject symlinked run or control roots
   before reading evidence through them.
4. Read `execution_mode` and `evidence_ceiling` directly from the supervised
   attempt. A deterministic adapter is E2 at most. Reject any Archimedes report
   or downstream claim that relabels adapter evidence as E3.
5. Compare expected versus produced outputs. Keep missing, empty, stale, duplicate, overwritten, or unlinked evidence explicit.
6. Verify Daedalus reported the research question, hypothesis, synthetic inputs,
   methods, attempted stages, analyses, outputs, measured results,
   failures/retries, limitations, and unresolved questions. Real native events
   use Daedalus `type` fields and do not invent semantic stage labels.
   Archimedes records a separate `workflow_stage_evidence` map with unique,
   resolvable references. Only direct `verified_execution` or `observed_result`
   evidence can satisfy a stage. Each of the six declared stages must point to
   its required Daedalus report fragment; inference, hypothesis, unknown,
   wrong-fragment, duplicate-reference, and invented-stage mappings fail closed.
   Archimedes must not manufacture missing Daedalus content.
7. Assign `accepted`, `partial`, `failed`, or `stopped`. Archimedes must not convert a partial or failed run into success.
8. Write the Archimedes report from direct evidence and list timing, stop conditions, concerns, and remaining gaps.

Completion criterion: the verdict is reproducible from the retained records, and every directly verified claim names its source.

## Pitfalls

- An internally consistent manifest can still describe stale bytes; recompute from files.
- Exit zero plus empty required output is silent success.
- A missing Daedalus section is not permission for Archimedes to write it.
- A retry sharing an earlier path destroys attempt identity.
- A stage name inside an Archimedes report is not native runtime evidence. Keep
  its evidence class and exact artifact or event reference explicit.
- A flat fixture is not a supervised attempt. Legacy fixture mode is a package
  test aid and cannot produce an accepted verdict.
- A local hash chain detects changes relative to itself; it does not prove who
  authored the chain. Compare it with an independently retained snapshot anchor
  for E3 acceptance.
- Publication preparation follows acceptance; it is not part of the evidence verdict.

## Verification

- Run the valid synthetic fixture and every corruption test.
- Confirm each corruption fails with a specific reason.
- Confirm the three deliverables retain separate authorship.
- Confirm no validator path writes to the run directory.
