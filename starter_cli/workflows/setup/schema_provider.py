"""Schema-aware wrapper for wizard input providers."""

from __future__ import annotations

import os
from collections.abc import Mapping

from starter_cli.adapters.io.console import console

from .schema import SchemaDecision, ValueLookup, WizardSchema
from .state import WizardStateStore


def _normalize(key: str) -> str:
    return key.strip().upper()


class SchemaAwareInputProvider:
    """Wraps an InputProvider and skips prompts with unmet dependencies."""

    def __init__(
        self,
        *,
        provider,
        schema: WizardSchema | None,
        state: WizardStateStore,
        context,
    ) -> None:
        self._provider = provider
        self._schema = schema
        self._state = state
        self._context = context
        self._answers: dict[str, str] = {}

    # ------------------------------------------------------------------
    # InputProvider API
    # ------------------------------------------------------------------
    def prompt_string(self, *, key: str, prompt: str, default: str | None, required: bool) -> str:
        decision = self._decide(key)
        if not decision.should_prompt:
            value = self._fallback_string(key, default=default, decision=decision)
            self._record_skip(key, decision.reason or "Skipped via dependency graph.")
            return value
        value = self._provider.prompt_string(
            key=key,
            prompt=prompt,
            default=default,
            required=required,
        )
        self._record_answer(key, value)
        return value

    def prompt_bool(self, *, key: str, prompt: str, default: bool) -> bool:
        decision = self._decide(key)
        if not decision.should_prompt:
            value = self._fallback_bool(decision, default=default)
            self._record_skip(key, decision.reason or "Skipped via dependency graph.")
            return value
        value = self._provider.prompt_bool(key=key, prompt=prompt, default=default)
        self._record_answer(key, "true" if value else "false")
        return value

    def prompt_secret(
        self,
        *,
        key: str,
        prompt: str,
        existing: str | None,
        required: bool,
    ) -> str:
        decision = self._decide(key)
        if not decision.should_prompt:
            value = existing or decision.fallback or ""
            self._record_skip(key, decision.reason or "Skipped via dependency graph.")
            if value:
                self._record_answer(key, "***")
            return value
        value = self._provider.prompt_secret(
            key=key,
            prompt=prompt,
            existing=existing,
            required=required,
        )
        masked = "***" if value else ""
        if value:
            self._record_answer(key, masked)
        return value

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _decide(self, key: str):
        if not self._schema:
            return SchemaDecision(should_prompt=True)
        lookup = ValueLookup(self._value_sources)
        return self._schema.decision(key, lookup)

    @property
    def _value_sources(self) -> tuple[Mapping[str, str], ...]:
        backend: dict[str, str] = getattr(self._context.backend_env, "as_dict", lambda: {})()
        state_snapshot: dict[str, str] = self._state.snapshot()
        env_values = {k.upper(): v for k, v in os.environ.items()}
        return (
            self._answers,
            {k.upper(): v for k, v in backend.items()},
            state_snapshot,
            env_values,
        )

    def _record_answer(self, key: str, value: str) -> None:
        normalized = _normalize(key)
        self._answers[normalized] = value
        self._state.record_answer(normalized, value)

    def _record_skip(self, key: str, reason: str) -> None:
        normalized = _normalize(key)
        console.info(f"Skipping {key}: {reason}", topic="wizard")
        self._state.record_skip(normalized, reason)

    def _fallback_string(
        self,
        key: str,
        *,
        default: str | None,
        decision,
    ) -> str:
        if decision.fallback is not None:
            return decision.fallback
        if default is not None:
            return default
        current = self._context.current(key)
        if current is not None:
            return current
        return ""

    @staticmethod
    def _fallback_bool(decision, *, default: bool) -> bool:
        raw = decision.fallback
        if raw is None:
            return default
        normalized = str(raw).strip().lower()
        if normalized in {"1", "true", "yes", "y"}:
            return True
        if normalized in {"0", "false", "no", "n"}:
            return False
        return default

    @property
    def answers(self):  # pragma: no cover - passthrough access
        if hasattr(self._provider, "answers"):
            return getattr(self._provider, "answers")
        raise AttributeError("answers not available")


__all__ = ["SchemaAwareInputProvider"]
