from ....inputs import InputProvider
from ...context import WizardContext
from .ai import collect_ai_providers
from .billing import collect_billing
from .database import collect_database
from .email import collect_email
from .migrations import request_migrations
from .redis import collect_redis
from .sso import collect_sso


def run(context: WizardContext, provider: InputProvider) -> None:
    context.console.section(
        "Infra & Providers",
        "Wire up databases, AI providers, Redis, billing, and email transports.",
    )
    collect_database(context, provider)
    collect_ai_providers(context, provider)
    collect_redis(context, provider)
    collect_billing(context, provider)
    collect_email(context, provider)
    collect_sso(context, provider)
    request_migrations(context, provider)


__all__ = ["run"]
