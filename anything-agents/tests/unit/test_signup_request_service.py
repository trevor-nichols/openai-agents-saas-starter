"""Focused unit tests for signup request service helpers."""

from uuid import uuid4

from app.services.signup_request_service import _normalize_uuid


def test_normalize_uuid_accepts_uuid_instance() -> None:
    sample = uuid4()

    assert _normalize_uuid(sample) == sample


def test_normalize_uuid_accepts_string_representation() -> None:
    sample = uuid4()

    assert _normalize_uuid(str(sample)) == sample


def test_normalize_uuid_returns_none_for_invalid_string() -> None:
    assert _normalize_uuid("not-a-uuid") is None


def test_normalize_uuid_returns_none_for_blank_input() -> None:
    assert _normalize_uuid("   ") is None
