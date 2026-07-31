# Runtime Failure Lab Notes

Failures are recorded here as experimental boundaries, not embarrassments. A
stopped run is useful when it says exactly what was tried, what passed, what
failed, and what remained untouched.

## Attempt 1: mixed NumPy process

### Setup

- exact notebook and bundle hashes authorized;
- only those two code sources uploaded;
- one Tesla T4 with 15,360 MiB allocated;
- no scientific input or evidence artifact transferred.

### Observation

```text
ImportError: cannot import name '_center' from 'numpy._core.umath'
```

The pinned install replaced NumPy on disk after Colab had already imported parts
of the old version. Metadata checks saw the new package; the process still held
a mixed module graph.

### Repair

The install cell now writes a sentinel containing:

- install schema;
- SHA-256 of the complete install specification;
- installing process identity derived from PID and `/proc/self/stat` start time.

The notebook refuses binary imports until a manual Colab session restart produces
a different process identity.

## Attempt 2: incompatible optional Torchvision

### What improved

The second run completed the install, restarted the same Colab session, proved a
fresh process, and passed package, source, commit, revision, CUDA, and excluded
input checks.

### Observation

```text
RuntimeError: operator torchvision::nms does not exist
ModuleNotFoundError: Could not import module 'Qwen3ForCausalLM'.
```

Torch 2.13 was active while Colab's Torchvision 0.26 remained discoverable.
Torchvision tried to register an operator that did not exist in the active Torch
build. Transformers' lazy model-class resolution surfaced the lower-level failure
as a missing Qwen3 class.

### Repair decision

Three options were considered:

| Option | Benefit | Cost |
|---|---|---|
| Remove Torchvision | Smallest text-only environment; no unused compiled vision surface | Must prove absence after restart |
| Pin Torchvision 0.28 | Official match for Torch 2.13 | Adds an unnecessary compiled vision wheel |
| Change Torch to 2.11 | Matches Torchvision 0.26 | Changes the explicit Torch pin and widens validation |

Dr. Mani approved removal. The new install schema binds
`remove_packages: ["torchvision"]`; the notebook uninstalls it before the pinned
stack and rejects the runtime if metadata or import resolution still sees it.

## Attempt 3: the bounded instrument path runs

The third attempt used the newly authorized canonical notebook and code bundle,
then repeated the same strict sequence: exact bundle check, one Tesla T4,
pinned install, session restart, fresh-process proof, Torchvision absence, source
identity checks, model/lens load, four-layer parity probes, and one complete
excluded-input crossing.

It completed. The core observation was small enough to understand:

```text
full crossing completed in 1.141s; peak allocated 4.074 GiB
```

That one line covers 81 distinct decoded readouts which losslessly reconstruct
64 donor-by-map factorials at layer 13. Model loading took 166.485 seconds; the
fitted lens took 4.260 seconds; capturing nine excluded inputs took 4.914
seconds; selected-layer probes took 0.042 seconds. Peak reserved memory was
4.096 GiB on a 15,360 MiB Tesla T4.

The notebook projected 6,480 readouts at 91.252 seconds by simple linear scaling.
That number is useful for engineering conversations and nothing more. It does not
include the complete pilot's orchestration, provenance, exclusions, validation,
failure recovery, or statistical work, so it is not measured pilot runtime.

The report was written inside Colab with SHA-256
`71b58ce846d319c6c26562a7765c67ab3a3468609f67306d8a767ea8f73a477c`.
It was not transferred. Cell 15 remained unexecuted. No pilot or confirmation
input was accessed.

The result answers one narrow question: the pinned Qwen model, fitted Jacobian
Lens, dual-floor capture, four selected layers, and compact 8×8 crossing can
coexist in one clean T4 runtime. It does not show that the scientific artifact
contract is ready. The adversarial review still found independent defects in
target binding, excluded-floor handling, recursive schema closure, authorization
transition, reusable tensor checks, and unratified policy isolation.

Those source defects were repaired before the separately authorized 2026-07-31
pilot. The pilot then completed operationally, but its robust result was undefined
because the primary floor missed the preregistered category-coverage minimum. See
[[Stage 2b Pilot Result]] for the scientific outcome; the smoke report described
here remains an engineering record.

## Why no live repair

Editing a running notebook would create source bytes that were never reviewed or
authorized. Reusing the old approval would hide the actual intervention. Each
repair therefore produces:

1. new canonical source;
2. new bundle and notebook hashes;
3. local tests and deterministic rebuild checks;
4. independent review;
5. a new exact authorization request.

This costs time. It also makes the result reproducible.
