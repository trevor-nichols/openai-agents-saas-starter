from __future__ import annotations

import pytest

from starter_contracts.profiles import schema as profile_schema


def test_load_default_profiles() -> None:
    document = profile_schema.load_profiles()
    assert document.version == 1
    assert {"demo", "staging", "production"}.issubset(document.profiles)


def test_profile_inheritance_merges_defaults_and_inherits_lists() -> None:
    raw = {
        "version": 1,
        "profiles": {
            "base": {
                "env": {
                    "defaults": {"backend": {"DEBUG": False}},
                    "required": {"backend": ["OPENAI_API_KEY"]},
                }
            },
            "child": {
                "extends": "base",
                "env": {"defaults": {"backend": {"DEBUG": True}}},
            },
        },
    }
    document = profile_schema.parse_profiles(raw)
    resolved = profile_schema.resolve_profile(document, "child")
    assert resolved.env.backend.defaults["DEBUG"] == "true"
    assert resolved.env.backend.required == ("OPENAI_API_KEY",)


def test_detect_profile_prefers_lowest_priority() -> None:
    raw = {
        "version": 1,
        "profiles": {
            "a": {
                "detect": {
                    "priority": 20,
                    "any": [{"env": {"key": "ENVIRONMENT", "equals": "prod"}}],
                }
            },
            "b": {
                "detect": {
                    "priority": 10,
                    "any": [{"env": {"key": "ENVIRONMENT", "equals": "prod"}}],
                }
            },
        },
    }
    profiles = profile_schema.resolve_profiles(profile_schema.parse_profiles(raw))
    detected = profile_schema.detect_profile(profiles, {"ENVIRONMENT": "prod"})
    assert detected is not None
    assert detected.profile_id == "b"

def test_detect_priority_accepts_zero() -> None:
    raw = {
        "version": 1,
        "profiles": {
            "a": {
                "detect": {
                    "priority": 0,
                    "any": [{"env": {"key": "ENVIRONMENT", "equals": "prod"}}],
                }
            }
        },
    }
    profile = profile_schema.resolve_profile(profile_schema.parse_profiles(raw), "a")
    assert profile.detect is not None
    assert profile.detect.priority == 0


def test_detect_rule_requires_predicate() -> None:
    raw = {
        "version": 1,
        "profiles": {"demo": {"detect": {"any": [{"env": {"key": "ENVIRONMENT"}}]}}},
    }
    with pytest.raises(profile_schema.ProfileSchemaError):
        profile_schema.parse_profiles(raw)


def test_geoip_required_mode_validation() -> None:
    raw = {
        "version": 1,
        "profiles": {"demo": {"rules": {"geoip_required_mode": "typo"}}},
    }
    with pytest.raises(profile_schema.ProfileSchemaError):
        profile_schema.parse_profiles(raw)


def test_automation_allow_empty_list_is_preserved() -> None:
    raw = {
        "version": 1,
        "profiles": {"demo": {"wizard": {"automation": {"allow": []}}}},
    }
    profile = profile_schema.resolve_profile(profile_schema.parse_profiles(raw), "demo")
    assert profile.wizard.automation.allow == ()


def test_automation_allow_unset_is_none() -> None:
    raw = {"version": 1, "profiles": {"demo": {}}}
    profile = profile_schema.resolve_profile(profile_schema.parse_profiles(raw), "demo")
    assert profile.wizard.automation.allow is None


def test_unknown_rule_raises_error() -> None:
    raw = {
        "version": 1,
        "profiles": {"demo": {"rules": {"unknown_rule": True}}},
    }
    try:
        profile_schema.parse_profiles(raw)
    except profile_schema.ProfileSchemaError as exc:
        assert "Unknown rules" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected ProfileSchemaError")
