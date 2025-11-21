"""Unit tests for auth domain helpers."""

from __future__ import annotations

import pytest

from app.domain.auth import hash_refresh_token, verify_refresh_token


@pytest.mark.parametrize("pepper", ["pepper-one", "pepper-two"])
def test_hash_refresh_token_round_trip(pepper: str) -> None:
    token = "refresh-token-value"
    digest = hash_refresh_token(token, pepper=pepper)

    assert digest != token
    assert verify_refresh_token(token, digest, pepper=pepper)


def test_verify_refresh_token_rejects_wrong_pepper() -> None:
    token = "refresh-token-value"
    digest = hash_refresh_token(token, pepper="pepper-a")

    assert not verify_refresh_token(token, digest, pepper="pepper-b")


def test_hash_refresh_token_requires_pepper() -> None:
    with pytest.raises(ValueError):
        hash_refresh_token("token", pepper="")
