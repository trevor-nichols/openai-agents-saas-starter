from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

from starter_cli.core import CLIError


@dataclass(frozen=True, slots=True)
class BackendScriptResult:
    payload: dict[str, Any]
    stdout: str
    stderr: str
    returncode: int


def resolve_backend_env_files(project_root: Path) -> list[Path]:
    env_files: list[Path] = []
    compose = project_root / ".env.compose"
    if compose.is_file():
        env_files.append(compose)

    backend_root = project_root / "apps" / "api-service"
    env_local = backend_root / ".env.local"
    env_default = backend_root / ".env"

    if env_local.is_file():
        env_files.append(env_local)
    elif env_default.is_file():
        env_files.append(env_default)
    else:
        raise CLIError(
            "No apps/api-service/.env.local or apps/api-service/.env found; "
            "run the setup wizard first."
        )

    return env_files


def merge_env_files(paths: Iterable[Path]) -> dict[str, str]:
    merged: dict[str, str] = {}
    for path in paths:
        values = dotenv_values(path)
        for key, value in values.items():
            if key and value is not None:
                merged[key] = value
    return merged


def run_backend_script(
    *,
    project_root: Path,
    script_name: str,
    args: list[str] | None = None,
    env_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    backend_root = project_root / "apps" / "api-service"
    script_path = backend_root / "scripts" / script_name
    if not script_path.is_file():
        raise CLIError(f"Backend script missing: {script_path}")

    env_files = resolve_backend_env_files(project_root)
    env = os.environ.copy()
    env.update(merge_env_files(env_files))
    if env_overrides:
        env.update(env_overrides)

    cmd = ["hatch", "run", "python", f"scripts/{script_name}"]
    if args:
        cmd.extend(args)

    return subprocess.run(
        cmd,
        cwd=backend_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def extract_json_payload(
    stdout: str,
    *,
    required_keys: Iterable[str] | None = None,
) -> dict[str, Any]:
    raw = stdout.strip()
    if not raw:
        raise CLIError("Backend script produced no output.")

    last_error: json.JSONDecodeError | None = None
    for line in reversed(raw.splitlines()):
        candidate = line.strip()
        if not candidate:
            continue
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError as exc:
            last_error = exc
            continue
        if isinstance(payload, dict):
            if required_keys and not all(key in payload for key in required_keys):
                continue
            return payload

    if last_error is not None:
        raise CLIError(f"Backend script returned invalid JSON: {last_error}") from last_error
    raise CLIError("Backend script returned invalid JSON output.")


__all__ = [
    "BackendScriptResult",
    "extract_json_payload",
    "merge_env_files",
    "resolve_backend_env_files",
    "run_backend_script",
]
