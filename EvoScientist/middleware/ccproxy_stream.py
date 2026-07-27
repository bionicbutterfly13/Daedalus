"""Middleware that forces streaming on the ccproxy Codex Responses API call.

ccproxy's ``StreamingBufferService`` drops the response body when it
assembles a *non-streaming* Responses reply at agent scale: the client gets
``status: completed`` with an empty ``output`` array, which LangChain
faithfully parses into ``AIMessage(content=[])`` — a silent empty answer, no
error.  A byte-identical replay of a 37-tool payload with only ``stream``
toggled returns the full SSE body and the real text, so streaming is the
only thing separating a working call from a lost one.  (Forcing Chat
Completions instead is not an escape: the same missing ``output`` surfaces
there as a 502 "Failed to convert provider response using format chain".)

The fix has to be per-call rather than per-instance.  Setting
``streaming=True`` on the shared ``ChatOpenAI`` would also reach the tool
selector's structured-output copy, which sets ``disable_streaming=True``:
that suppresses LangChain's streaming dispatch but ``_default_params`` still
serializes ``stream: true`` onto the wire, so the Responses branch of
``_generate`` would hand a ``Stream`` to code expecting a completed
``Response``.  Overriding ``model_settings`` touches only the call this
middleware wraps, leaving the selector's own model untouched.

The real defect is server-side, in ccproxy's non-streaming assembly.  It
cannot be patched from here: ccproxy runs as a separate process (see
``ccproxy_manager.start_ccproxy``), so the client-side monkey-patches in
``llm/patches.py`` never reach it.  This middleware is a deliberate
workaround, not a repair of the underlying bug.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from langchain.agents.middleware.types import (
    AgentMiddleware,
    ModelRequest,
    ModelResponse,
)

logger = logging.getLogger(__name__)


def _is_ccproxy_codex_responses_model(model: Any) -> bool:
    """Return whether ``model`` talks to ccproxy's Codex Responses endpoint.

    Checked against the model instance rather than the environment so that a
    fallback or auxiliary model pointed somewhere else is never forced into
    streaming just because the process happens to be configured for ccproxy.
    """
    if getattr(model, "use_responses_api", False) is not True:
        return False
    base_url = getattr(model, "openai_api_base", None) or ""
    return "/codex/" in str(base_url)


class CcproxyCodexStreamMiddleware(AgentMiddleware):
    """Force ``stream=True`` for ccproxy Codex Responses API model calls."""

    name = "ccproxy_codex_stream"

    def _maybe_override(self, request: ModelRequest) -> ModelRequest:
        if not _is_ccproxy_codex_responses_model(request.model):
            return request
        if request.model_settings.get("stream"):
            return request
        logger.debug(
            "CcproxyCodexStreamMiddleware: forcing stream=True "
            "(ccproxy loses non-streaming Responses output)"
        )
        return request.override(
            model_settings={**request.model_settings, "stream": True}
        )

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        return handler(self._maybe_override(request))

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        return await handler(self._maybe_override(request))
