# API Service Test Taxonomy

This suite follows a layered test pyramid. Each layer has a clear intent and runtime cost.

- Unit (`tests/unit/`): fast, isolated tests over pure functions/services with fakes.
- Contract (`tests/contract/`): API boundary tests (FastAPI/TestClient) and schema/stream fixture validation.
- Integration (`tests/integration/`): resource-dependent suites (e.g., Postgres/Redis/Stripe adapters).
- Smoke (`tests/smoke/http/`): API-level end-to-end checks against a running service (shallow, fast).
- Manual (`tests/manual/`): opt-in live-provider checks used to record streaming fixtures; never run in CI.

Manual streaming tests can record NDJSON fixtures consumed by
`tests/contract/streams/test_stream_goldens.py` for deterministic CI validation.
