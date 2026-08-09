---
name: supervising-daedalus-mock-study-runs
description: Use when operating an authorized synthetic Daedalus run.
version: 0.1.0
author: Dr. Mani, Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [research, runtime, monitoring, daedalus]
    related_skills: [preparing-daedalus-mock-studies, accepting-daedalus-mock-study-evidence]
---

# Supervising Daedalus Mock Study Runs

Launch and monitor a frozen synthetic study through the real Daedalus interface. Preserve native evidence; do not substitute a simulation, manual analysis, or operator-authored output for a broken Daedalus function.

## When to Use

Use only after the packet is frozen and study execution is explicitly authorized. Do not use this skill to activate providers, broaden filesystem access, access private memory, transfer artifacts, or publish.

## Prerequisites

- Frozen packet and matching authorization record.
- Current interface rechecked with `terminal(command="EvoSci --help")`.
- Data-only work directory containing no `EvoScientist/` package.
- Installed import path verified outside a checkout package.
- A `ready` result from `scripts/daedalus_preflight.py` for the exact launcher,
  repository, data-only work directory, and frozen WebUI source.
- Frozen `templates/execution-allowlist.json` and
  `templates/supervisor-runtime.json` instances for this packet.
- Authorization explicitly sets `tool_action_preapproval_authorized` false and
  `tool_action_approval_policy` to `separate_per_interrupt_exact_digest`; every
  prohibited boundary must be present as the boolean `false`.
- Unique attempt directory whose `workspace/` is the data-only work directory;
  `supervisor-evidence/` remains outside Daedalus's workspace.
- A host where the preflight proves the process-containment contract. The current
  implementation uses macOS `sandbox-exec` and fails closed when it is absent.
- A production-safe Daedalus subagent execution gate. The current source does
  not have one: `create_cli_agent` applies execution interrupts to the main
  agent only while synchronous subagents remain available. The driver and
  preflight therefore report `subagent_execute_human_gate_unresolved` and block
  production starts. Do not waive this check or treat adapter readiness as
  permission to run a model.
- Deterministic enforcement of the packet's `maximum_cost_usd` before any paid
  provider is enabled. The current driver validates the provider boundary but
  deliberately returns `provider_cost_enforcement_unavailable` for every paid
  production request. A positive number in a packet is not an enforced cap.

## Procedure

1. Recheck `references/current-daedalus-interface.md` against current source and CLI help. Run `scripts/daedalus_preflight.py` read-only and stop if its JSON status is `blocked`; never waive a failed check inside the run operator.
2. Resolve the source commit, imported package path, packet digest, authorization digest, exact work directory, and attempt ID before launch. Study authorization is not tool approval.
3. Freeze exact action names, arguments, argv, path arguments, path SHA-256
   identities, and artifact paths in the execution allowlist. The first harness
   permits only an exact `python3` script action. Reject network, transfer,
   publication, private-memory, traversal, symlink-escape, changed-script, and
   undeclared-write requests. The nested action sandbox must also deny every
   child executable, so the frozen script cannot introduce an undeclared
   subprocess.
4. Start only through the supervisor:

   ```text
   python3 scripts/drive_stream_json_resume.py start --repo-root REPO --packet PACKET --authorization AUTHORIZATION --allowlist ALLOWLIST --preflight PREFLIGHT --runtime-config RUNTIME --prompt-file PROMPT --attempt-dir ATTEMPT --workdir ATTEMPT/workspace --launcher EVOSCI_PATH --attempt-id ATTEMPT_ID --timeout-seconds SECONDS --max-cycles COUNT
   ```

5. If the result is `awaiting_approval` or `awaiting_user_input`, inspect the write-once `pending-NNN.json`. An explicit operator decision must repeat its exact `request_digest`. The driver recomputes that digest and verifies the complete pending identity before writing the decision. Invalid answers and corrupted pending or ledger records consume no decision slot. No decision is inferred from the packet, authorization, process exit, or terminal `done` event.
6. Approve one exact request or provide one exact answer set with `drive_stream_json_resume.py decide`. Rejection stops without resume. Approval uses the exported local gateway with `Command(resume=...)`, the exact full thread ID, and one new append-only cycle.
7. Repeat the human gate for every new interrupt until completion or the frozen cycle cap. Duplicate decisions, resumes, action IDs, interrupt IDs, changed requests, and replayed events fail closed.
8. Reconcile the terminal event, exit status, source identity, worker identity,
   work-directory delta, process-containment result, and required artifacts.
   The worker may write only inside the attempt. The approved Python action runs
   through a nested no-network wrapper with workspace-only writes and protected
   user/volume reads and child process execution denied. Declared provider
   credentials are removed from the process environment before tool execution.
   Timeout terminates the complete worker process group, not only its parent
   PID.
9. Preserve every attempt. A retry gets a new attempt ID and new evidence paths. Never overwrite, delete, or backfill a failed attempt.

Completion criterion: every cycle, interrupt, decision, resume, and terminal
state is preserved and internally consistent; every retry is isolated; required
Daedalus outputs exist; and no Archimedes substitute appears as Daedalus output.
Independent stage mapping and the scientific verdict belong to the acceptance
skill.

## Pitfalls

- A PID or listener proves process state, not research execution.
- Empty stream output plus exit zero is Silent success, not a no-op.
- `cwd` can shadow the editable install when it contains `EvoScientist/`.
- Generic `python` can be absent even when the launcher's exact interpreter works; use the preflight to test the documented command through the launcher environment.
- Stream termination does not prove server-side or artifact completion.
- `stream-json` implicitly enables unattended auto-mode unless `--no-auto-mode` is explicit.
- `EvoSci --resume` continues a conversation with a new text prompt; it does not send the interrupt-resume payload required by this supervisor.
- Native local stream events expose no run ID. `supervisor_run_id` is Archimedes-owned and must never be described as a native Daedalus run ID.
- Reusing output paths destroys retry provenance.
- Process containment is currently macOS-specific and uses a deprecated host
  utility. Preflight must block unsupported hosts. This E1/E2 contract is not E3
  proof that the real provider/runtime path remains compatible.
- `enable_async_subagents=False` does not disable subagents. It keeps configured
  subagents in-process, where their `execute` calls do not inherit the main
  agent's human interrupt middleware. Until a supported gate or disable path is
  implemented and tested, production execution is intentionally unreachable.
- Paid-provider authorization is also intentionally unreachable. The driver has
  no trustworthy spend meter or hard cutoff, so it fails closed even when the
  provider allowlist, approval record, and positive cost ceiling agree.
- `O_EXCL`, append mode, and SHA-256 chains make driver output write-once and
  tamper-evident under the retained chain. They are not a signature or an
  operating-system append-only guarantee against an actor who can rewrite the
  whole attempt. E3 evidence needs an independently retained hash anchor.

## Verification

- Read native events, stderr, status, and artifacts directly.
- Confirm run ID, thread ID, attempt ID, source identity, and packet ID agree.
- Confirm `execution_mode` is `deterministic_adapter` with
  `evidence_ceiling: E2` for fixture trials. Adapter evidence must never be
  relabeled E3. Confirm frozen `supervisor-source.py` and
  `cycle-worker-source.py` digests match the attempt manifest.
- Confirm `run_id_authority` is `archimedes_supervisor`, `native_run_id` remains null, and the exact thread ID is present in every cycle request and worker result.
- Preserve the preflight JSON and confirm every blocking check passed before launch.
- Confirm elapsed times derive from monotonic start and finish values.
- Confirm all attempts retain distinct evidence paths.
- Confirm no study result is accepted during supervision.
- Confirm self-check actually executes all six disposable containment probes;
  executable availability alone is not containment evidence.
