"""Helper functions for resolving and executing workflow hooks (guards, mappers, reducers)."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
from typing import Any


def import_callable(path: str, label: str) -> Callable[..., Any]:
    """Import a callable from ``module:attr`` or dotted ``module.attr`` syntax."""

    if ":" in path:
        module_path, attr = path.split(":", 1)
    elif "." in path:
        module_path, attr = path.rsplit(".", 1)
    else:
        raise ValueError(f"Invalid dotted path for {label}: {path}")

    module = __import__(module_path, fromlist=[attr])
    func = getattr(module, attr, None)
    if func is None or not callable(func):
        raise ValueError(f"{label} '{path}' must be a callable")
    return func


async def evaluate_guard(
    dotted_path: str, current_input: Any, prior_steps: Sequence[Any]
) -> bool:
    func = import_callable(dotted_path, "guard")
    value = func(current_input, prior_steps)
    if asyncio.iscoroutine(value):
        value = await value
    return bool(value)


async def run_mapper(
    dotted_path: str, current_input: Any, prior_steps: Sequence[Any]
) -> Any:
    func = import_callable(dotted_path, "input_mapper")
    value = func(current_input, prior_steps)
    if asyncio.iscoroutine(value):
        value = await value
    return value


async def apply_reducer(
    reducer_path: str | None, outputs: list[Any], prior_steps: Sequence[Any]
) -> Any:
    if reducer_path is None:
        if len(outputs) == 1:
            return outputs[0]
        return outputs
    func = import_callable(reducer_path, "reducer")
    value = func(outputs, prior_steps)
    if asyncio.iscoroutine(value):
        value = await value
    return value


__all__ = ["apply_reducer", "evaluate_guard", "import_callable", "run_mapper"]
