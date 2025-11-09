"""Auth service subpackage with focused helpers."""

from .errors import (
    ServiceAccountCatalogUnavailable,
    ServiceAccountError,
    ServiceAccountRateLimitError,
    ServiceAccountValidationError,
    UserAuthenticationError,
    UserLogoutError,
    UserRefreshError,
)
from .refresh_token_manager import RefreshTokenManager
from .service_account_service import ServiceAccountTokenService
from .session_service import UserSessionService
from .session_store import SessionStore

__all__ = [
    "ServiceAccountTokenService",
    "UserSessionService",
    "SessionStore",
    "RefreshTokenManager",
    "ServiceAccountError",
    "ServiceAccountCatalogUnavailable",
    "ServiceAccountRateLimitError",
    "ServiceAccountValidationError",
    "UserAuthenticationError",
    "UserLogoutError",
    "UserRefreshError",
]
