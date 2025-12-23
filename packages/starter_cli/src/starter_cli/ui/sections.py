from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import ListItem, Static


@dataclass(frozen=True, slots=True)
class SectionSpec:
    key: str
    label: str
    description: str
    detail: str
    shortcut: str


SECTIONS: Final[tuple[SectionSpec, ...]] = (
    SectionSpec(
        key="home",
        label="Home",
        description="Operational overview and quick actions",
        detail="Status, health, and shortcuts for the starter stack.",
        shortcut="H",
    ),
    SectionSpec(
        key="setup",
        label="Setup Hub",
        description="Bootstrap secrets, env, and providers",
        detail="Guided setup actions to get the stack production-ready.",
        shortcut="S",
    ),
    SectionSpec(
        key="wizard",
        label="Wizard",
        description="Interactive setup walkthrough",
        detail="Step-by-step prompts for first-time configuration.",
        shortcut="W",
    ),
    SectionSpec(
        key="logs",
        label="Logs",
        description="Tail and filter local logs",
        detail="Inspect API, frontend, and CLI logs with context.",
        shortcut="L",
    ),
    SectionSpec(
        key="infra",
        label="Infra",
        description="Local stack status and controls",
        detail="Compose services, vault, and supporting infra.",
        shortcut="I",
    ),
    SectionSpec(
        key="providers",
        label="Providers",
        description="External provider configuration",
        detail="OpenAI, email, storage, and other integrations.",
        shortcut="P",
    ),
    SectionSpec(
        key="stripe",
        label="Stripe",
        description="Billing setup and webhooks",
        detail="Keys, products, prices, and webhook verification.",
        shortcut="B",
    ),
    SectionSpec(
        key="usage",
        label="Usage",
        description="Usage and cost summaries",
        detail="Track token usage and spend across environments.",
        shortcut="U",
    ),
)


class NavItem(ListItem):
    def __init__(self, section: SectionSpec) -> None:
        super().__init__(classes="nav-item")
        self.section = section

    def compose(self) -> ComposeResult:
        with Horizontal(classes="nav-row"):
            yield Static(self.section.shortcut, classes="nav-key")
            yield Static(self.section.label, classes="nav-label")
        yield Static(self.section.description, classes="nav-desc")


__all__ = ["NavItem", "SECTIONS", "SectionSpec"]
