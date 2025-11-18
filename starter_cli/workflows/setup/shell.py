from __future__ import annotations

from collections.abc import Callable

from rich.table import Table
from rich.text import Text

from starter_cli.adapters.io.console import console
from ._wizard.context import WizardContext
from .section_specs import SectionSpec

_STATUS_STYLES: dict[str, tuple[str, str]] = {
    "pending": ("Pending", "#808080"),
    "running": ("In Progress", "yellow"),
    "done": ("Done", "green"),
    "failed": ("Failed", "red"),
}


class WizardShell:
    """Keyboard-driven shell that lets operators jump between wizard sections."""

    def __init__(
        self,
        *,
        context: WizardContext,
        sections: list[SectionSpec],
        section_states: dict[str, str],
        runners: dict[str, Callable[[], None]],
        run_section: Callable[[str, Callable[[], None]], bool],
    ) -> None:
        self.context = context
        self.sections = sections
        self.section_states = section_states
        self.runners = runners
        self._run_section_cb = run_section
        self._index_map: dict[str, str] = {
            str(idx + 1): spec.key for idx, spec in enumerate(sections)
        }
        self._section_lookup: dict[str, SectionSpec] = {spec.key: spec for spec in sections}

    def run(self) -> bool:
        first_render = self._is_first_run()
        while True:
            self._render_home(first_render)
            first_render = False
            all_complete = self._all_sections_complete()
            command = self._prompt_command(all_complete)
            if command == "quit":
                return False
            if command == "finish":
                return True
            if command == "next":
                key = self._next_incomplete()
                if key is None:
                    if all_complete:
                        return True
                    console.note(
                        (
                            "All sections completed; choose a number to revisit "
                            "or press Enter to finish."
                        ),
                        topic="wizard",
                    )
                    continue
            else:
                key = command
            if not key:
                continue
            self._open_section(key)

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------
    def _render_home(self, first_render: bool) -> None:
        completed = sum(1 for state in self.section_states.values() if state == "done")
        subtitle = f"{completed}/{len(self.sections)} sections complete"
        next_key = self._next_incomplete()
        if next_key:
            next_label = self._section_lookup[next_key].label
            subtitle += f" • Next: {next_label}"
        if first_render:
            subtitle += " • Use number keys or Enter to navigate"
        console.section("Starter CLI Setup", subtitle)
        table = Table(box=None, show_header=True, header_style="bold", expand=True)
        table.add_column("#", width=3, justify="right")
        table.add_column("Section")
        table.add_column("Status", no_wrap=True)
        table.add_column("Summary")
        for idx, spec in enumerate(self.sections, start=1):
            state = self.section_states.get(spec.key, "pending")
            display = self._status_text(state)
            table.add_row(str(idx), spec.label, display, spec.summary)
        console.render(table)
        console.note(
            "Commands: [Enter]=next incomplete, [number]=open section, Q=quit",
            topic="wizard",
        )

    def _status_text(self, state: str) -> Text:
        label, style = _STATUS_STYLES.get(state, (state.title(), "white"))
        return Text(label, style=style)

    # ------------------------------------------------------------------
    # Command handling
    # ------------------------------------------------------------------
    def _prompt_command(self, all_complete: bool) -> str:
        prompt = "Command > "
        while True:
            raw = input(prompt).strip().lower()
            if not raw:
                return "finish" if all_complete else "next"
            if raw in {"q", "quit"}:
                return "quit"
            if raw in {"n", "next"}:
                return "next"
            if raw.isdigit() and raw in self._index_map:
                return self._index_map[raw]
            # allow section keys directly
            if raw in self._section_lookup:
                return raw
            console.warn(
                "Unrecognized command. Use Enter for next, numbers for sections, "
                "or Q to quit.",
                topic="wizard",
            )

    def _next_incomplete(self) -> str | None:
        for spec in self.sections:
            if self.section_states.get(spec.key) != "done":
                return spec.key
        return None

    def _all_sections_complete(self) -> bool:
        return all(self.section_states.get(spec.key) == "done" for spec in self.sections)

    def _open_section(self, key: str) -> None:
        spec = self._section_lookup[key]
        console.note(f"Opening {spec.label} …", topic="wizard")
        runner = self.runners[key]
        success = self._run_section_cb(key, runner)
        if success:
            console.success(f"{spec.label} finished.", topic="wizard")
        else:
            console.error(
                (
                    f"{spec.label} encountered an error. Review the message above and "
                    "rerun when ready."
                ),
                topic="wizard",
            )
        console.newline()

    def _is_first_run(self) -> bool:
        store = self.context.state_store
        if store is None:
            return True
        snapshot = store.snapshot()
        return not snapshot


__all__ = ["WizardShell"]
