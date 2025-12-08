"""OpenAI moderation guardrail check implementation."""

from __future__ import annotations

import logging
from typing import Any

from app.guardrails._shared.client import get_guardrail_openai_client
from app.guardrails._shared.specs import GuardrailCheckResult

logger = logging.getLogger(__name__)

# All available moderation categories
ALL_CATEGORIES = [
    "hate",
    "hate/threatening",
    "harassment",
    "harassment/threatening",
    "self-harm",
    "self-harm/intent",
    "self-harm/instructions",
    "sexual",
    "sexual/minors",
    "violence",
    "violence/graphic",
]


async def run_check(
    content: str,
    config: dict[str, Any],
    *,
    conversation_history: list[dict[str, str]] | None = None,
    context: dict[str, Any] | None = None,
) -> GuardrailCheckResult:
    """Execute OpenAI moderation check.

    Args:
        content: The text content to moderate.
        config: Validated configuration dictionary.
        conversation_history: Not used for moderation.
        context: Runtime context (not used).

    Returns:
        GuardrailCheckResult indicating if content was flagged.
    """
    categories_to_check: list[str] = config.get("categories", [])
    threshold: float = config.get("threshold", 0.5)
    model: str = config.get("model", "omni-moderation-latest")

    # Use all categories if none specified
    if not categories_to_check:
        categories_to_check = ALL_CATEGORIES

    # Call OpenAI moderation API
    client = get_guardrail_openai_client()

    try:
        response = await client.moderations.create(
            input=content,
            model=model,
        )
    except Exception as e:
        logger.exception("Moderation API call failed: %s", e)
        return GuardrailCheckResult(
            tripwire_triggered=False,
            info={
                "guardrail_name": "Moderation",
                "flagged": False,
                "error": str(e),
            },
        )

    if not response.results:
        return GuardrailCheckResult(
            tripwire_triggered=False,
            info={
                "guardrail_name": "Moderation",
                "flagged": False,
                "error": "No results from moderation API",
            },
        )

    result = response.results[0]

    # Extract category scores
    category_scores: dict[str, float] = {}
    flagged_categories: list[str] = []

    # Map category names to attribute names (replace / with _)
    for category in categories_to_check:
        attr_name = category.replace("/", "_").replace("-", "_")

        # Get score from category_scores
        score = getattr(result.category_scores, attr_name, None)
        if score is not None:
            category_scores[category] = score
            if score >= threshold:
                flagged_categories.append(category)

    # Also check the boolean flags
    for category in categories_to_check:
        attr_name = category.replace("/", "_").replace("-", "_")
        is_flagged = getattr(result.categories, attr_name, False)
        if is_flagged and category not in flagged_categories:
            flagged_categories.append(category)

    flagged = len(flagged_categories) > 0

    return GuardrailCheckResult(
        tripwire_triggered=flagged,
        info={
            "guardrail_name": "Moderation",
            "flagged": flagged,
            "flagged_categories": flagged_categories,
            "category_scores": category_scores,
            "threshold": threshold,
            "model": model,
            "categories_checked": categories_to_check,
        },
    )
