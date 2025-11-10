from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from starter_shared.config import StarterSettingsProtocol, get_settings

from ..auth_commands import handle_keys_rotate
from ..common import CLIContext, CLIError
from ..console import console
from ..env import EnvFile
from .inputs import InputProvider
from .models import CheckResult, SectionResult
from .validators import (
    normalize_geoip_provider,
    normalize_logging_sink,
    parse_positive_int,
    probe_vault_transit,
    validate_plan_map,
    validate_redis_url,
)

PROFILE_CHOICES = ("local", "staging", "production")
FRONTEND_ENV_RELATIVE = Path("agent-next-15-frontend/.env.local")


@dataclass(slots=True)
class SetupWizard:
    ctx: CLIContext
    profile: str
    output_format: str
    input_provider: InputProvider | None
    backend_env: EnvFile = field(init=False)
    frontend_env: EnvFile | None = field(init=False)
    frontend_path: Path | None = field(init=False)
    api_base_url: str = field(init=False, default="http://127.0.0.1:8000")
    _is_headless: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        backend_path = self.ctx.project_root / ".env.local"
        backend_path.parent.mkdir(parents=True, exist_ok=True)
        self.backend_env = EnvFile(backend_path)

        frontend_path = self.ctx.project_root / FRONTEND_ENV_RELATIVE
        if frontend_path.parent.exists():
            self.frontend_env = EnvFile(frontend_path)
            self.frontend_path = frontend_path
        else:
            self.frontend_env = None
            self.frontend_path = None

    # ------------------------------------------------------------------
    # Public entrypoints
    # ------------------------------------------------------------------
    def execute(self) -> None:
        provider = self._require_inputs()
        self._is_headless = hasattr(provider, "answers")
        console.info("Starting setup wizard …", topic="wizard")
        self._collect_core(provider)
        self._run_m1(provider)
        self._run_m2(provider)
        self._run_m3(provider)
        self._run_m4(provider)
        self._collect_frontend(provider)

        self.backend_env.save()
        console.success("Updated .env.local", topic="wizard")
        if self.frontend_env:
            self.frontend_env.save()
            console.success("Updated agent-next-15-frontend/.env.local", topic="wizard")
        elif self.frontend_path:
            console.warn(
                "Frontend directory missing; skipped agent-next-15-frontend/.env.local.",
                topic="wizard",
            )

        self.ctx.load_environment(verbose=False)
        self._refresh_settings_cache()
        sections = self._build_sections()
        self._render(sections)

    def render_report(self) -> None:
        sections = self._build_sections()
        self._render(sections)

    # ------------------------------------------------------------------
    # Core + milestones
    # ------------------------------------------------------------------
    def _collect_core(self, provider: InputProvider) -> None:
        console.info("[Core] Deployment metadata", topic="wizard")
        env_default = {
            "local": "development",
            "staging": "staging",
            "production": "production",
        }[self.profile]
        environment = provider.prompt_string(
            key="ENVIRONMENT",
            prompt="Environment label (ENVIRONMENT)",
            default=self._current("ENVIRONMENT") or env_default,
            required=True,
        )
        self._set_backend("ENVIRONMENT", environment)

        debug_default = self._current_bool("DEBUG", default=self.profile == "local")
        debug = provider.prompt_bool(
            key="DEBUG",
            prompt="Enable FastAPI debug mode?",
            default=debug_default,
        )
        self._set_backend_bool("DEBUG", debug)

        port = provider.prompt_string(
            key="PORT",
            prompt="FastAPI port (PORT)",
            default=self._current("PORT") or "8000",
            required=True,
        )
        self._set_backend("PORT", port)

        app_public_url = provider.prompt_string(
            key="APP_PUBLIC_URL",
            prompt="Public site base URL (APP_PUBLIC_URL)",
            default=self._current("APP_PUBLIC_URL") or "http://localhost:3000",
            required=True,
        )
        self._set_backend("APP_PUBLIC_URL", app_public_url)

        allowed_hosts = provider.prompt_string(
            key="ALLOWED_HOSTS",
            prompt="Allowed hosts (comma-separated)",
            default=self._current("ALLOWED_HOSTS")
            or "localhost,localhost:8000,127.0.0.1,testserver,testclient",
            required=True,
        )
        self._set_backend("ALLOWED_HOSTS", allowed_hosts)

        allowed_origins = provider.prompt_string(
            key="ALLOWED_ORIGINS",
            prompt="Allowed origins (comma-separated)",
            default=self._current("ALLOWED_ORIGINS") or "http://localhost:3000,http://localhost:8000",
            required=True,
        )
        self._set_backend("ALLOWED_ORIGINS", allowed_origins)

        auto_run = provider.prompt_bool(
            key="AUTO_RUN_MIGRATIONS",
            prompt="Automatically run migrations on startup?",
            default=self._current_bool("AUTO_RUN_MIGRATIONS", default=self.profile == "local"),
        )
        self._set_backend_bool("AUTO_RUN_MIGRATIONS", auto_run)

        port_int = int(port) if port.isdigit() else 8000
        self.api_base_url = provider.prompt_string(
            key="API_BASE_URL",
            prompt="API base URL for frontend + tooling",
            default=self._current("API_BASE_URL") or f"http://127.0.0.1:{port_int}",
            required=True,
        )
        self._set_backend("API_BASE_URL", self.api_base_url)

    def _run_m1(self, provider: InputProvider) -> None:
        console.info("[M1] Secrets & Vault", topic="wizard")
        self._collect_secrets(provider)
        rotate = provider.prompt_bool(
            key="ROTATE_SIGNING_KEYS",
            prompt="Rotate the Ed25519 signing keyset now?",
            default=False,
        )
        if rotate:
            self._rotate_signing_keys()
        self._collect_vault(provider)
        if self._current_bool("VAULT_VERIFY_ENABLED", False):
            probe_vault_transit(
                base_url=self._require_env("VAULT_ADDR"),
                token=self._require_env("VAULT_TOKEN"),
                key_name=self._require_env("VAULT_TRANSIT_KEY"),
            )
            console.success("Vault transit key verified.", topic="vault")

    def _run_m2(self, provider: InputProvider) -> None:
        console.info("[M2] Providers & Infra", topic="wizard")
        self._collect_ai_providers(provider)
        self._collect_redis(provider)
        self._collect_billing(provider)
        self._collect_email(provider)
        self._maybe_run_migrations(provider)

    def _run_m3(self, provider: InputProvider) -> None:
        console.info("[M3] Tenant & Observability", topic="wizard")
        slug = provider.prompt_string(
            key="TENANT_DEFAULT_SLUG",
            prompt="Default tenant slug",
            default=self._current("TENANT_DEFAULT_SLUG") or "default",
            required=True,
        )
        self._set_backend("TENANT_DEFAULT_SLUG", slug)

        sink = normalize_logging_sink(
            provider.prompt_string(
                key="LOGGING_SINK",
                prompt="Logging sink (stdout/datadog/otlp/none)",
                default=self._current("LOGGING_SINK") or "stdout",
                required=True,
            )
        )
        self._set_backend("LOGGING_SINK", sink)
        if sink == "datadog":
            api_key = provider.prompt_secret(
                key="LOGGING_DATADOG_API_KEY",
                prompt="Datadog API key",
                existing=self._current("LOGGING_DATADOG_API_KEY"),
                required=True,
            )
            site = provider.prompt_string(
                key="LOGGING_DATADOG_SITE",
                prompt="Datadog site (e.g., datadoghq.com)",
                default=self._current("LOGGING_DATADOG_SITE") or "datadoghq.com",
                required=True,
            )
            self._set_backend("LOGGING_DATADOG_API_KEY", api_key, mask=True)
            self._set_backend("LOGGING_DATADOG_SITE", site)
        elif sink == "otlp":
            endpoint = provider.prompt_string(
                key="LOGGING_OTLP_ENDPOINT",
                prompt="OTLP/HTTP endpoint",
                default=self._current("LOGGING_OTLP_ENDPOINT") or "https://collector.example/v1/logs",
                required=True,
            )
            headers = provider.prompt_string(
                key="LOGGING_OTLP_HEADERS",
                prompt="OTLP headers JSON (optional)",
                default=self._current("LOGGING_OTLP_HEADERS") or "",
                required=False,
            )
            self._set_backend("LOGGING_OTLP_ENDPOINT", endpoint)
            if headers:
                self._set_backend("LOGGING_OTLP_HEADERS", headers)

        geo = normalize_geoip_provider(
            provider.prompt_string(
                key="GEOIP_PROVIDER",
                prompt="GeoIP provider (none/maxmind/ip2location)",
                default=self._current("GEOIP_PROVIDER") or "none",
                required=True,
            )
        )
        self._set_backend("GEOIP_PROVIDER", geo)
        if geo == "maxmind":
            license_key = provider.prompt_secret(
                key="GEOIP_MAXMIND_LICENSE_KEY",
                prompt="MaxMind license key",
                existing=self._current("GEOIP_MAXMIND_LICENSE_KEY"),
                required=True,
            )
            self._set_backend("GEOIP_MAXMIND_LICENSE_KEY", license_key, mask=True)
        elif geo == "ip2location":
            api_key = provider.prompt_secret(
                key="GEOIP_IP2LOCATION_API_KEY",
                prompt="IP2Location API key",
                existing=self._current("GEOIP_IP2LOCATION_API_KEY"),
                required=True,
            )
            self._set_backend("GEOIP_IP2LOCATION_API_KEY", api_key, mask=True)

    def _run_m4(self, provider: InputProvider) -> None:
        console.info("[M4] Signup & Worker policy", topic="wizard")
        allow_public = provider.prompt_bool(
            key="ALLOW_PUBLIC_SIGNUP",
            prompt="Allow public signup?",
            default=self._current_bool("ALLOW_PUBLIC_SIGNUP", True),
        )
        self._set_backend_bool("ALLOW_PUBLIC_SIGNUP", allow_public)

        allow_override = provider.prompt_bool(
            key="ALLOW_SIGNUP_TRIAL_OVERRIDE",
            prompt="Allow clients to request custom trial lengths?",
            default=self._current_bool("ALLOW_SIGNUP_TRIAL_OVERRIDE", False),
        )
        self._set_backend_bool("ALLOW_SIGNUP_TRIAL_OVERRIDE", allow_override)

        rate_limit = parse_positive_int(
            provider.prompt_string(
                key="SIGNUP_RATE_LIMIT_PER_HOUR",
                prompt="Signup attempts per hour (per IP)",
                default=self._current("SIGNUP_RATE_LIMIT_PER_HOUR") or "20",
                required=True,
            ),
            field="SIGNUP_RATE_LIMIT_PER_HOUR",
            minimum=1,
        )
        self._set_backend("SIGNUP_RATE_LIMIT_PER_HOUR", str(rate_limit))

        plan_code = provider.prompt_string(
            key="SIGNUP_DEFAULT_PLAN_CODE",
            prompt="Default signup plan code",
            default=self._current("SIGNUP_DEFAULT_PLAN_CODE") or "starter",
            required=True,
        )
        self._set_backend("SIGNUP_DEFAULT_PLAN_CODE", plan_code)

        trial_days = parse_positive_int(
            provider.prompt_string(
                key="SIGNUP_DEFAULT_TRIAL_DAYS",
                prompt="Default trial days",
                default=self._current("SIGNUP_DEFAULT_TRIAL_DAYS") or "14",
                required=True,
            ),
            field="SIGNUP_DEFAULT_TRIAL_DAYS",
            minimum=1,
        )
        self._set_backend("SIGNUP_DEFAULT_TRIAL_DAYS", str(trial_days))

        run_retry_here = provider.prompt_bool(
            key="ENABLE_BILLING_RETRY_WORKER",
            prompt="Run the Stripe retry worker inside this deployment?",
            default=self._current_bool("ENABLE_BILLING_RETRY_WORKER", True),
        )
        self._set_backend_bool("ENABLE_BILLING_RETRY_WORKER", run_retry_here)
        deployment_mode = "inline" if run_retry_here else "dedicated"
        self._set_backend("BILLING_RETRY_DEPLOYMENT_MODE", deployment_mode)

        replay_stream = provider.prompt_bool(
            key="ENABLE_BILLING_STREAM_REPLAY",
            prompt="Replay Stripe events from Redis on startup?",
            default=self._current_bool("ENABLE_BILLING_STREAM_REPLAY", True),
        )
        self._set_backend_bool("ENABLE_BILLING_STREAM_REPLAY", replay_stream)

    # ------------------------------------------------------------------
    # Interactive building blocks
    # ------------------------------------------------------------------
    def _collect_secrets(self, provider: InputProvider) -> None:
        self._ensure_secret(provider, "SECRET_KEY", "Application SECRET_KEY")
        self._ensure_secret(
            provider,
            "AUTH_PASSWORD_PEPPER",
            "Password hashing pepper",
        )
        self._ensure_secret(
            provider,
            "AUTH_REFRESH_TOKEN_PEPPER",
            "Refresh token pepper",
        )
        self._ensure_secret(
            provider,
            "AUTH_EMAIL_VERIFICATION_TOKEN_PEPPER",
            "Email verification token pepper",
        )
        self._ensure_secret(
            provider,
            "AUTH_PASSWORD_RESET_TOKEN_PEPPER",
            "Password reset token pepper",
        )
        self._ensure_secret(
            provider,
            "AUTH_SESSION_ENCRYPTION_KEY",
            "Session encryption key",
            length=64,
        )
        salt_default = self._current("AUTH_SESSION_IP_HASH_SALT") or ""
        salt_value = provider.prompt_string(
            key="AUTH_SESSION_IP_HASH_SALT",
            prompt="Session IP hash salt (optional)",
            default=salt_default,
            required=False,
        )
        if salt_value:
            self._set_backend("AUTH_SESSION_IP_HASH_SALT", salt_value)

    def _collect_ai_providers(self, provider: InputProvider) -> None:
        openai_key = provider.prompt_secret(
            key="OPENAI_API_KEY",
            prompt="OpenAI API key (required)",
            existing=self._current("OPENAI_API_KEY"),
            required=True,
        )
        self._set_backend("OPENAI_API_KEY", openai_key, mask=True)

        for key, label in (
            ("ANTHROPIC_API_KEY", "Anthropic API key"),
            ("GEMINI_API_KEY", "Google Gemini API key"),
            ("XAI_API_KEY", "xAI API key"),
        ):
            default_enabled = bool(self._current(key))
            if provider.prompt_bool(
                key=f"ENABLE_{key}",
                prompt=f"Configure {label}?",
                default=default_enabled,
            ):
                value = provider.prompt_secret(
                    key=key,
                    prompt=label,
                    existing=self._current(key),
                    required=False,
                )
                if value:
                    self._set_backend(key, value, mask=True)
                else:
                    self._set_backend(key, "")
            else:
                self._set_backend(key, "")

        if provider.prompt_bool(
            key="ENABLE_TAVILY",
            prompt="Enable Tavily search tools?",
            default=bool(self._current("TAVILY_API_KEY")),
        ):
            tavily_key = provider.prompt_secret(
                key="TAVILY_API_KEY",
                prompt="Tavily API key",
                existing=self._current("TAVILY_API_KEY"),
                required=False,
            )
            if tavily_key:
                self._set_backend("TAVILY_API_KEY", tavily_key, mask=True)
            else:
                self._set_backend("TAVILY_API_KEY", "")
        else:
            self._set_backend("TAVILY_API_KEY", "")

    def _collect_redis(self, provider: InputProvider) -> None:
        primary = provider.prompt_string(
            key="REDIS_URL",
            prompt="Primary Redis URL",
            default=self._current("REDIS_URL") or "redis://localhost:6379/0",
            required=True,
        )
        validate_redis_url(primary, require_tls=self.profile != "local", role="Primary")
        self._set_backend("REDIS_URL", primary)

        billing = provider.prompt_string(
            key="BILLING_EVENTS_REDIS_URL",
            prompt="Billing events Redis URL (blank = reuse primary)",
            default=self._current("BILLING_EVENTS_REDIS_URL") or "",
            required=False,
        )
        if billing:
            validate_redis_url(billing, require_tls=self.profile != "local", role="Billing events")
            self._set_backend("BILLING_EVENTS_REDIS_URL", billing)
        else:
            self._set_backend("BILLING_EVENTS_REDIS_URL", "")
            if self.profile != "local":
                console.warn(
                    "Using the primary Redis instance for billing streams."
                    " Provision a dedicated instance for production.",
                    topic="redis",
                )

    def _collect_billing(self, provider: InputProvider) -> None:
        enable_billing = provider.prompt_bool(
            key="ENABLE_BILLING",
            prompt="Enable billing endpoints now?",
            default=self._current_bool("ENABLE_BILLING", False),
        )
        self._set_backend_bool("ENABLE_BILLING", enable_billing)

        enable_stream = provider.prompt_bool(
            key="ENABLE_BILLING_STREAM",
            prompt="Enable billing stream (Redis SSE)?",
            default=self._current_bool("ENABLE_BILLING_STREAM", False),
        )
        self._set_backend_bool("ENABLE_BILLING_STREAM", enable_stream)

        if enable_billing:
            secret = provider.prompt_secret(
                key="STRIPE_SECRET_KEY",
                prompt="Stripe secret key",
                existing=self._current("STRIPE_SECRET_KEY"),
                required=True,
            )
            webhook = provider.prompt_secret(
                key="STRIPE_WEBHOOK_SECRET",
                prompt="Stripe webhook signing secret",
                existing=self._current("STRIPE_WEBHOOK_SECRET"),
                required=True,
            )
            plan_map_raw = provider.prompt_string(
                key="STRIPE_PRODUCT_PRICE_MAP",
                prompt="Stripe product price map (JSON)",
                default=self._current("STRIPE_PRODUCT_PRICE_MAP")
                or '{"starter":"price_xxx","pro":"price_xxx"}',
                required=True,
            )
            validated = validate_plan_map(plan_map_raw)
            self._set_backend("STRIPE_SECRET_KEY", secret, mask=True)
            self._set_backend("STRIPE_WEBHOOK_SECRET", webhook, mask=True)
            self._set_backend(
                "STRIPE_PRODUCT_PRICE_MAP",
                json.dumps(validated, separators=(",", ":")),
            )

            if not self._is_headless:
                should_seed = provider.prompt_bool(
                    key="RUN_STRIPE_SEED",
                    prompt="Run the Stripe setup helper now?",
                    default=False,
                )
                if should_seed:
                    self._run_subprocess(
                        ["python", "-m", "starter_cli.cli", "stripe", "setup"],
                        topic="stripe",
                    )
            else:
                console.warn(
                    "Headless run detected. Run `python -m starter_cli.cli stripe setup` "
                    "manually to seed plans.",
                    topic="stripe",
                )
        else:
            console.info("Stripe secrets skipped (ENABLE_BILLING=false).", topic="wizard")

    def _collect_email(self, provider: InputProvider) -> None:
        enable_resend = provider.prompt_bool(
            key="RESEND_EMAIL_ENABLED",
            prompt="Enable Resend email delivery?",
            default=self._current_bool("RESEND_EMAIL_ENABLED", False),
        )
        self._set_backend_bool("RESEND_EMAIL_ENABLED", enable_resend)
        base_url = provider.prompt_string(
            key="RESEND_BASE_URL",
            prompt="Resend API base URL",
            default=self._current("RESEND_BASE_URL") or "https://api.resend.com",
            required=True,
        )
        self._set_backend("RESEND_BASE_URL", base_url)
        if enable_resend:
            api_key = provider.prompt_secret(
                key="RESEND_API_KEY",
                prompt="Resend API key",
                existing=self._current("RESEND_API_KEY"),
                required=True,
            )
            default_from = provider.prompt_string(
                key="RESEND_DEFAULT_FROM",
                prompt="Default From address",
                default=self._current("RESEND_DEFAULT_FROM") or "support@example.com",
                required=True,
            )
            template_verify = provider.prompt_string(
                key="RESEND_EMAIL_VERIFICATION_TEMPLATE_ID",
                prompt="Verification template ID (optional)",
                default=self._current("RESEND_EMAIL_VERIFICATION_TEMPLATE_ID") or "",
                required=False,
            )
            template_reset = provider.prompt_string(
                key="RESEND_PASSWORD_RESET_TEMPLATE_ID",
                prompt="Password reset template ID (optional)",
                default=self._current("RESEND_PASSWORD_RESET_TEMPLATE_ID") or "",
                required=False,
            )
            self._set_backend("RESEND_API_KEY", api_key, mask=True)
            self._set_backend("RESEND_DEFAULT_FROM", default_from)
            self._set_backend("RESEND_EMAIL_VERIFICATION_TEMPLATE_ID", template_verify)
            self._set_backend("RESEND_PASSWORD_RESET_TEMPLATE_ID", template_reset)

    def _collect_vault(self, provider: InputProvider) -> None:
        require_vault = self.profile in {"staging", "production"}
        default_vault = self._current_bool("VAULT_VERIFY_ENABLED", require_vault)
        enable_vault = provider.prompt_bool(
            key="VAULT_VERIFY_ENABLED",
            prompt="Enforce Vault Transit verification?",
            default=default_vault,
        )
        if require_vault and not enable_vault:
            raise CLIError("Vault verification is mandatory outside local environments.")
        self._set_backend_bool("VAULT_VERIFY_ENABLED", enable_vault)
        if enable_vault:
            addr = provider.prompt_string(
                key="VAULT_ADDR",
                prompt="Vault address",
                default=self._current("VAULT_ADDR") or "https://vault.example.com",
                required=True,
            )
            token = provider.prompt_secret(
                key="VAULT_TOKEN",
                prompt="Vault token/AppRole secret",
                existing=self._current("VAULT_TOKEN"),
                required=True,
            )
            transit = provider.prompt_string(
                key="VAULT_TRANSIT_KEY",
                prompt="Vault Transit key name",
                default=self._current("VAULT_TRANSIT_KEY") or "auth-service",
                required=True,
            )
            self._set_backend("VAULT_ADDR", addr)
            self._set_backend("VAULT_TOKEN", token, mask=True)
            self._set_backend("VAULT_TRANSIT_KEY", transit)

    def _collect_frontend(self, provider: InputProvider) -> None:
        if not self.frontend_env:
            return
        console.info("[Frontend] Next.js env", topic="wizard")
        self._set_frontend("NEXT_PUBLIC_API_URL", self.api_base_url)
        playwright_default = self.frontend_env.get("PLAYWRIGHT_BASE_URL") or "http://localhost:3000"
        playwright = provider.prompt_string(
            key="PLAYWRIGHT_BASE_URL",
            prompt="Playwright base URL",
            default=playwright_default,
            required=True,
        )
        self._set_frontend("PLAYWRIGHT_BASE_URL", playwright)

        use_mock = provider.prompt_bool(
            key="AGENT_API_MOCK",
            prompt="Use mock API responses in Next.js?",
            default=self._current_frontend_bool("AGENT_API_MOCK", False),
        )
        self._set_frontend_bool("AGENT_API_MOCK", use_mock)

        force_secure = provider.prompt_bool(
            key="AGENT_FORCE_SECURE_COOKIES",
            prompt="Force secure cookies on the frontend?",
            default=self._current_frontend_bool(
                "AGENT_FORCE_SECURE_COOKIES",
                self.profile != "local",
            ),
        )
        self._set_frontend_bool("AGENT_FORCE_SECURE_COOKIES", force_secure)

        allow_insecure = provider.prompt_bool(
            key="AGENT_ALLOW_INSECURE_COOKIES",
            prompt="Allow insecure cookies (helps local dev without HTTPS)?",
            default=self._current_frontend_bool(
                "AGENT_ALLOW_INSECURE_COOKIES",
                self.profile == "local",
            ),
        )
        self._set_frontend_bool("AGENT_ALLOW_INSECURE_COOKIES", allow_insecure)

    # ------------------------------------------------------------------
    # Infra helpers
    # ------------------------------------------------------------------
    def _maybe_run_migrations(self, provider: InputProvider) -> None:
        run_now = provider.prompt_bool(
            key="RUN_MIGRATIONS_NOW",
            prompt="Run `make migrate` now?",
            default=self.profile != "local",
        )
        if not run_now:
            return
        self._run_subprocess(["make", "migrate"], topic="migrate")

    def _rotate_signing_keys(self) -> None:
        result = handle_keys_rotate(argparse.Namespace(kid=None), self.ctx)
        if result != 0:
            raise CLIError("Key rotation failed; see logs above.")

    def _run_subprocess(self, cmd: list[str], *, topic: str, check: bool = True) -> None:
        console.info(" ".join(cmd), topic=topic)
        subprocess.run(cmd, check=check, cwd=self.ctx.project_root)

    def _refresh_settings_cache(self) -> None:
        """Ensure subsequent settings loads reflect the newly written env."""

        self.ctx.settings = None
        try:
            cache_clear = get_settings.cache_clear
        except AttributeError:  # pragma: no cover - defensive
            return
        cache_clear()

    # ------------------------------------------------------------------
    # Audit helpers (shared with report)
    # ------------------------------------------------------------------
    def _build_sections(self) -> list[SectionResult]:
        settings = self.ctx.optional_settings()
        env_snapshot = dict(os.environ)
        return [
            self._secrets_section(settings, env_snapshot),
            self._providers_section(settings, env_snapshot),
            self._tenant_observability_section(env_snapshot),
            self._signup_worker_section(settings, env_snapshot),
        ]

    def _secrets_section(
        self,
        settings: StarterSettingsProtocol | None,
        env_snapshot: dict[str, str],
    ) -> SectionResult:
        section = SectionResult("M1 - Secrets & Key Management", "Rotate and harden keys.")
        password_pepper = env_snapshot.get("AUTH_PASSWORD_PEPPER")
        refresh_pepper = env_snapshot.get("AUTH_REFRESH_TOKEN_PEPPER")

        section.checks.append(
            self._pepper_status("AUTH_PASSWORD_PEPPER", password_pepper)
        )
        section.checks.append(
            self._pepper_status("AUTH_REFRESH_TOKEN_PEPPER", refresh_pepper)
        )

        vault_required = self.profile in {"staging", "production"}
        section.checks.extend(
            [
                self._env_presence("VAULT_ADDR", env_snapshot, required=vault_required),
                self._env_presence("VAULT_TOKEN", env_snapshot, required=vault_required),
                self._env_presence("VAULT_TRANSIT_KEY", env_snapshot, required=vault_required),
            ]
        )

        if settings:
            warnings = settings.secret_warnings()
            if warnings:
                section.checks.append(
                    CheckResult(
                        name="secret_warnings",
                        status="warning",
                        required=True,
                        detail="; ".join(warnings),
                    )
                )
            else:
                section.checks.append(
                    CheckResult(
                        name="secret_warnings",
                        status="ok",
                        required=False,
                        detail="All managed secrets overridden.",
                    )
                )
        else:
            section.checks.append(
                CheckResult(
                    name="secret_warnings",
                    status="pending",
                    required=True,
                    detail="Unable to load settings; verify .env completeness.",
                )
            )

        return section

    def _providers_section(
        self,
        settings: StarterSettingsProtocol | None,
        env_snapshot: dict[str, str],
    ) -> SectionResult:
        section = SectionResult(
            "M2 - Provider & Infra Provisioning",
            "Validate third-party credentials & database.",
        )
        section.checks.extend(
            [
                self._env_presence("OPENAI_API_KEY", env_snapshot),
                self._env_presence("STRIPE_SECRET_KEY", env_snapshot),
                self._env_presence("STRIPE_WEBHOOK_SECRET", env_snapshot),
                self._env_presence("STRIPE_PRODUCT_PRICE_MAP", env_snapshot),
                self._env_presence("REDIS_URL", env_snapshot),
                self._env_presence("RESEND_BASE_URL", env_snapshot, required=False),
            ]
        )
        section.checks.append(
            self._env_presence(
                "BILLING_EVENTS_REDIS_URL",
                env_snapshot,
                required=self.profile != "local",
            )
        )

        if settings and settings.enable_billing:
            missing = settings.required_stripe_envs_missing()
            if missing:
                section.checks.append(
                    CheckResult(
                        name="stripe_validation",
                        status="missing",
                        detail=f"Missing when ENABLE_BILLING=true: {', '.join(missing)}",
                    )
                )
            else:
                section.checks.append(
                    CheckResult(
                        name="stripe_validation",
                        status="ok",
                        required=False,
                        detail="Stripe config satisfied for billing.",
                    )
                )
        else:
            section.checks.append(
                CheckResult(
                    name="stripe_validation",
                    status="pending",
                    required=False,
                    detail="Billing disabled; run `stripe setup` before enabling.",
                )
            )

        section.checks.append(
            self._env_presence("DATABASE_URL", env_snapshot, required=self.profile != "local")
        )
        return section

    def _tenant_observability_section(self, env_snapshot: dict[str, str]) -> SectionResult:
        section = SectionResult(
            "M3 - Tenant & Observability Guardrails",
            "Ensure tenant defaults, log forwarding, and GeoIP wiring.",
        )
        section.checks.append(
            self._env_presence("TENANT_DEFAULT_SLUG", env_snapshot, required=True)
        )
        section.checks.append(
            self._env_presence("LOGGING_SINK", env_snapshot, required=True)
        )
        section.checks.append(
            self._env_presence("GEOIP_PROVIDER", env_snapshot, required=False)
        )
        return section

    def _signup_worker_section(
        self,
        settings: StarterSettingsProtocol | None,
        env_snapshot: dict[str, str],
    ) -> SectionResult:
        section = SectionResult(
            "M4 - Signup & Worker Policy Controls",
            "Document signup exposure and Stripe worker topology.",
        )
        section.checks.append(
            self._env_presence("ALLOW_PUBLIC_SIGNUP", env_snapshot, required=True)
        )
        section.checks.append(
            self._env_presence("SIGNUP_RATE_LIMIT_PER_HOUR", env_snapshot, required=True)
        )
        section.checks.append(
            self._env_presence("BILLING_RETRY_DEPLOYMENT_MODE", env_snapshot, required=False)
        )

        if settings:
            section.checks.append(
                CheckResult(
                    name="signup_policy",
                    status="ok",
                    detail=(
                        f"allow_public_signup={settings.allow_public_signup}, "
                        f"rate_limit={settings.signup_rate_limit_per_hour}/hr"
                    ),
                )
            )
            retry_status = "ok" if settings.enable_billing_retry_worker else "warning"
            detail = (
                "Stripe retry worker enabled in-process."
                if retry_status == "ok"
                else "Retry worker disabled; plan dedicated deployment before launch."
            )
            section.checks.append(
                CheckResult(
                    name="retry_worker",
                    status=retry_status,
                    detail=detail,
                )
            )
        else:
            section.checks.append(
                CheckResult(
                    name="signup_policy",
                    status="pending",
                    detail="Load settings to determine allow_public_signup and quotas.",
                )
            )
            section.checks.append(
                CheckResult(
                    name="retry_worker",
                    status="pending",
                    detail="Need settings to inspect ENABLE_BILLING_RETRY_WORKER.",
                )
            )
        return section

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------
    def _render(self, sections: Sequence[SectionResult]) -> None:
        if self.output_format == "json":
            payload = [
                {
                    "milestone": section.milestone,
                    "focus": section.focus,
                    "status": section.overall_status,
                    "checks": [
                        {
                            "name": check.name,
                            "status": check.status,
                            "required": check.required,
                            "detail": check.detail,
                        }
                        for check in section.checks
                    ],
                }
                for section in sections
            ]

            print(json.dumps(payload, indent=2))
            return

        console.info(f"Profile: {self.profile}")
        if self.ctx.loaded_env_files:
            console.info(
                "Loaded env files: " + ", ".join(str(path) for path in self.ctx.loaded_env_files),
                topic="env",
            )
        else:
            console.warn("No env files loaded. Provide values via --env-file or environment.")

        for section in sections:
            console.newline()
            console.info(f"{section.milestone} — {section.focus}")
            for check in section.checks:
                detail = f" ({check.detail})" if check.detail else ""
                console.info(f"- {check.name}: {check.status}{detail}")

    # ------------------------------------------------------------------
    # Shared utility helpers
    # ------------------------------------------------------------------
    def _current(self, key: str) -> str | None:
        return self.backend_env.get(key) or os.environ.get(key)

    def _current_bool(self, key: str, default: bool = False) -> bool:
        value = self._current(key)
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "y"}

    def _current_frontend_bool(self, key: str, default: bool = False) -> bool:
        if not self.frontend_env:
            return default
        value = self.frontend_env.get(key)
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "y"}

    def _set_backend(self, key: str, value: str, *, mask: bool = False) -> None:
        self.backend_env.set(key, value)
        os.environ[key] = value
        display = "***" if mask else value
        console.info(f"{key} => {display}", topic="env")

    def _set_backend_bool(self, key: str, value: bool) -> None:
        self._set_backend(key, "true" if value else "false")

    def _require_env(self, key: str) -> str:
        value = self._current(key)
        if not value:
            raise CLIError(f"{key} must be set before continuing.")
        return value

    def _set_frontend(self, key: str, value: str) -> None:
        if not self.frontend_env:
            return
        self.frontend_env.set(key, value)
        console.info(f"[frontend] {key} => {value}", topic="env")

    def _set_frontend_bool(self, key: str, value: bool) -> None:
        self._set_frontend(key, "true" if value else "false")

    def _ensure_secret(
        self,
        provider: InputProvider,
        key: str,
        label: str,
        *,
        length: int = 32,
    ) -> None:
        existing = self._current(key)
        placeholders = {
            "",
            "change-me",
            "change-me-too",
            "change-me-again",
            "change-me-email",
            "change-me-reset",
        }
        if existing and existing not in placeholders:
            self._set_backend(key, existing, mask=True)
            return
        console.info(f"{label} is not set; leave blank to autogenerate.", topic="wizard")
        value = provider.prompt_secret(
            key=key,
            prompt=label,
            existing=None,
            required=False,
        )
        if not value:
            value = secrets.token_urlsafe(length)
            console.info(f"Generated random value for {key}", topic="wizard")
        self._set_backend(key, value, mask=True)

    @staticmethod
    def _env_presence(
        key: str,
        env: dict[str, str],
        *,
        required: bool = True,
    ) -> CheckResult:
        status = "ok" if env.get(key) else "missing"
        return CheckResult(name=key, status=status, required=required)

    @staticmethod
    def _pepper_status(key: str, value: str | None) -> CheckResult:
        if not value:
            return CheckResult(name=key, status="missing")
        placeholders = {
            "change-me",
            "change-me-too",
            "change-me-again",
        }
        if value in placeholders:
            return CheckResult(name=key, status="warning", detail="Using starter value")
        return CheckResult(name=key, status="ok")

    def _require_inputs(self) -> InputProvider:
        if self.input_provider is None:
            raise CLIError(
                "This command requires inputs. Provide --answers-file/--var overrides or "
                "run without --non-interactive."
            )
        return self.input_provider


__all__ = ["SetupWizard", "PROFILE_CHOICES", "FRONTEND_ENV_RELATIVE"]
