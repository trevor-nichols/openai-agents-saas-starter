"""Integration provider configuration (Slack, etc.)."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


def _flatten_channels(value: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for entry in value:
        candidate = entry.strip()
        if not candidate:
            continue
        if candidate in seen:
            continue
        normalized.append(candidate)
        seen.add(candidate)
    return normalized


def _parse_channel_list(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, list | tuple | set):
        return _flatten_channels([str(item) for item in value])
    if isinstance(value, str):
        trimmed = value.strip()
        if not trimmed:
            return []
        try:
            parsed = json.loads(trimmed)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            return _flatten_channels([str(item) for item in parsed])
        return _flatten_channels(trimmed.split(","))
    raise ValueError("Channel values must be a string, list, or tuple.")


class IntegrationSettingsMixin(BaseModel):
    enable_slack_status_notifications: bool = Field(
        default=False,
        alias="ENABLE_SLACK_STATUS_NOTIFICATIONS",
        description="Toggle Slack fan-out for status incidents.",
    )
    slack_status_bot_token: str | None = Field(
        default=None,
        alias="SLACK_STATUS_BOT_TOKEN",
        description="OAuth bot token with chat:write scope.",
    )
    slack_status_default_channels: list[str] = Field(
        default_factory=list,
        alias="SLACK_STATUS_DEFAULT_CHANNELS",
        description="Default Slack channel IDs (comma-separated or JSON list).",
    )
    slack_status_tenant_channel_map: dict[str, list[str]] = Field(
        default_factory=dict,
        alias="SLACK_STATUS_TENANT_CHANNEL_MAP",
        description="JSON map of tenant_id → channel list overrides.",
    )
    slack_api_base_url: str = Field(
        default="https://slack.com/api",
        alias="SLACK_API_BASE_URL",
        description="Slack Web API base URL (override for tests).",
    )
    slack_http_timeout_seconds: float = Field(
        default=5.0,
        alias="SLACK_HTTP_TIMEOUT_SECONDS",
        description="HTTP timeout for Slack API requests.",
        gt=0.0,
    )
    slack_status_rate_limit_window_seconds: float = Field(
        default=1.0,
        alias="SLACK_STATUS_RATE_LIMIT_WINDOW_SECONDS",
        description="Per-channel throttle window for Slack posts.",
        gt=0.0,
    )
    slack_status_max_retries: int = Field(
        default=3,
        alias="SLACK_STATUS_MAX_RETRIES",
        description="Maximum retry attempts for Slack delivery failures.",
        ge=1,
    )

    @field_validator("slack_status_default_channels", mode="before")
    @classmethod
    def _coerce_default_channels(cls, value: Any) -> list[str]:
        return _parse_channel_list(value)

    @field_validator("slack_status_tenant_channel_map", mode="before")
    @classmethod
    def _coerce_channel_map(cls, value: Any) -> dict[str, list[str]]:
        if value in (None, "", {}):
            return {}
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError as exc:  # pragma: no cover - defensive
                raise ValueError("SLACK_STATUS_TENANT_CHANNEL_MAP must be JSON.") from exc
        elif isinstance(value, dict):
            parsed = value
        else:
            raise ValueError("Tenant channel map must be JSON or a dict of tenant -> channels.")
        result: dict[str, list[str]] = {}
        for key, raw in parsed.items():
            result[str(key).lower()] = _parse_channel_list(raw)
        return result

    @model_validator(mode="after")
    def _validate_slack_configuration(self) -> IntegrationSettingsMixin:
        if not self.enable_slack_status_notifications:
            return self
        if not (self.slack_status_bot_token and self.slack_status_bot_token.strip()):
            raise ValueError(
                "ENABLE_SLACK_STATUS_NOTIFICATIONS=true requires SLACK_STATUS_BOT_TOKEN."
            )
        has_default = bool(self.slack_status_default_channels)
        has_overrides = any(self.slack_status_tenant_channel_map.values())
        if not (has_default or has_overrides):
            raise ValueError(
                "Provide SLACK_STATUS_DEFAULT_CHANNELS or tenant overrides when "
                "Slack alerts are enabled."
            )
        return self
