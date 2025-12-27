"""User directory services."""

from __future__ import annotations

from app.domain.users import PasswordReuseError

from .errors import (
    EmailAlreadyInUseError,
    InvalidCredentialsError,
    IpThrottledError,
    LastOwnerRemovalError,
    MembershipNotFoundError,
    PasswordPolicyViolationError,
    TenantContextRequiredError,
    UserDisabledError,
    UserLockedError,
    UserServiceError,
)
from .factory import build_user_service, get_user_service
from .service import UserService
from .throttling import LoginThrottle, NullLoginThrottle, RedisLoginThrottle, build_ip_throttler

__all__ = [
    "build_ip_throttler",
    "build_user_service",
    "EmailAlreadyInUseError",
    "get_user_service",
    "InvalidCredentialsError",
    "IpThrottledError",
    "LastOwnerRemovalError",
    "LoginThrottle",
    "MembershipNotFoundError",
    "NullLoginThrottle",
    "PasswordReuseError",
    "PasswordPolicyViolationError",
    "RedisLoginThrottle",
    "TenantContextRequiredError",
    "UserDisabledError",
    "UserLockedError",
    "UserService",
    "UserServiceError",
]
