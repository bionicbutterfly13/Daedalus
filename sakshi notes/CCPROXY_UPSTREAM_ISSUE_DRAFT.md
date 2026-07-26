# DRAFT — upstream ccproxy issue (NOT FILED)

Filing this is an outward-facing action and was deliberately not performed. It is
drafted here for Dr. Mani to file, edit, or discard. Target repository: whichever
repo publishes `ccproxy_api` (installed version 0.2.10 per `uv.lock`).

Before filing, confirm the version-specific claims against the current upstream
source — everything below was verified against the locally installed 0.2.10, not
against upstream HEAD.

---

**Title:** Non-streaming Responses requests return `status: completed` with an
empty `output` array at scale

**Body:**

## Summary

When a Responses API request is made through the Codex route with
`"stream": false`, ccproxy can return a well-formed response with
`status: "completed"`, a populated `usage` block reporting nonzero output tokens,
and an **empty `output` array**. No error is raised at any layer.

Clients that faithfully parse the response then produce an empty assistant
message. In our case (LangChain's `langchain-openai`) this surfaces as
`AIMessage(content=[])` — the agent run "succeeds", the user sees nothing, and
there is no error anywhere in the stack to search for. It took a full day to
localize precisely because every layer reports success.

## Reproduction

Capture any sufficiently large agent-shaped Responses payload — ours was 37 tools
and roughly 30,000 input tokens — and replay it twice through
`/codex/v1/responses`, changing only the `stream` field. Headers, model, and body
are otherwise byte-identical.

| `stream` | Result |
|---|---|
| `false` | `status: completed`, `output` is `[]`, `usage.output_tokens: 5` |
| `true` | Full SSE: `response.output_item.added`, `response.output_text.delta`, real text, `response.completed` |

The same payload therefore succeeds or silently loses its body depending only on
the streaming flag.

Small non-streaming requests (a couple of hundred tokens, no tools) return
content correctly, so the failure appears load- or shape-dependent rather than
unconditional. **We did not establish the exact trigger** — whether it is total
payload size, tool count, generation latency, or a timing race in buffer
assembly. That is the main gap in this report and probably the first thing worth
narrowing.

## Where it appears to originate

Reading the installed 0.2.10 source, the non-streaming path assembles a reply
from the buffered stream:

- `ccproxy/streaming/buffer.py:628` calls
  `accumulator_for_rebuild.get_completed_response()`.
- `ccproxy/llms/streaming/accumulators.py:770-776` returns the captured
  `completed_response` if it is a `ResponseObject`, else `None`.
- Returning `None` is what makes `buffer.py` fall through to
  `rebuild_response_object()`, which reconstructs from the accumulated items.

If the accumulator has captured a `response.completed` event whose `output` is
empty — but has accumulated real output items — then `get_completed_response()`
returns that empty payload as a valid object, the rebuild path is never reached,
and the accumulated items are discarded. That is consistent with everything we
observed, but we have not instrumented ccproxy itself to confirm it, so treat the
mechanism as a hypothesis and the reproduction table as the evidence.

## Suggested direction

Prefer the reconstructed response whenever the captured completed event's
`output` is empty but accumulated items exist. Concretely, treat an empty
`output` the same way a missing one is treated, so the rebuild path runs. A
narrower alternative is to reconcile the two — keep the completed event's
metadata while taking `output` from the accumulator when the former is empty.

Whichever way, failing loudly would be better than the current behavior. An empty
`output` alongside nonzero `usage.output_tokens` is internally inconsistent and
could reasonably raise rather than return.

## Environment

- `ccproxy_api` 0.2.10, `ccproxy serve --port 8000`
- Route: `/codex/v1/responses` → `chatgpt.com/backend-api/codex/responses`
- ChatGPT subscription auth; `originator: codex_cli_rs`, `version: 0.145.0`
- Client: `langchain-openai` with `use_responses_api=True`
- macOS, Python 3.12

## Note for downstream readers

Client-side monkey-patching of `ResponsesAccumulator` does **not** work around
this when ccproxy runs as its own process, which is the normal deployment. The
accumulator executes in the server process; patches applied in the client process
never reach it. Our workaround was to force `stream: true` per call from the
client instead.
