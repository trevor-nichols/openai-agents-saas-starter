"""Terraform input specifications for Starter infra exports."""

from __future__ import annotations

from collections.abc import Mapping

from .aws import AWS_REQUIREMENTS, AWS_VALIDATIONS, AWS_VARIABLES
from .azure import AZURE_REQUIREMENTS, AZURE_VALIDATIONS, AZURE_VARIABLES
from .gcp import GCP_REQUIREMENTS, GCP_VALIDATIONS, GCP_VARIABLES
from .models import (
    TerraformAllowedValuesCheck,
    TerraformComparisonCheck,
    TerraformCondition,
    TerraformDisallowedValuesCheck,
    TerraformMapKeyExclusionCheck,
    TerraformProvider,
    TerraformProviderSpec,
    TerraformRangeCheck,
    TerraformRequirementRule,
    TerraformStringPresence,
    TerraformValidationRule,
    TerraformVarCategory,
    TerraformVariableSpec,
    matches_condition,
    validate_provider_values,
)
from .models import (
    resolve_required_variables as _resolve_required_variables,
)
from .registry import get_provider_spec, list_provider_specs


def resolve_required_variables(
    provider: TerraformProvider | str,
    values: Mapping[str, object] | None = None,
) -> tuple[TerraformVariableSpec, ...]:
    spec = get_provider_spec(provider)
    return _resolve_required_variables(spec, values)


def resolve_required_variables_for_provider(
    provider: TerraformProvider | str,
    values: Mapping[str, object] | None = None,
) -> tuple[TerraformVariableSpec, ...]:
    return resolve_required_variables(provider, values)


__all__ = [
    "AWS_REQUIREMENTS",
    "AWS_VALIDATIONS",
    "AWS_VARIABLES",
    "AZURE_REQUIREMENTS",
    "AZURE_VALIDATIONS",
    "AZURE_VARIABLES",
    "GCP_REQUIREMENTS",
    "GCP_VALIDATIONS",
    "GCP_VARIABLES",
    "TerraformAllowedValuesCheck",
    "TerraformComparisonCheck",
    "TerraformCondition",
    "TerraformDisallowedValuesCheck",
    "TerraformMapKeyExclusionCheck",
    "TerraformProvider",
    "TerraformProviderSpec",
    "TerraformRangeCheck",
    "TerraformRequirementRule",
    "TerraformStringPresence",
    "TerraformValidationRule",
    "TerraformVarCategory",
    "TerraformVariableSpec",
    "get_provider_spec",
    "list_provider_specs",
    "matches_condition",
    "resolve_required_variables",
    "resolve_required_variables_for_provider",
    "validate_provider_values",
]
