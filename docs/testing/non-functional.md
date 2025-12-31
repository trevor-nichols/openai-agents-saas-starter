# Non-Functional Testing

This repo follows a layered test strategy. Functional tests live under
`apps/api-service/tests/`. Non-functional tests are kept separate so they can
run on their own cadence without slowing PR feedback.

## Security scanning (already in CI)
- SAST: GitHub CodeQL (`.github/workflows/codeql.yml`).
- Secrets scan: Gitleaks (`.github/workflows/secrets-scan.yml`).
- Dependency review: `dependency-review` action on PRs.
- SCA + SBOMs: `backend-ci.yml` (pip-audit/pnpm audit + CycloneDX).

## Performance smoke (CI-friendly)
- Purpose: fast, deterministic signal for critical API endpoints.
- Tool: k6 (`tools/perf/k6/smoke.js`).
- Runs: PRs + main branch (short duration, low VUs).
- Target: local stub provider (no external dependencies).

Run locally:
```
cd apps/api-service
just perf-smoke
```

## Load / stress testing (manual or scheduled)
For heavier tests, target a real environment and provide credentials:
- Set `PERF_BASE_URL` to your deployed API.
- Provide `PERF_ACCESS_TOKEN` + `PERF_TENANT_ID` (or enable `/test-fixtures`).

These should run on a nightly schedule or manual trigger in CI to avoid
blocking PRs.

## Chaos / fault-injection (manual only)
Chaos testing intentionally breaks dependencies (Redis/Postgres/HTTP latency)
so we can verify retries, error handling, and graceful degradation. In a starter
repo, keep this manual and run it only in a staging-like environment.

Starter scaffold:
- `tools/chaos/run_chaos_stub.sh` is a non-destructive stub (defaults to a dry-run).
- `.github/workflows/chaos-manual.yml` provides a manual entrypoint for operators.

Follow-up for real deployments:
- Wire an injector (e.g., toxiproxy/service-mesh faults) and implement scenarios
  inside `tools/chaos/`.
