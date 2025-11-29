from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from starter_contracts.config import StarterSettingsProtocol

from starter_cli.core.constants import TRUE_LITERALS
from starter_cli.core.status_models import ProbeResult


@dataclass(frozen=True, slots=True)
class ProbeContext:
    """Shared context available to all probe factories."""

    env: Mapping[str, str]
    settings: StarterSettingsProtocol | None
    profile: str
    strict: bool
    warn_only: bool

    def is_truthy(self, key: str, *, default: bool = False) -> bool:
        raw = self.env.get(key)
        if raw is None:
            return default
        return raw.lower() in TRUE_LITERALS


@dataclass(frozen=True, slots=True)
class ProbeSpec:
    name: str
    factory: Callable[[ProbeContext], ProbeResult]
    category: str = "core"
    optional: bool = False


PROBE_SPECS: tuple[ProbeSpec, ...] = (
    ProbeSpec("environment", lambda ctx: _env_probe(), category="core"),
    ProbeSpec("ports", lambda ctx: _ports_probe(), category="core"),
    ProbeSpec("stack", lambda ctx: _stack_probe(), category="core", optional=True),
    ProbeSpec("database", lambda ctx: _db_probe(ctx.warn_only), category="core"),
    ProbeSpec("redis", lambda ctx: _redis_probe(ctx.warn_only), category="core"),
    ProbeSpec("api", lambda ctx: _api_probe(ctx.warn_only), category="core"),
    ProbeSpec("frontend", lambda ctx: _frontend_probe(ctx.warn_only), category="core"),
    ProbeSpec("migrations", lambda ctx: _migrations_probe(), category="core"),
    ProbeSpec("secrets", lambda ctx: _secrets_probe(ctx), category="secrets", optional=True),
    ProbeSpec("billing", lambda ctx: _billing_probe(ctx), category="billing", optional=True),
    ProbeSpec("storage", lambda ctx: _storage_probe(ctx), category="storage", optional=True),
)


def _env_probe() -> ProbeResult:
    from starter_cli.workflows.home.probes.env import env_coverage_probe

    return env_coverage_probe()


def _ports_probe() -> ProbeResult:
    from starter_cli.workflows.home.probes.ports import ports_probe

    return ports_probe()


def _stack_probe() -> ProbeResult:
    from starter_cli.workflows.home.probes.stack import stack_probe

    return stack_probe()


def _db_probe(warn_only: bool) -> ProbeResult:
    from starter_cli.workflows.home.probes.db import db_probe

    return db_probe(warn_only=warn_only)


def _redis_probe(warn_only: bool) -> ProbeResult:
    from starter_cli.workflows.home.probes.redis import redis_probe

    return redis_probe(warn_only=warn_only)


def _api_probe(warn_only: bool) -> ProbeResult:
    from starter_cli.workflows.home.probes.api import api_probe

    return api_probe(warn_only=warn_only)


def _frontend_probe(warn_only: bool) -> ProbeResult:
    from starter_cli.workflows.home.probes.frontend import frontend_probe

    return frontend_probe(warn_only=warn_only)


def _migrations_probe() -> ProbeResult:
    from starter_cli.workflows.home.probes.migrations import migrations_probe

    return migrations_probe()


def _secrets_probe(ctx: ProbeContext) -> ProbeResult:
    from starter_cli.workflows.home.probes.secrets import secrets_probe

    return secrets_probe(ctx)


def _billing_probe(ctx: ProbeContext) -> ProbeResult:
    from starter_cli.workflows.home.probes.billing import billing_probe

    return billing_probe(ctx)


def _storage_probe(ctx: ProbeContext) -> ProbeResult:
    from starter_cli.workflows.home.probes.storage import storage_probe

    return storage_probe(ctx)


__all__ = ["ProbeContext", "ProbeSpec", "PROBE_SPECS"]
