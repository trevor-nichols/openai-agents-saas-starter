from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol

from starter_shared.secrets.models import SecretsProviderLiteral

from ..common import TELEMETRY_ENV, CLIContext
from ..console import console
from ..setup.inputs import InputProvider
from ..verification import VerificationArtifact


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
    """Optional knobs that workflows may consult (e.g., skip Make targets)."""

    skip_make: bool = False


class SecretsWorkflow(Protocol):
    def __call__(
        self,
        ctx: CLIContext,
        provider: InputProvider,
        *,
        options: SecretsWorkflowOptions,
    ) -> OnboardResult:  # pragma: no cover - protocol definition
        ...


def render_onboard_result(result: OnboardResult) -> None:
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


def emit_cli_telemetry(provider: str, *, success: bool) -> None:
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
