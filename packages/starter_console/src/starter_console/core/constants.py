"""Shared constants for Starter Console."""

from __future__ import annotations

from pathlib import Path

# File location: packages/starter_console/src/starter_console/core/constants.py
# Repo root is five levels up from this file.
PROJECT_ROOT = Path(__file__).resolve().parents[5]
PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_FILES: tuple[Path, ...] = (
    PROJECT_ROOT / ".env.compose",
    PROJECT_ROOT / "apps" / "api-service" / ".env",
    PROJECT_ROOT / "apps" / "api-service" / ".env.local",
)
DEFAULT_COMPOSE_FILE = PROJECT_ROOT / "ops" / "compose" / "docker-compose.yml"
TELEMETRY_ENV_FLAG = "STARTER_CONSOLE_TELEMETRY_OPT_IN"
SKIP_ENV_FLAG = "STARTER_CONSOLE_SKIP_ENV"
TRUE_LITERALS = {"1", "true", "yes"}
SAFE_ENVIRONMENTS = {"development", "dev", "demo", "test"}
