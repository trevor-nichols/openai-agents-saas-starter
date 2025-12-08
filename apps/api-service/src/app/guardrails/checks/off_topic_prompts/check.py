"""Off-topic prompts guardrail check implementation."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.guardrails._shared.client import get_guardrail_openai_client
from app.guardrails._shared.specs import GuardrailCheckResult

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a classifier that determines if a user message stays within the defined "
    "business scope.\n\n"
    "Scope description:\n"
    "{scope_description}\n\n"
    "Respond in JSON:\n"
    "{\n"
    '  "flagged": boolean (true if the message is off-topic),\n'
    '  "confidence": number (0.0-1.0),\n'
    '  "reason": string\n'
    "}\n\n"
    "Base the decision solely on whether the message fits the described scope."
)


async def run_check(
    content: str,
    config: dict[str, Any],
    *,
    conversation_history: list[dict[str, str]] | None = None,
    context: dict[str, Any] | None = None,
) -> GuardrailCheckResult:
    """Execute off-topic prompt detection using an LLM."""
    model: str = config.get("model", "gpt-4.1-mini")
    threshold: float = config.get("confidence_threshold", 0.7)
    scope_description: str = config.get(
        "system_prompt_details",
        "Customer support for our e-commerce platform.",
    )

    system_prompt = SYSTEM_PROMPT.format(scope_description=scope_description)

    client = get_guardrail_openai_client()

    user_content = content
    if conversation_history:
        history_text = "\n".join(
            f"{item.get('role')}: {item.get('content')}" for item in conversation_history
        )
        user_content = f"Conversation so far:\n{history_text}\n\nLatest message:\n{content}"

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.0,
            max_tokens=400,
        )
    except Exception as e:
        logger.exception("Off-topic guardrail LLM call failed: %s", e)
        return GuardrailCheckResult(
            tripwire_triggered=False,
            info={
                "guardrail_name": "Off Topic Prompts",
                "flagged": False,
                "error": str(e),
            },
        )

    response_text = response.choices[0].message.content or ""
    parsed = _parse_response(response_text)

    flagged = parsed["flagged"] and parsed["confidence"] >= threshold

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
        confidence=parsed["confidence"],
        token_usage=token_usage,
        info={
            "guardrail_name": "Off Topic Prompts",
            "flagged": parsed["flagged"],
            "confidence": parsed["confidence"],
            "threshold": threshold,
            "reason": parsed["reason"],
            "model": model,
            "scope": scope_description,
        },
    )


def _parse_response(response_text: str) -> dict[str, Any]:
    """Parse the JSON-ish response from the model."""
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
            json_str = response_text[start:end] if start >= 0 and end > start else response_text

        data = json.loads(json_str)
        return {
            "flagged": bool(data.get("flagged", False)),
            "confidence": float(data.get("confidence", 0.0)),
            "reason": str(data.get("reason", "")),
        }
    except Exception as e:
        logger.warning("Failed to parse off-topic response: %s", e)
        return {"flagged": False, "confidence": 0.0, "reason": "Failed to parse response"}
