"""Repository factory for status subscriptions."""

from __future__ import annotations

from app.core.config import Settings, get_settings
from app.infrastructure.db import get_async_sessionmaker
from app.infrastructure.persistence.status.postgres import PostgresStatusSubscriptionRepository


def get_status_subscription_repository(
    settings: Settings | None = None,
) -> PostgresStatusSubscriptionRepository | None:
    resolved = settings or get_settings()
    if not resolved.database_url:
        return None
    secret = resolved.status_subscription_encryption_key or resolved.secret_key
    if not secret:
        raise RuntimeError(
            "STATUS_SUBSCRIPTION_ENCRYPTION_KEY or SECRET_KEY must be set to manage subscriptions."
        )
    session_factory = get_async_sessionmaker()
    return PostgresStatusSubscriptionRepository(
        session_factory,
        encryption_secret=secret,
    )
