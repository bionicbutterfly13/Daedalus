# Contract: `stage2b_preflight`

Public surface of
`EvoScientist/skills/jspace-research-operations/scripts/stage2b_preflight.py`.

**Hard constraint**: this module MUST import cleanly with neither `torch`, `jlens`,
nor `scipy` installed. It is the only part of Stage 2b exercised by the repo's
pytest suite, and the machine running that suite has no GPU and no interpretability
stack. Every check therefore takes already-extracted metadata — shape tuples, dtype
*strings*, device *strings*, digests, floats — never a live tensor.

That constraint is what makes US3 testable at all: "the preflight can be exercised
against a deliberately broken configuration with no GPU and no measurement."

---

## Failure model

One exception type. Preflight fails closed and names the offending item.

```python
class PreflightError(Exception):
    """Raised when a preflight assertion fails. Carries a machine-readable code."""
    code: str      # stable slug, e.g. "orphaned_constant", "dtype_mismatch"
    detail: dict   # the offending values, for the artifact
```

Rules:

- **Never warn where a check could fail.** A warning is a check that does not run.
- **Never aggregate.** The first failure raises, naming exactly one cause. A
  preflight that reports "3 problems" invites triage; one that names the first
  invites a fix.
- Every `code` is stable and testable. Tests assert on `code`, not on message text.

---

## `check_tensor_contracts(observed: dict) -> None`

Asserts the R5 contract table. `observed` is a plain dict of strings and tuples
extracted at the call site in the notebook.

| Key | Type | Assertion |
|---|---|---|
| `residual_shape` | tuple[int, ...] | `== (d_model,)` |
| `residual_dtype` | str | `== "torch.float32"` — `transport` does not cast; a half-precision residual is a silently wrong matmul |
| `jacobian_shape` | tuple[int, int] | `== (d_model, d_model)` |
| `jacobian_dtype` | str | `== "torch.float32"` |
| `readout_device` | str | `== "cpu"` |
| `decode_parity_max_abs` | float | `<= DECODE_PARITY_TOL` |
| `logit_softcapping` | float \| None | recorded; `PreflightError` if not None, since it would change every rank statistic |

Codes: `shape_mismatch`, `dtype_mismatch`, `device_mismatch`, `decode_parity`,
`unexpected_softcapping`.

**Why dtype is a string**: comparing `torch.float32` requires importing torch.
`str(tensor.dtype)` is extracted at the call site, which has torch, and compared
here, which does not.

---

## `check_constant_registry(registry: dict, gates: dict) -> None`

The Principle IV mechanization. See
[constant-registry.md](./constant-registry.md) for the full rules.

Three checks, all required:

1. Every registry entry has ≥ 1 name in `consumed_by` → else
   `PreflightError("orphaned_constant")`.
2. Every constant name any gate reads appears in the registry → else
   `PreflightError("unregistered_constant")`.
3. Every name in any `consumed_by` resolves to a declared consumer — a gate in the
   inventory, or a `preflight:`-prefixed check in this file → else
   `PreflightError("phantom_consumer")`.

Check 1 alone would have caught Stage 2's `INFERENCE_SEEDS` but not a gate quietly
reading a value nobody declared. Neither 1 nor 2 catches an entry that names a
consumer which was never built — and that case is worse than both, because it
passes and then writes a `registry` block asserting the constant is consumed.

`check_constant_registry` therefore takes the declared preflight check names
alongside `gates`, so the `preflight:` namespace is resolvable rather than assumed:

```python
def check_constant_registry(registry, gates, preflight_checks) -> None: ...
```

---

## `check_manifest(manifest: dict, stage2_digests: list[str]) -> None`

| Assertion | Code |
|---|---|
| `manifest_version == "jspace-stage2b-stimulus/v1"` | `manifest_version` |
| `n_prompts == len(prompts) == 200` | `manifest_size` |
| exactly 40 prompts per category, 5 categories | `category_imbalance` |
| every `sha256` is 64 lowercase hex | `malformed_digest` |
| per-prompt digests are internally unique | `duplicate_prompt` |
| digest set ∩ `stage2_digests` is empty (FR-011) | `stage2_overlap` |
| `STAGE1_PROMPT_SHA256` absent | `anchor_contamination` |
| every `token_count <= MAX_PROMPT_TOKENS` | `prompt_too_long` |
| recomputed manifest digest matches the recorded one | `manifest_digest` |

`stage2_overlap` and `anchor_contamination` are separate codes on purpose. Both are
contamination, but the anchor case is expected-and-deliberate elsewhere in the
protocol (it is the reproduction kill check) and must not be diagnosed as an
ordinary overlap bug.

---

## `check_ratification(thresholds: dict) -> None`

```
if not thresholds.get("THRESHOLDS_RATIFIED"):
    raise PreflightError(code="not_ratified", ...)
```

FR-013 and Q10. Runs **last**, so that authoring-time validation of everything else
is exercisable on an unratified configuration — which is the state the notebook
ships in and the state every test runs against.

Additional assertion: if `THRESHOLDS_RATIFIED` is true, every constant whose
declared value is `None` (currently `SPEC_MIN_EFFECT` and `NTA_MIN_DENOMINATOR`,
both deferred to the Q6 pilot) raises `PreflightError("unset_constant")`.
Ratification cannot be signed while a threshold the decision depends on is still
unset — that is the Stage 2 failure mode restated, and it should be impossible
rather than discouraged.

---

## `check_environment(env: dict) -> None`

| Assertion | Code | Note |
|---|---|---|
| `python_version >= (3, 11)` | `python_version` | Stage 2 recorded but never asserted this |
| `jlens_commit == JLENS_COMMIT` | `jlens_commit` | **read back from the installed package**, not from the install line — research.md R2 |
| `cuda_available` is true | `no_cuda` | |
| `vram_gib >= MIN_VRAM_GIB` | `insufficient_vram` | |
| `model_revision`, `lens_revision`, `lens_sha256` match pins | `identity_mismatch` | |

`jlens_commit` is the one worth stating plainly: `%pip` does interpolate the pin
(R2, verified from IPython source), but that was established by reading upstream
source on a machine with no IPython installed. Asserting the *installed* commit
converts an inference into a measurement for one line of code.

---

## `emit_registry_record(registry, gates) -> dict`

Returns the `registry` block for the aggregate artifact: every entry with its
`consumed_by` list as resolved at preflight. Pure; no I/O.

This is what makes FR-009 auditable *after* the run rather than only during it. The
check passing leaves no trace by itself; the emitted record is the trace.

---

## Test obligations

The suite MUST include, for each check, at least one test that makes it **fail**.
Per Principle III, a preflight suite that only proves valid configurations pass has
not tested the preflight. Concretely, `tests/jspace/test_stage2b_preflight.py`
asserts each `code` above is raised by a configuration constructed to trigger it —
including `orphaned_constant`, which is a direct regression test for the Stage 2
audit finding, and `stage2_overlap`, which is one for FR-011.
