from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest
from starter_cli.cli.common import CLIContext, CLIError
from starter_cli.cli.env import EnvFile
from starter_cli.cli.secrets import registry as secrets_registry
from starter_cli.cli.secrets.models import OnboardResult
from starter_shared.secrets.models import SecretsProviderLiteral
from starter_cli.cli.setup._wizard import audit
from starter_cli.cli.setup._wizard.context import WizardContext
from starter_cli.cli.setup._wizard.sections import core, frontend, secrets, security
from starter_cli.cli.setup.inputs import InputProvider


@dataclass(slots=True)
class StubProvider(InputProvider):
    strings: dict[str, str] = field(default_factory=dict)
    bools: dict[str, bool] = field(default_factory=dict)
    secrets: dict[str, str] = field(default_factory=dict)

    def prompt_string(self, *, key: str, prompt: str, default: str | None, required: bool) -> str:
        if key in self.strings:
            return self.strings[key]
        if default is not None:
            return default
        return ""

    def prompt_bool(self, *, key: str, prompt: str, default: bool) -> bool:
        return self.bools.get(key, default)

    def prompt_secret(
        self,
        *,
        key: str,
        prompt: str,
        existing: str | None,
        required: bool,
    ) -> str:
        if key in self.secrets:
            return self.secrets[key]
        if existing:
            return existing
        if required:
            raise CLIError(f"Missing required secret for {key}")
        return ""


@pytest.fixture()
def cli_ctx(tmp_path: Path) -> CLIContext:
    project_root = tmp_path
    env_path = project_root / ".env.local"
    env_path.write_text("", encoding="utf-8")
    return CLIContext(project_root=project_root, env_files=(env_path,))


def _build_context(cli_ctx: CLIContext, *, profile: str = "local") -> WizardContext:
    backend_env = EnvFile(cli_ctx.project_root / ".env.local")
    return WizardContext(
        cli_ctx=cli_ctx,
        profile=profile,
        backend_env=backend_env,
        frontend_env=None,
        frontend_path=None,
    )


def test_core_section_sets_api_base_url(cli_ctx: CLIContext) -> None:
    context = _build_context(cli_ctx)
    provider = StubProvider(
        strings={
            "ENVIRONMENT": "development",
            "PORT": "8123",
            "APP_PUBLIC_URL": "http://localhost:3000",
            "ALLOWED_HOSTS": "localhost",
            "ALLOWED_ORIGINS": "http://localhost:3000",
            "API_BASE_URL": "http://127.0.0.1:8123",
        },
        bools={"DEBUG": True, "AUTO_RUN_MIGRATIONS": False},
    )

    core.run(context, provider)

    assert context.backend_env.get("API_BASE_URL") == "http://127.0.0.1:8123"
    assert context.api_base_url == "http://127.0.0.1:8123"
    assert context.backend_env.get("DEBUG") == "true"


def test_core_section_extended_prompts(cli_ctx: CLIContext) -> None:
    context = _build_context(cli_ctx)
    provider = StubProvider(
        strings={
            "ENVIRONMENT": "staging",
            "PORT": "9000",
            "APP_PUBLIC_URL": "https://example.com",
            "ALLOWED_HOSTS": "example.com",
            "ALLOWED_ORIGINS": "https://example.com",
            "ALLOWED_METHODS": "GET,POST",
            "ALLOWED_HEADERS": "Content-Type,Authorization",
            "API_BASE_URL": "https://api.example.com",
            "APP_NAME": "Acme AI",
            "APP_DESCRIPTION": "Acme Agents Backend",
            "APP_VERSION": "2.1.0",
            "AUTH_AUDIENCE": "agent-api,billing",
            "JWT_ALGORITHM": "EdDSA",
            "AUTH_KEY_STORAGE_BACKEND": "secret-manager",
            "AUTH_KEY_STORAGE_PATH": "/secrets/keyset",
            "AUTH_KEY_SECRET_NAME": "kv/signing",
            "DATABASE_POOL_SIZE": "12",
            "DATABASE_MAX_OVERFLOW": "4",
            "DATABASE_POOL_RECYCLE": "900",
            "DATABASE_POOL_TIMEOUT": "45.5",
            "DATABASE_HEALTH_TIMEOUT": "7.5",
            "LOG_LEVEL": "DEBUG",
        },
        bools={
            "DEBUG": False,
            "AUTO_RUN_MIGRATIONS": True,
            "DATABASE_ECHO": True,
        },
    )

    core.run(context, provider)

    env = context.backend_env
    assert env.get("APP_NAME") == "Acme AI"
    assert env.get("ALLOWED_METHODS") == "GET,POST"
    assert env.get("AUTH_AUDIENCE") == "agent-api,billing"
    assert env.get("AUTH_KEY_STORAGE_BACKEND") == "secret-manager"
    assert env.get("AUTH_KEY_SECRET_NAME") == "kv/signing"
    assert env.get("DATABASE_POOL_SIZE") == "12"
    assert env.get("DATABASE_POOL_TIMEOUT") == "45.5"
    assert env.get("LOG_LEVEL") == "DEBUG"


def test_secrets_section_generates_missing_peppers(cli_ctx: CLIContext) -> None:
    context = _build_context(cli_ctx)
    provider = StubProvider(strings={"AUTH_SESSION_IP_HASH_SALT": ""})

    secrets.run(context, provider)

    assert context.backend_env.get("SECRET_KEY")
    assert context.backend_env.get("AUTH_PASSWORD_PEPPER")
    assert context.backend_env.get("AUTH_SESSION_ENCRYPTION_KEY")
    assert context.backend_env.get("SECRETS_PROVIDER") == "vault_dev"


def test_frontend_section_writes_env_values(cli_ctx: CLIContext, tmp_path: Path) -> None:
    frontend_dir = tmp_path / "agent-next-15-frontend"
    frontend_dir.mkdir(parents=True, exist_ok=True)
    frontend_env_path = frontend_dir / ".env.local"
    frontend_env = EnvFile(frontend_env_path)
    context = WizardContext(
        cli_ctx=cli_ctx,
        profile="staging",
        backend_env=EnvFile(cli_ctx.project_root / ".env.local"),
        frontend_env=frontend_env,
        frontend_path=frontend_env_path,
    )
    context.api_base_url = "http://internal.example"
    provider = StubProvider(
        strings={"PLAYWRIGHT_BASE_URL": "http://ui.example"},
        bools={
            "AGENT_API_MOCK": False,
            "AGENT_FORCE_SECURE_COOKIES": True,
            "AGENT_ALLOW_INSECURE_COOKIES": False,
        },
    )

    frontend.configure(context, provider)

    assert frontend_env.get("NEXT_PUBLIC_API_URL") == "http://internal.example"
    assert frontend_env.get("PLAYWRIGHT_BASE_URL") == "http://ui.example"
    assert frontend_env.get("AGENT_FORCE_SECURE_COOKIES") == "true"
    assert frontend_env.get("AGENT_ALLOW_INSECURE_COOKIES") == "false"


def test_security_section_populates_limits_and_secrets(cli_ctx: CLIContext) -> None:
    context = _build_context(cli_ctx)
    provider = StubProvider(
        strings={
            "AUTH_IP_LOCKOUT_THRESHOLD": "25",
            "CHAT_RATE_LIMIT_PER_MINUTE": "120",
            "RATE_LIMIT_KEY_PREFIX": "enterprise",
        }
    )

    security.run(context, provider)

    assert context.backend_env.get("AUTH_IP_LOCKOUT_THRESHOLD") == "25"
    assert context.backend_env.get("CHAT_RATE_LIMIT_PER_MINUTE") == "120"
    assert context.backend_env.get("RATE_LIMIT_KEY_PREFIX") == "enterprise"
    assert context.backend_env.get("AUTH_JWKS_ETAG_SALT")
    assert context.backend_env.get("STATUS_SUBSCRIPTION_ENCRYPTION_KEY")
    assert context.backend_env.get("STATUS_SUBSCRIPTION_TOKEN_PEPPER")


def test_audit_sections_flag_missing_values(cli_ctx: CLIContext) -> None:
    context = _build_context(cli_ctx, profile="production")
    context.set_backend("OPENAI_API_KEY", "sk-test", mask=True)
    # Ensure peppers aren't already present from other tests
    context.unset_backend("AUTH_PASSWORD_PEPPER")
    context.unset_backend("AUTH_REFRESH_TOKEN_PEPPER")

    sections = audit.build_sections(context)

    secrets_section = sections[0]
    statuses = {check.name: check.status for check in secrets_section.checks}
    assert statuses["AUTH_PASSWORD_PEPPER"] in {"warning", "missing"}
    assert statuses["VAULT_ADDR"] == "missing"
def test_secrets_section_runs_non_vault_provider(monkeypatch, cli_ctx: CLIContext) -> None:
    context = _build_context(cli_ctx)
    provider = StubProvider(strings={"SECRETS_PROVIDER": "infisical_cloud"})

    def fake_runner(ctx, input_provider, *, options):
        assert options.skip_make
        return OnboardResult(
            provider=SecretsProviderLiteral.INFISICAL_CLOUD,
            env_updates={
                "SECRETS_PROVIDER": "infisical_cloud",
                "INFISICAL_BASE_URL": "https://app.infisical.dev",
            },
            steps=[],
            warnings=[],
            artifacts=None,
        )

    monkeypatch.setattr(secrets_registry, "get_runner", lambda literal: fake_runner)

    secrets.run(context, provider)

    assert context.backend_env.get("SECRETS_PROVIDER") == "infisical_cloud"
    assert context.backend_env.get("INFISICAL_BASE_URL") == "https://app.infisical.dev"
