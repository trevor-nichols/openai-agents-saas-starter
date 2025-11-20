#!/usr/bin/env python
"""Ensure the local dev user exists and print fresh credentials.

Runs independently of the setup wizard so that reruns always surface login details.
Safe to run repeatedly: it rotates the password if the user already exists.
"""

from __future__ import annotations

import secrets
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import logging
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine.Engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").disabled = True
logging.getLogger("sqlalchemy.engine.Engine").disabled = True

from starter_cli.container import build_container
from starter_cli.workflows.setup.dev_user import (
    DEFAULT_EMAIL,
    DEFAULT_NAME,
    DEFAULT_ROLE,
    DEFAULT_TENANT,
    DEFAULT_TENANT_NAME,
    DevUserConfig,
    _persist_and_announce,
    seed_dev_user,
)


def main() -> None:
    container = build_container()
    ctx = container.create_context()
    container.load_environment(ctx, verbose=False)

    config = DevUserConfig(
        email=DEFAULT_EMAIL,
        display_name=DEFAULT_NAME,
        tenant_slug=DEFAULT_TENANT,
        tenant_name=DEFAULT_TENANT_NAME,
        role=DEFAULT_ROLE,
        password=secrets.token_urlsafe(20),
        generated_password=True,
        rotate_existing=True,
    )

    # seed_dev_user expects a WizardContext-like object with cli_ctx.project_root
    context = SimpleNamespace(cli_ctx=ctx)
    status = seed_dev_user(context, config)
    _persist_and_announce(context, config, status)


if __name__ == "__main__":
    main()
