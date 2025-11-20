"""Boundary tests for the ``starter_contracts`` package.

These ensure contracts stay import-safe and are only consumed from approved
surfaces (backend, CLI, scripts).
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ALLOWED_TOP_LEVEL = {"api-service", "starter_cli", "starter_contracts", "scripts"}


def test_imports_do_not_pull_app_or_cli_modules(monkeypatch) -> None:
    # Ensure local app package is not shadowed by any site-packages "app".
    monkeypatch.syspath_prepend(str(ROOT / "api-service"))

    before = set(sys.modules)

    # Import all public modules; they should not eagerly import app/CLI modules.
    importlib.reload(importlib.import_module("starter_contracts.config"))
    importlib.reload(importlib.import_module("starter_contracts.keys"))
    importlib.reload(importlib.import_module("starter_contracts.provider_validation"))
    importlib.reload(importlib.import_module("starter_contracts.vault_kv"))
    importlib.reload(importlib.import_module("starter_contracts.secrets.models"))

    after = set(sys.modules)
    new_modules = after - before

    leaked_app = {name for name in new_modules if name.startswith("app.")}
    leaked_cli = {name for name in new_modules if name.startswith("starter_cli")}

    assert not leaked_app, f"Contracts import pulled app modules: {sorted(leaked_app)}"
    assert not leaked_cli, f"Contracts import pulled CLI modules: {sorted(leaked_cli)}"


def test_only_approved_packages_import_contracts() -> None:
    offenders: list[str] = []
    for path in ROOT.rglob("*.py"):
        rel = path.relative_to(ROOT)
        top = rel.parts[0]
        if top.startswith(".venv"):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if "starter_contracts" not in content:
            continue
        if top not in ALLOWED_TOP_LEVEL:
            offenders.append(str(rel))

    assert not offenders, f"Unexpected imports of starter_contracts: {offenders}"
