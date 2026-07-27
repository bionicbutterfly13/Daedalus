# Known-good bounded J-space smoke test

Use this dated reference when reproducing or comparing the Qwen3-1.7B Jacobian Lens smoke test. Re-resolve every remote resource at execution time; this file is a provenance snapshot, not a floating source of truth.

## Canonical notebook snapshot

- Prepared: 2026-07-17
- Notebook name: `jspace_colab_smoke_test.ipynb`
- Size: 16,832 bytes
- SHA-256: `9696e90ed456eae5640afbcdfa1c47d6fbabe8b50f16ff85dc0ec035a21ebe85`
- Structure: nbformat 4, 18 cells, 8 code cells
- Boundary: observation only; no fitting, steering, ablation, downstream architecture mutation, or external publication
- Optional artifact download is an explicit authorization gate

## Pinned identities

- Jacobian Lens repository: `https://github.com/anthropics/jacobian-lens.git`
- Jacobian Lens commit: `581d398613e5602a5af361e1c34d3a92ea82ba8e`
- Model: `Qwen/Qwen3-1.7B`
- Model revision: `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`
- Expected model width: 2048
- Expected model layers: 28
- Lens repository: `neuronpedia/jacobian-lens`
- Lens revision: `a4114d7752d11eb546e6cf372213d7e75526d3a1`
- Lens file: `qwen3-1.7b/jlens/Salesforce-wikitext/Qwen3-1.7B_jacobian_lens.pt`
- Lens size observed in the successful run: 226,501,315 bytes
- Lens SHA-256 observed in the successful run: `6fcc79011bd921ffd87612255e2e99950a124fa519470ee44ebaf161c39be9d6`
- Lens fit metadata reports 466 prompts recorded in the artifact

## Capacity gate

- CUDA required
- Minimum total GPU VRAM: 14.0 GiB
- Abort before model/lens downloads if the gate fails
- Do not lower the threshold solely to force completion

## Direct successful run snapshot

Run time: 2026-07-21 UTC

Runtime measured:

- GPU: Tesla T4
- Total VRAM: 14.563 GiB
- Compute capability: 7.5
- Compute dtype: `torch.bfloat16`
- CUDA runtime: 12.8
- Driver: 580.82.07
- Python: 3.12.13
- Torch: 2.11.0+cu128
- Transformers: 5.13.1
- Hugging Face Hub: 1.23.0
- Free disk before large downloads: 65.904 GiB

Observation measured:

- Schema: `jspace-observation-smoke-test/v1`
- Scope: `open_loop_observation_only`
- Run ID: `130ac89c-bdad-42b5-9bd0-b4b55c9c51ff`
- Input token count: 13
- Input UTF-8 bytes: 60
- Raw prompt persisted: false
- Selected layers: 6, 13, 20, 26
- Position: -2
- Top-k: 10
- Same top-k token IDs across same-runtime repeats: true
- Maximum Jacobian-logit difference: 0.0
- Maximum model-logit difference: 0.0
- Raw activations persisted: false
- Full logits persisted: false

Downloaded primary artifact:

- Filename: `jspace_observation_b76896e2b441d06b.json`
- Size: 13,075 bytes
- SHA-256: `b76896e2b441d06b1e6183b7fee34ba9be8b19b2eead566707726edd1d4e76f9`
- Direct coverage: complete JSON, 599 lines
- Local checksum matched the runtime-reported checksum

## What this establishes

The exact model/lens pair produced sparse Jacobian and logit-lens readouts on one T4 runtime. Repeated application within that runtime produced identical top-k token IDs and zero maximum logit differences for the measured layers and position.

## What this does not establish

- cross-runtime or cross-hardware reproducibility;
- calibrated probabilities or construct-level uncertainty;
- predictive validity beyond one synthetic prompt;
- causal mediation;
- functional global-workspace properties;
- subjective or phenomenal consciousness;
- readiness for Sakshi, Elume, or other observer integration.

## Operational lessons

1. Current execution counters and outputs must replace inherited notebook output as evidence.
2. Hosted notebook file transfers require a separate authorization and independent local hash.
3. Colab's runtime file browser can transfer a verified artifact when code-cell automation is unreliable.
4. Direct AX value replacement is unsafe for Colab CodeMirror cells. During the successful run it visually changed the target cell but concatenated text into another cell and executed stale kernel-side code. Treat the affected uploaded copy as non-canonical.
5. Preserve and re-hash the local canonical notebook; repair or replace disposable uploaded copies rather than trusting their visual state.
