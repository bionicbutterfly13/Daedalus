# Contract: `jspace-observation-stage2b/v1`

Artifact shapes for Stage 2b. Two kinds, both content-addressed. Field-level rules
in [../data-model.md](../data-model.md) §6; this file is the contract a reader can
check an artifact against.

---

## Content addressing (unchanged from Stage 2)

```python
canonical = json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
digest    = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
filename  = f"{prefix}_{digest[:16]}.json"
```

Written with exclusive-create (`"xb"`). On `FileExistsError`, re-hash the existing
file and raise if it disagrees. Re-verify the on-disk digest after writing.

Carried over deliberately and byte-for-byte, so Stage 2b artifacts remain
comparable with Stage 2's. Under Principle V these files are immutable evidence:
excluded from formatters and linters, never reformatted after the fact, digest
re-verified after any operation that touches them.

Prefixes: `jspace_observation_s2b` (per-prompt), `jspace_discrimination_s2b`
(aggregate).

---

## Per-prompt record

Blocks inherited from Stage 2 unchanged: `schema`, `artifact_type`, `run_id`,
`observation_id`, `created_at_utc`, `evidence_class`, `scope`, `model`, `lens`,
`instrumentation`, `input`, `stimulus`, `runtime`, `retention`.

`schema` is `"jspace-observation-stage2b/v1"`; `artifact_type` is `"per_prompt"`;
`evidence_class` is `1`.

### `measurement`

```jsonc
{
  "selected_layers": [6, 13, 20, 26],
  "positions": [-2],
  "target_id": 12345,                     // Q3 — not delegable, unresolved
  "target_source": "model_argmax",        // records WHICH definition was used
  "rank_convention": "strict_gt_1indexed",
  "vocab_size": 151936,
  "per_layer": {
    "6": {
      "rank1":     { "jacobian": 41, "fit_broken_same_layer": 900, "...": 0 },
      "s":         { "jacobian": -0.31, "...": 0.0 },
      "nta":       { "jacobian": 0.42, "...": 0.0 },
      "denominator": 0.55,
      "excluded": false,
      "exclusion_reason": null
    }
  }
}
```

`target_source` is recorded rather than assumed. Q3 defines what this study means
by "information", and a reader must be able to tell from the artifact alone which
definition produced the number — a pass under the argmax target must never be
readable as a pass under some other target.

`prompt_only` and `output` appear in `rank1` and `s` but always as `0.0` and `1.0`
in `nta`, by construction (FR-002).

### `factorial`

```jsonc
{
  "per_layer": {
    "6": {
      "cells": {
        "correct_act_fitted_map":  0.42,
        "correct_act_broken_map":  0.11,
        "wrong_act_fitted_map":    0.05,
        "wrong_act_broken_map":    0.03
      },
      "paired_diff_h1": 0.31,          // fitted − broken, correct activation
      "paired_diff_h2": 0.18           // jacobian − logit_lens
    }
  },
  "wrong_activation_source_prompt_sha256": "…",   // FR-005: a real residual
  "broken_map_seed": 20260726,
  "broken_map_method": "haar_left_singular_rotation"
}
```

**Two naming conventions, deliberately.** Inside `factorial.cells`, names describe
the 2×2 position (`correct_act_broken_map`); everywhere else, names describe the
readout (`fit_broken_same_layer`). They refer to the same object. The cell naming
makes the factorial structure readable at a glance, which is the whole point of
replacing Stage 2's ad-hoc control family; the readout naming is what the rest of
the artifact and the registry use.

`wrong_activation_source_prompt_sha256` records that the wrong activation was a
real norm-matched residual from a different prompt in the same manifest, not a
random vector (FR-005). Without it the distinction is a claim in a design document
rather than a checkable property of the run.

### `contracts`

The R5 tensor-contract values as observed, recorded rather than merely checked:

```jsonc
{
  "residual_shape": [2048], "residual_dtype": "torch.float32",
  "jacobian_shape": [2048, 2048], "jacobian_dtype": "torch.float32",
  "readout_device": "cpu",
  "decode_parity_max_abs": 3.1e-6,
  "logit_softcapping": null,
  "rank_parity_verified": true          // FR-010, against jlens.vis._ranks_of
}
```

A preflight that passes leaves no trace by itself. These fields are the trace.

---

## Aggregate record

Inherited unchanged: `schema`, `artifact_type` (`"aggregate"`), `run_id`,
`created_at_utc`, `evidence_class`, `scope`, `model`, `lens`, `instrumentation`,
`runtime`, `stimulus_manifest`, `retention`.

### `registry` *(new, required)*

The resolved constant registry — every entry with `consumed_by` as computed at
preflight. See [constant-registry.md](./constant-registry.md).

### `disjointness` *(new, required)*

```jsonc
{
  "checked": true,
  "stage2_manifest_sha256": "…",
  "stage2b_manifest_sha256": "…",
  "overlap_count": 0,
  "anchor_present": false
}
```

FR-011. `checked: true` with `overlap_count: 0` is the assertion's *result*; the
design is explicit that disjointness is checked, not documented.

### `gates` *(new, required)*

One record per gate, per [../data-model.md](../data-model.md) §4:

```jsonc
{
  "name": "h1_specificity",
  "constant_name": "SPEC_MIN_EFFECT",
  "declared_value": null,
  "statistic": 0.29,
  "interval": { "method": "bca", "level": 0.99, "low": 0.14, "high": 0.44 },
  "interval_crosscheck": { "method": "percentile", "low": 0.15, "high": 0.43 },
  "n_clusters": 193,
  "exclusions": [ { "reason": "denominator_below_min", "count": 7, "layer": 26 } ],
  "outcome": "pass"
}
```

**Three rules a validator must enforce:**

1. `outcome` ∈ {`pass`, `fail`, `undefined`}. A non-finite `interval.low` or
   `.high` MUST produce `undefined`, never `fail` (research.md R6). BCa
   acceleration is unstable for a median under leave-one-out, and scipy returns NaN
   bounds on a degenerate bootstrap. An absent measurement and a measured null are
   different results and must not collapse into one.
2. `interval_crosscheck` is required whenever `interval.method` is `bca`. Recording
   only the interval that gated leaves no way to detect a degenerate BCa after the
   fact.
3. `exclusions` is a list with per-reason, per-layer counts. A bare total is not
   sufficient — the denominator guard is expected to bite hardest at late layers,
   and pooling would hide that.

### `descriptive` *(new, required)*

Per-layer NTA curves, 2×2 cell means with intervals, the interaction estimate,
per-distance-band mismatched-layer results, per-category breakdowns.

Kept in a sibling block to `gates`, not merged with it. The interaction in
particular is reported and interpreted but deliberately **not** gated — no pilot
estimate exists for it — and the structure should make that impossible to misread.

### `decision`

```jsonc
{ "result": "pass" | "ambiguity" | "fail" | "kill", "notes": "…" }
```

---

## Validator obligation (FR-012, SC-003)

`validate_observation.py` in the same skill directory gains a Stage 2b branch. Its
test is not that the artifact parses — it is that **every value a gate's outcome
depends on is present in the aggregate**, so each decision is recomputable from
artifacts alone, without the notebook.

That is the concrete difference from Stage 2, whose report could not be
independently certified from its own artifacts. The audit had to read notebook
source to establish what the gates actually did, and that is the failure this
schema is shaped to prevent.
