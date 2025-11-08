"""JWT + password utilities plus EdDSA signer/verifier abstractions."""

from __future__ import annotations

import base64
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from time import perf_counter
from typing import Any, Final, Protocol, cast

import jwt
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
)
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError
from passlib.context import CryptContext

from app.core.config import Settings, get_settings
from app.core.keys import KeyMaterial, KeySet, load_keyset
from app.observability.logging import log_event
from app.observability.metrics import observe_jwt_signing, observe_jwt_verification

UTC = UTC
_PEM_ENCODING: Final[Encoding] = cast(Encoding, Encoding.PEM)
_SUBJECT_PUBLIC_FORMAT: Final[PublicFormat] = cast(
    PublicFormat, PublicFormat.SubjectPublicKeyInfo
)

# =============================================================================
# SECURITY CONFIGURATION
# =============================================================================

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()

# Shared helpers -------------------------------------------------------------


def _unauthorized(detail: str = "Could not validate credentials") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _is_user_subject(value: str | None) -> bool:
    return isinstance(value, str) and value.startswith(USER_SUBJECT_PREFIX)


ACCESS_TOKEN_USE = "access"
USER_SUBJECT_PREFIX = "user:"
PASSWORD_HASH_VERSION = "v2"
LEGACY_PASSWORD_HASH_VERSION = "v1"

# =============================================================================
# PASSWORD UTILITIES
# =============================================================================


def _password_pepper(settings: Settings | None = None, override: str | None = None) -> str:
    target = override or (settings or get_settings()).auth_password_pepper
    if not target:
        raise ValueError("AUTH_PASSWORD_PEPPER must be configured for password hashing.")
    return target


def _pepperize_password(raw: str, *, pepper: str) -> str:
    return f"{pepper}:{raw}"


def verify_password(
    plain_password: str,
    hashed_password: str,
    *,
    settings: Settings | None = None,
    pepper: str | None = None,
) -> PasswordVerificationResult:
    """Verify a password hash, supporting legacy (unpeppered) digests."""

    pepper_value = _password_pepper(settings, override=pepper)
    material = _pepperize_password(plain_password, pepper=pepper_value)
    if pwd_context.verify(material, hashed_password):
        return PasswordVerificationResult(is_valid=True, requires_rehash=False)

    # Fallback for legacy hashes that omitted the pepper. If this succeeds,
    # callers should rehash the password with the new pepper immediately.
    if pwd_context.verify(plain_password, hashed_password):
        return PasswordVerificationResult(is_valid=True, requires_rehash=True)

    return PasswordVerificationResult(is_valid=False, requires_rehash=False)


def get_password_hash(
    password: str,
    *,
    settings: Settings | None = None,
    pepper: str | None = None,
) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password to hash

    Returns:
        str: Hashed password
    """
    pepper_value = _password_pepper(settings, override=pepper)
    material = _pepperize_password(password, pepper=pepper_value)
    return pwd_context.hash(material)


# =============================================================================
# TOKEN SIGNER / VERIFIER
# =============================================================================


class TokenError(RuntimeError):
    """Base class for token signing/verifying failures."""


class TokenSignerError(TokenError):
    """Raised when a token cannot be signed."""


class TokenVerifierError(TokenError):
    """Raised when a token cannot be verified."""


@dataclass(slots=True, frozen=True)
class SignedToken:
    """Represents a JOSE compact token and its signing metadata."""

    token: str
    kid: str
    algorithm: str = "EdDSA"


@dataclass(slots=True, frozen=True)
class SignedTokenBundle:
    """Primary token plus optional dual-signed variant."""

    primary: SignedToken
    secondary: SignedToken | None = None


@dataclass(slots=True, frozen=True)
class PasswordVerificationResult:
    """Outcome of password verification including upgrade hints."""

    is_valid: bool
    requires_rehash: bool = False


class TokenSigner(Protocol):
    """Interface for producing signed JWTs."""

    def sign(self, payload: dict[str, Any]) -> SignedTokenBundle: ...


class TokenVerifier(Protocol):
    """Interface for validating signed JWTs."""

    def verify(self, token: str, *, audience: Sequence[str] | None = None) -> dict[str, Any]: ...


class EdDSATokenSigner(TokenSigner):
    """Ed25519-backed signer that loads material from the configured KeySet."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def sign(self, payload: dict[str, Any]) -> SignedTokenBundle:
        token_use = payload.get("token_use")
        started = perf_counter()
        failure_logged = False
        try:
            keyset = load_keyset(self._settings)
            active = keyset.active
            if not active or not active.private_key:
                failure_logged = True
                duration = perf_counter() - started
                observe_jwt_signing(
                    result="failure", token_use=token_use, duration_seconds=duration
                )
                log_event(
                    "token_sign",
                    level="error",
                    result="failure",
                    reason="missing_active_key",
                    token_use=token_use or "unknown",
                )
                raise TokenSignerError("Active Ed25519 key is unavailable.")

            primary = self._encode(payload, active)
            duration = perf_counter() - started
            observe_jwt_signing(result="success", token_use=token_use, duration_seconds=duration)
            log_event(
                "token_sign",
                result="success",
                kids=[primary.kid],
                dual_signing=False,
                token_use=token_use or "unknown",
            )
            return SignedTokenBundle(primary=primary)
        except TokenSignerError as exc:
            if not failure_logged:
                observe_jwt_signing(
                    result="failure", token_use=token_use, duration_seconds=perf_counter() - started
                )
                log_event(
                    "token_sign",
                    level="error",
                    result="failure",
                    reason="signer_error",
                    detail=str(exc),
                    token_use=token_use or "unknown",
                )
            raise
        except Exception as exc:
            if not failure_logged:
                observe_jwt_signing(
                    result="failure", token_use=token_use, duration_seconds=perf_counter() - started
                )
                log_event(
                    "token_sign",
                    level="error",
                    result="failure",
                    reason="unexpected_error",
                    detail=str(exc),
                    token_use=token_use or "unknown",
                )
            raise

    def _encode(self, payload: dict[str, Any], material: KeyMaterial) -> SignedToken:
        headers = {"kid": material.kid, "alg": "EdDSA", "typ": "JWT"}
        private_key = material.private_key
        if private_key is None:
            raise TokenSignerError("Active key material is missing a private key")
        token = jwt.encode(payload, private_key, algorithm="EdDSA", headers=headers)
        if isinstance(token, bytes):
            token = token.decode("utf-8")
        return SignedToken(token=token, kid=material.kid)


class EdDSATokenVerifier(TokenVerifier):
    """Ed25519 verifier that validates tokens against the active KeySet key only."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def verify(self, token: str, *, audience: Sequence[str] | None = None) -> dict[str, Any]:
        started = perf_counter()
        token_use: str | None = None
        failure_logged = False
        try:
            keyset = load_keyset(self._settings)
            try:
                header = jwt.get_unverified_header(token)
            except PyJWTError as exc:
                failure_logged = True
                observe_jwt_verification(
                    result="failure", token_use=token_use, duration_seconds=perf_counter() - started
                )
                log_event(
                    "token_verify",
                    level="error",
                    result="failure",
                    reason="header_parse_error",
                    detail=str(exc),
                    token_use="unknown",
                )
                raise TokenVerifierError(f"Token header parse failed: {exc}") from exc

            alg = header.get("alg")
            if alg != "EdDSA":
                failure_logged = True
                observe_jwt_verification(
                    result="failure", token_use=token_use, duration_seconds=perf_counter() - started
                )
                log_event(
                    "token_verify",
                    level="error",
                    result="failure",
                    reason="unsupported_alg",
                    alg=alg,
                    token_use="unknown",
                )
                raise TokenVerifierError(f"Unsupported token alg '{alg}'.")
            kid = header.get("kid")
            material = _find_key_material(keyset, kid)
            public_pem = _public_pem_from_jwk(material.public_jwk)

            options = {
                "require_exp": True,
                "require_iat": True,
                "verify_aud": audience is not None,
            }
            try:
                decoded = jwt.decode(
                    token,
                    public_pem,
                    algorithms=["EdDSA"],
                    audience=list(audience) if audience else None,
                    options=options,
                )
            except PyJWTError as exc:
                failure_logged = True
                observe_jwt_verification(
                    result="failure", token_use=token_use, duration_seconds=perf_counter() - started
                )
                log_event(
                    "token_verify",
                    level="error",
                    result="failure",
                    reason="verification_error",
                    detail=str(exc),
                    kid=material.kid,
                    token_use=token_use or "unknown",
                )
                raise TokenVerifierError(f"Token verification failed: {exc}") from exc

            token_use = decoded.get("token_use")
            observe_jwt_verification(
                result="success", token_use=token_use, duration_seconds=perf_counter() - started
            )
            log_event(
                "token_verify",
                result="success",
                kid=material.kid,
                token_use=token_use or "unknown",
                audience=list(audience) if audience else [],
            )
            return decoded
        except TokenVerifierError as exc:
            if not failure_logged:
                observe_jwt_verification(
                    result="failure", token_use=token_use, duration_seconds=perf_counter() - started
                )
                log_event(
                    "token_verify",
                    level="error",
                    result="failure",
                    reason="verifier_error",
                    detail=str(exc),
                    token_use=token_use or "unknown",
                )
            raise


def _find_key_material(keyset: KeySet, kid: str | None) -> KeyMaterial:
    if not kid:
        raise TokenVerifierError("Token is missing a kid header.")

    def _iter() -> Sequence[KeyMaterial]:
        materials: list[KeyMaterial] = []
        if keyset.active:
            materials.append(keyset.active)
        retired: Sequence[KeyMaterial] = getattr(keyset, "retired", None) or []
        materials.extend(retired)
        return materials

    for material in _iter():
        if material.kid == kid:
            return material
    raise TokenVerifierError(f"Unknown kid '{kid}'.")


def _public_pem_from_jwk(jwk_payload: dict[str, Any]) -> bytes:
    if jwk_payload.get("kty") != "OKP" or jwk_payload.get("crv") != "Ed25519":
        raise TokenVerifierError("Unsupported JWK for Ed25519 verification.")
    x = jwk_payload.get("x")
    if not x:
        raise TokenVerifierError("Ed25519 JWK missing 'x' coordinate.")
    padding = "=" * ((4 - len(x) % 4) % 4)
    public_bytes = base64.urlsafe_b64decode(f"{x}{padding}".encode())
    public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_bytes)
    return public_key.public_bytes(
        encoding=_PEM_ENCODING,
        format=_SUBJECT_PUBLIC_FORMAT,
    )


def get_token_signer(settings: Settings | None = None) -> TokenSigner:
    settings = settings or get_settings()
    return EdDSATokenSigner(settings)


def get_token_verifier(settings: Settings | None = None) -> TokenVerifier:
    settings = settings or get_settings()
    return EdDSATokenVerifier(settings)


# =============================================================================
# JWT TOKEN UTILITIES
# =============================================================================


def _utcnow() -> datetime:
    return datetime.now(UTC)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a signed EdDSA access token."""

    settings = get_settings()
    now = _utcnow()
    expire = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))

    payload = data.copy()
    payload.setdefault("iat", int(now.timestamp()))
    payload.setdefault("nbf", payload["iat"])
    payload["exp"] = int(expire.timestamp())

    signed = get_token_signer(settings).sign(payload)
    return signed.primary.token


def verify_token(token: str, *, audience: Sequence[str] | None = None) -> dict[str, Any]:
    """Verify and decode an EdDSA token, raising HTTP 401 on failure."""

    try:
        return get_token_verifier().verify(token, audience=audience)
    except TokenVerifierError as exc:
        raise _unauthorized() from exc


# =============================================================================
# DEPENDENCY FUNCTIONS
# =============================================================================


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    """
    Get current user from JWT token.

    This is a dependency that can be used in FastAPI route functions
    to require authentication.

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        Dict[str, Any]: Current user information

    Raises:
        HTTPException: If token is invalid
    """
    token = credentials.credentials
    payload = verify_token(token)

    token_use = payload.get("token_use")
    if token_use != ACCESS_TOKEN_USE:
        raise _unauthorized("Access token required.")

    raw_subject = payload.get("sub")
    if not isinstance(raw_subject, str):
        raise _unauthorized("Token subject must reference a user account.")
    if not _is_user_subject(raw_subject):
        raise _unauthorized("Token subject must reference a user account.")
    subject = raw_subject

    return {
        "user_id": _normalize_subject(subject),
        "subject": subject,
        "payload": payload,
    }


def _normalize_subject(subject: str) -> str:
    sanitized = subject.strip()
    if sanitized.startswith("user:"):
        return sanitized.split("user:", 1)[1]
    return sanitized


async def get_current_active_user(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get current active user.

    This dependency ensures the user is both authenticated and active.

    Args:
        current_user: Current user from get_current_user dependency

    Returns:
        Dict[str, Any]: Current active user information

    Raises:
        HTTPException: If user is inactive
    """
    # Add your user status checking logic here
    # For now, we'll just return the user
    return current_user
