from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
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


def compose_wizard_layout() -> ComposeResult:
    yield Static("Setup Wizard", classes="section-title")
    yield Static("", id="wizard-summary", classes="section-summary")
    with Horizontal(id="wizard-controls"):
        yield Static("Profile", id="wizard-profile-label", classes="wizard-control-label")
        yield RadioSet(
            RadioButton("Demo", id="profile-demo"),
            RadioButton("Staging", id="profile-staging"),
            RadioButton("Production", id="profile-production"),
            id="wizard-profile",
        )
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
        yield Static("Advanced", id="wizard-advanced-label", classes="wizard-control-label")
        yield RadioSet(
            RadioButton("On", id="advanced-on"),
            RadioButton("Off", id="advanced-off"),
            id="wizard-advanced",
        )
        yield Button("Start Wizard", id="wizard-start", variant="primary")
    with Collapsible(
        title="Wizard options",
        id="wizard-options-collapsible",
        collapsed=True,
    ):
        with Horizontal(classes="wizard-options"):
            yield Static("Mode", classes="wizard-control-label")
            yield RadioSet(
                RadioButton("Interactive", id="wizard-mode-interactive"),
                RadioButton("Headless", id="wizard-mode-headless"),
                RadioButton("Report-only", id="wizard-mode-report"),
                id="wizard-mode",
            )
            yield Static("Strict", classes="wizard-control-label")
            yield Switch(value=False, id="wizard-strict")
        with Horizontal(classes="wizard-options"):
            yield Static("Output format", classes="wizard-control-label")
            yield RadioSet(
                RadioButton("Summary", id="wizard-output-summary"),
                RadioButton("JSON", id="wizard-output-json"),
                RadioButton("Checklist", id="wizard-output-checklist"),
                id="wizard-output-format",
            )
        with Horizontal(classes="wizard-options"):
            yield Static("Answers files", classes="wizard-control-label")
            yield Input(id="wizard-answers-files")
            yield Static("Var overrides", classes="wizard-control-label")
            yield Input(id="wizard-var-overrides")
        with Horizontal(classes="wizard-options"):
            yield Static("Export answers path", classes="wizard-control-label")
            yield Input(id="wizard-export-answers")
            yield Static("Summary path", classes="wizard-control-label")
            yield Input(id="wizard-summary-path")
        with Horizontal(classes="wizard-options"):
            yield Static("Markdown summary path", classes="wizard-control-label")
            yield Input(id="wizard-markdown-summary-path")
        with Collapsible(
            title="Automation overrides",
            id="wizard-automation-overrides",
            collapsed=True,
        ):
            for phase in ALL_AUTOMATION_PHASES:
                with Horizontal(classes="wizard-options"):
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
