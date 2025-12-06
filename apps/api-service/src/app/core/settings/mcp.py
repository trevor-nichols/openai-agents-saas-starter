"""Settings for hosted Model Context Protocol tools.

These settings let operators declaratively register hosted MCP tools (remote MCP
servers or OpenAI connectors) that are wired into the tool registry and exposed
to agents via `tool_keys`.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class MCPToolSettings(BaseModel):
    """Single hosted MCP tool definition."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Registry key; referenced in agent tool_keys.")
    server_label: str = Field(..., description="Label forwarded to the MCP tool surface.")
    server_url: str | None = Field(default=None, description="Public MCP server URL.")
    connector_id: str | None = Field(default=None, description="OpenAI connector id.")
    authorization: str | None = Field(
        default=None,
        description="Bearer/OAuth token used when calling the MCP server or connector.",
    )
    require_approval: str | dict[str, Any] = Field(
        default="always",
        description=(
            "Approval policy for the MCP tool (""always"", ""never"" or per-tool mapping). "
            "Defaults to 'always' for safer posture."
        ),
    )
    allowed_tools: list[str] | None = Field(
        default=None, description="Optional allow-list of tool names to import from the server."
    )
    description: str | None = Field(
        default=None, description="Optional server description shown to the model."
    )
    auto_approve_tools: list[str] | None = Field(
        default=None,
        description="Tools that should be auto-approved without escalation.",
    )
    deny_tools: list[str] | None = Field(
        default=None,
        description="Tools that should always be denied (wins over auto_approve_tools).",
    )

    @model_validator(mode="after")
    def _validate_endpoints(self) -> MCPToolSettings:
        has_url = bool(self.server_url)
        has_connector = bool(self.connector_id)
        if has_url == has_connector:
            raise ValueError(
                f"MCP tool '{self.name}' must set exactly one of server_url or connector_id."
            )
        if self.connector_id and not (self.authorization and self.authorization.strip()):
            raise ValueError(
                f"MCP tool '{self.name}' uses connector_id but is missing authorization."
            )
        return self

    @model_validator(mode="after")
    def _validate_allow_deny(self) -> MCPToolSettings:
        if self.auto_approve_tools and self.deny_tools:
            overlap = set(self.auto_approve_tools) & set(self.deny_tools)
            if overlap:
                raise ValueError(
                    "auto_approve_tools and deny_tools cannot overlap: " + ", ".join(overlap)
                )
        return self

    @field_validator("require_approval")
    @classmethod
    def _validate_require_approval(cls, value: str | dict[str, Any]) -> str | dict[str, Any]:
        allowed = {"always", "never"}
        if isinstance(value, str):
            if value not in allowed:
                raise ValueError("require_approval must be 'always', 'never', or a per-tool map")
            return value
        if isinstance(value, dict):
            invalid = {v for v in value.values() if isinstance(v, str) and v not in allowed}
            if invalid:
                raise ValueError(
                    "require_approval mapping values must be 'always' or 'never' when strings"
                )
        return value


class MCPSettingsMixin(BaseModel):
    """Mixin providing hosted MCP tool configuration."""
    mcp_tools: list[MCPToolSettings] = Field(
        default_factory=list,
        alias="MCP_TOOLS",
        description="Hosted MCP tool definitions registered into the tool registry.",
    )

    @field_validator("mcp_tools", mode="before")
    @classmethod
    def _coerce_mcp_tools(cls, value: Any) -> Any:
        if value in (None, "", []):
            return []
        if isinstance(value, str):
            trimmed = value.strip()
            if not trimmed:
                return []
            try:
                return json.loads(trimmed)
            except json.JSONDecodeError as exc:  # pragma: no cover - defensive
                raise ValueError("MCP_TOOLS must be a JSON array of tool configs.") from exc
        return value

    @model_validator(mode="after")
    def _validate_unique_names(self) -> MCPSettingsMixin:
        names = [cfg.name for cfg in self.mcp_tools]
        if len(names) != len(set(names)):
            raise ValueError("MCP tool names must be unique.")
        labels = [cfg.server_label for cfg in self.mcp_tools]
        if len(labels) != len(set(labels)):
            raise ValueError("MCP tool server_label values must be unique.")
        return self
