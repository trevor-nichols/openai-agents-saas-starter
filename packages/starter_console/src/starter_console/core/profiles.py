"""Profile registry and selection helpers for the setup wizard."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from dotenv import dotenv_values
from starter_contracts.profiles import (
    ProfilePolicy,
    ProfileSchemaError,
    ProfilesDocument,
    detect_profile,
    load_profiles,
    resolve_profiles,
)

from .constants import PROJECT_ROOT
from .exceptions import CLIError

DEFAULT_PROFILE_ID = "demo"
PROFILE_ENV_KEY = "STARTER_PROFILE"
PROFILE_CONFIG_PATH = PROJECT_ROOT / "config" / "starter-console.profile.yaml"
MANIFEST_RELATIVE_PATH = Path("var/reports/profile-manifest.json")
FRONTEND_ENV_RELATIVE_PATH = Path("apps/web-app/.env.local")


class ProfileSource(StrEnum):
    CLI = "cli"
    CONFIG = "config"
    ENV = "env"
    DETECT = "detect"
    DEFAULT = "default"


@dataclass(slots=True)
class ProfileRegistry:
    document: ProfilesDocument
    profiles: dict[str, ProfilePolicy]
    config_path: Path | None
    active_profile: str | None

    @property
    def profile_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self.profiles))


@dataclass(slots=True)
class ProfileSelection:
    profile: ProfilePolicy
    source: ProfileSource
    explicit_profile: str | None
    config_profile: str | None
    env_profile: str | None
    detected_profile: str | None
    config_path: Path | None


@dataclass(slots=True)
class LockedEnvStatus:
    scope: str
    key: str
    default: str
    current: str | None
    overridden: bool


def load_profile_registry(
    *,
    project_root: Path | None = None,
    override_path: Path | None = None,
) -> ProfileRegistry:
    root = project_root or PROJECT_ROOT
    base_doc = _safe_load_profiles()
    config_path = override_path
    if config_path is None:
        config_path = root / "config" / "starter-console.profile.yaml"
    override_doc = None
    if config_path.exists():
        override_doc = _safe_load_profiles(config_path)
    elif override_path is not None:
        raise CLIError(f"Profile config not found at {config_path}")

    merged_doc = _merge_documents(base_doc, override_doc)
    resolved = resolve_profiles(merged_doc)
    profiles = _normalize_profile_map(resolved)
    active_profile = _normalize_profile_id(merged_doc.active_profile)
    return ProfileRegistry(
        document=merged_doc,
        profiles=profiles,
        config_path=config_path if override_doc else None,
        active_profile=active_profile,
    )


def select_profile(
    registry: ProfileRegistry,
    *,
    explicit: str | None = None,
    env: Mapping[str, str] | None = None,
) -> ProfileSelection:
    env_map = dict(env or os.environ)
    explicit_id = _normalize_profile_id(explicit)
    config_id = _normalize_profile_id(registry.active_profile)
    env_id = _normalize_profile_id(env_map.get(PROFILE_ENV_KEY))
    detected = detect_profile(registry.profiles, env_map)
    detected_id = detected.profile_id if detected else None

    if explicit_id:
        profile = _resolve_profile_id(registry, explicit_id, source="CLI")
        return ProfileSelection(
            profile=profile,
            source=ProfileSource.CLI,
            explicit_profile=explicit,
            config_profile=config_id,
            env_profile=env_id,
            detected_profile=detected_id,
            config_path=registry.config_path,
        )
    if config_id:
        profile = _resolve_profile_id(registry, config_id, source="config")
        return ProfileSelection(
            profile=profile,
            source=ProfileSource.CONFIG,
            explicit_profile=None,
            config_profile=config_id,
            env_profile=env_id,
            detected_profile=detected_id,
            config_path=registry.config_path,
        )
    if env_id:
        profile = _resolve_profile_id(registry, env_id, source="env")
        return ProfileSelection(
            profile=profile,
            source=ProfileSource.ENV,
            explicit_profile=None,
            config_profile=None,
            env_profile=env_id,
            detected_profile=detected_id,
            config_path=registry.config_path,
        )
    if detected is not None:
        profile = detected
        return ProfileSelection(
            profile=profile,
            source=ProfileSource.DETECT,
            explicit_profile=None,
            config_profile=None,
            env_profile=env_id,
            detected_profile=detected_id,
            config_path=registry.config_path,
        )

    profile = _resolve_profile_id(registry, DEFAULT_PROFILE_ID, source="default")
    return ProfileSelection(
        profile=profile,
        source=ProfileSource.DEFAULT,
        explicit_profile=None,
        config_profile=None,
        env_profile=env_id,
        detected_profile=detected_id,
        config_path=registry.config_path,
    )


def write_profile_manifest(
    selection: ProfileSelection,
    *,
    project_root: Path | None = None,
    path: Path | None = None,
    env: Mapping[str, str] | None = None,
    frontend_env: Mapping[str, str] | None = None,
) -> Path:
    root = project_root or PROJECT_ROOT
    target = path or (root / MANIFEST_RELATIVE_PATH)
    env_map = dict(env or os.environ)
    locked_statuses = locked_env_statuses(
        selection.profile,
        backend_env=env_map,
        frontend_env=frontend_env,
    )
    payload = _build_manifest_payload(selection, locked_statuses=locked_statuses)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return target


def _resolve_profile_id(
    registry: ProfileRegistry,
    profile_id: str,
    *,
    source: str,
) -> ProfilePolicy:
    normalized = _normalize_profile_id(profile_id)
    if not normalized:
        raise CLIError(f"{source} profile id is empty.")
    profile = registry.profiles.get(normalized)
    if profile is None:
        available = ", ".join(registry.profile_ids)
        raise CLIError(
            f"{source} profile '{profile_id}' not found. Available: {available}"
        )
    return profile


def _merge_documents(
    base: ProfilesDocument,
    override: ProfilesDocument | None,
) -> ProfilesDocument:
    if override is None:
        return base
    if override.version != base.version:
        raise CLIError(
            "Profile schema version mismatch: "
            f"built-in={base.version} override={override.version}"
        )
    profiles = dict(base.profiles)
    profiles.update(override.profiles)
    active_profile = override.active_profile or base.active_profile
    return ProfilesDocument(
        version=base.version,
        profiles=profiles,
        active_profile=active_profile,
    )


def _normalize_profile_map(profiles: Mapping[str, ProfilePolicy]) -> dict[str, ProfilePolicy]:
    normalized: dict[str, ProfilePolicy] = {}
    for profile in profiles.values():
        key = _normalize_profile_id(profile.profile_id)
        if not key:
            raise CLIError("Profile ids must be non-empty.")
        if key in normalized:
            raise CLIError(f"Duplicate profile id detected: {key}")
        normalized[key] = profile
    return normalized


def _normalize_profile_id(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip().lower()
    return text or None


def _safe_load_profiles(path: Path | None = None) -> ProfilesDocument:
    try:
        return load_profiles(path)
    except ProfileSchemaError as exc:
        raise CLIError(str(exc)) from exc


def load_frontend_env(*, project_root: Path | None = None) -> dict[str, str]:
    root = project_root or PROJECT_ROOT
    path = root / FRONTEND_ENV_RELATIVE_PATH
    if not path.exists():
        return {}
    values = dotenv_values(path)
    return {key: value for key, value in values.items() if value is not None}


def locked_env_statuses(
    policy: ProfilePolicy,
    *,
    backend_env: Mapping[str, str],
    frontend_env: Mapping[str, str] | None = None,
) -> tuple[LockedEnvStatus, ...]:
    statuses: list[LockedEnvStatus] = []
    statuses.extend(
        _locked_scope_statuses(
            scope="backend",
            locked_keys=policy.env.backend.locked,
            defaults=policy.env.backend.defaults,
            env=backend_env,
        )
    )
    if policy.env.frontend.locked:
        statuses.extend(
            _locked_scope_statuses(
                scope="frontend",
                locked_keys=policy.env.frontend.locked,
                defaults=policy.env.frontend.defaults,
                env=frontend_env or {},
            )
        )
    return tuple(statuses)


def _locked_scope_statuses(
    *,
    scope: str,
    locked_keys: tuple[str, ...],
    defaults: Mapping[str, str],
    env: Mapping[str, str],
) -> list[LockedEnvStatus]:
    statuses: list[LockedEnvStatus] = []
    for key in locked_keys:
        default = defaults.get(key)
        if default is None:
            raise CLIError(f"Profile locks {key} but no default is configured.")
        current = env.get(key)
        overridden = bool(current) and current != default
        statuses.append(
            LockedEnvStatus(
                scope=scope,
                key=key,
                default=default,
                current=current,
                overridden=overridden,
            )
        )
    return statuses


def _build_manifest_payload(
    selection: ProfileSelection,
    *,
    locked_statuses: tuple[LockedEnvStatus, ...],
) -> dict[str, object]:
    profile = selection.profile
    locked_overrides = [
        {
            "scope": status.scope,
            "key": status.key,
            "expected": status.default,
            "actual": status.current,
        }
        for status in locked_statuses
        if status.overridden
    ]
    return {
        "version": "v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "profile": {
            "id": profile.profile_id,
            "label": profile.label,
            "description": profile.description,
            "source": selection.source.value,
        },
        "selection": {
            "explicit": selection.explicit_profile,
            "config_active": selection.config_profile,
            "env": selection.env_profile,
            "detected": selection.detected_profile,
            "config_path": str(selection.config_path) if selection.config_path else None,
        },
        "locked": {
            "total": len(locked_statuses),
            "overrides": locked_overrides,
        },
    }


__all__ = [
    "DEFAULT_PROFILE_ID",
    "FRONTEND_ENV_RELATIVE_PATH",
    "MANIFEST_RELATIVE_PATH",
    "PROFILE_CONFIG_PATH",
    "PROFILE_ENV_KEY",
    "ProfileRegistry",
    "ProfileSelection",
    "ProfileSource",
    "LockedEnvStatus",
    "load_profile_registry",
    "load_frontend_env",
    "locked_env_statuses",
    "select_profile",
    "write_profile_manifest",
]
