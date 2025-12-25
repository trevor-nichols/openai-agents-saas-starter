from __future__ import annotations

import json
from pathlib import Path

from starter_console.adapters.env import EnvFile


def load_backend_env_files(project_root: Path) -> tuple[EnvFile, EnvFile, EnvFile]:
    env_local = EnvFile(project_root / "apps" / "api-service" / ".env.local")
    env_fallback = EnvFile(project_root / "apps" / "api-service" / ".env")
    env_compose = EnvFile(project_root / ".env.compose")
    return (env_local, env_fallback, env_compose)


def update_backend_env(
    env_local: EnvFile,
    *,
    secret_key: str,
    webhook_secret: str,
    price_map: dict[str, str],
) -> None:
    env_local.set("STRIPE_SECRET_KEY", secret_key)
    env_local.set("STRIPE_WEBHOOK_SECRET", webhook_secret)
    env_local.set("STRIPE_PRODUCT_PRICE_MAP", json.dumps(price_map, separators=(",", ":")))
    env_local.set("ENABLE_BILLING", "true")
    env_local.save()


def update_frontend_env(project_root: Path) -> bool:
    frontend_path = project_root / "apps" / "web-app" / ".env.local"
    if not frontend_path.parent.exists():
        return False

    env_frontend = EnvFile(frontend_path)
    env_frontend.set("NEXT_PUBLIC_ENABLE_BILLING", "true")
    env_frontend.save()
    return True


__all__ = ["load_backend_env_files", "update_backend_env", "update_frontend_env"]
