from __future__ import annotations

import argparse
import os
import subprocess
from collections.abc import Callable
from dataclasses import dataclass

import boto3
import httpx
from azure.core.exceptions import AzureError
from azure.identity import (
    ChainedTokenCredential,
    ClientSecretCredential,
    DefaultAzureCredential,
    ManagedIdentityCredential,
)
from azure.keyvault.secrets import SecretClient
from botocore.exceptions import BotoCoreError, ClientError
from starter_shared.secrets.models import SecretsProviderLiteral

from .common import TELEMETRY_ENV, CLIContext, CLIError
from .console import console
from .setup.inputs import (
    HeadlessInputProvider,
    InputProvider,
    InteractiveInputProvider,
    ParsedAnswers,
    load_answers_files,
    merge_answer_overrides,
)


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    secrets_parser = subparsers.add_parser("secrets", help="Secrets provider workflows.")
    secrets_subparsers = secrets_parser.add_subparsers(dest="secrets_command")

    onboard_parser = secrets_subparsers.add_parser(
        "onboard",
        help="Guided setup for the secrets/signing provider.",
    )
    onboard_parser.add_argument(
        "--provider",
        choices=[choice.value for choice in SecretsProviderLiteral],
        help="Secrets provider to configure (defaults to interactive menu).",
    )
    onboard_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Disable prompts and rely entirely on --answers-file/--var.",
    )
    onboard_parser.add_argument(
        "--answers-file",
        action="append",
        default=[],
        help="JSON file containing KEY: value pairs for prompts (repeatable).",
    )
    onboard_parser.add_argument(
        "--var",
        action="append",
        default=[],
        help="Override a prompt answer, e.g. --var VAULT_ADDR=https://vault.local",
    )
    onboard_parser.add_argument(
        "--skip-make",
        action="store_true",
        help="Do not invoke make targets even if the workflow normally offers to do so.",
    )
    onboard_parser.set_defaults(handler=handle_onboard)


@dataclass(slots=True)
class ProviderOption:
    literal: SecretsProviderLiteral
    label: str
    description: str
    available: bool


PROVIDER_OPTIONS: tuple[ProviderOption, ...] = (
    ProviderOption(
        literal=SecretsProviderLiteral.VAULT_DEV,
        label="Vault Dev (Docker)",
        description="Single-command dev signer via make vault-up on http://127.0.0.1:18200.",
        available=True,
    ),
    ProviderOption(
        literal=SecretsProviderLiteral.VAULT_HCP,
        label="HCP Vault (Dedicated/SaaS)",
        description="Point at an existing HCP Vault cluster with Transit enabled.",
        available=True,
    ),
    ProviderOption(
        literal=SecretsProviderLiteral.INFISICAL_CLOUD,
        label="Infisical Cloud",
        description="Managed Infisical workspace with service tokens.",
        available=True,
    ),
    ProviderOption(
        literal=SecretsProviderLiteral.INFISICAL_SELF_HOST,
        label="Infisical Self-Hosted",
        description="Docker/Kubernetes deploy of Infisical in your VPC.",
        available=True,
    ),
    ProviderOption(
        literal=SecretsProviderLiteral.AWS_SM,
        label="AWS Secrets Manager",
        description="Use Secrets Manager to store the signing secret (HMAC).",
        available=True,
    ),
    ProviderOption(
        literal=SecretsProviderLiteral.AZURE_KV,
        label="Azure Key Vault",
        description="Use Azure Key Vault secrets as the signing key store.",
        available=True,
    ),
)


@dataclass(slots=True)
class OnboardResult:
    provider: SecretsProviderLiteral
    env_updates: dict[str, str]
    steps: list[str]
    warnings: list[str]


def handle_onboard(args: argparse.Namespace, ctx: CLIContext) -> int:
    option = _resolve_provider_choice(args.provider, args.non_interactive)
    if not option.available:
        console.warn(
            f"{option.label} is not yet available. "
            "Keep SECRETS_PROVIDER set to vault_dev until provider support lands.",
            topic="secrets",
        )
        return 1

    answers = _load_answers(args)
    input_provider: InputProvider
    if args.non_interactive:
        input_provider = HeadlessInputProvider(answers)
    else:
        input_provider = InteractiveInputProvider(answers)

    runners: dict[SecretsProviderLiteral, Callable[..., OnboardResult]] = {
        SecretsProviderLiteral.VAULT_DEV: lambda: _run_vault_dev_flow(
            ctx, input_provider, args.skip_make
        ),
        SecretsProviderLiteral.VAULT_HCP: lambda: _run_vault_hcp_flow(ctx, input_provider),
        SecretsProviderLiteral.INFISICAL_CLOUD: lambda: _run_infisical_flow(
            ctx,
            input_provider,
            default_base_url="https://app.infisical.com",
            label="Infisical Cloud",
        ),
        SecretsProviderLiteral.INFISICAL_SELF_HOST: lambda: _run_infisical_flow(
            ctx,
            input_provider,
            default_base_url="http://localhost:8080",
            label="Infisical Self-Hosted",
            prompt_ca_bundle=True,
        ),
        SecretsProviderLiteral.AWS_SM: lambda: _run_aws_sm_flow(ctx, input_provider),
        SecretsProviderLiteral.AZURE_KV: lambda: _run_azure_kv_flow(ctx, input_provider),
    }

    runner = runners.get(option.literal)
    if runner is None:
        raise CLIError(f"No onboarding workflow implemented for {option.literal.value}.")

    result = runner()
    _render_result(result)
    _emit_cli_telemetry(result.provider.value, success=True)
    return 0


def _resolve_provider_choice(
    provider_arg: str | None,
    non_interactive: bool,
) -> ProviderOption:
    if provider_arg:
        literal = SecretsProviderLiteral(provider_arg)
        return next(option for option in PROVIDER_OPTIONS if option.literal is literal)

    if non_interactive:
        raise CLIError("--provider is required when --non-interactive is set.")

    console.info("Select a secrets provider:", topic="secrets")
    for idx, option in enumerate(PROVIDER_OPTIONS, start=1):
        status = "" if option.available else " (coming soon)"
        console.info(f"{idx}. {option.label}{status}", topic="secrets")
        console.info(f"   {option.description}", topic="secrets")

    while True:
        choice = input("Enter provider number: ").strip()
        if not choice.isdigit():
            console.warn("Please enter a numeric choice.", topic="secrets")
            continue
        idx = int(choice)
        if 1 <= idx <= len(PROVIDER_OPTIONS):
            return PROVIDER_OPTIONS[idx - 1]
        console.warn("Choice out of range.", topic="secrets")


def _load_answers(args: argparse.Namespace) -> ParsedAnswers:
    answers = load_answers_files(args.answers_file or [])
    if args.var:
        answers = merge_answer_overrides(answers, args.var)
    return answers


def _run_vault_dev_flow(
    ctx: CLIContext,
    provider: InputProvider,
    skip_make: bool,
) -> OnboardResult:
    settings = ctx.optional_settings()
    default_addr = (settings.vault_addr if settings else None) or "http://127.0.0.1:18200"
    default_token = (settings.vault_token if settings else None) or "vault-dev-root"
    default_transit = settings.vault_transit_key if settings else "auth-service"

    addr = provider.prompt_string(
        key="VAULT_ADDR",
        prompt="Vault dev address",
        default=default_addr,
        required=True,
    )
    token = provider.prompt_secret(
        key="VAULT_TOKEN",
        prompt="Vault token",
        existing=default_token,
        required=True,
    )
    transit_key = provider.prompt_string(
        key="VAULT_TRANSIT_KEY",
        prompt="Transit key name",
        default=default_transit,
        required=True,
    )
    verify = provider.prompt_bool(
        key="VAULT_VERIFY_ENABLED",
        prompt="Enforce Vault verification for service-account issuance?",
        default=True,
    )

    env_updates = {
        "SECRETS_PROVIDER": SecretsProviderLiteral.VAULT_DEV.value,
        "VAULT_ADDR": addr,
        "VAULT_TOKEN": token,
        "VAULT_TRANSIT_KEY": transit_key,
        "VAULT_VERIFY_ENABLED": "true" if verify else "false",
    }

    steps = [
        "Run `make vault-up` to start the local dev signer (remains in-memory, non-production).",
        "Export the variables above or add them to .env.local / .env.compose.",
        "Re-run `make verify-vault` after updating FastAPI env to ensure end-to-end signing works.",
    ]

    if not skip_make and _prompt_yes_no("Run `make vault-up` now?", default=True):
        _run_make_target(ctx, "vault-up", topic="secrets")
        steps[0] = "Started the dev signer via `make vault-up`."

    warnings: list[str] = [
        (
            "Dev Vault stores state in-memory with a static root token. "
            "Never expose it to production traffic."
        )
    ]

    return OnboardResult(
        provider=SecretsProviderLiteral.VAULT_DEV,
        env_updates=env_updates,
        steps=steps,
        warnings=warnings,
    )


def _run_vault_hcp_flow(
    ctx: CLIContext,
    provider: InputProvider,
) -> OnboardResult:
    settings = ctx.optional_settings()
    default_addr = ""
    if settings and settings.vault_addr:
        default_addr = settings.vault_addr
    default_namespace = (
        settings.vault_namespace if settings and settings.vault_namespace else "admin"
    )
    default_transit = settings.vault_transit_key if settings else "auth-service"

    addr = provider.prompt_string(
        key="VAULT_ADDR",
        prompt="HCP Vault address (https://...:8200)",
        default=default_addr or None,
        required=True,
    )
    namespace = provider.prompt_string(
        key="VAULT_NAMESPACE",
        prompt="Vault namespace (admin/tenant)",
        default=default_namespace,
        required=True,
    )
    token = provider.prompt_secret(
        key="VAULT_TOKEN",
        prompt="Vault token/AppRole secret",
        existing=settings.vault_token if settings else None,
        required=True,
    )
    transit_key = provider.prompt_string(
        key="VAULT_TRANSIT_KEY",
        prompt="Transit key name",
        default=default_transit,
        required=True,
    )
    verify = provider.prompt_bool(
        key="VAULT_VERIFY_ENABLED",
        prompt="Enforce Vault verification for service-account issuance?",
        default=True,
    )

    env_updates = {
        "SECRETS_PROVIDER": SecretsProviderLiteral.VAULT_HCP.value,
        "VAULT_ADDR": addr,
        "VAULT_NAMESPACE": namespace,
        "VAULT_TOKEN": token,
        "VAULT_TRANSIT_KEY": transit_key,
        "VAULT_VERIFY_ENABLED": "true" if verify else "false",
    }

    steps = [
        "Ensure the Transit secrets engine is enabled and the specified key exists.",
        "Configure a minimally scoped token/AppRole with transit:sign + transit:verify.",
        "Update backend/CLI env files with the values above and restart FastAPI.",
        "Run `make verify-vault` (pointed at the HCP cluster) to smoke test signatures.",
    ]

    warnings = [
        (
            "HCP Vault enforces TLS + namespaces; confirm your VAULT_NAMESPACE "
            "matches the cluster settings."
        ),
        "Store the Vault token/AppRole secret in your password manager or secure secret store.",
    ]

    return OnboardResult(
        provider=SecretsProviderLiteral.VAULT_HCP,
        env_updates=env_updates,
        steps=steps,
        warnings=warnings,
    )


def _run_infisical_flow(
    ctx: CLIContext,
    provider: InputProvider,
    *,
    default_base_url: str,
    label: str,
    prompt_ca_bundle: bool = False,
) -> OnboardResult:
    settings = ctx.optional_settings()
    defaults = settings.infisical_settings if settings else None
    base_url = provider.prompt_string(
        key="INFISICAL_BASE_URL",
        prompt=f"{label} base URL",
        default=(defaults.base_url if defaults and defaults.base_url else default_base_url),
        required=True,
    )
    service_token = provider.prompt_secret(
        key="INFISICAL_SERVICE_TOKEN",
        prompt="Infisical service token",
        existing=defaults.service_token if defaults else None,
        required=True,
    )
    project_id = provider.prompt_string(
        key="INFISICAL_PROJECT_ID",
        prompt="Infisical project/workspace ID",
        default=defaults.project_id if defaults and defaults.project_id else None,
        required=True,
    )
    environment = provider.prompt_string(
        key="INFISICAL_ENVIRONMENT",
        prompt="Infisical environment slug",
        default=(defaults.environment if defaults and defaults.environment else "dev"),
        required=True,
    )
    secret_path = provider.prompt_string(
        key="INFISICAL_SECRET_PATH",
        prompt="Secret path (e.g., /backend)",
        default=defaults.secret_path if defaults and defaults.secret_path else "/",
        required=True,
    )
    signing_secret = provider.prompt_string(
        key="INFISICAL_SIGNING_SECRET_NAME",
        prompt="Signing secret name",
        default=(
            defaults.signing_secret_name if defaults else "auth-service-signing-secret"
        ),
        required=True,
    )
    ca_bundle = ""
    if prompt_ca_bundle:
        ca_bundle = provider.prompt_string(
            key="INFISICAL_CA_BUNDLE_PATH",
            prompt="Custom CA bundle path (leave blank for default trust store)",
            default=defaults.ca_bundle_path if defaults and defaults.ca_bundle_path else "",
            required=False,
        )

    env_updates = {
        "SECRETS_PROVIDER": (
            SecretsProviderLiteral.INFISICAL_SELF_HOST.value
            if prompt_ca_bundle
            else SecretsProviderLiteral.INFISICAL_CLOUD.value
        ),
        "INFISICAL_BASE_URL": base_url,
        "INFISICAL_SERVICE_TOKEN": service_token,
        "INFISICAL_PROJECT_ID": project_id,
        "INFISICAL_ENVIRONMENT": environment,
        "INFISICAL_SECRET_PATH": secret_path,
        "INFISICAL_SIGNING_SECRET_NAME": signing_secret,
        "VAULT_VERIFY_ENABLED": "true",
    }
    if ca_bundle:
        env_updates["INFISICAL_CA_BUNDLE_PATH"] = ca_bundle

    verified = _probe_infisical_secret(
        base_url=base_url,
        service_token=service_token,
        project_id=project_id,
        environment=environment,
        secret_path=secret_path,
        secret_name=signing_secret,
        ca_bundle_path=ca_bundle or None,
    )

    steps = [
        "Install the Infisical CLI or configure service tokens for CI/CD.",
        "Store the service token securely (rotate via Infisical dashboard).",
        "Add the env vars above to .env/.env.local and restart FastAPI + CLI shells.",
    ]
    warnings: list[str] = []

    if verified:
        steps.insert(
            0,
            f"Validated that secret `{signing_secret}` exists and is readable.",
        )
    else:
        warnings.append(
            "Could not verify the signing secret via the Infisical API. "
            "Double-check the service token permissions and secret name."
        )

    return OnboardResult(
        provider=SecretsProviderLiteral.INFISICAL_SELF_HOST
        if prompt_ca_bundle
        else SecretsProviderLiteral.INFISICAL_CLOUD,
        env_updates=env_updates,
        steps=steps,
        warnings=warnings,
    )


def _run_aws_sm_flow(ctx: CLIContext, provider: InputProvider) -> OnboardResult:
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

    env_updates: dict[str, str] = {
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
        (
            "Attach IAM permissions allowing secretsmanager:GetSecretValue / "
            "DescribeSecret on the signing secret."
        ),
        "Store the HMAC signing secret value in Secrets Manager (plain text).",
        "Add the env vars above to backend + CLI and redeploy FastAPI.",
    ]
    warnings: list[str] = []
    if verified:
        steps.insert(0, "Validated AWS credentials by fetching the signing secret.")
    else:
        warnings.append(
            "AWS credential or secret validation failed. "
            "Double-check IAM policies and network settings."
        )

    return OnboardResult(
        provider=SecretsProviderLiteral.AWS_SM,
        env_updates=env_updates,
        steps=steps,
        warnings=warnings,
    )


def _run_azure_kv_flow(ctx: CLIContext, provider: InputProvider) -> OnboardResult:
    settings = ctx.optional_settings()
    defaults = settings.azure_settings if settings else None
    vault_url = provider.prompt_string(
        key="AZURE_KEY_VAULT_URL",
        prompt="Azure Key Vault URL",
        default=defaults.vault_url if defaults and defaults.vault_url else None,
        required=True,
    )
    secret_name = provider.prompt_string(
        key="AZURE_KV_SIGNING_SECRET_NAME",
        prompt="Signing secret name",
        default=defaults.signing_secret_name if defaults and defaults.signing_secret_name else None,
        required=True,
    )
    ttl_raw = provider.prompt_string(
        key="AZURE_KV_CACHE_TTL_SECONDS",
        prompt="Secret cache TTL (seconds)",
        default=str(defaults.cache_ttl_seconds if defaults else 60),
        required=True,
    )
    cache_ttl = _coerce_positive_int(ttl_raw, "AZURE_KV_CACHE_TTL_SECONDS")

    use_managed_identity = provider.prompt_bool(
        key="AZURE_USE_MANAGED_IDENTITY",
        prompt="Use managed identity (vs service principal)?",
        default=bool(defaults and defaults.managed_identity_client_id),
    )

    tenant_id = None
    client_id = None
    client_secret = None
    managed_identity_client_id = None

    if use_managed_identity:
        managed_identity_client_id = provider.prompt_string(
            key="AZURE_MANAGED_IDENTITY_CLIENT_ID",
            prompt="Managed identity client ID (blank for system-assigned)",
            default=(
                defaults.managed_identity_client_id
                if defaults and defaults.managed_identity_client_id
                else ""
            ),
            required=False,
        )
    else:
        tenant_id = provider.prompt_string(
            key="AZURE_TENANT_ID",
            prompt="Azure AD tenant ID",
            default=defaults.tenant_id if defaults and defaults.tenant_id else None,
            required=True,
        )
        client_id = provider.prompt_string(
            key="AZURE_CLIENT_ID",
            prompt="Azure AD application (client) ID",
            default=defaults.client_id if defaults and defaults.client_id else None,
            required=True,
        )
        client_secret = provider.prompt_secret(
            key="AZURE_CLIENT_SECRET",
            prompt="Azure AD client secret",
            existing=defaults.client_secret if defaults else None,
            required=True,
        )

    verified = _probe_azure_secret(
        vault_url=vault_url,
        secret_name=secret_name,
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
        managed_identity_client_id=managed_identity_client_id or None,
    )

    env_updates: dict[str, str] = {
        "SECRETS_PROVIDER": SecretsProviderLiteral.AZURE_KV.value,
        "AZURE_KEY_VAULT_URL": vault_url,
        "AZURE_KV_SIGNING_SECRET_NAME": secret_name,
        "AZURE_KV_CACHE_TTL_SECONDS": str(cache_ttl),
        "VAULT_VERIFY_ENABLED": "true",
    }
    if tenant_id:
        env_updates["AZURE_TENANT_ID"] = tenant_id
    if client_id:
        env_updates["AZURE_CLIENT_ID"] = client_id
    if client_secret:
        env_updates["AZURE_CLIENT_SECRET"] = client_secret
    if managed_identity_client_id:
        env_updates["AZURE_MANAGED_IDENTITY_CLIENT_ID"] = managed_identity_client_id

    steps = [
        (
            "Assign the Key Vault Secrets User role (or equivalent) to the "
            "service principal or managed identity."
        ),
        "Ensure the signing secret exists in Key Vault; rotate by updating the secret value.",
        "Add the env vars above to backend + CLI and restart FastAPI.",
    ]
    warnings: list[str] = []
    if verified:
        steps.insert(0, "Validated Key Vault access by reading the signing secret.")
    else:
        warnings.append(
            "Azure Key Vault validation failed. Check tenant/app credentials "
            "or managed identity permissions."
        )

    return OnboardResult(
        provider=SecretsProviderLiteral.AZURE_KV,
        env_updates=env_updates,
        steps=steps,
        warnings=warnings,
    )


def _prompt_yes_no(question: str, *, default: bool) -> bool:
    hint = "Y/n" if default else "y/N"
    while True:
        raw = input(f"{question} ({hint}) ").strip().lower()
        if not raw:
            return default
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        console.warn("Please answer yes or no.", topic="secrets")


def _run_make_target(ctx: CLIContext, target: str, *, topic: str) -> None:
    console.info(f"Running `make {target}` …", topic=topic)
    subprocess.run(["make", target], cwd=ctx.project_root, check=True)


def _render_result(result: OnboardResult) -> None:
    console.success(
        f"Secrets provider configured: {result.provider.value}",
        topic="secrets",
    )
    console.info("Add or update the following environment variables:", topic="secrets")
    for key, value in result.env_updates.items():
        console.info(f"{key}={value}", topic="secrets")

    if result.steps:
        console.newline()
        console.info("Next steps:", topic="secrets")
        for step in result.steps:
            console.info(f"- {step}", topic="secrets")

    if result.warnings:
        console.newline()
        for warning in result.warnings:
            console.warn(warning, topic="secrets")


def _emit_cli_telemetry(provider: str, success: bool) -> None:
    if os.getenv(TELEMETRY_ENV, "false").lower() not in {"1", "true", "yes"}:
        return
    console.info(
        f"[telemetry] secrets_provider={provider} success={success}",
        topic="secrets",
    )


def _probe_infisical_secret(
    *,
    base_url: str,
    service_token: str,
    project_id: str,
    environment: str,
    secret_path: str,
    secret_name: str,
    ca_bundle_path: str | None,
) -> bool:
    params = {
        "environment": environment,
        "workspaceId": project_id,
        "type": "shared",
        "path": secret_path or "/",
    }
    headers = {"Authorization": f"Bearer {service_token}"}
    verify: bool | str = ca_bundle_path or True
    url = f"{base_url.rstrip('/')}/api/v4/secrets/{secret_name}"
    try:
        response = httpx.get(url, headers=headers, params=params, timeout=5.0, verify=verify)
    except httpx.HTTPError as exc:
        console.warn(f"Infisical probe failed: {exc}", topic="secrets")
        return False

    if response.status_code == 200:
        return True
    if response.status_code == 404:
        return False
    console.warn(
        f"Infisical probe returned {response.status_code}: {response.text}",
        topic="secrets",
    )
    return False


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
    except (BotoCoreError, ClientError) as exc:
        console.warn(f"AWS probe failed: {exc}", topic="secrets")
        return False


def _probe_azure_secret(
    *,
    vault_url: str,
    secret_name: str,
    tenant_id: str | None,
    client_id: str | None,
    client_secret: str | None,
    managed_identity_client_id: str | None,
) -> bool:
    try:
        credentials: list = []
        if tenant_id and client_id and client_secret:
            credentials.append(
                ClientSecretCredential(
                    tenant_id=tenant_id,
                    client_id=client_id,
                    client_secret=client_secret,
                )
            )
        if managed_identity_client_id:
            credentials.append(
                ManagedIdentityCredential(client_id=managed_identity_client_id)
            )
        credentials.append(
            DefaultAzureCredential(exclude_interactive_browser_credential=True)
        )
        credential = (
            credentials[0]
            if len(credentials) == 1
            else ChainedTokenCredential(*credentials)
        )
        client = SecretClient(vault_url=vault_url, credential=credential)
        client.get_secret(secret_name)
        return True
    except AzureError as exc:
        console.warn(f"Azure probe failed: {exc}", topic="secrets")
        return False


def _coerce_positive_int(value: str, label: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise CLIError(f"{label} must be an integer.") from exc
    if parsed <= 0:
        raise CLIError(f"{label} must be greater than zero.")
    return parsed


__all__ = ["register"]
