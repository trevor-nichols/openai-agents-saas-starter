"""Unit tests for SSO configuration helpers."""

from __future__ import annotations

import pytest

from app.services.sso.config import normalize_provider_key
from app.services.sso.errors import SsoConfigurationError


def test_normalize_provider_key_lowercases_and_trims() -> None:
    assert normalize_provider_key("  GoOgLE  ") == "google"


def test_normalize_provider_key_allows_underscores_and_digits() -> None:
    assert normalize_provider_key("okta_v2") == "okta_v2"


def test_normalize_provider_key_rejects_empty() -> None:
    with pytest.raises(SsoConfigurationError) as exc:
        normalize_provider_key("   ")
    assert exc.value.reason == "provider_required"


@pytest.mark.parametrize("value", ["bad-key", "bad key", "Bad.Key", "weird$"])
def test_normalize_provider_key_rejects_invalid_characters(value: str) -> None:
    with pytest.raises(SsoConfigurationError) as exc:
        normalize_provider_key(value)
    assert exc.value.reason == "provider_invalid"
