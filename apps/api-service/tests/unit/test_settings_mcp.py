"""Validation tests for hosted MCP tool settings."""

from __future__ import annotations

import pytest

from app.core.settings import Settings


def test_mcp_tool_settings_accepts_server_url() -> None:
    settings = Settings(
        _env_file=None,
        mcp_tools=[
            {
                "name": "demo_mcp",
                "server_label": "demo",
                "server_url": "https://demo.mcp",
            }
        ],
    )

    assert len(settings.mcp_tools) == 1
    tool = settings.mcp_tools[0]
    assert tool.name == "demo_mcp"
    assert tool.require_approval == "always"


def test_mcp_tool_settings_connector_requires_auth() -> None:
    with pytest.raises(ValueError):
        Settings(
            _env_file=None,
            mcp_tools=[
                {
                    "name": "conn_mcp",
                    "server_label": "conn",
                    "connector_id": "connector_dropbox",
                }
            ],
        )


def test_mcp_tool_settings_rejects_duplicate_names() -> None:
    with pytest.raises(ValueError):
        Settings(
            _env_file=None,
            mcp_tools=[
                {
                    "name": "dup",
                    "server_label": "one",
                    "server_url": "https://one.mcp",
                },
                {
                    "name": "dup",
                    "server_label": "two",
                    "server_url": "https://two.mcp",
                },
            ],
        )


def test_mcp_tool_settings_rejects_duplicate_server_labels() -> None:
    with pytest.raises(ValueError):
        Settings(
            _env_file=None,
            mcp_tools=[
                {
                    "name": "one",
                    "server_label": "dup",
                    "server_url": "https://one.mcp",
                },
                {
                    "name": "two",
                    "server_label": "dup",
                    "server_url": "https://two.mcp",
                },
            ],
        )


def test_mcp_tool_settings_validates_require_approval() -> None:
    with pytest.raises(ValueError):
        Settings(
            _env_file=None,
            mcp_tools=[
                {
                    "name": "invalid",
                    "server_label": "invalid",
                    "server_url": "https://invalid.mcp",
                    "require_approval": "sometimes",
                }
            ],
        )


def test_mcp_tool_settings_rejects_allow_deny_overlap() -> None:
    with pytest.raises(ValueError):
        Settings(
            _env_file=None,
            mcp_tools=[
                {
                    "name": "dup",
                    "server_label": "dup",
                    "server_url": "https://dup.mcp",
                    "auto_approve_tools": ["read"],
                    "deny_tools": ["read"],
                }
            ],
        )

def test_mcp_tool_settings_parses_json_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "MCP_TOOLS",
        '[{"name":"env_mcp","server_label":"env","server_url":"https://env.mcp"}]',
    )

    settings = Settings(_env_file=None)

    assert len(settings.mcp_tools) == 1
    assert settings.mcp_tools[0].name == "env_mcp"
