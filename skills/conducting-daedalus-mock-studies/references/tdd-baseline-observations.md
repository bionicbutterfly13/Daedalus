# Skill TDD Baseline Observations

Date: 2026-08-07

Method: five isolated baseline agents were instructed not to read or use the proposed project-local skills. No mock study ran and no publication action occurred. Their outputs were compared with the approved design, then the post-skill deterministic tests exercised the frozen contracts.

## Conducting

Baseline gap: the response invented a generic state model (`Requested -> Scoped -> Specified -> Validated`) instead of the approved controller states and did not bind the four stage skills to one immutable packet, run identity, evidence verdict, and separate publication gate.

Post-skill check: `test_conducting_skill.py` verifies the exact controller transitions, the four stage-skill references, the acceptance boundary, and the human-gated publication states.

## Preparing

Baseline gap: the response invented a different YAML packet and RFC8785 conventions with unresolved placeholders. It did not preserve the approved field names, real Daedalus interface contract, exact synthetic input, or canonical artifact inventory.

Post-skill check: `test_preparing_skill.py` validates the immutable JSON packet, authorization defaults, source/interface fields, retry and stop boundaries, and publication metadata.

## Supervising

Baseline gap: the response proposed the repository checkout itself as the workspace, which violates the verified data-only workdir boundary and risks import shadowing. It also lacked the exact inspected single-shot command shape.

Post-skill check: `test_supervising_skill.py` verifies the real `EvoSci` command shape, data-only workdir, native JSONL capture, append-only ledger, unique retry paths, and no Archimedes substitution.

## Accepting

Baseline gap: the response provided sound general principles but no executable schema, canonical file names, deterministic error contract, exact Daedalus versus Archimedes authorship checks, or fixed corruption suite.

Post-skill check: `test_validator.py` exercises the valid fixture and fail-closed cases for missing, empty, mismatched, stale, corrupted, unauthorized, retried, malformed, escaped-path, silent-success, and report-integrity evidence.

## Publishing

Baseline gap: the response provided strong generic publication principles but not the approved state tokens, five exact claim classes, canonical article fields, deterministic public-content checks, or a machine-enforced stop before the human gate.

Post-skill check: `test_publishing_skill.py` verifies outcome fidelity for all four verdicts, claim evidence, privacy classes, frozen metadata, blocked invalid states, and rejection of locally self-asserted publication approval.
