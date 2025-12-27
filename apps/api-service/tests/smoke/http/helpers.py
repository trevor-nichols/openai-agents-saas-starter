"""Shared helpers for HTTP smoke tests (gating + SSE)."""

from __future__ import annotations

import asyncio
from typing import Final

import httpx
import pytest

DEFAULT_SSE_TIMEOUT_SECONDS: Final[float] = 5.0


def require_enabled(enabled: bool, *, reason: str) -> None:
    """Skip the test when a smoke gate is disabled."""
    if not enabled:
        pytest.skip(reason)


def assert_event_stream_response(response: httpx.Response) -> None:
    if response.status_code != 200:
        raise AssertionError(f"Expected 200, got {response.status_code}: {response.text}")
    content_type = response.headers.get("content-type", "")
    if "text/event-stream" not in content_type:
        raise AssertionError(f"Expected text/event-stream, got {content_type!r}")


async def read_first_sse_event(
    response: httpx.Response,
    *,
    timeout_seconds: float = DEFAULT_SSE_TIMEOUT_SECONDS,
) -> str:
    """Read the first SSE data frame (or raise on timeout)."""
    assert_event_stream_response(response)

    async def _read() -> str:
        async for line in response.aiter_lines():
            if not line:
                continue
            if line.startswith("data:"):
                return line.removeprefix("data:").strip()
        raise AssertionError("No SSE data frames received.")

    try:
        return await asyncio.wait_for(_read(), timeout=timeout_seconds)
    except asyncio.TimeoutError as exc:
        raise AssertionError("Timed out waiting for SSE data frame.") from exc


__all__ = ["assert_event_stream_response", "read_first_sse_event", "require_enabled"]
