"""Shared OpenAI client factory for guardrail checks."""

from __future__ import annotations

from functools import lru_cache

from openai import AsyncOpenAI

from app.core.settings import get_settings


@lru_cache(maxsize=1)
def _client(api_key: str | None) -> AsyncOpenAI:
    """Return a cached AsyncOpenAI client for guardrails."""
    return AsyncOpenAI(api_key=api_key)


def get_guardrail_openai_client() -> AsyncOpenAI:
    """Return a shared AsyncOpenAI client configured from application settings."""
    settings = get_settings()
    return _client(settings.openai_api_key)


__all__ = ["get_guardrail_openai_client"]
