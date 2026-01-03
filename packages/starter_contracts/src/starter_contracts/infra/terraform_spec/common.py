"""Common Terraform variable definitions shared across providers."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, cast

from .models import (
    TerraformCondition,
    TerraformMapKeyExclusionCheck,
    TerraformStringPresence,
    TerraformValidationRule,
    TerraformVarCategory,
    TerraformVariableSpec,
)

_REQUIRED_PLACEHOLDER = "__REQUIRED__"


def _var(
    name: str,
    var_type: str,
    description: str,
    *,
    category: TerraformVarCategory,
    required: bool = False,
    default: object | None = None,
    sensitive: bool = False,
    advanced: bool = False,
    env_aliases: tuple[str, ...] = (),
    template_value: object | None = None,
    required_when: tuple[TerraformCondition, ...] = (),
    string_presence: TerraformStringPresence = TerraformStringPresence.TRIMMED,
) -> TerraformVariableSpec:
    return TerraformVariableSpec(
        name=name,
        var_type=var_type,
        description=description,
        category=category,
        required=required,
        default=default,
        sensitive=sensitive,
        advanced=advanced,
        env_aliases=env_aliases,
        template_value=template_value,
        required_when=required_when,
        string_presence=string_presence,
    )


def _clone(spec: TerraformVariableSpec, **changes: Any) -> TerraformVariableSpec:
    return cast(TerraformVariableSpec, replace(spec, **changes))


_COMMON_PROJECT_NAME = _var(
    "project_name",
    "string",
    "Base project name used for resource naming.",
    category=TerraformVarCategory.CORE,
    required=True,
)
_COMMON_ENVIRONMENT = _var(
    "environment",
    "string",
    "Deployment environment (dev/staging/prod).",
    category=TerraformVarCategory.CORE,
    required=True,
    env_aliases=("ENVIRONMENT",),
)
_COMMON_API_IMAGE = _var(
    "api_image",
    "string",
    "Container image for the API service.",
    category=TerraformVarCategory.IMAGES,
    required=True,
)
_COMMON_WEB_IMAGE = _var(
    "web_image",
    "string",
    "Container image for the web app.",
    category=TerraformVarCategory.IMAGES,
    required=True,
)
_COMMON_API_ENV = _var(
    "api_env",
    "map(string)",
    "Additional non-sensitive env vars for the API service.",
    category=TerraformVarCategory.RUNTIME,
    default={},
)
_COMMON_WEB_ENV = _var(
    "web_env",
    "map(string)",
    "Additional non-sensitive env vars for the web service.",
    category=TerraformVarCategory.RUNTIME,
    default={},
)
_COMMON_API_SECRETS = _var(
    "api_secrets",
    "map(string)",
    "Secret references for the API service (DATABASE_URL + REDIS_URL).",
    category=TerraformVarCategory.RUNTIME,
    default={"DATABASE_URL": "", "REDIS_URL": ""},
    template_value={"DATABASE_URL": _REQUIRED_PLACEHOLDER, "REDIS_URL": _REQUIRED_PLACEHOLDER},
    required=True,
    sensitive=True,
)
_COMMON_WEB_SECRETS = _var(
    "web_secrets",
    "map(string)",
    "Secret references for the web service.",
    category=TerraformVarCategory.RUNTIME,
    default={},
    sensitive=True,
)
_COMMON_API_ENV_DISALLOW_SECRETS_VALIDATION = TerraformValidationRule(
    when=(),
    check=TerraformMapKeyExclusionCheck(
        key="api_env",
        disallowed_keys=("DATABASE_URL", "REDIS_URL"),
    ),
    message="DATABASE_URL and REDIS_URL must be provided via api_secrets, not api_env.",
)
_COMMON_REGISTRY_SERVER = _var(
    "registry_server",
    "string",
    "Container registry server hostname.",
    category=TerraformVarCategory.REGISTRY,
    default="",
)
_COMMON_REGISTRY_USERNAME = _var(
    "registry_username",
    "string",
    "Container registry username.",
    category=TerraformVarCategory.REGISTRY,
    default="",
)
_COMMON_REGISTRY_PASSWORD = _var(
    "registry_password",
    "string",
    "Container registry password/token.",
    category=TerraformVarCategory.REGISTRY,
    default="",
    sensitive=True,
)

__all__ = [
    "_REQUIRED_PLACEHOLDER",
    "_clone",
    "_var",
    "_COMMON_API_ENV",
    "_COMMON_API_IMAGE",
    "_COMMON_API_SECRETS",
    "_COMMON_ENVIRONMENT",
    "_COMMON_PROJECT_NAME",
    "_COMMON_REGISTRY_PASSWORD",
    "_COMMON_REGISTRY_SERVER",
    "_COMMON_REGISTRY_USERNAME",
    "_COMMON_WEB_ENV",
    "_COMMON_WEB_IMAGE",
    "_COMMON_WEB_SECRETS",
    "_COMMON_API_ENV_DISALLOW_SECRETS_VALIDATION",
]
