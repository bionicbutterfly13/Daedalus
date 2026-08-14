"""Regression tests for the ccproxy silent-empty-answer workaround."""

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
    model.streaming = False

    def model_copy(*, update):
        copied = MagicMock()
        copied.use_responses_api = model.use_responses_api
        copied.openai_api_base = model.openai_api_base
        copied.streaming = update.get("streaming", model.streaming)
        return copied

    model.model_copy.side_effect = model_copy
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
    model = MagicMock(spec=[])
    assert _is_ccproxy_codex_responses_model(model) is False


def test_forces_stream_true_for_ccproxy_codex():
    middleware = CcproxyCodexStreamMiddleware()
    request = _request(_model())
    seen = {}

    def handler(req):
        seen["request"] = req
        return "response"

    assert middleware.wrap_model_call(request, handler) == "response"
    assert seen["request"].model.streaming is True
    assert "stream" not in seen["request"].model_settings


def test_preserves_existing_model_settings():
    middleware = CcproxyCodexStreamMiddleware()
    request = _request(_model(), {"temperature": 0.5})
    seen = {}

    def handler(req):
        seen["request"] = req
        return "response"

    middleware.wrap_model_call(request, handler)
    assert seen["request"].model_settings == {"temperature": 0.5}
    assert seen["request"].model.streaming is True


def test_does_not_mutate_original_request():
    middleware = CcproxyCodexStreamMiddleware()
    request = _request(_model())
    original_model = request.model
    middleware.wrap_model_call(request, lambda req: "response")
    assert request.model is original_model
    assert request.model.streaming is False
    assert "stream" not in request.model_settings


def test_leaves_non_ccproxy_request_untouched():
    middleware = CcproxyCodexStreamMiddleware()
    request = _request(_model(use_responses_api=False))
    seen = {}

    def handler(req):
        seen["req"] = req
        return "response"

    middleware.wrap_model_call(request, handler)
    assert seen["req"] is request
    assert "stream" not in seen["req"].model_settings


def test_respects_model_already_configured_for_streaming():
    middleware = CcproxyCodexStreamMiddleware()
    model = _model()
    model.streaming = True
    request = _request(model)
    seen = {}

    def handler(req):
        seen["req"] = req
        return "response"

    middleware.wrap_model_call(request, handler)
    assert seen["req"] is request


@pytest.mark.asyncio
async def test_async_forces_stream_true_for_ccproxy_codex():
    middleware = CcproxyCodexStreamMiddleware()
    request = _request(_model())
    seen = {}

    async def handler(req):
        seen["request"] = req
        return "response"

    assert await middleware.awrap_model_call(request, handler) == "response"
    assert seen["request"].model.streaming is True
    assert "stream" not in seen["request"].model_settings


@pytest.mark.asyncio
async def test_async_leaves_non_ccproxy_request_untouched():
    middleware = CcproxyCodexStreamMiddleware()
    request = _request(_model(base_url="https://api.openai.com/v1"))
    handler = AsyncMock(return_value="response")

    await middleware.awrap_model_call(request, handler)
    assert handler.await_args.args[0] is request


@pytest.fixture
def ccproxy_model(monkeypatch):
    monkeypatch.setenv("OPENAI_BASE_URL", "http://127.0.0.1:8000/codex/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "ccproxy-oauth")
    from EvoScientist.llm.models import get_chat_model

    return get_chat_model("gpt-5-nano", provider="openai")


def test_instance_streaming_stays_unset(ccproxy_model):
    assert "streaming" not in ccproxy_model.model_fields_set


def test_request_model_copy_selects_streaming_path(ccproxy_model):
    streaming_model = ccproxy_model.model_copy(update={"streaming": True})
    assert streaming_model._should_stream(async_api=False) is True
    payload = streaming_model._get_request_payload([HumanMessage("hi")])
    assert payload["stream"] is True


def test_without_override_the_call_does_not_stream(ccproxy_model):
    assert ccproxy_model._should_stream(async_api=False) is False


def test_original_model_stays_non_streaming(ccproxy_model):
    streaming_model = ccproxy_model.model_copy(update={"streaming": True})
    assert streaming_model is not ccproxy_model
    assert ccproxy_model._should_stream(async_api=False) is False
    payload = ccproxy_model._get_request_payload([HumanMessage("hi")])
    assert payload["stream"] is False
