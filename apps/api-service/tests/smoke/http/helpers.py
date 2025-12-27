"""Shared helpers for HTTP smoke tests (gating + SSE)."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable, Final, Iterable, Sequence

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


def assert_status_in(response: httpx.Response, expected: Iterable[int]) -> None:
    expected_set = set(expected)
    if response.status_code not in expected_set:
        raise AssertionError(
            f"Expected status in {sorted(expected_set)}, got {response.status_code}: {response.text}"
        )


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


async def read_first_sse_line(
    response: httpx.Response,
    *,
    timeout_seconds: float = DEFAULT_SSE_TIMEOUT_SECONDS,
) -> str:
    """Read the first non-empty SSE line (data or ping)."""
    assert_event_stream_response(response)

    async def _read() -> str:
        async for line in response.aiter_lines():
            if line:
                return line
        raise AssertionError("No SSE lines received.")

    try:
        return await asyncio.wait_for(_read(), timeout=timeout_seconds)
    except asyncio.TimeoutError as exc:
        raise AssertionError("Timed out waiting for SSE line.") from exc


async def read_sse_event_json(
    response: httpx.Response,
    *,
    predicate: Callable[[dict[str, Any]], bool] | None = None,
    timeout_seconds: float = DEFAULT_SSE_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Read the first SSE data frame that parses as JSON (and matches predicate)."""
    assert_event_stream_response(response)

    async def _read() -> dict[str, Any]:
        async for line in response.aiter_lines():
            if not line or not line.startswith("data:"):
                continue
            payload = line.removeprefix("data:").strip()
            try:
                parsed = json.loads(payload)
            except json.JSONDecodeError as exc:
                raise AssertionError(f"Invalid SSE JSON payload: {payload!r}") from exc
            if isinstance(parsed, dict) and (predicate is None or predicate(parsed)):
                return parsed
        raise AssertionError("No SSE JSON data frames received.")

    try:
        return await asyncio.wait_for(_read(), timeout=timeout_seconds)
    except asyncio.TimeoutError as exc:
        raise AssertionError("Timed out waiting for SSE JSON data frame.") from exc


async def fetch_first_sse_event(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    timeout_seconds: float = DEFAULT_SSE_TIMEOUT_SECONDS,
    **kwargs,
) -> str:
    """Open an SSE stream, read the first data frame, then close the stream."""
    async with client.stream(method, url, **kwargs) as response:
        return await read_first_sse_event(response, timeout_seconds=timeout_seconds)


async def fetch_first_sse_line(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    timeout_seconds: float = DEFAULT_SSE_TIMEOUT_SECONDS,
    **kwargs,
) -> str:
    """Open an SSE stream, read the first non-empty line, then close the stream."""
    async with client.stream(method, url, **kwargs) as response:
        return await read_first_sse_line(response, timeout_seconds=timeout_seconds)


async def fetch_sse_event_json(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    predicate: Callable[[dict[str, Any]], bool] | None = None,
    timeout_seconds: float = DEFAULT_SSE_TIMEOUT_SECONDS,
    **kwargs,
) -> dict[str, Any]:
    """Open an SSE stream, read the first JSON data frame (optionally matching predicate)."""
    async with client.stream(method, url, **kwargs) as response:
        return await read_sse_event_json(
            response,
            predicate=predicate,
            timeout_seconds=timeout_seconds,
        )


async def delete_if_exists(
    client: httpx.AsyncClient,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    expected_statuses: Sequence[int] = (200, 202, 204, 404),
) -> None:
    """Delete a resource, treating missing resources as a no-op."""
    response = await client.delete(url, headers=headers)
    assert_status_in(response, expected_statuses)


__all__ = [
    "assert_event_stream_response",
    "assert_status_in",
    "delete_if_exists",
    "fetch_first_sse_event",
    "fetch_first_sse_line",
    "fetch_sse_event_json",
    "read_sse_event_json",
    "read_first_sse_event",
    "read_first_sse_line",
    "require_enabled",
]
