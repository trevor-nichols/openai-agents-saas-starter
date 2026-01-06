from __future__ import annotations

from ....inputs import InputProvider
from ...context import WizardContext


def collect_ai_providers(context: WizardContext, provider: InputProvider) -> None:
    openai_key = provider.prompt_secret(
        key="OPENAI_API_KEY",
        prompt="OpenAI API key (required)",
        existing=context.current("OPENAI_API_KEY"),
        required=True,
    )
    context.set_backend("OPENAI_API_KEY", openai_key, mask=True)

__all__ = ["collect_ai_providers"]
