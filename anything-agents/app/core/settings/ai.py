"""API keys for model providers and tools."""
from __future__ import annotations

from pydantic import BaseModel, Field


class AIProviderSettingsMixin(BaseModel):
    openai_api_key: str | None = Field(default=None, description="OpenAI API key")
    anthropic_api_key: str | None = Field(default=None, description="Anthropic API key")
    gemini_api_key: str | None = Field(default=None, description="Google Gemini API key")
    xai_api_key: str | None = Field(default=None, description="xAI API key")
    tavily_api_key: str | None = Field(default=None, description="Tavily web search API key")
