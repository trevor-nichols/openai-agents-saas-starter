"""Lightweight config bridge for the Agent Starter CLI.

This module exposes a narrow, import-safe surface that lets CLI code obtain the
backend's Pydantic settings without importing `anything-agents/app` directly at
module import time. The CLI should depend on the protocol defined here rather
than on the concrete FastAPI settings class.
"""

from __future__ import annotations

from functools import lru_cache
from importlib import import_module
from typing import Protocol, runtime_checkable


@runtime_checkable
class StarterSettingsProtocol(Protocol):
    """Subset of settings fields/methods required by the CLI."""

    vault_addr: str | None
    vault_token: str | None
    vault_transit_key: str
    auth_key_storage_backend: str
    auth_key_storage_path: str
    auth_key_secret_name: str | None
    enable_billing: bool
    enable_billing_retry_worker: bool
    allow_public_signup: bool
    signup_rate_limit_per_hour: int

    def secret_warnings(self) -> list[str]: ...

    def required_stripe_envs_missing(self) -> list[str]: ...


def _resolve_settings_class():
    try:
        module = import_module("app.core.config")
    except ModuleNotFoundError as exc:  # pragma: no cover - defensive
        raise RuntimeError("FastAPI settings module is unavailable") from exc
    try:
        return module.Settings
    except AttributeError as exc:  # pragma: no cover - defensive
        raise RuntimeError("app.core.config.Settings is missing") from exc


@lru_cache(maxsize=1)
def get_settings() -> StarterSettingsProtocol:
    """Lazily instantiate (and cache) the FastAPI settings object."""

    settings_cls = _resolve_settings_class()
    return settings_cls()  # type: ignore[return-value]


__all__ = ["StarterSettingsProtocol", "get_settings"]
