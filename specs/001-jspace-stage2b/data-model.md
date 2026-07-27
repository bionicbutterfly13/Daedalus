# Phase 1 Data Model: Stage 2b J-space discrimination

Entities, their fields, and the validation rules each carries. Derived from
spec.md Key Entities and the requirements FR-001 … FR-013, with dtype and shape
facts taken from [research.md](./research.md) R1/R5.

Schema identifier for this stage: `jspace-observation-stage2b/v1`.

---

## 1. Stimulus manifest

Version `jspace-stage2b-stimulus/v1`. A versioned JSON file in the repo, not a
literal list inside the notebook — this is the one structural change from Stage 2,
and it exists so the recorded digest has a referent that can be checked without
reading notebook source.

**Manifest document**

| Field | Type | Rule |
|---|---|---|
| `manifest_version` | str | `"jspace-stage2b-stimulus/v1"` exactly |
| `n_prompts` | int | 200 (Q1); MUST equal `len(prompts)` |
| `categories` | list[str] | sorted; 5 entries, inherited from Stage 2 |
| `prompts` | list[Prompt] | 40 per category (Q1), enforced |

**Prompt**

| Field | Type | Rule |
|---|---|---|
| `id` | str | `f"s{index:03d}"` — three digits, since n=200 overflows Stage 2's two |
| `index` | int | 0-based, contiguous, matches position in list |
| `category` | str | member of `categories` |
| `text` | str | the raw prompt; lives here and nowhere else (Q8) |
| `sha256` | str | 64 hex chars, SHA-256 of `text` UTF-8 bytes |
| `utf8_byte_count` | int | matches `len(text.encode())` |
| `token_count` | int | ≤ `MAX_PROMPT_TOKENS` (128); recorded at build time |

**Manifest digest**: SHA-256 of
`json.dumps(manifest_doc, sort_keys=True, indent=2, ensure_ascii=False) + "\n"`,
matching Stage 2's canonicalization exactly so the two are comparable.

**The digest is never stored inside the manifest.** A document cannot contain its
own hash. It lives in exactly two places, both outside: the filename
(`jspace-stage2b-stimulus-v1.json` is content-named at commit time only for
humans; the authoritative copy is the artifact) and
`aggregate.stimulus_manifest.sha256` in every observation artifact.
`check_manifest` therefore takes the expected digest as an argument and compares it
to the value recomputed from the document — it has no self-consistent field to
check against, and asking it to find one is how a digest check quietly becomes a
tautology.

**Validation rules**

- **Disjointness (FR-011)**: the set of per-prompt `sha256` values MUST be disjoint
  from Stage 2's manifest. Checked at preflight against the recorded Stage 2 digest
  list, and the assertion result recorded in the artifact. Documented-as-a-rule is
  not sufficient; the design is explicit that this is checked.
- **Anchor exclusion**: `STAGE1_PROMPT_SHA256` MUST NOT appear in this manifest.
  The Stage 1 anchor is retained as the reproduction kill check and lives *outside*
  the analysis sample; including it would contaminate held-out status.
- **Category balance**: exactly 40 prompts per category, asserted at build time and
  re-asserted at preflight.
- **Immutability**: once the manifest file's digest is recorded in any artifact, the
  file is content-addressed evidence under Principle V — excluded from formatters
  and linters, never reformatted.

---

## 2. Readout

A token ranking in the model's vocabulary basis. Not persisted in full; only
derived statistics reach artifacts.

**Readout kinds** — seven, of which four form the factorial:

| Kind | Activation | Map | Role |
|---|---|---|---|
| `jacobian` | correct | fitted | the instrument (2×2 cell A) |
| `fit_broken_same_layer` | correct | Haar-rotated (FR-004) | does the fit matter? (cell B) |
| `jacobian_wrong_activation` | wrong (FR-005) | fitted | does the activation matter? (cell C) |
| `fit_broken_wrong_activation` | wrong | Haar-rotated | transport floor (cell D) |
| `logit_lens` | correct | none (`use_jacobian=False`) | cheap baseline, H2 |
| `prompt_only` | — | — | endpoint floor, maps to NTA 0 |
| `output` | — | — | endpoint ceiling, maps to NTA 1 |

Secondary comparators retained for commensurability with Stage 2, not primary:
`random_vector` (sanity floor), `shuffled_layer`, `mismatched_probe`, the last
balanced across preregistered layer distances (FR-008, Q7 default `|Δ| ∈ {3,7,14}`).

**Tensor contract** (asserted at preflight, FR-009; sources in research.md R5)

| Property | Required value | Note |
|---|---|---|
| residual shape | `(d_model,)` = `(2048,)` | per locus, per position |
| residual dtype **before transport** | `float32` | `transport` does not cast; a half-precision residual is a dtype-mismatched matmul |
| Jacobian shape | `(2048, 2048)` dense | `lens.jacobians[layer]` |
| Jacobian dtype | `float32` | `.float()` in `JacobianLens.__init__` |
| decoded readout device | CPU | `apply` forces `.float().cpu()`; direct `unembed` does **not** — normalize explicitly |
| decode parity | `\|decode_residual(x) − lens.unembed(x)\|` ≤ `DECODE_PARITY_TOL` (1e-5) on a fixed probe | proves all readouts share one vocabulary basis |
| logit softcapping | recorded, expected inactive for Qwen3-1.7B | `unembed` applies it when config sets it; would silently change every rank |

---

## 3. Endpoint: normalized target attainment

Not an entity so much as the derived quantity every gate reads. Specified here
because its edge cases are validation rules.

```
rank1(t, r, p, l) = (logits_r > logits_r[t]).sum(-1) + 1     # 1-indexed, strict >
s(r, p, l)        = -log(rank1(t, r, p, l)) / log(V)
NTA(r, p, l)      = ( s(r) - s(prompt_only) ) / ( s(output) - s(prompt_only) )
```

| Rule | Requirement |
|---|---|
| Rank convention | 0-indexed comparison count, `+1` for the log. Strict `>` (best rank among ties), preregistered and recorded. |
| Rank verification (FR-010) | comparison-count rank MUST equal `jlens.vis._ranks_of` on a fixed probe. Disagreement means the optimization changed the statistic. |
| Target `t(p)` | governed by Q3, **not delegable**, unresolved. Default proposed: the model's own next-token argmax. |
| Denominator guard | cells with `s(output) − s(prompt_only)` ≤ `NTA_MIN_DENOMINATOR` are excluded; exclusion count reported **per layer**, never silently dropped |
| Layer stratification | all comparisons within layer. Depth-pooled NTA is descriptive only and MUST NOT gate. |
| Anchors | `prompt_only` = 0 and `output` = 1 by construction (FR-002) — the Stage 2 omission is unrepresentable, not re-added as a gate |

---

## 4. Gate

A named decision. This is the entity FR-012 exists to make recomputable.

| Field | Type | Rule |
|---|---|---|
| `name` | str | unique within the run |
| `constant_name` | str \| null | MUST be present in the constant registry |
| `declared_value` | any | the preregistered value, verbatim |
| `statistic` | float | observed |
| `interval` | {`method`, `level`, `low`, `high`} | `method` ∈ {`bca`, `percentile`}; both recorded (R6) |
| `n_clusters` | int | prompts contributing, post-exclusion |
| `exclusions` | list[{`reason`, `count`, `layer`}] | never a bare total |
| `outcome` | enum | `pass` \| `fail` \| `undefined` |

**Validation rules**

- **Non-finite interval ⇒ `undefined`, not `fail` (R6).** A NaN BCa bound is an
  absent measurement, not a measured null. Collapsing the two would let a
  degenerate bootstrap masquerade as a result — the exact overstatement Principle V
  forbids.
- Every gate MUST resolve to a registry entry; no gate reads an unregistered
  constant.

**Gate inventory**

The `ID` column is canonical. It is what `consumed_by` entries in the registry
resolve against, so these strings and those strings must match exactly.

| ID | Gate | Statistic | Constant | Default |
|---|---|---|---|---|
| `reproduction` | Reproduction (kill) | anchor top-k identity, max abs logit diff | `STAGE1_RERUN_NOISE_MAX_ABS_LOGIT_DIFF` | `0.0` |
| `h1_specificity` | H1 specificity | cluster-bootstrap median `NTA(jac) − NTA(fit_broken)`, **per layer** | `SPEC_MIN_EFFECT` | **unset (Q5)** |
| `h1_interval` | H1 interval | BCa lower bound of that median above zero | `BOOTSTRAP_CI_LEVEL` | `0.99` |
| `h2_overlap` | H2 non-redundancy, overlap | median top-10 Jaccard vs logit lens | `NONREDUNDANCY_MAX_JACCARD` | `0.70` |
| `h2_target` | H2 non-redundancy, target | interval on `NTA(jac) − NTA(logit_lens)` excludes 0 | `BOOTSTRAP_CI_LEVEL` | `0.99` |
| `sanity_floor` | Sanity floor | `NTA(jac) − NTA(random_vector)` excludes 0 | — | must hold |

**H1 is two conjunctive clauses, not one.** `h1_specificity` requires the median
paired difference to exceed `SPEC_MIN_EFFECT`; `h1_interval` requires the interval
on that median to exclude zero. H1 passes only if both hold. This follows
`STAGE2B_DESIGN.md` §2 and §6 — "the median paired difference is greater than
`SPEC_MIN_EFFECT`, with a cluster-bootstrap confidence interval excluding zero."

It is **not** the single criterion "the lower bound exceeds `SPEC_MIN_EFFECT`",
which is strictly stronger and would fail cases the two-clause rule passes. spec.md
Acceptance Scenario 2 under US1 originally stated the stronger form; it has been
corrected to match the design. Whichever is intended, the important thing is that
one rule is written in one place, because a decision rule that differs between the
spec and the data model is a rule nobody can implement.

**Per-layer, then combined.** Because all comparisons are within layer (§3), the
gate statistic is computed per layer and the gate passes only if it holds at every
layer in `SELECTED_LAYERS`. Concatenating every layer's paired differences into one
pooled median would let a strong late layer carry the result — the same depth-
pooling this design forbids for absolute NTA, reintroduced one level down. Pooled
figures remain reportable under `descriptive`.

Decision composition: **pass** = reproduction ∧ H1 ∧ H2(both clauses);
**ambiguity** = reproduction ∧ exactly one of H1/H2; **fail** = reproduction ∧
neither, or sanity floor not cleared; **kill** = reproduction fails, any pinned
identity mismatches, or the capacity gate fails.

The 2×2 interaction is computed and reported but is **not** a gate — no pilot
estimate exists for it, and adding a third preregistered threshold to a quantity
with no prior would be guessing.

---

## 5. Constant registry entry

The mechanization of Principle IV. Full contract in
[contracts/constant-registry.md](./contracts/constant-registry.md).

| Field | Type | Rule |
|---|---|---|
| `name` | str | the declared constant or decision-relevant field |
| `kind` | enum | `constant` \| `derived_field` |
| `declared_value` | any | for `constant` only |
| `consumed_by` | list[str] | ≥ 1 gate name; **empty is a preflight failure** |

`derived_field` exists because of research.md R7: Stage 2's orphan was a computed
field (`output_argmax_rank_*`), not a declared constant. A registry covering only
constants would have missed it.

---

## 6. Observation artifact

Content-addressed JSON, per-prompt and aggregate. Canonicalization and filename
scheme carried over unchanged from Stage 2 so artifacts remain comparable:
`json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n"`, SHA-256,
`f"{prefix}_{digest[:16]}.json"`, exclusive-create with an immutability re-check
on collision.

**Per-prompt record** — Stage 2's shape, with `measurement` and `discrimination`
replaced:

- unchanged: `schema`, `artifact_type`, `run_id`, `observation_id`,
  `created_at_utc`, `evidence_class`, `scope`, `model`, `lens`, `instrumentation`,
  `input`, `stimulus`, `runtime`, `retention`
- `measurement`: `selected_layers`, `positions`, `target_id`, `target_source`,
  `rank_convention`, per-readout `rank1` and `s`, `nta` per readout per layer,
  `denominator`, `excluded` + `exclusion_reason`
- `factorial`: the four cells' NTA at each layer, plus the per-layer paired
  differences that feed H1
- `contracts`: the asserted tensor-contract values, recorded rather than merely
  checked

**Aggregate record**

- unchanged: `schema`, `artifact_type`, `run_id`, `created_at_utc`,
  `evidence_class`, `scope`, `model`, `lens`, `instrumentation`, `runtime`,
  `stimulus_manifest`, `retention`
- `registry`: the full constant registry as resolved at preflight, including
  `consumed_by` for every entry — this is what makes the FR-009 check auditable
  after the fact rather than only at run time
- `gates`: list of Gate records (§4), one per gate
- `disjointness`: `{checked: true, stage2_manifest_sha256, overlap_count: 0}`
- `decision`: `{result, notes}` where `result` ∈ `pass` | `ambiguity` | `fail` | `kill`
- `descriptive`: per-layer NTA curves, 2×2 cell means with intervals, the
  interaction estimate, per-distance-band mismatched-layer results, per-category
  breakdowns — explicitly separated from `gates` so that nothing descriptive can be
  mistaken for a decision input

**Validation rule (FR-012)**: every value a gate's outcome depends on MUST appear
in the aggregate. The test is whether a reader can recompute each decision from
the artifact alone. Stage 2's could not, which is why its audit had to read
notebook source.

---

## Entity relationships

```text
Stimulus manifest ─┬─> Prompt ──> (per-prompt) Observation artifact
                   │                    │
                   │                    └──> Readout ──> rank1 ──> s ──> NTA
                   │                                                     │
                   └──> manifest digest ──> disjointness check           │
                                                                         v
Constant registry ──> Gate <──────────────── paired difference ──> cluster bootstrap
        │               │                                                │
        │               └──> outcome ──> decision                        │
        └──> preflight: every entry has ≥1 consumer, every gate reads a registered name
```
