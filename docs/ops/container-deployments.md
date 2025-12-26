# Container Deployment Guide

This guide documents the production-grade container workflow for the FastAPI API service and the Next.js web app. It is cloud-agnostic and intended as the baseline for AWS ECS/Fargate and Azure Container Apps.

## Prerequisites
- Docker Engine with BuildKit enabled.
- `.env.compose` at the repo root (see `.env.compose.example`).
- `apps/api-service/.env.local` and `apps/web-app/.env.local` generated via the Starter Console (`starter-console setup wizard`).

## Build Images

From the repo root:

```bash
docker build -f apps/api-service/Dockerfile -t openai-agent-api .
docker build -f apps/web-app/Dockerfile -t openai-agent-web .
```

## Run Containers (local)

### API Service

```bash
docker run --rm \
  --env-file .env.compose \
  --env-file apps/api-service/.env.local \
  -v ./var/keys:/app/var/keys \
  -p 8000:8000 \
  openai-agent-api
```
Notes:
- For demo/dev file-based keys, mount `./var/keys` so the container can persist Ed25519 key material.
- For staging/production, set `AUTH_KEY_STORAGE_BACKEND=secret-manager` and provide `AUTH_KEY_SECRET_NAME` via your secret manager instead of using the file backend.

### Web App

```bash
docker run --rm \
  --env-file apps/web-app/.env.local \
  -p 3000:3000 \
  openai-agent-web
```

## Run Full Stack with Compose

Bring up infra + app stack together:

```bash
docker compose \
  -f ops/compose/docker-compose.yml \
  -f ops/compose/docker-compose.app.yml \
  up --build
```

Notes:
- `docker-compose.app.yml` expects `.env.compose`, `apps/api-service/.env.local`, and `apps/web-app/.env.local` to exist.
- The app compose stack mounts `./var/keys` into the API container for demo/local keyset persistence; production should use `AUTH_KEY_STORAGE_BACKEND=secret-manager`.
- Use `docker compose down` to shut everything down.

## Migrations

For production deployments, run migrations out-of-band (job/task) rather than on API boot:

```bash
just migrate
# or
starter-console release db
```

Set `AUTO_RUN_MIGRATIONS=false` for production API deployments.

## Health Checks
- API: `GET /health/ready` on port 8000
- Web: `GET /api/health/ready` on port 3000

## Cloud Notes (AWS/Azure)
- Use managed Postgres + Redis (RDS/Azure Database, ElastiCache/Azure Cache).
- Keep secrets in the configured provider (AWS Secrets Manager or Azure Key Vault).
- Object storage should use native S3 or Azure Blob (see `apps/api-service/src/app/services/storage/README.md`).
- Follow the release runbook for migrations and rollback: `docs/ops/runbook-release.md`.
