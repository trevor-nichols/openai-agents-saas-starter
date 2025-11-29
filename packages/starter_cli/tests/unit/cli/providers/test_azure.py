from __future__ import annotations

from starter_cli.workflows.secrets.models import SecretsWorkflowOptions
from starter_cli.workflows.secrets.providers import azure

from .._stubs import StubInputProvider


def test_azure_kv_success(cli_ctx, monkeypatch) -> None:
    ctx = cli_ctx
    ctx.settings = None
    monkeypatch.setattr(azure, "_probe_azure_secret", lambda **_: True)
    provider = StubInputProvider(
        strings={
            "AZURE_KEY_VAULT_URL": "https://vault.vault.azure.net/",
            "AZURE_KV_SIGNING_SECRET_NAME": "auth-secret",
            "AZURE_TENANT_ID": "tenant",
            "AZURE_CLIENT_ID": "client",
            "AZURE_MANAGED_IDENTITY_CLIENT_ID": "managed",
        },
        secrets={"AZURE_CLIENT_SECRET": "secret"},
    )

    result = azure.run_azure_kv(
        ctx,
        provider,
        options=SecretsWorkflowOptions(),
    )

    assert result.env_updates["SECRETS_PROVIDER"] == "azure_kv"
    assert result.env_updates["AZURE_CLIENT_SECRET"] == "secret"
    assert result.env_updates["AZURE_KV_SIGNING_SECRET_NAME"] == "auth-secret"
    assert result.env_updates["VAULT_VERIFY_ENABLED"] == "true"
    assert result.steps[0].startswith("Validated")


def test_azure_kv_warns_when_probe_fails(cli_ctx, monkeypatch) -> None:
    ctx = cli_ctx
    ctx.settings = None
    monkeypatch.setattr(azure, "_probe_azure_secret", lambda **_: False)
    provider = StubInputProvider(
        strings={
            "AZURE_KEY_VAULT_URL": "https://vault.vault.azure.net/",
            "AZURE_KV_SIGNING_SECRET_NAME": "auth-secret",
        },
    )

    result = azure.run_azure_kv(
        ctx,
        provider,
        options=SecretsWorkflowOptions(),
    )

    assert result.warnings
    assert result.env_updates["VAULT_VERIFY_ENABLED"] == "true"
