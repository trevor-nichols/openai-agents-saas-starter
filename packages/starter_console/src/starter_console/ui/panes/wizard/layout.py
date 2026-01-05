from __future__ import annotations

from collections.abc import Sequence

from textual.app import ComposeResult
from textual.containers import Grid, Horizontal, Vertical
from textual.widgets import (
    Button,
    Collapsible,
    DataTable,
    Input,
    OptionList,
    ProgressBar,
    RadioButton,
    RadioSet,
    Static,
    Switch,
)

from starter_console.workflows.setup.automation import ALL_AUTOMATION_PHASES
from starter_console.workflows.setup.section_specs import SECTION_SPECS

from .models import ProfileOption


def compose_wizard_layout(profile_options: Sequence[ProfileOption]) -> ComposeResult:
    yield Static("Setup Wizard", classes="section-title")
    yield Static("", id="wizard-summary", classes="section-summary")
    with Grid(id="wizard-controls", classes="form-grid"):
        yield Static("Profile", id="wizard-profile-label", classes="wizard-control-label")
        yield RadioSet(
            *(RadioButton(option.label, id=option.widget_id) for option in profile_options),
            id="wizard-profile",
        )
        yield Static("Profile hint", id="wizard-profile-hint-label", classes="wizard-control-label")
        yield Static("", id="wizard-profile-hint", classes="wizard-control-hint")
        yield Static(
            "Policy locks",
            id="wizard-profile-locks-label",
            classes="wizard-control-label",
        )
        yield Static("", id="wizard-profile-locks", classes="wizard-control-hint")
        yield Static("Hosting", id="wizard-preset-label", classes="wizard-control-label")
        yield RadioSet(
            RadioButton("Local Docker", id="preset-local"),
            RadioButton("Cloud Managed", id="preset-cloud"),
            RadioButton("Enterprise", id="preset-enterprise"),
            id="wizard-preset",
        )
        yield Static("Cloud", id="wizard-cloud-label", classes="wizard-control-label")
        yield RadioSet(
            RadioButton("AWS", id="cloud-aws"),
            RadioButton("Azure", id="cloud-azure"),
            RadioButton("GCP", id="cloud-gcp"),
            RadioButton("Other", id="cloud-other"),
            id="wizard-cloud",
        )
    with Horizontal(classes="ops-actions"):
        yield Button("Start Wizard", id="wizard-start", variant="primary")
    with Collapsible(
        title="Wizard options",
        id="wizard-options-collapsible",
        collapsed=True,
    ):
        with Grid(classes="form-grid"):
            yield Static("Mode", classes="wizard-control-label")
            yield RadioSet(
                RadioButton("Interactive", id="wizard-mode-interactive"),
                RadioButton("Headless", id="wizard-mode-headless"),
                RadioButton("Report-only", id="wizard-mode-report"),
                id="wizard-mode",
            )
            yield Static("Strict", classes="wizard-control-label")
            yield Switch(value=False, id="wizard-strict")
            yield Static("Output format", classes="wizard-control-label")
            yield RadioSet(
                RadioButton("Summary", id="wizard-output-summary"),
                RadioButton("JSON", id="wizard-output-json"),
                RadioButton("Checklist", id="wizard-output-checklist"),
                id="wizard-output-format",
            )
            yield Static("Answers files", classes="wizard-control-label")
            yield Input(id="wizard-answers-files")
            yield Static("Var overrides", classes="wizard-control-label")
            yield Input(id="wizard-var-overrides")
            yield Static("Export answers path", classes="wizard-control-label")
            yield Input(id="wizard-export-answers")
            yield Static("Summary path", classes="wizard-control-label")
            yield Input(id="wizard-summary-path")
            yield Static("Markdown summary path", classes="wizard-control-label")
            yield Input(id="wizard-markdown-summary-path")
        with Collapsible(
            title="Automation overrides",
            id="wizard-automation-overrides",
            collapsed=True,
        ):
            with Grid(classes="form-grid"):
                for phase in ALL_AUTOMATION_PHASES:
                    yield Static(phase.value, classes="wizard-control-label")
                    yield RadioSet(
                        RadioButton("Auto", id=f"wizard-auto-{phase.value}"),
                        RadioButton("On", id=f"wizard-on-{phase.value}"),
                        RadioButton("Off", id=f"wizard-off-{phase.value}"),
                        id=f"wizard-automation-{phase.value}",
                    )
    yield ProgressBar(id="wizard-progress", total=len(SECTION_SPECS))
    with Horizontal(id="wizard-main"):
        yield DataTable(id="wizard-sections", zebra_stripes=True)
        yield DataTable(id="wizard-automation", zebra_stripes=True)
    yield DataTable(id="wizard-conditional", zebra_stripes=True)
    yield Static("", id="wizard-activity", classes="section-footnote")
    yield Static("", id="wizard-output", classes="ops-output")
    yield Static("", id="wizard-status", classes="section-footnote")
    with Vertical(id="wizard-prompt"):
        yield Static("", id="wizard-prompt-label")
        yield Static("", id="wizard-prompt-detail")
        yield Input(id="wizard-input")
        yield OptionList(id="wizard-options")
        with Horizontal(id="wizard-prompt-actions"):
            yield Button("Submit", id="wizard-submit", variant="primary")
            yield Button("Clear", id="wizard-clear")
        yield Static("", id="wizard-prompt-status", classes="section-footnote")


__all__ = ["compose_wizard_layout"]
