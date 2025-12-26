"""Prompt context assembly with extensible provider hooks."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from openai.types.responses.web_search_tool_param import UserLocation

from app.services.agents.context import ConversationActorContext

ContextProvider = Callable[["PromptRuntimeContext", Any], dict[str, Any]]


@dataclass(slots=True)
class ContainerOverrideContext:
    """Resolved container override for a specific agent."""

    container_id: str
    openai_container_id: str
    source: str = "override"


@dataclass(slots=True)
class PromptRuntimeContext:
    """Base data available when rendering prompts.

    - actor: tenant/user identity for the conversation
    - conversation_id: current conversation id
    - request_message: latest user message (optional)
    - settings: application settings (to expose env, limits, etc.)
    - user_location: optional coarse location for hosted web search tools
    - file_search: optional per-agent resolution data (vector store ids, options)
    - client_overrides: arbitrary client-provided context (from request)
    - memory_summary: optional cross-session summary text to inject into prompts
    """

    actor: ConversationActorContext | None
    conversation_id: str
    request_message: str | None
    settings: Any
    user_location: UserLocation | None = None
    container_bindings: dict[str, str] | None = None
    container_overrides: dict[str, ContainerOverrideContext] | None = None
    file_search: dict[str, Any] | None = None
    client_overrides: dict[str, Any] | None = None
    memory_summary: str | None = None


_PROVIDER_REGISTRY: dict[str, ContextProvider] = {}


def register_context_provider(name: str) -> Callable[[ContextProvider], ContextProvider]:
    """Decorator to register a named context provider.

    Provider outputs are merged into the prompt context for all agents.
    """

    def decorator(func: ContextProvider) -> ContextProvider:
        _PROVIDER_REGISTRY[name] = func
        return func

    return decorator


def get_registered_provider(name: str) -> ContextProvider | None:
    return _PROVIDER_REGISTRY.get(name)


def _run_provider(name: str, ctx: PromptRuntimeContext, spec) -> dict[str, Any]:
    provider = get_registered_provider(name)
    if provider is None:
        raise ValueError(f"Context provider '{name}' is not registered")
    return provider(ctx, spec)


def _merge_provider_context(
    ctx: dict[str, Any],
    provider_name: str,
    provided: dict[str, Any],
) -> None:
    for key, value in provided.items():
        if key in ctx:
            raise ValueError(
                f"Context provider '{provider_name}' attempted to overwrite '{key}'. "
                "Choose a distinct key or remove the default value."
            )
        ctx[key] = value


def build_prompt_context(
    *,
    spec,
    runtime_ctx: PromptRuntimeContext | None,
    base: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the prompt context for a given agent spec.

    - spec: AgentSpec
    - runtime_ctx: PromptRuntimeContext (may be None at boot)
    - base: optional seed dict merged first
    - registered providers: merged into the context for every agent
    """

    ctx = dict(base or {})

    # Always include defaults if a runtime context exists.
    if runtime_ctx is not None:
        actor = runtime_ctx.actor
        if actor is not None:
            ctx.setdefault("user", {})
            ctx["user"].setdefault("id", actor.user_id)
            ctx.setdefault("tenant", {})
            ctx["tenant"].setdefault("id", actor.tenant_id)
        ctx.setdefault("run", {})
        ctx["run"].setdefault("conversation_id", runtime_ctx.conversation_id)
        if runtime_ctx.request_message:
            ctx["run"].setdefault("request_message", runtime_ctx.request_message)
        settings = runtime_ctx.settings
        if settings is not None:
            ctx.setdefault("env", {})
            if hasattr(settings, "environment"):
                ctx["env"].setdefault("environment", settings.environment)
        ctx.setdefault("agent", {})
        ctx["agent"].setdefault("key", spec.key)
        ctx["agent"].setdefault("display_name", spec.display_name)
        ctx.setdefault("memory", {})
        if runtime_ctx.memory_summary:
            ctx["memory"].setdefault("summary", runtime_ctx.memory_summary)

    # Merge prompt defaults from spec (if any)
    if getattr(spec, "prompt_defaults", None):
        for k, v in spec.prompt_defaults.items():
            if k not in ctx:
                ctx[k] = v
            elif isinstance(ctx[k], dict) and isinstance(v, dict):
                for inner_k, inner_v in v.items():
                    ctx[k].setdefault(inner_k, inner_v)

    # Run all registered providers (global prompt variables).
    if runtime_ctx is not None:
        for provider_name in _PROVIDER_REGISTRY:
            provided = _run_provider(provider_name, runtime_ctx, spec)
            if provided:
                _merge_provider_context(ctx, provider_name, provided)

    return ctx


# ---------------------------------------------------------------------------
# Default providers (examples): extend as needed.
# ---------------------------------------------------------------------------


@register_context_provider("datetime")
def _datetime_provider(ctx: PromptRuntimeContext, spec) -> dict[str, Any]:  # pragma: no cover
    import datetime

    now = datetime.datetime.now(datetime.UTC)
    date = f"{now.strftime('%B')} {now.day}, {now.year}"
    time = now.strftime("%H:%M UTC")
    return {
        "date": date,
        "time": time,
        "date_and_time": f"{date} at {time}",
    }


__all__ = [
    "ContainerOverrideContext",
    "PromptRuntimeContext",
    "build_prompt_context",
    "register_context_provider",
]
