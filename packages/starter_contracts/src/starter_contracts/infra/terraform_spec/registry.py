"""Provider registry for Terraform specs."""

from __future__ import annotations

from collections.abc import Mapping

from .aws import AWS_REQUIREMENTS, AWS_VALIDATIONS, AWS_VARIABLES
from .azure import AZURE_REQUIREMENTS, AZURE_VALIDATIONS, AZURE_VARIABLES
from .gcp import GCP_REQUIREMENTS, GCP_VALIDATIONS, GCP_VARIABLES
from .models import (
    TerraformProvider,
    TerraformProviderSpec,
    TerraformVariableSpec,
    resolve_required_variables,
)

_PROVIDER_SPECS: dict[TerraformProvider, TerraformProviderSpec] = {
    TerraformProvider.AWS: TerraformProviderSpec(
        provider=TerraformProvider.AWS,
        variables=AWS_VARIABLES,
        requirements=AWS_REQUIREMENTS,
        validations=AWS_VALIDATIONS,
    ),
    TerraformProvider.AZURE: TerraformProviderSpec(
        provider=TerraformProvider.AZURE,
        variables=AZURE_VARIABLES,
        requirements=AZURE_REQUIREMENTS,
        validations=AZURE_VALIDATIONS,
    ),
    TerraformProvider.GCP: TerraformProviderSpec(
        provider=TerraformProvider.GCP,
        variables=GCP_VARIABLES,
        requirements=GCP_REQUIREMENTS,
        validations=GCP_VALIDATIONS,
    ),
}


def get_provider_spec(provider: TerraformProvider | str) -> TerraformProviderSpec:
    key = TerraformProvider(provider) if not isinstance(provider, TerraformProvider) else provider
    return _PROVIDER_SPECS[key]


def list_provider_specs() -> tuple[TerraformProviderSpec, ...]:
    return tuple(_PROVIDER_SPECS.values())


def resolve_required_variables_for_provider(
    provider: TerraformProvider | str,
    values: Mapping[str, object] | None = None,
) -> tuple[TerraformVariableSpec, ...]:
    spec = get_provider_spec(provider)
    return resolve_required_variables(spec, values)


__all__ = [
    "get_provider_spec",
    "list_provider_specs",
    "resolve_required_variables_for_provider",
]
