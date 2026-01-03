# VPS / Single-Server Hosting Guide

This guide documents a production-grade single-server deployment using Docker Compose and Caddy.
The production compose file will live in `ops/compose/docker-compose.prod.yml`.

## Recommended Stack

- Docker Engine + Compose plugin
- Caddy for TLS + reverse proxy
- Managed Postgres/Redis when possible (or local containers for small deployments)
- Object storage via S3-compatible provider or MinIO

## Prerequisites

- Linux VPS with public IP
- Docker Engine + Compose plugin
- Domain names for web and API (or a single domain with `/api` path)
- Ports 80/443 open on the firewall

## Quickstart (non-technical)

1. **Provision secrets provider** (recommended: Infisical Cloud or Vault).
2. **Generate env files** with `starter-console setup wizard` for the target profile.
3. **Copy env files** to the server (`.env.compose`, `apps/api-service/.env.local`, `apps/web-app/.env.local`).
4. **Configure Caddy** with your domain names.
5. **Run Compose**:
   ```bash
   docker compose -f ops/compose/docker-compose.prod.yml up -d
   ```
   For a dedicated billing worker:
   ```bash
   docker compose -f ops/compose/docker-compose.prod.yml -f ops/compose/docker-compose.worker.yml --profile worker up -d
   ```
6. **Run migrations** once per deploy (`starter-console release db`).
7. **Verify health**: `/health/ready` (API) and `/api/health/ready` (web).

## Compose Layout

`ops/compose/docker-compose.prod.yml` includes:
- `caddy` (TLS + reverse proxy)
- `api` and `web`
- `worker` (profile: `worker`)
- `postgres` and `redis` (profile: `local-db`)
Enable optional services with `--profile local-db` and/or `--profile worker`.

### Required env vars

- `API_IMAGE` (required)
- `WEB_IMAGE` (required)
- `WORKER_IMAGE` (optional; defaults to `API_IMAGE`)
- `APP_HOST` (required for Caddy, ex: `app.example.com`)
- `CADDY_EMAIL` (recommended for ACME)

Optional:
- `API_HOST` (if you want a separate API domain; uncomment the block in `ops/compose/caddy/Caddyfile`).

### Local DB profile notes

If you enable `--profile local-db`, make sure your API env uses the Compose service names:
- `DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/saas_starter_db`
- `REDIS_URL=redis://redis:6379/0`

## Secrets + Key Storage

- Production should use `AUTH_KEY_STORAGE_BACKEND=secret-manager`.
- Choose a secrets provider supported by the console (Infisical/Vault/AWS/Azure/GCP).
- Avoid filesystem key storage outside demo/dev.

### Environment Variables (minimal)

API:
- `ENVIRONMENT`
- `APP_PUBLIC_URL`
- `SECRETS_PROVIDER`
- `AUTH_KEY_STORAGE_BACKEND=secret-manager`
- `AUTH_KEY_STORAGE_PROVIDER`
- `AUTH_KEY_SECRET_NAME`
- `STORAGE_PROVIDER` plus provider-specific settings

Web:
- `API_BASE_URL`

## Storage Options

- **Recommended:** external S3-compatible storage.
- **Self-hosted:** run MinIO with persistent volumes and backup schedules (see `ops/compose/docker-compose.minio.yml`).

## Data Persistence + Backups

### Volumes (local-db profile)
- Postgres: `postgres-data`
- Redis: `redis-data` (AOF enabled)
- Caddy: `caddy_data`, `caddy_config`
- MinIO (optional): `minio-data` in `ops/compose/docker-compose.minio.yml`

### Backups (self-hosted only)
- **Postgres:** run `pg_dump` (or `pg_basebackup`) on a schedule and store off-host.
- **Redis:** keep AOF enabled and snapshot with `redis-cli BGSAVE` if using RDB backups.
- **MinIO:** use `mc mirror` or `rclone sync` to an external bucket.
- Backup `var/keys` only for dev/local; production keys should live in secret managers.

### Recommended topology
- Use managed Postgres/Redis where possible; keep `local-db` for small or dev stacks only.

## TLS / Reverse Proxy

- Caddy terminates TLS and proxies `/` to the web app and `/api` to the API service.
- Ensure `APP_PUBLIC_URL` and `API_BASE_URL` use HTTPS.

## Billing Worker Topology

When running more than one API replica (rare on a single VPS), move billing retries into a dedicated worker:
- API: `ENABLE_BILLING_RETRY_WORKER=false`
- Worker: `ENABLE_BILLING_RETRY_WORKER=true`, `BILLING_RETRY_DEPLOYMENT_MODE=dedicated`
Use the worker override file to disable retries in the API container:
```bash
docker compose -f ops/compose/docker-compose.prod.yml -f ops/compose/docker-compose.worker.yml --profile worker up -d
```

## Migrations

Run migrations as a pre-deploy job or one-off task:

```bash
starter-console release db
```

## Rollback Notes

- **Fast rollback**: pin previous image tags and restart the compose stack.
- **Data rollback**: use Postgres backups; do not rely on container rollbacks for state.

## Upgrade Notes

1. Pull new images (`docker compose pull`).
2. Run migrations (`starter-console release db`).
3. Restart the stack (`docker compose up -d`).

## Ops Checklist

- [ ] Firewall allows ports 80/443 only (plus SSH).
- [ ] Caddy certificates issued and renewed.
- [ ] Secrets provider configured and reachable.
- [ ] Backups scheduled for Postgres/Redis/MinIO if self-hosted.
- [ ] Health checks are green for API and web.
