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
- [x] T008 (F2/F8) DONE: `evolution_enforcement.py` derives which mechanisms the run owed from
      the paper's rules and compares them against the evolution reports actually written.
      IDE is owed once a tournament produced direction-summary.md; IVE on either paper
      condition (a stage exhausting its budget without meeting its gate, or stage 3 failing
      to beat the tuned baseline); ESE on ANY completed pipeline, success or not. That last
      is the F8 correction: the installed skill gates ESE on all four stages passing, which
      the paper does not, and which on the paper's own ~21% stage-3 rate would keep the
      mechanism that produced its +10.17pp from ever firing. Pinned by two tests that fail
      if the success gate is reintroduced.
- [x] T009 (F5) DONE as a prompt addendum, not a skill edit: templates/ideation-width-addendum.md
      directs the run to build the 15-21 leaf tree that research-ideation's own
      references/tree-search-protocol.md already specifies, and to record every entrant in
      direction-summary.md. Enforced by `gate_pipeline_artifacts`, which rejects a
      tournament field of 3 or fewer. Kept out of the installed skills so it carries no
      upstream merge surface; the upstream fix is drafted separately in
      contributions/evoskills-pr-ideation-tree.md.
- [x] T010 (F4) DONE: `injected_memory_entries` records which M_I/M_E entries retrieval
      selected (k_I=2 / k_E=1), making an LLM-judged choice auditable even though the
      engine has no embedding backend. Retrieval remains non-deterministic upstream; this
      records the outcome rather than fixing the mechanism.
- [x] T011 (F9) BLOCKED - not attempted, needs Dr. Mani's decision. Two reasons. (1) Which models
      to bind is a cost and provider choice nobody has made; the paper's split
      (Gemini-2.5-Pro ideation/writing, Claude-4.5-Haiku code) is the paper's, not
      necessarily this lab's. (2) It is only half-achievable regardless: the per-agent
      `model:` YAML key works for sync subagents, but async containers hardcode the main
      model except scheduler (subagents/_factory.py, expert_container_async.py), and
      writing-agent is async - so the paper's Gemini-for-writing assignment is unreachable
      without an upstream change. Editing shipped subagent YAMLs would also add upstream
      merge surface for a change of unclear value. Recommend deciding (a) whether a role
      split is wanted at all, and (b) whether to raise the async-routing gap upstream.
- [x] T012 (F13) DONE: docs/cognitive-lab-architecture.md now states that M_I/M_E receive none of
      MemoryFilesystemBackend's create/edit/delete guards because /memory/ resolves into the
      ordinary workspace, and directs that they be hashed into the evidence manifest and
      pinned in the launch record rather than trusted as memory.
## P2 — hygiene (fix directly)

- [x] T013 (F10) NO ACTION, with reasoning. "Towards Self-Evolving AI Scientists" is upstream's
      consistent branding (pyproject description AND the README typing banner), not a
      mis-citation of the paper. Our own docs cite the paper title correctly
      (docs/daedalus-paper-alignment-review.md:6). Editing an upstream-owned file would buy
      permanent merge friction for a cosmetic difference that is not a defect in this fork.
      F10 is downgraded to an upstream style observation.
- [x] T014 (F11) DONE: both links in docs/cognitive-lab-architecture.md (:122, :374) now point at
      guides/stream-json.md. A full relative-link sweep of that file also found two
      references that never existed in the working tree or anywhere in git history
      (runs/cognitive-hypothesis-lab/context-intake-2026-07-16.md and
      journals/archimedes/2026-07-16.md, the cited evidence for the July 16 episode).
      Per constitution V they are marked UNRESOLVED in place rather than silently dropped;
      the claim they support is flagged as an unsourced recollection. See T018.
- [x] T015 (D2) DONE, inverted from the original intent: the acceptance-gate section is no longer
      aspirational, so instead of marking it unimplemented it now carries per-check
      implementation status. The four checks backed by parity_gates.py are marked
      **[implemented]** with their gate names; the rest are explicitly design-only, with the
      instruction to treat an unmarked check as unperformed rather than assumed.
## Found during implementation

- [ ] T018 (new) Re-source or remove the July 16, 2026 episodic-memory account in
      docs/cognitive-lab-architecture.md. Both artifacts it cites as evidence are absent
      from the working tree and from all of git history; the passage is currently marked
      UNRESOLVED in place. Only Dr. Mani can say whether the episode happened and where
      its record went. The architectural point it illustrates does not depend on it.

## Upstream tracking (drafts written - filing needs explicit approval)

- [x] T016 Draft upstream contributions - see contributions/ (5 drafts + filing order):
      engine bug issue (F3 memory path, strengthened by upstream CONTRIBUTING.md's own
      diagram documenting /memory/ as persistent), engine docs issue (F6), EvoSkills PRs
      for memory path (T001), ESE trigger (T008), ideation tree width (T009).
- [ ] T017 On approval: file per contributions/README.md order; then implement the two
      EvoSkills PR branches on a clean EvoSkills fork following their Conventional
      Commits + skill-anatomy rules; link engine issue number into the memory-path PR.
