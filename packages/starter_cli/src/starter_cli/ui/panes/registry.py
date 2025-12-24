from __future__ import annotations

from collections.abc import Callable, Iterable

from textual.containers import Vertical

from starter_cli.core import CLIContext
from starter_cli.workflows.home.hub import HubService
from starter_cli.workflows.setup_menu.detection import STALE_AFTER_DAYS

from ..sections import SectionSpec
from ..wizard_pane import WizardLaunchConfig, WizardPane
from .home import HomePane
from .infra import InfraPane
from .logs import LogsPane
from .placeholder import PlaceholderPane
from .providers import ProvidersPane
from .setup import SetupPane
from .stripe import StripePane
from .usage import UsagePane

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
    "logs": lambda ctx, hub, config, section: LogsPane(ctx, hub),
    "infra": lambda ctx, hub, config, section: InfraPane(ctx, hub),
    "providers": lambda ctx, hub, config, section: ProvidersPane(ctx, hub),
    "stripe": lambda ctx, hub, config, section: StripePane(ctx, hub),
    "usage": lambda ctx, hub, config, section: UsagePane(ctx, hub),
}


def build_panes(
    ctx: CLIContext,
    sections: Iterable[SectionSpec],
    *,
    hub: HubService,
    wizard_config: WizardLaunchConfig | None = None,
) -> list[Vertical]:
    panes: list[Vertical] = []
    for section in sections:
        factory = PANE_FACTORIES.get(section.key, _placeholder_factory)
        panes.append(factory(ctx, hub, wizard_config, section))
    return panes


__all__ = ["build_panes"]
