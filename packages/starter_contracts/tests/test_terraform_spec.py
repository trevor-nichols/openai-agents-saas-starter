"""Tests for Terraform export specifications."""

from __future__ import annotations

from pathlib import Path

from starter_contracts.infra.terraform_spec import (
    TerraformProvider,
    get_provider_spec,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def _variable_names(path: Path) -> set[str]:
    names: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith('variable "'):
            continue
        name = stripped.split('"', 2)[1]
        names.add(name)
    return names


def _assert_spec_matches(provider: TerraformProvider, variables_path: Path) -> None:
    spec = get_provider_spec(provider)
    spec_names = {variable.name for variable in spec.variables}
    tf_names = _variable_names(variables_path)
    assert spec_names == tf_names, (
        f"{provider.value} spec drift: "
        f"missing={sorted(tf_names - spec_names)} "
        f"extra={sorted(spec_names - tf_names)}"
    )


def test_terraform_spec_aws_matches_variables() -> None:
    _assert_spec_matches(
        TerraformProvider.AWS,
        REPO_ROOT / "ops" / "infra" / "aws" / "variables.tf",
    )


def test_terraform_spec_azure_matches_variables() -> None:
    _assert_spec_matches(
        TerraformProvider.AZURE,
        REPO_ROOT / "ops" / "infra" / "azure" / "variables.tf",
    )


def test_terraform_spec_gcp_matches_variables() -> None:
    _assert_spec_matches(
        TerraformProvider.GCP,
        REPO_ROOT / "ops" / "infra" / "gcp" / "variables.tf",
    )


def _rule_with_any_of(spec, token: str):
    return next(rule for rule in spec.requirements if token in rule.any_of)


def test_aws_requires_signing_secret_aliases() -> None:
    spec = get_provider_spec(TerraformProvider.AWS)
    rule = _rule_with_any_of(spec, "aws_sm_signing_secret_arn")
    assert "api_env.AWS_SM_SIGNING_SECRET_ARN" in rule.any_of
    assert "api_secrets.AWS_SM_SIGNING_SECRET_ARN" in rule.any_of


def test_azure_requires_signing_secret_aliases() -> None:
    spec = get_provider_spec(TerraformProvider.AZURE)
    rule = _rule_with_any_of(spec, "auth_signing_secret_name")
    assert "api_env.AZURE_KV_SIGNING_SECRET_NAME" in rule.any_of
    assert "api_secrets.AZURE_KV_SIGNING_SECRET_NAME" in rule.any_of


def test_azure_requires_auth_key_aliases() -> None:
    spec = get_provider_spec(TerraformProvider.AZURE)
    rule = _rule_with_any_of(spec, "auth_key_secret_name")
    assert "api_env.AUTH_KEY_SECRET_NAME" in rule.any_of
    assert "api_secrets.AUTH_KEY_SECRET_NAME" in rule.any_of


def test_gcp_requires_signing_secret_aliases() -> None:
    spec = get_provider_spec(TerraformProvider.GCP)
    rule = _rule_with_any_of(spec, "gcp_sm_signing_secret_name")
    assert "api_env.GCP_SM_SIGNING_SECRET_NAME" in rule.any_of
    assert "api_secrets.GCP_SM_SIGNING_SECRET_NAME" in rule.any_of


def test_gcp_requires_auth_key_aliases() -> None:
    spec = get_provider_spec(TerraformProvider.GCP)
    rule = _rule_with_any_of(spec, "auth_key_secret_name")
    assert "api_env.AUTH_KEY_SECRET_NAME" in rule.any_of
    assert "api_secrets.AUTH_KEY_SECRET_NAME" in rule.any_of


def test_api_env_disallows_database_keys_for_all_providers() -> None:
    expected = "DATABASE_URL and REDIS_URL must be provided via api_secrets, not api_env."
    for provider in TerraformProvider:
        spec = get_provider_spec(provider)
        messages = {rule.message for rule in spec.validations}
        assert expected in messages
