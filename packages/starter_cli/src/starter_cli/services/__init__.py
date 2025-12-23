"""Service layer entrypoint with lazy imports to avoid circular dependencies."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from . import infra, ops_models, stripe_status
    from .infra import DependencyStatus, collect_dependency_statuses
    from .stripe_status import REQUIRED_ENV_KEYS, StripeStatus, load_stripe_status

_LAZY_ATTRS: dict[str, str] = {
    "ops_models": "starter_cli.services.ops_models",
    "infra": "starter_cli.services.infra",
    "stripe_status": "starter_cli.services.stripe_status",
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


__all__ = [
    "DependencyStatus",
    "REQUIRED_ENV_KEYS",
    "StripeStatus",
    "collect_dependency_statuses",
    "infra",
    "load_stripe_status",
    "ops_models",
    "stripe_status",
]
