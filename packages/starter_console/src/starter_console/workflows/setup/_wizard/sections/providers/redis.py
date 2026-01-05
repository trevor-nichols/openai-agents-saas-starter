from __future__ import annotations

from ....inputs import InputProvider
from ....validators import validate_redis_url
from ...context import WizardContext


def collect_redis(context: WizardContext, provider: InputProvider) -> None:
    require_tls = context.policy_rule_bool("redis_tls_required", fallback=True)
    warn_on_shared = require_tls
    primary = provider.prompt_string(
        key="REDIS_URL",
        prompt="Primary Redis URL",
        default=context.policy_env_default("REDIS_URL", fallback="redis://localhost:6379/0"),
        required=True,
    )
    validate_redis_url(primary, require_tls=require_tls, role="Primary")
    context.set_backend("REDIS_URL", primary)
    redis_targets: dict[str, str] = {"Primary": primary}

    def _configure_optional(key: str, label: str) -> None:
        value = provider.prompt_string(
            key=key,
            prompt=f"{label} Redis URL (blank = reuse primary)",
            default=context.current(key) or "",
            required=False,
        )
        if value:
            validate_redis_url(value, require_tls=require_tls, role=label)
            context.set_backend(key, value)
            redis_targets[label] = value
        else:
            context.set_backend(key, "")
            if warn_on_shared:
                context.console.warn(
                    f"{label} Redis workloads will reuse the primary Redis instance. "
                    "Provision a dedicated pool in production.",
                    topic="redis",
                )

    _configure_optional("RATE_LIMIT_REDIS_URL", "Rate limiting")
    _configure_optional("AUTH_CACHE_REDIS_URL", "Auth/session cache")
    _configure_optional("SECURITY_TOKEN_REDIS_URL", "Security token")

    billing = provider.prompt_string(
        key="BILLING_EVENTS_REDIS_URL",
        prompt="Billing events Redis URL (blank = reuse primary)",
        default=context.current("BILLING_EVENTS_REDIS_URL") or "",
        required=False,
    )
    if billing:
        validate_redis_url(billing, require_tls=require_tls, role="Billing events")
        context.set_backend("BILLING_EVENTS_REDIS_URL", billing)
        redis_targets["Billing events"] = billing
    else:
        context.set_backend("BILLING_EVENTS_REDIS_URL", "")
        if warn_on_shared:
            context.console.warn(
                "Using the primary Redis instance for billing streams. Provision a dedicated "
                "instance for production.",
                topic="redis",
            )

    context.provider_automation_plan.redis_targets = redis_targets


__all__ = ["collect_redis"]
