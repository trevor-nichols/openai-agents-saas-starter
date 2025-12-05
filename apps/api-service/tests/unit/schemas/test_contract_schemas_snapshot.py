"""Snapshot tests to freeze shared contracts (settings schema + enums).

These guardrails ensure backend + CLI stay aligned and any breaking changes are
intentional. Update the snapshots in ``docs/contracts`` only when schema
changes are deliberate.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, get_args

import pytest

# tests live under apps/api-service/tests/**, so repo root is four levels up
ROOT = Path(__file__).resolve().parents[4]
CONTRACTS_DIR = ROOT / "docs" / "contracts"


@pytest.fixture(autouse=True)
def _prepend_api_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure our local ``app`` package wins over any installed ``app`` module."""

    monkeypatch.syspath_prepend(str(ROOT / "apps" / "api-service" / "src"))


def _canonical(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _canonical(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        return [_canonical(v) for v in obj]
    return obj


def _load_snapshot(name: str) -> Any:
    path = CONTRACTS_DIR / name
    if not path.exists():
        raise AssertionError(f"Snapshot missing: {path}")
    return _canonical(json.loads(path.read_text(encoding="utf-8")))


def test_settings_schema_snapshot() -> None:
    from app.core.settings import Settings

    actual = _canonical(Settings().model_json_schema())
    expected = _load_snapshot("settings.schema.json")

    assert actual == expected


def test_provider_literal_snapshot() -> None:
    from starter_contracts.secrets.models import (
        SecretProviderStatus,
        SecretPurpose,
        SecretScope,
        SecretsProviderLiteral,
    )

    from app.core.settings import SignupAccessPolicyLiteral

    actual = {
        "secrets_provider_literal": sorted(item.value for item in SecretsProviderLiteral),
        "secret_scope": sorted(item.value for item in SecretScope),
        "secret_purpose": sorted(item.value for item in SecretPurpose),
        "secret_provider_status": sorted(item.value for item in SecretProviderStatus),
        "signup_access_policy_literal": sorted(get_args(SignupAccessPolicyLiteral)),
    }

    expected = _load_snapshot("provider_literals.json")

    assert actual == expected
