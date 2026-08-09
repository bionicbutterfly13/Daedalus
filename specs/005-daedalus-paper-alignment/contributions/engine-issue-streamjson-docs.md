# Draft — engine documentation issue (template: documentation)

Title: stream-json docs say auto-mode "auto-handles" ask_user gates; the middleware is removed

**What documentation is affected**

- `docs/guides/stream-json.md`, the "Unattended by default" bullet
- The matching comment above the effective-auto-mode resolution in `EvoScientist/cli/commands.py`

**What is unclear or incorrect**

Both state that under `stream-json`, auto-mode "auto-handles" approval and `ask_user` gates.
The implementation does not answer those gates; it removes the mechanism that raises them.
`--output-format stream-json` defaults auto-mode on, auto-mode sets `enable_ask_user=False`,
and `AskUserMiddleware` is mounted only when `enable_ask_user and not auto_mode`, so the
`ask_user` tool is absent from the run. Approval interrupts are likewise removed rather than
answered from a recorded default.

The practical difference matters for a programmatic consumer. "Auto-handled" implies a
recorded decision a client could inspect or reproduce. What actually happens is that no gate
handler and no default are installed; any prompt instructing the agent to consult a user
remains as model-visible text, and the response to it is model-dependent. Nothing in the
event stream distinguishes a prompt-level question that was resolved from one that was never
raised.

**Deterministic demonstration** (configuration path only, no model involved)

1. Resolve the effective flags for a `stream-json` run without passing `--auto-mode`:
   auto-mode resolves on, and the CLI overrides set `enable_ask_user=False`.
2. Build the middleware stack with that config and list it: `AskUserMiddleware` is not
   present, because its mount condition is `cfg.enable_ask_user and not cfg.auto_mode`.

Both steps are visible in the source without executing a model turn.

**Suggested fix**

Reword both places to say that auto-mode removes the `ask_user` and approval mechanisms
rather than auto-answering them, and that prompt-level instructions to consult a user have
no handler in that mode. If it is worth documenting an alternative, note that `--no-auto-mode`
surfaces the interrupt as an event — while stating the current limitation, since the CLI
warns the run ends there and is not yet resumable.

Happy to send the wording as a PR.
