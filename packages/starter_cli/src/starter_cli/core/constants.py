"""Shared constants for Starter CLI."""

from __future__ import annotations

from pathlib import Path

# File location: packages/starter_cli/src/starter_cli/core/constants.py
# Repo root is five levels up from this file.
PROJECT_ROOT = Path(__file__).resolve().parents[5]
PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_FILES: tuple[Path, ...] = (
    PROJECT_ROOT / ".env.compose",
    PROJECT_ROOT / "apps" / "api-service" / ".env",
    PROJECT_ROOT / "apps" / "api-service" / ".env.local",
)
DEFAULT_COMPOSE_FILE = PROJECT_ROOT / "ops" / "compose" / "docker-compose.yml"
TELEMETRY_ENV_FLAG = "STARTER_CLI_TELEMETRY_OPT_IN"
SKIP_ENV_FLAG = "STARTER_CLI_SKIP_ENV"
TRUE_LITERALS = {"1", "true", "yes"}
SAFE_ENVIRONMENTS = {"development", "dev", "demo", "test"}
