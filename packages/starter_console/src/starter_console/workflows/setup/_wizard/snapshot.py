from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from starter_console.core.inventory import FRONTEND_ENV_VARS, WIZARD_PROMPTED_ENV_VARS

from .context import WizardContext

_SNAPSHOT_VERSION = 1


def _hash_value(value: str | None) -> str | None:
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _capture_values(
    keys: Iterable[str],
    value_lookup,
) -> dict[str, dict[str, str | bool | None]]:
    result: dict[str, dict[str, str | bool | None]] = {}
    for key in sorted(keys):
        value = value_lookup(key)
        is_set = bool(value)
        result[key] = {
            "set": is_set,
            "hash": _hash_value(value) if is_set else None,
        }
    return result


def build_snapshot(context: WizardContext) -> dict[str, Any]:
    metadata = {
        "profile": context.profile,
        "hosting_preset": context.hosting_preset,
        "cloud_provider": context.cloud_provider,
    }
    backend_values = _capture_values(WIZARD_PROMPTED_ENV_VARS, context.current)
    frontend_values = _capture_values(
        FRONTEND_ENV_VARS,
        lambda key: context.frontend_env.get(key) if context.frontend_env else None,
    )
    return {
        "version": _SNAPSHOT_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "metadata": metadata,
        "backend_env": backend_values,
        "frontend_env": frontend_values,
    }


def load_snapshot(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _diff_section(
    previous: dict[str, Any] | None,
    current: dict[str, Any],
    *,
    section_key: str,
) -> dict[str, list[str]]:
    prev_section = previous.get(section_key, {}) if previous else {}
    curr_section = current.get(section_key, {})
    added: list[str] = []
    removed: list[str] = []
    changed: list[str] = []

    keys = set(prev_section) | set(curr_section)
    for key in sorted(keys):
        prev_entry = prev_section.get(key, {})
        curr_entry = curr_section.get(key, {})
        prev_set = bool(prev_entry.get("set"))
        curr_set = bool(curr_entry.get("set"))
        prev_hash = prev_entry.get("hash")
        curr_hash = curr_entry.get("hash")

        if not prev_set and curr_set:
            added.append(key)
            continue
        if prev_set and not curr_set:
            removed.append(key)
            continue
        if prev_set and curr_set and prev_hash != curr_hash:
            changed.append(key)

    return {"added": added, "removed": removed, "changed": changed}


def build_diff(previous: dict[str, Any] | None, current: dict[str, Any]) -> dict[str, Any]:
    metadata_changes: dict[str, dict[str, Any]] = {}
    prev_meta = previous.get("metadata", {}) if previous else {}
    curr_meta = current.get("metadata", {})
    for key in sorted(set(prev_meta) | set(curr_meta)):
        prev_val = prev_meta.get(key)
        curr_val = curr_meta.get(key)
        if prev_val != curr_val:
            metadata_changes[key] = {"from": prev_val, "to": curr_val}

    return {
        "has_previous": previous is not None,
        "generated_at": current.get("generated_at"),
        "metadata_changes": metadata_changes,
        "backend_env": _diff_section(previous, current, section_key="backend_env"),
        "frontend_env": _diff_section(previous, current, section_key="frontend_env"),
    }


def render_diff_markdown(diff: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Setup Diff")
    lines.append("")
    lines.append(f"Generated at: {diff.get('generated_at')}")
    lines.append("")

    if not diff.get("has_previous"):
        lines.append("No prior snapshot found. This run establishes the baseline.")
        return "\n".join(lines).strip() + "\n"

    metadata_changes = diff.get("metadata_changes", {})
    if metadata_changes:
        lines.append("## Metadata Changes")
        lines.append("")
        for key, change in metadata_changes.items():
            lines.append(f"- `{key}`: `{change.get('from')}` → `{change.get('to')}`")
        lines.append("")

    def _render_section(title: str, section: dict[str, list[str]]) -> None:
        added = section.get("added", [])
        removed = section.get("removed", [])
        changed = section.get("changed", [])
        lines.append(f"## {title}")
        lines.append("")
        if not (added or removed or changed):
            lines.append("No changes detected.")
            lines.append("")
            return
        if added:
            lines.append("- Added: " + ", ".join(f"`{key}`" for key in added))
        if removed:
            lines.append("- Removed: " + ", ".join(f"`{key}`" for key in removed))
        if changed:
            lines.append("- Changed: " + ", ".join(f"`{key}`" for key in changed))
        lines.append("")

    _render_section("Backend Env", diff.get("backend_env", {}))
    _render_section("Frontend Env", diff.get("frontend_env", {}))

    return "\n".join(lines).strip() + "\n"


def write_snapshot_and_diff(context: WizardContext) -> tuple[Path, Path]:
    reports_dir = context.cli_ctx.project_root / "var/reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = reports_dir / "setup-snapshot.json"
    diff_path = reports_dir / "setup-diff.md"

    previous = load_snapshot(snapshot_path)
    current = build_snapshot(context)
    snapshot_path.write_text(json.dumps(current, indent=2), encoding="utf-8")

    diff = build_diff(previous, current)
    diff_path.write_text(render_diff_markdown(diff), encoding="utf-8")

    return snapshot_path, diff_path


__all__ = [
    "build_snapshot",
    "build_diff",
    "load_snapshot",
    "render_diff_markdown",
    "write_snapshot_and_diff",
]
