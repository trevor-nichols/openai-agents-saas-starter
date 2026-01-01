# Performance Smoke Tests (k6)

This folder contains lightweight, deterministic performance smoke tests. The
smoke suite is designed to be fast enough for CI and runs against the local
stub provider (no external model calls).

## What runs in CI
- `tools/perf/k6/smoke.js`: short load test for `/health`, `/api/v1/chat`, and
  `/api/v1/workflows/analysis_code/run`.
- CI uses a local api-service instance + Redis. No staging URL required.

## Local run
Prereqs:
- `k6` installed and on your PATH.
- Redis available on `localhost:6379` (or set `REDIS_URL`).
- api-service Hatch environment created (`cd apps/api-service && hatch env create`).

Run:
```
cd apps/api-service
just perf-smoke
```

## Override inputs
- `PERF_BASE_URL`: Base URL (default `http://127.0.0.1:8000`).
- `PERF_VUS`: Virtual users (default `1`).
- `PERF_DURATION`: Duration (default `30s`).
- `PERF_ACCESS_TOKEN` + `PERF_TENANT_ID`: Skip fixture seeding if you want to
  target a remote environment.

If `PERF_ACCESS_TOKEN` and `PERF_TENANT_ID` are not provided, the script uses the
`/api/v1/test-fixtures/apply` endpoint to seed a tenant and then logs in.
