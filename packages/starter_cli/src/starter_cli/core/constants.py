"""Shared constants for Starter CLI."""

from __future__ import annotations

from pathlib import Path

# File location: packages/starter_cli/src/starter_cli/core/constants.py
# Repo root is five levels up from this file.
REPO_ROOT = Path(__file__).resolve().parents[5]
PROJECT_ROOT = REPO_ROOT  # backward-compat alias for existing imports
PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_FILES: tuple[Path, ...] = (
    REPO_ROOT / ".env.compose",
    REPO_ROOT / "apps" / "api-service" / ".env",
    REPO_ROOT / "apps" / "api-service" / ".env.local",
)
DEFAULT_COMPOSE_FILE = REPO_ROOT / "ops" / "compose" / "docker-compose.yml"
TELEMETRY_ENV_FLAG = "STARTER_CLI_TELEMETRY_OPT_IN"
SKIP_ENV_FLAG = "STARTER_CLI_SKIP_ENV"
TRUE_LITERALS = {"1", "true", "yes"}
SAFE_ENVIRONMENTS = {"development", "dev", "local", "test"}
