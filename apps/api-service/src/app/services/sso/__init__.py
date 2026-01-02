"""SSO services package."""

from .errors import (
    SsoConfigurationError,
    SsoIdentityError,
    SsoProvisioningError,
    SsoServiceError,
    SsoStateError,
    SsoTokenError,
)
from .factory import build_sso_service, get_sso_service
from .models import SsoStartResult
from .oidc_client import (
    OidcClient,
    OidcDiscoveryDocument,
    OidcDiscoveryError,
    OidcError,
    OidcTokenExchangeError,
    OidcTokenResponse,
    OidcTokenVerificationError,
)
from .service import SsoService
from .state_store import SsoStatePayload, SsoStateStore, build_sso_state_store

__all__ = [
    "OidcClient",
    "OidcDiscoveryDocument",
    "OidcDiscoveryError",
    "OidcError",
    "OidcTokenExchangeError",
    "OidcTokenResponse",
    "OidcTokenVerificationError",
    "SsoConfigurationError",
    "SsoIdentityError",
    "SsoProvisioningError",
    "SsoService",
    "SsoServiceError",
    "SsoStartResult",
    "SsoStatePayload",
    "SsoStateStore",
    "SsoStateError",
    "SsoTokenError",
    "build_sso_service",
    "build_sso_state_store",
    "get_sso_service",
]
