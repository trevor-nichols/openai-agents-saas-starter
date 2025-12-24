from __future__ import annotations

from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import ContentSwitcher, Footer, Header, ListView, Static

from starter_cli.core import CLIContext
from starter_cli.workflows.home.hub import HubService

from .palette import CommandPaletteScreen, CommandSpec
from .panes import build_panes
from .secrets_onboard import SecretsOnboardScreen
from .sections import SECTIONS, NavItem, SectionSpec
from .wizard_pane import WizardLaunchConfig


class StarterTUI(App[None]):
    """Textual hub for the Starter CLI."""

    CSS: ClassVar[str] = """
    Screen {
        layout: vertical;
    }

    #shell {
        height: 1fr;
    }

    #nav {
        width: 32;
        min-width: 28;
        background: $boost;
        border-right: tall $panel-darken-1;
    }

    #nav-title {
        padding: 1 2 0 2;
        text-style: bold;
    }

    #nav-subtitle {
        padding: 0 2 1 2;
        color: $text-muted;
    }

    #nav-hint {
        padding: 1 2;
        color: $text-muted;
    }

    #nav-list {
        padding: 0 1;
    }

    .nav-item {
        padding: 0 1 1 1;
    }

    .nav-row {
        height: auto;
    }

    .nav-key {
        width: 3;
        text-style: bold;
        color: $accent;
    }

    .nav-label {
        text-style: bold;
    }

    .nav-desc {
        color: $text-muted;
    }

    #content {
        padding: 1 2;
    }

    .section-pane {
        padding: 1 2;
    }

    .section-title {
        text-style: bold;
    }

    .section-description {
        color: $text-muted;
        padding-bottom: 1;
    }

    .section-detail {
        padding-bottom: 1;
    }

    .section-footnote {
        color: $text-muted;
    }

    .section-pane DataTable {
        width: 1fr;
    }

    .ops-actions {
        height: auto;
        padding-bottom: 1;
    }

    .ops-output {
        color: $text-muted;
        height: auto;
    }

    .section-summary {
        color: $text-muted;
        padding-bottom: 1;
    }

    .home-actions {
        height: auto;
        padding-bottom: 1;
    }

    .setup-actions {
        height: auto;
        padding-bottom: 1;
    }

    #wizard-controls {
        height: auto;
        padding-bottom: 1;
    }

    .wizard-control-label {
        padding-right: 1;
        color: $text-muted;
    }

    .stripe-options {
        height: auto;
        padding-bottom: 1;
    }

    .stripe-options-actions {
        height: auto;
        align: left middle;
        gap: 1;
        padding-bottom: 1;
    }

    .stripe-reset {
        height: auto;
        padding: 0 1;
    }

    #stripe-output {
        height: auto;
        color: $text-muted;
        padding-top: 1;
    }

    #stripe-prompt {
        margin-top: 1;
        padding-top: 1;
        border-top: solid $panel-darken-1;
    }

    #stripe-prompt-actions {
        height: auto;
        padding-top: 1;
    }

    #wizard-main DataTable {
        width: 1fr;
    }

    #wizard-conditional {
        height: auto;
        margin-top: 1;
    }

    #wizard-prompt {
        margin-top: 1;
        padding: 1 0 0 0;
        border-top: solid $panel-darken-1;
    }

    #wizard-prompt-actions {
        height: auto;
        padding-top: 1;
    }
    """

    BINDINGS: ClassVar = [
        Binding("h", "go('home')", "Home", show=True),
        Binding("s", "go('setup')", "Setup", show=True),
        Binding("w", "go('wizard')", "Wizard", show=True),
        Binding("l", "go('logs')", "Logs", show=True),
        Binding("i", "go('infra')", "Infra", show=True),
        Binding("p", "go('providers')", "Providers", show=True),
        Binding("b", "go('stripe')", "Stripe", show=True),
        Binding("u", "go('usage')", "Usage", show=True),
        Binding("ctrl+p", "open_palette", "Palette", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(
        self,
        ctx: CLIContext,
        *,
        initial_screen: str = "home",
        wizard_config: WizardLaunchConfig | None = None,
    ) -> None:
        self.ctx = ctx
        self._hub = HubService(ctx)
        self._sections = SECTIONS
        self._section_index = {section.key: idx for idx, section in enumerate(SECTIONS)}
        self._initial_key = self._resolve_initial(initial_screen)
        self._nav_items = [NavItem(section) for section in SECTIONS]
        self._panes = build_panes(
            ctx,
            SECTIONS,
            hub=self._hub,
            wizard_config=wizard_config,
        )
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="shell"):
            with Vertical(id="nav"):
                yield Static("Starter CLI", id="nav-title")
                yield Static("Operations Hub", id="nav-subtitle")
                yield ListView(
                    *self._nav_items,
                    id="nav-list",
                    initial_index=self._section_index.get(self._initial_key, 0),
                )
                yield Static("Ctrl+P for commands", id="nav-hint")
            with Vertical(id="content"):
                yield ContentSwitcher(
                    *self._panes,
                    id="content-switcher",
                    initial=self._initial_key,
                )
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Starter CLI"
        self._activate_section(self._initial_key, update_nav=False)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if not isinstance(item, NavItem):
            return
        self._activate_section(item.section.key, update_nav=False)

    def action_go(self, section_key: str) -> None:
        self._activate_section(section_key, update_nav=True)

    def action_open_palette(self) -> None:
        self.push_screen(CommandPaletteScreen(self._palette_commands()))

    async def action_quit(self) -> None:
        self.exit()

    def open_secrets_onboard(self) -> None:
        self.push_screen(SecretsOnboardScreen(self.ctx))

    def _palette_commands(self) -> list[CommandSpec]:
        commands: list[CommandSpec] = []
        for section in self._sections:
            commands.append(self._nav_command(section))
        commands.append(
            CommandSpec(
                key="quit",
                label="Quit",
                description="Exit the Starter CLI hub",
                action=self.exit,
            )
        )
        return commands

    def _nav_command(self, section: SectionSpec) -> CommandSpec:
        def _navigate() -> None:
            self._activate_section(section.key, update_nav=True)

        return CommandSpec(
            key=section.key,
            label=f"Go to {section.label}",
            description=section.description,
            action=_navigate,
        )

    def _activate_section(self, section_key: str, *, update_nav: bool) -> None:
        key = section_key.lower()
        if key not in self._section_index:
            return
        if update_nav:
            nav = self.query_one("#nav-list", ListView)
            index = self._section_index[key]
            if nav.index != index:
                nav.index = index
        switcher = self.query_one("#content-switcher", ContentSwitcher)
        switcher.current = key
        section = self._sections[self._section_index[key]]
        self.sub_title = section.label

    def _resolve_initial(self, requested: str) -> str:
        key = requested.lower()
        if key in self._section_index:
            return key
        return self._sections[0].key


__all__ = ["StarterTUI"]
