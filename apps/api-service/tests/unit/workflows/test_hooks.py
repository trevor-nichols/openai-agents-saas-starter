from __future__ import annotations

import pytest

from app.services.workflows.hooks import apply_reducer, run_mapper


async def _async_mapper(current_input, prior_steps):
    return f"mapped-{current_input}-{len(prior_steps)}"


async def _async_reducer(outputs, prior_steps):
    return f"{len(outputs)}|{len(prior_steps)}|" + ",".join(str(o) for o in outputs)


@pytest.mark.asyncio
async def test_apply_reducer_without_path_single_element():
    result = await apply_reducer(None, ["only"], [])
    assert result == "only"


@pytest.mark.asyncio
async def test_apply_reducer_without_path_multiple_elements():
    result = await apply_reducer(None, [1, 2, 3], [])
    assert result == [1, 2, 3]


@pytest.mark.asyncio
async def test_run_mapper_awaits_async_callable():
    result = await run_mapper(
        "tests.unit.workflows.test_hooks:_async_mapper", "msg", [1, 2]
    )
    assert result == "mapped-msg-2"


@pytest.mark.asyncio
async def test_apply_reducer_awaits_async_callable_and_passes_prior_steps():
    outputs = ["a", "b"]
    prior = ["step1"]
    result = await apply_reducer(
        "tests.unit.workflows.test_hooks:_async_reducer", outputs, prior
    )
    assert result == "2|1|a,b"
