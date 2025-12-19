from app.infrastructure.persistence.conversations.usage_store import _normalize_requests


def test_normalize_requests_defaults_to_one_when_missing():
    assert _normalize_requests(None) == 1


def test_normalize_requests_clamps_negative_to_zero():
    assert _normalize_requests(-3) == 0


def test_normalize_requests_passes_through_positive_values():
    assert _normalize_requests(2) == 2
