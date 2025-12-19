from __future__ import annotations

from typing import Any


async def final_answer_only(run_result: Any) -> str:
    """
    Reduce an agent-tool run result to its final textual answer.

    Fallback order:
    - run_result.final_output (common in OpenAI Agents SDK)
    - run_result.output / .result (other adapters)
    - str(run_result) as a last resort
    """

    for attr in ("final_output", "output", "result"):
        value = getattr(run_result, attr, None)
        if value:
            return str(value)

    return str(run_result)
