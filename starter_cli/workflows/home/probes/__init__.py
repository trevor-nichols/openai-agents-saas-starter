"""Probe registry for the home hub and doctor flows.

Probes will be added incrementally (db, redis, api health, frontend devserver,
ports, env coverage, migrations, Stripe, Vault). The module exports a simple
type alias plus shared utilities used by concrete probes.
"""

from __future__ import annotations

from collections.abc import Callable

from starter_cli.core.status_models import ProbeResult
from starter_cli.workflows.home.probes import util

Probe = Callable[[], ProbeResult]

__all__ = ["Probe", "util"]
