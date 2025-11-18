from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from ..schema import Condition, PromptRule, WizardSchema
from .state import DependencyStatus, PromptMeta


def build_section_prompt_metadata(schema: WizardSchema | None) -> dict[str, tuple[PromptMeta, ...]]:
    """Group prompt metadata by section for UI rendering."""

    if schema is None:
        return {}

    grouped: dict[str, list[PromptMeta]] = defaultdict(list)
    for rule in schema.rules.values():
        metadata = _rule_to_prompt_meta(rule)
        if metadata is None:
            continue
        grouped[rule.section].append(metadata)
    return {section: tuple(entries) for section, entries in grouped.items()}


def _rule_to_prompt_meta(rule: PromptRule) -> PromptMeta | None:
    labels = tuple(filter(None, (_condition_summary(cond) for cond in rule.when)))
    if not labels:
        return None
    label = rule.label or rule.key
    dependencies = tuple(DependencyStatus(label=dependency) for dependency in labels)
    return PromptMeta(
        key=rule.key,
        label=label,
        description=rule.description,
        conditions=rule.when,
        dependency_labels=labels,
        dependencies=dependencies,
    )


def _condition_summary(condition: Condition) -> str | None:
    key = condition.key
    if condition.equals is not None:
        return f"{key} = {condition.equals}"
    if condition.not_equals is not None:
        return f"{key} ≠ {condition.not_equals}"
    if condition.any_of:
        options = ", ".join(condition.any_of)
        return f"{key} ∈ {{{options}}}"
    if condition.none_of:
        options = ", ".join(condition.none_of)
        return f"{key} ∉ {{{options}}}"
    if condition.truthy:
        return f"{key} is enabled"
    if condition.falsy:
        return f"{key} is disabled"
    return None


__all__ = ["build_section_prompt_metadata"]
