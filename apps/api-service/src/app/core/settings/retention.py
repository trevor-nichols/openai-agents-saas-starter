"""Retention and housekeeping settings for conversation history."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RetentionSettingsMixin(BaseModel):
    run_events_ttl_days: int = Field(
        default=180,
        ge=1,
        description="Number of days to retain agent_run_events before cleanup.",
        alias="RUN_EVENTS_TTL_DAYS",
    )
    run_events_cleanup_batch_size: int = Field(
        default=10_000,
        ge=1,
        description="Delete batch size for run-event cleanup jobs.",
        alias="RUN_EVENTS_CLEANUP_BATCH",
    )
    run_events_cleanup_sleep_ms: int = Field(
        default=0,
        ge=0,
        description="Sleep between cleanup batches in milliseconds (throttle).",
        alias="RUN_EVENTS_CLEANUP_SLEEP_MS",
    )

    workflow_min_purge_age_hours: int = Field(
        default=0,
        ge=0,
        description=(
            "Minimum age in hours before a workflow run can be hard-deleted. "
            "Set to 0 to disable the guard."
        ),
        alias="WORKFLOW_MIN_PURGE_AGE_HOURS",
    )
