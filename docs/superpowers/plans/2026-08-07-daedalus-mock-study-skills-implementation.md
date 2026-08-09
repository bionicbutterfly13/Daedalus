# Daedalus Mock Study Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use software-development:test-driven-development and executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and validate the canonical Archimedes mock-study skill system, then close the two approved Daedalus production blockers with a single-agent supervised lane and a durable hard cost ceiling, without executing a study or publishing anything.

**Architecture:** `skills/` remains the only canonical skill source. The approved core amendment adds an explicit `SupervisedRunPolicy` to the isolated worker path, removes delegation and hidden model callers only there, and reserves worst-case model cost durably before every provider call. The ordinary Daedalus path remains unchanged, while the existing stdlib-only supervisor and acceptance validator independently freeze and verify the new cost contract and ledger.

**Tech Stack:** Python 3.11+, LangChain agent middleware, DeepAgents harness profiles, exact `decimal.Decimal` accounting, JSON evidence records, pytest, and Ruff.

## Global Constraints

- Daedalus means the customized EvoScientist system; Archimedes is the Hermes governance envelope.
- The synthetic study is one vertical acceptance test, not proof that every Daedalus function works.
- Daedalus executes and authors its primary study report; Archimedes independently verifies and reports evidence.
- Preparing a public article is authorized; publication requires Dr. Mani's later explicit approval.
- Modify EvoScientist core only within the approved supervised construction and model-budget boundary.
- Do not execute a study, activate providers, publish, transfer artifacts, or access private memory.
- Preserve one canonical `skills/` package and use discovery links or pointers, never maintained copies.
- Do not commit because Dr. Mani has not authorized a commit.

Tasks 1-7 were completed and independently reviewed before the 2026-08-08 core
amendment. Their original checkboxes are preserved as historical planning text.
Tasks 8 onward are the active implementation sequence.

---

### Task 1: Conducting Skill

**Files:**
- Create: `skills/conducting-daedalus-mock-studies/SKILL.md`
- Create: `skills/conducting-daedalus-mock-studies/references/state-contract.md`
- Test: `skills/conducting-daedalus-mock-studies/tests/test_conducting_skill.py`

**Interfaces:**
- Consumes: stage completion evidence from the other four skills.
- Produces: exact state transitions from `intake` through study verdict and publication disposition.

- [ ] Write tests that require all state transitions, all four terminal study verdicts, evidence-backed transitions, and no claim of full Daedalus validation.
- [ ] Run the focused test and observe failure because the skill package is absent.
- [ ] Write the minimal SKILL.md and state reference.
- [ ] Run the focused test and observe a pass.

### Task 2: Preparation Skill

**Files:**
- Create: `skills/preparing-daedalus-mock-studies/SKILL.md`
- Create: `skills/preparing-daedalus-mock-studies/templates/study-packet.json`
- Create: `skills/preparing-daedalus-mock-studies/templates/authorization-record.json`
- Test: `skills/preparing-daedalus-mock-studies/tests/test_preparing_skill.py`

**Interfaces:**
- Consumes: synthetic question, stage inventory, real-interface identity, permissions, expected outputs, and publication intent.
- Produces: immutable `daedalus-mock-study-packet/v1` and `daedalus-mock-study-authorization/v1` records.

- [ ] Write tests for every frozen execution, evidence, privacy, retry, publication, and correction field.
- [ ] Run the focused test and observe failure because templates are absent.
- [ ] Write the skill and fail-closed templates with every provider, execution, transfer, and publication authorization false.
- [ ] Run the focused test and observe a pass.

### Task 3: Supervision Skill

**Files:**
- Create: `skills/supervising-daedalus-mock-study-runs/SKILL.md`
- Create: `skills/supervising-daedalus-mock-study-runs/references/current-daedalus-interface.md`
- Create: `skills/supervising-daedalus-mock-study-runs/templates/run-ledger.jsonl`
- Create: `skills/supervising-daedalus-mock-study-runs/templates/attempt-manifest.json`
- Test: `skills/supervising-daedalus-mock-study-runs/tests/test_supervising_skill.py`

**Interfaces:**
- Consumes: frozen packet and authorization record.
- Produces: unique-attempt native event, stderr, status, ledger, run ID, thread ID, and timing evidence.

- [ ] Write tests requiring the currently observed `EvoSci` single-shot interface, data-only workdir/import-path check, distinct attempt paths, monotonic timing fields, and silent-success stop.
- [ ] Run the focused test and observe failure because the package is absent.
- [ ] Write the skill, current-interface reference, and templates without invoking Daedalus.
- [ ] Run the focused test and observe a pass.

### Task 4: Independent Acceptance Skill and Validator

**Files:**
- Create: `skills/accepting-daedalus-mock-study-evidence/SKILL.md`
- Create: `skills/accepting-daedalus-mock-study-evidence/scripts/validate_mock_study.py`
- Create: `skills/accepting-daedalus-mock-study-evidence/templates/evidence-manifest.json`
- Create: `skills/accepting-daedalus-mock-study-evidence/templates/archimedes-independent-evidence-report.json`
- Create: `skills/accepting-daedalus-mock-study-evidence/tests/fixtures/valid-study/*`
- Create: `skills/accepting-daedalus-mock-study-evidence/tests/test_accepting_skill.py`
- Test: `skills/accepting-daedalus-mock-study-evidence/tests/test_validator.py`

**Interfaces:**
- Consumes: run directory with packet, authorization, ledger, expected/produced artifact manifest, and Daedalus primary report.
- Produces: deterministic JSON validation result and one of `accepted`, `partial`, `failed`, or `stopped` without upgrading the observed verdict.

- [ ] Write the valid-fixture and first corruption test before the validator exists; observe failure.
- [ ] Implement the smallest validator slice for schema, file presence, non-emptiness, size, checksum, and run/thread linkage; observe pass.
- [ ] Add RED-GREEN slices for silent success, missing evidence, privacy leakage, unauthorized actions, retry overwrite, and partial-as-complete.
- [ ] Add the Archimedes report template and tests requiring direct verification, gaps, timing, concerns, and exact verdict.
- [ ] Run the complete acceptance test directory and observe all corruption cases fail closed.

### Task 5: Publication Skill

**Files:**
- Create: `skills/publishing-daedalus-study-journals/SKILL.md`
- Create: `skills/publishing-daedalus-study-journals/references/publication-gate.md`
- Create: `skills/publishing-daedalus-study-journals/templates/public-journal-article.json`
- Test: `skills/publishing-daedalus-study-journals/tests/test_publishing_skill.py`
- Extend: `skills/accepting-daedalus-mock-study-evidence/scripts/validate_mock_study.py`
- Extend: `skills/accepting-daedalus-mock-study-evidence/tests/test_validator.py`

**Interfaces:**
- Consumes: terminal evidence verdict and public-safe evidence links or content hashes.
- Produces: `publication_prepared`, then `awaiting_dr_mani_approval`, followed only by `published`, `publication_declined`, or `publication_blocked`.

- [ ] Write tests for article completeness, claim classification, forbidden content, accurate outcome, hashes for non-public evidence, and explicit post-review approval.
- [ ] Run focused tests and observe failure because the skill and article checks are absent.
- [ ] Write the skill, gate reference, article template, and validator slice.
- [ ] Run focused tests and observe a pass.

### Task 6: Canonical Discovery and Package Verification

**Files:**
- Create: `skills/README.md`
- Create: `.agents/skills/{conducting-daedalus-mock-studies,preparing-daedalus-mock-studies,supervising-daedalus-mock-study-runs,accepting-daedalus-mock-study-evidence,publishing-daedalus-study-journals}` filesystem links to the five canonical packages.
- Create: `.claude/skills/{conducting-daedalus-mock-studies,preparing-daedalus-mock-studies,supervising-daedalus-mock-study-runs,accepting-daedalus-mock-study-evidence,publishing-daedalus-study-journals}` filesystem links where the existing ignored Claude integration permits local discovery.
- Test: `skills/tests/test_daedalus_mock_study_skill_pack.py`

**Interfaces:**
- Consumes: five canonical skill directories.
- Produces: one canonical path per skill plus verified Codex and Claude link resolution; Hermes project context points to `skills/` without a copied source tree.

- [ ] Write a package test for names, frontmatter, descriptions, linked files, no duplicate maintained copies, and discovery link targets; observe failure.
- [ ] Add the README and links only after the failing test.
- [ ] Run all skill tests, Ruff on Python files, a secret/private-path scan, and `git diff --check`.

### Task 7: Independent Verification

**Files:**
- Review only: all files under `skills/` and discovery links.

**Interfaces:**
- Consumes: complete uncommitted implementation and fresh test output.
- Produces: independent spec-compliance and code-quality verdicts.

- [ ] Dispatch a fresh reviewer with the approved design, exact changed-file inventory, test output, and diff.
- [ ] Verify every reviewer claim directly against current files.
- [ ] Fix only confirmed findings and rerun focused plus complete verification.
- [ ] Report observed test counts, failures, lint status, discovery status, and unverified runtime gaps without executing the mock study.

---

## Phase 2: Supervised Production Readiness

### File and Responsibility Map

- Create `EvoScientist/supervision.py`: immutable supervised-policy and cost
  contracts, exact-money conversion, provider cost-adapter registry,
  process-scoped DeepAgents profile registration, and durable cost-ledger
  primitives.
- Create `EvoScientist/middleware/supervised_budget.py`: request-boundary and
  write-ahead budget middleware. It owns no provider pricing and accepts only a
  validated `SupervisedRunPolicy`.
- Modify `EvoScientist/middleware/__init__.py`: export the two supervised
  middleware classes without changing existing exports.
- Modify `EvoScientist/EvoScientist.py`: add an explicit supervised construction
  branch with no memory backend route and no middleware that calls a model or a
  remote token counter outside the budget adapter. The existing branch remains
  the ordinary path.
- Modify `EvoScientist/__init__.py`: lazily export the public supervised policy
  types used by the isolated worker.
- Create `tests/test_supervision_contract.py`: exact accounting, ledger,
  contract, and adapter tests.
- Create `tests/fixtures/supervised_cost_contract_cases.json`: one canonical
  parser-parity corpus consumed by core and stdlib-driver tests.
- Create `tests/test_supervised_budget_middleware.py`: model-request,
  usage-settlement, and forbidden-tool tests.
- Create `tests/test_supervised_agent.py`: graph-construction and ordinary-path
  non-regression tests.
- Modify
  `skills/supervising-daedalus-mock-study-runs/scripts/drive_stream_json_resume.py`:
  validate and freeze the cost contract, construct the supervised agent, carry
  the cost ledger across resume workers, and report conditional production
  readiness.
- Modify
  `skills/supervising-daedalus-mock-study-runs/scripts/daedalus_preflight.py`:
  require the new structural self-check without selecting a provider.
- Modify
  `skills/supervising-daedalus-mock-study-runs/templates/supervisor-runtime.json`:
  declare the v2 runtime and explicit unratified cost-contract slot.
- Modify
  `skills/supervising-daedalus-mock-study-runs/tests/test_daedalus_resume_driver.py`
  and `test_daedalus_preflight.py`: red-first driver and preflight coverage.
- Modify
  `skills/accepting-daedalus-mock-study-evidence/scripts/validate_mock_study.py`
  and its tests: independently validate production cost records and prevent E2
  evidence from being relabeled E3.
- Modify the supervision skill reference, capability matrix, and approved design
  only after behavior and tests are green.

### Task 8: Exact Cost Contract and Crash-Safe Ledger

**Files:**

- Create: `EvoScientist/supervision.py`
- Create: `tests/test_supervision_contract.py`
- Create: `tests/fixtures/supervised_cost_contract_cases.json`

**Interfaces:**

- `SupervisedCostContract.from_mapping()` accepts only the frozen v1 contract.
- `SupervisedRunPolicy` binds one attempt, cycle, model object, adapter, and
  ledger directory.
- `CostLedger.reserve()` writes before a model call.
- `CostLedger.settle()` releases unused reservation only after valid usage.
- `CostLedger.summary()` charges unresolved reservations at their full amount.

- [ ] **Step 1: Write exact-decimal and schema tests**

Add this complete base fixture and first assertions to
`tests/test_supervision_contract.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

import pytest

from EvoScientist.supervision import (
    CostLedger,
    SupervisedBudgetExceeded,
    SupervisedContractError,
    SupervisedCostContract,
)


def valid_contract() -> dict[str, object]:
    return {
        "schema": "daedalus-supervisor-cost-contract/v1",
        "contract_id": "cost-contract-001",
        "packet_id": "synthetic-driver-001",
        "provider": "anthropic",
        "model": "claude-test-exact",
        "currency": "USD",
        "maximum_cost_usd": "0.000400",
        "input_usd_per_million_tokens": "2.0",
        "output_usd_per_million_tokens": "10.0",
        "maximum_output_tokens_per_call": 20,
        "maximum_model_calls": 2,
        "token_counter_adapter": "fixture-exact-text-tools-v1",
        "supported_request_shapes": ["text_messages", "tool_schemas"],
        "counter_billing": "local_nonbillable",
        "counter_evidence_sha256": "a" * 64,
        "pricing_source": {
            "uri": "https://example.invalid/frozen-pricing",
            "captured_at": "2026-08-08T00:00:00Z",
            "content_sha256": "b" * 64,
            "approved_by": "Dr. Mani",
            "approval_evidence": "approval-record-001",
        },
        "fail_closed_policy": "write_ahead_full_reservation_v1",
    }


def test_contract_converts_to_exact_microdollars() -> None:
    contract = SupervisedCostContract.from_mapping(valid_contract())
    assert contract.maximum_micro_usd == 400
    assert contract.reservation_micro_usd(input_tokens=100) == 400


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("maximum_cost_usd", 0.0004),
        ("maximum_cost_usd", "NaN"),
        ("input_usd_per_million_tokens", "-1"),
        ("maximum_output_tokens_per_call", 0),
        ("maximum_model_calls", True),
        ("counter_billing", "unknown"),
    ],
)
def test_contract_rejects_non_exact_or_unsafe_values(field: str, value: object) -> None:
    raw = valid_contract()
    raw[field] = value
    with pytest.raises(SupervisedContractError):
        SupervisedCostContract.from_mapping(raw)
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_supervision_contract.py -q
```

Expected: collection fails because `EvoScientist.supervision` does not exist.

- [ ] **Step 3: Implement immutable contract parsing and exact pricing**

Create `EvoScientist/supervision.py` with these public types and formulas:

```python
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_CEILING
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Protocol

MICRO_USD_PER_USD = Decimal("1000000")
_ALLOWED_COUNTER_BILLING = {"local_nonbillable", "provider_documented_nonbillable"}


class SupervisedContractError(ValueError):
    """The supervised contract or durable ledger is invalid."""


class SupervisedBudgetExceeded(RuntimeError):
    """A model call would exceed the frozen call or money ceiling."""


class SupervisedAdapterUnsupportedError(SupervisedContractError):
    """No audited adapter can bound the requested provider path."""


class SupervisedUsageError(RuntimeError):
    """A supervised request or provider usage record is unsafe."""


def _decimal_string(value: object, field: str, *, positive: bool = False) -> Decimal:
    if not isinstance(value, str) or not value.strip():
        raise SupervisedContractError(f"{field} must be a decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise SupervisedContractError(f"{field} is not a finite decimal") from exc
    if not parsed.is_finite() or parsed < 0 or (positive and parsed <= 0):
        raise SupervisedContractError(f"{field} is outside its allowed range")
    return parsed


def _usd_to_micro_usd(value: Decimal) -> int:
    scaled = value * MICRO_USD_PER_USD
    if scaled != scaled.to_integral_value():
        raise SupervisedContractError("USD values support at most six decimal places")
    return int(scaled)


def _token_cost_micro_usd(tokens: int, usd_per_million: Decimal) -> int:
    if isinstance(tokens, bool) or not isinstance(tokens, int) or tokens < 0:
        raise SupervisedContractError("token counts must be nonnegative integers")
    return int((Decimal(tokens) * usd_per_million).to_integral_value(rounding=ROUND_CEILING))


@dataclass(frozen=True, slots=True)
class SupervisedCostContract:
    schema: str
    contract_id: str
    packet_id: str
    provider: str
    model: str
    currency: str
    maximum_cost_usd: Decimal
    input_usd_per_million_tokens: Decimal
    output_usd_per_million_tokens: Decimal
    maximum_output_tokens_per_call: int
    maximum_model_calls: int
    token_counter_adapter: str
    supported_request_shapes: tuple[str, ...]
    counter_billing: str
    counter_evidence_sha256: str
    pricing_source: Mapping[str, str]
    fail_closed_policy: str
    contract_sha256: str

    @property
    def maximum_micro_usd(self) -> int:
        return _usd_to_micro_usd(self.maximum_cost_usd)

    def reservation_micro_usd(self, *, input_tokens: int) -> int:
        return _token_cost_micro_usd(
            input_tokens, self.input_usd_per_million_tokens
        ) + _token_cost_micro_usd(
            self.maximum_output_tokens_per_call,
            self.output_usd_per_million_tokens,
        )

    def usage_micro_usd(self, *, input_tokens: int, output_tokens: int) -> int:
        return _token_cost_micro_usd(
            input_tokens, self.input_usd_per_million_tokens
        ) + _token_cost_micro_usd(output_tokens, self.output_usd_per_million_tokens)

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "SupervisedCostContract":
        # Validate the exact key set, scalar types, SHA-256 fields, pricing source,
        # supported shapes, policy version, and cross-field invariants before
        # constructing the frozen object. Reject booleans where integers are required.
        return _parse_cost_contract_v1(raw)


class ProviderCostAdapter(Protocol):
    adapter_id: str

    def validate_model(self, model: Any, contract: SupervisedCostContract) -> None:
        raise NotImplementedError

    def count_input_tokens(self, request: Any) -> int:
        raise NotImplementedError

    def extract_usage(self, response: Any) -> tuple[int, int]:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class SupervisedRunPolicy:
    attempt_id: str
    cycle_id: str
    ledger_dir: Path
    contract: SupervisedCostContract
    model: Any
    adapter: ProviderCostAdapter
```

Implement `_parse_cost_contract_v1()` in the same file with an exact required-key
set. It must reject unknown keys, verify `currency == "USD"`, verify both SHA-256
strings with `[0-9a-f]{64}`, require the canonical ordered request-shape list
`["text_messages", "tool_schemas"]`, require
`fail_closed_policy == "write_ahead_full_reservation_v1"`, and instantiate the
dataclass using `_decimal_string()`. Deep-copy the validated JSON-compatible
mapping before hashing it with UTF-8 JSON serialized using
`sort_keys=True, separators=(",", ":"), ensure_ascii=False`; store that digest as
`contract_sha256`. Require the pricing-source object to have exactly `uri`,
`captured_at`, `content_sha256`, `approved_by`, and `approval_evidence`. The
contract's maximum must be positive, integer limits must be positive non-booleans,
and the full output-only reservation must fit within the attempt ceiling. Store the
validated pricing-source copy behind `MappingProxyType` so the frozen contract does
not retain a mutable caller-owned dictionary.

Add `build_supervised_run_policy()` in the same file. It selects an adapter by the
exact `token_counter_adapter`, requires `adapter.adapter_id` to match, calls
`adapter.validate_model(model, contract)`, and stores that exact model object in
the frozen policy. The deterministic fixture adapter is injectable only by tests.
The first real adapter accepts only native `langchain_anthropic.ChatAnthropic`, an
exact `model.model == contract.model`, `max_tokens` equal to the contract,
`max_retries == 0`, no thinking configuration, and the approved direct Anthropic
endpoint. It also requires
`counter_billing == "provider_documented_nonbillable"` and the frozen counter
evidence digest. Any custom base URL, compatibility route, proxy, unsupported
provider, or model mismatch raises a typed unsupported-adapter error before a
request.

- [ ] **Step 4: Add ledger boundary and crash tests**

Append tests that reserve exactly 400 microdollars, reject the next reservation,
and prove an unsettled reservation remains fully charged after reopening the
ledger. Add table cases at one microdollar below, exactly at, and one microdollar
above the remaining ceiling; a call-count exhaustion case; duplicate settlement;
settlement without reservation; and output above the cap:

```python
def test_write_ahead_reservation_is_exact_and_fail_closed(tmp_path: Path) -> None:
    contract = SupervisedCostContract.from_mapping(valid_contract())
    ledger = CostLedger(tmp_path / "cost-ledger", "attempt-001", contract)
    reservation = ledger.reserve(cycle_id="cycle-001", input_tokens=100)
    assert reservation["reserved_micro_usd"] == 400
    assert ledger.summary()["committed_micro_usd"] == 400
    with pytest.raises(SupervisedBudgetExceeded):
        ledger.reserve(cycle_id="cycle-001", input_tokens=1)

    reopened = CostLedger(tmp_path / "cost-ledger", "attempt-001", contract)
    assert reopened.summary()["committed_micro_usd"] == 400
    assert reopened.summary()["unresolved_reservations"] == 1


def test_settlement_releases_only_durable_unused_reservation(tmp_path: Path) -> None:
    contract = SupervisedCostContract.from_mapping(valid_contract())
    ledger = CostLedger(tmp_path / "cost-ledger", "attempt-001", contract)
    reservation = ledger.reserve(cycle_id="cycle-001", input_tokens=100)
    settlement = ledger.settle(
        reservation_id=reservation["reservation_id"],
        input_tokens=50,
        output_tokens=10,
    )
    assert settlement["settled_micro_usd"] == 200
    assert settlement["released_micro_usd"] == 200
    assert ledger.summary()["committed_micro_usd"] == 200


def test_corrupt_or_cross_attempt_records_fail_closed(tmp_path: Path) -> None:
    contract = SupervisedCostContract.from_mapping(valid_contract())
    ledger = CostLedger(tmp_path / "cost-ledger", "attempt-001", contract)
    ledger.reserve(cycle_id="cycle-001", input_tokens=100)
    record = next((tmp_path / "cost-ledger").glob("*.json"))
    payload = json.loads(record.read_text(encoding="utf-8"))
    payload["attempt_id"] = "attempt-002"
    record.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(SupervisedContractError):
        ledger.summary()
```

- [ ] **Step 5: Implement create-exclusive hash-linked ledger records**

Implement `CostLedger` with these exact public methods:

```python
class CostLedger:
    def __init__(
        self,
        root: Path,
        attempt_id: str,
        contract: SupervisedCostContract,
    ) -> None:
        self.root = root.resolve()
        self.attempt_id = attempt_id
        self.contract = contract

    def reserve(self, *, cycle_id: str, input_tokens: int) -> dict[str, Any]:
        records = self._validated_records()
        summary = self._summarize(records)
        if summary["reservation_count"] >= self.contract.maximum_model_calls:
            raise SupervisedBudgetExceeded("maximum_model_calls reached")
        amount = self.contract.reservation_micro_usd(input_tokens=input_tokens)
        if summary["committed_micro_usd"] + amount > self.contract.maximum_micro_usd:
            raise SupervisedBudgetExceeded("maximum_cost_usd would be exceeded")
        return self._append_record(
            records,
            record_type="reservation",
            cycle_id=cycle_id,
            reservation_id=self._new_reservation_id(records),
            input_token_upper_bound=input_tokens,
            output_token_limit=self.contract.maximum_output_tokens_per_call,
            reserved_micro_usd=amount,
        )

    def settle(
        self,
        *,
        reservation_id: str,
        input_tokens: int,
        output_tokens: int,
    ) -> dict[str, Any]:
        records = self._validated_records()
        reservation = self._unsettled_reservation(records, reservation_id)
        actual = self.contract.usage_micro_usd(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        if input_tokens > reservation["input_token_upper_bound"]:
            raise SupervisedUsageError("provider input usage exceeded the approved bound")
        if output_tokens > reservation["output_token_limit"]:
            raise SupervisedUsageError("provider output usage exceeded the approved limit")
        if actual > reservation["reserved_micro_usd"]:
            raise SupervisedUsageError("provider usage exceeded the durable reservation")
        return self._append_record(
            records,
            record_type="settlement",
            cycle_id=reservation["cycle_id"],
            reservation_id=reservation_id,
            settled_micro_usd=actual,
            released_micro_usd=reservation["reserved_micro_usd"] - actual,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    def summary(self) -> dict[str, Any]:
        return self._summarize(self._validated_records())
```

Each record is one `000001-reservation-<id>.json` or
`000002-settlement-<id>.json` file created with `os.O_CREAT | os.O_EXCL`, mode
`0o600`, followed by `os.fsync()` on the file and directory. `_validated_records`
must enforce contiguous sequence, prior-record SHA-256, record SHA-256, contract
digest, attempt identity, one settlement per reservation, and no settlement
without a reservation. `_summarize` uses settled cost for settled reservations
and full reserved cost for unresolved reservations. It must reject an unexpected
filename or non-record entry rather than silently skipping it.

Use one exact record envelope for core and independent validators:

```json
{
  "schema": "daedalus-supervisor-cost-ledger-entry/v1",
  "sequence": 1,
  "record_type": "reservation",
  "recorded_at": "2026-08-08T00:00:00Z",
  "attempt_id": "attempt-001",
  "cycle_id": "cycle-001",
  "model_call_id": "model-call-uuid",
  "contract_sha256": "<sha256>",
  "previous_record_sha256": null,
  "payload": {},
  "record_sha256": "<sha256-of-envelope-without-record_sha256>"
}
```

Reservation payloads contain the input upper bound, output limit, and reserved
microdollars. Settlement payloads contain provider input/output usage, settled
microdollars, and released microdollars. Task 11 adds `retained-reservation` and
`terminal-budget` records with the same envelope. `_append_record()` derives the
next sequence from fully validated records, builds canonical JSON, computes the
hash without `record_sha256`, creates the final filename exclusively, writes all
bytes, fsyncs the file, closes it, and fsyncs the directory. A collision is a
fail-closed concurrency error. `_new_reservation_id()` uses `uuid.uuid4()`;
`_unsettled_reservation()` rejects unknown or already settled IDs; `_summarize()`
reconstructs reservations and settlements rather than trusting stored totals.

- [ ] **Step 6: Run contract tests GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_supervision_contract.py -q
.venv/bin/ruff check EvoScientist/supervision.py tests/test_supervision_contract.py
```

Expected: both commands exit 0.

### Task 9: Supervised Request Boundary and Budget Middleware

**Files:**

- Create: `EvoScientist/middleware/supervised_budget.py`
- Modify: `EvoScientist/middleware/__init__.py`
- Create: `tests/test_supervised_budget_middleware.py`

- [ ] **Step 1: Write model-call reservation and settlement tests**

Create a local fake counter and a real `ModelRequest`:

```python
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from langchain.agents.middleware.types import ModelRequest, ModelResponse
from langchain_core.messages import AIMessage, HumanMessage

from EvoScientist.middleware.supervised_budget import (
    APPROVED_SUPERVISED_TOOLS,
    SupervisedBoundaryMiddleware,
    SupervisedBudgetMiddleware,
)
from EvoScientist.supervision import (
    CostLedger,
    SupervisedCostContract,
    SupervisedRunPolicy,
    SupervisedUsageError,
)
from tests.test_supervision_contract import valid_contract


class FixedAdapter:
    adapter_id = "fixture-exact-text-tools-v1"

    def validate_model(self, model: MagicMock, contract: SupervisedCostContract) -> None:
        assert model.max_tokens == contract.maximum_output_tokens_per_call
        assert model.max_retries == 0

    def count_input_tokens(self, request: ModelRequest) -> int:
        assert request.system_message is None
        assert len(request.messages) == 1
        return 100

    def extract_usage(self, response: ModelResponse) -> tuple[int, int]:
        message = response.result[0]
        if not isinstance(message, AIMessage) or message.usage_metadata is None:
            raise SupervisedUsageError("provider usage metadata is required")
        usage = message.usage_metadata
        input_tokens = usage["input_tokens"]
        output_tokens = usage["output_tokens"]
        if usage["total_tokens"] != input_tokens + output_tokens:
            raise SupervisedUsageError("provider usage metadata is inconsistent")
        return input_tokens, output_tokens


def policy(tmp_path: Path) -> SupervisedRunPolicy:
    model = MagicMock()
    model.max_tokens = 20
    model.max_retries = 0
    return SupervisedRunPolicy(
        attempt_id="attempt-001",
        cycle_id="cycle-001",
        ledger_dir=tmp_path / "cost-ledger",
        contract=SupervisedCostContract.from_mapping(valid_contract()),
        model=model,
        adapter=FixedAdapter(),
    )


def request(
    run_policy: SupervisedRunPolicy,
    *,
    model: MagicMock | None = None,
) -> ModelRequest:
    tools = []
    for name in sorted(APPROVED_SUPERVISED_TOOLS):
        tool = MagicMock()
        tool.name = name
        tools.append(tool)
    return ModelRequest(
        model=run_policy.model if model is None else model,
        messages=[HumanMessage(content="synthetic prompt")],
        tools=tools,
        model_settings={},
    )


def test_budget_middleware_reserves_before_handler_and_settles_afterward(
    tmp_path: Path,
) -> None:
    run_policy = policy(tmp_path)
    middleware = SupervisedBudgetMiddleware(run_policy)

    def handler(model_request: ModelRequest) -> ModelResponse:
        summary = CostLedger(
            run_policy.ledger_dir,
            run_policy.attempt_id,
            run_policy.contract,
        ).summary()
        assert summary["committed_micro_usd"] == 400
        return ModelResponse(
            result=[
                AIMessage(
                    content="bounded response",
                    usage_metadata={
                        "input_tokens": 50,
                        "output_tokens": 10,
                        "total_tokens": 60,
                    },
                )
            ]
        )

    middleware.wrap_model_call(request(run_policy), handler)
    assert CostLedger(
        run_policy.ledger_dir,
        run_policy.attempt_id,
        run_policy.contract,
    ).summary()["committed_micro_usd"] == 200
```

- [ ] **Step 2: Add missing-usage, model-drift, and forbidden-tool tests**

```python
def test_missing_usage_retains_full_reservation(tmp_path: Path) -> None:
    run_policy = policy(tmp_path)
    middleware = SupervisedBudgetMiddleware(run_policy)
    with pytest.raises(SupervisedUsageError):
        middleware.wrap_model_call(
            request(run_policy),
            lambda _request: ModelResponse(result=[AIMessage(content="no usage")]),
        )
    assert CostLedger(
        run_policy.ledger_dir,
        run_policy.attempt_id,
        run_policy.contract,
    ).summary()["committed_micro_usd"] == 400


def test_model_identity_drift_fails_before_reservation(tmp_path: Path) -> None:
    run_policy = policy(tmp_path)
    changed = request(run_policy, model=MagicMock())
    with pytest.raises(SupervisedUsageError):
        SupervisedBudgetMiddleware(run_policy).wrap_model_call(
            changed,
            lambda _request: ModelResponse(result=[]),
        )
    assert not run_policy.ledger_dir.exists()


@pytest.mark.parametrize("tool_name", ["task", "start_async_task", "unknown_tool"])
def test_boundary_rejects_every_unapproved_tool_call(tool_name: str) -> None:
    tool_request = MagicMock()
    tool_request.tool_call = {"name": tool_name, "args": {}, "id": "call-1"}
    with pytest.raises(SupervisedUsageError):
        SupervisedBoundaryMiddleware().wrap_tool_call(
            tool_request,
            lambda _request: MagicMock(),
        )
```

- [ ] **Step 3: Run middleware tests RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_supervised_budget_middleware.py -q
```

Expected: collection fails because the middleware module does not exist.

- [ ] **Step 4: Implement synchronous and asynchronous middleware paths**

Create `EvoScientist/middleware/supervised_budget.py` with:

```python
from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from langchain.agents.middleware.types import (
    AgentMiddleware,
    ModelRequest,
    ModelResponse,
)
from langchain_core.messages import AIMessage

from EvoScientist.supervision import (
    CostLedger,
    SupervisedRunPolicy,
    SupervisedUsageError,
)

APPROVED_SUPERVISED_TOOLS = frozenset(
    {
        "think_tool",
        "write_todos",
        "ls",
        "read_file",
        "write_file",
        "edit_file",
        "glob",
        "grep",
        "execute",
    }
)


def _tool_name(tool: Any) -> str | None:
    if isinstance(tool, dict):
        value = tool.get("name")
    else:
        value = getattr(tool, "name", None)
    return value if isinstance(value, str) else None


class SupervisedBoundaryMiddleware(AgentMiddleware):
    name = "supervised_boundary"

    def _check_model_request(self, request: ModelRequest) -> None:
        names = [_tool_name(tool) for tool in request.tools]
        if None in names or len(names) != len(set(names)):
            raise SupervisedUsageError("supervised tool names are missing or duplicated")
        visible = set(names)
        if visible != APPROVED_SUPERVISED_TOOLS:
            raise SupervisedUsageError(
                "supervised tool surface changed: "
                f"missing={sorted(APPROVED_SUPERVISED_TOOLS - visible)}, "
                f"unexpected={sorted(visible - APPROVED_SUPERVISED_TOOLS)}"
            )

    def _check_model_response(self, response: ModelResponse) -> None:
        for item in response.result:
            if not isinstance(item, AIMessage):
                continue
            unexpected = sorted(
                call["name"]
                for call in item.tool_calls
                if call.get("name") not in APPROVED_SUPERVISED_TOOLS
            )
            if unexpected:
                raise SupervisedUsageError(
                    f"model emitted unapproved supervised tool calls: {unexpected}"
                )

    def wrap_model_call(self, request: ModelRequest, handler: Callable):
        self._check_model_request(request)
        response = handler(request)
        self._check_model_response(response)
        return response

    async def awrap_model_call(self, request: ModelRequest, handler: Callable):
        self._check_model_request(request)
        response = await handler(request)
        self._check_model_response(response)
        return response

    def wrap_tool_call(self, request: Any, handler: Callable):
        name = request.tool_call.get("name")
        if name not in APPROVED_SUPERVISED_TOOLS:
            raise SupervisedUsageError(f"unapproved supervised tool call: {name}")
        return handler(request)

    async def awrap_tool_call(self, request: Any, handler: Callable):
        name = request.tool_call.get("name")
        if name not in APPROVED_SUPERVISED_TOOLS:
            raise SupervisedUsageError(f"unapproved supervised tool call: {name}")
        return await handler(request)


class SupervisedBudgetMiddleware(AgentMiddleware):
    name = "supervised_budget"

    def __init__(self, policy: SupervisedRunPolicy) -> None:
        self.policy = policy

    def _ledger(self) -> CostLedger:
        return CostLedger(
            self.policy.ledger_dir,
            self.policy.attempt_id,
            self.policy.contract,
        )

    def _validate_model(self, request: ModelRequest) -> None:
        if request.model is not self.policy.model:
            raise SupervisedUsageError("supervised model object changed")
        if request.model_settings or request.response_format is not None:
            raise SupervisedUsageError("runtime model overrides are forbidden")
        self.policy.adapter.validate_model(request.model, self.policy.contract)

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        self._validate_model(request)
        input_bound = self.policy.adapter.count_input_tokens(request)
        ledger = self._ledger()
        reservation = ledger.reserve(
            cycle_id=self.policy.cycle_id,
            input_tokens=input_bound,
        )
        response = handler(request)
        input_tokens, output_tokens = self.policy.adapter.extract_usage(response)
        ledger.settle(
            reservation_id=reservation["reservation_id"],
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        return response

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Any],
    ) -> ModelResponse:
        self._validate_model(request)
        async_counter = getattr(self.policy.adapter, "acount_input_tokens", None)
        if callable(async_counter):
            input_bound = await async_counter(request)
        else:
            input_bound = await asyncio.to_thread(
                self.policy.adapter.count_input_tokens,
                request,
            )
        ledger = self._ledger()
        reservation = ledger.reserve(
            cycle_id=self.policy.cycle_id,
            input_tokens=input_bound,
        )
        response = await handler(request)
        input_tokens, output_tokens = self.policy.adapter.extract_usage(response)
        ledger.settle(
            reservation_id=reservation["reservation_id"],
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        return response
```

The adapter must validate one `AIMessage`, complete provider usage metadata,
integer nonnegative totals, and `total_tokens == input_tokens + output_tokens`.
The Anthropic adapter also pins the installed LangChain behavior that folds base,
cache-read, and cache-creation tokens into `usage_metadata.input_tokens`; any new
or contradictory category fails closed. Do not catch provider exceptions, because
the unresolved reservation must remain charged. Add async parity tests, handler
exception tests, runtime `model_settings` override tests, missing/duplicate visible
tool tests, and a test proving the adapter sees the final system message and exact
tool schemas presented to the model.

- [ ] **Step 5: Export middleware and run GREEN**

Add both classes to `EvoScientist/middleware/__init__.py` and `__all__`, then run:

```bash
.venv/bin/python -m pytest tests/test_supervision_contract.py tests/test_supervised_budget_middleware.py -q
.venv/bin/ruff check EvoScientist/supervision.py EvoScientist/middleware/supervised_budget.py tests/test_supervision_contract.py tests/test_supervised_budget_middleware.py
```

Expected: both commands exit 0.

### Task 10: Single-Agent Supervised Graph Construction

**Files:**

- Modify: `EvoScientist/supervision.py`
- Modify: `EvoScientist/EvoScientist.py:489-527,663-852,938-1077`
- Modify: `EvoScientist/__init__.py:12-41`
- Create: `tests/test_supervised_agent.py`

- [ ] **Step 1: Write construction tests before changing the factory**

The tests must patch `deepagents.create_deep_agent` and assert the exact
supervised arguments:

```python
def test_supervised_factory_omits_delegation_mcp_and_hidden_middleware(
    tmp_path, safe_config, fake_supervised_model, supervised_policy, monkeypatch
):
    create = MagicMock()
    create.return_value.with_config.return_value = MagicMock()
    monkeypatch.setattr("deepagents.create_deep_agent", create)

    create_cli_agent(
        workspace_dir=str(tmp_path),
        config=safe_config,
        chat_model=fake_supervised_model,
        supervised_policy=supervised_policy,
    )

    kwargs = create.call_args.kwargs
    assert kwargs["subagents"] == []
    assert [tool.name for tool in kwargs["tools"]] == ["think_tool"]
    assert set(kwargs["backend"].routes) == {"/skills/"}
    names = {type(item).__name__ for item in kwargs["middleware"]}
    assert "SupervisedBoundaryMiddleware" in names
    assert "SupervisedBudgetMiddleware" in names
    assert "HumanInTheLoopMiddleware" in names
    assert names.isdisjoint(
        {
            "ErrorNormalizationMiddleware",
            "ContextOverflowMapperMiddleware",
            "RuntimeContextMiddleware",
            "ConfigurableModelMiddleware",
            "ModelFallbackMiddleware",
            "_ConditionalToolSelectorMiddleware",
            "EvoMemoryMiddleware",
            "EvoMemoryLifecycleMiddleware",
            "SchedulerMiddleware",
            "BackgroundExecutionMiddleware",
            "CodeInterpreterMiddleware",
            "SteerMiddleware",
            "AskUserMiddleware",
        }
    )
```

Add separate tests that:

- reject a policy unless both `config` and `chat_model` are explicit;
- reject `auto_approve`, `auto_mode`, `dangerous_mode`, memory, scheduler, or
  async-subagent settings in the effective config;
- patch `MemoryFilesystemBackend` to raise and prove supervised construction never
  reads or constructs the `/memories/` route;
- patch user/global skill-path access to raise and prove the supervised `/skills/`
  route contains only the read-only built-in Daedalus skill directory;
- inspect the supervised `CustomSandboxBackend` and prove tool subprocesses use
  `inherit_env=False` plus a fixed non-secret environment allowlist that excludes
  every provider credential named by the driver;
- prove the ordinary branch still calls `load_mcp_and_build_kwargs` and retains
  configured subagents when `supervised_policy=None`;
- invoke a fresh normal subprocess before and after a separate profile-registering
  subprocess and compare the serialized ordinary kwargs;
- inspect the resolved DeepAgents profile and require
  `general_purpose_subagent.enabled is False` plus
  `"SummarizationMiddleware"` in `excluded_middleware`;
- run one compiled fake-model turn and assert the final model-visible tools are
  exactly `APPROVED_SUPERVISED_TOOLS`, with no `task` or hidden tool;
- make a fake model emit `execute`, assert the graph produces a real LangGraph
  interrupt before the backend runs, then resume the approved action through the
  existing driver payload contract;
- make an actual fake model emit a `task` tool call and require a typed failure
  without any subagent invocation.

- [ ] **Step 2: Run the focused tests RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_supervised_agent.py -q
```

Expected: tests fail because `create_cli_agent` has no `supervised_policy`
argument and no supervised profile helper.

- [ ] **Step 3: Register the restrictive profile only in the dedicated process**

Add to `EvoScientist/supervision.py`:

```python
def register_supervised_harness_profile(model: Any) -> str:
    from deepagents import (
        GeneralPurposeSubagentProfile,
        HarnessProfile,
        register_harness_profile,
    )
    from deepagents._models import get_model_identifier, get_model_provider
    from deepagents.profiles.harness.harness_profiles import (
        _harness_profile_for_model,
    )

    provider = get_model_provider(model)
    identifier = get_model_identifier(model)
    if not provider or not identifier or ":" in identifier:
        raise SupervisedContractError(
            "DeepAgents could not derive one exact supervised profile key"
        )
    key = f"{provider}:{identifier}"
    register_harness_profile(
        key,
        HarnessProfile(
            excluded_middleware=frozenset({"SummarizationMiddleware"}),
            general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False),
        ),
    )
    resolved = _harness_profile_for_model(model, None)
    gp = resolved.general_purpose_subagent
    if (
        gp is None
        or gp.enabled is not False
        or "SummarizationMiddleware" not in resolved.excluded_middleware
    ):
        raise SupervisedContractError("supervised DeepAgents profile did not resolve")
    return key
```

The use of the pinned DeepAgents private identity resolver must remain isolated in
this helper and pinned by a direct test. A future dependency change must fail this
test before the production driver is considered ready.

- [ ] **Step 4: Add a separate supervised middleware and kwargs builder**

In `EvoScientist/EvoScientist.py`, add `_get_supervised_middleware()` rather than
adding conditionals throughout `_get_default_middleware()`. Its exact stack is:

```python
[
    ToolHistoryRepairMiddleware(),
    SupervisedBoundaryMiddleware(),
    ToolErrorHandlerMiddleware(),
    SupervisedBudgetMiddleware(policy),
    HumanInTheLoopMiddleware(interrupt_on={"execute": True}),
]
```

Add `_build_supervised_kwargs()` returning only:

```python
{
    "name": "EvoScientist-supervised",
    "model": chat_model,
    "tools": [think_tool],
    "backend": backend,
    "subagents": [],
    "middleware": middleware,
    "system_prompt": _configured_system_prompt(cfg),
    "skills": list(DEFAULT_SKILL_SOURCES),
}
```

It must not call `_load_mcp_tools_cached`, `load_subagents`,
`_ensure_general_purpose_subagent`, `_inject_subagent_middleware`, or
`_maybe_swap_async_subagents`. It also must not construct
`MemoryFilesystemBackend`, add a `/memories/` route, or call
`create_context_editing_middleware`: the installed context-editing middleware can
invoke `get_num_tokens_from_messages()` before the budget middleware, which would
create an ungoverned remote counter path for Anthropic. The supervised backend is
a `CompositeBackend` whose default is the attempt `CustomSandboxBackend` and whose
only route is `/skills/` to `ReadOnlyFilesystemBackend(root_dir=SKILLS_DIR,
virtual_mode=True)`. It must not read `_paths.USER_SKILLS_DIR` or
`_paths.GLOBAL_SKILLS_DIR`.

Construct the attempt backend with `inherit_env=False`. Pass only `PATH`, `HOME`,
`TMPDIR`, `TMP`, `TEMP`, `LANG`, `LC_ALL`, `SSL_CERT_FILE`, and `SSL_CERT_DIR` when
present in the already sanitized worker environment, plus
`PYTHONDONTWRITEBYTECODE=1` and `PYTHONUNBUFFERED=1`. Never pass an API key, token,
provider base URL, or the full worker environment into a model-controlled tool
subprocess. Preserve the driver's action-wrapper prefix in `PATH` so nested Python
execution remains sandboxed.

Do not include `ErrorNormalizationMiddleware`: it wraps every exception under a
recognized provider model, including the new budget and boundary exceptions, and
would erase their typed fail-closed identity. Do not include
`ContextOverflowMapperMiddleware` because summarization is deliberately absent and
an overflow must stop with its reservation retained. The isolated driver owns
stderr redaction and terminal classification for raw provider failures.
Do not include `RuntimeContextMiddleware`: it injects the worker's live date and
timezone, which violates the study packet's frozen-input and same-snapshot rules.
Any temporal context required by the mock study must be explicit in the frozen
packet content.

- [ ] **Step 5: Add the opt-in factory parameter without altering default flow**

Extend only the keyword-only portion of `create_cli_agent`:

```python
def create_cli_agent(
    workspace_dir: str | None = None,
    checkpointer=None,
    config=None,
    chat_model=None,
    *,
    on_mcp_progress=None,
    events: "MiddlewareEventSink | None" = None,
    supervised_policy: "SupervisedRunPolicy | None" = None,
) -> "CompiledStateGraph":
```

When the policy is present, require the explicit pure path, require
`policy.model is chat_model`, reject `on_mcp_progress`, verify the safe config,
register the process-wide profile, construct the workspace-plus-built-in-skills backend,
lean middleware, and kwargs, and compile. Take this branch before reading the
memory directory or constructing any ordinary-path backend. When absent, execute
the existing lines 985-1077 without semantic change.
Lazily export `SupervisedCostContract` and `SupervisedRunPolicy` from
`EvoScientist/__init__.py`.

- [ ] **Step 6: Run focused graph and existing factory regressions GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_supervised_agent.py tests/test_model_command.py tests/test_async_subagent_factory.py tests/test_async_subagent_swap.py tests/test_tool_selector_middleware.py -q
.venv/bin/ruff check EvoScientist/EvoScientist.py EvoScientist/__init__.py tests/test_supervised_agent.py
```

Expected: both commands exit 0, and no provider or service starts.

### Task 11: Wire the Policy Through the Isolated Resume Driver

**Files:**

- Modify:
  `skills/supervising-daedalus-mock-study-runs/scripts/drive_stream_json_resume.py`
- Modify:
  `skills/supervising-daedalus-mock-study-runs/templates/supervisor-runtime.json`
- Modify:
  `skills/supervising-daedalus-mock-study-runs/tests/test_daedalus_resume_driver.py`

- [ ] **Step 1: Replace the permanent-blocker test with contract validation tests**

Keep the existing contradictory-boundary cases. Replace
`test_production_authorization_fails_closed_without_cost_enforcement` with four
tests:

1. Missing `cost_contract` returns `provider_cost_contract_missing`.
2. Packet, runtime, provider, model, or maximum-cost mismatch returns
   `provider_cost_contract_mismatch`.
3. Unsupported adapter returns `provider_cost_adapter_unsupported`.
4. A matching structurally supported contract returns normally without launching
   a model.

Use `valid_contract()` from Task 8, change its packet ID to the driver fixture,
and keep `paid_provider_activation_authorized=True`,
`paid_providers_authorized=True`, and a packet ceiling of `0.0004` only inside
these local validation tests.

- [ ] **Step 2: Add runtime v2 and exact-contract validation**

Define:

```python
RUNTIME_SCHEMA_V1 = "daedalus-supervisor-runtime/v1"
RUNTIME_SCHEMA_V2 = "daedalus-supervisor-runtime/v2"
COST_CONTRACT_SCHEMA = "daedalus-supervisor-cost-contract/v1"
```

Adapter mode may retain runtime v1 with no cost contract. Production requires v2.
The parent supervisor must remain stdlib-only. Add an independent
`_parse_cost_contract_v1()` there using `decimal.Decimal`, the same exact key and
type rules, and canonical digest rules, without importing `EvoScientist`.
`_validate_runtime_config()` cross-checks packet ID, provider, exact model, and
rejects all runtime model/fallback/auxiliary overrides. `_validate_authorization`
compares exact microdollars rather than floats and stops raising the two obsolete
permanent blocker codes only after the matching contract passes. A shared corpus
of valid and invalid JSON fixtures must be parameterized through both the core and
stdlib parsers to detect schema drift while preserving independent implementations.

Update `supervisor-runtime.json` to v2 with:

```json
{
  "schema": "daedalus-supervisor-runtime/v2",
  "packet_id": "synthetic-vertical-acceptance-001",
  "provider": "REQUIRES_SEPARATE_RATIFICATION",
  "model": "REQUIRES_SEPARATE_RATIFICATION",
  "credential_env_names": [],
  "config_overrides": {},
  "cost_contract": "REQUIRES_SEPARATE_RATIFICATION"
}
```

The string sentinel must fail production validation. It is an explicit human gate,
not a usable default.

- [ ] **Step 3: Remove the unconditional subagent blocker only after source check**

In `_freeze_inputs()`, preserve `_verify_current_source_snapshot()` for production,
then validate runtime, authorization, and allowlist. Remove the unconditional
`PRODUCTION_BLOCKER_CODE` raise. Add a manifest field:

```python
"supervised_policy": {
    "delegation": "disabled",
    "mcp": "disabled",
    "hidden_model_callers": "disabled",
    "cost_contract_sha256": _json_digest(runtime["cost_contract"]),
}
```

- [ ] **Step 4: Construct a zero-retry, output-capped model in the worker**

Replace the worker model line with:

```python
contract = SupervisedCostContract.from_mapping(runtime["cost_contract"])
chat_model = get_chat_model(
    config.model,
    provider=config.provider,
    max_retries=0,
    max_tokens=contract.maximum_output_tokens_per_call,
    thinking=None,
)
policy = build_supervised_run_policy(
    attempt_id=str(request["attempt_id"]),
    cycle_id=str(request["cycle_id"]),
    ledger_dir=Path(str(request["cost_ledger_dir"])),
    contract=contract,
    model=chat_model,
)
```

Pass `supervised_policy=policy` to `create_cli_agent`. The adapter factory supports
the deterministic fixture counter in tests and the audited Anthropic text-plus-tool
counter only. Every other provider remains structurally blocked. The Anthropic
adapter must reject non-`ChatAnthropic` models, non-text message blocks, unsupported
tools, thinking/reasoning configuration, custom endpoints, proxy routes, or absent
nonbillable-counter evidence before calling the counter. It counts the final system
message, all historical messages, and the exact approved tool schemas. Tests may
construct the model with dummy credentials but must never invoke it or the remote
counter.

- [ ] **Step 5: Persist cost evidence across fresh resume workers**

Add `self.cost_ledger_dir = self.evidence_dir / "cost-ledger"`. Include its exact
path and the frozen contract digest in every cycle request. After each worker exits,
validate the ledger independently with stdlib-only driver code and add these fields
to the worker result and terminal status:

```json
{
  "cost_contract_sha256": "<sha256>",
  "cost_ledger_tail_sha256": "<sha256-or-null>",
  "cost_micro_usd_committed": 0,
  "cost_micro_usd_remaining": 400,
  "model_call_reservations": 0,
  "unresolved_cost_reservations": 0
}
```

The outer validator must reject missing sequence numbers, broken hashes,
cross-attempt records, duplicate settlements, or a summary that disagrees with
the worker result. Never infer cost from stream `usage_stats`.

The parent owns two control records using the same create-exclusive, canonical,
fsynced envelope. If a worker exits with a reservation that did not receive a
settlement, append one `retained-reservation` record per unresolved model-call ID;
its payload records the worker exit class and preserves the full charge. When the
attempt reaches a terminal state, append exactly one `terminal-budget` record whose
payload contains the recomputed committed and remaining microdollars, reservation
count, unresolved count, and terminal status. A completed attempt with any
unresolved reservation is invalid. Once a terminal record exists, both core and
parent writers reject every later reservation, settlement, retention, or second
terminal record.

- [ ] **Step 6: Update self-check semantics**

When all deterministic containment and structural probes pass, return:

```json
{
  "status": "conditionally_ready",
  "adapter_status": "mechanism_ready_provider_unselected",
  "production_status": "ready_for_provider_specific_preflight",
  "blocking_reasons": [],
  "human_gate": {
    "main_agent_execute_interrupts": true,
    "supervised_subagents_disabled": true,
    "all_supervised_executable_actions_human_gated": true
  },
  "cost_enforcement": {
    "write_ahead_reservation": true,
    "crash_retains_full_reservation": true,
    "provider_adapter_required": true,
    "provider_activated": false
  }
}
```

Containment failures still produce `status="blocked"`. This self-check proves only
the mechanism and must not report a provider, model, study, or E3 run as ready.

- [ ] **Step 7: Run driver tests GREEN without provider activation**

Run:

```bash
.venv/bin/python -m pytest skills/supervising-daedalus-mock-study-runs/tests/test_daedalus_resume_driver.py -q
.venv/bin/ruff check skills/supervising-daedalus-mock-study-runs/scripts/drive_stream_json_resume.py skills/supervising-daedalus-mock-study-runs/tests/test_daedalus_resume_driver.py
```

Expected: both commands exit 0. Test output must show only deterministic adapter
and mocked/fake model execution.

### Task 12: Independent Preflight and Evidence Validation

**Files:**

- Modify:
  `skills/supervising-daedalus-mock-study-runs/scripts/daedalus_preflight.py`
- Modify:
  `skills/supervising-daedalus-mock-study-runs/tests/test_daedalus_preflight.py`
- Modify:
  `skills/accepting-daedalus-mock-study-evidence/scripts/validate_mock_study.py`
- Modify:
  `skills/accepting-daedalus-mock-study-evidence/tests/test_validator.py`
- Modify relevant acceptance fixtures under
  `skills/accepting-daedalus-mock-study-evidence/tests/fixtures/`

- [ ] **Step 1: Update preflight RED tests**

Require `check_resume_driver()` to pass only when the report has
`production_status == "ready_for_provider_specific_preflight"`, both structural
human-gate booleans true, all three cost-enforcement booleans true, provider
activation false, and no blocking reasons. A report that merely changes its status
string while retaining a subagent or missing reservation enforcement must fail.

- [ ] **Step 2: Implement the stricter preflight check and run GREEN**

Run:

```bash
.venv/bin/python -m pytest skills/supervising-daedalus-mock-study-runs/tests/test_daedalus_preflight.py -q
```

Expected: exit 0 with no launcher, model, or provider invocation beyond the
existing deterministic self-check subprocess.

- [ ] **Step 3: Add independent cost-ledger corruption tests**

Extend the production-layout validator tests with distinct expected errors for:

```text
cost_contract_missing
cost_contract_digest_mismatch
cost_ledger_missing
cost_ledger_sequence_invalid
cost_ledger_hash_invalid
cost_ledger_attempt_mismatch
cost_ledger_duplicate_settlement
cost_ledger_settlement_without_reservation
cost_ledger_retention_missing
cost_ledger_terminal_duplicate
cost_ledger_record_after_terminal
cost_ledger_summary_mismatch
cost_ceiling_exceeded
unresolved_cost_reservation_at_completion
provider_adapter_evidence_missing
```

The valid E1/E2 fixture remains valid without a paid-provider contract. A synthetic
production fixture may reach structural validation in tests, but it must be marked
`mock_backed` and cannot be accepted as E3 runtime evidence.

- [ ] **Step 4: Validate cost records independently of core code**

The stdlib-only acceptance validator must parse decimal strings itself, verify the
contract digest from the frozen runtime, reconstruct the cost chain, recompute each
reservation and settlement with round-up semantics, charge unresolved reservations
fully, and compare the terminal summary. It must not import
`EvoScientist.supervision`, trust worker summaries, or use `usage_stats` as the
accounting authority.

- [ ] **Step 5: Run acceptance tests GREEN**

Run:

```bash
.venv/bin/python -m pytest skills/accepting-daedalus-mock-study-evidence/tests -q
.venv/bin/ruff check skills/accepting-daedalus-mock-study-evidence/scripts/validate_mock_study.py skills/accepting-daedalus-mock-study-evidence/tests
```

Expected: both commands exit 0 and every named corruption has its own failing
reason.

### Task 13: Documentation, Same-Snapshot Verification, and Independent Review

**Files:**

- Modify: `skills/supervising-daedalus-mock-study-runs/SKILL.md`
- Modify:
  `skills/supervising-daedalus-mock-study-runs/references/current-daedalus-interface.md`
- Modify:
  `docs/superpowers/specs/2026-08-08-daedalus-capability-acceptance-matrix.md`
- Modify:
  `docs/superpowers/specs/2026-08-07-daedalus-mock-study-skills-design.md`
- Modify this plan only to mark completed phase-two steps and record observed
  commands.

- [ ] **Step 1: Run the complete focused production-readiness set**

```bash
.venv/bin/python -m pytest \
  tests/test_supervision_contract.py \
  tests/test_supervised_budget_middleware.py \
  tests/test_supervised_agent.py \
  skills/supervising-daedalus-mock-study-runs/tests \
  skills/accepting-daedalus-mock-study-evidence/tests \
  -q
```

Expected: exit 0. Preserve the complete command, test count, duration, and final
exit code.

- [ ] **Step 2: Run adjacent core regressions**

```bash
.venv/bin/python -m pytest \
  tests/test_model_command.py \
  tests/test_async_subagent_factory.py \
  tests/test_async_subagent_swap.py \
  tests/test_tool_selector_middleware.py \
  tests/test_model_fallback.py \
  tests/test_stream_events.py \
  tests/test_graph_gateway.py \
  -q
```

Expected: exit 0 with no model or service activation.

- [ ] **Step 3: Run full static and repository verification**

```bash
.venv/bin/ruff check EvoScientist tests skills
.venv/bin/python -m pytest --collect-only -q
.venv/bin/python -m pytest -q
git diff --check
```

Expected: every command exits 0. Record existing warnings separately and do not
attribute pre-existing failures to this work.

- [ ] **Step 4: Update claims only from observed results**

Change the matrix and skill reference from permanent implementation blockers to:

- supervised single-agent mechanism implemented and deterministically tested;
- hard-ceiling mechanism implemented and deterministically tested;
- provider-specific production support limited to adapters whose counter,
  output-limit, retry, usage, pricing, and nonbillable-counting evidence pass;
- no provider/model/study E3 execution performed;
- live selected-provider compatibility remains unknown until separately approved.

Do not state that Daedalus is production-ready in general.

- [ ] **Step 5: Dispatch independent adversarial review**

Give the reviewer the approved design, this plan, exact changed-file inventory,
focused and full-suite output, and these required falsification targets:

1. Find any reachable synchronous or asynchronous subagent path.
2. Find any model call outside the budget middleware.
3. Find any way to settle or reclaim an unresolved reservation.
4. Find any float, retry, model override, MCP, code-interpreter, background, or
   summarization bypass.
5. Find any E1/E2 evidence that can be relabeled E3.
6. Prove the ordinary Daedalus path changes, or report that no such proof exists.

The reviewer must return file-and-line findings, not a general approval.

- [ ] **Step 6: Verify findings and rerun affected checks**

Confirm each finding directly against the same working-tree snapshot. Add a
failing regression test before any fix, implement only confirmed fixes, rerun the
focused set, Ruff, and full suite, then obtain a final independent PASS or retain
the blocker explicitly.

- [ ] **Step 7: Stop before every external gate**

Do not activate a provider, run a model, execute a study, approve a tool action,
accept study evidence, transfer artifacts, publish, commit, push, or open a pull
request. Report the exact next authorization required for a provider-specific E3
preflight.
