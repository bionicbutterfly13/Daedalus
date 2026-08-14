# Current Daedalus Interface

Verified by direct read-only inspection on 2026-08-08 at source commit
`3339a1187cf14f50f80cfb28696d03de716419fd`:

- `pyproject.toml` maps `EvoSci` to `EvoScientist.cli:main`.
- `EvoSci --help` exposes single-shot `--prompt`, isolated `--mode run`, run `--name`, `--workdir`, and `--output-format stream-json`.
- `stream-json` defaults to unattended auto-mode unless the caller explicitly passes `--no-auto-mode`; current source resolves this in `_resolve_stream_json_auto_mode()`.
- Running `EvoSci --help` does not execute a study.
- `EvoSci --resume` is conversation resume, not interrupt resume. Single-shot CLI source always builds `RunRequest(message=prompt, ...)`, where `prompt` is a new string.
- `GraphRunInput` accepts `str | Command`; `LocalGraphGateway` forwards both the exact message object and exact full thread ID to `stream_agent_events`.
- Daedalus's interactive path resumes tool approval with `Command(resume={"decisions": ...})` and `ask_user` with `Command(resume={"answers": ..., "status": "answered"})`.
- Native local stream events expose neither thread ID nor run ID. The supervisor injects and verifies the exact thread. Its `supervisor_run_id` is external evidence identity, not a native Daedalus run ID.

The inherited single-shot shape remains useful for interface diagnosis, but it
is not the supervised resume path:

```text
EvoSci --mode run --name ATTEMPT_NAME --prompt PACKET_PROMPT --workdir DATA_ONLY_WORKDIR --output-format stream-json --no-auto-mode
```

The canonical supervised start is:

```text
python3 skills/supervising-daedalus-mock-study-runs/scripts/drive_stream_json_resume.py start --repo-root /Volumes/Asylum/Daedalus --packet PACKET --authorization AUTHORIZATION --allowlist ALLOWLIST --preflight PREFLIGHT --runtime-config RUNTIME --prompt-file PROMPT --attempt-dir ATTEMPT --workdir ATTEMPT/workspace --launcher EVOSCI_PATH --attempt-id ATTEMPT_ID --timeout-seconds SECONDS --max-cycles COUNT
```

An approval resume requires the exact digest printed by the prior cycle:

```text
python3 skills/supervising-daedalus-mock-study-runs/scripts/drive_stream_json_resume.py decide --attempt-dir ATTEMPT --decision approve --request-digest SHA256 --operator OPERATOR_ID
```

Rejection uses `--decision reject` and stops without invoking the worker again.
An `ask_user` gate uses `--decision answer --answers-file ANSWERS_JSON`.

Before launch, run the read-only preflight from the repository root:

```text
python3 skills/supervising-daedalus-mock-study-runs/scripts/daedalus_preflight.py --repo-root /Volumes/Asylum/Daedalus --workdir DATA_ONLY_WORKDIR --launcher EvoSci --webui-source-dir FROZEN_WEBUI_SOURCE --pretty
```

The preflight resolves the exact interpreter from the installed launcher's shebang and uses that interpreter to print `EvoScientist.__file__`; do not substitute generic `python` for this identity check. Require JSON status `ready`, require the resolved path to match the intended source, and require the work directory to contain no `EvoScientist/` package. Preserve the preflight JSON and record the source commit separately.

The driver launches a hidden worker under the exact interpreter recorded by the
preflight. Before importing the inherited `EvoScientist` package, the worker
sets isolated HOME, XDG config, data, memory, skills, runs, media, workspace,
temporary, cache, and checkpoint paths. It constructs an explicit configuration with
`auto_mode=False`, `auto_approve=False`, `dangerous_mode=False`, empty shell
allowlist, disabled private memory and workers, disabled async subagents,
disabled scheduler, and disabled channels. It then uses `LocalGraphGateway`,
`RunRequest`, and `Command(resume=...)` without changing Daedalus core.

Production launch is currently blocked before that worker is created. Direct
source inspection shows that `create_cli_agent` appends
`HumanInTheLoopMiddleware` to the main agent only
(`EvoScientist/EvoScientist.py:1050-1062`). `_build_base_kwargs` still loads and
materializes synchronous subagents (`EvoScientist/EvoScientist.py:489-523`),
while `_inject_subagent_middleware` adds no human interrupt middleware
(`EvoScientist/EvoScientist.py:291-365`). Setting
`enable_async_subagents=False` only prevents the asynchronous swap and returns
the same subagents in-process (`EvoScientist/EvoScientist.py:385-414`); it does
not disable them. Because an in-process subagent can reach the backend's real
shell execution path (`EvoScientist/backends.py:1231-1249`) without the main
agent gate, the self-check reports adapter readiness but production status
`blocked` with `subagent_execute_human_gate_unresolved`. No authorization or
preflight packet may override this blocker.

Paid-provider production is independently blocked. The driver verifies that the
provider is allowlisted, activation is explicitly authorized, and
`maximum_cost_usd` is finite and positive, then returns
`provider_cost_enforcement_unavailable`. No current path measures accumulated
spend or guarantees a hard stop at the approved ceiling, so accepting the number
as sufficient authorization would be misleading. This blocker remains until a
deterministic meter and cutoff are implemented and adversarially tested.

On the current macOS host, the outer worker runs under `sandbox-exec` with
writes limited to the attempt directory. Protected user, volume, and host-temp
reads are denied except for the frozen interpreter, Daedalus source, supervisor,
and attempt paths required to run. Approved tool execution is restricted to a
frozen-hash `python3` script and resolves through a nested wrapper that denies
network access, limits writes to `workspace/`, and denies child process
execution. The driver fails closed when that containment facility is absent. A
timeout signals the complete isolated worker process group. Absolute
interpreters, inline Python, Python commands without a frozen script at argv
position 1, and subprocesses started by the script are rejected so they cannot
bypass the nested wrapper. No production model/provider path was run, so
compatibility of this boundary with an E3 run remains unverified.

Driver-created files use create-exclusive or append writes and linked SHA-256
records. Each attempt also freezes exact copies and digests of the supervisor
source and cycle-worker source. A production start rechecks the clean Git commit
against the frozen preflight before reaching the current subagent blocker.
Adapter manifests declare `execution_mode: deterministic_adapter` and
`evidence_ceiling: E2`; the acceptance validator rejects an E3 relabeling. These
controls detect retained-record corruption, but they are not a cryptographic
signature against an actor who can rewrite the whole local attempt. A future E3
run must retain an external same-snapshot hash anchor.

The self-check establishes its containment claims by executing six disposable
allow and deny probes under the same wrapper contract. Presence of
`sandbox-exec` alone is not counted as a pass. The deterministic fake-launcher
suite establishes E1/E2 harness evidence only.
It does not establish a safe production agent graph, E3 runtime acceptance,
provider readiness, scientific validity, or a completed real study. Resolve and
test the synchronous-subagent execution gate first, then re-run current
`EvoSci --help`, source inspection, preflight, and the full approval boundary
before any separately authorized runtime launch.
