from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.guardrails._shared.config_adapter import (
    BundleConfig,
    ConfigBundle,
    GuardrailConfig,
    GuardrailConfigError,
    PipelineBundles,
    ResolvedGuardrailConfig,
    load_pipeline_bundles,
    resolve_guardrail_configs,
)
from app.guardrails._shared.loaders import load_guardrail_specs
from app.guardrails._shared.registry import GuardrailRegistry


def build_registry() -> GuardrailRegistry:
    reg = GuardrailRegistry()
    for spec in load_guardrail_specs():
        reg.register_spec(spec)
    return reg


def test_load_pipeline_bundles_from_dict() -> None:
    data = {
        "version": 1,
        "pre_flight": {
            "version": 1,
            "guardrails": [{"name": "pii_detection_input", "config": {"block": False}}],
        },
    }

    pipeline = load_pipeline_bundles(data)
    assert pipeline.pre_flight is not None
    assert pipeline.pre_flight.guardrails[0].name == "pii_detection_input"


def test_load_pipeline_bundles_accepts_str_path(tmp_path: Path):
    config_path = tmp_path / "guardrails_config.json"
    config_path.write_text(
        json.dumps(
            {
                "version": 1,
                "input": {
                    "version": 1,
                    "guardrails": [],
                },
            }
        )
    )

    bundles = load_pipeline_bundles(str(config_path))

    assert bundles.input is not None
    assert bundles.input.guardrails == []


def test_resolve_guardrail_configs_success() -> None:
    registry = build_registry()
    pipeline = PipelineBundles(
        version=1,
        pre_flight=ConfigBundle(
            guardrails=[GuardrailConfig(name="pii_detection_input", config={"block": True})],
            config=None,
        ),
        input=ConfigBundle(
            guardrails=[GuardrailConfig(name="moderation", config={"threshold": 0.6})],
            config=None,
        ),
        tool_output=ConfigBundle(
            guardrails=[
                GuardrailConfig(name="pii_tool_output", config={"block": False}),
            ],
            config=None,
        ),
    )

    resolved = resolve_guardrail_configs(pipeline, registry)
    assert isinstance(resolved, ResolvedGuardrailConfig)
    assert resolved.agent_guardrails is not None
    assert resolved.tool_guardrails is not None
    agent_keys = {cfg.guardrail_key for cfg in resolved.agent_guardrails.guardrails}
    assert "pii_detection_input" in agent_keys
    assert "moderation" in agent_keys
    tool_output_keys = {
        cfg.guardrail_key for cfg in resolved.tool_guardrails.output.guardrails  # type: ignore[union-attr]
    }
    assert "pii_tool_output" in tool_output_keys


def test_resolve_guardrail_configs_unknown_guardrail_raises() -> None:
    registry = build_registry()
    pipeline = PipelineBundles(
        version=1,
        input=ConfigBundle(
            guardrails=[GuardrailConfig(name="does_not_exist", config={})],
            config=None,
        ),
    )

    with pytest.raises(GuardrailConfigError):
        resolve_guardrail_configs(pipeline, registry)


def test_resolve_guardrail_configs_stage_mismatch_raises() -> None:
    registry = build_registry()
    pipeline = PipelineBundles(
        version=1,
        input=ConfigBundle(
            guardrails=[GuardrailConfig(name="pii_detection_output", config={})],
            config=None,
        ),
    )

    with pytest.raises(GuardrailConfigError):
        resolve_guardrail_configs(pipeline, registry)


def test_suppress_flags_are_not_global() -> None:
    registry = build_registry()
    pipeline = PipelineBundles(
        version=1,
        pre_flight=ConfigBundle(
            guardrails=[GuardrailConfig(name="pii_detection_input", config={})],
            config=BundleConfig(suppress_tripwire=False),
        ),
        input=ConfigBundle(
            guardrails=[GuardrailConfig(name="moderation", config={})],
            config=BundleConfig(suppress_tripwire=False),
        ),
        tool_output=ConfigBundle(
            guardrails=[GuardrailConfig(name="pii_tool_output", config={})],
            config=BundleConfig(suppress_tripwire=True),
        ),
    )

    resolved = resolve_guardrail_configs(pipeline, registry)
    assert resolved.agent_guardrails is not None
    assert resolved.agent_guardrails.suppress_tripwire is False
    assert resolved.tool_guardrails is not None
    assert resolved.tool_guardrails.output is not None
    assert resolved.tool_guardrails.output.suppress_tripwire is True


def test_bundle_concurrency_sets_runtime_options() -> None:
    registry = build_registry()
    pipeline = PipelineBundles(
        version=1,
        pre_flight=ConfigBundle(
            guardrails=[GuardrailConfig(name="pii_detection_input", config={})],
            config=BundleConfig(concurrency=5),
        ),
        tool_output=ConfigBundle(
            guardrails=[GuardrailConfig(name="pii_tool_output", config={})],
            config=BundleConfig(concurrency=3),
        ),
    )

    resolved = resolve_guardrail_configs(pipeline, registry)
    assert resolved.runtime_options is not None
    assert resolved.runtime_options.concurrency == 3  # picks the most restrictive
