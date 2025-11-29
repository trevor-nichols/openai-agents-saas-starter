"""Ensure home workflows stay decoupled from backend/frontend code."""

from __future__ import annotations

from pathlib import Path

HOME_ROOT = Path(__file__).resolve().parents[3] / "starter_cli" / "workflows" / "home"
BANNED_TOKENS = (
    "from app.",
    "import app.",
    "from api_service",
    "import api_service",
    "from web_app",
    "import web_app",
)


def test_home_workflows_do_not_import_backend_or_frontend() -> None:
    offenders: list[str] = []
    for path in HOME_ROOT.rglob("*.py"):
        if "tests" in path.parts or "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in BANNED_TOKENS):
            offenders.append(str(path.relative_to(Path(__file__).resolve().parents[3])))

    assert not offenders, f"Home workflows must not import backend/frontend code: {offenders}"
