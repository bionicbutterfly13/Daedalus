# Wiki Maintenance

This Wiki is a living explanatory layer, not the protocol authority.

## Source of truth

Versioned Wiki source lives under `docs/wiki/` in the main repository. GitHub's
separate Wiki repository mirrors those pages for navigation. Governing protocol,
contracts, tasks, and current state remain under `.specify/` and `specs/`.

The same curated pages are rendered at
`https://bionicbutterfly13.github.io/EvoScientist/` for search discovery. The
Pages build adds canonical metadata, a sitemap, and machine-readable navigation;
it does not become a new protocol authority.

## Update rule

Every material update should include:

- date;
- status label: observed, inferred, unknown, or authorized;
- direct repository path, run record, hash, or primary external source;
- what changed;
- what did not change;
- whether scientific inputs, gates, or artifacts were touched.

## Writing standard

Explain the mechanism with the smallest concrete example that still preserves the
real structure. Use diagrams where relationships matter. Include exact errors,
but never credentials, tokens, private prompts, or raw evidence artifacts.

Prefer:

> Torch 2.13 was active while Torchvision 0.26 remained importable. The latter
> attempted to register an operator absent from the active Torch build.

Avoid:

> Colab dependencies were broken.

The first statement can be reproduced and challenged. The second cannot.

## Scientific integrity checks

Before publishing a Wiki update:

1. Compare every numeric claim with its source.
2. Distinguish a local test from a real-runtime observation.
3. Distinguish preparation hashes from authorized hashes.
4. Keep failed attempts in the record.
5. State unknowns explicitly.
6. Do not convert engineering projections into measured runtime.
7. Do not convert evidence class 1 into a functional or cognitive claim.
8. The full stimulus manifest is public, but runtime confirmation access remains
   sealed; do not expose retained evidence artifacts or imply holdout access.

## Page map

- `Home.md`: current orientation and navigation.
- `Concepts-and-Relationships.md`: conceptual model and system relationships.
- `Global-Workspace-and-J-space.md`: theoretical motivation, operational bridge,
  and claim boundaries.
- `Stage-2b-Experiment.md`: estimand, controls, floors, and factorial design.
- `Stage-2b-Pilot-Result.md`: observed pilot result and custody boundary.
- `Primary-Floor-Decision.md`: live mechanism alternatives and decision gate.
- `Evidence-Ledger.md`: observations, inferences, and unknowns.
- `Runtime-Failure-Lab-Notes.md`: exact obstacles and repairs.
- `EvoScientist-Authorship-Incident.md`: source-isolation failure, impact, and
  restricted-authorship prevention standard.
- `Reproducibility-and-Gates.md`: source hashes, commands, and authorization chain.
- `Wiki-Maintenance.md`: this policy.

## Review cadence

Update the Wiki after:

- a ratified protocol decision;
- a changed canonical source hash;
- an authorized runtime attempt;
- a new failure boundary;
- a completed independent review;
- a pilot or confirmation decision.

Do not rewrite history when the interpretation changes. Amend the interpretation
and preserve the original observation.
