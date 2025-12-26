# Retention: agent_run_events

Defaults (env-driven)
- `RUN_EVENTS_TTL_DAYS`: 180 (prod), set lower for non-prod (e.g., 30).
- `RUN_EVENTS_CLEANUP_BATCH`: 10_000 rows per delete batch.
- `RUN_EVENTS_CLEANUP_SLEEP_MS`: 0 (set to >0 to throttle batches).

Cleanup command (env-loaded via Starter Console)
- Dry run: `just cleanup-run-events dry_run=true`
- Override TTL: `just cleanup-run-events days=90`
- Throttle: `just cleanup-run-events sleep_ms=200`

Notes
- No backfill required for greenfield; cleanup is safe once TTL reached.
- Use dry-run first in new environments to confirm match counts.
