"""Factory helpers for SSO services."""

from __future__ import annotations

from collections.abc import Callable

from app.core.settings import Settings, get_settings
from app.domain.sso import SsoProviderConfigRepository, UserIdentityRepository
from app.domain.team import (
    TeamInviteAcceptanceRepository,
    TeamInviteRepository,
    TenantMembershipRepository,
)
from app.domain.tenant_accounts import TenantAccountRepository
from app.domain.users import UserRepository
from app.infrastructure.persistence.auth.membership_repository import (
    get_tenant_membership_repository,
)
from app.infrastructure.persistence.auth.sso_repository import (
    get_sso_provider_config_repository,
    get_user_identity_repository,
)
from app.infrastructure.persistence.auth.team_invite_acceptance_repository import (
    get_team_invite_acceptance_repository,
)
from app.infrastructure.persistence.auth.team_invite_repository import (
    get_team_invite_repository,
)
from app.infrastructure.persistence.auth.user_repository import get_user_repository
from app.infrastructure.persistence.tenants.account_repository import (
    get_tenant_account_repository,
)
from app.services.auth_service import AuthService, get_auth_service
from app.services.team.acceptance_service import TeamInviteAcceptanceService
from app.services.users.provisioning import UserProvisioningService

from .oidc_client import OidcClient
from .provisioning import SsoProvisioner
from .service import SsoService
from .state_store import SsoStateStore, build_sso_state_store


def build_sso_service(
    *,
    settings: Settings | None = None,
    state_store: SsoStateStore | None = None,
    provider_repository: SsoProviderConfigRepository | None = None,
    identity_repository: UserIdentityRepository | None = None,
    user_repository: UserRepository | None = None,
    membership_repository: TenantMembershipRepository | None = None,
    invite_repository: TeamInviteRepository | None = None,
    invite_acceptance_repository: TeamInviteAcceptanceRepository | None = None,
    tenant_repository: TenantAccountRepository | None = None,
    auth_service: AuthService | None = None,
    oidc_client_factory: Callable[[], OidcClient] | None = None,
    invite_acceptance_service: TeamInviteAcceptanceService | None = None,
    user_provisioning_service: UserProvisioningService | None = None,
) -> SsoService:
    resolved_settings = settings or get_settings()

    resolved_state_store = state_store or build_sso_state_store(resolved_settings)
    resolved_provider_repo = (
        provider_repository or get_sso_provider_config_repository(resolved_settings)
    )
    resolved_identity_repo = (
        identity_repository or get_user_identity_repository(resolved_settings)
    )
    resolved_user_repo = user_repository or get_user_repository(resolved_settings)
    resolved_membership_repo = (
        membership_repository or get_tenant_membership_repository(resolved_settings)
    )
    resolved_invite_repo = invite_repository or get_team_invite_repository(resolved_settings)
    resolved_invite_acceptance_repo = (
        invite_acceptance_repository
        or get_team_invite_acceptance_repository(resolved_settings)
    )
    resolved_tenant_repo = tenant_repository or get_tenant_account_repository(resolved_settings)
    resolved_auth_service = auth_service or get_auth_service()

    if resolved_provider_repo is None:
        raise RuntimeError("SSO provider config repository is not configured.")
    if resolved_identity_repo is None:
        raise RuntimeError("User identity repository is not configured.")
    if resolved_user_repo is None:
        raise RuntimeError("User repository is not configured.")
    if resolved_membership_repo is None:
        raise RuntimeError("Tenant membership repository is not configured.")
    if resolved_invite_repo is None:
        raise RuntimeError("Team invite repository is not configured.")
    if resolved_invite_acceptance_repo is None:
        raise RuntimeError("Team invite acceptance repository is not configured.")
    if resolved_tenant_repo is None:
        raise RuntimeError("Tenant account repository is not configured.")

    resolved_invite_acceptance_service = (
        invite_acceptance_service
        or TeamInviteAcceptanceService(
            invite_repository=resolved_invite_repo,
            acceptance_repository=resolved_invite_acceptance_repo,
            user_repository=resolved_user_repo,
        )
    )
    resolved_user_provisioning_service = (
        user_provisioning_service
        or UserProvisioningService(
            user_repository=resolved_user_repo,
            membership_repository=resolved_membership_repo,
        )
    )

    provisioner = SsoProvisioner(
        membership_repository=resolved_membership_repo,
        invite_acceptance_service=resolved_invite_acceptance_service,
        user_provisioning_service=resolved_user_provisioning_service,
    )

    return SsoService(
        settings_factory=lambda: resolved_settings,
        state_store=resolved_state_store,
        provider_repository=resolved_provider_repo,
        identity_repository=resolved_identity_repo,
        user_repository=resolved_user_repo,
        tenant_repository=resolved_tenant_repo,
        auth_service=resolved_auth_service,
        oidc_client_factory=oidc_client_factory,
        provisioner=provisioner,
    )


def get_sso_service() -> SsoService:
    from app.bootstrap.container import get_container

    container = get_container()
    if container.sso_service is None:
        container.sso_service = build_sso_service()
    assert container.sso_service is not None
    return container.sso_service


__all__ = ["build_sso_service", "get_sso_service"]
