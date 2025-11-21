"""Shared status and action models for the CLI home hub/doctor flows.

Contract note: doctor JSON/Markdown output is versioned via
`starter_contracts/doctor_v1.json`. If you add/rename fields here, update the
schema and keep compatibility in `DoctorRunner._serialize_*` (created_at is
intentionally omitted from the contract).

These dataclasses intentionally avoid runtime dependencies so they remain safe to
import from both interactive TUIs and headless/reporting code paths.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from time import time
from typing import Callable, Iterable, Mapping, Sequence


class ProbeState(str, Enum):
    OK = "ok"
    WARN = "warn"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass(frozen=True, slots=True)
class ProbeResult:
    name: str
    state: ProbeState
    detail: str | None = None
    remediation: str | None = None
    duration_ms: float | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)
    created_at: float = field(default_factory=time)

    @property
    def severity_rank(self) -> int:
        return {ProbeState.ERROR: 3, ProbeState.WARN: 2, ProbeState.OK: 1, ProbeState.SKIPPED: 0}[
            self.state
        ]


@dataclass(frozen=True, slots=True)
class ServiceStatus:
    """Aggregated status for a service/process surfaced in the hub."""

    label: str
    state: ProbeState
    endpoints: Sequence[str] = field(default_factory=tuple)
    pid: int | None = None
    detail: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)
    created_at: float = field(default_factory=time)

    @property
    def severity_rank(self) -> int:
        return {ProbeState.ERROR: 3, ProbeState.WARN: 2, ProbeState.OK: 1, ProbeState.SKIPPED: 0}[
            self.state
        ]


@dataclass(frozen=True, slots=True)
class ActionShortcut:
    key: str
    label: str
    description: str | None = None
    callback: Callable[[], None] | None = None


@dataclass(frozen=True, slots=True)
class LaunchStep:
    label: str
    command: Sequence[str]
    env: Mapping[str, str] = field(default_factory=dict)
    timeout_seconds: float | None = None


@dataclass(frozen=True, slots=True)
class LaunchPlan:
    name: str
    steps: Sequence[LaunchStep]
    post_checks: Iterable[Callable[[], ProbeResult]] = field(default_factory=tuple)


__all__ = [
    "ActionShortcut",
    "LaunchPlan",
    "LaunchStep",
    "ProbeResult",
    "ProbeState",
    "ServiceStatus",
]
