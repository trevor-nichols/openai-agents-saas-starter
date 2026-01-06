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
    RadioButton,
    RadioSet,
    Static,
    Switch,
)

from starter_console.workflows.setup.automation import ALL_AUTOMATION_PHASES

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
    with Collapsible(
        title="Advanced run options",
        id="wizard-options-collapsible",
        collapsed=True,
    ):
        with Grid(classes="form-grid"):
            yield Static("Mode", id="wizard-mode-label", classes="wizard-control-label")
            yield RadioSet(
                RadioButton("Interactive", id="wizard-mode-interactive"),
                RadioButton("Headless", id="wizard-mode-headless"),
                RadioButton("Report-only", id="wizard-mode-report"),
                id="wizard-mode",
            )
            yield Static("Strict", id="wizard-strict-label", classes="wizard-control-label")
            yield Switch(value=False, id="wizard-strict")
            yield Static("Output format", id="wizard-output-label", classes="wizard-control-label")
            yield RadioSet(
                RadioButton("Summary", id="wizard-output-summary"),
                RadioButton("JSON", id="wizard-output-json"),
                RadioButton("Checklist", id="wizard-output-checklist"),
                id="wizard-output-format",
            )
            yield Static(
                "Show automation overrides",
                id="wizard-show-automation-label",
                classes="wizard-control-label",
            )
            yield Switch(value=False, id="wizard-show-automation")
        with Collapsible(
            title="Headless inputs",
            id="wizard-headless-inputs",
            collapsed=True,
        ):
            with Grid(classes="form-grid"):
                yield Static(
                    "Answers files",
                    id="wizard-answers-files-label",
                    classes="wizard-control-label",
                )
                yield Input(id="wizard-answers-files")
                yield Static(
                    "Var overrides",
                    id="wizard-var-overrides-label",
                    classes="wizard-control-label",
                )
                yield Input(id="wizard-var-overrides")
                yield Static(
                    "Export answers path",
                    id="wizard-export-answers-label",
                    classes="wizard-control-label",
                )
                yield Input(id="wizard-export-answers")
        with Collapsible(
            title="Output files (optional)",
            id="wizard-output-paths",
            collapsed=True,
        ):
            with Grid(classes="form-grid"):
                yield Static(
                    "Summary path",
                    id="wizard-summary-path-label",
                    classes="wizard-control-label",
                )
                yield Input(id="wizard-summary-path")
                yield Static(
                    "Markdown summary path",
                    id="wizard-markdown-summary-path-label",
                    classes="wizard-control-label",
                )
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
    yield Static("", id="wizard-stepper")
    with Horizontal(id="wizard-main"):
        yield DataTable(id="wizard-sections", zebra_stripes=True)
        yield DataTable(id="wizard-automation", zebra_stripes=True)
    yield DataTable(id="wizard-conditional", zebra_stripes=True)
    yield Static("", id="wizard-activity", classes="section-footnote")
    with Horizontal(classes="ops-actions"):
        yield Button("Open Editor", id="wizard-open-editor")
        yield Button("Start Wizard", id="wizard-start", variant="primary")
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
