# Quickstart: validating Stage 2b without running it

Every scenario here runs on a laptop with no GPU, no `torch`, no `jlens`, and no
`scipy`. That is deliberate: Stage 2b's authoring deliverables are validated by
tests, and the measurement is not run at all until Dr. Mani ratifies the ten open
parameters (FR-013, Q10).

If a scenario below requires a GPU, it is in the wrong document.

---

## Prerequisites

```bash
cd /Volumes/Asylum/archimedes
uv sync --extra dev
```

Baseline, so a regression is attributable: `uv run pytest` on `main` is
**3036 passed, 12 skipped**.

---

## Scenario 1 — The preflight catches every failure it claims to

The primary validation. Per Principle III, a preflight suite that only proves valid
configurations pass has not tested the preflight, so each test below constructs a
configuration built to fail.

```bash
uv run pytest tests/jspace/test_stage2b_preflight.py -v
```

Expected: one passing test per failure code in
[contracts/preflight-api.md](./contracts/preflight-api.md) —

| Test asserts | Code |
|---|---|
| a declared constant with no consuming gate is rejected | `orphaned_constant` |
| a gate reading an unregistered constant is rejected | `unregistered_constant` |
| a residual in the wrong dtype is rejected | `dtype_mismatch` |
| a readout on the wrong device is rejected | `device_mismatch` |
| decode parity beyond tolerance is rejected | `decode_parity` |
| a manifest overlapping Stage 2 is rejected | `stage2_overlap` |
| a manifest containing the Stage 1 anchor is rejected | `anchor_contamination` |
| ratification with an unset threshold is rejected | `unset_constant` |
| an unratified configuration refuses to run | `not_ratified` |

`orphaned_constant` is the regression test for the audit finding, and
`stage2_overlap` is the one for FR-011. Both should be readable as such by someone
who has not read the audit.

**This scenario satisfies US3's independent test**: exercised against a
deliberately broken configuration, with no GPU and no measurement.

---

## Scenario 2 — The endpoint behaves at its edges

```bash
uv run pytest tests/jspace/test_stage2b_endpoint.py -v
```

| Property | Expected |
|---|---|
| `NTA(prompt_only) == 0.0` and `NTA(output) == 1.0` | exactly, by construction (FR-002) |
| rank convention | 1-indexed, strict `>`; the top token ranks 1, never 0 |
| rank parity (FR-010) | comparison-count rank equals the `_ranks_of` reference on a fixed probe |
| denominator at or below `NTA_MIN_DENOMINATOR` | cell excluded, reason recorded, **not** divided |
| exclusion accounting | counted per layer, never pooled to a bare total |

The rank-parity test is the one that matters most. FR-010 exists because an
optimization that silently changes a statistic is indistinguishable from a correct
one until the results are wrong, and `jlens.vis._ranks_of` is a reference
implementation the library itself ships tests for (research.md R4).

Note the parity test needs a logits array, not a model — build it with a fixed
seed. If `_ranks_of` cannot be imported (no torch locally), the test compares
against an inline naive `argsort` reference with the same documented convention and
is marked so the Colab run repeats it against the real function.

---

## Scenario 3 — The manifest is held out, and provably so

```bash
uv run pytest tests/jspace/test_stage2b_manifest.py -v
```

| Property | Expected |
|---|---|
| 200 prompts, 5 categories, 40 each | asserted, not assumed |
| every `sha256` is 64 lowercase hex and internally unique | — |
| digest set is disjoint from Stage 2's | `overlap_count == 0` |
| Stage 1 anchor absent | `anchor_present == false` |
| recomputed manifest digest matches the recorded one | canonicalization is byte-identical to Stage 2's |
| every `token_count <= 128` | `MAX_PROMPT_TOKENS` |

---

## Scenario 4 — The shipped notebook cannot run

The boundary check. Whatever else is true, the committed notebook must refuse.

```bash
grep -n "THRESHOLDS_RATIFIED" "sakshi notes/jspace_colab_stage2b_discrimination.ipynb"
```

Expected: `THRESHOLDS_RATIFIED = False` in the constants cell, and a guard that
raises before the measurement loop.

```bash
uv run pytest tests/jspace/test_stage2b_preflight.py -k not_ratified -v
```

Expected: passes — an unratified configuration raises `PreflightError` with code
`not_ratified` before any measurement path is entered.

This is the one scenario worth re-running after **any** edit to the notebook. FR-013
is the boundary between authoring, which this feature covers, and execution, which
it does not.

---

## Scenario 5 — An artifact is recomputable from itself

Once an aggregate artifact exists (post-ratification, not part of this feature):

```bash
uv run python EvoScientist/skills/jspace-research-operations/scripts/validate_observation.py \
    <artifact.json> --expected-sha256 <digest>
```

The schema is auto-detected from the artifact's own `schema` field
(`validate_observation.py:412-414`); there is no `--schema` flag. T041's Stage 2b
branch is selected the same way.

Expected: every gate's `outcome` is derivable from the fields in the same artifact —
`statistic`, `interval`, `declared_value`, `exclusions`, `n_clusters` — with no
appeal to the notebook. That is SC-003, and it is the property Stage 2's artifacts
lacked, which is why its audit had to read notebook source to establish what the
gates did.

Also verify the file's own digest still matches its filename prefix. These are
immutable evidence; a mismatch means something reformatted them.

---

## What is deliberately not here

- **Any GPU scenario.** Execution is unauthorized until Q1–Q9 are ratified and Q10
  is signed.
- **An unguarded bootstrap test.** `scipy` is a Colab-side dependency and is not in
  this repo's lockfile (research.md R6), so the bootstrap tests exist but are
  guarded with `pytest.importorskip("scipy")` — they run wherever scipy is present
  and skip cleanly here. What is genuinely absent is a hand-rolled numpy resampler,
  which would itself need an equivalence check against scipy and buys nothing.
- **An end-to-end notebook run.** The notebook is a shell over the tested modules by
  design (see plan.md Structure Decision). Stage 2 put everything in one cell, and
  no test could reach any of it — which is why four declared-but-unconsumed
  quantities survived to an audit.
