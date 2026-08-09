# Feature Specification: Daedalus Paper-Alignment Remediation

**Feature ID**: 005-daedalus-paper-alignment
**Created**: 2026-08-09
**Status**: Draft
**Evidence base**: [docs/daedalus-paper-alignment-review.md](../../docs/daedalus-paper-alignment-review.md)
(14 findings, twice Codex-verified: v0.2.3 tree `3339a11`, re-confirmed post-V0.2.6 merge `57e144e`)

## Problem

Daedalus (this EvoScientist fork, wrapped and CLI-driven by Hermes) does not implement the
accumulation mechanism its paper (arXiv 2603.08127v1) claims: memories are written to a
per-workspace path instead of the persistent store (F3), nothing enforces the pipeline or the
evolution mechanisms (F12, F2, F8), human decision gates dissolve silently under the headless
driver (F6), and run evidence is not machine-checkable (F14). A run can start from zero,
skip the science, answer its own gates, and still report success. This is the silent-success
failure mode the lab constitution treats as a bug.

## Scope split

- **Upstream defects** (engine: F2, F3, F4, F6, F12; skills: F1, F5, F8, F13, F14): we do not
  own these codebases. Items below either mitigate locally at the Hermes boundary or track an
  upstream report. Filing upstream issues requires Dr. Mani's explicit approval per hard
  boundaries.
- **Fork defects** (F10, F11): fix directly.
- **Deployment gaps** (D1-D3): ours regardless of upstream — the wrapper must make upstream's
  failures loud.

## Success criteria

1. Two consecutive Daedalus runs in different workdirs demonstrably share M_I/M_E, or the
   acceptance gate fails loudly when they do not (kills F3's silent mode).
2. A Hermes-driven run cannot be accepted unless the launch record pins skill versions and the
   evidence includes machine-checkable stage artifacts (kills F1/F14 silent modes).
3. Selection gates (idea Top-3, code-generation mode) are either resolved by recorded policy or
   surfaced to Hermes as events - never silently dropped (kills F6's silent mode).
4. Fork defects F10, F11 fixed.

## Contribution lane

Implementation follows two standing rules:

1. **Update-proof by construction**: remediation lives in layers upstream does not own
   (Hermes acceptance gates, our supervising/accepting skills, launch records, env-var
   config). Only T009/T011 touch upstream-owned files; both are small and covered by the
   fork-merge protection pattern (inverted tests + divergence markers).
2. **Contribute while implementing**: fixes that are upstream-shaped are drafted under
   [contributions/](contributions/) in upstream's own protocol format (engine: issue-first,
   PR template, ruff+pytest; EvoSkills: Conventional Commits, skill anatomy). Drafts only;
   filing requires explicit approval.

## Out of scope

- Reimplementing the paper's method (embedding retrieval, EMA agent, N_I=21 tree) inside the
  engine - upstream's job, tracked not built.
- GPU work; anything touching Stage 2b authorization (separate governance).
