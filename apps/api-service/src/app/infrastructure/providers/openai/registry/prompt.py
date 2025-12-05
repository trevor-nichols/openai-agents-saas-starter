"""Prompt rendering helpers for OpenAI agents."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.agents._shared.loaders import resolve_prompt
from app.agents._shared.prompt_context import (
    PromptRuntimeContext,
    build_prompt_context,
)
from app.agents._shared.prompt_template import render_prompt
from app.agents._shared.specs import AgentSpec
from app.core.settings import Settings
from app.services.agents.context import ConversationActorContext


class PromptRenderer:
    def __init__(self, *, settings_factory: Callable[[], Settings]):
        self._settings_factory = settings_factory

    def build_static_context(self) -> PromptRuntimeContext:
        settings = self._settings_factory()
        return PromptRuntimeContext(
            actor=ConversationActorContext(
                tenant_id="bootstrap-tenant",
                user_id="bootstrap-user",
            ),
            conversation_id="bootstrap",
            request_message="",
            settings=settings,
            file_search=None,
            client_overrides=None,
        )

    def render_instructions(
        self,
        *,
        spec: AgentSpec,
        runtime_ctx: PromptRuntimeContext | None,
        validate_prompts: bool,
    ) -> tuple[str, dict[str, Any]]:
        raw_prompt = resolve_prompt(spec)
        prompt_ctx = {}
        if runtime_ctx is not None:
            prompt_ctx = build_prompt_context(spec=spec, runtime_ctx=runtime_ctx, base=None)
        instructions = render_prompt(raw_prompt, context=prompt_ctx, validate=validate_prompts)
        return instructions, prompt_ctx


__all__ = ["PromptRenderer"]
