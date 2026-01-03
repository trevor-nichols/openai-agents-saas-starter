"""AWS Terraform variable definitions."""

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
    TerraformRequirementRule,
    TerraformStringPresence,
    TerraformValidationRule,
    TerraformVarCategory,
)

_AWS_REGISTRY_USERNAME = _clone(
    _COMMON_REGISTRY_USERNAME,
    required_when=(TerraformCondition(key="registry_server", present=True, trim_whitespace=False),),
)
_AWS_REGISTRY_PASSWORD = _clone(
    _COMMON_REGISTRY_PASSWORD,
    required_when=(TerraformCondition(key="registry_server", present=True, trim_whitespace=False),),
)

AWS_VARIABLES = (
    _COMMON_PROJECT_NAME,
    _COMMON_ENVIRONMENT,
    _var(
        "region",
        "string",
        "AWS region for all resources.",
        category=TerraformVarCategory.CORE,
        default="us-east-1",
        env_aliases=("AWS_REGION",),
    ),
    _var(
        "vpc_cidr",
        "string",
        "CIDR block for the VPC.",
        category=TerraformVarCategory.NETWORK,
        default="10.20.0.0/16",
        advanced=True,
    ),
    _COMMON_API_IMAGE,
    _COMMON_WEB_IMAGE,
    _var(
        "api_base_url",
        "string",
        (
            "Optional public API base URL (e.g., https://api.example.com). "
            "Defaults to the API ALB URL."
        ),
        category=TerraformVarCategory.URLS,
        default="",
        env_aliases=("API_BASE_URL",),
    ),
    _var(
        "app_public_url",
        "string",
        "Optional public web URL (e.g., https://app.example.com). Defaults to the web ALB URL.",
        category=TerraformVarCategory.URLS,
        default="",
        env_aliases=("APP_PUBLIC_URL",),
    ),
    _var(
        "secrets_provider",
        "string",
        "Secrets provider used by the API service (SECRETS_PROVIDER).",
        category=TerraformVarCategory.SECRETS,
        default="aws_sm",
        env_aliases=("SECRETS_PROVIDER",),
    ),
    _var(
        "aws_sm_signing_secret_arn",
        "string",
        "Secrets Manager ARN for the signing secret used by service-account issuance.",
        category=TerraformVarCategory.SECRETS,
        default="",
        env_aliases=("AWS_SM_SIGNING_SECRET_ARN",),
    ),
    _var(
        "auth_key_secret_arn",
        "string",
        "Secrets Manager ARN for the Ed25519 keyset JSON (AUTH_KEY_SECRET_NAME).",
        category=TerraformVarCategory.SECRETS,
        default="",
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
    _var(
        "auth_key_secret_name",
        "string",
        "Secret-manager key/path for the Ed25519 keyset JSON (AUTH_KEY_SECRET_NAME).",
        category=TerraformVarCategory.SECRETS,
        default="",
        env_aliases=("AUTH_KEY_SECRET_NAME",),
    ),
    _COMMON_REGISTRY_SERVER,
    _AWS_REGISTRY_USERNAME,
    _AWS_REGISTRY_PASSWORD,
    _var(
        "api_cpu",
        "number",
        "CPU units for the API task definition.",
        category=TerraformVarCategory.COMPUTE,
        default=512,
    ),
    _var(
        "api_memory",
        "number",
        "Memory (MiB) for the API task definition.",
        category=TerraformVarCategory.COMPUTE,
        default=1024,
    ),
    _var(
        "web_cpu",
        "number",
        "CPU units for the web task definition.",
        category=TerraformVarCategory.COMPUTE,
        default=512,
    ),
    _var(
        "web_memory",
        "number",
        "Memory (MiB) for the web task definition.",
        category=TerraformVarCategory.COMPUTE,
        default=1024,
    ),
    _var(
        "api_desired_count",
        "number",
        "Desired task count for the API service.",
        category=TerraformVarCategory.SCALING,
        default=1,
    ),
    _var(
        "web_desired_count",
        "number",
        "Desired task count for the web service.",
        category=TerraformVarCategory.SCALING,
        default=1,
    ),
    _var(
        "db_instance_class",
        "string",
        "RDS instance class for Postgres.",
        category=TerraformVarCategory.DATABASE,
        default="db.t4g.micro",
        advanced=True,
    ),
    _var(
        "db_allocated_storage",
        "number",
        "Allocated storage (GiB) for Postgres.",
        category=TerraformVarCategory.DATABASE,
        default=20,
        advanced=True,
    ),
    _var(
        "db_backup_retention_days",
        "number",
        "Backup retention (days) for Postgres.",
        category=TerraformVarCategory.DATABASE,
        default=7,
        advanced=True,
    ),
    _var(
        "db_storage_encrypted",
        "bool",
        "Enable storage encryption at rest for Postgres.",
        category=TerraformVarCategory.DATABASE,
        default=True,
        advanced=True,
    ),
    _var(
        "db_deletion_protection",
        "bool",
        "Enable deletion protection for Postgres.",
        category=TerraformVarCategory.DATABASE,
        default=True,
        advanced=True,
    ),
    _var(
        "db_skip_final_snapshot",
        "bool",
        "Skip final snapshot on destroy (useful for dev only).",
        category=TerraformVarCategory.DATABASE,
        default=False,
        advanced=True,
    ),
    _var(
        "db_publicly_accessible",
        "bool",
        "Expose Postgres to the public internet (not recommended).",
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
        "db_username",
        "string",
        "Postgres master username.",
        category=TerraformVarCategory.DATABASE,
        default="agent_admin",
    ),
    _var(
        "db_password",
        "string",
        "Postgres master password.",
        category=TerraformVarCategory.DATABASE,
        required=True,
        sensitive=True,
        template_value=_REQUIRED_PLACEHOLDER,
    ),
    _var(
        "redis_node_type",
        "string",
        "ElastiCache node type.",
        category=TerraformVarCategory.REDIS,
        default="cache.t4g.micro",
        advanced=True,
    ),
    _var(
        "redis_transit_encryption_enabled",
        "bool",
        "Enable in-transit encryption (TLS) for Redis.",
        category=TerraformVarCategory.REDIS,
        default=True,
        advanced=True,
    ),
    _var(
        "redis_at_rest_encryption_enabled",
        "bool",
        "Enable at-rest encryption for Redis.",
        category=TerraformVarCategory.REDIS,
        default=True,
        advanced=True,
    ),
    _var(
        "redis_require_auth_token",
        "bool",
        "Require a Redis AUTH token (recommended).",
        category=TerraformVarCategory.REDIS,
        default=True,
        advanced=True,
    ),
    _var(
        "redis_auth_token",
        "string",
        "Redis AUTH token (required when redis_require_auth_token=true).",
        category=TerraformVarCategory.REDIS,
        default="",
        sensitive=True,
        template_value=_REQUIRED_PLACEHOLDER,
        required_when=(TerraformCondition(key="redis_require_auth_token", truthy=True),),
        string_presence=TerraformStringPresence.RAW,
    ),
    _var(
        "storage_bucket_name",
        "string",
        "Storage bucket name for object storage.",
        category=TerraformVarCategory.STORAGE,
        required=True,
        env_aliases=("S3_BUCKET",),
        template_value=_REQUIRED_PLACEHOLDER,
    ),
    _var(
        "storage_provider",
        "string",
        "Storage provider for the API service (STORAGE_PROVIDER).",
        category=TerraformVarCategory.STORAGE,
        default="s3",
        env_aliases=("STORAGE_PROVIDER",),
    ),
    _var(
        "create_s3_bucket",
        "bool",
        "Whether to manage the S3 bucket in this stack.",
        category=TerraformVarCategory.STORAGE,
        default=True,
        advanced=True,
    ),
    _var(
        "s3_block_public_access",
        "bool",
        "Block all public access to the S3 bucket.",
        category=TerraformVarCategory.STORAGE,
        default=True,
        advanced=True,
    ),
    _var(
        "s3_enable_encryption",
        "bool",
        "Enable default server-side encryption for the S3 bucket.",
        category=TerraformVarCategory.STORAGE,
        default=True,
        advanced=True,
    ),
    _var(
        "s3_kms_key_id",
        "string",
        "Optional KMS key ID for S3 bucket encryption (defaults to SSE-S3).",
        category=TerraformVarCategory.STORAGE,
        default="",
        advanced=True,
    ),
    _var(
        "s3_enable_versioning",
        "bool",
        "Enable S3 bucket versioning.",
        category=TerraformVarCategory.STORAGE,
        default=True,
        advanced=True,
    ),
    _var(
        "enable_https",
        "bool",
        "Whether to enable HTTPS listeners on the ALBs.",
        category=TerraformVarCategory.SECURITY,
        default=True,
        advanced=True,
    ),
    _var(
        "acm_certificate_arn",
        "string",
        "ACM certificate ARN for HTTPS. Required when enable_https=true.",
        category=TerraformVarCategory.SECURITY,
        default=None,
        required_when=(TerraformCondition(key="enable_https", truthy=True),),
    ),
    _clone(_COMMON_API_ENV, description="Additional environment variables for the API container."),
    _clone(_COMMON_WEB_ENV, description="Additional environment variables for the web container."),
    _clone(
        _COMMON_API_SECRETS,
        description="Map of API env var name to AWS Secrets Manager secret ARN.",
    ),
    _clone(
        _COMMON_WEB_SECRETS,
        description="Map of web env var name to AWS Secrets Manager secret ARN.",
    ),
)

AWS_REQUIREMENTS = (
    TerraformRequirementRule(
        when=(TerraformCondition(key="secrets_provider", any_of=("aws_sm",)),),
        any_of=(
            "aws_sm_signing_secret_arn",
            "api_env.AWS_SM_SIGNING_SECRET_ARN",
            "api_secrets.AWS_SM_SIGNING_SECRET_ARN",
        ),
        message=(
            "Provide aws_sm_signing_secret_arn or AWS_SM_SIGNING_SECRET_ARN via "
            "api_env/api_secrets when secrets_provider=aws_sm."
        ),
    ),
    TerraformRequirementRule(
        when=(
            TerraformCondition(
                key="auth_key_storage_provider",
                any_of=("aws_sm",),
                fallback_key="secrets_provider",
            ),
        ),
        any_of=("auth_key_secret_arn", "auth_key_secret_name"),
        message=(
            "Provide auth_key_secret_arn or auth_key_secret_name when "
            "auth_key_storage_provider=aws_sm."
        ),
    ),
    TerraformRequirementRule(
        when=(
            TerraformCondition(
                key="auth_key_storage_provider",
                none_of=("aws_sm",),
                fallback_key="secrets_provider",
            ),
        ),
        any_of=(
            "auth_key_secret_name",
            "api_env.AUTH_KEY_SECRET_NAME",
            "api_secrets.AUTH_KEY_SECRET_NAME",
        ),
        message=(
            "auth_key_secret_name is required when auth_key_storage_provider is not "
            "aws_sm (or provide AUTH_KEY_SECRET_NAME via api_env/api_secrets)."
        ),
    ),
)

AWS_VALIDATIONS = (
    _COMMON_API_ENV_DISALLOW_SECRETS_VALIDATION,
    TerraformValidationRule(
        when=(),
        check=TerraformAllowedValuesCheck(
            key="storage_provider",
            allowed=("s3",),
        ),
        message='storage_provider must be "s3" for the AWS blueprint.',
    ),
)

__all__ = ["AWS_REQUIREMENTS", "AWS_VALIDATIONS", "AWS_VARIABLES"]
