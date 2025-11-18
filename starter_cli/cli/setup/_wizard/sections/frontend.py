from __future__ import annotations

from starter_cli.cli.console import console
from starter_cli.cli.setup._wizard.context import WizardContext
from starter_cli.cli.setup.inputs import InputProvider


def configure(context: WizardContext, provider: InputProvider) -> None:
    if not context.frontend_env:
        return
    console.section(
        "Frontend",
        "Finalize Next.js environment variables and local testing hooks.",
    )
    context.set_frontend("NEXT_PUBLIC_API_URL", context.api_base_url)
    playwright_default = context.frontend_env.get("PLAYWRIGHT_BASE_URL") or "http://localhost:3000"
    playwright = provider.prompt_string(
        key="PLAYWRIGHT_BASE_URL",
        prompt="Playwright base URL",
        default=playwright_default,
        required=True,
    )
    context.set_frontend("PLAYWRIGHT_BASE_URL", playwright)

    use_mock = provider.prompt_bool(
        key="AGENT_API_MOCK",
        prompt="Use mock API responses in Next.js?",
        default=context.current_frontend_bool("AGENT_API_MOCK", False),
    )
    context.set_frontend_bool("AGENT_API_MOCK", use_mock)

    force_secure = provider.prompt_bool(
        key="AGENT_FORCE_SECURE_COOKIES",
        prompt="Force secure cookies on the frontend?",
        default=context.current_frontend_bool(
            "AGENT_FORCE_SECURE_COOKIES",
            context.profile != "local",
        ),
    )
    context.set_frontend_bool("AGENT_FORCE_SECURE_COOKIES", force_secure)

    allow_insecure = provider.prompt_bool(
        key="AGENT_ALLOW_INSECURE_COOKIES",
        prompt="Allow insecure cookies (helps local dev without HTTPS)?",
        default=context.current_frontend_bool(
            "AGENT_ALLOW_INSECURE_COOKIES",
            context.profile == "local",
        ),
    )
    context.set_frontend_bool("AGENT_ALLOW_INSECURE_COOKIES", allow_insecure)
