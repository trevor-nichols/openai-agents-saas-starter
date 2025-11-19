"""Core configuration scaffolding for modular settings."""
from __future__ import annotations

import json
import logging
from types import MethodType
from typing import Any, Literal, cast

from pydantic_settings import BaseSettings
from pydantic_settings.sources import PydanticBaseSettingsSource

from app.domain.secrets import SecretsProviderLiteral

SAFE_ENVIRONMENTS = {"development", "dev", "local", "test"}
SignupAccessPolicyLiteral = Literal["public", "invite_only", "approval"]

VAULT_PROVIDER_KEYS = {
    SecretsProviderLiteral.VAULT_DEV,
    SecretsProviderLiteral.VAULT_HCP,
}

signup_policy_logger = logging.getLogger("app.core.config.signup")


class BaseAppSettings(BaseSettings):
    """Shared base for all application settings."""

    model_config = {
        "env_file": (".env.local", ".env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
        "populate_by_name": True,
    }

    @classmethod
    def settings_customise_sources(
        cls,
        _settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource | None,
        dotenv_settings: PydanticBaseSettingsSource | None,
        file_secret_settings: PydanticBaseSettingsSource | None,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Hook CSV parsing helpers into pydantic-settings sources."""

        cls._patch_auth_audience_parsing(env_settings)
        cls._patch_auth_audience_parsing(dotenv_settings)

        return tuple(
            source
            for source in (init_settings, env_settings, dotenv_settings, file_secret_settings)
            if source is not None
        )

    @staticmethod
    def _patch_auth_audience_parsing(source: PydanticBaseSettingsSource | None) -> None:
        if source is None:
            return
        original_prepare = source.prepare_field_value
        settings_cls: type[BaseSettings] | None = getattr(source, "settings_cls", None)

        def prepare_field_value(self, field_name, field, value, value_is_complex):
            parser = getattr(settings_cls, "parse_auth_audience_string", None)
            if field_name == "auth_audience" and isinstance(value, str) and callable(parser):
                return parser(value)
            return original_prepare(field_name, field, value, value_is_complex)

        cast(Any, source).prepare_field_value = MethodType(prepare_field_value, source)

    @staticmethod
    def parse_auth_audience_string(raw_value: str) -> list[str]:
        stripped = raw_value.strip()
        if not stripped:
            return []
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
        return [item.strip() for item in stripped.split(",") if item.strip()]

    @classmethod
    def parse_auth_audience_value(
        cls,
        value: str | list[str] | tuple[str, ...] | set[str] | None,
    ) -> list[str] | None:
        if value is None:
            return None
        if isinstance(value, str):
            items = cls.parse_auth_audience_string(value)
        elif isinstance(value, list | tuple | set):
            items = [str(item).strip() for item in value if str(item).strip()]
        else:
            raise ValueError("auth_audience must be a list or comma-separated string.")
        if not items:
            raise ValueError("auth_audience must include at least one audience identifier.")
        return list(dict.fromkeys(items))
