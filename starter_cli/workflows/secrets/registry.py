from __future__ import annotations

from dataclasses import dataclass

from starter_contracts.secrets.models import SecretsProviderLiteral

from .models import ProviderOption, SecretsWorkflow
from .providers import aws, azure, infisical, vault


@dataclass(frozen=True, slots=True)
class ProviderWorkflow:
    option: ProviderOption
    runner: SecretsWorkflow


PROVIDER_WORKFLOWS: tuple[ProviderWorkflow, ...] = (
    ProviderWorkflow(
        ProviderOption(
            literal=SecretsProviderLiteral.VAULT_DEV,
            label="Vault Dev (Docker)",
            description=(
                "Single-command dev signer via just vault-up on http://127.0.0.1:18200."
            ),
            available=True,
        ),
        vault.run_vault_dev,
    ),
    ProviderWorkflow(
        ProviderOption(
            literal=SecretsProviderLiteral.VAULT_HCP,
            label="HCP Vault (Dedicated/SaaS)",
            description="Point at an existing HCP Vault cluster with Transit enabled.",
            available=True,
        ),
        vault.run_vault_hcp,
    ),
    ProviderWorkflow(
        ProviderOption(
            literal=SecretsProviderLiteral.INFISICAL_CLOUD,
            label="Infisical Cloud",
            description="Managed Infisical workspace with service tokens.",
            available=True,
        ),
        infisical.run_infisical_cloud,
    ),
    ProviderWorkflow(
        ProviderOption(
            literal=SecretsProviderLiteral.INFISICAL_SELF_HOST,
            label="Infisical Self-Hosted",
            description="Docker/Kubernetes deploy of Infisical in your VPC.",
            available=True,
        ),
        infisical.run_infisical_self_hosted,
    ),
    ProviderWorkflow(
        ProviderOption(
            literal=SecretsProviderLiteral.AWS_SM,
            label="AWS Secrets Manager",
            description="Use Secrets Manager to store the signing secret (HMAC).",
            available=True,
        ),
        aws.run_aws_sm,
    ),
    ProviderWorkflow(
        ProviderOption(
            literal=SecretsProviderLiteral.AZURE_KV,
            label="Azure Key Vault",
            description="Use Azure Key Vault secrets as the signing key store.",
            available=True,
        ),
        azure.run_azure_kv,
    ),
)

_PROVIDER_BY_LITERAL = {workflow.option.literal: workflow for workflow in PROVIDER_WORKFLOWS}


def provider_options() -> tuple[ProviderOption, ...]:
    return tuple(workflow.option for workflow in PROVIDER_WORKFLOWS)


def get_runner(literal: SecretsProviderLiteral) -> SecretsWorkflow:
    workflow = _PROVIDER_BY_LITERAL.get(literal)
    if workflow is None:  # pragma: no cover - defensive guard
        raise KeyError(f"No workflow registered for {literal.value}")
    return workflow.runner


def get_option(literal: SecretsProviderLiteral) -> ProviderOption:
    workflow = _PROVIDER_BY_LITERAL.get(literal)
    if workflow is None:  # pragma: no cover - defensive guard
        raise KeyError(f"No provider option registered for {literal.value}")
    return workflow.option


__all__ = ["provider_options", "get_runner", "get_option", "ProviderWorkflow"]
