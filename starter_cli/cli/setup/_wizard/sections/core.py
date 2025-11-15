from __future__ import annotations

from starter_cli.cli.console import console
from starter_cli.cli.setup._wizard.context import WizardContext
from starter_cli.cli.setup.inputs import InputProvider


def run(context: WizardContext, provider: InputProvider) -> None:
    """Collect deployment metadata shared across all milestones."""

    console.info("[Core] Deployment metadata", topic="wizard")

    env_default = {
        "local": "development",
        "staging": "staging",
        "production": "production",
    }[context.profile]
    environment = provider.prompt_string(
        key="ENVIRONMENT",
        prompt="Environment label (ENVIRONMENT)",
        default=context.current("ENVIRONMENT") or env_default,
        required=True,
    )
    context.set_backend("ENVIRONMENT", environment)

    debug_default = context.current_bool("DEBUG", default=context.profile == "local")
    debug = provider.prompt_bool(
        key="DEBUG",
        prompt="Enable FastAPI debug mode?",
        default=debug_default,
    )
    context.set_backend_bool("DEBUG", debug)

    port = provider.prompt_string(
        key="PORT",
        prompt="FastAPI port (PORT)",
        default=context.current("PORT") or "8000",
        required=True,
    )
    context.set_backend("PORT", port)

    app_public_url = provider.prompt_string(
        key="APP_PUBLIC_URL",
        prompt="Public site base URL (APP_PUBLIC_URL)",
        default=context.current("APP_PUBLIC_URL") or "http://localhost:3000",
        required=True,
    )
    context.set_backend("APP_PUBLIC_URL", app_public_url)

    allowed_hosts = provider.prompt_string(
        key="ALLOWED_HOSTS",
        prompt="Allowed hosts (comma-separated)",
        default=context.current("ALLOWED_HOSTS")
        or "localhost,localhost:8000,127.0.0.1,testserver,testclient",
        required=True,
    )
    context.set_backend("ALLOWED_HOSTS", allowed_hosts)

    allowed_origins = provider.prompt_string(
        key="ALLOWED_ORIGINS",
        prompt="Allowed origins (comma-separated)",
        default=context.current("ALLOWED_ORIGINS")
        or "http://localhost:3000,http://localhost:8000",
        required=True,
    )
    context.set_backend("ALLOWED_ORIGINS", allowed_origins)

    auto_run = provider.prompt_bool(
        key="AUTO_RUN_MIGRATIONS",
        prompt="Automatically run migrations on startup?",
        default=context.current_bool("AUTO_RUN_MIGRATIONS", default=context.profile == "local"),
    )
    context.set_backend_bool("AUTO_RUN_MIGRATIONS", auto_run)

    port_int = int(port) if port.isdigit() else 8000
    api_base_url = provider.prompt_string(
        key="API_BASE_URL",
        prompt="API base URL for frontend + tooling",
        default=context.current("API_BASE_URL") or f"http://127.0.0.1:{port_int}",
        required=True,
    )
    context.api_base_url = api_base_url
    context.set_backend("API_BASE_URL", api_base_url)
