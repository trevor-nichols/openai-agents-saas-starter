from __future__ import annotations

import pytest
from starter_console.core import CLIError
from starter_console.services.sso.registry import (
    CUSTOM_PRESET,
    find_preset,
    get_preset,
    list_presets,
)


def test_registry_includes_custom_preset() -> None:
    keys = {preset.key for preset in list_presets()}
    assert CUSTOM_PRESET.key in keys


def test_get_preset_custom() -> None:
    preset = get_preset("custom")
    assert preset.key == CUSTOM_PRESET.key


def test_get_preset_unknown_raises() -> None:
    with pytest.raises(CLIError, match="Unknown SSO provider preset"):
        get_preset("unknown")


def test_find_preset_unknown_returns_none() -> None:
    assert find_preset("unknown") is None
