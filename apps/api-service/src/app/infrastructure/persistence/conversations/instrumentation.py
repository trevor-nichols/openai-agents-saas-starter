"""Thin wrappers around metrics to keep stores free of observability coupling."""

from __future__ import annotations

from time import perf_counter

from app.observability.metrics import (
    AGENT_RUN_EVENTS_DRIFT,
    AGENT_RUN_EVENTS_PROJECTION_DURATION_SECONDS,
    AGENT_RUN_EVENTS_PROJECTION_TOTAL,
    AGENT_RUN_EVENTS_READ_DURATION_SECONDS,
    AGENT_RUN_EVENTS_READ_TOTAL,
    _sanitize_agent,
    _sanitize_tenant,
)


class RunEventMetrics:
    """Best-effort metric emitters for run event projections/reads."""

    def __init__(self, tenant_id: str, agent: str | None = None) -> None:
        self.tenant_label = _sanitize_tenant(tenant_id)
        self.agent_label = _sanitize_agent(agent)

    def projection_success(self, start: float) -> None:
        AGENT_RUN_EVENTS_PROJECTION_TOTAL.labels(
            tenant=self.tenant_label,
            agent=self.agent_label,
            result="success",
        ).inc()
        AGENT_RUN_EVENTS_PROJECTION_DURATION_SECONDS.labels(
            tenant=self.tenant_label,
            agent=self.agent_label,
        ).observe(perf_counter() - start)

    def projection_conflict(self) -> None:
        AGENT_RUN_EVENTS_PROJECTION_TOTAL.labels(
            tenant=self.tenant_label,
            agent=self.agent_label,
            result="conflict",
        ).inc()

    def projection_error(self) -> None:
        AGENT_RUN_EVENTS_PROJECTION_TOTAL.labels(
            tenant=self.tenant_label,
            agent=self.agent_label,
            result="error",
        ).inc()

    def read_success(self, start: float) -> None:
        AGENT_RUN_EVENTS_READ_TOTAL.labels(
            tenant=self.tenant_label,
            result="success",
        ).inc()
        AGENT_RUN_EVENTS_READ_DURATION_SECONDS.labels(
            tenant=self.tenant_label,
        ).observe(perf_counter() - start)

    @staticmethod
    def set_drift_gauge(tenant_id: str, conversation_id: str, drift: int) -> None:
        try:
            AGENT_RUN_EVENTS_DRIFT.labels(
                tenant=_sanitize_tenant(tenant_id),
                conversation_id=conversation_id,
            ).set(drift)
        except Exception:  # pragma: no cover - best-effort metric
            pass


__all__ = ["RunEventMetrics"]
