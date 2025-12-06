"""Ensure CLI modules never import FastAPI internals directly."""

from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[3] / "starter_cli"
FORBIDDEN_TOKENS = ("from app.", "import app.")


def test_cli_modules_do_not_import_backend() -> None:
    offenders: list[str] = []
    for path in PACKAGE_ROOT.rglob("*.py"):
        if "tests" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in FORBIDDEN_TOKENS):
            offenders.append(str(path.relative_to(Path(__file__).resolve().parents[3])))

    assert not offenders, f"CLI modules must not import app.* directly: {offenders}"
