from __future__ import annotations

from collections.abc import Sequence

from textual.app import ComposeResult
from textual.containers import Grid, Horizontal, Vertical
from textual.widgets import (
    Button,
    Collapsible,
    Input,
    OptionList,
    RadioButton,
    RadioSet,
    Static,
)

from starter_console.ui.panes.wizard.models import ProfileOption


def compose_wizard_editor_layout(profile_options: Sequence[ProfileOption]) -> ComposeResult:
    yield Static("Wizard Editor", classes="section-title")
    yield Static("", id="wizard-editor-summary", classes="section-summary")
    with Horizontal(classes="ops-actions"):
        yield Button("Back to Wizard", id="wizard-editor-back")
        yield Button("Save", id="wizard-editor-save", variant="primary")
        yield Button("Save + Automation", id="wizard-editor-save-automation")
    with Collapsible(title="Profile", id="wizard-editor-profile", collapsed=True):
        with Grid(classes="form-grid"):
            yield Static("Profile", classes="wizard-control-label")
            yield RadioSet(
                *(RadioButton(option.label, id=option.widget_id) for option in profile_options),
                id="wizard-editor-profile-options",
            )
    with Horizontal(id="wizard-editor-main"):
        yield OptionList(id="wizard-editor-sections")
        with Vertical(id="wizard-editor-fields-pane"):
            yield Input(
                id="wizard-editor-filter",
                placeholder="Filter fields by label or key",
            )
            yield OptionList(id="wizard-editor-fields")
    yield Static("", id="wizard-editor-detail", classes="section-footnote")
    yield Static("", id="wizard-editor-status", classes="section-footnote")
    yield Static("", id="wizard-editor-output", classes="ops-output")
    with Vertical(id="wizard-editor-prompt"):
        yield Static("", id="wizard-editor-prompt-label")
        yield Static("", id="wizard-editor-prompt-detail")
        yield Input(id="wizard-editor-input")
        yield OptionList(id="wizard-editor-options")
        with Horizontal(id="wizard-editor-prompt-actions"):
            yield Button("Apply", id="wizard-editor-apply", variant="primary")
            yield Button("Cancel", id="wizard-editor-cancel")
        yield Static("", id="wizard-editor-prompt-status", classes="section-footnote")


__all__ = ["compose_wizard_editor_layout"]
