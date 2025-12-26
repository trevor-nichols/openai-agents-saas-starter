from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from starter_console.core import CLIError


@dataclass(frozen=True, slots=True)
class PlanConfig:
    code: str
    name: str
    default_cents: int


PLAN_CATALOG: tuple[PlanConfig, ...] = (
    PlanConfig(code="starter", name="Starter", default_cents=2000),
    PlanConfig(code="pro", name="Pro", default_cents=9900),
)

PLAN_METADATA_KEY = "starter_console_plan_code"


def parse_amount_cents(raw: str) -> int:
    try:
        amount = Decimal(raw)
    except InvalidOperation as exc:
        raise CLIError("Enter a numeric amount (e.g., 29 or 29.99).") from exc
    if amount <= 0:
        raise CLIError("Amount must be greater than zero.")
    return int((amount * 100).to_integral_value())


def parse_plan_overrides(
    items: Iterable[str],
    *,
    require_all: bool,
    catalog: Iterable[PlanConfig] = PLAN_CATALOG,
) -> dict[str, int]:
    overrides: dict[str, int] = {}
    for item in items:
        if "=" not in item:
            raise CLIError(f"Invalid plan override '{item}'. Expected format code=amount.")
        code, raw = item.split("=", 1)
        overrides[code.strip()] = parse_amount_cents(raw.strip())
    if require_all:
        missing = [plan.code for plan in catalog if plan.code not in overrides]
        if missing:
            raise CLIError(
                f"--non-interactive requires plan overrides (missing: {', '.join(missing)})."
            )
    return overrides


__all__ = [
    "PLAN_CATALOG",
    "PLAN_METADATA_KEY",
    "PlanConfig",
    "parse_amount_cents",
    "parse_plan_overrides",
]
