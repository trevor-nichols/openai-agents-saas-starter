from __future__ import annotations

from collections.abc import Sequence

from starter_cli.adapters.io.console import console

from ..section_specs import SectionSpec
from .view import WizardUIView


class WizardUICommandHandler:
    """Parses inline commands (e.g., :expand core) to control the wizard UI."""

    def __init__(self, ui: WizardUIView, sections: Sequence[SectionSpec]) -> None:
        self.ui = ui
        self._order_map: dict[str, str] = {
            str(idx + 1): spec.key for idx, spec in enumerate(sections)
        }
        self._sections_by_key: dict[str, SectionSpec] = {spec.key: spec for spec in sections}
        self._label_map: dict[str, str] = {spec.key.lower(): spec.key for spec in sections}

    def handle(self, raw: str) -> bool:
        if not raw.startswith(":"):
            return False
        tokens = raw[1:].strip().split()
        if not tokens:
            return False
        command = tokens[0].lower()
        arg = " ".join(tokens[1:]).strip()
        if command in {"h", "help"}:
            self._render_help()
            return True
        if command in {"expand", "open"}:
            return self._expand(arg)
        if command in {"collapse", "close"}:
            return self._collapse(arg)
        if command == "toggle":
            return self._toggle(arg)
        if command in {"list", "sections"}:
            self._list_sections()
            return True
        console.warn(f"Unknown UI command '{command}'. Type :help for options.", topic="wizard")
        return True

    # ------------------------------------------------------------------
    # Command handlers
    # ------------------------------------------------------------------
    def _expand(self, target: str) -> bool:
        key = self._resolve_section(target)
        if not key:
            return True
        self.ui.expand_section(key)
        console.info(f"Expanded {key} in wizard UI.", topic="wizard")
        return True

    def _collapse(self, target: str) -> bool:
        key = self._resolve_section(target)
        if not key:
            return True
        self.ui.collapse_section(key)
        console.info(f"Collapsed {key} in wizard UI.", topic="wizard")
        return True

    def _toggle(self, target: str) -> bool:
        key = self._resolve_section(target)
        if not key:
            return True
        self.ui.toggle_section(key)
        console.info(f"Toggled {key} in wizard UI.", topic="wizard")
        return True

    def _resolve_section(self, ref: str) -> str | None:
        candidate = ref.strip().lower()
        if not candidate:
            console.warn("Specify a section key or number.", topic="wizard")
            return None
        if candidate in self._order_map:
            return self._order_map[candidate]
        if candidate in self._label_map:
            return self._label_map[candidate]
        console.warn(f"Unknown section '{ref}'. Use :list to view options.", topic="wizard")
        return None

    def _list_sections(self) -> None:
        rows: list[str] = []
        for num, key in self._order_map.items():
            spec = self._sections_by_key[key]
            rows.append(f"{num}. {spec.label} ({key})")
        console.info("Available sections:\n" + "\n".join(rows), topic="wizard")

    def _render_help(self) -> None:
        console.note(
            "UI commands: :expand <section>, :collapse <section>, :toggle <section>, :list, :help",
            topic="wizard",
        )


__all__ = ["WizardUICommandHandler"]
