from __future__ import annotations

import pytest

from starter_console.core import CLIError
from starter_console.services.auth.status_ops import DEFAULT_STATUS_BASE_URL, load_status_api_config


def test_status_ops_requires_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("STATUS_API_TOKEN", raising=False)
    monkeypatch.delenv("API_BASE_URL", raising=False)
    with pytest.raises(CLIError):
        load_status_api_config()


def test_status_ops_prefers_api_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STATUS_API_TOKEN", "token")
    monkeypatch.setenv("API_BASE_URL", "https://api.example")
    config = load_status_api_config()
    assert config.base_url == "https://api.example"


def test_status_ops_uses_default_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STATUS_API_TOKEN", "token")
    monkeypatch.delenv("API_BASE_URL", raising=False)
    config = load_status_api_config()
    assert config.base_url == DEFAULT_STATUS_BASE_URL
