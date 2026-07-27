# J-space Colab smoke-test provenance

Date prepared: 2026-07-17
Workspace: `/Volumes/Asylum/archimedes`
Artifact: `sakshi notes/jspace_colab_smoke_test.ipynb`

## Source accessed directly in this session

1. Anthropic `jacobian-lens` repository
   - URL: https://github.com/anthropics/jacobian-lens
   - Access: shallow Git clone and direct file inspection
   - Commit: `581d398613e5602a5af361e1c34d3a92ea82ba8e`
   - Coverage: complete README; complete `pyproject.toml`; extracted complete walkthrough notebook; complete `jlens/lens.py`; complete `jlens/hf.py`. The whole repository was not reviewed.

2. Qwen3-1.7B model metadata
   - URL: https://huggingface.co/Qwen/Qwen3-1.7B
   - Access: Hugging Face model API and pinned `config.json`
   - Revision: `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`
   - Verified metadata: Qwen3 causal-LM architecture, 28 layers, hidden size 2048, BF16 declaration. Model weights were not downloaded or executed in this local session.

3. Neuronpedia Jacobian lens metadata
   - URL: https://huggingface.co/neuronpedia/jacobian-lens
   - Access: Hugging Face model API, pinned fit `config.yaml`, and lens-file HTTP headers
   - Revision: `a4114d7752d11eb546e6cf372213d7e75526d3a1`
   - File: `qwen3-1.7b/jlens/Salesforce-wikitext/Qwen3-1.7B_jacobian_lens.pt`
   - Observed remote size: 226,501,315 bytes
   - Fit metadata reports 466 prompts actually fitted despite the command requesting up to 1000; this distinction is preserved.
   - The lens binary was not downloaded or deserialized locally. The notebook computes its SHA-256 after download in Colab.

## Derivative context used

The prior Archimedes session recommendation and local Sakshi/Elume planning notes were used to define the bounded scope: observation only, no fitting, steering, or architecture mutation.

## Verification performed before GPU execution

- Parsed the notebook as JSON and verified nbformat 4 structure: 18 cells total.
- Syntax-compiled all 8 Python code cells after neutralizing the one Colab `%pip` magic line.
- Executed the pure pinned-configuration cell in isolation.
- Re-resolved both pinned Hugging Face revisions through the live Hub API and confirmed exact matches.
- Notebook SHA-256 after validation: `9696e90ed456eae5640afbcdfa1c47d6fbabe8b50f16ff85dc0ec035a21ebe85`.

## Direct Colab execution

Date executed: 2026-07-21 UTC

Access method: the canonical notebook was copied byte-for-byte to a disposable upload file, uploaded through Brave to Google Colab, and executed cell-by-cell in a connected GPU runtime. Current execution counters and outputs were checked after each cell. Cells 1–7 were run in sequence; optional download cell 8 was initially left unexecuted and was run only after Dr. Mani separately authorized artifact transfer.

Runtime measured directly:

- GPU: Tesla T4
- Total VRAM: 14.563 GiB; the 14 GiB fail-fast threshold passed
- Compute capability: 7.5
- Compute dtype: `torch.bfloat16`
- Driver: 580.82.07
- CUDA runtime: 12.8
- Python: 3.12.13
- Torch: 2.11.0+cu128
- Transformers: 5.13.1
- Hugging Face Hub: 1.23.0
- Free disk before large downloads: 65.904 GiB

Pinned artifact identities verified in the runtime:

- Jacobian Lens commit: `581d398613e5602a5af361e1c34d3a92ea82ba8e`
- Qwen3-1.7B revision: `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`
- Fitted-lens revision: `a4114d7752d11eb546e6cf372213d7e75526d3a1`
- Fitted-lens size: 226,501,315 bytes
- Fitted-lens SHA-256: `6fcc79011bd921ffd87612255e2e99950a124fa519470ee44ebaf161c39be9d6`
- Model width/layer count, lens width, and lens source-layer compatibility assertions completed without error.

Observation measured directly:

- Schema: `jspace-observation-smoke-test/v1`
- Scope: `open_loop_observation_only`
- Run ID: `130ac89c-bdad-42b5-9bd0-b4b55c9c51ff`
- Input size: 60 UTF-8 bytes and 13 tokens; raw prompt not persisted
- Selected layers: 6, 13, 20, 26
- Position: -2
- Top-k: 10
- Same top-k token IDs across same-runtime repeats: true
- Maximum Jacobian-logit difference: 0.0
- Maximum model-logit difference: 0.0
- Raw activations and full-vocabulary logits not persisted

## Downloaded primary artifact

- Runtime path: `/content/jspace_artifacts/jspace_observation_b76896e2b441d06b.json`
- Local source accessed directly: `~/Documents/jspace_observation_b76896e2b441d06b.json`
- Access method: Colab Files panel download, local SHA-256 computation, direct UTF-8 JSON extraction
- Coverage: complete JSON, 599/599 lines
- Size: 13,075 bytes
- Runtime and local SHA-256: `b76896e2b441d06b1e6183b7fee34ba9be8b19b2eead566707726edd1d4e76f9`
- The local checksum matched the runtime-reported checksum.
- The downloaded primary artifact remains outside this repository and is not included in the publication packet.

## Skill and repository verification

- Added `EvoScientist/skills/jspace-research-operations/` with an operating protocol, dated baseline reference, evidence-report template, and standard-library artifact validator.
- The validator accepted the downloaded primary artifact with zero errors.
- A negative test with a deliberately incorrect expected checksum returned failure as intended.
- Full repository suite: `uv run pytest`: 2,697 passed, 10 skipped, one pre-existing Starlette/httpx deprecation warning.
- Canonical notebook identity after execution and download workflow: 16,832 bytes; SHA-256 `9696e90ed456eae5640afbcdfa1c47d6fbabe8b50f16ff85dc0ec035a21ebe85`.

## Incident and source preservation

Direct accessibility value replacement in Colab's CodeMirror editor visually changed the intended download cell but concatenated text into cell 1 of the disposable uploaded copy and executed stale kernel-side code. The artifact was instead transferred through Colab's Files panel. Treat the uploaded Colab copy as non-canonical. The local canonical notebook remained unchanged and is the only notebook authorized for publication.

## Remaining gaps

- The 14 GiB threshold passed on one T4 but remains a conservative smoke-test gate, not a measured exact minimum.
- Same-runtime repeatability does not establish cross-runtime or cross-hardware reproducibility.
- The synthetic prompt does not establish predictive or construct validity.
- No random-vector, non-J-space, prompt-only, output-only, or causal-intervention controls have run.
- No claim about functional global-workspace properties, subjective experience, or phenomenal consciousness is supported.
- Sakshi/Elume or other observer integration readiness remains unverified.
