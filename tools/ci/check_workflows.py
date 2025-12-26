#!/usr/bin/env python3
"""Lightweight validation for GitHub workflow YAML files."""
from __future__ import annotations

from pathlib import Path

import yaml


def _iter_workflow_files(root: Path) -> list[Path]:
    workflows_dir = root / ".github" / "workflows"
    if not workflows_dir.exists():
        return []
    return sorted(path for path in workflows_dir.rglob("*.yml")) + sorted(
        path for path in workflows_dir.rglob("*.yaml")
    )


def run() -> int:
    root = Path(__file__).resolve().parents[2]
    files = _iter_workflow_files(root)
    if not files:
        print("No workflow files found.")
        return 0
    errors: list[str] = []
    for path in files:
        try:
            with path.open("r", encoding="utf-8") as handle:
                yaml.safe_load(handle)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{path}: {exc}")
    if errors:
        print("Workflow YAML validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1
    print(f"Workflow YAML validated: {len(files)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
