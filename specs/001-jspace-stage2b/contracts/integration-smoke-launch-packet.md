# Stage 2b excluded-input Colab integration-smoke launch packet

Status: **COMPLETED ON THIRD EXACT-HASH-AUTHORIZED ATTEMPT; AUTHORIZATION SPENT**

This packet records preparation and execution evidence. The completed
authorization does not authorize a repeat browser upload, another Colab GPU
allocation, runtime-report transfer, scientific decision, pilot, confirmation,
publication, commit, push, or merge.

## Canonical sources

| Source | Size | SHA-256 |
|---|---:|---|
| `j-space-lab/jspace_colab_stage2b_integration_smoke.ipynb` | 30,799 bytes | `e3e0cdcfa73732138dcfaf374f9946a7993f1647cb424f8acbed91cf3ae9b5fc` |
| `runs/stage2b-integration-smoke-torchvision-repair-v2-20260730/stage2b_integration_smoke_bundle.zip` | 22,964 bytes | `4f18c96303d1451941ca050e3159e12b31b5d8d8dba4d8981a1a03e118f4cbfb` |

The code-only bundle contains exactly:

| File | Size | SHA-256 |
|---|---:|---|
| `stage2b_endpoint.py` | 23,009 bytes | `46086a02ed66a60d508813f253399149a6fe3f31fc9d6a18466fe77990515573` |
| `stage2b_preflight.py` | 38,577 bytes | `0248d2f28cc6e72afc7cefc55e581d93783cf8824c80a248d8583f1a257cf275` |
| `stage2b_integration_smoke.py` | 13,746 bytes | `b1297362205e90d26e2ced85d98749559705ab1d8610e423346d9d30c96bb46c` |

The bundle excludes pilot/confirmatory prompts, credentials, model/lens weights,
and runtime artifacts. Its deterministic builder refuses to overwrite different
bytes at an existing output path.

## First authorized attempt

Dr. Mani authorized the earlier notebook/bundle identities on 2026-07-29. Codex
uploaded only those two code sources and allocated one Tesla T4 with 15,360 MiB
VRAM. The bundle, capacity, exact package versions, Jacobian Lens commit, model
revision, lens revision, and nine excluded inputs passed their runtime checks.

Model loading then stopped in cell 9 with:

```text
ImportError: cannot import name '_center' from 'numpy._core.umath'
```

The pinned NumPy replacement had completed in a Python process that already held
NumPy modules from Colab's original runtime. No live repair was attempted. No
pilot or confirmatory input was accessed, no compatibility report was generated,
and no artifact was transferred. The direct observation record is
`runs/stage2b-integration-smoke-repair-20260729/first-authorized-attempt-failure.json`
(SHA-256
`4a0f2b2fbacd38a2583d4bfcbb8a6ccbdd7831e696ec0aa6feaf66f1feb0c9ce`).

The first repair records an install-specification digest and the installing
process identity, then requires a different `/proc/self/stat` process identity
before any NumPy, Torch, Transformers, or Jacobian Lens import.

## Second authorized attempt

Dr. Mani authorized the first repaired notebook/bundle identities on 2026-07-30.
The disposable notebook and code bundle were uploaded to one Tesla T4 with
15,360 MiB VRAM. The install completed, the same Colab session restarted, and
the fresh-process, package-version, source-bundle, instrumentation-commit,
model-revision, lens-revision, CUDA, and excluded-input checks passed.

Model class resolution then stopped in cell 9 before model-weight load:

```text
RuntimeError: operator torchvision::nms does not exist
ModuleNotFoundError: Could not import module 'Qwen3ForCausalLM'.
```

The pinned Torch 2.13 runtime retained Colab's preinstalled Torchvision 0.26.
PyTorch's compatibility matrix pairs Torch 2.13 with Torchvision 0.28 and
Torch 2.11 with Torchvision 0.26. The pinned Jacobian Lens package depends on
Torch, Hugging Face Hub, Transformers, and NumPy, not Torchvision. Dr. Mani
therefore approved the smaller text-only contract: remove Torchvision before
the pinned install and require it to be absent after restart.

No live repair was attempted. No model weights or fitted lens were loaded, no
pilot or confirmatory input was accessed, no compatibility report was created,
and no artifact was transferred. The direct failure record is
`runs/stage2b-integration-smoke-repair-20260729/second-authorized-attempt-failure.json`
(SHA-256
`16c4128f9754940726d73dec398a50d75455b3961e38aad2d4d16c5c3503693e`).

The current repair binds `remove_packages: ["torchvision"]` into install schema
`stage2b-colab-runtime-install/v2`, executes an explicit uninstall before the
pinned install, and rejects the post-restart runtime if distribution metadata
or import resolution still exposes Torchvision. The runtime-only report schema
is now `jspace-stage2b-integration-smoke/v3` and requires both
`fresh_process_after_install: true` and `torchvision_state: "absent"`.

## Third authorized attempt: runtime compatibility established

Dr. Mani authorized the canonical notebook and bundle identities listed above.
The disposable launch copy ran on one Tesla T4 with 15,360 MiB VRAM. After the
pinned install and required session restart, the run verified:

- exact pinned package versions and Torchvision absence;
- exact source-bundle, Jacobian Lens commit, model revision, lens revision,
  fitted-lens file, and fitted-lens SHA-256 identities;
- nine excluded-input identities with no pilot/confirmation overlap;
- rank-convention and transport parity;
- all four selected layers; and
- one complete 81-readout/64-logical-crossing measurement at layer 13.

Observed timings and memory:

| Measurement | Observation |
|---|---:|
| model load | 166.485052 s |
| fitted-lens load | 4.259576 s |
| nine-input capture | 4.914328 s |
| selected-layer probes | 0.041844 s |
| 81-readout crossing | 1.140647 s |
| peak CUDA allocation | 4.074223 GiB |
| peak CUDA reservation | 4.095703 GiB |

The linear 81-to-6,480-readout projection was 91.251723 seconds. It remains
labelled `engineering_projection_not_measured_pilot_runtime`; it is not a wall
clock estimate for the complete pilot.

The content-addressed report remains in the Colab runtime at
`/content/jspace_stage2b_integration_smoke/stage2b_integration_smoke_71b58ce846d319c6.json`.
Its SHA-256 is
`71b58ce846d319c6c26562a7765c67ab3a3468609f67306d8a767ea8f73a477c`
and its recorded size is 5,172 bytes. Cell 15, the optional transfer cell, was
confirmed unexecuted. The report was not downloaded or copied into this
repository. No pilot or confirmation input was accessed.

This closes runtime compatibility only. It does not close the independent
pilot-readiness findings in the measurement producer, schema, validator,
authorization transition, reusable preflight contract, or unratified policy
surface.

## Fixed excluded inputs

The smoke module carries nine engineering-only inputs: one recipient and eight
donors. Local preparation recomputed their text digests and confirmed zero overlap
with:

- all 200 Stage 2b source prompts;
- the ratified 20-prompt pilot view;
- the Stage 2 input digests; and
- the Stage 1 anchor.

Their SHA-256 identities are:

```text
283df7363258df881528f130b9cf709a8f2ce39d831693c9112efc337377d3cd
d7a50d62a254b46366c603bd31d1ddd8e5ab372b0429778aa887421cf5ae0e9f
5c0e1c22487e3b640bc6eda44850f499e3b32f093a47009e226366823ac81f19
d5741e8d4d3d236ea26e3b277642bcf7b62c7f0ab9fdff395a9128a1cfc68fe1
e3fca3f0b6fa3f34771692f0592478008a3224d89054163d8bd798910d8800b6
7e8884e020fff1cc4e7a1cb2c054066ff05a90de4daf237b6e1c8392c50e682b
f83637836e94d4062b41d2a1b7589c46c2a499c0e6c006b034744ac00cd8491d
c7b252aed3ee5d11369430cbcfdd0c754161892fcbacda6b95178c390bb29daa
bb9c2752055cb9a9c832a07c707048f1369b1752215744a1e1bf88b337ef39a7
```

The smoke-only donor seeds are `(0, 1, 3, 4, 8, 9, 16, 30)` and map seeds are
`5000` through `5007`. They live only in the integration-smoke module. The pilot
registries remain empty and unratified.

## Bounded runtime action

After separate authorization:

1. Recompute the canonical notebook and bundle hashes locally.
2. Record Dr. Mani's exact hash-specific approval in a local content-addressed
   authorization record. The record must preserve the approved notebook/bundle
   hashes, GPU floor, excluded-input scope, and transfer=false boundary.
3. Create the disposable notebook copy with
   `authorize_stage2b_integration_smoke_notebook.py`, passing the authorization
   record's SHA-256. The tool verifies the canonical notebook hash, changes only
   `INTEGRATION_SMOKE_AUTHORIZED = False` to `True`, adds the authorization-record
   digest to notebook metadata, preserves `ARTIFACT_TRANSFER_AUTHORIZED = False`,
   rejects executed source, and refuses overwrite.
4. Record the disposable copy's size and SHA-256.
5. Use the already authenticated browser session to open one Google Colab
   notebook and connect one GPU runtime.
6. Upload only the disposable notebook and the hash-bound code-only bundle.
7. Execute the authorization/constants, bundle/capacity, and pinned-install cells
   sequentially while checking current execution counters and outputs.
8. After the first successful pinned install, use Colab's
   **Runtime → Restart session** action. Reconnect the same runtime, rerun the
   authorization/constants, bundle/capacity, and install-sentinel cells, and
   require the recorded installing process identity to differ from the current
   process identity. Do not continue in the installing process.
9. Stop before model/lens downloads unless:
   - exactly one NVIDIA GPU is visible;
   - total VRAM is at least 14 GiB;
   - the uploaded bundle SHA-256 matches; and
   - the exact pinned package versions install successfully in a process that is
     then replaced and independently verified; and
   - Torchvision is absent by both installed-distribution metadata and import
     resolution before Transformers is imported.
10. Load only the pinned Qwen3-1.7B model, Jacobian Lens commit, and fitted-lens
   revision/file/hash.
11. Capture the nine excluded prompts, probe all four selected lens layers, and run
   one complete 81-readout/64-logical-cell crossing at layer 13.
12. Retain the content-addressed compatibility report in the ephemeral Colab
    runtime. Do not execute the transfer cell.
13. Recompute the local canonical notebook and bundle hashes after the run.

## Measurements permitted

- current Python/package/CUDA/GPU identities;
- model and fitted-lens load times;
- nine-prompt capture time;
- all-selected-layer parity-probe time;
- one complete 81-readout crossing time;
- peak allocated and reserved VRAM;
- rank and transport parity;
- repeatability of live residual/map content hashes;
- exact 81/64 counts; and
- a labeled linear 81-to-6480 engineering projection.

The projection is not measured pilot runtime and cannot be presented as one.

## Stop conditions

Stop without substitution or repair in the live runtime if:

- authentication, quota, payment, 2FA, or permission is requested;
- the browser cannot target the exact Colab notebook;
- the GPU is absent, plural, or below 14 GiB;
- any local/uploaded source hash differs;
- a pinned package, model, lens, or instrumentation identity differs;
- the install sentinel is missing, malformed, bound to another install
  specification, or still identifies the current Python process;
- Torchvision remains installed or importable after the pinned install and
  required restart;
- model/lens dimensions, source layers, dtype, rank parity, or transport parity
  fails;
- an input is not one of the nine smoke hashes;
- 81 unique readouts or 64 logical cells do not materialize;
- raw prompts, activations, or full logits would be persisted;
- a scientific gate, threshold, decision, pilot field, or confirmatory field
  appears; or
- the runtime asks to transfer/download the report without separate authorization.

Do not swap hardware, weaken pins, lower the VRAM floor, change package versions,
choose different seeds, repair live notebook cells, or fall back to pilot inputs.
Return the exact failure evidence for a new decision.

## Acceptance evidence

Preparation is ready for authorization only when:

- the complete J-space suite, full repository suite, Ruff, format, and diff checks
  pass after this packet;
- the canonical notebook contains no outputs/execution counts and parses;
- its static tests prove both authorization flags false, no scientific input path,
  exact bundle binding, full-cross calls, VRAM/timing capture, runtime-only schema,
  fresh-process enforcement, install-specification binding, Torchvision removal
  and absence enforcement, and transfer refusal;
- the bundle rebuild is deterministic; and
- independent Archimedes review returns ACCEPT for launch preparation.

Runtime success later requires the notebook's final JSON summary with report
path/hash/size, timings, projection label, and peak VRAM. That UI evidence is
enough for the compatibility decision; downloading the report remains a separate
authorization.

## Spent authorization text

The third attempt was authorized with the following exact text. It is retained
for provenance and MUST NOT be reused:

> Authorize the excluded-input Stage 2b Colab integration smoke using canonical
> notebook SHA-256
> `e3e0cdcfa73732138dcfaf374f9946a7993f1647cb424f8acbed91cf3ae9b5fc`
> and code-bundle SHA-256
> `4f18c96303d1451941ca050e3159e12b31b5d8d8dba4d8981a1a03e118f4cbfb`,
> including upload of those two code-only sources and allocation of one Google
> Colab GPU with at least 14 GiB VRAM. Retain the runtime report in Colab; do not
> access pilot/confirmatory inputs or transfer any artifact.

Silence, earlier generic authorization, prior pilot decisions, and approval of
this preparation packet do not authorize another run.
