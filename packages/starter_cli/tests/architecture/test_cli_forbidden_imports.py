"""Ensure CLI modules never import FastAPI internals directly."""

from __future__ import annotations

from pathlib import Path


def _find_repo_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in current.parents:
        if (candidate / "pnpm-workspace.yaml").exists():
            return candidate
    for candidate in current.parents:
        if (candidate / "apps").is_dir() and (candidate / "packages").is_dir():
            return candidate
    raise RuntimeError(
        "Unable to locate repository root (pnpm-workspace.yaml or apps/packages not found)"
    )


REPO_ROOT = _find_repo_root()
PACKAGE_ROOT = REPO_ROOT / "packages" / "starter_cli" / "src" / "starter_cli"
FORBIDDEN_TOKENS = ("from app.", "import app.")


def test_cli_modules_do_not_import_backend() -> None:
    offenders: list[str] = []
    for path in PACKAGE_ROOT.rglob("*.py"):
        if "tests" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in FORBIDDEN_TOKENS):
            offenders.append(str(path.relative_to(REPO_ROOT)))

    assert not offenders, f"CLI modules must not import app.* directly: {offenders}"
