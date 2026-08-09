---
name: preparing-daedalus-mock-studies
description: Use when freezing a synthetic Daedalus study packet.
version: 0.1.0
author: Dr. Mani, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [research, preregistration, authorization, daedalus]
    related_skills: [conducting-daedalus-mock-studies, supervising-daedalus-mock-study-runs]
---

# Preparing Daedalus Mock Studies

Freeze one synthetic study packet and a separate authorization record before Daedalus starts. Preparation defines boundaries; it does not grant execution, provider, transfer, private-memory, or publication permission.

## When to Use

Use after the synthetic question is selected and before any Daedalus process is launched. Do not use private research content or inherit authorization from an earlier run.

## Prerequisites

- Synthetic inputs with stable IDs and SHA-256 digests.
- A declared real Daedalus interface to verify at launch time.
- Expected stages, artifacts, stop rules, and public-journal intent.
- Exact action, argv, path, artifact, runtime, and interrupt-cycle boundaries
  for the supervised driver.
- Dr. Mani's scoped decisions recorded separately from defaults.

## Procedure

1. Copy `templates/study-packet.json` and replace every unresolved identity before execution.
2. Freeze the question, hypothesis, synthetic input inventory, stages, methods, expected artifacts, and acceptance criteria.
3. Freeze permitted and prohibited operations, provider/cost boundary, retention, transfer, retries, timeouts, and kill criteria.
4. Freeze the public destination, title, authorship, public/private inventory, redaction rules, evidence links, approval state, and correction procedure.
5. Instantiate the supervision skill's `execution-allowlist.json` and `supervisor-runtime.json`. An action must match the frozen name, arguments, argv, and path indexes exactly. Runtime credentials are named by environment-variable name only and never stored in the packet.
6. Copy `templates/authorization-record.json`; set only actions Dr. Mani explicitly authorized and attach the exact approval evidence. Study execution authorization never preapproves a tool. Every interrupt retains its own exact-digest human gate.
7. Canonically serialize and hash all records. Archimedes must not substitute a manual or simulated stage for a broken Daedalus function.

Completion criterion: the records are immutable, complete, mutually consistent, and every consequential authorization defaults false unless explicitly approved.

## Pitfalls

- A study packet is not an authorization record.
- A study authorization is not an action approval.
- `synthetic_study: true` is invalid when any input came from private memory or research data.
- A planned publication destination does not authorize publication.
- An expected artifact without a stage and producer cannot be accepted later.

## Verification

- Recompute every listed input digest from the exact synthetic bytes.
- Confirm no unresolved source identity remains before launch.
- Confirm all authorization booleans match explicit approval evidence.
- Confirm `publication_authorized` remains false during article preparation.
