"""Custom prompt guardrail check implementation.

Provides flexible, user-defined checks using natural language instructions.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.guardrails._shared.client import get_guardrail_openai_client
from app.guardrails._shared.specs import GuardrailCheckResult

logger = logging.getLogger(__name__)

BASE_SYSTEM_PROMPT = """You are a content analyzer that checks text against specific criteria.

Your task: {custom_instructions}

Analyze the provided text and determine if it violates the specified criteria.

Respond with JSON:
{{
    "flagged": boolean (true if criteria violated),
    "confidence": number (0.0 to 1.0),
    "reason": string (explanation of decision)
}}

Be precise and consistent in your analysis."""


async def run_check(
    content: str,
    config: dict[str, Any],
    *,
    conversation_history: list[dict[str, str]] | None = None,
    context: dict[str, Any] | None = None,
) -> GuardrailCheckResult:
    """Execute custom prompt check.

    Args:
        content: The text content to check.
        config: Validated configuration dictionary.
        conversation_history: Not used for custom prompt check.
        context: Runtime context.

    Returns:
        GuardrailCheckResult based on custom check criteria.
    """
    model: str = config.get("model", "gpt-4.1-mini")
    threshold: float = config.get("confidence_threshold", 0.7)
    custom_instructions: str = config.get(
        "system_prompt_details",
        "Check if the content violates any policies.",
    )

    # Build system prompt with custom instructions
    system_prompt = BASE_SYSTEM_PROMPT.format(custom_instructions=custom_instructions)

    client = get_guardrail_openai_client()

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this text:\n\n{content}"},
            ],
            temperature=0.0,
            max_tokens=500,
        )
    except Exception as e:
        logger.exception("Custom prompt check LLM call failed: %s", e)
        return GuardrailCheckResult(
            tripwire_triggered=False,
            info={
                "guardrail_name": "Custom Prompt Check",
                "flagged": False,
                "error": str(e),
            },
        )

    response_text = response.choices[0].message.content or ""
    result = _parse_response(response_text)

    flagged = result["flagged"] and result["confidence"] >= threshold

    usage = response.usage
    token_usage = None
    if usage:
        token_usage = {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
        }

    return GuardrailCheckResult(
        tripwire_triggered=flagged,
        confidence=result["confidence"],
        token_usage=token_usage,
        info={
            "guardrail_name": "Custom Prompt Check",
            "flagged": result["flagged"],
            "confidence": result["confidence"],
            "threshold": threshold,
            "reason": result["reason"],
            "custom_instructions": custom_instructions,
            "model": model,
        },
    )


def _parse_response(response_text: str) -> dict[str, Any]:
    """Parse the LLM response.

    Args:
        response_text: Raw response from the LLM.

    Returns:
        Parsed result.
    """
    try:
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            json_str = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            json_str = response_text[start:end].strip()
        else:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = response_text[start:end]
            else:
                json_str = response_text.strip()

        result = json.loads(json_str)
        return {
            "flagged": bool(result.get("flagged", False)),
            "confidence": float(result.get("confidence", 0.0)),
            "reason": str(result.get("reason", "")),
        }
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.warning("Failed to parse custom prompt response: %s", e)
        return {
            "flagged": False,
            "confidence": 0.0,
            "reason": "Failed to parse response",
        }
