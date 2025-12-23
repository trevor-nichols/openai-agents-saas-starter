from __future__ import annotations

from starter_cli.workflows.secrets.models import SecretsWorkflowOptions
from starter_cli.workflows.secrets.providers import infisical

from tests.unit.support.stubs import StubInputProvider


def test_infisical_cloud_validates_secret(cli_ctx, monkeypatch) -> None:
    ctx = cli_ctx
    ctx.settings = None
    monkeypatch.setattr(infisical, "_probe_infisical_secret", lambda **_: True)
    provider = StubInputProvider(
        strings={
            "INFISICAL_BASE_URL": "https://cloud.example",
            "INFISICAL_PROJECT_ID": "proj",
            "INFISICAL_ENVIRONMENT": "dev",
            "INFISICAL_SECRET_PATH": "/backend",
            "INFISICAL_SIGNING_SECRET_NAME": "auth-secret",
        },
        secrets={"INFISICAL_SERVICE_TOKEN": "st-service"},
    )

    result = infisical.run_infisical_cloud(
        ctx,
        provider,
        options=SecretsWorkflowOptions(),
    )

    assert result.env_updates["SECRETS_PROVIDER"] == "infisical_cloud"
    assert result.steps[0].startswith("Validated")
    assert not result.warnings


def test_infisical_self_hosted_warns_when_probe_fails(cli_ctx, monkeypatch) -> None:
    ctx = cli_ctx
    ctx.settings = None
    monkeypatch.setattr(infisical, "_probe_infisical_secret", lambda **_: False)
    provider = StubInputProvider(
        strings={
            "INFISICAL_BASE_URL": "http://internal",
            "INFISICAL_PROJECT_ID": "proj",
            "INFISICAL_ENVIRONMENT": "dev",
            "INFISICAL_SECRET_PATH": "/backend",
            "INFISICAL_SIGNING_SECRET_NAME": "auth-secret",
            "INFISICAL_CA_BUNDLE_PATH": "/tmp/ca.pem",
        },
        secrets={"INFISICAL_SERVICE_TOKEN": "st-service"},
    )

    result = infisical.run_infisical_self_hosted(
        ctx,
        provider,
        options=SecretsWorkflowOptions(),
    )

    assert result.env_updates["INFISICAL_CA_BUNDLE_PATH"] == "/tmp/ca.pem"
    assert result.env_updates["SECRETS_PROVIDER"] == "infisical_self_host"
    assert result.warnings
