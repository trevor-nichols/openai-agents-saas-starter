from __future__ import annotations

import curses
from pathlib import Path

from starter_console.core import CLIContext

from .actions import apply_and_save
from .input import prompt_input, prompt_search, select_choice
from .layout import PANE_DIVIDER_X
from .models import FieldSpec, SectionModel
from .renderer import draw_fields, draw_footer, draw_header, draw_sections, field_window_size
from .sources import collect_sections, load_setting_descriptions
from .utils import automation_ready


class EditorController:
    def __init__(
        self,
        *,
        ctx: CLIContext,
        profile_id: str,
        profiles_path: Path | None,
        answers: dict[str, str],
        output_format: str,
        summary_path: Path | None,
        markdown_summary_path: Path | None,
        export_answers_path: Path | None,
    ) -> None:
        self._ctx = ctx
        self._profile_id = profile_id
        self._profiles_path = profiles_path
        self._answers = answers
        self._output_format = output_format
        self._summary_path = summary_path
        self._markdown_summary_path = markdown_summary_path
        self._export_answers_path = export_answers_path
        self._descriptions = load_setting_descriptions(ctx.project_root)
        self._sections: list[SectionModel] = []
        self._selected_section = 0
        self._selected_field = 0
        self._active_pane = "sections"
        self._status = ""
        self._field_scroll = 0
        self._field_filter: str | None = None
        self._dirty = False
        self._refresh()

    def run(self) -> None:
        curses.wrapper(self._loop)

    # ------------------------------------------------------------------
    # Rendering + input loop
    # ------------------------------------------------------------------
    def _loop(self, stdscr) -> None:
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_YELLOW, -1)
        curses.init_pair(3, curses.COLOR_RED, -1)
        curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(5, curses.COLOR_GREEN, -1)
        curses.init_pair(6, curses.COLOR_WHITE, -1)

        while True:
            stdscr.clear()
            height, width = stdscr.getmaxyx()
            if height < 12 or width < 70:
                stdscr.addstr(0, 0, "Terminal too small. Resize to continue.")
                stdscr.refresh()
                if stdscr.getch() in {ord("q"), ord("Q")}:
                    return
                continue

            draw_header(
                stdscr,
                width=width,
                title="Setup Wizard Editor (CLI)",
                profile_id=self._profile_id,
                dirty=self._dirty,
            )
            draw_sections(
                stdscr,
                sections=self._sections,
                height=height,
                width=width,
                selected_section=self._selected_section,
                active_pane=self._active_pane,
            )
            draw_fields(
                stdscr,
                fields=self._current_fields(),
                height=height,
                width=width,
                selected_field=self._selected_field,
                active_pane=self._active_pane,
                scroll_offset=self._field_scroll,
                filter_text=self._field_filter,
            )
            draw_footer(
                stdscr,
                sections=self._sections,
                height=height,
                width=width,
                status=self._status,
                filter_text=self._field_filter,
                dirty=self._dirty,
            )
            stdscr.refresh()

            key = stdscr.getch()
            if key in {ord("q"), ord("Q")}:
                return
            if key in {27, ord("c"), ord("C")} and self._field_filter:
                self._clear_filter()
                continue
            if key == ord("/"):
                self._prompt_filter(stdscr)
                continue
            if key in {ord("s"), ord("S")}:
                self._exit_and_save(run_automation=False)
                return
            if key in {ord("a"), ord("A")}:
                if automation_ready(self._sections):
                    self._exit_and_save(run_automation=True)
                    return
                self._status = "Automation disabled: missing required values."
            if key in {9}:  # Tab
                self._active_pane = "fields" if self._active_pane == "sections" else "sections"
            elif key in {curses.KEY_UP, ord("k")}:
                self._move_selection(-1)
            elif key in {curses.KEY_DOWN, ord("j")}:
                self._move_selection(1)
            elif key in {curses.KEY_RIGHT, ord("l")} and self._active_pane == "sections":
                self._active_pane = "fields"
            elif key in {curses.KEY_LEFT, ord("h")} and self._active_pane == "fields":
                self._active_pane = "sections"
            elif key in {curses.KEY_ENTER, 10, 13} and self._active_pane == "fields":
                self._edit_field(stdscr)
            self._ensure_field_visible(height=height)

    # ------------------------------------------------------------------
    # Editing + state
    # ------------------------------------------------------------------
    def _current_fields(self) -> list[FieldSpec]:
        if not self._sections:
            return []
        fields = self._sections[self._selected_section].fields
        return self._apply_filter(fields)

    def _move_selection(self, delta: int) -> None:
        if self._active_pane == "sections":
            self._selected_section = max(
                0, min(self._selected_section + delta, len(self._sections) - 1)
            )
            self._selected_field = 0
            self._field_scroll = 0
        else:
            fields = self._current_fields()
            if not fields:
                return
            self._selected_field = max(
                0, min(self._selected_field + delta, len(fields) - 1)
            )

    def _edit_field(self, stdscr) -> None:
        fields = self._current_fields()
        if not fields:
            return
        field = fields[self._selected_field]
        new_value = self._resolve_edit_value(stdscr, field)
        if new_value is None:
            return
        previous = self._answers.get(field.key)
        self._answers[field.key] = new_value
        if new_value != previous:
            self._dirty = True
        self._refresh(focus_key=field.key)

    def _resolve_edit_value(self, stdscr, field: FieldSpec) -> str | None:
        if field.kind == "bool":
            current = field.value or "false"
            return "false" if current.strip().lower() in {"1", "true", "yes", "y"} else "true"
        if field.kind == "choice":
            return select_choice(stdscr, field)
        if field.kind in {"string", "secret"}:
            return prompt_input(stdscr, field, divider_x=PANE_DIVIDER_X)
        return None

    def _refresh(self, *, focus_key: str | None = None) -> None:
        sections, _ = collect_sections(
            self._ctx,
            profile_id=self._profile_id,
            profiles_path=self._profiles_path,
            answers=self._answers,
            descriptions=self._descriptions,
            dry_run=True,
        )
        self._sections = sections
        self._field_scroll = 0
        if self._current_fields():
            self._selected_field = min(self._selected_field, len(self._current_fields()) - 1)
        else:
            self._selected_field = 0
        if focus_key:
            for s_idx, section in enumerate(self._sections):
                for _f_idx, field in enumerate(section.fields):
                    if field.key == focus_key:
                        self._selected_section = s_idx
                        filtered = self._apply_filter(section.fields)
                        if filtered:
                            for filtered_idx, filtered_field in enumerate(filtered):
                                if filtered_field.key == focus_key:
                                    self._selected_field = filtered_idx
                                    break
                            else:
                                self._selected_field = 0
                        else:
                            self._selected_field = 0
                        return

    def _ensure_field_visible(self, *, height: int) -> None:
        visible_count = field_window_size(height)
        if visible_count <= 0:
            self._field_scroll = 0
            return
        fields = self._current_fields()
        if not fields:
            self._field_scroll = 0
            self._selected_field = 0
            return
        max_scroll = max(0, len(fields) - visible_count)
        self._field_scroll = min(self._field_scroll, max_scroll)
        if self._selected_field < self._field_scroll:
            self._field_scroll = self._selected_field
        elif self._selected_field >= self._field_scroll + visible_count:
            self._field_scroll = self._selected_field - visible_count + 1
        self._field_scroll = max(0, min(self._field_scroll, max_scroll))

    def _apply_filter(self, fields: list[FieldSpec]) -> list[FieldSpec]:
        if not self._field_filter:
            return fields
        needle = self._field_filter.lower()
        return [
            field
            for field in fields
            if needle in field.key.lower() or needle in field.label.lower()
        ]

    def _prompt_filter(self, stdscr) -> None:
        value = prompt_search(stdscr, current=self._field_filter, divider_x=PANE_DIVIDER_X)
        if value is None:
            return
        self._field_filter = value or None
        self._selected_field = 0
        self._field_scroll = 0

    def _clear_filter(self) -> None:
        self._field_filter = None
        self._selected_field = 0
        self._field_scroll = 0

    def _exit_and_save(self, *, run_automation: bool) -> None:
        curses.endwin()
        apply_and_save(
            self._ctx,
            profile_id=self._profile_id,
            profiles_path=self._profiles_path,
            answers=self._answers,
            summary_path=self._summary_path,
            markdown_summary_path=self._markdown_summary_path,
            export_answers_path=self._export_answers_path,
            output_format=self._output_format,
            run_automation=run_automation,
        )


def run_editor(
    ctx: CLIContext,
    *,
    profile_id: str,
    profiles_path: Path | None,
    answers: dict[str, str],
    output_format: str,
    summary_path: Path | None,
    markdown_summary_path: Path | None,
    export_answers_path: Path | None,
) -> None:
    EditorController(
        ctx=ctx,
        profile_id=profile_id,
        profiles_path=profiles_path,
        answers=answers,
        output_format=output_format,
        summary_path=summary_path,
        markdown_summary_path=markdown_summary_path,
        export_answers_path=export_answers_path,
    ).run()


__all__ = ["run_editor"]
