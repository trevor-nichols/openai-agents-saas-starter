from __future__ import annotations

import pytest
from starter_cli.cli.common import CLIError
from starter_cli.cli.secrets.models import SecretsWorkflowOptions
from starter_cli.cli.secrets.providers import aws

from .._stubs import StubInputProvider


def test_aws_sm_with_profile(cli_ctx, monkeypatch) -> None:
    ctx = cli_ctx
    ctx.settings = None
    monkeypatch.setattr(aws, "_probe_aws_secret", lambda **_: True)
    provider = StubInputProvider(
        strings={
            "AWS_REGION": "us-west-2",
            "AWS_SM_SIGNING_SECRET_ARN": "arn:aws:secretsmanager:...:secret:signing",
            "AWS_SM_CACHE_TTL_SECONDS": "120",
            "AWS_PROFILE": "dev",
        },
        bools={"AWS_USE_PROFILE": True},
    )

    result = aws.run_aws_sm(
        ctx,
        provider,
        options=SecretsWorkflowOptions(),
    )

    assert result.env_updates["AWS_PROFILE"] == "dev"
    assert result.env_updates["AWS_SM_CACHE_TTL_SECONDS"] == "120"
    assert result.env_updates["VAULT_VERIFY_ENABLED"] == "true"
    assert result.steps[0].startswith("Validated")


def test_aws_sm_invalid_ttl_raises(cli_ctx) -> None:
    ctx = cli_ctx
    ctx.settings = None
    provider = StubInputProvider(
        strings={
            "AWS_REGION": "us-west-2",
            "AWS_SM_SIGNING_SECRET_ARN": "arn",
            "AWS_SM_CACHE_TTL_SECONDS": "oops",
        },
        bools={"AWS_USE_PROFILE": False, "AWS_USE_STATIC_KEYS": False},
    )

    with pytest.raises(CLIError):
        aws.run_aws_sm(ctx, provider, options=SecretsWorkflowOptions())
