"""Global pytest bootstrap to keep tests hermetic regardless of import order."""

from __future__ import annotations

import os

from app.core import config as config_module

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["AUTO_RUN_MIGRATIONS"] = "false"
os.environ["ENABLE_BILLING"] = "false"
os.environ["ALLOW_PUBLIC_SIGNUP"] = "true"
os.environ["ALLOW_SIGNUP_TRIAL_OVERRIDE"] = "false"
os.environ["STARTER_CLI_SKIP_ENV"] = "true"

config_module.get_settings.cache_clear()
