"""Force streaming only for ccproxy Codex Responses API model calls."""

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
    """Return whether the model uses ccproxy's Codex Responses endpoint."""
    if getattr(model, "use_responses_api", False) is not True:
        return False
    base_url = getattr(model, "openai_api_base", None) or ""
    return "/codex/" in str(base_url)


class CcproxyCodexStreamMiddleware(AgentMiddleware):
    """Avoid ccproxy's silent empty non-streaming response path."""

    name = "ccproxy_codex_stream"

    def _maybe_override(self, request: ModelRequest) -> ModelRequest:
        if not _is_ccproxy_codex_responses_model(request.model):
            return request
        if getattr(request.model, "streaming", False) is True:
            return request
        logger.debug(
            "CcproxyCodexStreamMiddleware: forcing stream=True "
            "because ccproxy loses non-streaming Responses output"
        )
        # Do not add ``stream`` to model_settings. LangChain's v2 event path
        # already passes its own ``stream`` accumulator, so a call-time
        # ``stream=True`` collides with that internal argument. A per-request
        # model copy selects the streaming wire path without mutating the
        # shared model or the tool selector's separate model.
        model = request.model.model_copy(update={"streaming": True})
        return request.override(model=model)

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
