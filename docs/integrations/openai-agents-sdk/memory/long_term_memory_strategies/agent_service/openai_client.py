from __future__ import annotations

from typing import Optional

from openai import AsyncOpenAI

from .deps import set_default_openai_client, set_tracing_disabled

# --------------------------------------------------------------------------------------
# OpenAI client initialization
# --------------------------------------------------------------------------------------

OPENAI_CLIENT: Optional[AsyncOpenAI] = None

# Disable tracing by default for this service (keeps logs quieter in the bridge process).
set_tracing_disabled(True)


def ensure_openai_client() -> AsyncOpenAI:
    """Create (once) and register the default AsyncOpenAI client for the Agents SDK."""
    global OPENAI_CLIENT
    if OPENAI_CLIENT is not None:
        return OPENAI_CLIENT

    try:
        OPENAI_CLIENT = AsyncOpenAI()
    except Exception as exc:  # pragma: no cover - propagate configuration errors gracefully
        raise RuntimeError(
            "Failed to initialize OpenAI client. Ensure OPENAI_API_KEY is set in the environment."
        ) from exc

    set_default_openai_client(OPENAI_CLIENT)
    return OPENAI_CLIENT
