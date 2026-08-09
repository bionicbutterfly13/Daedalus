# Tasks: Daedalus Paper-Alignment Remediation

Evidence for every item: docs/daedalus-paper-alignment-review.md (finding IDs cited).
Priority: P0 = blocks/invalidates unattended Hermes runs silently; P1 = scientific-behavior
divergence; P2 = hygiene.

## P0 — silent-failure killers (do first)

- [ ] T001 (F3) Memory-path mitigation: make M_I/M_E persist across runs. Options to evaluate
      in plan: (a) launch Daedalus with EVOSCIENTIST_WORKSPACE_DIR fixed to a durable lab
      workspace; (b) patch installed skills' `/memory/` -> `/memories/` (home-dir skill edit,
      survives no reinstall - pair with T007); (c) Hermes post-run artifact sweep that copies
      `<workdir>/memory/` into the lab store and injects it on launch. Acceptance test: run A
      writes a direction, run B (fresh workdir) retrieves it.
- [ ] T002 (F3) Acceptance-gate check: after every Daedalus run, verify M_I/M_E files exist,
      grew or changed plausibly, and carry the run's cycle marker; empty-when-expected = REJECT.
- [ ] T003 (F12) Pipeline-evidence gate: acceptance requires artifacts proving the claimed
      steps ran (direction-summary, tournament table, stage logs, evolution report). `done`
      event alone is never acceptance.
- [ ] T004 (F6) Gate policy: decide per-gate policy (auto-select Top-1 like the paper, or
      surface to Hermes via --no-auto-mode + resume driver in
      skills/supervising-daedalus-mock-study-runs/scripts/drive_stream_json_resume.py).
      Record the decision in the launch record; detect gate-narration in transcripts.
- [ ] T005 (F14) Machine-checkable evidence: require the structured attempt-manifest /
      run-ledger templates (skills/supervising-daedalus-mock-study-runs/templates/) for stage
      logs so C_best, budget use, and gate status are verifiable fields, not prose.
- [ ] T006 (D1) Upstream update cadence: recurring task to fetch upstream, report
      behind/ahead + changed finding-relevant files. This sync (v0.2.3 -> V0.2.6) found two
      shipped rewrites of fork-critical code.

## P1 — scientific divergences

- [ ] T007 (F1, D3) Skill-version pinning: launch record captures sha256 of every installed
      skill dir (~/.EvoScientist/skills) used by the run; acceptance rejects unpinned runs.
      Prerequisite for T001(b)'s local skill edits.
- [ ] T008 (F2/F8) Evolution enforcement: Hermes post-run step that runs IDE/IVE/ESE
      classification when Daedalus did not - including ESE on partial trajectories (paper
      imposes no success precondition; the success gate contradicts the paper's own +10.17pp
      mechanism).
- [ ] T009 (F5) Ideation width: prompt/packet instructs the documented 15-21 leaf tree
      (references/tree-search-protocol.md) so the Elo tournament selects from >3 candidates;
      verify via tournament table artifact (ties into T003).
- [ ] T010 (F4) Retrieval determinism: record which M_I/M_E entries were injected into each
      run (k_I=2/k_E=1 selections) in the launch record so retrieval is auditable even while
      it remains LLM-judged rather than embedding-based.
- [ ] T011 (F9) Model routing: set per-agent `model:` in subagent YAMLs if/when role-split is
      wanted (sync agents only; async containers hardcode main model - track upstream).
- [ ] T012 (F13) Note in lab docs: /memory/ files carry no MemoryFilesystemBackend
      protections; treat them as ordinary artifacts in provenance (hash them in manifests).

## P2 — hygiene (fix directly)

- [ ] T013 (F10) pyproject.toml description -> paper title "Multi-Agent Evolving".
- [ ] T014 (F11) Fix docs/cognitive-lab-architecture.md links to guides/stream-json.md.
- [ ] T015 (D2) Mark the acceptance-gate section of docs/cognitive-lab-architecture.md as
      design-not-yet-implemented until T002/T003/T005 land.

## Upstream tracking (drafts written - filing needs explicit approval)

- [x] T016 Draft upstream contributions - see contributions/ (5 drafts + filing order):
      engine bug issue (F3 memory path, strengthened by upstream CONTRIBUTING.md's own
      diagram documenting /memory/ as persistent), engine docs issue (F6), EvoSkills PRs
      for memory path (T001), ESE trigger (T008), ideation tree width (T009).
- [ ] T017 On approval: file per contributions/README.md order; then implement the two
      EvoSkills PR branches on a clean EvoSkills fork following their Conventional
      Commits + skill-anatomy rules; link engine issue number into the memory-path PR.
