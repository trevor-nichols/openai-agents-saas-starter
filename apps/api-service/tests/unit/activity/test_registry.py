from __future__ import annotations

import pytest

from app.services.activity.registry import REGISTRY, validate_action


def test_validate_action_allows_whitelisted_metadata() -> None:
    validate_action("auth.login.success", {"user_id": "u1", "tenant_id": "t1"})


def test_validate_service_account_issued_allows_reason() -> None:
    validate_action(
        "auth.service_account.issued",
        {"service_account": "sa-demo", "scopes": "a b", "reason": "issued"},
    )


def test_validate_invoice_failed_allows_total_and_reason() -> None:
    validate_action(
        "billing.invoice.failed",
        {"invoice_id": "inv_123", "total": 100, "reason": "card_declined"},
    )


def test_validate_workflow_run_cancelled() -> None:
    validate_action(
        "workflow.run.cancelled",
        {"workflow_key": "analysis", "run_id": "run-1"},
    )


@pytest.mark.parametrize(
    ("action", "metadata"),
    [
        ("auth.login.success", None),
        ("billing.invoice.failed", {"invoice_id": "inv_123", "extra": "x"}),
    ],
)
def test_validate_action_raises_on_missing_or_extra(action: str, metadata) -> None:
    with pytest.raises(ValueError):
        validate_action(action, metadata)


def test_validate_action_rejects_unknown_action() -> None:
    with pytest.raises(ValueError):
        validate_action("unknown.action", {})
