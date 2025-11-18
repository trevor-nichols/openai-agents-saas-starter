"""Shared constants for Starter CLI."""

from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = PACKAGE_ROOT.parent
DEFAULT_ENV_FILES: tuple[Path, ...] = (
    PROJECT_ROOT / ".env.compose",
    PROJECT_ROOT / ".env",
    PROJECT_ROOT / ".env.local",
)
TELEMETRY_ENV_FLAG = "STARTER_CLI_TELEMETRY_OPT_IN"
SKIP_ENV_FLAG = "STARTER_CLI_SKIP_ENV"
TRUE_LITERALS = {"1", "true", "yes"}
SAFE_ENVIRONMENTS = {"development", "dev", "local", "test"}
