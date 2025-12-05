"""Password policy and history helpers."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from app.core.password_policy import PasswordPolicyError, validate_password_strength
from app.core.security import verify_password
from app.core.settings import Settings
from app.domain.users import PasswordReuseError, UserRepository

from .errors import PasswordPolicyViolationError


class PasswordPolicyManager:
    def __init__(self, repository: UserRepository, settings: Settings) -> None:
        self._repository = repository
        self._settings = settings

    async def enforce_history(self, user_id: UUID, candidate: str) -> None:
        limit = self._history_limit()
        if limit <= 0:
            return
        history = await self._repository.list_password_history(user_id, limit=limit)
        for entry in history:
            if verify_password(candidate, entry.password_hash).is_valid:
                raise PasswordReuseError("Password was recently used.")

    async def trim_history(self, user_id: UUID) -> None:
        limit = self._history_limit()
        await self._repository.trim_password_history(user_id, max(limit, 0))

    def validate_strength(self, password: str, *, hints: Sequence[str] | None = None) -> None:
        try:
            validate_password_strength(password, user_inputs=hints or [])
        except PasswordPolicyError as exc:
            raise PasswordPolicyViolationError(str(exc)) from exc

    def _history_limit(self) -> int:
        value = getattr(self._settings, "auth_password_history_count", 0)
        try:
            return max(int(value), 0)
        except (TypeError, ValueError):  # pragma: no cover - defensive
            return 0


__all__ = ["PasswordPolicyManager"]
