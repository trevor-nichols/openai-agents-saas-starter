from __future__ import annotations

import pytest

from app.agents._shared.prompt_context import PromptRuntimeContext
from app.infrastructure.providers.openai.context import resolve_runtime_context


def test_resolve_runtime_context_bootstrap_used_when_missing():
    bootstrap = PromptRuntimeContext(
        actor=None,
        conversation_id="bootstrap",
        request_message=None,
        settings=None,
    )

    ctx, safe = resolve_runtime_context(None, bootstrap_ctx=bootstrap)

    assert ctx is bootstrap
    assert safe == {}


def test_resolve_runtime_context_strips_prompt_ctx_and_preserves_rest():
    bootstrap = PromptRuntimeContext(
        actor=None,
        conversation_id="bootstrap",
        request_message=None,
        settings=None,
    )
    provided = PromptRuntimeContext(
        actor=None,
        conversation_id="conv-1",
        request_message="hi",
        settings=None,
    )

    ctx, safe = resolve_runtime_context(
        {"prompt_runtime_ctx": provided, "trace_id": "t-1"},
        bootstrap_ctx=bootstrap,
    )

    assert ctx is provided
    assert safe == {"trace_id": "t-1"}


def test_resolve_runtime_context_type_error_on_invalid_prompt_ctx():
    bootstrap = PromptRuntimeContext(
        actor=None,
        conversation_id="bootstrap",
        request_message=None,
        settings=None,
    )
    with pytest.raises(TypeError):
        resolve_runtime_context({"prompt_runtime_ctx": object()}, bootstrap_ctx=bootstrap)
