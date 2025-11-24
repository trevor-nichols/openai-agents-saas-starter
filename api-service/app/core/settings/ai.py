"""API keys for model providers and tools."""
from __future__ import annotations

from pydantic import BaseModel, Field


class AIProviderSettingsMixin(BaseModel):
    openai_api_key: str | None = Field(default=None, description="OpenAI API key")
    anthropic_api_key: str | None = Field(default=None, description="Anthropic API key")
    gemini_api_key: str | None = Field(default=None, description="Google Gemini API key")
    xai_api_key: str | None = Field(default=None, description="xAI API key")

    agent_default_model: str = Field(
        default="gpt-5.1",
        description="Default reasoning model for triage and agent fallbacks.",
        alias="AGENT_MODEL_DEFAULT",
    )
    agent_triage_model: str | None = Field(
        default=None,
        description="Override for the triage agent model; defaults to agent_default_model.",
        alias="AGENT_MODEL_TRIAGE",
    )
    agent_code_model: str | None = Field(
        default=None,
        description="Override for the code assistant model; defaults to agent_default_model.",
        alias="AGENT_MODEL_CODE",
    )
    agent_data_model: str | None = Field(
        default=None,
        description="Override for the data analyst model; defaults to agent_default_model.",
        alias="AGENT_MODEL_DATA",
    )
