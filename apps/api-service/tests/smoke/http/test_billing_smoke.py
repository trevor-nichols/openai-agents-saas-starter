from __future__ import annotations

import uuid

import httpx
import pytest

from tests.smoke.http.auth import auth_headers
from tests.smoke.http.config import SmokeConfig
from tests.smoke.http.helpers import fetch_first_sse_line, require_enabled
from tests.smoke.http.state import SmokeState


pytestmark = [pytest.mark.smoke, pytest.mark.asyncio]


def _pick_plan_code(catalog: list[dict[str, object]], preferred: str | None) -> str:
    if preferred:
        for plan in catalog:
            if plan.get("code") == preferred:
                return preferred
    for plan in catalog:
        code = plan.get("code")
        if isinstance(code, str) and code:
            return code
    raise AssertionError("No billing plan codes available to start subscription.")


async def test_billing_subscription_lifecycle_and_events(
    http_client: httpx.AsyncClient,
    smoke_config: SmokeConfig,
    smoke_state: SmokeState,
) -> None:
    require_enabled(smoke_config.enable_billing, reason="SMOKE_ENABLE_BILLING not enabled")

    headers = auth_headers(smoke_state, tenant_role="owner")

    plans = await http_client.get("/api/v1/billing/plans", headers=headers)
    assert plans.status_code == 200, plans.text
    catalog = plans.json()
    assert isinstance(catalog, list)

    sub = await http_client.get(
        f"/api/v1/billing/tenants/{smoke_state.tenant_id}/subscription", headers=headers
    )
    assert sub.status_code == 200, sub.text
    current = sub.json()
    assert current.get("tenant_id") == smoke_state.tenant_id

    preferred_plan = current.get("plan_code")
    plan_code = _pick_plan_code(
        catalog, preferred_plan if isinstance(preferred_plan, str) else None
    )

    start_payload = {
        "plan_code": plan_code,
        "billing_email": smoke_config.admin_email,
        "auto_renew": True,
    }
    start = await http_client.post(
        f"/api/v1/billing/tenants/{smoke_state.tenant_id}/subscription",
        json=start_payload,
        headers=headers,
    )
    assert start.status_code == 201, start.text
    start_body = start.json()
    assert start_body.get("tenant_id") == smoke_state.tenant_id
    assert start_body.get("plan_code") == plan_code

    updated_email = f"smoke-billing+{uuid.uuid4().hex[:8]}@example.com"
    update = await http_client.patch(
        f"/api/v1/billing/tenants/{smoke_state.tenant_id}/subscription",
        json={"billing_email": updated_email},
        headers=headers,
    )
    assert update.status_code == 200, update.text
    update_body = update.json()
    assert update_body.get("billing_email") == updated_email

    portal = await http_client.post(
        f"/api/v1/billing/tenants/{smoke_state.tenant_id}/portal",
        json={"billing_email": updated_email},
        headers=headers,
    )
    assert portal.status_code == 200, portal.text
    portal_body = portal.json()
    portal_url = portal_body.get("url")
    assert isinstance(portal_url, str)
    assert portal_url

    setup_intent = await http_client.post(
        f"/api/v1/billing/tenants/{smoke_state.tenant_id}/payment-methods/setup-intent",
        json={"billing_email": updated_email},
        headers=headers,
    )
    assert setup_intent.status_code == 200, setup_intent.text
    setup_body = setup_intent.json()
    assert isinstance(setup_body.get("id"), str)

    payment_methods = await http_client.get(
        f"/api/v1/billing/tenants/{smoke_state.tenant_id}/payment-methods",
        headers=headers,
    )
    assert payment_methods.status_code == 200, payment_methods.text
    methods_body = payment_methods.json()
    assert isinstance(methods_body, list)

    preview = await http_client.post(
        f"/api/v1/billing/tenants/{smoke_state.tenant_id}/upcoming-invoice",
        json={"seat_count": 1},
        headers=headers,
    )
    assert preview.status_code == 200, preview.text
    preview_body = preview.json()
    assert preview_body.get("plan_code") == plan_code

    alternate_plan = next(
        (
            plan.get("code")
            for plan in catalog
            if plan.get("code") != plan_code
        ),
        None,
    )
    if isinstance(alternate_plan, str) and alternate_plan:
        change = await http_client.post(
            f"/api/v1/billing/tenants/{smoke_state.tenant_id}/subscription/plan",
            json={"plan_code": alternate_plan, "timing": "period_end"},
            headers=headers,
        )
        assert change.status_code == 200, change.text
        change_body = change.json()
        assert change_body.get("target_plan_code") == alternate_plan
        subscription_payload = change_body.get("subscription", {})
        assert subscription_payload.get("pending_plan_code") == alternate_plan

    usage = await http_client.post(
        f"/api/v1/billing/tenants/{smoke_state.tenant_id}/usage",
        json={
            "feature_key": "smoke.requests",
            "quantity": 1,
            "idempotency_key": f"smoke-{uuid.uuid4().hex}",
        },
        headers=headers,
    )
    assert usage.status_code == 202, usage.text
    usage_body = usage.json()
    assert usage_body.get("message") == "Usage recorded."

    totals = await http_client.get(
        f"/api/v1/billing/tenants/{smoke_state.tenant_id}/usage-totals",
        headers=headers,
    )
    assert totals.status_code == 200, totals.text
    totals_body = totals.json()
    assert isinstance(totals_body, list)
    matched = next(
        (
            item
            for item in totals_body
            if item.get("feature_key") == "smoke.requests"
        ),
        None,
    )
    assert matched is not None, "Expected usage totals for smoke.requests"
    assert isinstance(matched.get("quantity"), int)
    assert matched.get("quantity") >= 1

    events = await http_client.get(
        f"/api/v1/billing/tenants/{smoke_state.tenant_id}/events",
        headers=headers,
    )
    assert events.status_code == 200, events.text
    events_body = events.json()
    items = events_body.get("items", [])
    assert isinstance(items, list)

    cancel = await http_client.post(
        f"/api/v1/billing/tenants/{smoke_state.tenant_id}/subscription/cancel",
        json={"cancel_at_period_end": True},
        headers=headers,
    )
    assert cancel.status_code == 200, cancel.text
    cancel_body = cancel.json()
    assert cancel_body.get("tenant_id") == smoke_state.tenant_id
    assert cancel_body.get("plan_code") == plan_code
    assert cancel_body.get("cancel_at") is not None


async def test_billing_stream_handshake(
    http_client: httpx.AsyncClient,
    smoke_config: SmokeConfig,
    smoke_state: SmokeState,
) -> None:
    require_enabled(smoke_config.enable_billing, reason="SMOKE_ENABLE_BILLING not enabled")
    require_enabled(
        smoke_config.enable_billing_stream,
        reason="SMOKE_ENABLE_BILLING_STREAM not enabled",
    )

    line = await fetch_first_sse_line(
        http_client,
        "GET",
        "/api/v1/billing/stream",
        headers=auth_headers(smoke_state, tenant_role="owner"),
        timeout_seconds=smoke_config.request_timeout,
    )
    assert line.startswith(":") or line.startswith("data:")
