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

    # Vector store defaults / guardrails
    vector_max_file_mb: int = Field(
        default=512,
        ge=1,
        description="Max file size (MB) allowed when attaching to a vector store.",
    )
    vector_max_total_bytes: int | None = Field(
        default=None,
        description=(
            "Optional per-tenant hard cap on total bytes across vector stores. None disables."
        ),
    )
    vector_max_files_per_store: int = Field(
        default=5000,
        ge=1,
        description="Max number of files per vector store.",
    )
    vector_max_stores_per_tenant: int = Field(
        default=10,
        ge=1,
        description="Max number of vector stores per tenant.",
    )
    vector_allowed_mime_types: list[str] = Field(
        default_factory=lambda: [
            "text/x-c",
            "text/x-c++",
            "text/x-csharp",
            "text/css",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/x-golang",
            "text/html",
            "text/x-java",
            "text/javascript",
            "application/json",
            "text/markdown",
            "application/pdf",
            "text/x-php",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "text/x-python",
            "text/x-script.python",
            "text/x-ruby",
            "application/x-sh",
            "text/x-tex",
            "application/typescript",
            "text/plain",
        ],
        description="Allowed MIME types for vector store file attachments (mirrors OpenAI docs).",
    )

    enable_vector_store_sync_worker: bool = Field(
        default=True,
        description=(
            "Run background sync worker to refresh vector store/file status and expiry. "
            "Set false only for constrained/local dev."
        ),
    )
    vector_store_sync_poll_seconds: float = Field(
        default=60.0,
        ge=5.0,
        description="Polling interval for vector store sync worker.",
    )
    vector_store_sync_batch_size: int = Field(
        default=20,
        ge=1,
        description="Maximum stores refreshed per sync iteration.",
    )
    auto_purge_expired_vector_stores: bool = Field(
        default=False,
        description=(
            "When true, expired vector stores are deleted remotely and soft-deleted locally."
        ),
    )
