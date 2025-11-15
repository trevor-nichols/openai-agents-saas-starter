#!/usr/bin/env python3
"""Verify docs/trackers/CLI_ENV_INVENTORY.md matches the runtime settings schema."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from starter_cli.cli.inventory import WIZARD_PROMPTED_ENV_VARS
from starter_shared.config import get_settings

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = REPO_ROOT / "docs/trackers/CLI_ENV_INVENTORY.md"


@dataclass(slots=True)
class EnvEntry:
    env_var: str
    wizard_prompted: bool


def _collect_settings_entries() -> dict[str, EnvEntry]:
    settings = get_settings()
    fields = getattr(settings.__class__, "model_fields", {})
    entries: dict[str, EnvEntry] = {}
    for name, field in fields.items():
        alias = (field.alias or name).upper()
        entries[alias] = EnvEntry(env_var=alias, wizard_prompted=alias in WIZARD_PROMPTED_ENV_VARS)
    return entries


def _parse_inventory_doc(path: Path) -> dict[str, EnvEntry]:
    entries: dict[str, EnvEntry] = {}
    wizard_idx: int | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line.startswith("|"):
            continue
        if "Env Var" in line and "Wizard" in line:
            wizard_idx = _detect_column_index(line, target="wizard")
            continue
        if not line.startswith("| `") or line.startswith("| `Env Var`"):
            continue
        segments = _split_markdown_row(line)
        if len(segments) < 4:
            continue
        env_cell = segments[0].strip()
        if env_cell.startswith("---"):
            continue
        env_var = env_cell.strip("`").strip().upper()
        wizard_cell = _extract_wizard_cell(segments, wizard_idx)
        wizard_prompted = "✅" in wizard_cell
        entries[env_var] = EnvEntry(env_var=env_var, wizard_prompted=wizard_prompted)
    return entries


def _detect_column_index(header_line: str, target: str) -> int | None:
    segments = _split_markdown_row(header_line)
    for idx, cell in enumerate(segments):
        normalized = cell.strip().lower()
        if normalized.startswith(target):
            return idx
    return None


def _extract_wizard_cell(segments: list[str], wizard_idx: int | None) -> str:
    if wizard_idx is not None and 0 <= wizard_idx < len(segments):
        return segments[wizard_idx].strip()
    # Fallback for legacy structure: Wizard column sits second-to-last
    if len(segments) >= 2:
        return segments[-2].strip()
    return ""


def _split_markdown_row(line: str) -> list[str]:
    inner = line.strip().strip("|")
    segments: list[str] = []
    current: list[str] = []
    in_code = False
    i = 0
    while i < len(inner):
        ch = inner[i]
        if ch == "`":
            in_code = not in_code
            current.append(ch)
        elif ch == "|" and not in_code:
            segments.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
        i += 1
    segments.append("".join(current).strip())
    return segments


def _report_diff(expected: Mapping[str, EnvEntry], documented: Mapping[str, EnvEntry]) -> int:
    missing = sorted(expected.keys() - documented.keys())
    extra = sorted(documented.keys() - expected.keys())
    mismatched = sorted(
        alias
        for alias, entry in expected.items()
        if alias in documented and entry.wizard_prompted != documented[alias].wizard_prompted
    )

    exit_code = 0
    if missing:
        print("Missing entries in CLI_ENV_INVENTORY.md:")
        for alias in missing:
            print(f"  - {alias}")
        exit_code = 1
    if extra:
        print("Extraneous entries in CLI_ENV_INVENTORY.md:")
        for alias in extra:
            print(f"  - {alias}")
        exit_code = 1
    if mismatched:
        print("Wizard coverage mismatches:")
        for alias in mismatched:
            expected_flag = expected[alias].wizard_prompted
            doc_flag = documented[alias].wizard_prompted
            print(f"  - {alias}: settings={expected_flag} docs={doc_flag}")
        exit_code = 1

    if exit_code == 0:
        print(
            f"Inventory verified: {len(expected)} env vars documented with correct wizard flags."
        )
    else:
        print(
            "Run `starter_cli config dump-schema --format table` to review expected values. "
            "Update docs/trackers/CLI_ENV_INVENTORY.md accordingly."
        )
    return exit_code


def run() -> int:
    expected = _collect_settings_entries()
    documented = _parse_inventory_doc(DOC_PATH)
    return _report_diff(expected, documented)


if __name__ == "__main__":
    raise SystemExit(run())
