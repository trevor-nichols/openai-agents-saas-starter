"""Azure Terraform variable definitions."""

from __future__ import annotations

from .common import (
    _COMMON_API_ENV,
    _COMMON_API_ENV_DISALLOW_SECRETS_VALIDATION,
    _COMMON_API_IMAGE,
    _COMMON_API_SECRETS,
    _COMMON_ENVIRONMENT,
    _COMMON_PROJECT_NAME,
    _COMMON_REGISTRY_PASSWORD,
    _COMMON_REGISTRY_SERVER,
    _COMMON_REGISTRY_USERNAME,
    _COMMON_WEB_ENV,
    _COMMON_WEB_IMAGE,
    _COMMON_WEB_SECRETS,
    _REQUIRED_PLACEHOLDER,
    _clone,
    _var,
)
from .models import (
    TerraformAllowedValuesCheck,
    TerraformCondition,
    TerraformDisallowedValuesCheck,
    TerraformRequirementRule,
    TerraformValidationRule,
    TerraformVarCategory,
)

_AZURE_REGISTRY_USERNAME = _clone(
    _COMMON_REGISTRY_USERNAME,
    required_when=(TerraformCondition(key="registry_server", present=True, trim_whitespace=False),),
)

AZURE_VARIABLES = (
    _COMMON_PROJECT_NAME,
    _COMMON_ENVIRONMENT,
    _var(
        "region",
        "string",
        "Azure region.",
        category=TerraformVarCategory.CORE,
        default="eastus",
    ),
    _var(
        "enable_private_networking",
        "bool",
        "Enable private networking for database/redis via VNet + private endpoints.",
        category=TerraformVarCategory.NETWORK,
        default=True,
        advanced=True,
    ),
    _var(
        "vnet_address_space",
        "string",
        "Address space for the VNet.",
        category=TerraformVarCategory.NETWORK,
        default="10.30.0.0/16",
        advanced=True,
    ),
    _var(
        "containerapps_subnet_cidr",
        "string",
        "CIDR for the Container Apps infrastructure subnet.",
        category=TerraformVarCategory.NETWORK,
        default="10.30.0.0/23",
        advanced=True,
    ),
    _var(
        "postgres_subnet_cidr",
        "string",
        "CIDR for the Postgres delegated subnet.",
        category=TerraformVarCategory.NETWORK,
        default="10.30.2.0/24",
        advanced=True,
    ),
    _var(
        "private_endpoints_subnet_cidr",
        "string",
        "CIDR for the private endpoints subnet.",
        category=TerraformVarCategory.NETWORK,
        default="10.30.3.0/24",
        advanced=True,
    ),
    _COMMON_API_IMAGE,
    _COMMON_WEB_IMAGE,
    _var(
        "secrets_provider",
        "string",
        "Secrets provider used by the API service (SECRETS_PROVIDER).",
        category=TerraformVarCategory.SECRETS,
        default="azure_kv",
        env_aliases=("SECRETS_PROVIDER",),
    ),
    _var(
        "api_base_url",
        "string",
        "Public API base URL for the web app (e.g. https://api.example.com).",
        category=TerraformVarCategory.URLS,
        default="",
        env_aliases=("API_BASE_URL",),
    ),
    _var(
        "app_public_url",
        "string",
        "Public web URL used by the API service (e.g. https://app.example.com).",
        category=TerraformVarCategory.URLS,
        default="",
        env_aliases=("APP_PUBLIC_URL",),
    ),
    _COMMON_REGISTRY_SERVER,
    _AZURE_REGISTRY_USERNAME,
    _COMMON_REGISTRY_PASSWORD,
    _var(
        "registry_password_secret_id",
        "string",
        "Key Vault secret ID containing the registry password/token.",
        category=TerraformVarCategory.REGISTRY,
        default="",
    ),
    _var(
        "api_cpu",
        "number",
        "CPU cores for the API container.",
        category=TerraformVarCategory.COMPUTE,
        default=1,
    ),
    _var(
        "api_memory",
        "string",
        "Memory for the API container (Gi).",
        category=TerraformVarCategory.COMPUTE,
        default="2Gi",
    ),
    _var(
        "web_cpu",
        "number",
        "CPU cores for the web container.",
        category=TerraformVarCategory.COMPUTE,
        default=1,
    ),
    _var(
        "web_memory",
        "string",
        "Memory for the web container (Gi).",
        category=TerraformVarCategory.COMPUTE,
        default="2Gi",
    ),
    _var(
        "db_admin_username",
        "string",
        "Postgres admin username.",
        category=TerraformVarCategory.DATABASE,
        default="agent_admin",
    ),
    _var(
        "db_admin_password",
        "string",
        "Postgres admin password.",
        category=TerraformVarCategory.DATABASE,
        required=True,
        sensitive=True,
        template_value=_REQUIRED_PLACEHOLDER,
    ),
    _var(
        "db_public_network_access_enabled",
        "bool",
        "Allow public network access to Postgres (not recommended).",
        category=TerraformVarCategory.DATABASE,
        default=False,
        advanced=True,
    ),
    _var(
        "db_name",
        "string",
        "Postgres database name.",
        category=TerraformVarCategory.DATABASE,
        default="agent_app",
    ),
    _var(
        "redis_sku_name",
        "string",
        "Redis SKU name.",
        category=TerraformVarCategory.REDIS,
        default="Standard",
        advanced=True,
    ),
    _var(
        "redis_capacity",
        "number",
        "Redis capacity tier.",
        category=TerraformVarCategory.REDIS,
        default=0,
        advanced=True,
    ),
    _var(
        "redis_public_network_access_enabled",
        "bool",
        "Allow public network access to Redis (not recommended).",
        category=TerraformVarCategory.REDIS,
        default=False,
        advanced=True,
    ),
    _var(
        "storage_account_name",
        "string",
        "Storage account name for Blob storage (must be globally unique).",
        category=TerraformVarCategory.STORAGE,
        required=True,
        template_value=_REQUIRED_PLACEHOLDER,
    ),
    _var(
        "storage_bucket_name",
        "string",
        "Blob container name for object storage.",
        category=TerraformVarCategory.STORAGE,
        default="assets",
        env_aliases=("AZURE_BLOB_CONTAINER",),
    ),
    _var(
        "storage_provider",
        "string",
        "Storage provider for the API service (STORAGE_PROVIDER).",
        category=TerraformVarCategory.STORAGE,
        default="azure_blob",
        env_aliases=("STORAGE_PROVIDER",),
    ),
    _var(
        "key_vault_name",
        "string",
        "Key Vault name (must be globally unique).",
        category=TerraformVarCategory.SECRETS,
        required=True,
        template_value=_REQUIRED_PLACEHOLDER,
    ),
    _var(
        "log_analytics_name",
        "string",
        "Log Analytics workspace name.",
        category=TerraformVarCategory.MISC,
        required=True,
        template_value=_REQUIRED_PLACEHOLDER,
    ),
    _var(
        "auth_signing_secret_name",
        "string",
        "Key Vault secret name containing the signing secret.",
        category=TerraformVarCategory.SECRETS,
        default="",
        env_aliases=("AZURE_KV_SIGNING_SECRET_NAME",),
    ),
    _var(
        "auth_key_secret_name",
        "string",
        "Key Vault secret name for the Ed25519 keyset JSON (AUTH_KEY_SECRET_NAME).",
        category=TerraformVarCategory.SECRETS,
        default="",
        env_aliases=("AUTH_KEY_SECRET_NAME",),
    ),
    _var(
        "auth_key_storage_provider",
        "string",
        (
            "Secrets provider used for key storage (AUTH_KEY_STORAGE_PROVIDER). "
            "Defaults to secrets_provider."
        ),
        category=TerraformVarCategory.SECRETS,
        default="",
        env_aliases=("AUTH_KEY_STORAGE_PROVIDER",),
    ),
    _clone(_COMMON_API_ENV, description="Additional environment variables for the API container."),
    _clone(_COMMON_WEB_ENV, description="Additional environment variables for the web container."),
    _clone(
        _COMMON_API_SECRETS,
        description="Map of API secret env var name to Key Vault secret ID.",
    ),
    _clone(
        _COMMON_WEB_SECRETS,
        description="Map of web secret env var name to Key Vault secret ID.",
    ),
)

AZURE_REQUIREMENTS = (
    TerraformRequirementRule(
        when=(TerraformCondition(key="secrets_provider", any_of=("azure_kv",)),),
        any_of=(
            "auth_signing_secret_name",
            "api_env.AZURE_KV_SIGNING_SECRET_NAME",
            "api_secrets.AZURE_KV_SIGNING_SECRET_NAME",
        ),
        message=(
            "auth_signing_secret_name is required when secrets_provider=azure_kv "
            "(or provide AZURE_KV_SIGNING_SECRET_NAME via api_env/api_secrets)."
        ),
    ),
    TerraformRequirementRule(
        when=(),
        any_of=(
            "auth_key_secret_name",
            "api_env.AUTH_KEY_SECRET_NAME",
            "api_secrets.AUTH_KEY_SECRET_NAME",
        ),
        message=(
            "auth_key_secret_name is required for secret-manager key storage "
            "(or provide AUTH_KEY_SECRET_NAME via api_env/api_secrets)."
        ),
    ),
    TerraformRequirementRule(
        when=(TerraformCondition(key="registry_server", present=True, trim_whitespace=False),),
        any_of=("registry_password", "registry_password_secret_id"),
        message=(
            "registry_password or registry_password_secret_id is required when "
            "registry_server is set."
        ),
    ),
)

AZURE_VALIDATIONS = (
    _COMMON_API_ENV_DISALLOW_SECRETS_VALIDATION,
    TerraformValidationRule(
        when=(),
        check=TerraformAllowedValuesCheck(
            key="storage_provider",
            allowed=("azure_blob",),
        ),
        message='storage_provider must be "azure_blob" for the Azure blueprint.',
    ),
    TerraformValidationRule(
        when=(TerraformCondition(key="enable_private_networking", truthy=True),),
        check=TerraformDisallowedValuesCheck(
            key="redis_sku_name",
            disallowed=("Basic",),
        ),
        message="redis_sku_name must be Standard or Premium when enable_private_networking=true.",
    ),
)

__all__ = ["AZURE_REQUIREMENTS", "AZURE_VALIDATIONS", "AZURE_VARIABLES"]
