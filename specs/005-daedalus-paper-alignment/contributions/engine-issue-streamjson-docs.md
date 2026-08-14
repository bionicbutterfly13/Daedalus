# Draft: engine documentation issue (template: documentation)

Title: stream-json docs say ask_user is handled, but auto-mode disables it

**What documentation is affected?**

- `docs/guides/stream-json.md`, the "Unattended by default" bullet
- The matching auto-mode comment in `EvoScientist/cli/commands.py`

**What is wrong or missing?**

The guide says approval and `ask_user` gates are "auto-handled" when `stream-json`
enables auto-mode. Those two cases do not behave the same way.

Tool approval prompts are skipped through `auto_approve`. The `ask_user` mechanism is
disabled: the CLI sets `enable_ask_user=False`, and the middleware stack does not include
`AskUserMiddleware` when auto-mode is on. No question is raised and no automatic answer is
recorded. If a prompt tells the agent to consult a user, what happens next depends on the
prompt and model rather than a defined default answer.

The same bullet says a `--no-auto-mode` interrupt can be answered by re-invoking with
`--resume`. The CLI warning says the stream-json interrupt "is not yet resumable," so the
guide currently recommends a path the CLI says is unavailable.

This behavior is covered by two current upstream tests and can be checked without an LLM:

```bash
uv run pytest -q \
  tests/test_cli_output_format.py::test_stream_json_defaults_auto_mode_on_in_overrides \
  tests/test_ask_user.py::test_auto_mode_disables_ask_user_middleware
```

Observed on `main` at `e086f76`:

```text
2 passed
```

**Suggested improvement**

Change the guide and source comment to state that auto-mode skips tool approval prompts and
disables `ask_user`. State that `--no-auto-mode` can emit the interrupt event, but the
single-shot stream-json run ends there and cannot currently resume it. Remove the current
instruction to re-invoke with `--resume` until that path is supported.

I can send the wording change as a focused documentation pull request.
