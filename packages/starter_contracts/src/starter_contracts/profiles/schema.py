"""Profile policy contract for the Starter Console setup wizard."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import Any

import yaml


class ProfileSchemaError(RuntimeError):
    """Raised when a profile document is invalid."""


_AUTOMATION_PHASES = frozenset(
    {
        "infra",
        "secrets",
        "stripe",
        "sso",
        "migrations",
        "redis",
        "geoip",
        "dev_user",
        "demo_token",
    }
)
_HOSTING_PRESETS = frozenset({"local_docker", "cloud_managed", "enterprise_custom"})
_CLOUD_PROVIDERS = frozenset({"aws", "azure", "gcp", "other"})
_GEOIP_REQUIRED_MODES = frozenset({"disabled", "warn", "error"})

_RULES = {
    "require_vault",
    "require_database_url",
    "redis_tls_required",
    "stripe_webhook_auto_allowed",
    "dev_user_allowed",
    "geoip_required_mode",
    "frontend_log_ingest_requires_confirmation",
    "migrations_prompt_default",
}


@dataclass(slots=True)
class EnvMatchRule:
    key: str
    equals: str | None = None
    contains: str | None = None
    present: bool = False

    def matches(self, env: Mapping[str, Any]) -> bool:
        value = env.get(self.key)
        raw = "" if value is None else str(value)
        if self.present and not raw:
            return False
        if self.equals is not None and raw.lower() != self.equals.lower():
            return False
        if self.contains is not None and self.contains.lower() not in raw.lower():
            return False
        return True


@dataclass(slots=True)
class DetectRule:
    env: EnvMatchRule | None = None

    def matches(self, env: Mapping[str, Any]) -> bool:
        if self.env is None:
            return False
        return self.env.matches(env)


@dataclass(slots=True)
class DetectPolicy:
    priority: int = 100
    any: tuple[DetectRule, ...] = ()

    def matches(self, env: Mapping[str, Any]) -> bool:
        if not self.any:
            return False
        return any(rule.matches(env) for rule in self.any)


@dataclass(slots=True)
class AutomationOverrides:
    allow: tuple[str, ...] | None = None
    defaults: dict[str, bool] | None = None


@dataclass(slots=True)
class AutomationPolicy:
    allow: tuple[str, ...] | None = None
    defaults: dict[str, bool] = field(default_factory=dict)


@dataclass(slots=True)
class WizardOverrides:
    hosting_preset_default: str | None = None
    cloud_provider_default: str | None = None
    show_advanced_default: bool | None = None
    automation: AutomationOverrides | None = None


@dataclass(slots=True)
class WizardPolicy:
    hosting_preset_default: str | None = None
    cloud_provider_default: str | None = None
    show_advanced_default: bool | None = None
    automation: AutomationPolicy = field(default_factory=AutomationPolicy)


@dataclass(slots=True)
class EnvScopeOverrides:
    defaults: dict[str, str] | None = None
    required: tuple[str, ...] | None = None
    optional: tuple[str, ...] | None = None
    hidden: tuple[str, ...] | None = None
    locked: tuple[str, ...] | None = None


@dataclass(slots=True)
class EnvScopePolicy:
    defaults: dict[str, str] = field(default_factory=dict)
    required: tuple[str, ...] = ()
    optional: tuple[str, ...] = ()
    hidden: tuple[str, ...] = ()
    locked: tuple[str, ...] = ()


@dataclass(slots=True)
class EnvPolicyOverrides:
    backend: EnvScopeOverrides = field(default_factory=EnvScopeOverrides)
    frontend: EnvScopeOverrides = field(default_factory=EnvScopeOverrides)


@dataclass(slots=True)
class EnvPolicy:
    backend: EnvScopePolicy = field(default_factory=EnvScopePolicy)
    frontend: EnvScopePolicy = field(default_factory=EnvScopePolicy)


@dataclass(slots=True)
class ProfileRules:
    require_vault: bool | None = None
    require_database_url: bool | None = None
    redis_tls_required: bool | None = None
    stripe_webhook_auto_allowed: bool | None = None
    dev_user_allowed: bool | None = None
    geoip_required_mode: str | None = None
    frontend_log_ingest_requires_confirmation: bool | None = None
    migrations_prompt_default: bool | None = None


@dataclass(slots=True)
class ProfileDefinition:
    profile_id: str
    label: str | None = None
    description: str | None = None
    extends: str | None = None
    detect: DetectPolicy | None = None
    wizard: WizardOverrides = field(default_factory=WizardOverrides)
    env: EnvPolicyOverrides = field(default_factory=EnvPolicyOverrides)
    choices: dict[str, tuple[str, ...]] = field(default_factory=dict)
    rules: ProfileRules = field(default_factory=ProfileRules)


@dataclass(slots=True)
class ProfilePolicy:
    profile_id: str
    label: str
    description: str
    detect: DetectPolicy | None
    wizard: WizardPolicy
    env: EnvPolicy
    choices: dict[str, tuple[str, ...]]
    rules: ProfileRules


@dataclass(slots=True)
class ProfilesDocument:
    version: int
    profiles: dict[str, ProfileDefinition]
    active_profile: str | None = None


def load_profiles(path: Path | None = None) -> ProfilesDocument:
    if path is None:
        target = resources.files("starter_contracts.profiles") / "profiles.yaml"
        raw = yaml.safe_load(target.read_text(encoding="utf-8"))
    else:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return parse_profiles(raw)


def parse_profiles(raw: Any) -> ProfilesDocument:
    if not isinstance(raw, dict):
        raise ProfileSchemaError("Profile document must be a mapping.")
    version = int(raw.get("version") or 1)
    raw_profiles = raw.get("profiles")
    if not isinstance(raw_profiles, dict) or not raw_profiles:
        raise ProfileSchemaError("Profile document must define a non-empty 'profiles' map.")
    profiles: dict[str, ProfileDefinition] = {}
    for profile_id, payload in raw_profiles.items():
        if not isinstance(payload, dict):
            raise ProfileSchemaError(f"Profile '{profile_id}' must be a mapping.")
        definition = _parse_profile(profile_id, payload)
        profiles[definition.profile_id] = definition
    active_profile = raw.get("active_profile")
    if active_profile is not None:
        active_profile = str(active_profile).strip()
    return ProfilesDocument(version=version, profiles=profiles, active_profile=active_profile)


def resolve_profiles(document: ProfilesDocument) -> dict[str, ProfilePolicy]:
    resolved: dict[str, ProfilePolicy] = {}
    for profile_id in document.profiles:
        resolved[profile_id] = resolve_profile(document, profile_id)
    return resolved


def resolve_profile(document: ProfilesDocument, profile_id: str) -> ProfilePolicy:
    if profile_id not in document.profiles:
        raise ProfileSchemaError(f"Unknown profile '{profile_id}'.")
    return _resolve_profile(document, profile_id, seen=set())


def detect_profile(
    profiles: Mapping[str, ProfilePolicy],
    env: Mapping[str, Any],
) -> ProfilePolicy | None:
    candidates: list[ProfilePolicy] = []
    for profile in profiles.values():
        if profile.detect and profile.detect.matches(env):
            candidates.append(profile)
    if not candidates:
        return None
    candidates.sort(key=lambda item: item.detect.priority if item.detect else 100)
    return candidates[0]


def _resolve_profile(
    document: ProfilesDocument,
    profile_id: str,
    *,
    seen: set[str],
) -> ProfilePolicy:
    if profile_id in seen:
        cycle = " -> ".join([*list(seen), profile_id])
        raise ProfileSchemaError(f"Profile inheritance cycle detected: {cycle}")
    seen.add(profile_id)
    definition = document.profiles[profile_id]
    if not definition.extends:
        return _to_policy(definition)
    parent_id = definition.extends
    if parent_id not in document.profiles:
        raise ProfileSchemaError(
            f"Profile '{profile_id}' extends unknown profile '{parent_id}'."
        )
    parent = _resolve_profile(document, parent_id, seen=seen)
    return _merge_policy(parent, definition)


def _merge_policy(parent: ProfilePolicy, child: ProfileDefinition) -> ProfilePolicy:
    label = child.label or parent.label
    description = child.description or parent.description
    detect = child.detect or parent.detect
    wizard = _merge_wizard(parent.wizard, child.wizard)
    env = _merge_env(parent.env, child.env)
    choices = dict(parent.choices)
    if child.choices:
        for key, values in child.choices.items():
            choices[key] = values
    rules = _merge_rules(parent.rules, child.rules)
    return ProfilePolicy(
        profile_id=child.profile_id,
        label=label,
        description=description,
        detect=detect,
        wizard=wizard,
        env=env,
        choices=choices,
        rules=rules,
    )


def _merge_wizard(parent: WizardPolicy, child: WizardOverrides) -> WizardPolicy:
    automation = _merge_automation(parent.automation, child.automation)
    return WizardPolicy(
        hosting_preset_default=(child.hosting_preset_default or parent.hosting_preset_default),
        cloud_provider_default=(child.cloud_provider_default or parent.cloud_provider_default),
        show_advanced_default=
        child.show_advanced_default
        if child.show_advanced_default is not None
        else parent.show_advanced_default,
        automation=automation,
    )


def _merge_automation(
    parent: AutomationPolicy,
    overrides: AutomationOverrides | None,
) -> AutomationPolicy:
    if overrides is None:
        return parent
    allow = parent.allow
    if overrides.allow is not None:
        allow = overrides.allow
    defaults = dict(parent.defaults)
    if overrides.defaults:
        defaults.update(overrides.defaults)
    return AutomationPolicy(allow=allow, defaults=defaults)


def _merge_env(parent: EnvPolicy, overrides: EnvPolicyOverrides) -> EnvPolicy:
    return EnvPolicy(
        backend=_merge_env_scope(parent.backend, overrides.backend),
        frontend=_merge_env_scope(parent.frontend, overrides.frontend),
    )


def _merge_env_scope(parent: EnvScopePolicy, overrides: EnvScopeOverrides) -> EnvScopePolicy:
    defaults = dict(parent.defaults)
    if overrides.defaults is not None:
        defaults.update(overrides.defaults)
    required = overrides.required if overrides.required is not None else parent.required
    optional = overrides.optional if overrides.optional is not None else parent.optional
    hidden = overrides.hidden if overrides.hidden is not None else parent.hidden
    locked = overrides.locked if overrides.locked is not None else parent.locked
    return EnvScopePolicy(
        defaults=defaults,
        required=required,
        optional=optional,
        hidden=hidden,
        locked=locked,
    )


def _merge_rules(parent: ProfileRules, child: ProfileRules) -> ProfileRules:
    return ProfileRules(
        require_vault=_pick(child.require_vault, parent.require_vault),
        require_database_url=_pick(child.require_database_url, parent.require_database_url),
        redis_tls_required=_pick(child.redis_tls_required, parent.redis_tls_required),
        stripe_webhook_auto_allowed=_pick(
            child.stripe_webhook_auto_allowed, parent.stripe_webhook_auto_allowed
        ),
        dev_user_allowed=_pick(child.dev_user_allowed, parent.dev_user_allowed),
        geoip_required_mode=_pick(child.geoip_required_mode, parent.geoip_required_mode),
        frontend_log_ingest_requires_confirmation=_pick(
            child.frontend_log_ingest_requires_confirmation,
            parent.frontend_log_ingest_requires_confirmation,
        ),
        migrations_prompt_default=_pick(
            child.migrations_prompt_default,
            parent.migrations_prompt_default,
        ),
    )


def _pick(value, fallback):
    return fallback if value is None else value


def _to_policy(definition: ProfileDefinition) -> ProfilePolicy:
    label = definition.label or definition.profile_id
    description = definition.description or ""
    wizard = _merge_wizard(WizardPolicy(), definition.wizard)
    env = _merge_env(EnvPolicy(), definition.env)
    return ProfilePolicy(
        profile_id=definition.profile_id,
        label=label,
        description=description,
        detect=definition.detect,
        wizard=wizard,
        env=env,
        choices=dict(definition.choices),
        rules=definition.rules,
    )


def _parse_profile(profile_id: Any, payload: Mapping[str, Any]) -> ProfileDefinition:
    profile_key = str(profile_id).strip()
    label = _coerce_optional_str(payload.get("label"))
    description = _coerce_optional_str(payload.get("description"))
    extends = _coerce_optional_str(payload.get("extends"))
    detect = _parse_detect(payload.get("detect"))
    wizard = _parse_wizard(payload.get("wizard"))
    env = _parse_env(payload.get("env"))
    choices = _parse_choices(payload.get("choices"))
    rules = _parse_rules(payload.get("rules"))
    return ProfileDefinition(
        profile_id=profile_key,
        label=label,
        description=description,
        extends=extends,
        detect=detect,
        wizard=wizard,
        env=env,
        choices=choices,
        rules=rules,
    )


def _parse_detect(raw: Any) -> DetectPolicy | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ProfileSchemaError("detect must be a mapping.")
    priority_raw = raw.get("priority")
    priority = int(priority_raw) if priority_raw is not None else 100
    any_rules = raw.get("any") or []
    if not isinstance(any_rules, list):
        raise ProfileSchemaError("detect.any must be a list.")
    rules: list[DetectRule] = []
    for entry in any_rules:
        if not isinstance(entry, dict):
            raise ProfileSchemaError("detect.any entries must be mappings.")
        env_rule = entry.get("env")
        if env_rule is None:
            rules.append(DetectRule())
            continue
        if not isinstance(env_rule, dict):
            raise ProfileSchemaError("detect.any.env must be a mapping.")
        key = env_rule.get("key")
        if not key:
            raise ProfileSchemaError("detect.any.env.key is required.")
        equals = _coerce_optional_str(env_rule.get("equals"))
        contains = _coerce_optional_str(env_rule.get("contains"))
        present = bool(env_rule.get("present", False))
        if not (equals or contains or present):
            raise ProfileSchemaError(
                "detect.any.env must set equals, contains, or present."
            )
        rules.append(
            DetectRule(
                env=EnvMatchRule(
                    key=_normalize_env_key(key),
                    equals=equals,
                    contains=contains,
                    present=present,
                )
            )
        )
    return DetectPolicy(priority=priority, any=tuple(rules))


def _parse_wizard(raw: Any) -> WizardOverrides:
    if raw is None:
        return WizardOverrides()
    if not isinstance(raw, dict):
        raise ProfileSchemaError("wizard must be a mapping.")
    hosting_default = _coerce_optional_str(raw.get("hosting_preset_default"))
    if hosting_default and hosting_default not in _HOSTING_PRESETS:
        raise ProfileSchemaError(
            f"Invalid hosting_preset_default '{hosting_default}'."
        )
    cloud_default = _coerce_optional_str(raw.get("cloud_provider_default"))
    if cloud_default and cloud_default not in _CLOUD_PROVIDERS:
        raise ProfileSchemaError(f"Invalid cloud_provider_default '{cloud_default}'.")
    show_advanced = raw.get("show_advanced_default")
    if show_advanced is not None and not isinstance(show_advanced, bool):
        raise ProfileSchemaError("show_advanced_default must be a boolean.")
    automation = _parse_automation(raw.get("automation"))
    return WizardOverrides(
        hosting_preset_default=hosting_default,
        cloud_provider_default=cloud_default,
        show_advanced_default=show_advanced,
        automation=automation,
    )


def _parse_automation(raw: Any) -> AutomationOverrides | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ProfileSchemaError("wizard.automation must be a mapping.")
    allow_raw = raw.get("allow")
    allow = None
    if allow_raw is not None:
        allow_list = _coerce_list(allow_raw)
        for item in allow_list:
            if item not in _AUTOMATION_PHASES:
                raise ProfileSchemaError(f"Unknown automation phase '{item}'.")
        allow = tuple(allow_list)
    defaults_raw = raw.get("defaults")
    defaults: dict[str, bool] | None = None
    if defaults_raw is not None:
        if not isinstance(defaults_raw, dict):
            raise ProfileSchemaError("wizard.automation.defaults must be a mapping.")
        defaults = {}
        for key, value in defaults_raw.items():
            phase = str(key)
            if phase not in _AUTOMATION_PHASES:
                raise ProfileSchemaError(f"Unknown automation phase '{phase}'.")
            if not isinstance(value, bool):
                raise ProfileSchemaError(f"automation default for '{phase}' must be boolean.")
            defaults[phase] = value
    return AutomationOverrides(allow=allow, defaults=defaults)


def _parse_env(raw: Any) -> EnvPolicyOverrides:
    if raw is None:
        return EnvPolicyOverrides()
    if not isinstance(raw, dict):
        raise ProfileSchemaError("env must be a mapping.")
    defaults = raw.get("defaults", {})
    required = raw.get("required", {})
    optional = raw.get("optional", {})
    hidden = raw.get("hidden", {})
    locked = raw.get("locked", {})
    backend = _parse_env_scope(
        defaults.get("backend"),
        required.get("backend"),
        optional.get("backend"),
        hidden.get("backend"),
        locked.get("backend"),
    )
    frontend = _parse_env_scope(
        defaults.get("frontend"),
        required.get("frontend"),
        optional.get("frontend"),
        hidden.get("frontend"),
        locked.get("frontend"),
    )
    return EnvPolicyOverrides(backend=backend, frontend=frontend)


def _parse_env_scope(
    defaults: Any,
    required: Any,
    optional: Any,
    hidden: Any,
    locked: Any,
) -> EnvScopeOverrides:
    return EnvScopeOverrides(
        defaults=_coerce_env_map(defaults) if defaults is not None else None,
        required=_coerce_env_list(required),
        optional=_coerce_env_list(optional),
        hidden=_coerce_env_list(hidden),
        locked=_coerce_env_list(locked),
    )


def _parse_choices(raw: Any) -> dict[str, tuple[str, ...]]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ProfileSchemaError("choices must be a mapping.")
    choices: dict[str, tuple[str, ...]] = {}
    for key, value in raw.items():
        choices[str(key)] = tuple(_coerce_list(value))
    return choices


def _parse_rules(raw: Any) -> ProfileRules:
    if raw is None:
        return ProfileRules()
    if not isinstance(raw, dict):
        raise ProfileSchemaError("rules must be a mapping.")
    unknown = set(raw) - _RULES
    if unknown:
        raise ProfileSchemaError(f"Unknown rules: {sorted(unknown)}")
    geoip_required_mode = _coerce_optional_str(raw.get("geoip_required_mode"))
    if geoip_required_mode and geoip_required_mode not in _GEOIP_REQUIRED_MODES:
        raise ProfileSchemaError(
            "geoip_required_mode must be one of "
            f"{sorted(_GEOIP_REQUIRED_MODES)}."
        )
    return ProfileRules(
        require_vault=_coerce_optional_bool(raw.get("require_vault")),
        require_database_url=_coerce_optional_bool(raw.get("require_database_url")),
        redis_tls_required=_coerce_optional_bool(raw.get("redis_tls_required")),
        stripe_webhook_auto_allowed=_coerce_optional_bool(
            raw.get("stripe_webhook_auto_allowed")
        ),
        dev_user_allowed=_coerce_optional_bool(raw.get("dev_user_allowed")),
        geoip_required_mode=geoip_required_mode,
        frontend_log_ingest_requires_confirmation=_coerce_optional_bool(
            raw.get("frontend_log_ingest_requires_confirmation")
        ),
        migrations_prompt_default=_coerce_optional_bool(raw.get("migrations_prompt_default")),
    )


def _coerce_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip()


def _coerce_optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y"}:
        return True
    if text in {"0", "false", "no", "n"}:
        return False
    raise ProfileSchemaError(f"Invalid boolean value '{value}'.")


def _coerce_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list | tuple | set):
        return [str(item) for item in value]
    return [str(value)]


def _coerce_env_map(value: Any) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ProfileSchemaError("env defaults must be a mapping.")
    result: dict[str, str] = {}
    for key, item in value.items():
        result[_normalize_env_key(key)] = _normalize_env_value(item)
    return result


def _normalize_env_key(key: Any) -> str:
    return str(key).strip().upper()


def _normalize_env_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return str(value).strip()


def _coerce_env_list(value: Any) -> tuple[str, ...] | None:
    if value is None:
        return None
    return tuple(_normalize_env_key(item) for item in _coerce_list(value))


__all__ = [
    "AutomationPolicy",
    "AutomationOverrides",
    "DetectPolicy",
    "DetectRule",
    "EnvMatchRule",
    "EnvPolicy",
    "EnvPolicyOverrides",
    "EnvScopePolicy",
    "EnvScopeOverrides",
    "ProfileDefinition",
    "ProfilePolicy",
    "ProfileRules",
    "ProfileSchemaError",
    "ProfilesDocument",
    "WizardPolicy",
    "WizardOverrides",
    "detect_profile",
    "load_profiles",
    "parse_profiles",
    "resolve_profile",
    "resolve_profiles",
]
