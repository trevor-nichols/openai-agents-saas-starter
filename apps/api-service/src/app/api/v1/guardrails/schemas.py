"""Schemas for guardrails API endpoints."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class GuardrailSummary(BaseModel):
    """Lightweight representation of a guardrail specification."""

    key: str = Field(description="Unique identifier for the guardrail.")
    display_name: str = Field(description="Human-friendly display name.")
    description: str = Field(description="Short description of what the guardrail checks.")
    stage: Literal["pre_flight", "input", "output", "tool_input", "tool_output"] = Field(
        description="Stage at which the guardrail executes."
    )
    engine: Literal["regex", "llm", "api", "hybrid"] = Field(
        description="Underlying engine type for the guardrail."
    )
    supports_masking: bool = Field(
        default=False,
        description="Whether the guardrail can mask/redact content instead of blocking.",
    )


class GuardrailDetail(GuardrailSummary):
    """Detailed information about a guardrail specification."""

    uses_conversation_history: bool = Field(
        default=False,
        description="Whether the guardrail requires conversation history context.",
    )
    tripwire_on_error: bool = Field(
        default=False,
        description="Whether errors in the guardrail should trigger a tripwire.",
    )
    default_config: dict[str, Any] = Field(
        default_factory=dict,
        description="Default configuration values for this guardrail.",
    )
    config_schema: dict[str, Any] = Field(
        default_factory=dict,
        description="JSON schema describing the configuration options.",
    )


class GuardrailCheckConfigSchema(BaseModel):
    """Configuration for a guardrail within a preset."""

    guardrail_key: str = Field(description="Key of the guardrail.")
    enabled: bool = Field(default=True, description="Whether this guardrail is enabled.")
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Configuration overrides for this guardrail.",
    )


class PresetSummary(BaseModel):
    """Lightweight representation of a guardrail preset."""

    key: str = Field(description="Unique identifier for the preset.")
    display_name: str = Field(description="Human-friendly display name.")
    description: str = Field(description="Description of what this preset provides.")
    guardrail_count: int = Field(description="Number of guardrails in this preset.")


class PresetDetail(PresetSummary):
    """Detailed information about a guardrail preset."""

    guardrails: list[GuardrailCheckConfigSchema] = Field(
        description="List of guardrail configurations in this preset."
    )
