---
name: publishing-daedalus-study-journals
description: Use when preparing a public-safe Daedalus study article.
version: 0.1.0
author: Dr. Mani, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [research, publication, privacy, daedalus]
    related_skills: [accepting-daedalus-mock-study-evidence]
---

# Publishing Daedalus Study Journals

Prepare a public-safe article from the Daedalus primary report and Archimedes independent evidence report after a terminal study verdict. Article preparation does not publish or authorize an outward action.

## When to Use

Use after independent acceptance assigns `accepted`, `partial`, `failed`, or `stopped`. Any terminal outcome may be documented, but the article must preserve that exact outcome and disclose what did not run or could not be verified.

## Prerequisites

- Frozen publication fields from the study packet.
- Direct access to the Daedalus report and Archimedes evidence report.
- Terminal evidence verdict.
- Public/private artifact inventory and redaction rules.
- No unresolved claim, privacy, authorship, destination, or correction-policy conflict.

## Procedure

1. Copy `templates/public-journal-article.json` and preserve the frozen title, destination, and authorship.
2. Populate every required section from the two reports. Do not invent missing Daedalus scientific content.
3. Classify every material claim as `verified_execution`, `observed_result`, `supported_inference`, `hypothesis`, or `unknown`.
4. Attach a public evidence reference or SHA-256 content hash to every material claim.
5. Remove credentials, secrets, private memory, private research data, hidden prompts, unsafe internal paths, sensitive logs, unsupported claims, consciousness claims, and claims of universal Daedalus validation.
6. Set the exact terminal study outcome and run the deterministic publication validator.
7. Record `publication_prepared`, then `awaiting_dr_mani_approval`. Request explicit approval from Dr. Mani after review.
8. Without that explicit approval, stop. Do not publish, send, upload, or change the state to `published`.
9. If approved later, record a separate `publication-approval.json` naming Dr. Mani, the explicit decision and timestamp, and the exact article SHA-256.
10. Recheck the destination and correction procedure immediately before the separately authorized outward action.

Completion criterion for this skill: a validated public-safe article is awaiting approval or accurately marked declined/blocked. Publication itself is outside the current authorization unless Dr. Mani explicitly authorizes it after review.

## Pitfalls

- `accepted` does not mean every Daedalus function works.
- A partial, failed, or stopped study can still be useful, but its article cannot claim success.
- A checksum proves byte identity, not scientific correctness.
- An intended destination is not publication approval.
- Hidden prompts and sensitive logs stay private even when they explain a failure.

## Verification

- Run `validate_publication` through the acceptance validator.
- Confirm article outcome equals the Archimedes verdict.
- Confirm every claim has an evidence reference or content hash.
- Confirm forbidden public classes are absent.
- Confirm `publication_authorized` is false and no outward action occurred.
