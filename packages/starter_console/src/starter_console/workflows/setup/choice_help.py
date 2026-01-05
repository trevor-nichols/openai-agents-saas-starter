"""Shared choice help text for wizard prompts."""

from __future__ import annotations

CHOICE_HELP: dict[str, dict[str, str]] = {
    "SETUP_HOSTING_PRESET": {
        "local_docker": "Local dev with Docker Compose defaults (Postgres/Redis/Vault dev/MinIO).",
        "cloud_managed": "Hosted infra defaults (external DB/Redis, cloud secrets + storage).",
        "enterprise_custom": "No strong defaults; prompts stay explicit for custom setups.",
    },
}

__all__ = ["CHOICE_HELP"]
