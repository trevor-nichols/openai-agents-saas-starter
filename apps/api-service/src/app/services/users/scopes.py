"""Role-to-scope policy."""

from __future__ import annotations


def scopes_for_role(role: str) -> list[str]:
    normalized = role.lower()
    if normalized in {"admin", "owner"}:
        return [
            "conversations:read",
            "conversations:write",
            "conversations:delete",
            "workflows:delete",
            "tools:read",
            "billing:read",
            "billing:manage",
            "support:read",
            "activity:read",
        ]
    if normalized in {"member", "editor"}:
        return [
            "conversations:read",
            "conversations:write",
            "tools:read",
        ]
    return [
        "conversations:read",
        "tools:read",
    ]


__all__ = ["scopes_for_role"]
