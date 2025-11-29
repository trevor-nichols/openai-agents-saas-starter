from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class CheckResult:
    name: str
    status: str
    required: bool = True
    detail: str | None = None


@dataclass(slots=True)
class SectionResult:
    milestone: str
    focus: str
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def overall_status(self) -> str:
        if any(check.status == "missing" and check.required for check in self.checks):
            return "action_required"
        if any(check.status in {"warning", "pending"} for check in self.checks):
            return "pending"
        return "ok"
