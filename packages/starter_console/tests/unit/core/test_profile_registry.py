from __future__ import annotations

import json
from pathlib import Path

from starter_console.core.profiles import (
    ProfileSource,
    load_profile_registry,
    select_profile,
    write_profile_manifest,
)


def test_select_profile_prefers_explicit(tmp_path: Path) -> None:
    registry = load_profile_registry(project_root=tmp_path)
    selection = select_profile(
        registry,
        explicit="staging",
        env={"ENVIRONMENT": "development"},
    )
    assert selection.profile.profile_id == "staging"
    assert selection.source is ProfileSource.CLI


def test_select_profile_uses_config_active(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "starter-console.profile.yaml"
    config_path.write_text(
        """
version: 1
active_profile: custom
profiles:
  custom:
    extends: demo
    label: Custom
""".lstrip(),
        encoding="utf-8",
    )
    registry = load_profile_registry(project_root=tmp_path)
    selection = select_profile(registry, explicit=None, env={})
    assert selection.profile.profile_id == "custom"
    assert selection.source is ProfileSource.CONFIG


def test_select_profile_uses_env_override(tmp_path: Path) -> None:
    registry = load_profile_registry(project_root=tmp_path)
    selection = select_profile(registry, explicit=None, env={"STARTER_PROFILE": "production"})
    assert selection.profile.profile_id == "production"
    assert selection.source is ProfileSource.ENV


def test_manifest_records_locked_overrides(tmp_path: Path) -> None:
    registry = load_profile_registry(project_root=tmp_path)
    selection = select_profile(registry, explicit="staging", env={})
    manifest_path = write_profile_manifest(
        selection,
        project_root=tmp_path,
        env={"AUTH_KEY_STORAGE_BACKEND": "file"},
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    locked = payload["locked"]["overrides"]
    assert locked == [
        {
            "scope": "backend",
            "key": "AUTH_KEY_STORAGE_BACKEND",
            "expected": "secret-manager",
            "actual": "file",
        }
    ]


def test_manifest_records_frontend_locked_overrides(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "starter-console.profile.yaml").write_text(
        """
version: 1
active_profile: custom
profiles:
  custom:
    extends: demo
    env:
      defaults:
        frontend:
          NEXT_PUBLIC_LOG_SINK: console
      locked:
        frontend: [NEXT_PUBLIC_LOG_SINK]
""".lstrip(),
        encoding="utf-8",
    )
    registry = load_profile_registry(project_root=tmp_path)
    selection = select_profile(registry, explicit="custom")
    manifest_path = write_profile_manifest(
        selection,
        project_root=tmp_path,
        env={},
        frontend_env={"NEXT_PUBLIC_LOG_SINK": "beacon"},
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    locked = payload["locked"]["overrides"]
    assert locked == [
        {
            "scope": "frontend",
            "key": "NEXT_PUBLIC_LOG_SINK",
            "expected": "console",
            "actual": "beacon",
        }
    ]
