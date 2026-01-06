from __future__ import annotations

from ....automation import AutomationPhase
from ....inputs import InputProvider
from ...context import WizardContext


def request_migrations(context: WizardContext, provider: InputProvider) -> None:
    record = context.automation.get(AutomationPhase.MIGRATIONS)
    if record.enabled:
        return

    run_now = provider.prompt_bool(
        key="RUN_MIGRATIONS_NOW",
        prompt="Run `just migrate` now?",
        default=context.policy_rule_bool("migrations_prompt_default", fallback=False),
    )
    if run_now:
        context.provider_automation_plan.run_migrations = True


__all__ = ["request_migrations"]
