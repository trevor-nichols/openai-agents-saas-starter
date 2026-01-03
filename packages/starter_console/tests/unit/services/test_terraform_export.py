from __future__ import annotations

from typing import cast

import pytest

from starter_console.services.infra.terraform_export import (
    TerraformExportError,
    TerraformExportMode,
    TerraformExportOptions,
    build_export,
)
from starter_contracts.infra.terraform_spec import TerraformProvider


def _assert_validation_error(
    provider: TerraformProvider,
    overrides: dict[str, object],
    expected_message: str,
) -> None:
    options = TerraformExportOptions(
        provider=provider,
        mode=TerraformExportMode.FILLED,
    )
    with pytest.raises(TerraformExportError) as exc:
        build_export(options=options, overrides=overrides)
    assert expected_message in str(exc.value)


def _aws_base_overrides() -> dict[str, object]:
    return {
        "project_name": "starter",
        "environment": "prod",
        "api_image": "example.com/api:latest",
        "web_image": "example.com/web:latest",
        "db_password": "super-secret",
        "storage_bucket_name": "starter-assets",
        "api_secrets": {"DATABASE_URL": "db-secret", "REDIS_URL": "redis-secret"},
        "enable_https": False,
        "redis_require_auth_token": False,
        "secrets_provider": "aws_sm",
        "aws_sm_signing_secret_arn": "arn:aws:secretsmanager:us-east-1:123:secret:sign",
        "auth_key_secret_arn": "arn:aws:secretsmanager:us-east-1:123:secret:keyset",
    }


def _azure_base_overrides() -> dict[str, object]:
    return {
        "project_name": "starter",
        "environment": "prod",
        "api_image": "example.com/api:latest",
        "web_image": "example.com/web:latest",
        "db_admin_password": "super-secret",
        "storage_account_name": "starterassets",
        "key_vault_name": "starter-kv",
        "log_analytics_name": "starter-logs",
        "api_secrets": {"DATABASE_URL": "db-secret", "REDIS_URL": "redis-secret"},
        "auth_signing_secret_name": "signing-secret",
        "auth_key_secret_name": "auth-key",
    }


def _gcp_base_overrides() -> dict[str, object]:
    return {
        "project_name": "starter",
        "environment": "prod",
        "project_id": "starter-project",
        "api_image": "example.com/api:latest",
        "web_image": "example.com/web:latest",
        "api_base_url": "https://api.example.com",
        "app_public_url": "https://app.example.com",
        "db_password": "super-secret",
        "api_secrets": {"DATABASE_URL": "db-secret", "REDIS_URL": "redis-secret"},
        "gcp_sm_signing_secret_name": "signing-secret",
        "auth_key_secret_name": "auth-key",
    }


def test_template_mode_includes_placeholders() -> None:
    options = TerraformExportOptions(
        provider=TerraformProvider.AWS,
        mode=TerraformExportMode.TEMPLATE,
    )
    result = build_export(options=options)
    assert result.values["project_name"] == "__REQUIRED__"
    assert result.values["environment"] == "__REQUIRED__"
    assert result.values["api_image"] == "__REQUIRED__"
    assert result.values["web_image"] == "__REQUIRED__"
    assert result.values["db_password"] == "__REQUIRED__"
    assert result.values["storage_bucket_name"] == "__REQUIRED__"
    assert result.values["api_secrets"] == {
        "DATABASE_URL": "__REQUIRED__",
        "REDIS_URL": "__REQUIRED__",
    }


def test_redacts_sensitive_values_when_disabled() -> None:
    options = TerraformExportOptions(
        provider=TerraformProvider.AWS,
        mode=TerraformExportMode.TEMPLATE,
        include_secrets=False,
    )
    overrides = {
        "project_name": "starter",
        "environment": "prod",
        "api_image": "example.com/api:latest",
        "web_image": "example.com/web:latest",
        "db_password": "super-secret",
        "storage_bucket_name": "starter-assets",
        "api_secrets": {"DATABASE_URL": "db-secret", "REDIS_URL": "redis-secret"},
    }
    result = build_export(options=options, overrides=overrides)
    assert result.values["db_password"] == "__REDACTED__"
    api_secrets = cast(dict[str, str], result.values["api_secrets"])
    assert api_secrets["DATABASE_URL"] == "__REDACTED__"
    assert api_secrets["REDIS_URL"] == "__REDACTED__"


def test_filled_mode_requires_inputs() -> None:
    options = TerraformExportOptions(
        provider=TerraformProvider.AWS,
        mode=TerraformExportMode.FILLED,
    )
    with pytest.raises(TerraformExportError):
        build_export(options=options)


def test_filled_mode_accepts_minimal_inputs() -> None:
    options = TerraformExportOptions(
        provider=TerraformProvider.AWS,
        mode=TerraformExportMode.FILLED,
    )
    overrides = {
        "project_name": "starter",
        "environment": "prod",
        "api_image": "example.com/api:latest",
        "web_image": "example.com/web:latest",
        "db_password": "super-secret",
        "storage_bucket_name": "starter-assets",
        "api_secrets": {"DATABASE_URL": "db-secret", "REDIS_URL": "redis-secret"},
        "enable_https": False,
        "redis_require_auth_token": False,
        "secrets_provider": "vault_hcp",
        "auth_key_secret_name": "auth-key",
    }
    result = build_export(options=options, overrides=overrides)
    assert "project_name" in result.values


def test_filled_mode_accepts_signing_secret_via_api_env() -> None:
    options = TerraformExportOptions(
        provider=TerraformProvider.AWS,
        mode=TerraformExportMode.FILLED,
    )
    overrides = {
        "project_name": "starter",
        "environment": "prod",
        "api_image": "example.com/api:latest",
        "web_image": "example.com/web:latest",
        "db_password": "super-secret",
        "storage_bucket_name": "starter-assets",
        "api_secrets": {"DATABASE_URL": "db-secret", "REDIS_URL": "redis-secret"},
        "enable_https": False,
        "redis_require_auth_token": False,
        "secrets_provider": "aws_sm",
        "auth_key_secret_arn": "arn:aws:secretsmanager:us-east-1:123:secret:keyset",
        "api_env": {"AWS_SM_SIGNING_SECRET_ARN": "arn:aws:secretsmanager:us-east-1:123:secret:sign"},
    }
    result = build_export(options=options, overrides=overrides)
    assert "aws_sm_signing_secret_arn" not in result.values


def test_filled_mode_rejects_empty_signing_secret_key() -> None:
    options = TerraformExportOptions(
        provider=TerraformProvider.AWS,
        mode=TerraformExportMode.FILLED,
    )
    overrides = {
        "project_name": "starter",
        "environment": "prod",
        "api_image": "example.com/api:latest",
        "web_image": "example.com/web:latest",
        "db_password": "super-secret",
        "storage_bucket_name": "starter-assets",
        "api_secrets": {"DATABASE_URL": "db-secret", "REDIS_URL": "redis-secret"},
        "enable_https": False,
        "redis_require_auth_token": False,
        "secrets_provider": "aws_sm",
        "auth_key_secret_arn": "arn:aws:secretsmanager:us-east-1:123:secret:keyset",
        "api_env": {"AWS_SM_SIGNING_SECRET_ARN": ""},
    }
    with pytest.raises(TerraformExportError) as exc:
        build_export(options=options, overrides=overrides)
    assert (
        "Provide aws_sm_signing_secret_arn or AWS_SM_SIGNING_SECRET_ARN via "
        "api_env/api_secrets when secrets_provider=aws_sm."
        in str(exc.value)
    )


def test_aws_accepts_whitespace_redis_auth_token() -> None:
    overrides = {
        **_aws_base_overrides(),
        "redis_require_auth_token": True,
        "redis_auth_token": "   ",
    }
    options = TerraformExportOptions(
        provider=TerraformProvider.AWS,
        mode=TerraformExportMode.FILLED,
        include_secrets=True,
    )
    result = build_export(options=options, overrides=overrides)
    assert "redis_auth_token" in result.values


def test_aws_requires_registry_credentials_when_registry_server_whitespace() -> None:
    overrides = {**_aws_base_overrides(), "registry_server": "   "}
    _assert_validation_error(
        TerraformProvider.AWS,
        overrides,
        "registry_username",
    )


def test_aws_rejects_api_env_database_keys() -> None:
    overrides = {
        **_aws_base_overrides(),
        "api_env": {"DATABASE_URL": "postgres://example"},
    }
    _assert_validation_error(
        TerraformProvider.AWS,
        overrides,
        "DATABASE_URL and REDIS_URL must be provided via api_secrets, not api_env.",
    )


def test_azure_rejects_storage_provider_override() -> None:
    overrides = {**_azure_base_overrides(), "storage_provider": "s3"}
    _assert_validation_error(
        TerraformProvider.AZURE,
        overrides,
        'storage_provider must be "azure_blob" for the Azure blueprint.',
    )


def test_aws_rejects_storage_provider_override() -> None:
    overrides = {**_aws_base_overrides(), "storage_provider": "gcs"}
    _assert_validation_error(
        TerraformProvider.AWS,
        overrides,
        'storage_provider must be "s3" for the AWS blueprint.',
    )


def test_azure_rejects_basic_redis_sku_with_private_networking() -> None:
    overrides = {
        **_azure_base_overrides(),
        "enable_private_networking": True,
        "redis_sku_name": "Basic",
    }
    _assert_validation_error(
        TerraformProvider.AZURE,
        overrides,
        "redis_sku_name must be Standard or Premium when enable_private_networking=true.",
    )


def test_azure_rejects_api_env_database_keys() -> None:
    overrides = {
        **_azure_base_overrides(),
        "api_env": {"REDIS_URL": "redis://example"},
    }
    _assert_validation_error(
        TerraformProvider.AZURE,
        overrides,
        "DATABASE_URL and REDIS_URL must be provided via api_secrets, not api_env.",
    )


def test_gcp_rejects_private_service_cidr_prefix_out_of_range() -> None:
    overrides = {**_gcp_base_overrides(), "private_service_cidr_prefix": 12}
    _assert_validation_error(
        TerraformProvider.GCP,
        overrides,
        "private_service_cidr_prefix must be between 16 and 24.",
    )


def test_gcp_rejects_api_instance_bounds() -> None:
    overrides = {
        **_gcp_base_overrides(),
        "api_min_instances": 5,
        "api_max_instances": 1,
    }
    _assert_validation_error(
        TerraformProvider.GCP,
        overrides,
        "api_max_instances must be >= api_min_instances.",
    )


def test_gcp_rejects_storage_provider_override() -> None:
    overrides = {**_gcp_base_overrides(), "storage_provider": "s3"}
    _assert_validation_error(
        TerraformProvider.GCP,
        overrides,
        'storage_provider must be "gcs" for the GCP blueprint.',
    )


def test_gcp_rejects_db_availability_type() -> None:
    overrides = {**_gcp_base_overrides(), "db_availability_type": "invalid"}
    _assert_validation_error(
        TerraformProvider.GCP,
        overrides,
        "db_availability_type must be ZONAL or REGIONAL.",
    )


def test_gcp_requires_public_ipv4_when_private_access_disabled() -> None:
    overrides = {
        **_gcp_base_overrides(),
        "enable_private_service_access": False,
        "db_public_ipv4_enabled": False,
    }
    _assert_validation_error(
        TerraformProvider.GCP,
        overrides,
        "db_public_ipv4_enabled must be true when enable_private_service_access=false.",
    )


def test_gcp_rejects_redis_tier() -> None:
    overrides = {**_gcp_base_overrides(), "redis_tier": "fast"}
    _assert_validation_error(
        TerraformProvider.GCP,
        overrides,
        "redis_tier must be BASIC or STANDARD_HA.",
    )


def test_gcp_rejects_redis_memory_too_small() -> None:
    overrides = {**_gcp_base_overrides(), "redis_memory_size_gb": 0}
    _assert_validation_error(
        TerraformProvider.GCP,
        overrides,
        "redis_memory_size_gb must be at least 1.",
    )


def test_gcp_rejects_redis_transit_encryption_mode() -> None:
    overrides = {**_gcp_base_overrides(), "redis_transit_encryption_mode": "UNKNOWN"}
    _assert_validation_error(
        TerraformProvider.GCP,
        overrides,
        "redis_transit_encryption_mode must be SERVER_AUTHENTICATION or DISABLED.",
    )


def test_gcp_rejects_api_env_database_keys() -> None:
    overrides = {
        **_gcp_base_overrides(),
        "api_env": {"DATABASE_URL": "postgres://example"},
    }
    _assert_validation_error(
        TerraformProvider.GCP,
        overrides,
        "DATABASE_URL and REDIS_URL must be provided via api_secrets, not api_env.",
    )


def test_extra_vars_rejects_case_insensitive_collisions() -> None:
    options = TerraformExportOptions(provider=TerraformProvider.AWS)
    with pytest.raises(TerraformExportError) as exc:
        build_export(options=options, extra_vars={"Project_Name": "override"})
    assert "extra_vars cannot override known variable" in str(exc.value)


def test_extra_vars_rejects_duplicate_keys_case_insensitively() -> None:
    options = TerraformExportOptions(provider=TerraformProvider.AWS)
    with pytest.raises(TerraformExportError) as exc:
        build_export(options=options, extra_vars={"CustomFlag": "1", "customflag": "2"})
    assert "extra_vars defines" in str(exc.value)
