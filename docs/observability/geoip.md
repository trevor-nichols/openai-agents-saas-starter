# GeoIP Provider Playbook (OBS-007)

**Last updated:** November 17, 2025  
**Owners:** Platform Foundations – Observability

## 1. Purpose
Session telemetry now records the city/region/country derived from login IPs so security teams can audit device posture and alert on anomalous activity. This document describes the supported providers, configuration surface, CLI workflows, and retention expectations that ship with OBS-007.

## 2. Provider Matrix

| Provider | Mode | Requirements | Notes |
| --- | --- | --- | --- |
| `ipinfo` | SaaS API | `GEOIP_IPINFO_TOKEN` | Fastest setup. Recommended primary provider for staging/production. |
| `ip2location` | SaaS API | `GEOIP_IP2LOCATION_API_KEY` | Lower-cost alternative; limited fields but predictable pricing. |
| `maxmind_db` | Self-hosted `.mmdb` | `GEOIP_MAXMIND_LICENSE_KEY`, `GEOIP_MAXMIND_DB_PATH` | Ships GeoIP2/GeoLite2 databases locally. Wizard can download/refresh bundles. |
| `ip2location_db` | Self-hosted `.bin` | `GEOIP_IP2LOCATION_DB_PATH` | Operators supply BIN files manually (download token varies per license). |
| `none` | Disabled | — | Local/dev-only escape hatch; session telemetry shows `unknown`. |

All providers honor the shared cache knobs: `GEOIP_CACHE_TTL_SECONDS`, `GEOIP_CACHE_MAX_ENTRIES`, and `GEOIP_HTTP_TIMEOUT_SECONDS`. Default TTL is 900 seconds with 4 096 entries, keeping outbound requests within rate limits while ensuring recent lookups stay warm.

## 3. Setup Workflow

### 3.1 SaaS APIs (IPinfo, IP2Location)
1. Run `starter-console setup wizard --profile <env>` (interactive) or pass `--answers-file` for headless mode.
2. In the `[M3] Tenant & Observability` step choose `ipinfo` or `ip2location`.
3. Provide the API token when prompted. Secrets are written to `apps/api-service/.env.local` with masking in the console output.
4. Adjust cache TTL/capacity/timeouts if the default 900 s/4 096 entries/2 seconds does not match your expected login burst.
5. Redeploy FastAPI or restart the dev server; the container bootstrap will instantiate the correct provider immediately.

### 3.2 MaxMind GeoLite2 / GeoIP2 (Self-hosted)
1. Obtain a MaxMind license key (free GeoLite2 keys work for most dev/staging stacks).
2. In the wizard select `maxmind_db`, enter the license key, and confirm the destination path (default `var/geoip/GeoLite2-City.mmdb`).
3. The wizard asks whether to download/refresh the database now. Confirming triggers the new helper that calls MaxMind’s download endpoint, extracts the `.mmdb` payload, and saves it to the resolved path (relative paths land under the repo root).
4. On CI/headless runs, the download step auto-enables for non-`local` profiles; failures surface as CLI errors so pipelines can retry with a fresh key.
5. Store the resulting `.mmdb` file somewhere persistent (Docker volume, baked artifact). Re-run the wizard or `starter-console setup wizard --report-only` whenever you rotate the file so the audit log captures the decision.

### 3.3 IP2Location BIN (Self-hosted)
1. Supply a BIN path via the wizard prompt (default `var/geoip/IP2LOCATION-LITE-DB3.BIN`). The CLI warns if the file is missing after the run.
2. Download/refresh the BIN file using your IP2Location portal/token; automation varies per license, so we keep this manual for now.
3. Restart FastAPI; the new adapter loads the BIN file lazily and uses asyncio threads to avoid blocking the event loop.

## 4. Runtime Behavior
- The bootstrapper (`main.py`) calls `build_geoip_service(settings)` once, stores the provider in `ApplicationContainer`, and reuses it everywhere (`AuthService`, `SessionStore`). Shutdown hooks close HTTP clients/readers cleanly.
- Providers normalize/skip private, loopback, link-local, multicast, and reserved IPs to avoid noisy lookups.
- Lookup failures emit structured events (`geoip.lookup_*`) so observability dashboards can alert on upstream issues (timeouts, invalid credentials, missing databases).
- `SessionStore` only stores coarse metadata (`city`, `region`, `country`). We never persist lat/long, ASN, or ISP data by default.

## 5. Retention & Compliance
- **Retention target:** 90 days of session history. Use the existing session retention job (tracked separately) to prune records beyond the SLA.
- **Opt-out:** set `GEOIP_PROVIDER=none` if regulators require zero storage. Per-tenant storage disabling is not supported in this release.
- **PII handling:** structured logs should not include raw IP addresses once enrichment succeeds; only hashed/masked addresses remain in the repository.

## 6. Monitoring & Alerting
- Add log-based alerts for `event:geoip.lookup_http_error` and `event:geoip.lookup_invalid_credentials` scoped by provider.
- Include GeoIP status in health dashboards: surface provider, cache stats, and last download timestamp (for DB modes) so operators notice stale databases before accuracy degrades.
- Document provider-specific quotas (IPinfo free tier: 50k requests/month; IP2Location: plan-dependent) in runbooks and tie them to signup forecasts.

## 7. CLI Recap
- Wizard prompts now cover provider choice + secrets, cache knobs, and DB paths.
- MaxMind automation reuses the supplied license key to pull `GeoLite2-City` bundles—rerun the wizard (or call the helper module) during cron-based refreshes.
- Audit output (`var/reports/setup-summary.json`) captures the provider + path decisions so infra reviews can trace who enabled GeoIP enrichment per environment.

Refer back to this playbook whenever you add new providers or adjust retention policies; keep the table and guidance in sync with OBS updates.
