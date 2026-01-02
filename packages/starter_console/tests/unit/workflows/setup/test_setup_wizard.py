from __future__ import annotations

import json
import os
from pathlib import Path

import httpx
import pytest
from starter_console.core import CLIContext, CLIError
from starter_console.ports.console import StdConsole
from starter_console.presenters import build_headless_presenter
from starter_console.workflows.setup import (
    HeadlessInputProvider,
    InteractiveInputProvider,
    SetupWizard,
)
from starter_console.workflows.setup import wizard as wizard_module
from starter_console.workflows.setup._wizard import audit
from starter_console.workflows.setup._wizard.sections import providers as provider_section
from starter_console.workflows.setup.automation import AutomationPhase, AutomationStatus
from starter_console.workflows.setup.models import CheckResult, SectionResult
from starter_console.workflows.setup.validators import set_vault_probe_request


@pytest.fixture()
def temp_ctx(tmp_path: Path) -> CLIContext:
    env_path = tmp_path / "apps" / "api-service" / ".env.local"
    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text("", encoding="utf-8")
    return CLIContext(project_root=tmp_path, env_files=(env_path,))


@pytest.fixture(autouse=True)
def stub_vault_probe():
    def fake_request(url: str, headers: dict[str, str]):
        return httpx.Response(200, request=httpx.Request("GET", url))

    set_vault_probe_request(fake_request)
    yield
    set_vault_probe_request(None)


def backend_env_path(ctx: CLIContext) -> Path:
    return ctx.project_root / "apps" / "api-service" / ".env.local"


def _cleanup_env(snapshot: dict[str, str]) -> None:
    current_keys = set(os.environ.keys())
    for key in current_keys - snapshot.keys():
        os.environ.pop(key, None)
    for key, value in snapshot.items():
        os.environ[key] = value


def _local_headless_answers() -> dict[str, str]:
    return {
        "ENVIRONMENT": "development",
        "DEBUG": "true",
        "PORT": "8000",
        "APP_PUBLIC_URL": "http://localhost:3000",
        "ALLOWED_HOSTS": "localhost",
        "ALLOWED_ORIGINS": "http://localhost:3000",
        "AUTO_RUN_MIGRATIONS": "false",
        "STARTER_LOCAL_DATABASE_MODE": "compose",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "postgres",
        "POSTGRES_PASSWORD": "postgres",
        "POSTGRES_DB": "saas_starter_db",
        "API_BASE_URL": "http://127.0.0.1:8000",
        "ROTATE_SIGNING_KEYS": "false",
        "VAULT_VERIFY_ENABLED": "true",
        "VAULT_ADDR": "https://vault.example.com",
        "VAULT_TOKEN": "vault-token",
        "VAULT_TRANSIT_KEY": "auth-service",
        "AUTH_KEY_SECRET_NAME": "auth-signing-secret",
        "AWS_USE_PROFILE": "true",
        "AWS_PROFILE": "prod-profile",
        "AWS_REGION": "us-east-1",
        "OPENAI_API_KEY": "sk-openai",
        "ENABLE_ANTHROPIC_API_KEY": "false",
        "ENABLE_GEMINI_API_KEY": "false",
        "ENABLE_XAI_API_KEY": "false",
        "REDIS_URL": "redis://localhost:6379/0",
        "RATE_LIMIT_REDIS_URL": "",
        "AUTH_CACHE_REDIS_URL": "",
        "SECURITY_TOKEN_REDIS_URL": "",
        "BILLING_EVENTS_REDIS_URL": "",
        "ENABLE_BILLING": "false",
        "ENABLE_BILLING_STREAM": "false",
        "RESEND_EMAIL_ENABLED": "false",
        "RESEND_BASE_URL": "https://api.resend.com",
        "RUN_MIGRATIONS_NOW": "false",
        "TENANT_DEFAULT_SLUG": "local",
        "LOGGING_SINKS": "stdout",
        "GEOIP_PROVIDER": "none",
        "SIGNUP_ACCESS_POLICY": "public",
        "ALLOW_PUBLIC_SIGNUP": "true",
        "ALLOW_SIGNUP_TRIAL_OVERRIDE": "false",
        "SIGNUP_RATE_LIMIT_PER_HOUR": "15",
        "SIGNUP_RATE_LIMIT_PER_IP_DAY": "90",
        "SIGNUP_RATE_LIMIT_PER_EMAIL_DAY": "3",
        "SIGNUP_RATE_LIMIT_PER_DOMAIN_DAY": "20",
        "SIGNUP_CONCURRENT_REQUESTS_LIMIT": "2",
        "SIGNUP_DEFAULT_PLAN_CODE": "starter",
        "SIGNUP_DEFAULT_TRIAL_DAYS": "21",
        "BILLING_RETRY_DEPLOYMENT_MODE": "inline",
        "ENABLE_BILLING_RETRY_WORKER": "true",
        "ENABLE_BILLING_STREAM_REPLAY": "false",
        "STORAGE_PROVIDER": "minio",
        "STORAGE_BUCKET_PREFIX": "agent-data",
        "MINIO_ENDPOINT": "http://localhost:9000",
        "MINIO_ACCESS_KEY": "minioadmin",
        "MINIO_SECRET_KEY": "minioadmin",
        "MINIO_REGION": "",
        "MINIO_SECURE": "false",
        "IMAGE_DEFAULT_SIZE": "1024x1024",
        "IMAGE_DEFAULT_QUALITY": "high",
        "IMAGE_DEFAULT_FORMAT": "png",
        "IMAGE_DEFAULT_BACKGROUND": "auto",
        "IMAGE_DEFAULT_COMPRESSION": "",
        "IMAGE_OUTPUT_MAX_MB": "6",
        "IMAGE_MAX_PARTIAL_IMAGES": "2",
    }


def _create_setup_wizard(**kwargs) -> SetupWizard:
    kwargs.setdefault("enable_tui", False)
    kwargs.setdefault(
        "automation_overrides", {phase: False for phase in AutomationPhase}
    )
    return SetupWizard(**kwargs)


def test_wizard_headless_local_generates_env(temp_ctx: CLIContext) -> None:
    snapshot = dict(os.environ)
    answers = _local_headless_answers()
    wizard = _create_setup_wizard(
        ctx=temp_ctx,
        profile="demo",
        output_format="summary",
        input_provider=HeadlessInputProvider(answers=answers),
    )
    wizard.execute()

    env_body = backend_env_path(temp_ctx).read_text(encoding="utf-8")
    assert "OPENAI_API_KEY" in env_body
    assert "TENANT_DEFAULT_SLUG=local" in env_body
    assert "API_BASE_URL=http://127.0.0.1:8000" in env_body
    assert "LOGGING_SINKS=stdout" in env_body
    assert "SIGNUP_ACCESS_POLICY=public" in env_body
    assert "ALLOW_PUBLIC_SIGNUP=true" in env_body
    assert "BILLING_RETRY_DEPLOYMENT_MODE=inline" in env_body
    assert 'ANTHROPIC_API_KEY=""' in env_body
    _cleanup_env(snapshot)


def test_wizard_prompts_all_selected_sinks(temp_ctx: CLIContext) -> None:
    snapshot = dict(os.environ)
    answers = _local_headless_answers() | {
        "LOGGING_SINKS": "stdout,datadog",
        "LOGGING_DATADOG_API_KEY": "dd-api-key",
        "LOGGING_DATADOG_SITE": "datadoghq.eu",
    }

    wizard = _create_setup_wizard(
        ctx=temp_ctx,
        profile="demo",
        output_format="summary",
        input_provider=HeadlessInputProvider(answers=answers),
    )
    wizard.execute()

    from starter_console.adapters.env.files import EnvFile

    env_file = EnvFile(backend_env_path(temp_ctx))
    assert env_file.get("LOGGING_SINKS") == "stdout,datadog"
    assert env_file.get("LOGGING_DATADOG_API_KEY") == "dd-api-key"
    assert env_file.get("LOGGING_DATADOG_SITE") == "datadoghq.eu"
    _cleanup_env(snapshot)


def test_wizard_configures_slack_section(temp_ctx: CLIContext) -> None:
    snapshot = dict(os.environ)
    answers = _local_headless_answers() | {
        "ENABLE_SLACK_STATUS_NOTIFICATIONS": "true",
        "SLACK_STATUS_BOT_TOKEN": "xoxb-test",
        "SLACK_STATUS_DEFAULT_CHANNELS": "#incidents",
    }
    wizard = _create_setup_wizard(
        ctx=temp_ctx,
        profile="demo",
        output_format="summary",
        input_provider=HeadlessInputProvider(answers=answers),
    )
    wizard.execute()

    env_body = backend_env_path(temp_ctx).read_text(encoding="utf-8")
    assert "ENABLE_SLACK_STATUS_NOTIFICATIONS=true" in env_body
    assert 'SLACK_STATUS_DEFAULT_CHANNELS="#incidents"' in env_body
    assert "SLACK_STATUS_BOT_TOKEN=xoxb-test" in env_body
    _cleanup_env(snapshot)


def test_wizard_configures_sso_when_enabled(temp_ctx: CLIContext) -> None:
    snapshot = dict(os.environ)
    answers = _local_headless_answers() | {
        "SSO_GOOGLE_ENABLED": "true",
        "SSO_GOOGLE_SCOPE": "global",
        "SSO_GOOGLE_ISSUER_URL": "https://accounts.google.com",
        "SSO_GOOGLE_DISCOVERY_URL": "https://accounts.google.com/.well-known/openid-configuration",
        "SSO_GOOGLE_CLIENT_ID": "google-client",
        "SSO_GOOGLE_CLIENT_SECRET": "google-secret",
        "SSO_GOOGLE_SCOPES": "openid,email,profile",
        "SSO_GOOGLE_PKCE_REQUIRED": "true",
        "SSO_GOOGLE_AUTO_PROVISION_POLICY": "invite_only",
    }
    wizard = _create_setup_wizard(
        ctx=temp_ctx,
        profile="demo",
        output_format="summary",
        input_provider=HeadlessInputProvider(answers=answers),
    )
    wizard.execute()

    env_body = backend_env_path(temp_ctx).read_text(encoding="utf-8")
    assert "SSO_PROVIDERS=google" in env_body
    assert "SSO_GOOGLE_ENABLED=true" in env_body
    assert "SSO_GOOGLE_CLIENT_ID=google-client" in env_body
    assert "SSO_GOOGLE_CLIENT_SECRET=google-secret" in env_body
    assert 'SSO_GOOGLE_SCOPES="openid,email,profile"' in env_body
    _cleanup_env(snapshot)


def test_wizard_configures_multiple_sso_providers(temp_ctx: CLIContext) -> None:
    snapshot = dict(os.environ)
    answers = _local_headless_answers() | {
        "SSO_PROVIDERS": "google,azure",
        "SSO_GOOGLE_ISSUER_URL": "https://accounts.google.com",
        "SSO_GOOGLE_DISCOVERY_URL": "https://accounts.google.com/.well-known/openid-configuration",
        "SSO_GOOGLE_CLIENT_ID": "google-client",
        "SSO_GOOGLE_CLIENT_SECRET": "google-secret",
        "SSO_GOOGLE_SCOPES": "openid,email,profile",
        "SSO_GOOGLE_PKCE_REQUIRED": "true",
        "SSO_GOOGLE_AUTO_PROVISION_POLICY": "invite_only",
        "SSO_AZURE_ISSUER_URL": "https://login.microsoftonline.com/tenant-id/v2.0",
        "SSO_AZURE_DISCOVERY_URL": "https://login.microsoftonline.com/tenant-id/v2.0/.well-known/openid-configuration",
        "SSO_AZURE_CLIENT_ID": "azure-client",
        "SSO_AZURE_CLIENT_SECRET": "azure-secret",
        "SSO_AZURE_SCOPES": "openid,email,profile",
        "SSO_AZURE_PKCE_REQUIRED": "true",
        "SSO_AZURE_AUTO_PROVISION_POLICY": "invite_only",
    }
    wizard = _create_setup_wizard(
        ctx=temp_ctx,
        profile="demo",
        output_format="summary",
        input_provider=HeadlessInputProvider(answers=answers),
    )
    wizard.execute()

    from starter_console.adapters.env.files import EnvFile

    env_file = EnvFile(backend_env_path(temp_ctx))
    assert env_file.get("SSO_PROVIDERS") == "google,azure"
    env_body = backend_env_path(temp_ctx).read_text(encoding="utf-8")
    assert "SSO_GOOGLE_CLIENT_ID=google-client" in env_body
    assert "SSO_AZURE_CLIENT_ID=azure-client" in env_body
    _cleanup_env(snapshot)


def test_wizard_exports_answers_when_requested(temp_ctx: CLIContext) -> None:
    snapshot = dict(os.environ)
    answers = _local_headless_answers()
    export_path = temp_ctx.project_root / "ops" / "local.json"
    wizard = _create_setup_wizard(
        ctx=temp_ctx,
        profile="demo",
        output_format="summary",
        input_provider=HeadlessInputProvider(answers=answers),
        export_answers_path=export_path,
    )
    wizard.execute()

    payload = json.loads(export_path.read_text(encoding="utf-8"))
    assert payload["DATABASE_URL"] == "postgresql+asyncpg://postgres:postgres@localhost:5432/saas_starter_db"
    assert payload["OPENAI_API_KEY"] == answers["OPENAI_API_KEY"]
    _cleanup_env(snapshot)


def test_wizard_configures_bundled_collector(temp_ctx: CLIContext) -> None:
    snapshot = dict(os.environ)
    answers = _local_headless_answers() | {
        "LOGGING_SINKS": "otlp",
        "ENABLE_OTEL_COLLECTOR": "true",
        "LOGGING_OTLP_ENDPOINT": "http://otel-collector:4318/v1/logs",
        "LOGGING_OTLP_HEADERS": "",
        "OTEL_EXPORTER_SENTRY_ENABLED": "true",
        "OTEL_EXPORTER_SENTRY_ENDPOINT": "https://o11y.ingest.sentry.io/api/42/otlp",
        "OTEL_EXPORTER_SENTRY_AUTH_HEADER": "Bearer sentry-token",
        "OTEL_EXPORTER_SENTRY_HEADERS": "",
        "OTEL_EXPORTER_DATADOG_ENABLED": "true",
        "OTEL_EXPORTER_DATADOG_API_KEY": "dd-api-key",
        "OTEL_EXPORTER_DATADOG_SITE": "datadoghq.eu",
    }
    wizard = _create_setup_wizard(
        ctx=temp_ctx,
        profile="demo",
        output_format="summary",
        input_provider=HeadlessInputProvider(answers=answers),
    )
    wizard.execute()

    env_body = backend_env_path(temp_ctx).read_text(encoding="utf-8")
    assert "ENABLE_OTEL_COLLECTOR=true" in env_body
    assert "LOGGING_OTLP_ENDPOINT=http://otel-collector:4318/v1/logs" in env_body
    assert "OTEL_EXPORTER_SENTRY_ENDPOINT=https://o11y.ingest.sentry.io/api/42/otlp" in env_body
    assert 'OTEL_EXPORTER_SENTRY_AUTH_HEADER="Bearer sentry-token"' in env_body
    assert "OTEL_EXPORTER_DATADOG_API_KEY=dd-api-key" in env_body
    assert "OTEL_EXPORTER_DATADOG_SITE=datadoghq.eu" in env_body
    _cleanup_env(snapshot)


def test_wizard_headless_requires_worker_mode(temp_ctx: CLIContext) -> None:
    snapshot = dict(os.environ)
    answers = _local_headless_answers()
    answers.pop("BILLING_RETRY_DEPLOYMENT_MODE")
    wizard = _create_setup_wizard(
        ctx=temp_ctx,
        profile="demo",
        output_format="summary",
        input_provider=HeadlessInputProvider(answers=answers),
    )

    with pytest.raises(CLIError, match="BILLING_RETRY_DEPLOYMENT_MODE"):
        wizard.execute()

    _cleanup_env(snapshot)


def test_wizard_headless_invalid_number_raises(temp_ctx: CLIContext) -> None:
    snapshot = dict(os.environ)
    answers = _local_headless_answers() | {"SIGNUP_RATE_LIMIT_PER_HOUR": "abc"}
    wizard = _create_setup_wizard(
        ctx=temp_ctx,
        profile="demo",
        output_format="summary",
        input_provider=HeadlessInputProvider(answers=answers),
    )

    with pytest.raises(CLIError, match="SIGNUP_RATE_LIMIT_PER_HOUR must be an integer"):
        wizard.execute()

    _cleanup_env(snapshot)


def test_wizard_headless_export_invalid_number_raises(temp_ctx: CLIContext) -> None:
    snapshot = dict(os.environ)
    answers = _local_headless_answers() | {"SIGNUP_RATE_LIMIT_PER_HOUR": "abc"}
    export_path = temp_ctx.project_root / "ops" / "local.json"
    wizard = _create_setup_wizard(
        ctx=temp_ctx,
        profile="demo",
        output_format="summary",
        input_provider=HeadlessInputProvider(answers=answers),
        export_answers_path=export_path,
    )

    with pytest.raises(CLIError, match="SIGNUP_RATE_LIMIT_PER_HOUR must be an integer"):
        wizard.execute()

    _cleanup_env(snapshot)


def test_dev_user_automation_invoked_when_enabled(
    monkeypatch: pytest.MonkeyPatch, temp_ctx: CLIContext
) -> None:
    snapshot = dict(os.environ)
    answers = _local_headless_answers()
    called: dict[str, int] = {"count": 0}

    def fake_run(context):
        called["count"] += 1
        context.automation.update(
            AutomationPhase.DEV_USER, AutomationStatus.SUCCEEDED, "ok"
        )

    monkeypatch.setattr(wizard_module, "run_dev_user_automation", fake_run)

    overrides = {phase: False for phase in AutomationPhase}
    overrides[AutomationPhase.DEV_USER] = True
    wizard = _create_setup_wizard(
        ctx=temp_ctx,
        profile="demo",
        output_format="summary",
        input_provider=HeadlessInputProvider(answers=answers),
        automation_overrides=overrides,
    )
    wizard.execute()

    assert called["count"] == 1
    _cleanup_env(snapshot)


def test_demo_token_automation_invoked_when_enabled(
    monkeypatch: pytest.MonkeyPatch, temp_ctx: CLIContext
) -> None:
    snapshot = dict(os.environ)
    answers = _local_headless_answers()
    called: dict[str, int] = {"count": 0}

    def fake_run(context):
        called["count"] += 1
        context.automation.update(
            AutomationPhase.DEMO_TOKEN, AutomationStatus.SUCCEEDED, "ok"
        )

    monkeypatch.setattr(wizard_module, "run_demo_token_automation", fake_run)

    overrides = {phase: False for phase in AutomationPhase}
    overrides[AutomationPhase.DEMO_TOKEN] = True
    wizard = _create_setup_wizard(
        ctx=temp_ctx,
        profile="demo",
        output_format="summary",
        input_provider=HeadlessInputProvider(answers=answers),
        automation_overrides=overrides,
    )
    wizard.execute()

    assert called["count"] == 1
    _cleanup_env(snapshot)


def test_wizard_writes_dedicated_worker_artifacts(temp_ctx: CLIContext) -> None:
    snapshot = dict(os.environ)
    answers = {
        "SETUP_HOSTING_PRESET": "enterprise_custom",
        "SECRETS_PROVIDER": "vault_hcp",
        "ENVIRONMENT": "production",
        "DEBUG": "false",
        "PORT": "8000",
        "APP_PUBLIC_URL": "https://example.com",
        "ALLOWED_HOSTS": "example.com",
        "ALLOWED_ORIGINS": "https://example.com",
        "AUTO_RUN_MIGRATIONS": "false",
        "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/saas_starter_db",
        "API_BASE_URL": "https://api.example.com",
        "ROTATE_SIGNING_KEYS": "false",
        "VAULT_VERIFY_ENABLED": "true",
        "VAULT_ADDR": "https://vault.example.com",
        "VAULT_TOKEN": "vault-token",
        "VAULT_TRANSIT_KEY": "auth-service",
        "AUTH_KEY_SECRET_NAME": "auth-signing-secret",
        "AWS_USE_PROFILE": "true",
        "AWS_PROFILE": "prod-profile",
        "AWS_REGION": "us-east-1",
        "OPENAI_API_KEY": "sk-openai",
        "ENABLE_ANTHROPIC_API_KEY": "false",
        "ENABLE_GEMINI_API_KEY": "false",
        "ENABLE_XAI_API_KEY": "false",
        "REDIS_URL": "rediss://:secret@redis.example.com:6379/0",
        "RATE_LIMIT_REDIS_URL": "",
        "AUTH_CACHE_REDIS_URL": "",
        "SECURITY_TOKEN_REDIS_URL": "",
        "BILLING_EVENTS_REDIS_URL": "",
        "ENABLE_BILLING": "true",
        "ENABLE_BILLING_STREAM": "true",
        "STRIPE_SECRET_KEY": "sk_live_example",
        "STRIPE_WEBHOOK_SECRET": "whsec_example",
        "STRIPE_PRODUCT_PRICE_MAP": '{"starter":"price_123"}',
        "RESEND_EMAIL_ENABLED": "false",
        "RESEND_BASE_URL": "https://api.resend.com",
        "RUN_MIGRATIONS_NOW": "false",
        "TENANT_DEFAULT_SLUG": "prod",
        "LOGGING_SINKS": "stdout",
        "GEOIP_PROVIDER": "none",
        "SIGNUP_ACCESS_POLICY": "invite_only",
        "ALLOW_PUBLIC_SIGNUP": "false",
        "ALLOW_SIGNUP_TRIAL_OVERRIDE": "false",
        "SIGNUP_RATE_LIMIT_PER_HOUR": "10",
        "SIGNUP_RATE_LIMIT_PER_IP_DAY": "20",
        "SIGNUP_RATE_LIMIT_PER_EMAIL_DAY": "3",
        "SIGNUP_RATE_LIMIT_PER_DOMAIN_DAY": "5",
        "SIGNUP_CONCURRENT_REQUESTS_LIMIT": "1",
        "SIGNUP_DEFAULT_PLAN_CODE": "starter",
        "SIGNUP_DEFAULT_TRIAL_DAYS": "14",
        "BILLING_RETRY_DEPLOYMENT_MODE": "dedicated",
        "ENABLE_BILLING_RETRY_WORKER": "false",
        "ENABLE_BILLING_STREAM_REPLAY": "true",
    }
    wizard = _create_setup_wizard(
        ctx=temp_ctx,
        profile="production",
        output_format="summary",
        input_provider=HeadlessInputProvider(answers=answers),
    )
    wizard.execute()

    env_body = backend_env_path(temp_ctx).read_text(encoding="utf-8")
    assert "ENABLE_BILLING_RETRY_WORKER=false" in env_body
    assert "ENABLE_BILLING_STREAM_REPLAY=false" in env_body
    assert "BILLING_RETRY_DEPLOYMENT_MODE=dedicated" in env_body

    overlay_path = temp_ctx.project_root / "var/reports/billing-worker.env"
    summary_path = temp_ctx.project_root / "var/reports/billing-worker-topology.md"
    assert overlay_path.exists()
    assert summary_path.exists()
    overlay_body = overlay_path.read_text(encoding="utf-8")
    assert "ENABLE_BILLING_RETRY_WORKER=true" in overlay_body
    summary_body = summary_path.read_text(encoding="utf-8")
    assert "dedicated" in summary_body

    _cleanup_env(snapshot)


def test_wizard_refreshes_cached_settings(temp_ctx: CLIContext) -> None:
    # Seed .env.local with an initial value so Settings caches it.
    env_file = backend_env_path(temp_ctx)
    env_file.write_text("ALLOW_PUBLIC_SIGNUP=false\n", encoding="utf-8")

    temp_ctx.load_environment(verbose=False)
    temp_ctx.require_settings()

    snapshot = dict(os.environ)
    answers = {
        "ENVIRONMENT": "development",
        "DEBUG": "true",
        "PORT": "8000",
        "APP_PUBLIC_URL": "http://localhost:3000",
        "ALLOWED_HOSTS": "localhost",
        "ALLOWED_ORIGINS": "http://localhost:3000",
        "AUTO_RUN_MIGRATIONS": "false",
        "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/saas_starter_db",
        "API_BASE_URL": "http://127.0.0.1:8000",
        "ROTATE_SIGNING_KEYS": "false",
        "VAULT_VERIFY_ENABLED": "false",
        "OPENAI_API_KEY": "sk-openai",
        "ENABLE_ANTHROPIC_API_KEY": "false",
        "ENABLE_GEMINI_API_KEY": "false",
        "ENABLE_XAI_API_KEY": "false",
        "REDIS_URL": "redis://localhost:6379/0",
        "RATE_LIMIT_REDIS_URL": "",
        "AUTH_CACHE_REDIS_URL": "",
        "SECURITY_TOKEN_REDIS_URL": "",
        "BILLING_EVENTS_REDIS_URL": "",
        "ENABLE_BILLING": "false",
        "ENABLE_BILLING_STREAM": "false",
        "RESEND_EMAIL_ENABLED": "false",
        "RESEND_BASE_URL": "https://api.resend.com",
        "RUN_MIGRATIONS_NOW": "false",
        "TENANT_DEFAULT_SLUG": "local",
        "LOGGING_SINKS": "stdout",
        "GEOIP_PROVIDER": "none",
        "SIGNUP_ACCESS_POLICY": "public",
        "ALLOW_PUBLIC_SIGNUP": "true",
        "ALLOW_SIGNUP_TRIAL_OVERRIDE": "false",
        "SIGNUP_RATE_LIMIT_PER_HOUR": "15",
        "SIGNUP_RATE_LIMIT_PER_IP_DAY": "90",
        "SIGNUP_RATE_LIMIT_PER_EMAIL_DAY": "3",
        "SIGNUP_RATE_LIMIT_PER_DOMAIN_DAY": "20",
        "SIGNUP_CONCURRENT_REQUESTS_LIMIT": "2",
        "SIGNUP_DEFAULT_PLAN_CODE": "starter",
        "SIGNUP_DEFAULT_TRIAL_DAYS": "21",
        "BILLING_RETRY_DEPLOYMENT_MODE": "inline",
        "ENABLE_BILLING_RETRY_WORKER": "true",
        "ENABLE_BILLING_STREAM_REPLAY": "false",
    }

    wizard = _create_setup_wizard(
        ctx=temp_ctx,
        profile="demo",
        output_format="summary",
        input_provider=HeadlessInputProvider(answers=answers),
    )
    wizard.execute()

    settings = temp_ctx.optional_settings()
    assert settings is not None
    assert settings.allow_public_signup is True
    _cleanup_env(snapshot)


def test_wizard_clears_optional_provider_keys(temp_ctx: CLIContext) -> None:
    env_file = backend_env_path(temp_ctx)
    env_file.write_text(
        "\n".join(
            [
                "ANTHROPIC_API_KEY=sk-ant",
                "GEMINI_API_KEY=sk-gem",
                "XAI_API_KEY=sk-xai",
            ]
        ),
        encoding="utf-8",
    )

    snapshot = dict(os.environ)
    answers = {
        "ENVIRONMENT": "development",
        "DEBUG": "true",
        "PORT": "8000",
        "APP_PUBLIC_URL": "http://localhost:3000",
        "ALLOWED_HOSTS": "localhost",
        "ALLOWED_ORIGINS": "http://localhost:3000",
        "AUTO_RUN_MIGRATIONS": "false",
        "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/saas_starter_db",
        "API_BASE_URL": "http://127.0.0.1:8000",
        "ROTATE_SIGNING_KEYS": "false",
        "VAULT_VERIFY_ENABLED": "false",
        "OPENAI_API_KEY": "sk-openai",
        "ENABLE_ANTHROPIC_API_KEY": "false",
        "ENABLE_GEMINI_API_KEY": "false",
        "ENABLE_XAI_API_KEY": "false",
        "REDIS_URL": "redis://localhost:6379/0",
        "RATE_LIMIT_REDIS_URL": "",
        "AUTH_CACHE_REDIS_URL": "",
        "SECURITY_TOKEN_REDIS_URL": "",
        "BILLING_EVENTS_REDIS_URL": "",
        "ENABLE_BILLING": "false",
        "ENABLE_BILLING_STREAM": "false",
        "RESEND_EMAIL_ENABLED": "false",
        "RESEND_BASE_URL": "https://api.resend.com",
        "RUN_MIGRATIONS_NOW": "false",
        "TENANT_DEFAULT_SLUG": "local",
        "LOGGING_SINKS": "stdout",
        "GEOIP_PROVIDER": "none",
        "SIGNUP_ACCESS_POLICY": "public",
        "ALLOW_PUBLIC_SIGNUP": "true",
        "ALLOW_SIGNUP_TRIAL_OVERRIDE": "false",
        "SIGNUP_RATE_LIMIT_PER_HOUR": "15",
        "SIGNUP_RATE_LIMIT_PER_IP_DAY": "90",
        "SIGNUP_RATE_LIMIT_PER_EMAIL_DAY": "3",
        "SIGNUP_RATE_LIMIT_PER_DOMAIN_DAY": "20",
        "SIGNUP_CONCURRENT_REQUESTS_LIMIT": "2",
        "SIGNUP_DEFAULT_PLAN_CODE": "starter",
        "SIGNUP_DEFAULT_TRIAL_DAYS": "21",
        "BILLING_RETRY_DEPLOYMENT_MODE": "inline",
        "ENABLE_BILLING_RETRY_WORKER": "true",
        "ENABLE_BILLING_STREAM_REPLAY": "false",
    }

    wizard = _create_setup_wizard(
        ctx=temp_ctx,
        profile="demo",
        output_format="summary",
        input_provider=HeadlessInputProvider(answers=answers),
    )
    wizard.execute()

    env_body = env_file.read_text(encoding="utf-8")
    assert 'ANTHROPIC_API_KEY=""' in env_body
    assert 'GEMINI_API_KEY=""' in env_body
    assert 'XAI_API_KEY=""' in env_body
    _cleanup_env(snapshot)


def test_wizard_does_not_leak_env_values(temp_ctx: CLIContext) -> None:
    os.environ["ALLOW_PUBLIC_SIGNUP"] = "false"
    baseline_snapshot = dict(os.environ)

    answers = {
        "ENVIRONMENT": "development",
        "DEBUG": "true",
        "PORT": "8000",
        "APP_PUBLIC_URL": "http://localhost:3000",
        "ALLOWED_HOSTS": "localhost",
        "ALLOWED_ORIGINS": "http://localhost:3000",
        "AUTO_RUN_MIGRATIONS": "false",
        "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/saas_starter_db",
        "API_BASE_URL": "http://127.0.0.1:8000",
        "ROTATE_SIGNING_KEYS": "false",
        "VAULT_VERIFY_ENABLED": "false",
        "OPENAI_API_KEY": "sk-openai",
        "ENABLE_ANTHROPIC_API_KEY": "false",
        "ENABLE_GEMINI_API_KEY": "false",
        "ENABLE_XAI_API_KEY": "false",
        "REDIS_URL": "redis://localhost:6379/0",
        "RATE_LIMIT_REDIS_URL": "",
        "AUTH_CACHE_REDIS_URL": "",
        "SECURITY_TOKEN_REDIS_URL": "",
        "BILLING_EVENTS_REDIS_URL": "",
        "ENABLE_BILLING": "false",
        "ENABLE_BILLING_STREAM": "false",
        "RESEND_EMAIL_ENABLED": "false",
        "RESEND_BASE_URL": "https://api.resend.com",
        "RUN_MIGRATIONS_NOW": "false",
        "TENANT_DEFAULT_SLUG": "local",
        "LOGGING_SINKS": "stdout",
        "GEOIP_PROVIDER": "none",
        "SIGNUP_ACCESS_POLICY": "public",
        "ALLOW_PUBLIC_SIGNUP": "true",
        "ALLOW_SIGNUP_TRIAL_OVERRIDE": "false",
        "SIGNUP_RATE_LIMIT_PER_HOUR": "15",
        "SIGNUP_RATE_LIMIT_PER_IP_DAY": "90",
        "SIGNUP_RATE_LIMIT_PER_EMAIL_DAY": "3",
        "SIGNUP_RATE_LIMIT_PER_DOMAIN_DAY": "20",
        "SIGNUP_CONCURRENT_REQUESTS_LIMIT": "2",
        "SIGNUP_DEFAULT_PLAN_CODE": "starter",
        "SIGNUP_DEFAULT_TRIAL_DAYS": "21",
        "BILLING_RETRY_DEPLOYMENT_MODE": "inline",
        "ENABLE_BILLING_RETRY_WORKER": "true",
        "ENABLE_BILLING_STREAM_REPLAY": "false",
    }

    wizard = _create_setup_wizard(
        ctx=temp_ctx,
        profile="demo",
        output_format="summary",
        input_provider=HeadlessInputProvider(answers=answers),
    )
    wizard.execute()
    assert os.environ["ALLOW_PUBLIC_SIGNUP"] == "true"
    assert os.environ["SIGNUP_ACCESS_POLICY"] == "public"

    _cleanup_env(baseline_snapshot)
    assert os.environ["ALLOW_PUBLIC_SIGNUP"] == "false"
    assert "SIGNUP_ACCESS_POLICY" not in os.environ


def test_wizard_rotates_new_peppers(monkeypatch, temp_ctx: CLIContext) -> None:
    env_file = backend_env_path(temp_ctx)
    env_file.write_text(
        "\n".join(
            [
                "AUTH_EMAIL_VERIFICATION_TOKEN_PEPPER=change-me-email",
                "AUTH_PASSWORD_RESET_TOKEN_PEPPER=change-me-reset",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "starter_console.workflows.setup._wizard.context.secrets.token_urlsafe",
        lambda n=32: "rotated-secret",
    )

    answers = {
        "ENVIRONMENT": "development",
        "DEBUG": "true",
        "PORT": "8000",
        "APP_PUBLIC_URL": "http://localhost:3000",
        "ALLOWED_HOSTS": "localhost",
        "ALLOWED_ORIGINS": "http://localhost:3000",
        "AUTO_RUN_MIGRATIONS": "false",
        "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/saas_starter_db",
        "API_BASE_URL": "http://127.0.0.1:8000",
        "ROTATE_SIGNING_KEYS": "false",
        "VAULT_VERIFY_ENABLED": "false",
        "OPENAI_API_KEY": "sk-openai",
        "ENABLE_ANTHROPIC_API_KEY": "false",
        "ENABLE_GEMINI_API_KEY": "false",
        "ENABLE_XAI_API_KEY": "false",
        "REDIS_URL": "redis://localhost:6379/0",
        "RATE_LIMIT_REDIS_URL": "",
        "AUTH_CACHE_REDIS_URL": "",
        "SECURITY_TOKEN_REDIS_URL": "",
        "BILLING_EVENTS_REDIS_URL": "",
        "ENABLE_BILLING": "false",
        "ENABLE_BILLING_STREAM": "false",
        "RESEND_EMAIL_ENABLED": "false",
        "RESEND_BASE_URL": "https://api.resend.com",
        "RUN_MIGRATIONS_NOW": "false",
        "TENANT_DEFAULT_SLUG": "local",
        "LOGGING_SINKS": "stdout",
        "GEOIP_PROVIDER": "none",
        "SIGNUP_ACCESS_POLICY": "public",
        "ALLOW_PUBLIC_SIGNUP": "true",
        "ALLOW_SIGNUP_TRIAL_OVERRIDE": "false",
        "SIGNUP_RATE_LIMIT_PER_HOUR": "15",
        "SIGNUP_RATE_LIMIT_PER_IP_DAY": "90",
        "SIGNUP_RATE_LIMIT_PER_EMAIL_DAY": "3",
        "SIGNUP_RATE_LIMIT_PER_DOMAIN_DAY": "20",
        "SIGNUP_CONCURRENT_REQUESTS_LIMIT": "2",
        "SIGNUP_DEFAULT_PLAN_CODE": "starter",
        "SIGNUP_DEFAULT_TRIAL_DAYS": "21",
        "BILLING_RETRY_DEPLOYMENT_MODE": "inline",
        "ENABLE_BILLING_RETRY_WORKER": "true",
        "ENABLE_BILLING_STREAM_REPLAY": "false",
    }

    wizard = _create_setup_wizard(
        ctx=temp_ctx,
        profile="demo",
        output_format="summary",
        input_provider=HeadlessInputProvider(answers=answers),
    )
    wizard.execute()

    env_body = env_file.read_text(encoding="utf-8")
    assert "AUTH_EMAIL_VERIFICATION_TOKEN_PEPPER=rotated-secret" in env_body
    assert "AUTH_PASSWORD_RESET_TOKEN_PEPPER=rotated-secret" in env_body


def test_wizard_staging_verifies_vault(
    monkeypatch: pytest.MonkeyPatch,
    temp_ctx: CLIContext,
) -> None:
    snapshot = dict(os.environ)
    answers = {
        "SETUP_HOSTING_PRESET": "enterprise_custom",
        "SECRETS_PROVIDER": "vault_hcp",
        "ENVIRONMENT": "staging",
        "DEBUG": "false",
        "PORT": "8000",
        "APP_PUBLIC_URL": "https://staging.example.com",
        "ALLOWED_HOSTS": "staging.example.com",
        "ALLOWED_ORIGINS": "https://staging.example.com",
        "AUTO_RUN_MIGRATIONS": "false",
        "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@staging-db:5432/saas_starter_db",
        "API_BASE_URL": "https://api.staging.example.com",
        "ROTATE_SIGNING_KEYS": "false",
        "VAULT_VERIFY_ENABLED": "true",
        "VAULT_ADDR": "https://vault.example",
        "VAULT_TOKEN": "token",
        "VAULT_TRANSIT_KEY": "auth-service",
        "AUTH_KEY_SECRET_NAME": "auth-signing-secret",
        "AWS_USE_PROFILE": "true",
        "AWS_PROFILE": "staging-profile",
        "AWS_REGION": "us-east-1",
        "OPENAI_API_KEY": "sk-openai",
        "ENABLE_ANTHROPIC_API_KEY": "false",
        "ENABLE_GEMINI_API_KEY": "false",
        "ENABLE_XAI_API_KEY": "false",
        "REDIS_URL": "rediss://:secret@redis.example:6380/0",
        "RATE_LIMIT_REDIS_URL": "rediss://:secret@redis.example:6380/2",
        "AUTH_CACHE_REDIS_URL": "rediss://:secret@redis.example:6380/3",
        "SECURITY_TOKEN_REDIS_URL": "rediss://:secret@redis.example:6380/4",
        "BILLING_EVENTS_REDIS_URL": "rediss://:secret@redis.example:6380/1",
        "ENABLE_BILLING": "false",
        "ENABLE_BILLING_STREAM": "false",
        "RESEND_EMAIL_ENABLED": "false",
        "RESEND_BASE_URL": "https://api.resend.com",
        "RUN_MIGRATIONS_NOW": "false",
        "TENANT_DEFAULT_SLUG": "tenant-staging",
        "LOGGING_SINKS": "none",
        "GEOIP_PROVIDER": "none",
        "SIGNUP_ACCESS_POLICY": "invite_only",
        "ALLOW_PUBLIC_SIGNUP": "false",
        "ALLOW_SIGNUP_TRIAL_OVERRIDE": "false",
        "SIGNUP_RATE_LIMIT_PER_HOUR": "10",
        "SIGNUP_RATE_LIMIT_PER_IP_DAY": "50",
        "SIGNUP_RATE_LIMIT_PER_EMAIL_DAY": "2",
        "SIGNUP_RATE_LIMIT_PER_DOMAIN_DAY": "10",
        "SIGNUP_CONCURRENT_REQUESTS_LIMIT": "1",
        "SIGNUP_DEFAULT_PLAN_CODE": "starter",
        "SIGNUP_DEFAULT_TRIAL_DAYS": "14",
        "BILLING_RETRY_DEPLOYMENT_MODE": "dedicated",
        "ENABLE_BILLING_RETRY_WORKER": "false",
        "ENABLE_BILLING_STREAM_REPLAY": "true",
    }
    called: dict[str, str] = {}

    def fake_request(url: str, headers: dict[str, str]):
        called["url"] = url
        called["token"] = headers["X-Vault-Token"]
        return httpx.Response(200, request=httpx.Request("GET", url))

    monkeypatch.setenv("STARTER_CONSOLE_SKIP_VAULT_PROBE", "false")
    set_vault_probe_request(fake_request)

    wizard = _create_setup_wizard(
        ctx=temp_ctx,
        profile="staging",
        output_format="summary",
        input_provider=HeadlessInputProvider(answers=answers),
    )
    wizard.execute()

    assert called["url"] == "https://vault.example/v1/transit/keys/auth-service"
    assert called["token"] == "token"
    _cleanup_env(snapshot)
    set_vault_probe_request(None)


def test_wizard_summary_writes_milestones(temp_ctx: CLIContext) -> None:
    wizard = _create_setup_wizard(
        ctx=temp_ctx,
        profile="demo",
        output_format="summary",
        input_provider=None,
    )
    summary_path = temp_ctx.project_root / "summary.json"
    wizard.summary_path = summary_path

    sections = [
        SectionResult(
            milestone="M-test",
            focus="Prove summary output uses section fields",
            checks=[
                CheckResult(
                    name="example",
                    status="ok",
                    required=True,
                    detail="all good",
                )
            ],
        )
    ]

    audit.write_summary(wizard.context, sections)
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    assert data["milestones"][0]["milestone"] == "M-test"
    assert data["milestones"][0]["focus"].startswith("Prove summary")
    assert data["milestones"][0]["checks"][0]["name"] == "example"


def test_collect_database_local_compose_derives_database_url(temp_ctx: CLIContext) -> None:
    wizard = _create_setup_wizard(
        ctx=temp_ctx,
        profile="demo",
        output_format="summary",
        input_provider=None,
    )
    snapshot = dict(os.environ)
    provider = HeadlessInputProvider(
        answers={
            "STARTER_LOCAL_DATABASE_MODE": "compose",
            "POSTGRES_PORT": "5433",
            "POSTGRES_USER": "postgres",
            "POSTGRES_PASSWORD": "postgres",
            "POSTGRES_DB": "saas_starter_db",
        }
    )
    provider_section.collect_database(wizard.context, provider)
    assert wizard.context.backend_env.get("STARTER_LOCAL_DATABASE_MODE") == "compose"
    assert wizard.context.backend_env.get("POSTGRES_PORT") == "5433"
    assert (
        wizard.context.backend_env.get("DATABASE_URL")
        == "postgresql+asyncpg://postgres:postgres@localhost:5433/saas_starter_db"
    )
    _cleanup_env(snapshot)


def test_collect_database_local_external_uses_provided_url(temp_ctx: CLIContext) -> None:
    wizard = _create_setup_wizard(
        ctx=temp_ctx,
        profile="demo",
        output_format="summary",
        input_provider=None,
    )
    snapshot = dict(os.environ)
    provider = HeadlessInputProvider(
        answers={
            "STARTER_LOCAL_DATABASE_MODE": "external",
            "DATABASE_URL": "postgresql+asyncpg://remote.example:5432/saas_starter_db",
        }
    )
    provider_section.collect_database(wizard.context, provider)
    assert wizard.context.backend_env.get("STARTER_LOCAL_DATABASE_MODE") == "external"
    assert (
        wizard.context.backend_env.get("DATABASE_URL")
        == "postgresql+asyncpg://remote.example:5432/saas_starter_db"
    )
    assert wizard.context.backend_env.get("POSTGRES_PORT") is None
    _cleanup_env(snapshot)


def test_collect_database_requires_non_local_value(temp_ctx: CLIContext) -> None:
    snapshot = dict(os.environ)
    os.environ.pop("DATABASE_URL", None)
    wizard = _create_setup_wizard(
        ctx=temp_ctx,
        profile="staging",
        output_format="summary",
        input_provider=None,
    )
    provider = HeadlessInputProvider(answers={})
    with pytest.raises(CLIError):
        provider_section.collect_database(wizard.context, provider)
    _cleanup_env(snapshot)


def test_interactive_wizard_runs_tui_alongside_shell(
    monkeypatch: pytest.MonkeyPatch, temp_ctx: CLIContext
) -> None:
    class DummyUI:
        started = False
        stopped = False

        def __init__(self, *, sections, automation, section_prompts=None, enabled=True):
            self.enabled = enabled

        def start(self) -> None:
            DummyUI.started = True

        def stop(self) -> None:
            DummyUI.stopped = True

        def log(self, _: str) -> None:
            return None

        def mark_section(self, *_, **__) -> None:
            return None

        def mark_automation(self, *_, **__) -> None:
            return None

        def sync_prompt_states(self, *_: object) -> None:
            return None

    class DummyInfraSession:
        def __init__(self, *_: object, **__: object) -> None:
            return None

        def ensure_compose(self) -> None:
            return None

        def cleanup(self) -> None:
            return None

    monkeypatch.setattr(wizard_module, "WizardUIView", DummyUI)
    monkeypatch.setattr(wizard_module, "InfraSession", DummyInfraSession)
    monkeypatch.setattr(wizard_module, "run_preflight", lambda *_: None)
    monkeypatch.setattr(SetupWizard, "_configure_automation", lambda self, provider: None)
    monkeypatch.setattr(SetupWizard, "_post_sections", lambda self, provider: None)

    def _dummy_runners(self, provider):
        return {spec.key: (lambda: None) for spec in wizard_module.SECTION_SPECS}

    monkeypatch.setattr(SetupWizard, "_build_section_runners", _dummy_runners)

    presenter = build_headless_presenter(StdConsole())
    provider = InteractiveInputProvider(prefill={}, presenter=presenter)
    wizard = SetupWizard(
        ctx=temp_ctx,
        profile="demo",
        output_format="summary",
        input_provider=provider,
        enable_tui=True,
    )
    wizard.execute()

    assert DummyUI.started is True
    assert DummyUI.stopped is True
