"""Hallucination detection guardrail check implementation.

Validates factual claims against reference documents using file search.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.guardrails._shared.client import get_guardrail_openai_client
from app.guardrails._shared.specs import GuardrailCheckResult

logger = logging.getLogger(__name__)

DETECTION_SYSTEM_PROMPT = """\
You are a fact-checker that validates claims against reference documents.

Your task is to identify factual claims in the text and determine if they are:
1. SUPPORTED - clearly backed by the reference documents
2. CONTRADICTED - clearly contradicts the reference documents
3. UNSUPPORTED - makes factual claims not found in the references

Focus on verifiable factual claims (numbers, dates, names, specific assertions).
Ignore opinions, questions, hedged statements, and general knowledge.

Respond with JSON:
{
    "flagged": boolean (true if CONTRADICTED or significant UNSUPPORTED claims),
    "confidence": number (0.0 to 1.0),
    "reasoning": string,
    "hallucination_type": string or null ("factual_error", "unsupported_claim", "none"),
    "hallucinated_statements": [list of problematic statements],
    "verified_statements": [list of supported statements]
}"""


async def run_check(
    content: str,
    config: dict[str, Any],
    *,
    conversation_history: list[dict[str, str]] | None = None,
    context: dict[str, Any] | None = None,
) -> GuardrailCheckResult:
    """Execute hallucination detection check.

    Args:
        content: The text content to validate.
        config: Validated configuration dictionary.
        conversation_history: Not used for hallucination detection.
        context: Runtime context.

    Returns:
        GuardrailCheckResult indicating if hallucinations were detected.
    """
    model: str = config.get("model", "gpt-4.1-mini")
    threshold: float = config.get("confidence_threshold", 0.7)
    knowledge_source: str | None = config.get("knowledge_source")

    # If no knowledge source, skip validation
    if not knowledge_source:
        return GuardrailCheckResult(
            tripwire_triggered=False,
            info={
                "guardrail_name": "Hallucination Detection",
                "flagged": False,
                "reason": "No knowledge source configured",
            },
        )

    # Validate knowledge source format
    if not knowledge_source.startswith("vs_"):
        return GuardrailCheckResult(
            tripwire_triggered=False,
            info={
                "guardrail_name": "Hallucination Detection",
                "flagged": False,
                "error": "Invalid knowledge source ID (must start with vs_)",
            },
        )

    client = get_guardrail_openai_client()

    try:
        # Use Responses API with file search tool
        response = await client.responses.create(
            model=model,
            input=f"""Validate the following text against the reference documents.

Text to validate:
{content}

{DETECTION_SYSTEM_PROMPT}""",
            tools=[
                {
                    "type": "file_search",
                    "vector_store_ids": [knowledge_source],
                }
            ],
        )
    except Exception as e:
        logger.exception("Hallucination detection API call failed: %s", e)
        return GuardrailCheckResult(
            tripwire_triggered=False,
            info={
                "guardrail_name": "Hallucination Detection",
                "flagged": False,
                "error": str(e),
            },
        )

    # Parse response
    response_text = response.output_text or ""
    result = _parse_detection_response(response_text)

    flagged = result["flagged"] and result["confidence"] >= threshold

    # Calculate token usage
    usage = getattr(response, "usage", None)
    token_usage = None
    if usage:
        token_usage = {
            "input_tokens": getattr(usage, "input_tokens", 0),
            "output_tokens": getattr(usage, "output_tokens", 0),
            "total_tokens": getattr(usage, "total_tokens", 0),
        }

    return GuardrailCheckResult(
        tripwire_triggered=flagged,
        confidence=result["confidence"],
        token_usage=token_usage,
        info={
            "guardrail_name": "Hallucination Detection",
            "flagged": result["flagged"],
            "confidence": result["confidence"],
            "threshold": threshold,
            "reasoning": result.get("reasoning", ""),
            "hallucination_type": result.get("hallucination_type"),
            "hallucinated_statements": result.get("hallucinated_statements", []),
            "verified_statements": result.get("verified_statements", []),
            "model": model,
            "knowledge_source": knowledge_source,
        },
    )


def _parse_detection_response(response_text: str) -> dict[str, Any]:
    """Parse the LLM detection response.

    Args:
        response_text: Raw response from the LLM.

    Returns:
        Parsed detection result.
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
            # Try to find JSON object in text
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
            "reasoning": str(result.get("reasoning", "")),
            "hallucination_type": result.get("hallucination_type"),
            "hallucinated_statements": result.get("hallucinated_statements", []),
            "verified_statements": result.get("verified_statements", []),
        }
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.warning("Failed to parse hallucination detection response: %s", e)
        return {
            "flagged": False,
            "confidence": 0.0,
            "reasoning": "Failed to parse detection response",
            "hallucination_type": None,
            "hallucinated_statements": [],
            "verified_statements": [],
        }
