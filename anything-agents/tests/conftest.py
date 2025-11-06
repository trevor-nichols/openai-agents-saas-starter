"""Shared pytest fixtures for anything-agents tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core import config as config_module

TEST_KEYSET_PATH = Path(__file__).parent / "fixtures" / "keysets" / "test_keyset.json"


@pytest.fixture(autouse=True)
def _configure_auth_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Point key storage + auth settings at deterministic test fixtures."""

    monkeypatch.setenv("AUTH_KEY_STORAGE_BACKEND", "file")
    monkeypatch.setenv("AUTH_KEY_STORAGE_PATH", str(TEST_KEYSET_PATH))
    monkeypatch.setenv("AUTH_REFRESH_TOKEN_PEPPER", "test-refresh-pepper")
    monkeypatch.setenv("AUTH_DUAL_SIGNING_ENABLED", "false")
    config_module.get_settings.cache_clear()
    try:
        yield
    finally:
        config_module.get_settings.cache_clear()
