---
name: jspace-research-operations
description: Use when planning, operating, reviewing, reproducing, or integrating Jacobian Lens/J-space experiments in Colab, Jupyter, or GPU runtimes. Enforces exact source identity, capacity gates, immutable typed observations, sparse-retention boundaries, artifact verification, and separation of measured readouts from scientific or consciousness claims.
version: 1.0.0
author: Hermes Agent
license: Apache-2.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [research, jspace, jacobian-lens, gpu, provenance, reproducibility]
    related_skills: []
---

# J-space Research Operations

## Overview

Operate Jacobian Lens experiments as bounded scientific measurements, not as demonstrations of beliefs, intentions, cognition, or consciousness. Preserve exact identities for the model, tokenizer, fitted lens, instrumentation code, stimulus, runtime, and derived artifacts.

J-space is Anthropic's name for a model-internal subspace identified with a Jacobian Lens. It is not a package, Hermes profile, or autonomous scientific authority. The installable instrument is the Jacobian Lens implementation plus compatible model and fitted-lens artifacts.

Use progressive disclosure:

- Read `references/known-good-smoke-test.md` when reproducing or comparing against the pinned Qwen3-1.7B smoke test.
- Read `references/stage2-discrimination-baseline.md` when preparing or reviewing the Stage 2 observational-discrimination study (design, ratified thresholds, runtime fixes, and the first executed-run result).
- Read `sakshi notes/STAGE2_DISCRIMINATION_REPORT.md` for the full scientific write-up of the first Stage 2 execution (idea, hypothesis, methods, results, conclusion, discussion; decision was ambiguity).
- Read `sakshi notes/INGOING_BRIEF_ARCHIMEDES_EVOSCIENTIST.md` to start an EvoScientist run on this study: it carries the exact task, the full study, the operational journey and lessons, runtime/invocation facts, a source index with commit ids, and acceptance gates.
- Use `scripts/validate_observation.py` after downloading a sparse observation JSON (auto-detects the smoke-test and discrimination/v1 schemas).
- Use `templates/evidence-report.md` when reporting a run or handoff.

## When to Use

Load this skill for:

- Jacobian Lens or J-space notebook execution;
- GPU/runtime qualification for model-internal measurements;
- pinned model/lens reproduction;
- sparse observation artifact design or review;
- J-space evidence handoffs among Hermes, EvoScientist, Sakshi, Elume, or other research agents;
- proposals to interpret, compare, intervene on, or integrate J-space measurements.

Do not use it for ordinary hosted-model API calls, generic text-generation evaluation, unrelated GPU workloads, or claims that do not involve model-internal instrumentation.

## Authority and Scientific Boundaries

Keep roles separate:

- The orchestrator authorizes scope, resources, transfer, publication, and acceptance.
- The scientific operator executes the bounded protocol and reports evidence.
- The Jacobian Lens produces measurements; it does not interpret them.
- A witness/audit layer checks lineage and protocol compliance; it does not decide scientific meaning.
- A candidate cognitive architecture may consume typed observations; it does not validate itself.

Classify every claim:

1. **Observed:** directly measured activation-derived readout, runtime fact, artifact property, intervention, or behavioral output under a specified protocol.
2. **Supported inference:** a functional interpretation that survived predefined controls.
3. **Unresolved interpretation:** construct validity, generalization, subjective experience, phenomenal consciousness, or broader cognitive meaning.

Never promote a sparse token readout directly from class 1 to class 2 or 3.

## Required Inputs

Before execution, resolve:

- canonical notebook or script path/URL;
- source size, SHA-256, and modification/revision identity;
- instrumentation repository and commit;
- model repository and immutable revision;
- tokenizer identity when it is not implied by the model revision;
- fitted-lens repository, immutable revision, filename, and expected dimensions;
- minimum GPU VRAM and supported numerical precision;
- allowed stimuli, outputs, retention, transfer, and publication;
- success, ambiguity, failure, and kill criteria.

Completion criterion: every identity and authorization is explicit, or the unresolved item is a named blocker.

## Operating Workflow

### 1. Establish the canonical source

Access the notebook/script directly. Record access method and coverage. Compute size and SHA-256. Preserve the canonical source and use a disposable upload or repair copy.

Completion criterion: the canonical source has a stable identity and no planned operation requires mutating it.

### 2. Bound the experiment

State allowed measurement, prohibited intervention, stimulus restrictions, retention rules, transfer restrictions, and publication gate. Default to observation only. Lens fitting, steering, ablation, architecture mutation, artifact transfer, and publication require their own authorization.

Completion criterion: each consequential action is either authorized or excluded.

### 3. Verify actual runtime access

Prove that the intended signed-in browser/runtime is controllable. A healthy automation installation is not proof that the target window is reachable. Scope browser automation to the exact notebook window and avoid unrelated tabs/windows.

If a permission, password, 2FA, payment, or quota prompt appears, stop for the user.

Completion criterion: the notebook page and its runtime controls are directly observable.

### 4. Run the cheapest preflight first

Before large downloads, measure:

- CUDA availability;
- GPU model, total VRAM, compute capability, and driver;
- Python, Torch, CUDA runtime, Transformers, and Hub versions;
- disk capacity;
- intended precision support.

Honor the declared capacity threshold. Insufficient hardware is a measured failure, not permission to weaken the gate.

Completion criterion: the runtime satisfies every declared capacity gate or the run stops before model/lens downloads.

### 5. Resolve immutable identities

Resolve model and lens revisions through the source API and assert exact equality with requested commits. Download only the required fitted-lens artifact, compute its SHA-256 before deserialization, and record its byte size.

Completion criterion: requested and resolved revisions match exactly, and the lens has a locally measured checksum.

### 6. Verify compatibility

Load the pinned model, tokenizer, and lens. Check model width, layer count, lens width, source-layer range, tokenizer/model pairing, and numerical backend. Treat successful object construction without these checks as insufficient.

Completion criterion: every compatibility assertion passes in the measured runtime.

### 7. Execute the bounded observation

Use only authorized stimuli. Record a stimulus digest and token/byte counts rather than raw restricted text when required. Select layers and positions in advance. Produce sparse top-k Jacobian readouts plus an appropriate baseline. Repeat the same-runtime measurement under fixed seeds.

Do not persist raw activations or full-vocabulary logits unless separately authorized.

Completion criterion: the observation contains specified layers/positions, baseline, repeatability result, and provenance.

### 8. Export an immutable typed observation

Write canonical JSON bytes and derive the filename from SHA-256. Never overwrite an existing content-addressed path with different bytes. Include at minimum:

- schema and observation/run identity;
- evidence class and scope;
- model, tokenizer, instrumentation, and lens identities;
- stimulus digest and measurement location;
- sparse Jacobian readouts and baseline;
- runtime environment;
- repeatability and uncertainty;
- retention declarations;
- creation time.

Completion criterion: readback SHA-256 equals the content-derived filename digest.

### 9. Transfer only after authorization

A runtime artifact is not local evidence until transferred and independently verified. Prefer the hosted runtime's file browser/download action when notebook-editor automation is unreliable. After transfer, compute local size and SHA-256 and directly read the complete JSON.

Completion criterion: local size/hash match runtime output and complete JSON coverage is recorded.

### 10. Recheck preservation and report

Recompute the canonical source identity. Report direct sources, methods, coverage, derivative evidence, verification, gaps, and boundaries using `templates/evidence-report.md`.

Completion criterion: the canonical source is unchanged, every artifact is accounted for, and unsupported interpretations are explicit.

## Typed Observation Contract

Prefer an immutable seam between instrumentation and downstream systems. Raw Torch/CUDA/Jacobian objects should not become ordinary agent memory.

Required conceptual fields:

| Field | Purpose |
|---|---|
| `run_id` or `observation_id` | Stable replay/citation identity |
| `schema` | Versioned contract |
| model/tokenizer revisions | Exact measured system identity |
| lens revision, filename, hash | Exact fitted instrument identity |
| instrumentation repository/commit | Measurement implementation identity |
| input digest and counts | Stimulus identity without unnecessary retention |
| layer/position/span | Measurement location |
| sparse readouts and baseline | Bounded derived evidence |
| seed/runtime/backend | Replay controls |
| repeatability/uncertainty | Stability and interpretive limits |
| retention flags | Proof of excluded raw data classes |
| artifact checksum | Content-addressed evidence reference |

Validate downloaded artifacts with:

```bash
python EvoScientist/skills/jspace-research-operations/scripts/validate_observation.py \
  /path/to/jspace_observation_<digest-prefix>.json
```

Add `--expected-sha256 <digest>` when a runtime-reported checksum is available.

## Experiment Stage Gates

Do not skip stages:

1. **Measurement reproduction:** environment, known example, stability, provenance.
2. **Observational discrimination:** compare J-space with logit, output, prompt-only, random-vector, and non-J-space baselines.
3. **Causal intervention:** only after separate authorization; predefined ablation/addition/swap controls.
4. **Framework testing:** preregister functional predictions and alternative explanations.
5. **System integration:** only validated typed observations cross into Sakshi, Elume, or another architecture.

A same-runtime smoke test completes stage 1 only partially. It does not establish cross-runtime reproducibility, predictive validity, causal validity, or integration readiness.

## Browser and Notebook Safety

Hosted notebooks are stateful documents and UI automation can misdirect input.

- Target the exact browser PID/window and preserve unrelated windows.
- Re-capture accessibility state after every state-changing action.
- Verify execution counters and output, not just button presses.
- Do not treat inherited notebook output as current execution evidence.
- Avoid direct AX value replacement in CodeMirror editors; it can concatenate into the wrong cell while displaying the intended text elsewhere.
- Prefer an existing explicit opt-in cell, a runtime file browser, or a freshly inserted disposable cell for authorized transfers.
- If an uploaded copy is corrupted, stop editing it, preserve the canonical source, and label the uploaded copy non-canonical.
- Browser download history plus local hash is stronger evidence than a visual click alone.

## Common Pitfalls

1. **Calling J-space a package or agent.** It is a measured subspace; name the actual implementation and lens.
2. **Treating checksum identity as review coverage.** A checksum proves bytes, not that they were read or interpreted correctly.
3. **Inheriting old notebook errors or outputs.** Require current execution counters and outputs.
4. **Weakening VRAM thresholds.** Record capacity failure and request another runtime.
5. **Using floating Hub revisions.** Resolve and assert immutable commits.
6. **Interpreting decoded tokens psychologically.** Report ranks/logits and controls before functional inference.
7. **Downloading without authorization.** Runtime retention and local transfer are separate actions.
8. **Claiming artifact verification from notebook output alone.** Hash and completely read the downloaded primary JSON.
9. **Leaving raw activations in agent memory.** Keep numerical artifacts external and content-addressed.
10. **Integrating before controls.** A smoke-test success is not an architectural acceptance gate.

## Verification Checklist

- [ ] Canonical source directly accessed; size/hash/coverage recorded
- [ ] Disposable execution copy used
- [ ] Scope, retention, transfer, and publication gates explicit
- [ ] Actual signed-in runtime access verified
- [ ] CUDA, GPU, VRAM, precision, disk, and versions measured
- [ ] Exact model/lens/instrumentation revisions resolved
- [ ] Lens byte size and SHA-256 measured before load
- [ ] Model/lens dimensions and source layers checked
- [ ] Sparse observation and baseline executed
- [ ] Same-runtime repeatability measured
- [ ] Content-addressed artifact written and read back
- [ ] Local transfer separately authorized
- [ ] Downloaded artifact independently hashed and completely read
- [ ] Canonical source identity rechecked
- [ ] Observed facts, supported inferences, and unresolved interpretations separated
- [ ] Remaining controls and gaps reported
