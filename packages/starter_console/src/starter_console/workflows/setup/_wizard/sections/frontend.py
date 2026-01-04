from __future__ import annotations

from ...inputs import InputProvider
from ..context import WizardContext


def configure(context: WizardContext, provider: InputProvider) -> None:
    console = context.console
    if not context.frontend_env:
        return
    console.section(
        "Frontend",
        "Finalize Next.js environment variables and local testing hooks.",
    )
    context.set_frontend("API_BASE_URL", context.api_base_url)
    public_url = context.current("APP_PUBLIC_URL") or "http://localhost:3000"
    context.set_frontend("APP_PUBLIC_URL", public_url)
    playwright_default = context.frontend_env.get("PLAYWRIGHT_BASE_URL") or "http://localhost:3000"
    playwright = provider.prompt_string(
        key="PLAYWRIGHT_BASE_URL",
        prompt="Playwright base URL",
        default=playwright_default,
        required=True,
    )
    context.set_frontend("PLAYWRIGHT_BASE_URL", playwright)

    use_mock = provider.prompt_bool(
        key="NEXT_PUBLIC_AGENT_API_MOCK",
        prompt="Use mock API responses in Next.js?",
        default=context.current_frontend_bool("NEXT_PUBLIC_AGENT_API_MOCK", False),
    )
    context.set_frontend_bool("NEXT_PUBLIC_AGENT_API_MOCK", use_mock)

    force_secure = provider.prompt_bool(
        key="AGENT_FORCE_SECURE_COOKIES",
        prompt="Force secure cookies on the frontend?",
        default=context.current_frontend_bool(
            "AGENT_FORCE_SECURE_COOKIES",
            context.profile != "demo",
        ),
    )
    context.set_frontend_bool("AGENT_FORCE_SECURE_COOKIES", force_secure)

    allow_insecure = provider.prompt_bool(
        key="AGENT_ALLOW_INSECURE_COOKIES",
        prompt="Allow insecure cookies (helps demo/dev without HTTPS)?",
        default=context.current_frontend_bool(
            "AGENT_ALLOW_INSECURE_COOKIES",
            context.profile == "demo",
        ),
    )
    context.set_frontend_bool("AGENT_ALLOW_INSECURE_COOKIES", allow_insecure)

    log_level = provider.prompt_string(
        key="NEXT_PUBLIC_LOG_LEVEL",
        prompt="Frontend log level (debug/info/warn/error)",
        default=context.frontend_env.get("NEXT_PUBLIC_LOG_LEVEL") or "info",
        required=True,
    ).lower()
    context.set_frontend("NEXT_PUBLIC_LOG_LEVEL", log_level)

    ingest_enabled = context.current_bool(
        "ENABLE_FRONTEND_LOG_INGEST",
        default=context.profile in {"demo", "staging"},
    )
    sink_default = context.frontend_env.get("NEXT_PUBLIC_LOG_SINK") or (
        "beacon" if ingest_enabled else "console"
    )
    raw_sink = provider.prompt_string(
        key="NEXT_PUBLIC_LOG_SINK",
        prompt="Frontend log sink (console/beacon/none)",
        default=sink_default,
        required=True,
    ).strip().lower()
    sink = raw_sink if raw_sink in {"console", "beacon", "none"} else "console"
    if sink == "beacon" and not context.current_bool("ENABLE_FRONTEND_LOG_INGEST", False):
        console.warn(
            "Frontend beacon sink selected, but ENABLE_FRONTEND_LOG_INGEST is false; "
            "enable ingest to receive browser logs.",
            topic="frontend-logging",
        )
    context.set_frontend("NEXT_PUBLIC_LOG_SINK", sink)
