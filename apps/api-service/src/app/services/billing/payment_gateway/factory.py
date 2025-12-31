"""Gateway selection for billing services."""

from __future__ import annotations

import logging

from app.core.settings import Settings, get_settings

from .fixture_gateway import get_fixture_gateway
from .protocol import PaymentGateway

logger = logging.getLogger("api-service.services.payment_gateway")
_fixture_gateway_logged = False


def get_payment_gateway(settings: Settings | None = None) -> PaymentGateway:
    """Return the configured payment gateway implementation."""

    global _fixture_gateway_logged
    settings = settings or get_settings()
    if settings.use_test_fixtures:
        if not _fixture_gateway_logged:
            logger.warning(
                "Using fixture billing gateway because USE_TEST_FIXTURES is enabled."
            )
            _fixture_gateway_logged = True
        return get_fixture_gateway()
    from app.services.billing.stripe.gateway import get_stripe_gateway

    return get_stripe_gateway()


__all__ = ["get_payment_gateway"]
