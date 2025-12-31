"""Policy constants for tenant team management."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TeamInvitePolicy:
    default_expires_hours: int
    max_expires_hours: int


TEAM_INVITE_POLICY = TeamInvitePolicy(
    default_expires_hours=72,
    max_expires_hours=24 * 14,
)


__all__ = ["TEAM_INVITE_POLICY", "TeamInvitePolicy"]
