"""Pytest configuration for starter_cli tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from tests.utils.pytest_stripe import (
    configure_stripe_replay_option,
    register_stripe_replay_marker,
    skip_stripe_replay_if_disabled,
)


@pytest.fixture(autouse=True, scope="session")
def _ensure_import_paths() -> None:
    """Guarantee repo-local packages (starter_cli, api-service/app) are importable in CI."""

    repo_root = Path(__file__).resolve().parents[2]
    api_dir = repo_root / "api-service"
    for path in (repo_root, api_dir):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)

    # Configure deterministic key storage so auth-dependent tests can sign tokens.
    test_keyset = api_dir / "tests" / "fixtures" / "keysets" / "test_keyset.json"
    os.environ.setdefault("AUTH_KEY_STORAGE_BACKEND", "file")
    os.environ.setdefault("AUTH_KEY_STORAGE_PATH", str(test_keyset))
    os.environ.setdefault("STARTER_CLI_SKIP_VAULT_PROBE", "true")


def pytest_addoption(parser: pytest.Parser) -> None:
    configure_stripe_replay_option(parser)


def pytest_configure(config: pytest.Config) -> None:
    register_stripe_replay_marker(config)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    skip_stripe_replay_if_disabled(config, items)
