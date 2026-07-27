# Contract: constant registry ("declared means consumed")

Mechanizes constitution Principle IV. This is the design's self-described
highest-value change: cheap, mechanical, and it would have caught every finding of
the 2026-07-26 audit before execution rather than after.

---

## The defect class it prevents

Stage 2 declared constants, wrote them into artifacts, and never read them on a
decision path. The artifact faithfully recorded the *declaration*, so the record
testified that the constant was used. Four known instances:

| Item | What was declared | What ran |
|---|---|---|
| `INFERENCE_SEEDS = [0, 1]` | two seeds, "for seed-invariance" | seed 0 only; seeding was hardcoded |
| `RANDOM_VECTOR_SEEDS = [0, 1, 2]` | three seeds | three computed, one reached the decision |
| added-information gate | Jaccard **and** output/prompt-only clauses | Jaccard + Wilcoxon only |
| `output_argmax_rank_*` | "downstream criterion: the model's own next-token output", listed as ratified | computed, stored, read by no gate |

The first three are the audit's findings. The fourth is
[research.md](../research.md) R7 and is **not** in the amended record — it is an
open item for Dr. Mani, flagged rather than actioned.

The fourth is also why this contract covers two kinds of entry rather than one. A
registry checking only constants would have passed Stage 2's fourth defect, because
the orphan there was a computed field.

---

## Registry entry

```python
{
    "name": str,                  # constant or derived field
    "kind": "constant" | "derived_field",
    "declared_value": Any,        # constants only; None means deliberately deferred
    "consumed_by": list[str],     # gate names; MUST be non-empty
}
```

---

## The three checks

All run at preflight, before any measurement. Any one failing aborts the run.

**Forward — no orphans.**
For every registry entry, `len(consumed_by) >= 1`.
Failure code `orphaned_constant`.
*Catches: a declared constant that no gate reads.*

**Reverse — no strangers.**
For every constant name read by any gate, that name appears in the registry.
Failure code `unregistered_constant`.
*Catches: a gate reading a threshold nobody preregistered.*

**Referential — no phantom consumers.**
Every name appearing in any entry's `consumed_by` resolves to a declared consumer:
a gate in the gate inventory, or a preflight check declared in
[preflight-api.md](./preflight-api.md).
Failure code `phantom_consumer`.
*Catches: a registry entry that certifies a link to something that does not exist.*

The forward check alone would have caught Stage 2's `INFERENCE_SEEDS`, but not a
gate reading a value nobody declared — hence the reverse check.

Neither would catch the third case, and it is the one that most undermines the
mechanism: an entry naming a consumer that was never built passes the forward
check and produces a `registry` block in the artifact asserting the constant is
consumed. That is a registry manufacturing exactly the false assurance it exists to
prevent. Concretely, three entries below name preflight checks rather than gates —
without the referential check, a typo in any of them would be indistinguishable
from a real linkage.

**Consumer namespace.** `consumed_by` entries are resolved against two namespaces,
and the entry must say which:

| Prefix | Resolves against | Example |
|---|---|---|
| *(none)* | the gate inventory in [../data-model.md](../data-model.md) §4 | `h1_specificity` |
| `preflight:` | the check functions in [preflight-api.md](./preflight-api.md) | `preflight:decode_parity` |

A constant consumed only by a preflight check is still consumed — it governs an
abort, which is a decision. But it is not a scientific gate, and merging the two
namespaces would let a preflight-only constant look like it gated a hypothesis.

---

## What must be registered

| Registered | Not registered |
|---|---|
| every preregistered threshold and constant | run ids, timestamps, uuids |
| every constant a gate compares against | environment facts (VRAM, python version) |
| every derived field the preregistration describes as decision-relevant | purely descriptive outputs, if declared descriptive |

**The boundary rule**: if the preregistration says a quantity informs the decision,
it is registered and MUST have a consumer. If it is descriptive, it is recorded
under `descriptive` in the artifact and is not registered. What is forbidden is the
third state Stage 2 occupied — described as decision-relevant, recorded as if used,
consumed by nothing.

---

## Initial registry

Values from design §6 and Q-defaults. `None` means deliberately unset pending the
Q6 pilot, not forgotten.

| name | kind | declared_value | consumed_by |
|---|---|---|---|
| `STAGE1_RERUN_NOISE_MAX_ABS_LOGIT_DIFF` | constant | `0.0` | `reproduction` |
| `SPEC_MIN_EFFECT` | constant | `None` *(Q5, pilot-derived)* | `h1_specificity` |
| `BOOTSTRAP_CI_LEVEL` | constant | `0.99` | `h1_interval`, `h2_target` |
| `BOOTSTRAP_ITERATIONS` | constant | `10000` | `h1_interval`, `h2_target`, `sanity_floor` |
| `NONREDUNDANCY_MAX_JACCARD` | constant | `0.70` | `h2_overlap` |
| `NTA_MIN_DENOMINATOR` | constant | `None` *(Q6, pilot-derived)* | `preflight:denominator_guard` |
| `DECODE_PARITY_TOL` | constant | `1e-5` | `preflight:tensor_contracts` |
| `THRESHOLDS_RATIFIED` | constant | `False` | `preflight:ratification` |
| `nta_jacobian` | derived_field | — | `h1_specificity`, `h2_target`, `sanity_floor` |
| `nta_fit_broken_same_layer` | derived_field | — | `h1_specificity` |
| `nta_logit_lens` | derived_field | — | `h2_target` |
| `nta_random_vector` | derived_field | — | `sanity_floor` |
| `jaccard_top10_jacobian_vs_logit_lens` | derived_field | — | `h2_overlap` |
| `target_id` | derived_field | — | every `nta_*` |

Two constants carry `None`, and both are deliberate. `check_ratification` refuses to
accept `THRESHOLDS_RATIFIED = True` while any registered constant's declared value
is `None` (`unset_constant`) — so the deferral cannot survive into an authorized
run by accident. Deferring the threshold and signing the ratification are made
mutually exclusive rather than merely discouraged.

---

## Not registered, deliberately

`SAME_RUNTIME_REPEATS`, `INFERENCE_SEEDS`, `RANDOM_VECTOR_SEEDS` — Stage 2's three
loose constants. Under this contract each must either drive the loop that bears its
name and be registered, or be deleted. Carrying them forward as declarations that
happen to match hardcoded behaviour is what the registry exists to stop. The
decision on each belongs with the notebook-authoring task, not here.

---

## Artifact obligation

The resolved registry — every entry with its `consumed_by` as computed at preflight
— is written into the aggregate artifact under `registry`.

The check passing leaves no evidence on its own. The emitted record is what lets a
later reader verify the linkage without rerunning anything, which is the whole
point: Stage 2's audit had to read notebook source precisely because its artifact
recorded declarations without consumption.
