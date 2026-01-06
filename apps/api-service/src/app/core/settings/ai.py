"""API keys for model providers and tools."""
from __future__ import annotations

from pydantic import BaseModel, Field


class AIProviderSettingsMixin(BaseModel):
    openai_api_key: str | None = Field(default=None, description="OpenAI API key")

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
    auto_create_vector_store_for_file_search: bool = Field(
        default=True,
        description=(
            "Automatically create a primary vector store for tenants when file_search is used."
        ),
    )

    # Containers / Code Interpreter defaults
    container_default_auto_memory: str = Field(
        default="1g",
        description="Default memory tier for auto containers when not specified (1g,4g,16g,64g).",
    )
    container_allowed_memory_tiers: list[str] = Field(
        default_factory=lambda: ["1g", "4g", "16g", "64g"],
        description="Allowed memory tiers for explicit containers.",
    )
    container_max_containers_per_tenant: int = Field(
        default=10,
        ge=1,
        description="Maximum explicit containers a tenant may create.",
    )
    container_fallback_to_auto_on_missing_binding: bool = Field(
        default=True,
        description=(
            "When True, agent runs fall back to auto container if an explicit binding is missing "
            "or expired; when False, runs will error."
        ),
    )

    # Image generation defaults / guardrails
    image_default_size: str = Field(
        default="1024x1024",
        description=(
            "Default output size for image generation tool (supports auto, 1024x1024,"
            " 1024x1536, 1536x1024)."
        ),
    )
    image_default_quality: str = Field(
        default="high",
        description="Default quality for image generation (auto, low, medium, high).",
    )
    image_default_format: str = Field(
        default="png",
        description="Default image format (png, jpeg, webp).",
    )
    image_default_background: str = Field(
        default="auto",
        description="Default background mode (auto, opaque, transparent).",
    )
    image_default_compression: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description=(
            "Optional default compression level (0-100) for jpeg/webp; None lets"
            " provider choose."
        ),
    )
    image_output_max_mb: int = Field(
        default=6,
        ge=1,
        description="Hard cap on decoded image size in megabytes to avoid large inline payloads.",
    )
    image_allowed_formats: list[str] = Field(
        default_factory=lambda: ["png", "jpeg", "webp"],
        description="Whitelisted output formats accepted from the image tool.",
    )
    image_max_partial_images: int = Field(
        default=3,
        ge=0,
        le=3,
        description="Maximum partial images to stream when enabled (0-3).",
    )
