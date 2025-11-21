from __future__ import annotations

from rich.text import Text

from starter_cli.core.status_models import ProbeState


def state_chip(state: ProbeState) -> Text:
    colors = {
        ProbeState.OK: "bold green",
        ProbeState.WARN: "bold yellow",
        ProbeState.ERROR: "bold red",
        ProbeState.SKIPPED: "bright_black",
    }
    return Text(state.value.upper(), style=colors.get(state, "white"))


__all__ = ["state_chip"]
