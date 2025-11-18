"""Declarative schema + dependency graph for the setup wizard."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

SCHEMA_PATH = Path(__file__).with_name("schema.yaml")


class SchemaError(RuntimeError):
    """Raised when the schema file contains invalid data."""


def _normalize_key(key: str) -> str:
    return key.strip().upper()


def _normalize_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip()


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _falsy(value: Any) -> bool:
    if isinstance(value, bool):
        return not value
    if value is None:
        return True
    return str(value).strip().lower() in {"", "0", "false", "no", "n"}


@dataclass(slots=True)
class Condition:
    key: str
    equals: str | None = None
    not_equals: str | None = None
    any_of: tuple[str, ...] = ()
    none_of: tuple[str, ...] = ()
    truthy: bool = False
    falsy: bool = False

    def evaluate(self, lookup: ValueLookup) -> bool:
        value = lookup.get(self.key)
        normalized = _normalize_value(value) if value is not None else ""
        if self.equals is not None and normalized.lower() != self.equals.lower():
            return False
        if self.not_equals is not None and normalized.lower() == self.not_equals.lower():
            return False
        if self.any_of and normalized.lower() not in {item.lower() for item in self.any_of}:
            return False
        if self.none_of and normalized.lower() in {item.lower() for item in self.none_of}:
            return False
        if self.truthy and not _truthy(value):
            return False
        if self.falsy and not _falsy(value):
            return False
        return True


@dataclass(slots=True)
class PromptRule:
    key: str
    section: str
    label: str | None = None
    description: str | None = None
    default: str | None = None
    when: tuple[Condition, ...] = ()
    skip_message: str | None = None

    def decide(self, lookup: ValueLookup) -> SchemaDecision:
        if not self.when:
            return SchemaDecision(should_prompt=True)
        for condition in self.when:
            if condition.evaluate(lookup):
                continue
            reason = self.skip_message or f"{condition.key} unmet"
            return SchemaDecision(
                should_prompt=False,
                reason=reason,
                fallback=self.default,
            )
        return SchemaDecision(should_prompt=True)


@dataclass(slots=True)
class SchemaDecision:
    should_prompt: bool
    reason: str | None = None
    fallback: str | None = None


class ValueLookup:
    """Query interface used during dependency evaluation."""

    def __init__(self, providers: Iterable[Mapping[str, Any]]) -> None:
        self.providers = list(providers)

    def get(self, key: str) -> Any | None:
        normalized = _normalize_key(key)
        for provider in self.providers:
            if not provider:
                continue
            if normalized in provider:
                return provider[normalized]
        return None


@dataclass(slots=True)
class WizardSchema:
    version: int
    rules: dict[str, PromptRule] = field(default_factory=dict)

    def decision(self, key: str, lookup: ValueLookup) -> SchemaDecision:
        rule = self.rules.get(_normalize_key(key))
        if not rule:
            return SchemaDecision(should_prompt=True)
        return rule.decide(lookup)


def load_schema(path: Path | None = None) -> WizardSchema:
    target = path or SCHEMA_PATH
    if not target.exists():
        raise SchemaError(f"Schema file missing at {target}")
    raw = yaml.safe_load(target.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SchemaError("Schema root must be a mapping.")
    version = int(raw.get("version") or 1)
    raw_prompts = raw.get("prompts")
    if not isinstance(raw_prompts, dict):
        raise SchemaError("Schema must define a 'prompts' mapping.")
    rules: dict[str, PromptRule] = {}
    for raw_key, raw_rule in raw_prompts.items():
        if not isinstance(raw_rule, dict):
            raise SchemaError(f"Prompt {raw_key} must be a mapping.")
        rule = PromptRule(
            key=_normalize_key(raw_key),
            section=str(raw_rule.get("section") or "general"),
            label=raw_rule.get("label"),
            description=raw_rule.get("description"),
            default=_coerce_optional_str(raw_rule.get("default")),
            when=_parse_conditions(raw_rule.get("when")),
            skip_message=_coerce_optional_str(raw_rule.get("skip_message")),
        )
        rules[rule.key] = rule
    return WizardSchema(version=version, rules=rules)


def _parse_conditions(data: Any) -> tuple[Condition, ...]:
    if not data:
        return ()
    if not isinstance(data, list):
        raise SchemaError("'when' must be a list of conditions.")
    conditions: list[Condition] = []
    for entry in data:
        if not isinstance(entry, dict):
            raise SchemaError("Condition entries must be mappings.")
        key = entry.get("key")
        if not key:
            raise SchemaError("Condition missing 'key'.")
        conditions.append(
            Condition(
                key=_normalize_key(key),
                equals=_coerce_optional_str(entry.get("equals")),
                not_equals=_coerce_optional_str(entry.get("not_equals")),
                any_of=tuple(_coerce_list(entry.get("any_of"))),
                none_of=tuple(_coerce_list(entry.get("none_of"))),
                truthy=bool(entry.get("truthy", False)),
                falsy=bool(entry.get("falsy", False)),
            )
        )
    return tuple(conditions)


def _coerce_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _coerce_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list | tuple | set):
        return [str(item) for item in value]
    return [str(value)]


__all__ = [
    "WizardSchema",
    "SchemaDecision",
    "SchemaError",
    "load_schema",
    "ValueLookup",
]
