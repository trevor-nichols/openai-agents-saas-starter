from __future__ import annotations

from app.domain.ai import RunOptions
from app.infrastructure.providers.openai.run_config import build_run_config


def test_build_run_config_filters_allowed_keys_only():
    run_config = build_run_config(
        RunOptions(
            run_config={"model": "gpt-5.1", "tracing_disabled": True, "unsupported": True},
            handoff_input_filter="fresh",
        )
    )

    assert run_config is not None
    # Model override is intentionally not accepted from RunOptions.run_config.
    # Agents must be configured via AgentSpec.model / model_key or AGENT_MODEL_DEFAULT.
    assert run_config.model is None
    assert run_config.tracing_disabled is True
    # unsupported key is dropped
    assert not hasattr(run_config, "unsupported")
    # handoff_input_filter is attached
    assert run_config.handoff_input_filter is not None


def test_build_run_config_none_when_empty():
    assert build_run_config(None) is None
    assert build_run_config(RunOptions()) is None
