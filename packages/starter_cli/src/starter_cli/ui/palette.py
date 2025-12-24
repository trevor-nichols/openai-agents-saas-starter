from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, ListItem, ListView, Static


@dataclass(frozen=True, slots=True)
class CommandSpec:
    key: str
    label: str
    description: str
    action: Callable[[], None]


class CommandItem(ListItem):
    def __init__(self, command: CommandSpec) -> None:
        super().__init__(classes="palette-item")
        self.command = command

    def compose(self) -> ComposeResult:
        yield Static(self.command.label, classes="palette-label")
        yield Static(self.command.description, classes="palette-desc")


class CommandPaletteScreen(ModalScreen[None]):
    DEFAULT_CSS: ClassVar[str] = """
    CommandPaletteScreen {
        align: center middle;
    }

    #palette {
        width: 70%;
        max-width: 80;
        background: $panel;
        border: solid $primary;
        padding: 1 2;
    }

    #palette-title {
        text-style: bold;
        padding-bottom: 1;
    }

    #palette-input {
        margin-bottom: 1;
    }

    #palette-list {
        height: auto;
        max-height: 14;
    }

    .palette-label {
        text-style: bold;
    }

    .palette-desc {
        color: $text-muted;
    }
    """

    BINDINGS: ClassVar = [
        Binding("escape", "close", "Close", show=False),
        Binding("enter", "choose", "Choose", show=False),
    ]

    def __init__(self, commands: Iterable[CommandSpec]) -> None:
        super().__init__()
        self._commands = list(commands)
        self._visible: list[CommandSpec] = list(self._commands)

    def compose(self) -> ComposeResult:
        with Vertical(id="palette"):
            yield Static("Command Palette", id="palette-title")
            yield Input(placeholder="Type to filter commands", id="palette-input")
            yield ListView(id="palette-list")

    def on_mount(self) -> None:
        self._render_list()
        self.query_one(Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        query = event.value.strip().lower()
        if not query:
            self._visible = list(self._commands)
        else:
            self._visible = [
                cmd
                for cmd in self._commands
                if query in cmd.label.lower() or query in cmd.description.lower()
            ]
        self._render_list()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if not isinstance(item, CommandItem):
            return
        self._run_command(item.command)

    def action_close(self) -> None:
        self.dismiss()

    def action_choose(self) -> None:
        command = self._current_command()
        if command is None:
            return
        self._run_command(command)

    def _render_list(self) -> None:
        list_view = self.query_one("#palette-list", ListView)
        list_view.clear()
        for command in self._visible:
            list_view.append(CommandItem(command))
        if self._visible:
            list_view.index = 0

    def _current_command(self) -> CommandSpec | None:
        list_view = self.query_one("#palette-list", ListView)
        index = list_view.index
        if index is None or index < 0:
            return None
        if index >= len(self._visible):
            return None
        return self._visible[index]

    def _run_command(self, command: CommandSpec) -> None:
        self.dismiss()
        self.app.call_later(command.action)


__all__ = ["CommandPaletteScreen", "CommandSpec"]
