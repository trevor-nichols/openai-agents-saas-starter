from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from starter_contracts.secrets.models import SecretsProviderLiteral

from starter_cli.core import CLIContext
from starter_cli.core.constants import TELEMETRY_ENV_FLAG as TELEMETRY_ENV
from starter_cli.ports.console import ConsolePort
from starter_cli.telemetry import VerificationArtifact

if TYPE_CHECKING:
    from starter_cli.workflows.setup.inputs import InputProvider


@dataclass(slots=True)
class ProviderOption:
    literal: SecretsProviderLiteral
    label: str
    description: str
    available: bool


@dataclass(slots=True)
class OnboardResult:
    provider: SecretsProviderLiteral
    env_updates: dict[str, str]
    steps: list[str]
    warnings: list[str]
    artifacts: list[VerificationArtifact] | None = None


@dataclass(slots=True)
class SecretsWorkflowOptions:
    """Optional knobs that workflows may consult (e.g., skip local automation)."""

    skip_automation: bool = False


class SecretsWorkflow(Protocol):
    def __call__(
        self,
        ctx: CLIContext,
        provider: InputProvider,
        *,
        options: SecretsWorkflowOptions,
    ) -> OnboardResult:  # pragma: no cover - protocol definition
        ...


def render_onboard_result(console: ConsolePort, result: OnboardResult) -> None:
    console.success(
        f"Secrets provider configured: {result.provider.value}",
        topic="secrets",
    )
    console.info("Add or update the following environment variables:", topic="secrets")
    for key, value in result.env_updates.items():
        console.info(f"{key}={value}", topic="secrets")

    if result.steps:
        console.newline()
        console.info("Next steps:", topic="secrets")
        for step in result.steps:
            console.info(f"- {step}", topic="secrets")

    if result.warnings:
        console.newline()
        for warning in result.warnings:
            console.warn(warning, topic="secrets")

    if result.artifacts:
        console.newline()
        console.info("Verification artifacts:", topic="secrets")
        for artifact in result.artifacts:
            detail = f" ({artifact.detail})" if artifact.detail else ""
            console.info(
                f"- {artifact.provider}: {artifact.status} — {artifact.identifier}{detail}",
                topic="secrets",
            )


def emit_cli_telemetry(console: ConsolePort, provider: str, *, success: bool) -> None:
    if os.getenv(TELEMETRY_ENV, "false").lower() not in {"1", "true", "yes"}:
        return
    console.info(
        f"[telemetry] secrets_provider={provider} success={success}",
        topic="secrets",
    )


__all__ = [
    "ProviderOption",
    "OnboardResult",
    "SecretsWorkflowOptions",
    "SecretsWorkflow",
    "render_onboard_result",
    "emit_cli_telemetry",
]
