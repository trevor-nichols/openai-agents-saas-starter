from __future__ import annotations

import pytest

from starter_console.core import CLIError
from starter_console.workflows.secrets.models import SecretsWorkflowOptions
from starter_console.workflows.secrets.providers import gcp

from tests.unit.support.stubs import StubInputProvider


def test_gcp_sm_success(cli_ctx, monkeypatch) -> None:
    ctx = cli_ctx
    ctx.settings = None
    monkeypatch.setattr(gcp, "_probe_gcp_secret", lambda **_: True)
    provider = StubInputProvider(
        strings={
            "GCP_SM_PROJECT_ID": "demo-project",
            "GCP_SM_SIGNING_SECRET_NAME": "auth-signing-secret",
            "GCP_SM_CACHE_TTL_SECONDS": "90",
        }
    )

    result = gcp.run_gcp_sm(
        ctx,
        provider,
        options=SecretsWorkflowOptions(),
    )

    assert result.env_updates["SECRETS_PROVIDER"] == "gcp_sm"
    assert result.env_updates["GCP_SM_PROJECT_ID"] == "demo-project"
    assert result.env_updates["GCP_SM_SIGNING_SECRET_NAME"] == "auth-signing-secret"
    assert result.env_updates["GCP_SM_CACHE_TTL_SECONDS"] == "90"
    assert result.env_updates["VAULT_VERIFY_ENABLED"] == "true"
    assert result.steps[0].startswith("Validated")


def test_gcp_sm_warns_when_probe_fails(cli_ctx, monkeypatch) -> None:
    ctx = cli_ctx
    ctx.settings = None
    monkeypatch.setattr(gcp, "_probe_gcp_secret", lambda **_: False)
    provider = StubInputProvider(
        strings={
            "GCP_SM_PROJECT_ID": "demo-project",
            "GCP_SM_SIGNING_SECRET_NAME": "auth-signing-secret",
            "GCP_SM_CACHE_TTL_SECONDS": "60",
        }
    )

    result = gcp.run_gcp_sm(
        ctx,
        provider,
        options=SecretsWorkflowOptions(),
    )

    assert result.warnings
    assert result.env_updates["VAULT_VERIFY_ENABLED"] == "true"


def test_gcp_sm_requires_project_id_for_unqualified_secret(cli_ctx) -> None:
    ctx = cli_ctx
    ctx.settings = None
    provider = StubInputProvider(
        strings={
            "GCP_SM_PROJECT_ID": "",
            "GCP_SM_SIGNING_SECRET_NAME": "auth-signing-secret",
            "GCP_SM_CACHE_TTL_SECONDS": "60",
        }
    )

    with pytest.raises(CLIError, match="GCP_SM_PROJECT_ID"):
        gcp.run_gcp_sm(
            ctx,
            provider,
            options=SecretsWorkflowOptions(),
        )
