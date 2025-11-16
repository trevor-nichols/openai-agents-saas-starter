from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum


class AutomationPhase(str, Enum):
    INFRA = "infra"
    SECRETS = "secrets"
    STRIPE = "stripe"


class AutomationStatus(str, Enum):
    DISABLED = "disabled"
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


@dataclass(slots=True)
class AutomationRecord:
    enabled: bool = False
    status: AutomationStatus = AutomationStatus.DISABLED
    note: str | None = None


@dataclass(slots=True)
class AutomationState:
    records: dict[AutomationPhase, AutomationRecord] = field(default_factory=dict)

    def request(
        self,
        phase: AutomationPhase,
        *,
        enabled: bool,
        blocked_reasons: Iterable[str] | None = None,
        note: str | None = None,
    ) -> AutomationRecord:
        if not enabled:
            record = AutomationRecord(enabled=False, status=AutomationStatus.DISABLED, note=note)
        else:
            reasons = list(blocked_reasons or ())
            if reasons:
                reason_text = ", ".join(reasons)
                message = f"Blocked: {reason_text}"
                if note:
                    message = f"{note} — {message}"
                record = AutomationRecord(
                    enabled=True,
                    status=AutomationStatus.BLOCKED,
                    note=message,
                )
            else:
                record = AutomationRecord(
                    enabled=True,
                    status=AutomationStatus.PENDING,
                    note=note,
                )
        self.records[phase] = record
        return record

    def update(
        self,
        phase: AutomationPhase,
        status: AutomationStatus,
        note: str | None = None,
    ) -> AutomationRecord:
        record = self.records.setdefault(phase, AutomationRecord())
        record.status = status
        if note is not None:
            record.note = note
        return record

    def get(self, phase: AutomationPhase) -> AutomationRecord:
        return self.records.setdefault(phase, AutomationRecord())


ALL_AUTOMATION_PHASES: tuple[AutomationPhase, ...] = (
    AutomationPhase.INFRA,
    AutomationPhase.SECRETS,
    AutomationPhase.STRIPE,
)


__all__ = [
    "AutomationPhase",
    "AutomationRecord",
    "AutomationState",
    "AutomationStatus",
    "ALL_AUTOMATION_PHASES",
]
