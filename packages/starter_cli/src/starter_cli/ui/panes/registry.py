from __future__ import annotations

from collections.abc import Callable, Iterable

from textual.containers import Vertical

from starter_cli.core import CLIContext
from starter_cli.workflows.home.hub import HubService
from starter_cli.workflows.setup_menu.detection import STALE_AFTER_DAYS

from ..sections import NavGroupSpec, SectionSpec, iter_sections
from ..wizard_pane import WizardLaunchConfig, WizardPane
from .api_export import ApiExportPane
from .auth_tokens import AuthTokensPane
from .config_inventory import ConfigInventoryPane
from .doctor import DoctorPane
from .home import HomePane
from .infra import InfraPane
from .jwks import JwksPane
from .key_rotation import KeyRotationPane
from .logs import LogsPane
from .placeholder import PlaceholderPane
from .providers import ProvidersPane
from .release_db import ReleaseDbPane
from .secrets import SecretsOnboardPane
from .setup import SetupPane
from .start_stop import StartStopPane
from .status_ops import StatusOpsPane
from .stripe import StripePane
from .usage import UsagePane
from .util_run_with_env import UtilRunWithEnvPane

PaneFactory = Callable[[CLIContext, HubService, WizardLaunchConfig | None, SectionSpec], Vertical]


def _wizard_factory(
    ctx: CLIContext,
    hub: HubService,
    config: WizardLaunchConfig | None,
    section: SectionSpec,
) -> Vertical:
    del hub, section
    return WizardPane(ctx, config=config)


def _placeholder_factory(
    ctx: CLIContext,
    hub: HubService,
    config: WizardLaunchConfig | None,
    section: SectionSpec,
) -> Vertical:
    del ctx, hub, config
    return PlaceholderPane(section)


PANE_FACTORIES: dict[str, PaneFactory] = {
    "home": lambda ctx, hub, config, section: HomePane(ctx, hub),
    "setup": lambda ctx, hub, config, section: SetupPane(
        ctx,
        hub,
        stale_days=STALE_AFTER_DAYS,
    ),
    "wizard": _wizard_factory,
    "doctor": lambda ctx, hub, config, section: DoctorPane(ctx),
    "start-stop": lambda ctx, hub, config, section: StartStopPane(ctx),
    "logs": lambda ctx, hub, config, section: LogsPane(ctx, hub),
    "infra": lambda ctx, hub, config, section: InfraPane(ctx, hub),
    "providers": lambda ctx, hub, config, section: ProvidersPane(ctx, hub),
    "stripe": lambda ctx, hub, config, section: StripePane(ctx, hub),
    "usage": lambda ctx, hub, config, section: UsagePane(ctx, hub),
    "release-db": lambda ctx, hub, config, section: ReleaseDbPane(ctx),
    "config-inventory": lambda ctx, hub, config, section: ConfigInventoryPane(ctx),
    "api-export": lambda ctx, hub, config, section: ApiExportPane(ctx),
    "auth-tokens": lambda ctx, hub, config, section: AuthTokensPane(ctx),
    "key-rotation": lambda ctx, hub, config, section: KeyRotationPane(ctx),
    "jwks": lambda ctx, hub, config, section: JwksPane(ctx),
    "secrets": lambda ctx, hub, config, section: SecretsOnboardPane(ctx),
    "status-ops": lambda ctx, hub, config, section: StatusOpsPane(ctx),
    "util-run-with-env": lambda ctx, hub, config, section: UtilRunWithEnvPane(ctx),
}


def build_panes(
    ctx: CLIContext,
    groups: Iterable[NavGroupSpec],
    *,
    hub: HubService,
    wizard_config: WizardLaunchConfig | None = None,
) -> list[Vertical]:
    resolved_groups = tuple(groups)
    _validate_pane_registry(resolved_groups)
    panes: list[Vertical] = []
    for section in iter_sections(resolved_groups):
        factory = PANE_FACTORIES[section.key]
        panes.append(factory(ctx, hub, wizard_config, section))
    return panes


def _validate_pane_registry(groups: Iterable[NavGroupSpec]) -> None:
    missing = [
        section.key
        for section in iter_sections(tuple(groups))
        if section.key not in PANE_FACTORIES
    ]
    if missing:
        joined = ", ".join(sorted(missing))
        raise RuntimeError(
            "Missing pane factory for section(s): "
            f"{joined}. Add the pane or remove the section from NAV_GROUPS."
        )


__all__ = ["build_panes"]
