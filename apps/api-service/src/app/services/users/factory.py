"""Factory helpers for UserService and collaborators."""

from __future__ import annotations

from typing import cast

from app.core.settings import Settings, get_settings
from app.domain.users import UserRepository
from app.infrastructure.persistence.auth.user_repository import get_user_repository
from app.services.activity import get_activity_service

from .service import UserService
from .throttling import LoginThrottle, build_ip_throttler


def build_user_service(
    *,
    settings: Settings | None = None,
    repository=None,
    ip_throttler: LoginThrottle | None = None,
) -> UserService:
    """Construct a UserService with explicit dependencies."""

    resolved_settings = settings or get_settings()
    resolved_repository = repository or get_user_repository(resolved_settings)
    if resolved_repository is None:
        raise RuntimeError(
            "User repository is not configured. "
            "Run Postgres migrations and provide DATABASE_URL."
        )
    resolved_throttler = ip_throttler or build_ip_throttler(resolved_settings)
    activity_recorder = get_activity_service()
    return UserService(
        cast(UserRepository, resolved_repository),
        settings=resolved_settings,
        ip_throttler=resolved_throttler,
        activity_recorder=activity_recorder,
    )


def get_user_service() -> UserService:
    """Fetch the configured user service from the application container."""

    from app.bootstrap.container import get_container

    container = get_container()
    if container.user_service is None:
        container.user_service = build_user_service()
    return container.user_service


__all__ = ["build_user_service", "get_user_service"]
