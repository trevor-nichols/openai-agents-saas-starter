"""Central registry for ORM model imports."""

from __future__ import annotations

import importlib

MODEL_MODULES = (
    "app.infrastructure.persistence.activity.models",
    "app.infrastructure.persistence.auth.models.consent",
    "app.infrastructure.persistence.auth.models.membership",
    "app.infrastructure.persistence.auth.models.mfa",
    "app.infrastructure.persistence.auth.models.security",
    "app.infrastructure.persistence.auth.models.sessions",
    "app.infrastructure.persistence.auth.models.signup",
    "app.infrastructure.persistence.auth.models.sso",
    "app.infrastructure.persistence.auth.models.team_invites",
    "app.infrastructure.persistence.auth.models.user",
    "app.infrastructure.persistence.billing.models",
    "app.infrastructure.persistence.containers.models",
    "app.infrastructure.persistence.conversations.ledger_models",
    "app.infrastructure.persistence.conversations.models",
    "app.infrastructure.persistence.status.models",
    "app.infrastructure.persistence.storage.models",
    "app.infrastructure.persistence.stripe.models",
    "app.infrastructure.persistence.tenants.models",
    "app.infrastructure.persistence.usage.models",
    "app.infrastructure.persistence.vector_stores.models",
    "app.infrastructure.persistence.workflows.models",
)


def import_all_models() -> None:
    """Import all ORM model modules so SQLAlchemy metadata is populated."""

    for module_path in MODEL_MODULES:
        importlib.import_module(module_path)
