"""Tests for CcproxyCodexStreamMiddleware.

Regression cover for the silent-empty-answer bug: ccproxy returns
``status: completed`` with an empty ``output`` array when it assembles a
non-streaming Responses reply, which LangChain parses into
``AIMessage(content=[])``.  The middleware forces ``stream=True`` per call
so the SSE path is used instead — and must do so *only* for the ccproxy
Codex Responses model, leaving the tool selector's structured-output copy
alone.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain.agents.middleware.types import ModelRequest
from langchain_core.messages import HumanMessage

from EvoScientist.middleware.ccproxy_stream import (
    CcproxyCodexStreamMiddleware,
    _is_ccproxy_codex_responses_model,
)


def _model(*, use_responses_api=True, base_url="http://127.0.0.1:8000/codex/v1"):
    model = MagicMock()
    model.use_responses_api = use_responses_api
    model.openai_api_base = base_url
    return model


def _request(model, model_settings=None):
    return ModelRequest(
        model=model,
        system_prompt=None,
        messages=[HumanMessage("hi")],
        tool_choice=None,
        tools=[],
        response_format=None,
        model_settings=model_settings if model_settings is not None else {},
        state={},
        runtime=None,
    )


# --- model detection -------------------------------------------------------


def test_detects_ccproxy_codex_responses_model():
    assert _is_ccproxy_codex_responses_model(_model()) is True


def test_rejects_model_without_responses_api():
    assert _is_ccproxy_codex_responses_model(_model(use_responses_api=False)) is False


def test_rejects_non_codex_openai_endpoint():
    model = _model(base_url="https://api.openai.com/v1")
    assert _is_ccproxy_codex_responses_model(model) is False


def test_rejects_local_non_ccproxy_endpoint():
    model = _model(base_url="http://127.0.0.1:8080/v1")
    assert _is_ccproxy_codex_responses_model(model) is False


def test_rejects_model_without_openai_attributes():
    """An Anthropic model has neither attribute and must not be touched."""
    model = MagicMock(spec=[])
    assert _is_ccproxy_codex_responses_model(model) is False


# --- sync wrap -------------------------------------------------------------


def test_forces_stream_true_for_ccproxy_codex():
    mw = CcproxyCodexStreamMiddleware()
    request = _request(_model())
    seen = {}

    def handler(req):
        seen["settings"] = req.model_settings
        return "response"

    assert mw.wrap_model_call(request, handler) == "response"
    assert seen["settings"]["stream"] is True


def test_preserves_existing_model_settings():
    mw = CcproxyCodexStreamMiddleware()
    request = _request(_model(), {"temperature": 0.5})
    seen = {}

    def handler(req):
        seen["settings"] = req.model_settings
        return "response"

    mw.wrap_model_call(request, handler)
    assert seen["settings"]["temperature"] == 0.5
    assert seen["settings"]["stream"] is True


def test_does_not_mutate_original_request():
    mw = CcproxyCodexStreamMiddleware()
    request = _request(_model())
    mw.wrap_model_call(request, lambda req: "response")
    assert "stream" not in request.model_settings


def test_leaves_non_ccproxy_request_untouched():
    """The tool selector's own model must not be forced into streaming."""
    mw = CcproxyCodexStreamMiddleware()
    request = _request(_model(use_responses_api=False))
    seen = {}

    def handler(req):
        seen["req"] = req
        return "response"

    mw.wrap_model_call(request, handler)
    assert seen["req"] is request
    assert "stream" not in seen["req"].model_settings


def test_respects_explicit_stream_already_set():
    mw = CcproxyCodexStreamMiddleware()
    request = _request(_model(), {"stream": True})
    seen = {}

    def handler(req):
        seen["req"] = req
        return "response"

    mw.wrap_model_call(request, handler)
    assert seen["req"] is request


# --- async wrap ------------------------------------------------------------


@pytest.mark.asyncio
async def test_async_forces_stream_true_for_ccproxy_codex():
    mw = CcproxyCodexStreamMiddleware()
    request = _request(_model())
    seen = {}

    async def handler(req):
        seen["settings"] = req.model_settings
        return "response"

    assert await mw.awrap_model_call(request, handler) == "response"
    assert seen["settings"]["stream"] is True


@pytest.mark.asyncio
async def test_async_leaves_non_ccproxy_request_untouched():
    mw = CcproxyCodexStreamMiddleware()
    request = _request(_model(base_url="https://api.openai.com/v1"))
    handler = AsyncMock(return_value="response")

    await mw.awrap_model_call(request, handler)
    assert handler.await_args.args[0] is request


# --- payload level ---------------------------------------------------------
# The middleware sets a call-time kwarg, never the instance field.  These
# tests pin the wire-level consequence: the main call streams, while the
# shared instance stays non-streaming so the tool selector's
# ``disable_streaming`` copy still sends ``stream: false``.  Setting
# ``ChatOpenAI.streaming = True`` instead would serialize ``stream: true``
# through ``_default_params`` even on the ``_generate`` path, handing a
# ``Stream`` to code that expects a completed ``Response``.


@pytest.fixture
def ccproxy_model(monkeypatch):
    monkeypatch.setenv("OPENAI_BASE_URL", "http://127.0.0.1:8000/codex/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "ccproxy-oauth")
    from EvoScientist.llm.models import get_chat_model

    return get_chat_model("gpt-5-nano", provider="openai")


def test_instance_streaming_stays_unset(ccproxy_model):
    """Constructor must not set instance-level streaming (see test_llm.py)."""
    assert "streaming" not in ccproxy_model.model_fields_set


def test_call_time_stream_true_selects_streaming_path(ccproxy_model):
    assert ccproxy_model._should_stream(async_api=False, stream=True) is True


def test_without_override_the_call_does_not_stream(ccproxy_model):
    """Reproduces the bug: no override means the lost-output path is used."""
    assert ccproxy_model._should_stream(async_api=False) is False


def test_disable_streaming_copy_still_does_not_stream(ccproxy_model):
    """The tool selector's structured-output copy must stay non-streaming."""
    safe = ccproxy_model.model_copy(update={"disable_streaming": True})
    assert safe._should_stream(async_api=False, stream=True) is False
    payload = safe._get_request_payload([HumanMessage("hi")])
    assert not payload.get("stream")
