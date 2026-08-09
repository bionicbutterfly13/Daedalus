---
name: verifying-hermes-external-skills
description: Verify that a Hermes profile discovers and loads skills supplied through skills.external_dirs. Use when `hermes skills list` shows a local skill but `hermes skills inspect` says "No skill named ... found", when a profile was given a new external skill directory, when a fresh skill canary returns blank output, or before claiming that an Archimedes or other Hermes profile is aware of a project-local skill.
---

# Verifying Hermes External Skills

## Problem

Hermes has two different skill-resolution surfaces. A profile can index a skill from
`skills.external_dirs` and show it as enabled, while `skills inspect` still fails to find
that name. Treating the failed inspection as proof that the skill is absent produces a false
diagnosis.

## Procedure

Use the profile alias where one exists, such as `archimedes`.

1. Parse the profile's `config.yaml` without printing secret-bearing fields. Confirm each
   configured `skills.external_dirs` path exists.
2. Run `<profile-alias> skills list`. Confirm the target name appears as `local` and
   `enabled`.
3. Build the fresh-session prompt offline:

   ```bash
   <profile-alias> --skills <skill-name> prompt-size --json |
     rg -n '"name": "<skill-name>"|"path":'
   ```

   The resulting path is the strongest offline discovery evidence. Confirm it resolves to
   the intended canonical `SKILL.md`, not a stale copy.
4. Run a fresh no-tools one-shot that asks for one fact unique to the skill. Count only a
   non-empty, source-faithful answer as the behavioral pass.
5. If the one-shot is blank, run the same one-shot without the skill as a positive control
   and inspect the profile logs. When both are blank, report profile inference as unverified;
   do not blame skill discovery without additional evidence.

## Verification

Declare offline discovery verified only when:

- the external directory exists;
- `skills list` shows the skill enabled;
- `prompt-size --json` contains the skill name and intended canonical path; and
- the canonical `SKILL.md` parses successfully.

Declare behavioral loading verified only after the fresh one-shot returns a non-empty answer
that depends on the skill. A zero exit code or empty output is not a pass.

## Example

For an Archimedes project skill, this command proves which file enters the prompt index:

```bash
archimedes --skills enforcing-daedalus-paper-parity prompt-size --json |
  rg -n 'enforcing-daedalus-paper-parity|/Volumes/Asylum/archimedes/skills/'
```

## Notes

- `skills inspect` can remain useful for registry-backed skills. Do not use its failure as
  the sole test for external local skills.
- A new session is the correct activation boundary after changing `external_dirs` or skill
  contents.
- Keep one canonical skill directory and point profiles and agent discovery surfaces to it.
  Do not copy the same skill into several runtime-owned directories.
- This behavior was verified against Hermes Agent v0.20.0 on 2026-08-09. Recheck after a
  Hermes upgrade.
