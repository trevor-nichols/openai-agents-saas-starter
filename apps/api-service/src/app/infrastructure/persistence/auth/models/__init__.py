"""ORM models for the auth bounded context."""

from app.infrastructure.persistence.auth.models.consent import (
    UserConsent,
    UserNotificationPreference,
)
from app.infrastructure.persistence.auth.models.membership import TenantUserMembership
from app.infrastructure.persistence.auth.models.mfa import MfaMethodType, UserMfaMethod
from app.infrastructure.persistence.auth.models.security import SecurityEvent
from app.infrastructure.persistence.auth.models.sessions import ServiceAccountToken, UserSession
from app.infrastructure.persistence.auth.models.signup import (
    TenantSignupInvite,
    TenantSignupInviteReservation,
    TenantSignupRequest,
)
from app.infrastructure.persistence.auth.models.user import (
    PasswordHistory,
    UserAccount,
    UserLoginEvent,
    UserProfile,
    UserStatus,
)
from app.infrastructure.persistence.usage.models import UsageCounter, UsageCounterGranularity

__all__ = [
    "MfaMethodType",
    "UserMfaMethod",
    "PasswordHistory",
    "SecurityEvent",
    "ServiceAccountToken",
    "TenantSignupInvite",
    "TenantSignupInviteReservation",
    "TenantSignupRequest",
    "TenantUserMembership",
    "UsageCounter",
    "UsageCounterGranularity",
    "UserAccount",
    "UserConsent",
    "UserLoginEvent",
    "UserNotificationPreference",
    "UserProfile",
    "UserSession",
    "UserStatus",
]
