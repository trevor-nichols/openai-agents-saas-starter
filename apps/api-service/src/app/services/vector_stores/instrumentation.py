"""Common instrumentation helpers for vector store services."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from time import perf_counter

from agents import trace

from app.observability.metrics import (
    VECTOR_STORE_OPERATION_DURATION_SECONDS,
    VECTOR_STORE_OPERATIONS_TOTAL,
)


@asynccontextmanager
async def instrument(operation: str, metadata: dict[str, str] | None = None) -> AsyncIterator[None]:
    start = perf_counter()
    try:
        with trace(workflow_name=f"vector_store.{operation}", metadata=metadata or {}):
            yield
        _record(operation, "success", start)
    except Exception:
        _record(operation, "error", start)
        raise


def _record(operation: str, result: str, start_time: float) -> None:
    duration = max(perf_counter() - start_time, 0.0)
    VECTOR_STORE_OPERATIONS_TOTAL.labels(operation=operation, result=result).inc()
    VECTOR_STORE_OPERATION_DURATION_SECONDS.labels(operation=operation, result=result).observe(
        duration
    )


__all__ = ["instrument"]
