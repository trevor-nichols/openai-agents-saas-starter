"""Terraform export helpers for infra blueprints."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum

from starter_contracts.infra.terraform_spec import (
    TerraformCondition,
    TerraformProvider,
    TerraformProviderSpec,
    TerraformStringPresence,
    TerraformVariableSpec,
    get_provider_spec,
    matches_condition,
    resolve_required_variables,
    validate_provider_values,
)


class TerraformExportMode(StrEnum):
    TEMPLATE = "template"
    FILLED = "filled"


class TerraformExportFormat(StrEnum):
    HCL = "hcl"
    JSON = "json"


class TerraformExportError(RuntimeError):
    pass


_REQUIRED_PLACEHOLDER = "__REQUIRED__"
_REDACTED_PLACEHOLDER = "__REDACTED__"


@dataclass(slots=True)
class TerraformExportOptions:
    provider: TerraformProvider
    mode: TerraformExportMode = TerraformExportMode.TEMPLATE
    format: TerraformExportFormat = TerraformExportFormat.HCL
    include_advanced: bool = False
    include_secrets: bool = False
    include_defaults: bool = False


@dataclass(slots=True)
class TerraformExportResult:
    provider: TerraformProvider
    values: dict[str, object]
    missing_required: tuple[str, ...]
    missing_requirements: tuple[str, ...]
    failed_validations: tuple[str, ...]

    def render(self, *, format: TerraformExportFormat | None = None) -> str:
        target = format or TerraformExportFormat.HCL
        if target == TerraformExportFormat.JSON:
            return json.dumps(self.values, indent=2) + "\n"
        return render_hcl(self.values)


def build_export(
    *,
    options: TerraformExportOptions,
    overrides: Mapping[str, object] | None = None,
    answers: Mapping[str, object] | None = None,
    env: Mapping[str, object] | None = None,
    extra_vars: Mapping[str, object] | None = None,
) -> TerraformExportResult:
    spec = get_provider_spec(options.provider)
    normalized_overrides = _normalize_source(overrides or {})
    normalized_answers = _normalize_source(answers or {})
    normalized_env = _normalize_source(env or {})

    provided = _resolve_values(spec, normalized_overrides, normalized_answers, normalized_env)
    defaults = {var.name: var.default for var in spec.variables if var.default is not None}
    values_for_conditions = {**defaults, **provided}

    required_vars = resolve_required_variables(spec.provider, values_for_conditions)
    missing_required = tuple(
        var.name
        for var in required_vars
        if not _value_satisfies(var, values_for_conditions.get(var.name))
    )
    missing_requirements = _missing_requirement_messages(spec, values_for_conditions)
    failed_validations = validate_provider_values(spec, values_for_conditions)
    template_required = _template_required_names(missing_required, spec, missing_requirements)

    if options.mode == TerraformExportMode.FILLED and (
        missing_required or missing_requirements or failed_validations
    ):
        raise TerraformExportError(
            _format_missing_error(spec, missing_required, missing_requirements, failed_validations)
        )

    values = _build_output_values(
        spec=spec,
        options=options,
        provided=provided,
        defaults=defaults,
        template_required=template_required,
    )

    _merge_extra_vars(values, spec, extra_vars)

    return TerraformExportResult(
        provider=spec.provider,
        values=values,
        missing_required=missing_required,
        missing_requirements=missing_requirements,
        failed_validations=failed_validations,
    )


def render_hcl(values: Mapping[str, object]) -> str:
    lines: list[str] = []
    for key, value in values.items():
        rendered = _render_hcl_value(value, indent=0)
        if isinstance(value, Mapping):
            lines.append(f"{key} = {rendered}")
        else:
            lines.append(f"{key} = {rendered}")
    return "\n".join(lines) + "\n"


def _normalize_source(values: Mapping[str, object]) -> dict[str, object]:
    normalized: dict[str, object] = {}
    for key, value in values.items():
        normalized[_normalize_key(key)] = value
    return normalized


def _normalize_key(key: str) -> str:
    return key.strip().lower()


def _resolve_values(
    spec: TerraformProviderSpec,
    overrides: Mapping[str, object],
    answers: Mapping[str, object],
    env: Mapping[str, object],
) -> dict[str, object]:
    resolved: dict[str, object] = {}
    for variable in spec.variables:
        raw = _resolve_raw_value(variable, overrides, answers, env)
        if raw is None:
            continue
        resolved[variable.name] = _coerce_value(variable, raw)
    return resolved


def _resolve_raw_value(
    variable: TerraformVariableSpec,
    overrides: Mapping[str, object],
    answers: Mapping[str, object],
    env: Mapping[str, object],
) -> object | None:
    keys = (variable.name, *variable.env_aliases)
    for key in keys:
        normalized = _normalize_key(key)
        if normalized in overrides:
            return overrides[normalized]
        if normalized in answers:
            return answers[normalized]
        if normalized in env:
            return env[normalized]
    return None


def _coerce_value(variable: TerraformVariableSpec, raw: object) -> object:
    var_type = variable.var_type
    if var_type == "string":
        return str(raw)
    if var_type == "number":
        if isinstance(raw, bool):
            raise TerraformExportError(f"{variable.name} must be a number, not boolean.")
        if isinstance(raw, int | float):
            return raw
        raw_str = str(raw).strip()
        try:
            return int(raw_str)
        except ValueError:
            try:
                return float(raw_str)
            except ValueError as exc:
                raise TerraformExportError(
                    f"{variable.name} must be a number (got {raw_str})."
                ) from exc
    if var_type == "bool":
        if isinstance(raw, bool):
            return raw
        raw_str = str(raw).strip().lower()
        if raw_str in {"1", "true", "yes", "y", "on"}:
            return True
        if raw_str in {"0", "false", "no", "n", "off"}:
            return False
        raise TerraformExportError(f"{variable.name} must be a boolean (got {raw}).")
    if var_type.startswith("map("):
        if isinstance(raw, Mapping):
            return {str(key): str(value) for key, value in raw.items()}
        raw_str = str(raw).strip()
        if raw_str == "":
            return {}
        try:
            parsed = json.loads(raw_str)
        except json.JSONDecodeError as exc:
            raise TerraformExportError(
                f"{variable.name} must be a JSON object for {var_type}."
            ) from exc
        if not isinstance(parsed, Mapping):
            raise TerraformExportError(f"{variable.name} must be a JSON object.")
        return {str(key): str(value) for key, value in parsed.items()}
    return raw


def _build_output_values(
    *,
    spec: TerraformProviderSpec,
    options: TerraformExportOptions,
    provided: Mapping[str, object],
    defaults: Mapping[str, object],
    template_required: set[str],
) -> dict[str, object]:
    output: dict[str, object] = {}
    for variable in spec.variables:
        value = provided.get(variable.name)
        if value is None:
            if options.mode == TerraformExportMode.TEMPLATE and variable.name in template_required:
                value = variable.template_value or _REQUIRED_PLACEHOLDER
            elif options.include_defaults and variable.default is not None:
                value = variable.default
            else:
                continue

        if (
            not options.include_advanced
            and variable.advanced
            and variable.name not in template_required
        ):
            if variable.name not in provided:
                continue

        if variable.sensitive and not options.include_secrets:
            value = _redact_value(value)

        output[variable.name] = value
    return output


def _merge_extra_vars(
    output: dict[str, object],
    spec: TerraformProviderSpec,
    extra_vars: Mapping[str, object] | None,
) -> None:
    if not extra_vars:
        return
    existing_lower = {key.lower() for key in output}
    spec_names_lower = {variable.name.lower() for variable in spec.variables}
    for key, value in extra_vars.items():
        normalized = key.strip()
        normalized_lower = normalized.lower()
        if normalized_lower in spec_names_lower:
            raise TerraformExportError(
                f"extra_vars cannot override known variable '{normalized}'."
            )
        if normalized_lower in existing_lower:
            raise TerraformExportError(
                f"extra_vars defines '{normalized}' multiple times."
            )
        existing_lower.add(normalized_lower)
        output[normalized] = value


def _template_required_names(
    missing_required: Iterable[str],
    spec: TerraformProviderSpec,
    missing_requirements: Iterable[str],
) -> set[str]:
    template_required = set(missing_required)
    if not missing_requirements:
        return template_required
    rules_by_message = {rule.message: rule for rule in spec.requirements}
    for message in missing_requirements:
        rule = rules_by_message.get(message)
        if rule:
            template_required.update(rule.any_of)
    return template_required


def _missing_requirement_messages(
    spec: TerraformProviderSpec,
    values: Mapping[str, object],
) -> tuple[str, ...]:
    missing: list[str] = []
    for rule in spec.requirements:
        if not _matches_conditions(values, rule.when):
            continue
        if not _any_value_present(values, spec, rule.any_of):
            missing.append(rule.message)
    return tuple(missing)


def _matches_conditions(
    values: Mapping[str, object],
    conditions: Iterable[TerraformCondition],
) -> bool:
    return all(matches_condition(values, condition) for condition in conditions)


def _any_value_present(
    values: Mapping[str, object],
    spec: TerraformProviderSpec,
    names: Iterable[str],
) -> bool:
    spec_by_name = spec.variables_by_name()
    for name in names:
        variable = spec_by_name.get(name)
        if not variable:
            if _path_value_present(values, name):
                return True
            continue
        if _value_satisfies(variable, values.get(name)):
            return True
    return False


def _value_satisfies(variable: TerraformVariableSpec, value: object | None) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        if variable.string_presence == TerraformStringPresence.RAW:
            return value != ""
        return value.strip() != ""
    if isinstance(value, Mapping):
        if variable.template_value and isinstance(variable.template_value, Mapping):
            for key in variable.template_value:
                if not str(value.get(key, "")).strip():
                    return False
        return bool(value)
    return True


def _path_value_present(values: Mapping[str, object], path: str) -> bool:
    if "." not in path:
        return False
    parts = path.split(".")
    current: object = values
    for part in parts[:-1]:
        if not isinstance(current, Mapping):
            return False
        if part not in current:
            return False
        current = current[part]
    if not isinstance(current, Mapping):
        return False
    if parts[-1] not in current:
        return False
    value = current[parts[-1]]
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    return True


def _redact_value(value: object) -> object:
    if value == _REQUIRED_PLACEHOLDER:
        return value
    if isinstance(value, Mapping):
        return {key: _redact_value(val) for key, val in value.items()}
    return _REDACTED_PLACEHOLDER


def _render_hcl_value(value: object, *, indent: int) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    if isinstance(value, Mapping):
        return _render_hcl_map(value, indent=indent)
    return json.dumps(str(value))


def _render_hcl_map(value: Mapping[str, object], *, indent: int) -> str:
    inner_indent = "  " * (indent + 1)
    outer_indent = "  " * indent
    lines = ["{"]
    for key in sorted(value.keys()):
        rendered = _render_hcl_value(value[key], indent=indent + 1)
        lines.append(f"{inner_indent}{json.dumps(str(key))} = {rendered}")
    lines.append(f"{outer_indent}}}")
    return "\n".join(lines)


def _format_missing_error(
    spec: TerraformProviderSpec,
    missing_required: Iterable[str],
    missing_requirements: Iterable[str],
    failed_validations: Iterable[str],
) -> str:
    lines = [f"Terraform export validation failed for {spec.provider.value}:"]
    if missing_required:
        lines.append("Missing required inputs:")
        for name in sorted(missing_required):
            lines.append(f"- {name}")
    if missing_requirements:
        lines.append("Missing requirement rules:")
        for message in missing_requirements:
            lines.append(f"- {message}")
    if failed_validations:
        lines.append("Validation errors:")
        for message in failed_validations:
            lines.append(f"- {message}")
    return "\n".join(lines)


__all__ = [
    "TerraformExportError",
    "TerraformExportFormat",
    "TerraformExportMode",
    "TerraformExportOptions",
    "TerraformExportResult",
    "build_export",
    "render_hcl",
]
