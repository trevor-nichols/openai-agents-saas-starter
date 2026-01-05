from __future__ import annotations

import curses

from .models import FieldSpec


def prompt_input(stdscr, field: FieldSpec, *, divider_x: int | None = None) -> str | None:
    height, width = stdscr.getmaxyx()
    _clear_divider(stdscr, divider_x, height=height)
    prompt = f"{field.label} [{field.key}]"
    stdscr.addstr(height - 4, 2, " " * (width - 4))
    stdscr.addstr(height - 4, 2, prompt[: width - 4], curses.A_BOLD)
    stdscr.addstr(height - 3, 2, "> ")
    stdscr.refresh()
    curses.curs_set(1)
    if field.kind == "secret":
        value = _read_secret(stdscr, height - 3, 4, width - 6)
    else:
        curses.echo()
        raw = stdscr.getstr(height - 3, 4, width - 6)
        curses.noecho()
        value = raw.decode("utf-8") if raw else ""
    curses.curs_set(0)
    return value.strip()


def prompt_search(
    stdscr,
    *,
    current: str | None = None,
    divider_x: int | None = None,
) -> str | None:
    height, width = stdscr.getmaxyx()
    _clear_divider(stdscr, divider_x, height=height)
    prompt = "Search fields (env var or label)"
    stdscr.addstr(height - 4, 2, " " * (width - 4))
    stdscr.addstr(height - 4, 2, prompt[: width - 4], curses.A_BOLD)
    stdscr.addstr(height - 3, 2, "> ")
    stdscr.refresh()
    curses.curs_set(1)
    value = _read_line(stdscr, height - 3, 4, width - 6, initial=current or "")
    curses.curs_set(0)
    return value.strip() if value is not None else None


def select_choice(stdscr, field: FieldSpec) -> str | None:
    choices = list(field.choices)
    if not choices:
        return field.value or ""
    index = 0
    if field.value in choices:
        index = choices.index(field.value)
    height, width = stdscr.getmaxyx()
    win_height = min(len(choices) + 4, height - 4)
    win_width = min(max(len(choice) for choice in choices) + 6, width - 10)
    win = curses.newwin(
        win_height,
        win_width,
        max(2, (height - win_height) // 2),
        max(2, (width - win_width) // 2),
    )
    win.keypad(True)
    while True:
        win.clear()
        win.box()
        title = f"{field.label} [{field.key}]"
        win.addstr(1, 2, title[: win_width - 4])
        for idx, choice in enumerate(choices):
            line = f"{idx + 1}) {choice}"
            if choice in field.choice_help:
                detail = field.choice_help[choice]
                line = f"{line} - {detail}"
            attr = curses.A_REVERSE if idx == index else curses.A_NORMAL
            win.addstr(2 + idx, 2, line[: win_width - 4], attr)
        win.refresh()
        key = win.getch()
        if key in {curses.KEY_UP, ord("k")}:
            index = max(0, index - 1)
        elif key in {curses.KEY_DOWN, ord("j")}:
            index = min(len(choices) - 1, index + 1)
        elif key in {10, 13, curses.KEY_ENTER}:
            return choices[index]
        elif key in {27, ord("q")}:
            return None


def _read_secret(stdscr, y: int, x: int, max_width: int) -> str:
    value_chars: list[str] = []
    while True:
        ch = stdscr.getch(y, x + len(value_chars))
        if ch in {10, 13}:
            break
        if ch in {curses.KEY_BACKSPACE, 127, 8}:
            if value_chars:
                value_chars.pop()
                stdscr.addstr(y, x, "*" * len(value_chars) + " ")
            continue
        if 0 <= ch < 256 and len(value_chars) < max_width:
            value_chars.append(chr(ch))
            stdscr.addstr(y, x, "*" * len(value_chars))
    return "".join(value_chars)


def _read_line(stdscr, y: int, x: int, max_width: int, *, initial: str = "") -> str | None:
    value_chars = list(initial[:max_width])
    if value_chars:
        stdscr.addstr(y, x, "".join(value_chars))
        stdscr.refresh()
    while True:
        ch = stdscr.getch(y, x + len(value_chars))
        if ch in {10, 13}:
            break
        if ch in {27}:  # ESC
            return None
        if ch in {curses.KEY_BACKSPACE, 127, 8}:
            if value_chars:
                value_chars.pop()
                stdscr.addstr(y, x, "".join(value_chars) + " ")
            continue
        if 0 <= ch < 256 and len(value_chars) < max_width:
            value_chars.append(chr(ch))
            stdscr.addstr(y, x, "".join(value_chars))
    return "".join(value_chars)


def _clear_divider(stdscr, divider_x: int | None, *, height: int) -> None:
    for row in (height - 4, height - 3):
        stdscr.move(row, 0)
        stdscr.clrtoeol()


__all__ = ["prompt_input", "prompt_search", "select_choice"]
