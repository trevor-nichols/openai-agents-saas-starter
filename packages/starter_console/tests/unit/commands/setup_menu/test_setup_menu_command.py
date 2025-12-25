from __future__ import annotations

from starter_console.app import build_parser


def test_setup_menu_registered() -> None:
    parser = build_parser()
    args = parser.parse_args(["setup", "menu", "--no-tui"])
    assert getattr(args, "setup_command", None) == "menu"
    assert hasattr(args, "handler")

