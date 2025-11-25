"""Pytest configuration for starter_cli tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from starter_contracts import config as shared_config

# Make sure repo-local packages and shared test helpers are importable before
# importing anything that relies on them (e.g., api-service test utilities).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_API_DIR = _REPO_ROOT / "api-service"
_API_SRC = _API_DIR / "src"
_API_TESTS = _API_DIR / "tests"
for _path in (_REPO_ROOT, _API_DIR, _API_SRC, _API_TESTS):
    _path_str = str(_path)
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)

from app.core import config as api_config
from tests.utils.pytest_stripe import (
    configure_stripe_replay_option,
    register_stripe_replay_marker,
    skip_stripe_replay_if_disabled,
)


@pytest.fixture(autouse=True, scope="session")
def _ensure_import_paths() -> None:
    """Guarantee repo-local packages (starter_cli, api-service/src/app) are importable in CI."""

    repo_root = _REPO_ROOT
    api_dir = _API_DIR

    # Configure deterministic key storage so auth-dependent tests can sign tokens.
    test_keyset = api_dir / "tests" / "fixtures" / "keysets" / "test_keyset.json"
    os.environ["AUTH_KEY_STORAGE_BACKEND"] = "file"
    os.environ["AUTH_KEY_STORAGE_PATH"] = str(test_keyset)
    os.environ["STARTER_CLI_SKIP_VAULT_PROBE"] = "true"
    # Ensure API app boots without external services during contract tests.
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    os.environ.setdefault("OPENAI_API_KEY", "test-key")
    # Ensure settings pick up the overrides
    api_config.get_settings.cache_clear()
    shared_config.get_settings.cache_clear()


def pytest_addoption(parser: pytest.Parser) -> None:
    configure_stripe_replay_option(parser)


def pytest_configure(config: pytest.Config) -> None:
    register_stripe_replay_marker(config)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    skip_stripe_replay_if_disabled(config, items)
