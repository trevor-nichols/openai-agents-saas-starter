from __future__ import annotations

from collections.abc import Sequence

from textual.widgets import OptionList, Static

from starter_console.workflows.setup.editor.models import FieldSpec, SectionModel


def render_sections(
    pane,
    *,
    sections: Sequence[SectionModel],
    selected_index: int,
) -> list[str]:
    option_list = pane.query_one("#wizard-editor-sections", OptionList)
    option_list.clear_options()
    keys: list[str] = []
    for section in sections:
        label = section.label
        missing = section.missing_required
        if missing:
            label = f"{label} ({missing})"
        option_list.add_option(label)
        keys.append(section.key)
    if sections:
        option_list.highlighted = min(selected_index, len(sections) - 1)
    return keys


def render_fields(
    pane,
    *,
    fields: Sequence[FieldSpec],
    selected_index: int,
) -> list[str]:
    option_list = pane.query_one("#wizard-editor-fields", OptionList)
    option_list.clear_options()
    keys: list[str] = []
    for field in fields:
        value = field.display_value()
        label = field.label.strip() if field.label else field.key
        option_list.add_option(f"{label} • {value} [{field.key}]")
        keys.append(field.key)
    if fields:
        option_list.highlighted = min(selected_index, len(fields) - 1)
    return keys


def render_detail(pane, field: FieldSpec | None) -> None:
    detail = ""
    if field is not None:
        detail = field.description or "No description available."
    pane.query_one("#wizard-editor-detail", Static).update(detail)


__all__ = ["render_detail", "render_fields", "render_sections"]
