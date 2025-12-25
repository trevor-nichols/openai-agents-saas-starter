from __future__ import annotations

from starter_cli.core import CLIError

COMPOSE_ACTION_TARGETS = {
    "up": "dev-up",
    "down": "dev-down",
    "logs": "dev-logs",
    "ps": "dev-ps",
}

VAULT_ACTION_TARGETS = {
    "up": "vault-up",
    "down": "vault-down",
    "logs": "vault-logs",
    "verify": "verify-vault",
}


def resolve_compose_target(action: str) -> str:
    target = COMPOSE_ACTION_TARGETS.get(action)
    if not target:
        raise CLIError(f"Unknown compose action: {action}")
    return target


def resolve_vault_target(action: str) -> str:
    target = VAULT_ACTION_TARGETS.get(action)
    if not target:
        raise CLIError(f"Unknown vault action: {action}")
    return target


def just_command(target: str) -> list[str]:
    return ["just", target]


__all__ = [
    "COMPOSE_ACTION_TARGETS",
    "VAULT_ACTION_TARGETS",
    "just_command",
    "resolve_compose_target",
    "resolve_vault_target",
]
