# Tasks: Daedalus Paper-Alignment Remediation

Evidence for every item: docs/daedalus-paper-alignment-review.md (finding IDs cited).
Priority: P0 = blocks/invalidates unattended Hermes runs silently; P1 = scientific-behavior
divergence; P2 = hygiene.

## P0 — silent-failure killers (do first)

- [x] T001 (F3) Memory-path mitigation: DONE via option (a), workspace pinning.
      Option (b) was attempted and WITHDRAWN: boundary capture against v0.2.6 showed
      `MemoryFilesystemBackend.write()` rejects every raw write to `/memories/`, so
      repointing the skills converts silent data loss into a hard write failure. There is
      no path that is both persistent and agent-writable; that is now the upstream issue.
      Installed skills were patched, verified broken-by-design, and reverted to pristine
      (digests confirmed identical). Implemented: `scripts/memory_persistence.py`
      (`verify_persistence_config` requires an absolute, existing EVOSCIENTIST_WORKSPACE_DIR;
      `verify_shared_memory` refuses to pass on an empty store). 20 tests, including two
      that exercise live engine backends.
- [x] T002 (F3) DONE: `parity_gates.gate_memory_persistence` rejects an absent store and a
      store byte-identical to the pre-run baseline. An empty store can never pass, because
      "empty" is exactly what the skills read as "first cycle".
- [x] T003 (F12, F5) DONE: `parity_gates.gate_pipeline_artifacts` requires direction-summary,
      a tournament field larger than the retained top-3 (a field of 3 selects nothing), at
      least one experiments/stage* dir, and an evolution report. The `done` event is never
      consulted.
- [x] T004 (F6) DONE: `launch_record.py` makes the gate policy a declared, validated field
      (`GatePolicy.AUTO_SELECT_TOP1` = the paper's Extend(Top-1), or `SURFACE_TO_HERMES`
      = --no-auto-mode + resume driver). `validate_launch_record` rejects an undeclared
      policy or an uncovered decision point; `detect_gate_narration` scans the stream-json
      transcript for gates narrated instead of resolved, and the audit CLI exits nonzero
      when narration appears under the auto-select policy.
- [x] T005 (F14) DONE: `parity_gates.gate_stage_evidence_machine_checkable` requires a
      `stage-record.json` per stage (templates/stage-record.json) carrying stage, budget,
      attempts_used, best_attempt_id, gate_met. Cross-checks the paper's 20/12/12/18 budgets,
      rejects attempts over budget and gate_met with no best_attempt_id (unattributable C_best).
- [x] T006 (D1) DONE: `check_upstream_drift.py` reports ahead/behind and, more usefully, whether
      upstream touched a DIVERGENCE_FILE (needs graft-not-pick) or a FINDING_FILE (needs the
      review re-run), exiting nonzero only then. Compares against the merge base, not
      upstream/main directly: the first version diffed HEAD vs upstream and so fired on the
      fork's own permanent divergences forever -- caught by running it against the real repo,
      now pinned by test_permanent_fork_divergence_alone_needs_no_review.
## P1 — scientific divergences

- [x] T007 (F1, D3) DONE: `launch_record.build_launch_record` pins sha256 per installed skill
      dir (`skill_digest.digest_skill_tree`); `parity_gates.gate_skill_pins` rejects a run
      whose skills changed or vanished since launch, and rejects a launch record with no
      pins at all. Digest covers relative path plus bytes, so a rename is a different digest.
- [ ] T008 (F2/F8) Evolution enforcement: Hermes post-run step that runs IDE/IVE/ESE
      classification when Daedalus did not - including ESE on partial trajectories (paper
      imposes no success precondition; the success gate contradicts the paper's own +10.17pp
      mechanism).
- [ ] T009 (F5) Ideation width: prompt/packet instructs the documented 15-21 leaf tree
      (references/tree-search-protocol.md) so the Elo tournament selects from >3 candidates;
      verify via tournament table artifact (ties into T003).
- [x] T010 (F4) DONE: `injected_memory_entries` records which M_I/M_E entries retrieval
      selected (k_I=2 / k_E=1), making an LLM-judged choice auditable even though the
      engine has no embedding backend. Retrieval remains non-deterministic upstream; this
      records the outcome rather than fixing the mechanism.
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
