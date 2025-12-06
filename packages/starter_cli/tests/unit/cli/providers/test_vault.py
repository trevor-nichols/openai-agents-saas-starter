from __future__ import annotations

from types import SimpleNamespace

from starter_cli.workflows.secrets.models import SecretsWorkflowOptions
from starter_cli.workflows.secrets.providers import vault

from .._stubs import StubInputProvider


def test_run_vault_dev_collects_env(cli_ctx) -> None:
    ctx = cli_ctx
    ctx.settings = SimpleNamespace(
        vault_addr=None,
        vault_token=None,
        vault_transit_key="auth-service",
    )
    provider = StubInputProvider(
        strings={
            "VAULT_ADDR": "http://vault.dev",
            "VAULT_TRANSIT_KEY": "cli-service",
        },
        secrets={"VAULT_TOKEN": "dev-token"},
        bools={"VAULT_VERIFY_ENABLED": True},
    )

    result = vault.run_vault_dev(
        ctx,
        provider,
        options=SecretsWorkflowOptions(skip_automation=True),
    )

    assert result.env_updates == {
        "SECRETS_PROVIDER": "vault_dev",
        "VAULT_ADDR": "http://vault.dev",
        "VAULT_TOKEN": "dev-token",
        "VAULT_TRANSIT_KEY": "cli-service",
        "VAULT_VERIFY_ENABLED": "true",
    }
    assert result.steps[0].startswith("Run `just vault-up`")
    assert "Dev Vault" in result.warnings[0]


def test_run_vault_hcp_includes_namespace(cli_ctx) -> None:
    ctx = cli_ctx
    ctx.settings = SimpleNamespace(
        vault_addr="https://vault.example:8200",
        vault_namespace="admin",
        vault_token="hcp-token",
        vault_transit_key="auth-service",
    )
    provider = StubInputProvider(
        strings={
            "VAULT_ADDR": "https://vault.hcp:8200",
            "VAULT_NAMESPACE": "tenant",
            "VAULT_TRANSIT_KEY": "hcp-auth",
        },
        secrets={"VAULT_TOKEN": "hcp-token"},
        bools={"VAULT_VERIFY_ENABLED": True},
    )

    result = vault.run_vault_hcp(
        ctx,
        provider,
        options=SecretsWorkflowOptions(skip_automation=True),
    )

    assert result.env_updates["VAULT_NAMESPACE"] == "tenant"
    assert result.env_updates["SECRETS_PROVIDER"] == "vault_hcp"
    assert any("HCP Vault" in warning for warning in result.warnings)
