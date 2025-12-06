"""Stripe webhook intake endpoint."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, cast

import stripe
from fastapi import APIRouter, HTTPException, Request, status

from app.core.settings import get_settings
from app.infrastructure.persistence.stripe.repository import (
    StripeEventStatus,
    get_stripe_event_repository,
)
from app.observability.metrics import observe_stripe_webhook_event
from app.services.billing.billing_events import get_billing_events_service
from app.services.billing.stripe.dispatcher import stripe_event_dispatcher

SignatureVerificationError = cast(
    type[Exception],
    getattr(getattr(stripe, "error", None), "SignatureVerificationError", Exception),
)

logger = logging.getLogger("api-service.webhooks.stripe")

router = APIRouter()


@router.post("/webhooks/stripe", status_code=status.HTTP_202_ACCEPTED)
async def handle_stripe_webhook(request: Request) -> dict[str, bool]:
    settings = get_settings()
    secret = settings.stripe_webhook_secret
    if not secret:
        logger.error("STRIPE_WEBHOOK_SECRET is not configured; rejecting webhook call")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook secret not configured.",
        )

    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    if not signature:
        observe_stripe_webhook_event(event_type="unknown", result="missing_signature")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Stripe signature header."
        )

    try:
        event = stripe.Webhook.construct_event(
            payload=payload.decode("utf-8"), sig_header=signature, secret=secret
        )
    except ValueError as exc:  # pragma: no cover - invalid JSON
        observe_stripe_webhook_event(event_type="unknown", result="invalid_json")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload."
        ) from exc
    except SignatureVerificationError as exc:
        observe_stripe_webhook_event(event_type="unknown", result="invalid_signature")
        message = getattr(exc, "user_message", None) or str(exc)
        logger.warning("Stripe signature verification failed: %s", message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Signature verification failed."
        ) from exc

    event_dict = event.to_dict_recursive()
    event_type = event_dict.get("type", "unknown")
    tenant_hint = _extract_tenant_hint(event_dict)
    stripe_created = _extract_created(event_dict)

    repository = get_stripe_event_repository()
    record, created = await repository.upsert_event(
        stripe_event_id=event_dict["id"],
        event_type=event_type,
        payload=event_dict,
        tenant_hint=tenant_hint,
        stripe_created_at=stripe_created,
    )

    if not created:
        observe_stripe_webhook_event(event_type=event_type, result="duplicate")
        logger.info(
            "Received duplicate Stripe event; ignoring",
            extra={"stripe_event_id": event_dict["id"], "event_type": event_type},
        )
        return {"success": True, "duplicate": True}

    dispatch_result = None
    try:
        dispatch_result = await stripe_event_dispatcher.dispatch_now(record, event_dict)
    except Exception as exc:  # pragma: no cover - exercised via mocks
        observe_stripe_webhook_event(event_type=event_type, result="dispatch_failed")
        logger.exception(
            "Stripe webhook handler failed",
            extra={"stripe_event_id": event_dict["id"], "event_type": event_type},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process event."
        ) from exc

    processed_at = dispatch_result.processed_at if dispatch_result else None
    if processed_at:
        record.processed_at = processed_at
    record.processing_outcome = StripeEventStatus.PROCESSED.value
    if settings.enable_billing_stream:
        events_service = get_billing_events_service()
        try:
            await events_service.publish_from_event(
                record, event_dict, context=dispatch_result.broadcast if dispatch_result else None
            )
        except Exception as exc:  # pragma: no cover - failure path exercised via mocks
            failure_time = await repository.record_outcome(
                record.id,
                status=StripeEventStatus.FAILED,
                error=str(exc),
            )
            record.processed_at = failure_time
            record.processing_outcome = StripeEventStatus.FAILED.value
            observe_stripe_webhook_event(event_type=event_type, result="stream_failed")
            logger.exception(
                "Stripe billing stream publish failed",
                extra={"stripe_event_id": event_dict["id"], "event_type": event_type},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to publish billing event.",
            ) from exc
        await events_service.mark_processed(processed_at)
    observe_stripe_webhook_event(event_type=event_type, result="dispatched")
    logger.info(
        "Stored Stripe event",
        extra={
            "stripe_event_id": event_dict["id"],
            "event_type": event_type,
            "tenant": tenant_hint,
        },
    )
    return {"success": True, "duplicate": False}


def _extract_tenant_hint(event: dict[str, Any]) -> str | None:
    data_object = (event.get("data") or {}).get("object") or {}
    metadata = data_object.get("metadata") or {}
    tenant = metadata.get("tenant_id") or metadata.get("tenant")
    if tenant:
        return str(tenant)
    return None


def _extract_created(event: dict[str, Any]) -> datetime | None:
    created = event.get("created")
    if created is None:
        return None
    return datetime.fromtimestamp(float(created), tz=UTC)
