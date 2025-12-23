<!-- SECTION: Title -->
# Redis Isolation Milestone — INFRA-004

_Last updated: November 16, 2025_

## Objective
Give every Redis-backed subsystem (rate limiting, auth/session caches, nonce + token stores, billing streams) its own authenticated, TLS-enforced pool so production tenants cannot interfere with one another and outages remain isolated.

## Scope & Current Risks
| Area | Status | Notes |
| --- | --- | --- |
| Rate limiting | ✅ Complete | Dedicated `RATE_LIMIT_REDIS_URL` with TLS/auth enforcement wired through the new factory + rate limiter bootstrap. |
| Auth & session caches | ✅ Complete | `AUTH_CACHE_REDIS_URL` feeds login throttles, lockouts, refresh-token cache, and password history via shared clients managed by the factory. |
| Nonce/token stores | ✅ Complete | `SECURITY_TOKEN_REDIS_URL` backs nonce/email/password/token stores with per-loop caches and hardened clients. |
| Billing streams | ✅ Complete | Billing SSE backend now uses a dedicated client sourced from `BILLING_EVENTS_REDIS_URL` (fallback `REDIS_URL`) with factory-managed lifetime. |

## Purpose Matrix
| Purpose | Consumers | Env var (fallback) | Hard requirements |
| --- | --- | --- | --- |
| Rate limiting | `RateLimiter`, signup guards, chat/billing streaming quotas | `RATE_LIMIT_REDIS_URL` (`REDIS_URL`) | Dedicated logical DB/instance, TLS (`rediss://`) + auth outside local/dev, short TTL tuning |
| Auth/session cache | Login throttler, lockout store, refresh-token cache, password history | `AUTH_CACHE_REDIS_URL` (`REDIS_URL`) | Long-lived connections, pipelining safe, stored data considered PII ⇒ require auth + ACL |
| Security tokens | Vault nonce store, email verification, password reset, status alert tokens | `SECURITY_TOKEN_REDIS_URL` (`REDIS_URL`) | Must fail closed; TTL-critical; same TLS/auth requirements |
| Billing streams | Stripe replay/backfill service + SSE endpoints | `BILLING_EVENTS_REDIS_URL` (`REDIS_URL`) | Streams need persistence + higher maxlen; SSE readiness gated on connectivity |

## Execution Plan
1. **Config & CLI surfaces** — Introduce the new env vars in `Settings`, Starter CLI wizard, env templates, and trackers. Harden validation (TLS/auth) for non-demo profiles.
2. **Redis client factory** — Centralize client creation per purpose with TLS/auth enforcement + clean shutdown hooks; wire into the FastAPI container.
3. **Service refactors** — Route `RateLimiter`, auth/login throttles, lockout store, refresh-token cache, nonce/token stores, and billing stream backend through the factory so each purpose uses its own pool.
4. **Docs & validation** — Document rollout guidance, update ISSUE_TRACKER + CLI inventory, and add tests covering fallbacks + wizard prompts.

## Deliverables
- New env contract documented in `.env.local.example`, CLI inventory, and operator docs.
- Redis client factory with per-purpose handles + shutdown path.
- Auth/security/billing subsystems consuming their dedicated pools with explicit fallbacks.
- Tracker + ISSUE entry updated with closure details once merged.

## Changelog
- **2025-11-16**: Milestone drafted, inventory of Redis consumers captured, and execution plan approved.
- **2025-11-16**: Implemented `RATE_LIMIT_REDIS_URL`, `AUTH_CACHE_REDIS_URL`, and `SECURITY_TOKEN_REDIS_URL`, introduced the Redis client factory + shutdown path, rewired auth/security/billing services, documented the new contract, and updated the CLI wizard/templates.

## Sign-off
- **Owner**: @codex
- **Date**: November 16, 2025
- **Summary**: Configuration surfaces, runtime wiring, and regression coverage for dedicated Redis pools landed. ISSUE_TRACKER updated and milestone archived under `docs/trackers/complete/`.
