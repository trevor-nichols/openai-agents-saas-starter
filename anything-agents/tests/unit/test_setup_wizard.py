from __future__ import annotations

import json
import os
from pathlib import Path

import httpx
import pytest
from starter_cli.cli.common import CLIContext, CLIError
from starter_cli.cli.setup import HeadlessInputProvider, SetupWizard
from starter_cli.cli.setup._wizard import audit
from starter_cli.cli.setup._wizard.sections import providers as provider_section
from starter_cli.cli.setup.models import CheckResult, SectionResult
from starter_cli.cli.setup.validators import set_vault_probe_request


@pytest.fixture()
def temp_ctx(tmp_path: Path) -> CLIContext:
    env_path = tmp_path / ".env.local"
    env_path.write_text("", encoding="utf-8")
    return CLIContext(project_root=tmp_path, env_files=(env_path,))


def _cleanup_env(snapshot: dict[str, str]) -> None:
    current_keys = set(os.environ.keys())
    for key in current_keys - snapshot.keys():
        os.environ.pop(key, None)
    for key, value in snapshot.items():
        os.environ[key] = value


def test_wizard_headless_local_generates_env(temp_ctx: CLIContext) -> None:
    snapshot = dict(os.environ)
    answers = {
        "ENVIRONMENT": "development",
        "DEBUG": "true",
        "PORT": "8001",
        "APP_PUBLIC_URL": "http://localhost:3000",
        "ALLOWED_HOSTS": "localhost",
        "ALLOWED_ORIGINS": "http://localhost:3000",
        "AUTO_RUN_MIGRATIONS": "false",
        "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/anything_agents",
        "API_BASE_URL": "http://127.0.0.1:8001",
        "ROTATE_SIGNING_KEYS": "false",
        "VAULT_VERIFY_ENABLED": "false",
        "OPENAI_API_KEY": "sk-openai",
        "ENABLE_ANTHROPIC_API_KEY": "false",
        "ENABLE_GEMINI_API_KEY": "false",
        "ENABLE_XAI_API_KEY": "false",
        "ENABLE_TAVILY": "false",
        "REDIS_URL": "redis://localhost:6379/0",
        "BILLING_EVENTS_REDIS_URL": "",
        "ENABLE_BILLING": "false",
        "ENABLE_BILLING_STREAM": "false",
        "RESEND_EMAIL_ENABLED": "false",
        "RESEND_BASE_URL": "https://api.resend.com",
        "RUN_MIGRATIONS_NOW": "false",
        "TENANT_DEFAULT_SLUG": "local",
        "LOGGING_SINK": "stdout",
        "GEOIP_PROVIDER": "none",
        "ALLOW_PUBLIC_SIGNUP": "true",
        "ALLOW_SIGNUP_TRIAL_OVERRIDE": "false",
        "SIGNUP_RATE_LIMIT_PER_HOUR": "15",
        "SIGNUP_DEFAULT_PLAN_CODE": "starter",
        "SIGNUP_DEFAULT_TRIAL_DAYS": "21",
        "ENABLE_BILLING_RETRY_WORKER": "true",
        "ENABLE_BILLING_STREAM_REPLAY": "false",
    }
    wizard = SetupWizard(
        ctx=temp_ctx,
        profile="local",
        output_format="summary",
        input_provider=HeadlessInputProvider(answers=answers),
    )
    wizard.execute()

    env_body = (temp_ctx.project_root / ".env.local").read_text(encoding="utf-8")
    assert "OPENAI_API_KEY" in env_body
    assert "TENANT_DEFAULT_SLUG=local" in env_body
    assert "API_BASE_URL=http://127.0.0.1:8001" in env_body
    assert "LOGGING_SINK=stdout" in env_body
    assert "ALLOW_PUBLIC_SIGNUP=true" in env_body
    assert "BILLING_RETRY_DEPLOYMENT_MODE=inline" in env_body
    assert 'ANTHROPIC_API_KEY=""' in env_body
    assert 'TAVILY_API_KEY=""' in env_body
    _cleanup_env(snapshot)


def test_wizard_refreshes_cached_settings(temp_ctx: CLIContext) -> None:
    # Seed .env.local with an initial value so Settings caches it.
    env_file = temp_ctx.project_root / ".env.local"
    env_file.write_text("ALLOW_PUBLIC_SIGNUP=false\n", encoding="utf-8")

    temp_ctx.load_environment(verbose=False)
    temp_ctx.require_settings()

    snapshot = dict(os.environ)
    answers = {
        "ENVIRONMENT": "development",
        "DEBUG": "true",
        "PORT": "8001",
        "APP_PUBLIC_URL": "http://localhost:3000",
        "ALLOWED_HOSTS": "localhost",
        "ALLOWED_ORIGINS": "http://localhost:3000",
        "AUTO_RUN_MIGRATIONS": "false",
        "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/anything_agents",
        "API_BASE_URL": "http://127.0.0.1:8001",
        "ROTATE_SIGNING_KEYS": "false",
        "VAULT_VERIFY_ENABLED": "false",
        "OPENAI_API_KEY": "sk-openai",
        "ENABLE_ANTHROPIC_API_KEY": "false",
        "ENABLE_GEMINI_API_KEY": "false",
        "ENABLE_XAI_API_KEY": "false",
        "ENABLE_TAVILY": "false",
        "REDIS_URL": "redis://localhost:6379/0",
        "BILLING_EVENTS_REDIS_URL": "",
        "ENABLE_BILLING": "false",
        "ENABLE_BILLING_STREAM": "false",
        "RESEND_EMAIL_ENABLED": "false",
        "RESEND_BASE_URL": "https://api.resend.com",
        "RUN_MIGRATIONS_NOW": "false",
        "TENANT_DEFAULT_SLUG": "local",
        "LOGGING_SINK": "stdout",
        "GEOIP_PROVIDER": "none",
        "ALLOW_PUBLIC_SIGNUP": "true",
        "ALLOW_SIGNUP_TRIAL_OVERRIDE": "false",
        "SIGNUP_RATE_LIMIT_PER_HOUR": "15",
        "SIGNUP_DEFAULT_PLAN_CODE": "starter",
        "SIGNUP_DEFAULT_TRIAL_DAYS": "21",
        "ENABLE_BILLING_RETRY_WORKER": "true",
        "ENABLE_BILLING_STREAM_REPLAY": "false",
    }

    wizard = SetupWizard(
        ctx=temp_ctx,
        profile="local",
        output_format="summary",
        input_provider=HeadlessInputProvider(answers=answers),
    )
    wizard.execute()

    settings = temp_ctx.optional_settings()
    assert settings is not None
    assert settings.allow_public_signup is True
    _cleanup_env(snapshot)


def test_wizard_clears_optional_provider_keys(temp_ctx: CLIContext) -> None:
    env_file = temp_ctx.project_root / ".env.local"
    env_file.write_text(
        "\n".join(
            [
                "ANTHROPIC_API_KEY=sk-ant",
                "GEMINI_API_KEY=sk-gem",
                "XAI_API_KEY=sk-xai",
                "TAVILY_API_KEY=tv-key",
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
        "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/anything_agents",
        "API_BASE_URL": "http://127.0.0.1:8000",
        "ROTATE_SIGNING_KEYS": "false",
        "VAULT_VERIFY_ENABLED": "false",
        "OPENAI_API_KEY": "sk-openai",
        "ENABLE_ANTHROPIC_API_KEY": "false",
        "ENABLE_GEMINI_API_KEY": "false",
        "ENABLE_XAI_API_KEY": "false",
        "ENABLE_TAVILY": "false",
        "REDIS_URL": "redis://localhost:6379/0",
        "BILLING_EVENTS_REDIS_URL": "",
        "ENABLE_BILLING": "false",
        "ENABLE_BILLING_STREAM": "false",
        "RESEND_EMAIL_ENABLED": "false",
        "RESEND_BASE_URL": "https://api.resend.com",
        "RUN_MIGRATIONS_NOW": "false",
        "TENANT_DEFAULT_SLUG": "local",
        "LOGGING_SINK": "stdout",
        "GEOIP_PROVIDER": "none",
        "ALLOW_PUBLIC_SIGNUP": "true",
        "ALLOW_SIGNUP_TRIAL_OVERRIDE": "false",
        "SIGNUP_RATE_LIMIT_PER_HOUR": "15",
        "SIGNUP_DEFAULT_PLAN_CODE": "starter",
        "SIGNUP_DEFAULT_TRIAL_DAYS": "21",
        "ENABLE_BILLING_RETRY_WORKER": "true",
        "ENABLE_BILLING_STREAM_REPLAY": "false",
    }

    wizard = SetupWizard(
        ctx=temp_ctx,
        profile="local",
        output_format="summary",
        input_provider=HeadlessInputProvider(answers=answers),
    )
    wizard.execute()

    env_body = env_file.read_text(encoding="utf-8")
    assert 'ANTHROPIC_API_KEY=""' in env_body
    assert 'GEMINI_API_KEY=""' in env_body
    assert 'XAI_API_KEY=""' in env_body
    assert 'TAVILY_API_KEY=""' in env_body
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
        "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/anything_agents",
        "API_BASE_URL": "http://127.0.0.1:8000",
        "ROTATE_SIGNING_KEYS": "false",
        "VAULT_VERIFY_ENABLED": "false",
        "OPENAI_API_KEY": "sk-openai",
        "ENABLE_ANTHROPIC_API_KEY": "false",
        "ENABLE_GEMINI_API_KEY": "false",
        "ENABLE_XAI_API_KEY": "false",
        "ENABLE_TAVILY": "false",
        "REDIS_URL": "redis://localhost:6379/0",
        "BILLING_EVENTS_REDIS_URL": "",
        "ENABLE_BILLING": "false",
        "ENABLE_BILLING_STREAM": "false",
        "RESEND_EMAIL_ENABLED": "false",
        "RESEND_BASE_URL": "https://api.resend.com",
        "RUN_MIGRATIONS_NOW": "false",
        "TENANT_DEFAULT_SLUG": "local",
        "LOGGING_SINK": "stdout",
        "GEOIP_PROVIDER": "none",
        "ALLOW_PUBLIC_SIGNUP": "true",
        "ALLOW_SIGNUP_TRIAL_OVERRIDE": "false",
        "SIGNUP_RATE_LIMIT_PER_HOUR": "15",
        "SIGNUP_DEFAULT_PLAN_CODE": "starter",
        "SIGNUP_DEFAULT_TRIAL_DAYS": "21",
        "ENABLE_BILLING_RETRY_WORKER": "true",
        "ENABLE_BILLING_STREAM_REPLAY": "false",
    }

    wizard = SetupWizard(
        ctx=temp_ctx,
        profile="local",
        output_format="summary",
        input_provider=HeadlessInputProvider(answers=answers),
    )
    wizard.execute()
    assert os.environ["ALLOW_PUBLIC_SIGNUP"] == "true"

    _cleanup_env(baseline_snapshot)
    assert os.environ["ALLOW_PUBLIC_SIGNUP"] == "false"


def test_wizard_rotates_new_peppers(monkeypatch, temp_ctx: CLIContext) -> None:
    env_file = temp_ctx.project_root / ".env.local"
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
        "starter_cli.cli.setup.wizard.secrets.token_urlsafe",
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
        "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/anything_agents",
        "API_BASE_URL": "http://127.0.0.1:8000",
        "ROTATE_SIGNING_KEYS": "false",
        "VAULT_VERIFY_ENABLED": "false",
        "OPENAI_API_KEY": "sk-openai",
        "ENABLE_ANTHROPIC_API_KEY": "false",
        "ENABLE_GEMINI_API_KEY": "false",
        "ENABLE_XAI_API_KEY": "false",
        "ENABLE_TAVILY": "false",
        "REDIS_URL": "redis://localhost:6379/0",
        "BILLING_EVENTS_REDIS_URL": "",
        "ENABLE_BILLING": "false",
        "ENABLE_BILLING_STREAM": "false",
        "RESEND_EMAIL_ENABLED": "false",
        "RESEND_BASE_URL": "https://api.resend.com",
        "RUN_MIGRATIONS_NOW": "false",
        "TENANT_DEFAULT_SLUG": "local",
        "LOGGING_SINK": "stdout",
        "GEOIP_PROVIDER": "none",
        "ALLOW_PUBLIC_SIGNUP": "true",
        "ALLOW_SIGNUP_TRIAL_OVERRIDE": "false",
        "SIGNUP_RATE_LIMIT_PER_HOUR": "15",
        "SIGNUP_DEFAULT_PLAN_CODE": "starter",
        "SIGNUP_DEFAULT_TRIAL_DAYS": "21",
        "ENABLE_BILLING_RETRY_WORKER": "true",
        "ENABLE_BILLING_STREAM_REPLAY": "false",
    }

    wizard = SetupWizard(
        ctx=temp_ctx,
        profile="local",
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
        "ENVIRONMENT": "staging",
        "DEBUG": "false",
        "PORT": "8000",
        "APP_PUBLIC_URL": "https://staging.example.com",
        "ALLOWED_HOSTS": "staging.example.com",
        "ALLOWED_ORIGINS": "https://staging.example.com",
        "AUTO_RUN_MIGRATIONS": "false",
        "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@staging-db:5432/anything_agents",
        "API_BASE_URL": "https://api.staging.example.com",
        "ROTATE_SIGNING_KEYS": "false",
        "VAULT_VERIFY_ENABLED": "true",
        "VAULT_ADDR": "https://vault.example",
        "VAULT_TOKEN": "token",
        "VAULT_TRANSIT_KEY": "auth-service",
        "OPENAI_API_KEY": "sk-openai",
        "ENABLE_ANTHROPIC_API_KEY": "false",
        "ENABLE_GEMINI_API_KEY": "false",
        "ENABLE_XAI_API_KEY": "false",
        "ENABLE_TAVILY": "false",
        "REDIS_URL": "rediss://:secret@redis.example:6380/0",
        "BILLING_EVENTS_REDIS_URL": "rediss://:secret@redis.example:6380/1",
        "ENABLE_BILLING": "false",
        "ENABLE_BILLING_STREAM": "false",
        "RESEND_EMAIL_ENABLED": "false",
        "RESEND_BASE_URL": "https://api.resend.com",
        "RUN_MIGRATIONS_NOW": "false",
        "TENANT_DEFAULT_SLUG": "tenant-staging",
        "LOGGING_SINK": "none",
        "GEOIP_PROVIDER": "none",
        "ALLOW_PUBLIC_SIGNUP": "false",
        "ALLOW_SIGNUP_TRIAL_OVERRIDE": "false",
        "SIGNUP_RATE_LIMIT_PER_HOUR": "10",
        "SIGNUP_DEFAULT_PLAN_CODE": "starter",
        "SIGNUP_DEFAULT_TRIAL_DAYS": "14",
        "ENABLE_BILLING_RETRY_WORKER": "false",
        "ENABLE_BILLING_STREAM_REPLAY": "true",
    }
    called: dict[str, str] = {}

    def fake_request(url: str, headers: dict[str, str]):
        called["url"] = url
        called["token"] = headers["X-Vault-Token"]
        return httpx.Response(200, request=httpx.Request("GET", url))

    monkeypatch.setenv("STARTER_CLI_SKIP_VAULT_PROBE", "false")
    set_vault_probe_request(fake_request)

    wizard = SetupWizard(
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
    wizard = SetupWizard(
        ctx=temp_ctx,
        profile="local",
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


def test_collect_database_allows_clearing_local(temp_ctx: CLIContext) -> None:
    env_path = temp_ctx.project_root / ".env.local"
    env_path.write_text(
        "DATABASE_URL=postgresql+asyncpg://remote.example/anything_agents\n",
        encoding="utf-8",
    )
    wizard = SetupWizard(
        ctx=temp_ctx,
        profile="local",
        output_format="summary",
        input_provider=None,
    )
    snapshot = dict(os.environ)
    provider = HeadlessInputProvider(answers={"DATABASE_URL": ""})
    provider_section.collect_database(wizard.context, provider)
    assert wizard.context.backend_env.get("DATABASE_URL") is None
    assert "DATABASE_URL" not in os.environ
    _cleanup_env(snapshot)


def test_collect_database_requires_non_local_value(temp_ctx: CLIContext) -> None:
    snapshot = dict(os.environ)
    os.environ.pop("DATABASE_URL", None)
    wizard = SetupWizard(
        ctx=temp_ctx,
        profile="staging",
        output_format="summary",
        input_provider=None,
    )
    provider = HeadlessInputProvider(answers={})
    with pytest.raises(CLIError):
        provider_section.collect_database(wizard.context, provider)
    _cleanup_env(snapshot)
