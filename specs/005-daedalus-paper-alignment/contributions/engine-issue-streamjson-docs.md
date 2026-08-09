# Draft — engine documentation issue (template: documentation)

Title: stream-json docs say auto-mode "auto-handles" ask_user gates; auto-mode actually
removes the ask_user tool

**What is wrong**
Both the stream-json guide and the CLI comment state that headless auto-mode
"auto-handles" approval and `ask_user` gates. The implementation disables
`enable_ask_user`, which removes AskUserMiddleware from the composition — the ask_user
tool does not exist in the run. Prompt-mandated questions (e.g. workflow steps that
instruct the agent to ask the user and "not assume a default silently") are neither asked
nor answered by any recorded policy; the model improvises. For orchestrators driving
stream-json programmatically, "gate was auto-answered with default X" and "gate never
existed" are materially different contracts — the current wording claims the former while
the code implements the latter, and nothing in the event stream lets a consumer tell
which prompts were silently dropped.

**Where**
- docs/guides/stream-json.md, "Unattended by default" bullet
- cli/commands.py comment above the effective-auto-mode resolution
- Middleware gate: AskUserMiddleware only mounts when `enable_ask_user and not auto_mode`

**Suggested fix**
Reword both to: auto-mode removes the ask_user tool entirely; instructions to consult the
user become inert prompt text; behavior at prompt-level decision points is model-dependent.
Optionally document `--no-auto-mode` + resume as the only path that surfaces gates, with
its current single-shot limitation. Happy to PR the wording.
