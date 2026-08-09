# Daedalus Mock Study Skills

This directory is the only canonical source for the five project-local skills that govern the first synthetic Daedalus vertical acceptance study:

1. `conducting-daedalus-mock-studies`
2. `preparing-daedalus-mock-studies`
3. `supervising-daedalus-mock-study-runs`
4. `accepting-daedalus-mock-study-evidence`
5. `publishing-daedalus-study-journals`

Daedalus means the customized EvoScientist system. Archimedes is the Hermes profile and governance envelope managing Daedalus.

The `.agents/skills/` and local `.claude/skills/` entries are relative symbolic links to these directories. They are discovery surfaces, not copies. Hermes is configured to scan this canonical `skills/` directory directly. Codex uses `.agents/skills/`; Claude uses its local `.claude/skills/` surface. Edit only files under `skills/`.

The deterministic tests use synthetic fixtures only. They do not launch Daedalus, activate providers, access private memory, modify EvoScientist core, transfer artifacts, or publish.
