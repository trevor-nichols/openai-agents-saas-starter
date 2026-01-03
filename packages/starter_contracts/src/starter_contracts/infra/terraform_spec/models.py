"""Shared models and condition helpers for Terraform specs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, TypeAlias


class TerraformProvider(StrEnum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


class TerraformVarCategory(StrEnum):
    CORE = "core"
    URLS = "urls"
    IMAGES = "images"
    NETWORK = "network"
    COMPUTE = "compute"
    SCALING = "scaling"
    DATABASE = "database"
    REDIS = "redis"
    STORAGE = "storage"
    SECRETS = "secrets"
    REGISTRY = "registry"
    RUNTIME = "runtime"
    SECURITY = "security"
    MISC = "misc"


class TerraformStringPresence(StrEnum):
    TRIMMED = "trimmed"
    RAW = "raw"


@dataclass(frozen=True, slots=True)
class TerraformAllowedValuesCheck:
    key: str
    allowed: tuple[object, ...]
    case_insensitive: bool = False


@dataclass(frozen=True, slots=True)
class TerraformDisallowedValuesCheck:
    key: str
    disallowed: tuple[object, ...]
    case_insensitive: bool = False


@dataclass(frozen=True, slots=True)
class TerraformRangeCheck:
    key: str
    min_value: int | float | None = None
    max_value: int | float | None = None


@dataclass(frozen=True, slots=True)
class TerraformComparisonCheck:
    left: str
    operator: str
    right: str


@dataclass(frozen=True, slots=True)
class TerraformMapKeyExclusionCheck:
    key: str
    disallowed_keys: tuple[str, ...]


TerraformValidationCheck: TypeAlias = (
    TerraformAllowedValuesCheck
    | TerraformDisallowedValuesCheck
    | TerraformRangeCheck
    | TerraformComparisonCheck
    | TerraformMapKeyExclusionCheck
)


@dataclass(frozen=True, slots=True)
class TerraformCondition:
    key: str
    equals: str | bool | int | None = None
    any_of: tuple[str | bool | int, ...] | None = None
    none_of: tuple[str | bool | int, ...] | None = None
    truthy: bool | None = None
    present: bool | None = None
    trim_whitespace: bool = True
    fallback_key: str | None = None


@dataclass(frozen=True, slots=True)
class TerraformVariableSpec:
    name: str
    var_type: str
    description: str
    category: TerraformVarCategory
    required: bool = False
    default: object | None = None
    sensitive: bool = False
    advanced: bool = False
    env_aliases: tuple[str, ...] = ()
    template_value: object | None = None
    required_when: tuple[TerraformCondition, ...] = ()
    string_presence: TerraformStringPresence = TerraformStringPresence.TRIMMED


@dataclass(frozen=True, slots=True)
class TerraformRequirementRule:
    when: tuple[TerraformCondition, ...]
    any_of: tuple[str, ...]
    message: str


@dataclass(frozen=True, slots=True)
class TerraformValidationRule:
    when: tuple[TerraformCondition, ...]
    check: TerraformValidationCheck
    message: str


@dataclass(frozen=True, slots=True)
class TerraformProviderSpec:
    provider: TerraformProvider
    variables: tuple[TerraformVariableSpec, ...]
    requirements: tuple[TerraformRequirementRule, ...] = ()
    validations: tuple[TerraformValidationRule, ...] = ()

    def variables_by_name(self) -> dict[str, TerraformVariableSpec]:
        return {variable.name: variable for variable in self.variables}


def matches_condition(values: Mapping[str, object], condition: TerraformCondition) -> bool:
    value = _resolve_condition_value(values, condition)
    if condition.present is True:
        return _is_present(value, trim=condition.trim_whitespace)
    if condition.present is False:
        return not _is_present(value, trim=condition.trim_whitespace)
    if condition.truthy is True:
        return _truthy(value)
    if condition.truthy is False:
        return not _truthy(value)
    if condition.equals is not None:
        return value == condition.equals
    if condition.any_of is not None:
        return value in condition.any_of
    if condition.none_of is not None:
        return value not in condition.none_of
    return False


def resolve_required_variables(
    spec: TerraformProviderSpec,
    values: Mapping[str, object] | None = None,
) -> tuple[TerraformVariableSpec, ...]:
    if values is None:
        return tuple(variable for variable in spec.variables if variable.required)
    return tuple(variable for variable in spec.variables if _is_required(variable, values))


def _is_required(variable: TerraformVariableSpec, values: Mapping[str, object]) -> bool:
    if variable.required:
        return True
    if not variable.required_when:
        return False
    return all(matches_condition(values, condition) for condition in variable.required_when)


def _resolve_condition_value(values: Mapping[str, object], condition: TerraformCondition) -> Any:
    value = _resolve_value(values, condition.key)
    if condition.fallback_key and _is_empty(value):
        return _resolve_value(values, condition.fallback_key)
    return value


def _resolve_value(values: Mapping[str, object], key: str) -> Any:
    if "." not in key:
        return values.get(key)
    current: Any = values
    for part in key.split("."):
        if not isinstance(current, Mapping):
            return None
        current = current.get(part)
    return current


def _is_present(value: object | None, *, trim: bool = True) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != "" if trim else value != ""
    return True


def _is_empty(value: object | None) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    return False


def _truthy(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, int | float):
        return value != 0
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def validate_provider_values(
    spec: TerraformProviderSpec,
    values: Mapping[str, object],
) -> tuple[str, ...]:
    failures: list[str] = []
    for rule in spec.validations:
        if rule.when and not all(matches_condition(values, condition) for condition in rule.when):
            continue
        if not _validation_passes(values, rule.check):
            failures.append(rule.message)
    return tuple(failures)


def _validation_passes(values: Mapping[str, object], check: TerraformValidationCheck) -> bool:
    if isinstance(check, TerraformAllowedValuesCheck):
        value = _resolve_value(values, check.key)
        if value is None:
            return False
        normalized = _normalize_comparable(value, check.case_insensitive)
        allowed = {
            _normalize_comparable(item, check.case_insensitive) for item in check.allowed
        }
        return normalized in allowed
    if isinstance(check, TerraformDisallowedValuesCheck):
        value = _resolve_value(values, check.key)
        if value is None:
            return True
        normalized = _normalize_comparable(value, check.case_insensitive)
        disallowed = {
            _normalize_comparable(item, check.case_insensitive) for item in check.disallowed
        }
        return normalized not in disallowed
    if isinstance(check, TerraformRangeCheck):
        value = _resolve_value(values, check.key)
        if not isinstance(value, int | float):
            return False
        if check.min_value is not None and value < check.min_value:
            return False
        if check.max_value is not None and value > check.max_value:
            return False
        return True
    if isinstance(check, TerraformComparisonCheck):
        left = _resolve_value(values, check.left)
        right = _resolve_value(values, check.right)
        if not isinstance(left, int | float) or not isinstance(right, int | float):
            return False
        if check.operator == ">=":
            return left >= right
        if check.operator == ">":
            return left > right
        if check.operator == "<=":
            return left <= right
        if check.operator == "<":
            return left < right
        raise ValueError(f"Unsupported comparison operator: {check.operator}")
    if isinstance(check, TerraformMapKeyExclusionCheck):
        value = _resolve_value(values, check.key)
        if value is None:
            return True
        if not isinstance(value, Mapping):
            return False
        return not any(key in value for key in check.disallowed_keys)
    raise TypeError(f"Unsupported validation check: {check!r}")


def _normalize_comparable(value: object, case_insensitive: bool) -> object:
    if not case_insensitive or not isinstance(value, str):
        return value
    return value.upper()


__all__ = [
    "TerraformCondition",
    "TerraformAllowedValuesCheck",
    "TerraformComparisonCheck",
    "TerraformDisallowedValuesCheck",
    "TerraformMapKeyExclusionCheck",
    "TerraformProvider",
    "TerraformProviderSpec",
    "TerraformRequirementRule",
    "TerraformRangeCheck",
    "TerraformStringPresence",
    "TerraformVarCategory",
    "TerraformValidationRule",
    "TerraformVariableSpec",
    "matches_condition",
    "resolve_required_variables",
    "validate_provider_values",
]
