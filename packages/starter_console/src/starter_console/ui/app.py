from __future__ import annotations

import asyncio
from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import ContentSwitcher, Footer, Header, Static, Tree

from starter_console.core import CLIContext
from starter_console.workflows.home.hub import HubService

from .context_panel import ContextPanel, EnvReloaded
from .nav_tree import NavTree
from .palette import CommandPaletteScreen, CommandSpec
from .panes import build_panes
from .panes.wizard import WizardLaunchConfig
from .secrets_onboard import SecretsOnboardScreen
from .sections import NAV_GROUPS, NavGroupSpec, SectionSpec, iter_sections


class StarterTUI(App[None]):
    """Textual hub for the Starter Console."""

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

    #nav-tree {
        padding: 0 1;
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

    .context-panel {
        border: tall $panel-darken-1;
        padding: 1;
        margin-bottom: 1;
    }

    .context-title {
        text-style: bold;
    }

    .context-summary {
        color: $text-muted;
        padding-bottom: 1;
    }

    .context-actions {
        height: auto;
        padding-bottom: 1;
    }

    .context-label {
        padding-right: 1;
        color: $text-muted;
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

    .wizard-options {
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

    #secrets-prompt {
        margin-top: 1;
        padding-top: 1;
        border-top: solid $panel-darken-1;
    }

    #secrets-prompt-actions {
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
        self._groups = NAV_GROUPS
        self._sections = iter_sections(self._groups)
        self._section_index = {
            section.key: idx for idx, section in enumerate(self._sections)
        }
        self._initial_key = self._resolve_initial(initial_screen)
        self._background_tasks: set[asyncio.Task[object]] = set()
        self._panes = build_panes(
            ctx,
            self._groups,
            hub=self._hub,
            wizard_config=wizard_config,
        )
        super().__init__()
        self._bind_section_shortcuts()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="shell"):
            with Vertical(id="nav"):
                yield Static("Starter Console", id="nav-title")
                yield Static("Operations Hub", id="nav-subtitle")
                yield NavTree(self._groups, id="nav-tree")
                yield Static("Ctrl+P for commands", id="nav-hint")
            with Vertical(id="content"):
                yield ContextPanel(self.ctx)
                yield ContentSwitcher(
                    *self._panes,
                    id="content-switcher",
                    initial=self._initial_key,
                )
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Starter Console"
        self._activate_section(self._initial_key, update_nav=True)

    def on_tree_node_selected(self, event: Tree.NodeSelected[SectionSpec]) -> None:
        section = event.node.data
        if not isinstance(section, SectionSpec):
            return
        self._activate_section(section.key, update_nav=False)

    def on_env_reloaded(self, message: EnvReloaded) -> None:
        del message
        self._refresh_active_pane()

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
        for group in self._groups:
            commands.append(self._group_command(group))
        for section in self._sections:
            commands.append(self._nav_command(section))
        commands.append(
            CommandSpec(
                key="quit",
                label="Quit",
                description="Exit the Starter Console hub",
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

    def _group_command(self, group: NavGroupSpec) -> CommandSpec:
        def _navigate() -> None:
            nav = self.query_one("#nav-tree", NavTree)
            nav.expand_group(group.key)
            if group.items:
                self._activate_section(group.items[0].key, update_nav=True)
            else:
                nav.select_group(group.key)

        return CommandSpec(
            key=f"group:{group.key}",
            label=f"{group.label} (group)",
            description=group.description,
            action=_navigate,
        )

    def _activate_section(self, section_key: str, *, update_nav: bool) -> None:
        key = section_key.lower()
        if key not in self._section_index:
            return
        if update_nav:
            nav = self.query_one("#nav-tree", NavTree)
            nav.select_section(key)
        switcher = self.query_one("#content-switcher", ContentSwitcher)
        switcher.current = key
        section = self._sections[self._section_index[key]]
        self.sub_title = section.label

    def _bind_section_shortcuts(self) -> None:
        reserved = {_binding_key(binding) for binding in self.BINDINGS}
        seen: dict[str, str] = {}
        for section in self._sections:
            key = section.shortcut.strip().lower()
            if not key:
                raise RuntimeError(f"Missing shortcut for section '{section.key}'.")
            if key in reserved:
                raise RuntimeError(
                    f"Shortcut '{key}' for section '{section.key}' conflicts with reserved keys."
                )
            if key in seen:
                raise RuntimeError(
                    f"Duplicate shortcut '{key}' used by sections "
                    f"'{seen[key]}' and '{section.key}'."
                )
            seen[key] = section.key
            self.bind(
                key,
                f"go('{section.key}')",
                description=section.label,
                show=False,
            )

    def _resolve_initial(self, requested: str) -> str:
        key = requested.lower()
        if key in self._section_index:
            return key
        return self._sections[0].key

    def _refresh_active_pane(self) -> None:
        switcher = self.query_one("#content-switcher", ContentSwitcher)
        active = switcher.current
        if not active:
            return
        pane = next((pane for pane in self._panes if pane.id == active), None)
        if pane is None:
            return
        refresh = getattr(pane, "refresh_data", None)
        if callable(refresh):
            label = self._sections[self._section_index[active]].label
            try:
                result = refresh()
            except Exception as exc:
                self._handle_refresh_error(label, exc)
                return
            if asyncio.iscoroutine(result):
                task = asyncio.create_task(self._run_safe_refresh(result, label))
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)

    async def _run_safe_refresh(self, coro, label: str) -> None:
        try:
            await coro
        except Exception as exc:
            self._handle_refresh_error(label, exc)

    def _handle_refresh_error(self, label: str, exc: Exception) -> None:
        message = f"{label} refresh failed: {exc}"
        self.ctx.console.error(message, topic="tui")
        notify = getattr(self, "notify", None)
        if callable(notify):
            try:
                notify(message, severity="error")
            except Exception:
                return


__all__ = ["StarterTUI"]


def _binding_key(binding: Binding | tuple[str, ...]) -> str:
    if isinstance(binding, Binding):
        return binding.key
    if binding:
        return str(binding[0])
    return ""
