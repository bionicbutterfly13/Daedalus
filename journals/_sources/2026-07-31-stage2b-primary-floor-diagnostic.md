# Stage 2b primary-floor diagnostic source note: 2026-07-31

## Frozen diagnostic identity

| Source | Identity |
|---|---|
| Diagnostic commit | `3c26569b0d3fe4bb8a5fa79d311b231418cdb85c` |
| Diagnostic source SHA-256 | `f8bf8563ec8085ab0ca98bbf266aa93ee346ef7917abc7e5287d93d1b0edc32b` |
| Test source SHA-256 | `c6c23e0849f8eba31f2db164dce204b023e5857a1cf646cd4ddcc224e4241e0c` |
| Merge commit | `66fe6843854f380e5eec7bc17c46207c3c9c0544` |
| Pull request | `https://github.com/bionicbutterfly13/EvoScientist/pull/10` |

The diagnostic was frozen before prompt-level mechanism inspection. It binds the
canonical artifact filename and SHA-256, the canonical pilot-view filename and
SHA-256, the two floor identities, the model revision, and the fixed guard
derivation. It recomputes both floor-status trees and exact denominator
provenance before emitting a bounded JSON summary.

Independent adversarial review returned GO. Fresh local checks returned:

- `495 passed` for `tests/jspace`;
- `3553 passed, 12 skipped` repository-wide, with two unrelated deprecation
  warnings;
- Ruff lint clean;
- all 420 Python files formatted;
- `git diff --check` clean.

GitHub CI passed build, Ruff, Ubuntu Python 3.11 and 3.12, and Windows Python
3.11 and 3.12 before merge.

## Colab observation

The diagnostic was loaded into Colab's ephemeral scratch cell from the immutable
commit URL and its source SHA-256 was checked before execution. The executed
scientific notebook was not edited; its repository SHA-256 remained
`9564236a1f49d7ffe2bea44f8b04be5a584c0ff9740b11dd1e563c93b8dba2fe`.

The diagnostic stopped at its first input gate with:

```text
ValueError: required regular file is absent: /content/jspace_discrimination_s2b_pilot_d138846e7a189ad4.json
```

A second scratch-cell probe read filenames only and returned:

```text
{'required_present': {
  'jspace_discrimination_s2b_pilot_d138846e7a189ad4.json': False,
  'jspace-stage2b-pilot-v1.json': False
}}
{'content_names': ['.config', 'sample_data']}
```

Direct observation therefore establishes that neither exact input was present in
the active Colab runtime. The default-only `/content` state is consistent with a
runtime reset or replacement after pilot completion. It does not identify the
precise lifecycle event that removed the files.

## Boundaries preserved

- No artifact content was read during this diagnostic attempt.
- No pilot artifact was reconstructed, uploaded, downloaded, or transferred.
- No confirmation input was accessed.
- No threshold, gate, or scientific decision was derived.
- No prompt was added, removed, or selected.
- No pilot rule was changed or relaxed.
- The executed pilot notebook bytes were not changed.

## Scientific consequence

No association among prompt construction, tokenization, target properties,
output-to-floor geometry, or global-guard behavior was established. The options
packet specifies how those explanations could be tested lawfully, but Dr. Mani
must decide the next evidence path before any revised protocol or run is
implemented.
