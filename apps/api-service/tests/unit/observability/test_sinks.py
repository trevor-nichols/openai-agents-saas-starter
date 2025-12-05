from __future__ import annotations

from app.core.settings import Settings
from app.observability.logging.config import ALLOWED_SINKS
from app.observability.logging.sinks import SINK_BUILDERS, build_null_sink


def test_sink_registry_matches_allowed_sinks() -> None:
    # Ensure registry stays in lockstep with allowed config values.
    assert set(SINK_BUILDERS.keys()) == ALLOWED_SINKS


def test_build_null_sink_returns_null_handler() -> None:
    cfg = build_null_sink(Settings.model_validate({}), "INFO", "json", file_selected=False)

    assert cfg.root_handlers == ["null"]
    handler_cfg = cfg.handlers["null"]
    assert handler_cfg["class"] == "logging.NullHandler"
    assert handler_cfg["level"] == "INFO"
