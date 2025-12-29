"""Domain errors for tenant team management."""

from __future__ import annotations


class TeamServiceError(RuntimeError):
    """Base error for team management operations."""


class InvalidTeamRoleError(TeamServiceError):
    """Raised when a requested role is not supported."""


class OwnerRoleAssignmentError(TeamServiceError):
    """Raised when a non-owner attempts to grant or revoke owner role."""


class TeamMemberNotFoundError(TeamServiceError):
    """Raised when a tenant membership cannot be located."""


class TeamMemberAlreadyExistsError(TeamServiceError):
    """Raised when attempting to add an existing tenant member."""


class TeamInviteNotFoundError(TeamServiceError):
    """Raised when a team invite cannot be resolved."""


class TeamInviteExpiredError(TeamServiceError):
    """Raised when an invite has expired."""


class TeamInviteRevokedError(TeamServiceError):
    """Raised when an invite is revoked or already used."""


class TeamInviteEmailMismatchError(TeamServiceError):
    """Raised when an invite is bound to a different email."""


class TeamInviteUserExistsError(TeamServiceError):
    """Raised when the invite email already belongs to a user."""


class TeamInviteDeliveryError(TeamServiceError):
    """Raised when an invite email cannot be delivered."""


class TeamInviteValidationError(TeamServiceError):
    """Raised when invite acceptance payloads are invalid."""


__all__ = [
    "InvalidTeamRoleError",
    "OwnerRoleAssignmentError",
    "TeamInviteDeliveryError",
    "TeamInviteEmailMismatchError",
    "TeamInviteExpiredError",
    "TeamInviteNotFoundError",
    "TeamInviteRevokedError",
    "TeamInviteUserExistsError",
    "TeamInviteValidationError",
    "TeamMemberAlreadyExistsError",
    "TeamMemberNotFoundError",
    "TeamServiceError",
]
