<!-- SECTION: Title -->
# GeoIP & Session Telemetry Milestone (OBS-007)

_Last updated: November 17, 2025_

## Objective
Implement a production-grade GeoIP enrichment pipeline so authentication sessions carry accurate city/region/country metadata, telemetry is exportable through the structured logging stack, and operators can provision providers through the Starter Console without touching backend code.

## Scope
### In scope
- Add configurable `GeoIPService` implementations for the agreed providers (IPinfo SaaS, MaxMind GeoIP2/GeoLite2, IP2Location SaaS + downloadable DB).
- Wire provider selection into `Settings`, DI container bootstrap, and the auth/session services.
- Extend Starter Console wizard + validators so operators can pick a provider, validate credentials, and bootstrap self-hosted databases when desired.
- Cover session repository/API flows with tests to prove enrichment works across auth login, session listing, and revocation paths.
- Document operational guidance (provider setup, DB refresh cadence, telemetry alerts) and update trackers/docs accordingly.

### Out of scope
- Full threat-intel/proxy detection (future OBS follow-up).
- Replacing the existing structured logging sink (handled by OBS-006).
- Frontend UI changes beyond surfacing the GeoIP fields already exposed through the API.

## Architecture Threads
- **Provider contract & configuration** — finalize env knob names (`GEOIP_PROVIDER`, `GEOIP_IPINFO_TOKEN`, `GEOIP_MAXMIND_LICENSE_KEY`, `GEOIP_IP2LOCATION_API_KEY`, `GEOIP_MAXMIND_DB_PATH`, `GEOIP_IP2LOCATION_DB_PATH`), validation rules, and CLI inventory entries. Establish a fallthrough order (`ipinfo` → `maxmind_db` → `ip2location_db`) and document how we short-circuit when providers fail.
- **Service implementations** — create async clients for IPinfo + IP2Location HTTP APIs (timeout/retry, rate limit safe) and local readers for MaxMind/IP2Location database files. Each must translate provider responses into `SessionLocation`.
- **Container wiring** — update `ApplicationContainer` bootstrap to instantiate the right provider once, share it across auth/session services, and ensure graceful shutdown (closing httpx clients, file handles).
- **Data quality + telemetry** — enhance `SessionStore` logging for lookup errors/success, add structured metrics counters if needed, and ensure repository models persist the GeoIP fields set.
- **Starter Console UX** — update `observability` wizard section with provider descriptions, optional automation for database download (re-using `--auto-infra`), and validation hooks that hit the provider or verify DB presence in both interactive and headless flows.
- **Docs & changelog** — create/runbook under `docs/observability/geoip.md`, refresh `ISSUE_TRACKER.md`, `CONSOLE_ENV_INVENTORY.md`, and `starter_console/README.md` with the new flows, then file closure notes once OBS-007 is merged.

## Implementation Plan
| # | Task | Description | Owner | Status | Target |
| - | ---- | ----------- | ----- | ------ | ------ |
| 1 | Provider contract & env design | Finalize provider list, env var schema, validation rules, and fallthrough order; update `Settings` + CLI inventory. | Platform Foundations | ✅ Completed | Nov 17 |
| 2 | IPinfo HTTP adapter | Implement async client + `GeoIPService` wrapper with caching, timeout/retry, and structured logging; add unit tests and fixture recordings. | Platform Foundations | ✅ Completed | Nov 17 |
| 3 | MaxMind database adapter | Add local DB reader (GeoIP2/GeoLite2), automatic refresh hook (Make task/CLI automation), and configuration knobs for license + DB path. | Platform Foundations | ✅ Completed | Nov 17 |
| 4 | IP2Location adapters | Ship both SaaS HTTP and local BIN readers, sharing parsing helpers with the MaxMind flow where possible. | Platform Foundations | ✅ Completed | Nov 17 |
| 5 | Container + auth wiring | Inject provider into `ApplicationContainer`, `AuthService`, and `SessionStore`; add provider health logging during startup. | Platform Foundations | ✅ Completed | Nov 17 |
| 6 | Starter Console wizard updates | Expand `observability` section prompts, add provider-specific validation, support optional DB download automation, and update audit output. | Platform Foundations | ✅ Completed | Nov 17 |
| 7 | Persistence/API verification | Add database migration checks (if schema tweaks surface), update repositories/tests so GeoIP fields materialize in list/get responses, and extend contract tests. | Platform Foundations | ✅ Completed | Nov 17 |
| 8 | Documentation & tracker updates | Publish `docs/observability/geoip.md`, refresh README + trackers, and capture rollout guidance (monitoring, failover steps). | Platform Foundations | ✅ Completed | Nov 17 |
| 9 | Rollout checklist | Define enablement steps (staging dry-run, provider credentials, CLI wizard instructions) and update `docs/trackers/ISSUE_TRACKER.md` once production-ready. | Platform Foundations | ✅ Completed | Nov 17 |

## Deliverables
- Configurable GeoIP service implementations (IPinfo, MaxMind DB, IP2Location HTTP + DB).
- Starter Console wizard + automation covering provider selection/validation.
- Comprehensive tests: unit (provider adapters), integration (session repository), contract (API responses).
- Operator documentation + updated trackers verifying OBS-007 completion.

## Dependencies
- OBS-006 structured logging stack (already deployed) for instrumentation.
- Redis/auth refactors (complete) to store telemetry safely.
- Provider credentials or license files supplied via CLI wizard during setup.

## Risks & Mitigations
1. **Licensing compliance for database downloads** — ensure CLI automation only runs when license keys are present and store checksums of downloaded DBs. _Mitigation_: add checksum + EULA acceptance prompt.
2. **Provider rate limits during login bursts** — without caching we could saturate allowances. _Mitigation_: embed LRU/memory cache per provider and allow sampling toggle if needed.
3. **DB freshness drift** — local databases can go stale. _Mitigation_: document refresh Make target + optional cron hook; log warnings when DB age exceeds SLA.

## Decisions
1. **Provider default posture** — `GEOIP_PROVIDER` stays `none` by default so fresh checkouts never emit external traffic, but the CLI wizard will warn and strongly recommend selecting `ipinfo` (or another explicit provider) for `staging`/`production` profiles. FastAPI startup logs will emit a caution when non-dev environments launch without enrichment.
2. **Self-hosted database expectation** — Self-hosted MaxMind/IP2Location DB downloads remain optional resilience layers. Every non-dev profile must pick a primary SaaS/HTTP provider, while the wizard exposes an “enable local DB mirror” toggle that triggers the download automation when teams need data residency or offline support.
3. **Data retention & obfuscation** — Session telemetry will continue storing only coarse city/region/country strings (no lat/long or ISP) with recommended 90-day retention and purge guidance in the runbook. We will add doc notes about tenant-level opt-outs and ensure logs never emit raw IPs after enrichment succeeds. A future `GEOIP_STORE_LOCATION=false` escape hatch will be documented for tenants that must disable persistence entirely.
