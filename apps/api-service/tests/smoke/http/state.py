from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SmokeState:
    tenant_id: str
    conversation_id: str | None
    access_token: str
    refresh_token: str
    user_id: str | None
    session_id: str | None


__all__ = ["SmokeState"]
