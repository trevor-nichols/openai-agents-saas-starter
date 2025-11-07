"""Stripe webhook intake endpoint."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import stripe
from fastapi import APIRouter, HTTPException, Request, status

from app.core.config import get_settings
from app.infrastructure.persistence.stripe.repository import (
    StripeEventStatus,
    get_stripe_event_repository,
)
from app.observability.metrics import observe_stripe_webhook_event
from app.services.billing_events import get_billing_events_service

logger = logging.getLogger("anything-agents.webhooks.stripe")

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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Stripe signature header.")

    try:
        event = stripe.Webhook.construct_event(payload=payload.decode("utf-8"), sig_header=signature, secret=secret)
    except ValueError as exc:  # pragma: no cover - invalid JSON
        observe_stripe_webhook_event(event_type="unknown", result="invalid_json")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload.") from exc
    except stripe.error.SignatureVerificationError as exc:
        observe_stripe_webhook_event(event_type="unknown", result="invalid_signature")
        logger.warning("Stripe signature verification failed: %s", exc.user_message or str(exc))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Signature verification failed.") from exc

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

    try:
        await _dispatch_event(event_dict)
    except Exception as exc:  # pragma: no cover - exercised in tests via failure path
        failure_time = await repository.record_outcome(record.id, status=StripeEventStatus.FAILED, error=str(exc))
        record.processed_at = failure_time
        record.processing_outcome = StripeEventStatus.FAILED.value
        observe_stripe_webhook_event(event_type=event_type, result="failed")
        logger.exception(
            "Stripe webhook handler failed",
            extra={"stripe_event_id": event_dict["id"], "event_type": event_type},
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process event.") from exc

    if settings.enable_billing_stream:
        events_service = get_billing_events_service()
        try:
            await events_service.publish_from_event(record, event_dict)
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

    processed_at = await repository.record_outcome(record.id, status=StripeEventStatus.PROCESSED)
    record.processed_at = processed_at
    record.processing_outcome = StripeEventStatus.PROCESSED.value
    observe_stripe_webhook_event(event_type=event_type, result="processed")
    logger.info(
        "Stored Stripe event",
        extra={"stripe_event_id": event_dict["id"], "event_type": event_type, "tenant": tenant_hint},
    )
    return {"success": True, "duplicate": False}


async def _dispatch_event(event: dict) -> None:
    event_type = event.get("type")
    if event_type in {
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
        "invoice.paid",
        "invoice.payment_failed",
    }:
        logger.info("Stripe subscription event received", extra={"event_type": event_type})
        return

    logger.debug("Unhandled Stripe event type: %s", event_type)


def _extract_tenant_hint(event: dict) -> str | None:
    data_object = (event.get("data") or {}).get("object") or {}
    metadata = data_object.get("metadata") or {}
    tenant = metadata.get("tenant_id") or metadata.get("tenant")
    if tenant:
        return str(tenant)
    return None


def _extract_created(event: dict) -> datetime | None:
    created = event.get("created")
    if created is None:
        return None
    return datetime.fromtimestamp(float(created), tz=timezone.utc)
