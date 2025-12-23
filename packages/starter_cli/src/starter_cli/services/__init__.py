"""Service layer entrypoint with lazy imports to avoid circular dependencies."""

from __future__ import annotations

import importlib
from typing import Any

_LAZY_ATTRS: dict[str, str] = {
    "ops_models": "starter_cli.services.ops_models",
    "hub": "starter_cli.services.hub",
    "infra": "starter_cli.services.infra",
    "stripe_status": "starter_cli.services.stripe_status",
    "HubService": "starter_cli.services.hub",
    "DependencyStatus": "starter_cli.services.infra",
    "collect_dependency_statuses": "starter_cli.services.infra",
    "StripeStatus": "starter_cli.services.stripe_status",
    "REQUIRED_ENV_KEYS": "starter_cli.services.stripe_status",
    "load_stripe_status": "starter_cli.services.stripe_status",
}


def __getattr__(name: str) -> Any:
    target = _LAZY_ATTRS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = importlib.import_module(target)
    return getattr(module, name, module)


__all__ = sorted(_LAZY_ATTRS.keys())
