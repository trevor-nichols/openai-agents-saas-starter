from __future__ import annotations

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from starter_shared.secrets.models import SecretsProviderLiteral

from ...common import CLIContext, CLIError
from ...console import console
from ...setup.inputs import InputProvider
from ...verification import VerificationArtifact
from ..models import OnboardResult, SecretsWorkflowOptions


def run_aws_sm(
    ctx: CLIContext,
    provider: InputProvider,
    *,
    options: SecretsWorkflowOptions,
) -> OnboardResult:
    settings = ctx.optional_settings()
    defaults = settings.aws_settings if settings else None
    region = provider.prompt_string(
        key="AWS_REGION",
        prompt="AWS region",
        default=(defaults.region if defaults and defaults.region else "us-east-1"),
        required=True,
    )
    secret_arn = provider.prompt_string(
        key="AWS_SM_SIGNING_SECRET_ARN",
        prompt="Secrets Manager ARN or name for signing secret",
        default=defaults.signing_secret_arn if defaults and defaults.signing_secret_arn else None,
        required=True,
    )
    cache_ttl_raw = provider.prompt_string(
        key="AWS_SM_CACHE_TTL_SECONDS",
        prompt="Secret cache TTL (seconds)",
        default=str(defaults.cache_ttl_seconds if defaults else 60),
        required=True,
    )
    cache_ttl = _coerce_positive_int(cache_ttl_raw, "AWS_SM_CACHE_TTL_SECONDS")

    use_profile = provider.prompt_bool(
        key="AWS_USE_PROFILE",
        prompt="Use a named AWS profile?",
        default=bool(defaults and defaults.profile),
    )
    profile = None
    access_key_id = None
    secret_access_key = None
    session_token = None
    if use_profile:
        profile = provider.prompt_string(
            key="AWS_PROFILE",
            prompt="Profile name",
            default=defaults.profile if defaults and defaults.profile else None,
            required=True,
        )
    else:
        use_static_keys = provider.prompt_bool(
            key="AWS_USE_STATIC_KEYS",
            prompt="Provide static access keys?",
            default=bool(defaults and defaults.access_key_id),
        )
        if use_static_keys:
            access_key_id = provider.prompt_string(
                key="AWS_ACCESS_KEY_ID",
                prompt="AWS access key ID",
                default=defaults.access_key_id if defaults and defaults.access_key_id else None,
                required=True,
            )
            secret_access_key = provider.prompt_secret(
                key="AWS_SECRET_ACCESS_KEY",
                prompt="AWS secret access key",
                existing=defaults.secret_access_key if defaults else None,
                required=True,
            )
            session_token = provider.prompt_string(
                key="AWS_SESSION_TOKEN",
                prompt="AWS session token (optional)",
                default=defaults.session_token if defaults and defaults.session_token else "",
                required=False,
            )

    verified = _probe_aws_secret(
        region=region,
        secret_arn=secret_arn,
        profile=profile,
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        session_token=session_token,
    )

    env_updates = {
        "SECRETS_PROVIDER": SecretsProviderLiteral.AWS_SM.value,
        "AWS_REGION": region,
        "AWS_SM_SIGNING_SECRET_ARN": secret_arn,
        "AWS_SM_CACHE_TTL_SECONDS": str(cache_ttl),
        "VAULT_VERIFY_ENABLED": "true",
    }
    if profile:
        env_updates["AWS_PROFILE"] = profile
    if access_key_id:
        env_updates["AWS_ACCESS_KEY_ID"] = access_key_id
    if secret_access_key:
        env_updates["AWS_SECRET_ACCESS_KEY"] = secret_access_key
    if session_token:
        env_updates["AWS_SESSION_TOKEN"] = session_token

    steps = [
        "Ensure the signing secret exists in AWS Secrets Manager.",
        "Assign the IAM role or user permission secretsmanager:GetSecretValue.",
        "Store the env vars above and restart FastAPI.",
    ]
    warnings: list[str] = []
    if verified:
        steps.insert(0, "Validated Secrets Manager access by reading the signing secret.")
    else:
        warnings.append(
            "Failed to read the signing secret via Secrets Manager. Check IAM credentials or ARN."
        )

    artifacts = [
        VerificationArtifact(
            provider="aws_sm",
            identifier=secret_arn,
            status="passed" if verified else "failed",
            detail=f"region={region}",
            source="secrets.onboard",
        )
    ]

    return OnboardResult(
        provider=SecretsProviderLiteral.AWS_SM,
        env_updates=env_updates,
        steps=steps,
        warnings=warnings,
        artifacts=artifacts,
    )


def _probe_aws_secret(
    *,
    region: str,
    secret_arn: str,
    profile: str | None,
    access_key_id: str | None,
    secret_access_key: str | None,
    session_token: str | None,
) -> bool:
    try:
        session = boto3.Session(
            profile_name=profile,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            aws_session_token=session_token,
            region_name=region,
        )
        client = session.client("secretsmanager")
        client.get_secret_value(SecretId=secret_arn)
        return True
    except (BotoCoreError, ClientError) as exc:  # pragma: no cover - external API dependency
        console.warn(f"AWS probe failed: {exc}", topic="secrets")
        return False


def _coerce_positive_int(value: str, label: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise CLIError(f"{label} must be an integer.") from exc
    if parsed <= 0:
        raise CLIError(f"{label} must be greater than zero.")
    return parsed


__all__ = ["run_aws_sm"]
