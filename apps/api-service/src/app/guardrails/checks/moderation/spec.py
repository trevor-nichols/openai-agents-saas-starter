"""OpenAI moderation guardrail specification."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.guardrails._shared.specs import GuardrailSpec

# Supported moderation categories
ModerationCategory = Literal[
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


class ModerationConfig(BaseModel):
    """Configuration for OpenAI moderation guardrail.

    Attributes:
        categories: List of moderation categories to check. If empty, all
            categories are checked.
        threshold: Score threshold for flagging (0.0-1.0). Content with
            scores above this threshold in any checked category is flagged.
        model: Moderation model to use (omni recommended for latest).
    """

    categories: list[ModerationCategory] = Field(
        default_factory=list,
        description="Categories to check. Empty means all categories.",
    )
    threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Score threshold for flagging",
    )
    model: str = Field(
        default="omni-moderation-latest",
        description="Moderation model to use",
    )


def get_guardrail_spec() -> GuardrailSpec:
    """Return the moderation guardrail specification."""
    return GuardrailSpec(
        key="moderation",
        display_name="Moderation",
        description=(
            "Uses OpenAI's moderation API to detect content that violates "
            "usage policies including hate speech, harassment, violence, "
            "self-harm, and sexual content."
        ),
        stage="input",
        engine="api",
        config_schema=ModerationConfig,
        check_fn_path="app.guardrails.checks.moderation.check:run_check",
        uses_conversation_history=False,
        default_config={
            "categories": [],
            "threshold": 0.5,
            "model": "omni-moderation-latest",
        },
        supports_masking=False,
        tripwire_on_error=False,
    )
