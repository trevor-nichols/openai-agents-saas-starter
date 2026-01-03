from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ProviderAutomationPlan:
    run_migrations: bool = False
    run_stripe_setup: bool = False
    redis_targets: dict[str, str] = field(default_factory=dict)


__all__ = ["ProviderAutomationPlan"]
