from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static


class FooterPane(Vertical):
    def __init__(self, *, pane_id: str) -> None:
        super().__init__(id=pane_id, classes="section-pane footer-pane")

    def compose(self) -> ComposeResult:
        with Vertical(id=f"{self.id}-body", classes="pane-body"):
            yield from self.compose_body()
        with Horizontal(id=f"{self.id}-footer", classes="pane-footer"):
            yield from self.compose_footer()

    def compose_body(self) -> ComposeResult:
        raise NotImplementedError

    def compose_footer(self) -> ComposeResult:
        yield self.footer_spacer()

    @staticmethod
    def footer_spacer() -> Static:
        return Static("", classes="pane-footer-spacer")


__all__ = ["FooterPane"]
