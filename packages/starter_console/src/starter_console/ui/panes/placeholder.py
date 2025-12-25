from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

from ..sections import SectionSpec


class PlaceholderPane(Vertical):
    def __init__(self, section: SectionSpec) -> None:
        super().__init__(id=section.key, classes="section-pane")
        self.section = section

    def compose(self) -> ComposeResult:
        yield Static(self.section.label, classes="section-title")
        yield Static(self.section.description, classes="section-description")
        yield Static(self.section.detail, classes="section-detail")
        yield Static("More coming soon in this phase.", classes="section-footnote")


__all__ = ["PlaceholderPane"]
