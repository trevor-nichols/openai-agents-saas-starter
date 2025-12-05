"""Factory helpers for auth-related services."""

from __future__ import annotations

from app.core.service_accounts import ServiceAccountRegistry, get_default_service_account_registry
from app.core.settings import Settings, get_settings
from app.infrastructure.persistence.auth.repository import get_refresh_token_repository
from app.infrastructure.persistence.auth.session_repository import get_user_session_repository
from app.services.auth import RefreshTokenManager, SessionStore
from app.services.auth.service_account_service import ServiceAccountTokenService
from app.services.auth.session_service import UserSessionService
from app.services.geoip_service import GeoIPService, NullGeoIPService
from app.services.users import UserService


def build_session_service(
    *,
    settings: Settings | None = None,
    user_service: UserService | None = None,
    geoip_service: GeoIPService | None = None,
) -> UserSessionService:
    settings = settings or get_settings()
    refresh_repo = get_refresh_token_repository()
    session_repo = get_user_session_repository()
    refresh_manager = RefreshTokenManager(refresh_repo)
    session_store = SessionStore(session_repo, geoip_service or NullGeoIPService())
    return UserSessionService(
        refresh_tokens=refresh_manager,
        session_store=session_store,
        user_service=user_service,
    )


def build_service_account_token_service(
    *,
    registry: ServiceAccountRegistry | None = None,
    settings: Settings | None = None,
) -> ServiceAccountTokenService:
    resolved_settings = settings or get_settings()
    refresh_repo = get_refresh_token_repository()
    refresh_manager = RefreshTokenManager(refresh_repo)
    resolved_registry = registry or get_default_service_account_registry()
    return ServiceAccountTokenService(
        registry=resolved_registry,
        refresh_tokens=refresh_manager,
        settings=resolved_settings,
    )


__all__ = [
    "build_session_service",
    "build_service_account_token_service",
]
