"""JWT + password utilities plus EdDSA signer/verifier abstractions."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol, Sequence

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from jwt import PyJWTError
from passlib.context import CryptContext
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from app.core.config import Settings, get_settings
from app.core.keys import KeyMaterial, KeySet, load_keyset

UTC = timezone.utc

# =============================================================================
# SECURITY CONFIGURATION
# =============================================================================

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()

# =============================================================================
# PASSWORD UTILITIES
# =============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password to verify against
        
    Returns:
        bool: True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)

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


class TokenSigner(Protocol):
    """Interface for producing signed JWTs."""

    def sign(self, payload: dict[str, Any], *, dual_sign: bool | None = None) -> SignedTokenBundle:
        ...


class TokenVerifier(Protocol):
    """Interface for validating signed JWTs."""

    def verify(self, token: str, *, audience: Sequence[str] | None = None) -> dict[str, Any]:
        ...


class EdDSATokenSigner(TokenSigner):
    """Ed25519-backed signer that loads material from the configured KeySet."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def sign(self, payload: dict[str, Any], *, dual_sign: bool | None = None) -> SignedTokenBundle:
        keyset = load_keyset(self._settings)
        active = keyset.active
        if not active or not active.private_key:
            raise TokenSignerError("Active Ed25519 key is unavailable.")

        primary = self._encode(payload, active)

        should_dual = dual_sign if dual_sign is not None else self._settings.auth_dual_signing_enabled
        secondary = None
        if should_dual:
            next_key = keyset.next
            if not next_key or not next_key.private_key:
                raise TokenSignerError("Dual signing requested but next key is unavailable.")
            keyset.ensure_overlap_within(self._settings.auth_dual_signing_overlap_minutes)
            secondary = self._encode(payload, next_key)
        return SignedTokenBundle(primary=primary, secondary=secondary)

    def _encode(self, payload: dict[str, Any], material: KeyMaterial) -> SignedToken:
        headers = {"kid": material.kid, "alg": "EdDSA", "typ": "JWT"}
        token = jwt.encode(payload, material.private_key, algorithm="EdDSA", headers=headers)
        return SignedToken(token=token, kid=material.kid)


class EdDSATokenVerifier(TokenVerifier):
    """Ed25519 verifier that accepts active/next/retired keys from the KeySet."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def verify(self, token: str, *, audience: Sequence[str] | None = None) -> dict[str, Any]:
        keyset = load_keyset(self._settings)
        try:
            header = jwt.get_unverified_header(token)
        except PyJWTError as exc:  # noqa: BLE001
            raise TokenVerifierError(f"Token header parse failed: {exc}") from exc

        alg = header.get("alg")
        if alg != "EdDSA":
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
            return jwt.decode(
                token,
                public_pem,
                algorithms=["EdDSA"],
                audience=list(audience) if audience else None,
                options=options,
            )
        except PyJWTError as exc:
            raise TokenVerifierError(f"Token verification failed: {exc}") from exc


def _find_key_material(keyset: KeySet, kid: str | None) -> KeyMaterial:
    if not kid:
        raise TokenVerifierError("Token is missing a kid header.")

    def _iter() -> Sequence[KeyMaterial]:
        materials: list[KeyMaterial] = []
        if keyset.active:
            materials.append(keyset.active)
        if keyset.next:
            materials.append(keyset.next)
        materials.extend(keyset.retired or [])
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
    public_bytes = base64.urlsafe_b64decode(f"{x}{padding}".encode("utf-8"))
    public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_bytes)
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

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

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {"user_id": user_id, "payload": payload}

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
