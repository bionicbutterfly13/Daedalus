# J-space Global Workspace Stage 2b Colab integration

This is an evidence-first engineering record for the J-space Global Workspace
Project. EvoScientist supplies runtime infrastructure; it is not the scientific
subject.

Status on 2026-07-31: real model/lens compatibility was established by the third
excluded-input smoke, and the separately authorized 20-prompt pilot completed.
The pilot was an operational success and produced a positive sensitivity-floor
signal, but the preregistered robust result is undefined because the primary
floor missed its per-category coverage requirement. No confirmation execution or
artifact transfer is authorized.

## What we are building

Stage 2b asks whether a fitted Jacobian map is specific to the correct activation,
not merely different from a geometry-matched broken map. At each prompt and layer,
the recovered instrument evaluates eight wrong-activation donor assignments
against eight broken-map draws. A factorized representation computes 81 unique
readouts and reconstructs all 64 logical donor-by-map factorials. Each readout is
evaluated against both the decoded input-embedding floor and a layer-0 residual
sensitivity floor.

The integration smoke is deliberately narrower. It uses nine fixed engineering
prompts that were locally proven disjoint from the pilot, confirmation set, prior
Stage 2 inputs, and Stage 1 anchor. It may measure API compatibility, timing, VRAM,
rank parity, transport parity, hash repeatability, and one 81-readout crossing.
It cannot calculate scientific thresholds, gates, or decisions.

## Why the execution path is hash-authorized

The canonical notebook is unexecuted and ships with both execution and transfer
flags false. A separate tool creates a disposable launch copy only after Dr. Mani
authorizes the exact notebook and code-bundle SHA-256 values. The tool changes one
execution flag, binds the authorization-record digest into notebook metadata,
keeps artifact transfer false, rejects previously executed source, and refuses to
overwrite a copy from another authorization.

This makes each GPU action answerable:

- Which source bytes were approved?
- Which code-only bundle crossed the local-to-Colab boundary?
- Which GPU capacity gate ran?
- Which inputs were reachable?
- Where did execution stop?
- Was any artifact transferred?

An earlier approval cannot authorize later repaired bytes.

## Attempt 1: filesystem versions were right, process state was wrong

The first authorized run uploaded only the notebook and bundle and allocated one
Tesla T4 with 15,360 MiB VRAM. Source, package, commit, revision, CUDA, and
excluded-input checks passed. Model loading then stopped with:

```text
ImportError: cannot import name '_center' from 'numpy._core.umath'
```

The pinned install had replaced NumPy in a Python process that already held
modules from Colab's preinstalled NumPy. Package metadata described the new
filesystem, while the process still contained a mixed module graph.

The repair introduced a content-addressed install specification and a sentinel
bound to the installing process identity. The notebook now requires Colab's
explicit **Runtime > Restart session** action and refuses all binary imports until
`/proc/self/stat` proves a different Python process.

## Attempt 2: a fresh process exposed an optional compiled-package mismatch

The second authorized run passed the bundle and T4 capacity gate, completed the
pinned install, restarted the same session, proved a fresh process, and passed all
source, package, commit, revision, CUDA, and excluded-input checks. It then stopped
before model weights loaded:

```text
RuntimeError: operator torchvision::nms does not exist
ModuleNotFoundError: Could not import module 'Qwen3ForCausalLM'.
```

The smoke pinned Torch 2.13 but retained Colab's preinstalled Torchvision 0.26.
PyTorch's official matrix pairs Torch 2.13 with Torchvision 0.28 and Torch 2.11
with Torchvision 0.26. The pinned Jacobian Lens commit does not depend on
Torchvision, and the smoke loads a text-only Qwen3 causal language model.

Dr. Mani approved the smaller contract: uninstall optional Torchvision, bind that
removal into the install-specification digest, restart, and reject the runtime if
Torchvision remains present in distribution metadata or import resolution. The
runtime report must record `torchvision_state: "absent"`.

Primary sources:

- [PyTorch and Torchvision compatibility matrix](https://github.com/pytorch/vision/blob/main/README.md#installation)
- [Pinned Jacobian Lens dependencies](https://github.com/anthropics/jacobian-lens/blob/581d398613e5602a5af361e1c34d3a92ea82ba8e/pyproject.toml)
- [Transformers optional import architecture](https://huggingface.co/docs/transformers/main/en/internal/import_utils)

## What did not happen

Across both attempts:

- no pilot or confirmatory input was accessed;
- no scientific threshold, gate, or decision ran;
- no artifact was transferred;
- no live notebook repair or fallback input was used; and
- every failure ended the authorization rather than broadening it.

Attempt 1 stopped before model download. Attempt 2 accessed model configuration
and tokenizer metadata but stopped before model-weight load; the fitted lens was
not downloaded and no runtime compatibility report was created.

## Attempt 3: the excluded-input runtime completed

The third exact-hash-authorized smoke used:

- install schema `stage2b-colab-runtime-install/v2`;
- runtime report schema `jspace-stage2b-integration-smoke/v3`;
- canonical notebook SHA-256
  `e3e0cdcfa73732138dcfaf374f9946a7993f1647cb424f8acbed91cf3ae9b5fc`;
- code-bundle SHA-256
  `4f18c96303d1451941ca050e3159e12b31b5d8d8dba4d8981a1a03e118f4cbfb`.

It completed on one Tesla T4 with 15,360 MiB VRAM. The pinned Qwen model, fitted
Jacobian Lens, dual-floor capture, and all four selected layers coexisted in one
clean runtime. One 81-readout measurement at layer 13 reconstructed all 64
logical crossings in 1.14064654 seconds. Peak CUDA allocation was 4.074223 GiB
and peak reservation was 4.095703 GiB.

The 5,172-byte runtime report remained in Colab with SHA-256
`71b58ce846d319c6c26562a7765c67ab3a3468609f67306d8a767ea8f73a477c`.
Its 91.251723-second linear projection for 6,480 readouts was an engineering
projection, not measured pilot runtime. No scientific input was opened and the
report was not transferred.

An intermediate candidate had been rejected before review because the
repository-wide format check found one Python file that Ruff would change. The
formatter was run, new bundle and notebook identities were generated, and the
rejected hashes were never authorized. This is the intended role of
pre-authorization validation: source quality failures alter preparation, not a
live GPU runtime.

## Stage 2b pilot: operational success, robust result undefined

The later pilot used canonical notebook SHA-256
`9564236a1f49d7ffe2bea44f8b04be5a584c0ff9740b11dd1e563c93b8dba2fe`,
code-bundle SHA-256
`aeec8a76a426fa82f3fb96dc6700289a689fcb92fd9952da681fe03fe12dbef4`,
pilot-view SHA-256
`5bef8316f72682a628fc1240bf6068a91aa7c8a330377206cbd9145434b797e4`,
and authorization-record SHA-256
`1af4ec95bf1c0f257fa5f559b7a91c939723cb7382eb0f5812ebc113d842b63c`.
It ran on a T4 with 14.563 GiB VRAM and produced 80 prompt-layer records across
four layers, both floors, and the full 8-by-8 crossing. The validator returned no
errors; a final Colab-side audit independently matched the artifact SHA-256 and
confirmed all 80 records. The denominator guard was
`0.3388633415411974`.

The primary `input_embedding_decoded` floor had 18 eligible prompts per layer,
but only two eligible arithmetic-completion prompts. The protocol required at
least three per category, making every primary inference undefined. The
`layer0_residual_decoded` sensitivity floor had 19 eligible prompts with category
counts 4, 4, 4, 4, and 3. Its correct effect and fitted-map interaction were
positive at layers 6, 13, 20, and 26 under both 99% interval methods. Those
defined sensitivity results cannot substitute for the failed primary-floor
coverage gate.

Threshold derivation was therefore unavailable. The pilot emitted no pass/fail
decision, and confirmation remains blocked. This directly shows prompt-floor
dependence under this protocol; generalized instrument fragility remains an
inference for the mechanism audit. It is not a robust Stage 2b result and not a
claim about global workspace function or consciousness. See the curated
[public pilot record](../runs/stage2b-pilot-public-record-20260731/README.md).

The full 200-prompt stimulus manifest was already publicly specified, but the
confirmation subset remained runtime-sealed and unaccessed. `holdout_accessed`
was false and confirmation thresholds were not ratified. The retained result
artifact contains no raw prompt text, activations, or full logits; the separately
tracked stimulus and pilot-view inputs remain part of the protocol record.

The 5.43 MiB pilot artifact was retained in Colab at run completion as
`jspace_discrimination_s2b_pilot_d138846e7a189ad4.json`, SHA-256
`d138846e7a189ad42955a5990e6d1a5c00553ba768cd838c5b6bf0334095daef`.
It was not transferred into this repository. A later check found the artifact
and pilot view absent from the active `/content` runtime before the bounded
primary-floor mechanism audit could read them. That state is consistent with a
reset or replacement, but the precise lifecycle event is unknown. The diagnostic
stopped at its exact-file gate; neither input was reconstructed or uploaded.

## Engineering lessons

1. A package-version check does not prove a coherent live process after replacing
   compiled dependencies.
2. Optional compiled packages can still break lazy import resolution when their
   metadata is visible but their operators do not match the active Torch build.
3. Content-addressed authorization turns runtime repair into a new reviewable
   source state instead of an improvised live mutation.
4. A useful smoke test is allowed to fail. Its value is the exact boundary it
   establishes without contaminating scientific inputs or evidence.
5. Runtime compatibility, pilot execution, confirmation authorization, and
   artifact transfer are separate decisions and should remain separate in code.

## Reproducing the local contract checks

From the recovery worktree:

```bash
uv run pytest \
  tests/jspace/test_stage2b_integration_smoke.py \
  tests/jspace/test_stage2b_integration_smoke_notebook.py \
  tests/jspace/test_stage2b_smoke_bundle.py \
  tests/jspace/test_stage2b_smoke_launch_copy.py -q
```

Passing these tests validates source structure only. The completed smoke and
pilot provide separate runtime evidence tied to their exact source hashes; local
tests do not authorize another GPU execution.
