"""Prompt template rendering helpers using a sandboxed Jinja2 environment."""

from __future__ import annotations

from typing import Any

from jinja2 import DebugUndefined, Environment, StrictUndefined


def _build_env(*, validate: bool) -> Environment:
    return Environment(
        undefined=StrictUndefined if validate else DebugUndefined,
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_prompt(template_str: str, *, context: dict[str, Any], validate: bool) -> str:
    """Render a prompt template with the provided context.

    When `validate` is True, missing variables will raise an error (StrictUndefined).
    When False, missing variables are left as-is (DebugUndefined) to allow boot-time
    construction without full runtime context.
    """

    env = _build_env(validate=validate)
    template = env.from_string(template_str)
    return template.render(**context)


__all__ = ["render_prompt"]
