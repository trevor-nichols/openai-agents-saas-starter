# OPS-003 — Third-party Env Parity

| Field | Detail |
| --- | --- |
| Owner | *@codex* |
| Status | Completed (Nov 16 2025) |
| Scope | Enforce Stripe/Resend configuration parity across FastAPI runtime, CLI flows, and CI. |

## Deliverables

1. **Central validator** (`app/core/provider_validation.py`) that inspects provider toggles and
   returns structured violations (provider, code, severity). FastAPI startup now calls this helper
   before wiring Redis, billing, or agents.
2. **Runtime enforcement** — Lifespan logs every violation and raises on fatal issues (any hardened
   environment). Local development still emits warnings but keeps running for prototyping.
3. **Tool registry parity** — core services respect enabled providers so agent capabilities reflect
   actual provider coverage.
4. **Operator tooling** — `starter-console providers validate` (and
   `just validate-providers`) fail fast when required env vars are missing. CI can pass `--strict`
   to block merges before Docker builds/deployments.
5. **Documentation** — `docs/ops/provider-parity.md` captures the enforcement matrix, remediation
   steps, and references back to Stripe/Resend runbooks.

## Follow-ups / monitoring

- Keep `docs/ops/provider-parity.md` updated as new providers (search APIs, email vendors, billing
  processors) are added.
- When tenant-level entitlements diverge, wire that metadata into the validator so providers can be
  scoped per-tenant rather than globally fatal.
- Wire the CLI command into CI (GitHub Action) once the backend workflow is updated to call
  `just validate-providers` ahead of migrations/tests.
