from __future__ import annotations

import curses

from .layout import PANE_DIVIDER_X, VALUE_COLUMN_OFFSET
from .models import FieldSpec, SectionModel
from .utils import missing_required


def draw_header(
    stdscr,
    *,
    width: int,
    title: str,
    profile_id: str,
    dirty: bool,
) -> None:
    profile_label = f"Profile: {profile_id}"
    stdscr.addstr(0, 2, title, curses.A_BOLD)
    if dirty:
        indicator = " • unsaved"
        max_indicator = width - len(profile_label) - 6 - len(title)
        if max_indicator >= len(indicator):
            stdscr.addstr(0, 2 + len(title), indicator, curses.color_pair(2) | curses.A_BOLD)
        elif max_indicator >= 2:
            stdscr.addstr(0, 2 + len(title), " *", curses.color_pair(2) | curses.A_BOLD)
    stdscr.addstr(0, width - len(profile_label) - 2, profile_label)


def draw_sections(
    stdscr,
    *,
    sections: list[SectionModel],
    height: int,
    width: int,
    selected_section: int,
    active_pane: str,
) -> None:
    left_width = PANE_DIVIDER_X
    stdscr.vline(1, left_width, curses.ACS_VLINE, height - 3)
    stdscr.addstr(1, 2, "Sections", curses.A_BOLD)
    for idx, section in enumerate(sections):
        label = f"{section.label}"
        missing = section.missing_required
        if missing:
            label = f"{label} ({missing})"
        y = idx + 3
        if y >= height - 2:
            break
        if idx == selected_section and active_pane == "sections":
            stdscr.addstr(y, 2, label[: left_width - 4], curses.color_pair(4))
        else:
            stdscr.addstr(y, 2, label[: left_width - 4])


def draw_fields(
    stdscr,
    *,
    fields: list[FieldSpec],
    height: int,
    width: int,
    selected_field: int,
    active_pane: str,
    scroll_offset: int,
    filter_text: str | None,
) -> None:
    left_width = PANE_DIVIDER_X
    visible_count = field_window_size(height)
    visible_fields = fields[scroll_offset : scroll_offset + visible_count]
    header = _build_fields_header(
        total=len(fields),
        scroll_offset=scroll_offset,
        visible_count=visible_count,
        filter_text=filter_text,
    )
    max_header = width - left_width - 4
    stdscr.addstr(1, left_width + 2, _truncate(header, max_len=max_header), curses.A_BOLD)
    for idx, field in enumerate(visible_fields):
        absolute_index = scroll_offset + idx
        y = 3 + idx * 2
        if y >= height - 2:
            break
        value = field.display_value()
        label_base = _sanitize_label(field.label, field.key)
        label = f"- {label_base}" if label_base else "-"
        max_width = width - left_width - 4
        label_text, env_text = _build_label_parts(label, field.key, max_width=max_width)
        value_text = _truncate(value, max_len=max_width)
        selected = absolute_index == selected_field and active_pane == "fields"
        selection_attr = curses.A_REVERSE if selected else curses.A_NORMAL
        label_attr = curses.color_pair(2) | selection_attr
        env_attr = curses.color_pair(6) | curses.A_DIM | selection_attr
        if field.is_missing():
            value_attr = curses.color_pair(3) | selection_attr
        else:
            value_attr = curses.color_pair(1) | selection_attr
        x = left_width + 2
        stdscr.addstr(y, x, label_text, label_attr)
        value_y = y + 1
        x += len(label_text)
        if env_text:
            if label_text:
                stdscr.addstr(y, x, " ", label_attr)
                x += 1
            stdscr.addstr(y, x, env_text, env_attr)
        if value_y < height - 2:
            value_x = left_width + VALUE_COLUMN_OFFSET
            max_value = max(0, width - value_x - 2)
            stdscr.addstr(
                value_y,
                value_x,
                _truncate(value_text, max_len=max_value),
                value_attr,
            )


def draw_footer(
    stdscr,
    *,
    sections: list[SectionModel],
    height: int,
    width: int,
    status: str,
    filter_text: str | None,
    dirty: bool,
) -> None:
    missing = missing_required(sections)
    missing_count = len(missing)
    total_required = sum(
        1 for section in sections for field in section.fields if field.required
    )
    completed_required = max(0, total_required - missing_count)
    ready = "yes" if missing_count == 0 else "no"
    stdscr.hline(height - 2, 0, curses.ACS_HLINE, width)
    help_segments = [
        ("Tab:", curses.A_BOLD),
        (" switch pane  ", curses.A_NORMAL),
        ("Enter:", curses.A_BOLD),
        (" edit  ", curses.A_NORMAL),
        ("/:", curses.A_BOLD),
        (" search  ", curses.A_NORMAL),
        ("S:", curses.A_BOLD),
        (" save  ", curses.A_NORMAL),
        ("A:", curses.A_BOLD),
        (" save+automation  ", curses.A_NORMAL),
        ("Q:", curses.A_BOLD),
        (" quit", curses.A_NORMAL),
    ]
    if filter_text:
        help_segments.extend(
            [
                ("  C:", curses.A_BOLD),
                (" clear filter", curses.A_NORMAL),
            ]
        )
    x = 2
    y = height - 1
    for text, attr in help_segments:
        if x >= width - 2:
            break
        chunk = text[: max(0, width - 2 - x)]
        stdscr.addstr(y, x, chunk, curses.color_pair(1) | attr)
        x += len(chunk)
    if status:
        label_x = width - len(status) - 2
        if label_x > x:
            stdscr.addstr(y, label_x, status)
    else:
        prefix = "Automation ready: "
        dirty_prefix = "Unsaved changes • " if dirty else ""
        badge = ""
        if total_required:
            badge = f" ({completed_required}/{total_required})"
        label_x = width - len(dirty_prefix) - len(prefix) - len(ready) - len(badge) - 2
        if label_x > x:
            current_x = label_x
            if dirty_prefix:
                stdscr.addstr(
                    y,
                    current_x,
                    dirty_prefix,
                    curses.color_pair(2) | curses.A_BOLD,
                )
                current_x += len(dirty_prefix)
            stdscr.addstr(y, current_x, prefix)
            current_x += len(prefix)
            if ready == "yes":
                value_attr = curses.color_pair(5) | curses.A_BOLD
            else:
                value_attr = curses.color_pair(3) | curses.A_BOLD
            stdscr.addstr(y, current_x, ready, value_attr)
            current_x += len(ready)
            if badge:
                stdscr.addstr(y, current_x, badge, curses.A_DIM)


def field_window_size(height: int) -> int:
    max_label_y = height - 4
    first_label_y = 3
    if max_label_y < first_label_y:
        return 0
    max_rows = max_label_y - first_label_y
    return (max_rows // 2) + 1


def _build_fields_header(
    *,
    total: int,
    scroll_offset: int,
    visible_count: int,
    filter_text: str | None,
) -> str:
    if total <= visible_count:
        base = "Fields"
    else:
        has_above = scroll_offset > 0
        has_below = (scroll_offset + visible_count) < total
        if has_above and has_below:
            base = "Fields ↑↓"
        elif has_above:
            base = "Fields ↑"
        elif has_below:
            base = "Fields ↓"
        else:
            base = "Fields"
    if filter_text:
        return f"{base} / {filter_text}"
    return base


def _build_label_parts(label: str, key: str, *, max_width: int) -> tuple[str, str]:
    env_text = f"[{key}]"
    if max_width <= 0:
        return "", ""
    if len(env_text) + 1 > max_width:
        return _truncate(label, max_len=max_width), ""
    label_budget = max_width - len(env_text) - 1
    label_text = _truncate(label, max_len=label_budget)
    return label_text, env_text


def _sanitize_label(label: str, key: str) -> str:
    if not label:
        return ""
    scrubbed = label.replace(f"({key})", "").replace(f"[{key}]", "")
    return " ".join(scrubbed.split()).strip()


def _truncate(text: str, *, max_len: int) -> str:
    if max_len <= 0:
        return ""
    if len(text) <= max_len:
        return text
    if max_len <= 3:
        return text[:max_len]
    return f"{text[: max_len - 3]}..."


__all__ = [
    "draw_fields",
    "draw_footer",
    "draw_header",
    "draw_sections",
    "field_window_size",
]
