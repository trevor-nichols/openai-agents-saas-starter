"""Multi-factor authentication management (TOTP + WebAuthn placeholder)."""

from __future__ import annotations

import base64
import hmac
import os
import struct
import time
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Select, and_, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.settings import get_settings
from app.infrastructure.persistence.auth.models import (
    MfaMethodType,
    UserMfaMethod,
    UserRecoveryCode,
)
from app.infrastructure.security.cipher import build_cipher, encrypt_optional
from app.services.security_events import SecurityEventService, get_security_event_service


class MfaEnrollmentError(Exception):
    """Raised when MFA enrollment cannot proceed."""


class MfaVerificationError(Exception):
    """Raised when MFA verification fails."""


class RecoveryCodeError(Exception):
    """Raised when recovery code usage fails."""


class MfaService:
    """Handles MFA enrollment, verification, recovery codes, and revocation."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        security_events: SecurityEventService | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._security_events = security_events or get_security_event_service()
        settings = get_settings()
        secret = settings.auth_session_encryption_key or settings.secret_key
        self._cipher = build_cipher(secret)
        self._hash_pepper = settings.secret_key

    async def list_methods(self, user_id: UUID) -> list[UserMfaMethod]:
        query: Select[tuple[UserMfaMethod]] = (
            select(UserMfaMethod)
            .where(UserMfaMethod.user_id == user_id)
            .order_by(UserMfaMethod.created_at.asc())
        )
        async with self._session_factory() as session:
            result = await session.execute(query)
            return list(result.scalars().all())

    async def start_totp_enrollment(self, *, user_id: UUID, label: str | None) -> tuple[str, UUID]:
        secret = self._generate_totp_secret()
        encrypted = encrypt_optional(self._cipher, secret)
        method = UserMfaMethod(
            id=uuid4(),
            user_id=user_id,
            method_type=MfaMethodType.TOTP,
            label=label,
            secret_encrypted=encrypted,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        async with self._session_factory() as session:
            session.add(method)
            await session.commit()
        await self._security_events.record(
            event_type="mfa_totp_enroll_started",
            user_id=user_id,
        )
        return secret, method.id

    async def verify_totp(
        self,
        *,
        user_id: UUID,
        method_id: UUID,
        code: str,
        ip_hash: str | None = None,
        user_agent_hash: str | None = None,
    ) -> None:
        async with self._session_factory() as session:
            method = await session.get(UserMfaMethod, method_id)
            if not method or method.user_id != user_id:
                raise MfaVerificationError("MFA method not found.")
            if method.method_type != MfaMethodType.TOTP:
                raise MfaVerificationError("Unsupported MFA method.")
            if method.revoked_at:
                raise MfaVerificationError("MFA method has been revoked.")
            secret = self._decrypt_secret(method)
            if not secret:
                raise MfaVerificationError("MFA secret unavailable.")
            if not self._verify_totp_code(secret, code):
                raise MfaVerificationError("Invalid MFA code.")
            method.verified_at = datetime.now(UTC)
            method.last_used_at = datetime.now(UTC)
            session.add(method)
            await session.commit()
        await self._security_events.record(
            event_type="mfa_totp_verified",
            user_id=user_id,
            ip_hash=ip_hash,
            user_agent_hash=user_agent_hash,
        )

    async def revoke_method(self, *, user_id: UUID, method_id: UUID, reason: str | None) -> None:
        async with self._session_factory() as session:
            stmt = (
                update(UserMfaMethod)
                .where(UserMfaMethod.id == method_id, UserMfaMethod.user_id == user_id)
                .values(revoked_at=datetime.now(UTC), revoked_reason=reason)
            )
            result = await session.execute(stmt)
            await session.commit()
        rows = getattr(result, "rowcount", 0)
        if rows:
            await self._security_events.record(
                event_type="mfa_revoked", user_id=user_id, metadata={"method_id": str(method_id)}
            )

    async def regenerate_recovery_codes(self, *, user_id: UUID, count: int = 10) -> list[str]:
        codes = [self._generate_code() for _ in range(count)]
        hashed_codes = [self._hash_code(code) for code in codes]
        async with self._session_factory() as session:
            await session.execute(
                delete(UserRecoveryCode).where(UserRecoveryCode.user_id == user_id)
            )
            rows = [
                UserRecoveryCode(
                    id=uuid4(),
                    user_id=user_id,
                    code_hash=code_hash,
                    created_at=datetime.now(UTC),
                )
                for code_hash in hashed_codes
            ]
            session.add_all(rows)
            await session.commit()
        await self._security_events.record(event_type="mfa_recovery_reset", user_id=user_id)
        return codes

    async def consume_recovery_code(self, *, user_id: UUID, code: str) -> None:
        hashed = self._hash_code(code)
        async with self._session_factory() as session:
            query = select(UserRecoveryCode).where(
                and_(
                    UserRecoveryCode.user_id == user_id,
                    UserRecoveryCode.code_hash == hashed,
                    UserRecoveryCode.used_at.is_(None),
                )
            )
            result = await session.execute(query)
            row = result.scalar_one_or_none()
            if not row:
                raise RecoveryCodeError("Recovery code is invalid or already used.")
            row.used_at = datetime.now(UTC)
            session.add(row)
            await session.commit()
        await self._security_events.record(event_type="mfa_recovery_used", user_id=user_id)

    # ---------- helpers ----------

    def _decrypt_secret(self, method: UserMfaMethod) -> str | None:
        from app.infrastructure.security.cipher import decrypt_optional

        return decrypt_optional(self._cipher, method.secret_encrypted)

    @staticmethod
    def _generate_totp_secret(length: int = 20) -> str:
        return base64.b32encode(os.urandom(length)).decode("utf-8").rstrip("=")

    @staticmethod
    def _totp(secret: str, *, step: int = 30, digits: int = 6, offset: int = 0) -> int:
        key = base64.b32decode(secret + "=" * (-len(secret) % 8))
        counter = int(time.time() // step) + offset
        msg = struct.pack(">Q", counter)
        digest = hmac.new(key, msg, "sha1").digest()
        pos = digest[-1] & 0x0F
        code = struct.unpack(">I", digest[pos : pos + 4])[0] & 0x7FFFFFFF
        return code % (10**digits)

    def _verify_totp_code(self, secret: str, code: str, *, window: int = 1) -> bool:
        try:
            code_int = int(code)
        except ValueError:
            return False
        for offset in range(-window, window + 1):
            if self._totp(secret, offset=offset) == code_int:
                return True
        return False

    def _hash_code(self, code: str) -> str:
        import hashlib

        payload = f"{self._hash_pepper}:{code}".encode()
        return hashlib.sha256(payload).hexdigest()

    @staticmethod
    def _generate_code() -> str:
        return base64.b32encode(os.urandom(10)).decode("utf-8")[:10].lower()


def get_mfa_service() -> MfaService:
    from app.bootstrap.container import get_container
    from app.infrastructure.db import get_async_sessionmaker

    container = get_container()
    session_factory = container.session_factory or get_async_sessionmaker()
    container.session_factory = session_factory
    if container.security_event_service is None:
        container.security_event_service = get_security_event_service()
    if container.mfa_service is None:
        container.mfa_service = MfaService(
            session_factory,
            security_events=container.security_event_service,
        )
    return container.mfa_service


__all__ = ["MfaService", "get_mfa_service", "MfaEnrollmentError", "MfaVerificationError"]
