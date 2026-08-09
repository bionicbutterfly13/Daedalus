# Daedalus Mock Study Skills Design

Date: 2026-08-07, amended 2026-08-08
Status: Approved by Dr. Mani for implementation on 2026-08-08
Canonical project: `/Volumes/Asylum/Daedalus`

## Purpose

Create a narrow provisional acceptance-harness skill set for Archimedes to manage one complete synthetic mock study through Daedalus, the customized EvoScientist system.

The mock study uses synthetic research content while exercising Daedalus through its real interfaces. Broken Daedalus functions are reported as failures. Archimedes does not replace them with simulations, manual substitutes, or manufactured outputs.

Archimedes is the Hermes profile and governance envelope managing Daedalus. This synthetic mock study is the first vertical acceptance test across the bounded study workflow. Its result does not prove that every Daedalus function works.

## Role Contract

- Daedalus performs the study.
- Archimedes supervises execution and independently evaluates the evidence.
- Archimedes prepares public-safe publication material only after evidence acceptance and publishes only after Dr. Mani approves the final article.
- Archimedes does not certify its own substitutions.
- Daedalus runtime output is primary execution evidence only when accessed directly and tied to the identified run.
- Archimedes reports what was executed, verified, not verified, blocked, or stopped.

## Scope

The skills cover:

1. Study intake and scope confirmation.
2. Authorization and boundary checks.
3. Starting the Daedalus study through a verified real interface.
4. Monitoring every declared workflow stage.
5. Capturing outputs, failures, retries, and timing.
6. Verifying that declared outputs were actually produced.
7. Stopping on silent success, missing evidence, privacy violations, unauthorized actions, or substitutions.
8. Producing an independent final evidence report for Dr. Mani.
9. Preparing a public-safe journal article after evidence acceptance.
10. Holding publication behind Dr. Mani's explicit review and approval.

The workflow produces three distinct deliverables:

1. A Daedalus primary study report authored by Daedalus.
2. An Archimedes independent evidence report authored by Archimedes.
3. A public journal article prepared by Archimedes and published only after Dr. Mani's explicit approval.

## Non-Goals

This design and its approved production-readiness amendment do not:

- modify EvoScientist core outside the explicit supervised-agent construction,
  model-budget enforcement, and harness-integration changes defined below;
- execute the mock study;
- activate paid providers;
- publish or send outputs without Dr. Mani's explicit approval after review of the final article;
- use private memory or private research data;
- define the final Archimedes skill architecture;
- certify Daedalus merely because repository tests or service health checks pass;
- claim that one vertical mock study validates every Daedalus function.

## Canonical Layout

The repository owns one canonical package under `skills/`:

```text
skills/
├── conducting-daedalus-mock-studies/
│   ├── SKILL.md
│   └── references/
├── preparing-daedalus-mock-studies/
│   ├── SKILL.md
│   ├── templates/
│   └── tests/
├── supervising-daedalus-mock-study-runs/
│   ├── SKILL.md
│   ├── references/
│   ├── templates/
│   └── tests/
├── accepting-daedalus-mock-study-evidence/
│   ├── SKILL.md
│   ├── scripts/
│   ├── templates/
│   └── tests/
└── publishing-daedalus-study-journals/
    ├── SKILL.md
    ├── references/
    ├── templates/
    └── tests/
```

Hermes, Claude, and Codex registrations must point to this package. They must not become separately maintained source copies.

The complete provisional architecture is:

1. `conducting-daedalus-mock-studies`
2. `preparing-daedalus-mock-studies`
3. `supervising-daedalus-mock-study-runs`
4. `accepting-daedalus-mock-study-evidence`
5. `publishing-daedalus-study-journals`

## Skill Boundaries

### `conducting-daedalus-mock-studies`

This is the complete walkthrough controller. It defines the stage state machine, handoff contracts, stop rules, and completion criteria. It does not repeat the detailed procedures in the four stage skills.

States:

```text
intake -> prepared -> launched -> monitoring -> evidence_ready
evidence_ready -> accepted | partial | failed | stopped
accepted | partial | failed | stopped -> publication_prepared
publication_prepared -> awaiting_dr_mani_approval
awaiting_dr_mani_approval
  -> published | publication_declined | publication_blocked
```

No transition occurs from agent narration alone. Each transition requires the preceding stage's identified artifact or directly observed runtime evidence.

Any terminal study result, including `accepted`, `partial`, `failed`, or `stopped`, may proceed to `publication_prepared` when the article reports the real outcome accurately. Preparation does not authorize publication. Only Dr. Mani's approval of the final article permits the transition from `awaiting_dr_mani_approval` to `published`.

### `preparing-daedalus-mock-studies`

This skill owns intake and authorization. It freezes:

- synthetic study question and content;
- expected Daedalus workflow stages;
- real interface and source identity;
- permitted writes and runtime resources;
- forbidden data, providers, transfer, publication, and private-memory access;
- expected artifacts and acceptance criteria;
- retry ceiling, timeout policy, and kill criteria;
- intended public-journal destination;
- article title and authorship;
- public versus private artifact inventory;
- redaction and privacy rules;
- evidence-linking requirements;
- publication approval status;
- publication rollback or correction procedure.

Its output is an immutable study packet plus an authorization record. The packet must be complete before Daedalus starts.

### `supervising-daedalus-mock-study-runs`

This skill owns launch and monitoring. It verifies the current Daedalus interface from source and live command help before use. It captures:

- launch command or API request without secrets;
- exact workspace and imported package path;
- source revision and configuration identity where available;
- native event stream, stderr, exit status, exact thread ID, and explicitly
  labeled run-identity authority;
- supervisor-cycle start and finish times using monotonic timing;
- outputs declared at each stage;
- failures and separately identified retries.

Every attempt receives distinct evidence paths. A retry cannot overwrite the first attempt. A process ID, listener, empty event file, or polished final message is not proof that the study ran.

The supervised headless route is the project-local
`drive_stream_json_resume.py`, not direct `EvoSci --resume`. Direct CLI resume
sends a new text prompt. The supervisor uses Daedalus's exported
`LocalGraphGateway`, exact full thread ID, persistent isolated checkpoint, and
`Command(resume=...)`. It stops at every interrupt, requires a separate
exact-digest operator decision, and preserves each cycle in append-only
evidence. The local native event protocol exposes no run ID, so the harness
records an Archimedes-owned `supervisor_run_id`, labels its authority, and keeps
`native_run_id` null. Native events retain their real `type` values. The
supervisor does not infer semantic scientific stages from event names or cycle
timing; Archimedes maps workflow-stage evidence separately during acceptance.

This route is production-blocked in the current source. `create_cli_agent`
places `HumanInTheLoopMiddleware` on the main agent only
(`EvoScientist/EvoScientist.py:1050-1062`), but `_build_base_kwargs` still loads
synchronous subagents (`EvoScientist/EvoScientist.py:489-523`) and
`_inject_subagent_middleware` gives them no execution interrupt
(`EvoScientist/EvoScientist.py:291-365`). Disabling asynchronous subagents only
keeps those agents in-process (`EvoScientist/EvoScientist.py:385-414`). The
driver therefore allows deterministic adapter cycles for E1/E2 evaluation but
raises `subagent_execute_human_gate_unresolved` before every production start.

#### Approved supervised production lane

The approved repair adds an explicit supervised policy to agent construction. It
is opt-in, has no configuration-file or environment-only activation path, and
defaults off. Ordinary interactive, deployed, notebook, and channel agents retain
their existing middleware and delegation behavior.

The production supervisor activates the policy only inside its fresh isolated
cycle-worker process. In that process:

- the supervised branch bypasses `load_mcp_and_build_kwargs`, loads no MCP
  servers or MCP tools, and constructs base arguments without synchronous or
  asynchronous subagent specifications;
- the active DeepAgents harness profile disables the auto-created
  `general-purpose` subagent, which removes the `task` tool rather than merely
  hiding it in a prompt;
- DeepAgents summarization and Daedalus tool selection, model fallback,
  configurable-model replacement, memory workers, scheduler, background-agent,
  and code-interpreter paths are absent because they can create an unmetered
  model or executable-action path;
- the compile-time model is the only model permitted for the attempt;
- `execute` remains available only on the main agent and remains subject to the
  existing resumable `HumanInTheLoopMiddleware` interrupt;
- construction fails if `task`, a subagent launcher, an unapproved executable
  tool, or an unmetered model-calling middleware remains reachable.

DeepAgents harness profiles are process-wide registrations that persist for the
life of the Python process; they are not scoped to one agent. The supervisor may
therefore use the supported profile mechanism only in its dedicated worker, which
exits after one cycle. It must not register the restrictive profile in a normal
long-lived Daedalus process. Subprocess-level tests must prove that an ordinary
Daedalus process remains unchanged before and after a separate supervised worker
process runs.

This is intentionally a single-agent supervised lane. Preserving delegation would
require a separate nested-interrupt protocol that serializes subagent actions and
resumes them independently. That larger design is deferred because the current
parallel-interrupt path is known to be unsafe for this acceptance harness.

The current implementation uses macOS `sandbox-exec` to confine the worker to
the attempt and an independently sandboxed action wrapper to deny tool network,
protected-root reads, writes outside `workspace/`, and undeclared child process
execution. It fails closed when the host facility is absent. The boundary is
covered by deterministic E1/E2 tests; timeouts terminate the complete worker
process group. Its compatibility with a real E3 provider/runtime path is still
unknown.

The driver uses create-exclusive records, append writes, SHA-256-linked state
and ledger entries, frozen supervisor and cycle-worker source copies, and a
fresh clean-Git identity check for production. Adapter manifests are explicitly
limited to E2 and the acceptance validator rejects E3 relabeling. These are
write-once and tamper-evident under the driver's authority, not signed proof
against an actor who can rewrite the whole local attempt. E3 acceptance
therefore requires an independently retained same-snapshot hash anchor.

#### Approved hard cost ceiling

Every paid production runtime must include a frozen cost contract linked to the
study packet, authorization record, runtime configuration, selected provider, and
exact model. The contract contains:

- a schema and stable contract ID;
- the packet ID, provider, exact model identifier, and currency (`USD`);
- `maximum_cost_usd`, equal to the packet boundary;
- conservative input and output prices expressed as decimal-string USD per one
  million tokens, including the highest applicable cache or reasoning rate;
- a positive maximum output-token count per model call;
- the approved token-counting adapter and the request shapes it supports;
- evidence that token counting is local or provider-documented as nonbillable;
- pricing source identity, capture time, content digest, human approver, and
  approval evidence;
- a maximum model-call count and fail-closed policy version.

Floating-point arithmetic is not used for authorization or accounting. Monetary
values are parsed as exact decimals and converted to integer microdollars using a
documented round-up rule. The runtime contract and packet ceiling must agree
exactly after that conversion.

Before each model call, a budget middleware must:

1. Confirm that the request still uses the frozen provider and model.
2. Reject unsupported media, tool schemas, message blocks, model overrides, or a
   token counter that cannot bound every billable input category.
3. Obtain a provider-adapter input-token upper bound, include the complete system
   message and tool definitions, and reserve the upper-bound input cost plus the
   full permitted output cost.
4. Append and durably sync a create-exclusive, hash-linked reservation before the
   provider call. No call starts when the reservation would exceed the remaining
   attempt ceiling or model-call limit.
5. Force the approved output-token limit and provider retry count of zero.
6. On success, require provider usage metadata, conservatively price every usage
   category, and append a settlement. Unused reservation may be released only
   after that settlement is durably recorded.

An unresolved reservation caused by cancellation, timeout, provider error, or
worker crash is charged at its full reserved amount on every later cycle. Missing
or contradictory usage metadata stops the attempt and does not release the
reservation. This makes a crash conservative rather than a route around the
ceiling.

The cost ledger lives inside the isolated attempt root, survives the fresh worker
process used for each resume cycle, and is separately linked into the run ledger
and final manifest. Display-only `usage_stats` events are evidence to compare
against the ledger, not the authority that enforces it.

A provider is production-supported only when its adapter demonstrates a complete
upper bound for the selected request shapes and model output limit. Unknown or
partially counted providers, and remote counting endpoints without evidence that
they are nonbillable, remain blocked with a specific unsupported-adapter reason.
Deterministic fake-model tests establish the mechanism, not real-provider pricing
or tokenization validity.

### `accepting-daedalus-mock-study-evidence`

This skill owns independent acceptance and reporting. It compares the frozen expected inventory with directly accessed Daedalus outputs. It verifies:

- artifact presence and non-emptiness;
- size and SHA-256 identity;
- schema and required fields;
- run, thread, stage, and source linkage;
- declared output counts against produced output counts;
- evidence coverage and missing stages;
- absence of forbidden private content or unauthorized action records;
- consistency between native events, terminal status, and final artifacts.

Its output is an operator-authored final evidence report. It must not be represented as Daedalus-authored work.

### `publishing-daedalus-study-journals`

This skill owns public-safe article preparation, approval gating, publication verification, and any later correction or rollback procedure. It remains separate because publication is an outward-facing human-gated action.

The skill may prepare a complete article after Archimedes finishes evidence acceptance for an `accepted`, `partial`, `failed`, or `stopped` study. It must preserve the real verdict, link every public factual claim to publishable direct evidence or a content hash, and apply the frozen privacy and redaction rules.

The skill must stop at `awaiting_dr_mani_approval` until Dr. Mani reviews and explicitly approves the final article. Approval to prepare the article is not approval to publish it. A declined article records `publication_declined`; an article that cannot meet evidence, privacy, destination, or correction requirements records `publication_blocked`.

## Data Contracts

### Study Packet

The canonical packet contains:

- packet schema and packet ID;
- synthetic-study declaration;
- objective and bounded research question;
- exact input inventory and content digests;
- Daedalus interface and source identity;
- workflow stage inventory;
- expected artifact inventory;
- permitted and prohibited operations;
- provider and cost boundary;
- retention, transfer, and publication policy;
- retry, timeout, and stop policy;
- acceptance criteria;
- intended public-journal destination;
- article title and authorship;
- public and private artifact inventories;
- redaction and privacy rules;
- evidence-linking requirements;
- publication approval status;
- publication rollback or correction procedure.

### Run Ledger

The append-only ledger records chronological entries classified as:

- observation;
- hypothesis;
- operator action;
- Daedalus event;
- failure;
- retry;
- verification.

Each entry includes a timestamp, attempt ID, stage, source, and evidence reference. Corrections append a new entry and do not rewrite history.

### Supervised Runtime and Cost Contract

The frozen supervisor runtime identifies the selected provider and model and
embeds the approved cost contract described above. It cannot select a second
model, auxiliary model, fallback chain, or runtime override. Its digest is part of
the attempt manifest and every cycle request.

### Cost Ledger

The append-only cost ledger records reservation, settlement,
retained-reservation, and terminal-budget entries. Each record contains the
attempt, cycle, and model-call IDs; prior-record hash; contract digest;
conservative input bound; output limit; reserved and settled microdollars;
provider usage fields; and evidence timestamps. A settlement references exactly
one reservation. Duplicate, out-of-order, rewritten, released-without-usage, or
cross-attempt records fail validation.

### Evidence Manifest

The manifest records every expected and observed artifact with path, role, producer, attempt ID, stage, byte size, checksum, and verification status. Missing artifacts remain explicit entries.

### Daedalus Primary Study Report

Daedalus produces the primary scientific report. It contains:

- research question and hypothesis;
- synthetic inputs and methods;
- workflow stages attempted and analyses performed;
- outputs produced and measured results;
- failures, retries, and limitations;
- unresolved scientific questions.

Archimedes verifies the report as an artifact but does not backfill, paraphrase into existence, or manufacture missing Daedalus content. A missing or incomplete primary report remains missing or incomplete evidence.

### Archimedes Independent Evidence Report

The report contains:

1. What actually executed and which artifacts were directly verified.
2. Expected versus produced outputs, checksums, and provenance.
3. Missing, empty, stale, or unlinked evidence.
4. Failures, retries, timing, stop conditions, and concerns about Daedalus behavior.
5. A `workflow_stage_evidence` map whose references resolve to retained native
   event fragments or Daedalus artifacts and whose evidence classes remain
   explicit.
6. Blockers and final verdict.

The verdict is one of `accepted`, `partial`, `failed`, or `stopped`. It includes the exact reason and does not convert a partial run into success.

### Public Journal Article

After evidence acceptance, Archimedes prepares a complete public-safe article containing:

- the research question, why it was selected, and the separate roles of Daedalus and Archimedes;
- study design, synthetic inputs, methods, and what actually ran;
- verified outputs, measured results, failures, retries, and missing evidence;
- what worked, what did not work, limitations, and concerns about Daedalus;
- repairs or evaluations needed and the next study or engineering decision.

Every material statement is classified as `verified execution`, `observed result`, `supported inference`, `hypothesis`, or `unknown`. Where direct evidence cannot be published, the article includes a public-safe description and content hash.

The public article excludes credentials, secrets, private memory, private research data, hidden prompts, unsafe internal paths, sensitive logs, unsupported claims, claims that one mock study fully validates Daedalus, and consciousness or phenomenal claims inferred from functional behavior.

## Stop and Failure Policy

The harness stops immediately when:

- Daedalus reports success without required outputs;
- required evidence is missing, empty, stale, or unlinked;
- private or non-synthetic content is accessed or emitted;
- a provider, cost, mutation, transfer, or publication action exceeds authorization;
- a supervised graph exposes a subagent, `task`, an unapproved executable tool,
  or an unmetered model-calling path;
- a cost contract, reservation, settlement, usage record, or provider adapter is
  missing, inconsistent, unsupported, or over budget;
- Archimedes would need to substitute for a broken Daedalus function;
- run identity cannot be tied to the observed outputs;
- a retry ceiling is reached.

Publication preparation or publication also stops when the article cannot preserve the independent evidence verdict, a material claim lacks evidence linkage, redaction cannot make the evidence public-safe, the destination is not frozen, or Dr. Mani has not explicitly approved the final article.

A stop preserves existing evidence and records the boundary. It does not delete, rewrite, or backfill the failed attempt.

## Real Interface Rule

The implementation must inspect current Daedalus source and live `--help` output before documenting a command, API, port, assistant identifier, event schema, or artifact path. Historical reports can guide discovery but cannot establish the current interface.

The operator must use a data-only work directory that cannot shadow the installed `EvoScientist` package. The imported package path is checked before launch. Service health, interface reachability, and study execution are separate acceptance layers.

## Verification Design

Each skill follows skill TDD independently and sequentially:

1. Run baseline agent scenarios without the new skill and record the failure.
2. Create the minimal skill that corrects the observed failure.
3. Run the same scenarios with the skill loaded.
4. Add a new pressure or corruption case and close any loophole.
5. Validate frontmatter, links, scripts, fixtures, and discovery before moving to the next skill.

The acceptance package includes deterministic validators and fixtures:

- one valid synthetic completed study;
- missing expected artifact;
- empty artifact with success narration;
- mismatched run or thread identity;
- corrupted checksum or schema;
- privacy-marker leak;
- unauthorized provider or external action;
- a structurally valid paid-provider request whose positive cost ceiling cannot
  be deterministically metered and enforced;
- a supervised construction that passes no subagents but silently receives the
  DeepAgents default `general-purpose` subagent;
- a fabricated `task` call or hidden subagent launcher that remains executable
  after supervised construction;
- a supervised lane containing tool-selector, summarization, fallback,
  configurable-model, memory-worker, scheduler, background-agent, or
  code-interpreter middleware;
- a separate normal Daedalus process whose subagents or middleware changed after
  a supervised worker subprocess ran;
- a model call whose write-ahead reservation is one microdollar below, exactly
  equal to, and one microdollar above the remaining ceiling;
- a second model call after the maximum call count, a provider-internal retry, or
  a runtime model override;
- missing, malformed, duplicated, cross-attempt, or contradictory usage metadata;
- a crash or timeout after reservation but before settlement, followed by a
  resume attempt that tries to reclaim the unresolved reservation;
- a token counter that ignores the system message, tool schemas, cache categories,
  reasoning/output categories, or an unsupported multimodal block;
- a changed pricing source, cost contract, packet ceiling, provider, model, or
  output-token limit after authorization;
- retry that overwrites prior evidence;
- partial stage coverage presented as complete;
- malformed or broken state and ledger hash chains;
- changed pending payloads, invalid answers that consume a decision slot, or a
  decision/resume payload mismatch;
- invented native run identity or unresolved semantic-stage references;
- an allowlisted script changed after authorization;
- an approved action that attempts network, protected-root access, or a write
  outside the workspace;
- an allowlisted command containing shell substitution or other nonliteral
  expansion syntax;
- a frozen script that tries to start an undeclared child executable;
- a changed supervisor or cycle-worker source snapshot, or adapter evidence
  relabeled as E3;
- a timeout that leaves a child process alive;
- a flat legacy fixture presented as supervised evidence, or legacy fixture
  evidence relabeled from `fixture_valid` to `accepted`;
- semantic-stage evidence that uses inference, the wrong report fragment, an
  unknown stage, or the same reference more than once;
- containment inferred from executable presence without executing the complete
  disposable allow and deny probe set;
- a public article that overstates a partial, failed, or stopped result;
- publication attempted without Dr. Mani's approval;
- a public claim lacking publishable evidence or a content hash;
- leakage of a forbidden public-article content class.

A valid fixture must pass. Every corruption fixture must fail closed with a specific reason. Repository tests and lint checks follow the focused package tests.

## Discovery and Registration

The project `skills/` directory is canonical. Project context points repository-working agents to it. Hermes registration uses a supported external directory or verified filesystem link. Claude and Codex exposure must resolve to the same canonical files. Fresh-session discovery is tested because loaders may cache skills at startup.

Registration is complete only when each intended agent can locate the five skill names and access their linked files. Filesystem presence alone is not discovery evidence.

## Acceptance Criteria

The implementation is complete when:

- all five skills exist in the canonical project package;
- names and descriptions trigger on the intended mock-study stages;
- stage boundaries preserve Daedalus execution versus Archimedes validation;
- publication remains separate and human-gated after article preparation;
- current real interfaces are documented from direct inspection;
- valid and corrupt fixtures exercise deterministic validators;
- every corruption case fails closed;
- baseline and post-skill agent scenarios show the intended behavior change;
- Hermes, Claude, and Codex can locate the canonical skills;
- the three deliverables remain distinct in authorship, evidence role, and acceptance status;
- the current executable supervisor declares macOS support only, proves its
  containment facility during adapter self-check, and blocks unsupported hosts;
- the production contract remains failed while any executable subagent action
  can bypass the human interrupt gate;
- paid-provider production remains failed until the approved cost ceiling is
  deterministically measured and enforced;
- the supervised lane proves that no subagent or `task` tool is reachable and
  that only main-agent `execute` can request executable work;
- every model call is preceded by a durable upper-bound reservation, no call can
  begin above the attempt ceiling, and unresolved reservations remain charged;
- hidden model callers, retries, and model replacement are absent from the
  supervised lane while a separate ordinary Daedalus process remains unchanged;
- production readiness is reported per provider adapter; an unknown provider or
  unsupported request shape remains blocked rather than inheriting a generic
  pass;
- accepted, partial, failed, and stopped outcomes can each produce an accurate public-safe article;
- no paid provider, published surface, private memory, or real study has been touched;
- the final diff contains only the approved supervised core boundary, cost
  enforcement, harness integration, tests, and design or plan documents, in
  addition to the already approved provisional skill package and discovery
  wiring.

## Deferred Work

Nested resumable delegation remains deferred. The approved implementation
disables delegation only in the supervised lane and does not redesign normal
Daedalus subagent behavior.

No real E3 execution is authorized by this amendment. After the supervised lane,
cost mechanism, adversarial tests, independent review, and production preflight
pass, another separately approved task may execute one complete synthetic study
through Daedalus. That run will require a fresh live readiness check, a frozen
study packet, a provider-specific approved cost adapter and pricing record,
explicit runtime authorization, and independent acceptance from produced
artifacts. It must establish that macOS containment, early credential scrubbing,
provider token counting, output limits, usage metadata, and zero-retry behavior
work on the selected real provider path. Deterministic fake-model tests do not
establish those E3 facts. Article preparation may follow the real terminal
result, but publication will still require Dr. Mani's explicit approval after
review of the final article.
