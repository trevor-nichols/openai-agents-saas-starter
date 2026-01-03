# Hosting & Infrastructure Overview

This repo ships production-ready container images and a cloud-agnostic architecture. The reference blueprints below are intentionally minimal, clean, and maintainable, so teams can extend them without coupling application code to a specific cloud provider.

## What Runs Where

- **API service**: FastAPI app (ASGI) plus optional background workers (billing retries, stream fan-out). Runs as a stateless container.
- **Web app**: Next.js 16 server (App Router) with server-rendered routes and BFF API handlers. Proxies should route browser `/api` traffic to this service. Runs as a stateless container.
- **Postgres**: Durable system of record.
- **Redis**: Rate limiting, refresh tokens, billing streams.
- **Object storage**: Tenant-scoped assets + attachments (S3, Azure Blob, GCS, MinIO).
- **Secrets**: Vault/Infisical/AWS Secrets Manager/Azure Key Vault/GCP Secret Manager via the Starter Console.

## Reference Blueprints

- **AWS (ECS/Fargate)** — `ops/infra/aws/` + `docs/ops/hosting-aws.md`
- **Azure (Container Apps)** — `ops/infra/azure/` + `docs/ops/hosting-azure.md`
- **GCP (Cloud Run)** — `ops/infra/gcp/` + `docs/ops/hosting-gcp.md`
- **Release runbook** — `docs/ops/runbook-release.md`

### Terraform tfvars export

Use the Starter Console to generate tfvars templates without hardcoding secrets:

```bash
starter-console infra terraform export --provider aws
```

By default, exports land in `var/infra/<provider>/terraform.tfvars` (gitignored) and redact
sensitive values. See `docs/ops/terraform-export.md` for the full workflow.

## Planned Targets (in progress)

- **Kubernetes (Helm)** — `ops/charts/starter/` + `docs/ops/hosting-kubernetes.md`
- **VPS / Single Server** — `ops/compose/docker-compose.prod.yml` + `docs/ops/hosting-vps.md`

## Deployment Contract (Canonical)

All deployment targets share a common contract so app code stays cloud-agnostic.

### Required inputs
- `project_name`, `environment`
- `api_image`, `web_image` (optional `worker_image`)
- `secrets_provider`, `auth_key_storage_provider`, `auth_key_secret_name`
- `api_secrets` must include `DATABASE_URL` and `REDIS_URL`
- `storage_provider` + bucket/container name
- Optional `api_env`, `web_env`

### Required outputs
- `api_url`, `web_url`
- `storage_bucket`
- `database_endpoint`
- `redis_endpoint`

## DNS + TLS

For custom domains and certificate validation, follow the per-cloud guides:
- AWS Route53 + ACM: `docs/ops/hosting-aws.md`
- Azure DNS + managed certs: `docs/ops/hosting-azure.md`

## Deployment Topologies

- **Single-process**: API + billing retry worker in the same service (default).
- **Split worker**: Run the billing retry worker as a separate service when scaling API replicas to avoid duplicate retries. Configure `ENABLE_BILLING_RETRY_WORKER=false` and `ENABLE_BILLING_STREAM_REPLAY=false` on the API service, and enable the worker deployment with `ENABLE_BILLING_STREAM_REPLAY=true` and `BILLING_RETRY_DEPLOYMENT_MODE=dedicated`.

## Observability

- Log to stdout and forward with platform-native collectors.
- Optionally enable OTLP (`LOGGING_SINKS=otlp`) and point to an OTel collector.

## Secrets & Config

- Use the Starter Console to generate `.env.local` for local/dev, and to seed secrets providers for hosted environments.
- For production, inject secrets via the platform secret manager and pass the rest of the env variables at deploy time.
- In hosted environments, set `AUTH_KEY_STORAGE_BACKEND=secret-manager`, `AUTH_KEY_STORAGE_PROVIDER`, and `AUTH_KEY_SECRET_NAME` so Ed25519 keysets live in the chosen secrets provider.
- The reference blueprints require `DATABASE_URL` and `REDIS_URL` to be stored in Secrets Manager/Key Vault and wired via secret references (avoids plaintext in task definitions). If Terraform creates the database, the admin password still lives in Terraform state—use a remote backend with encryption + tight access or provision the DB outside Terraform if that’s a concern.

For storage provider specifics, see `apps/api-service/src/app/services/storage/README.md`. For secrets
and key‑storage provider setup, see `docs/security/secrets-providers.md`.

### Default vs optional secrets providers

The AWS and Azure reference blueprints are optimized for **cloud‑native secrets** by default:
- AWS: Secrets Manager (`SECRETS_PROVIDER=aws_sm`)
- Azure: Key Vault (`SECRETS_PROVIDER=azure_kv`)
- GCP: Secret Manager (`SECRETS_PROVIDER=gcp_sm`)

Vault and Infisical remain **optional enterprise paths** for teams that already run those systems or
need cross‑cloud governance. If you choose Vault/Infisical, you must explicitly wire their env vars
via `api_env` / `api_secrets` and ensure `AUTH_KEY_STORAGE_PROVIDER` + `AUTH_KEY_SECRET_NAME` are set.

## Secure-by-default

The AWS/Azure blueprints default to private networking and encrypted data paths. AWS also enables HTTPS listeners by default (requires ACM). Dev overrides exist for faster experimentation, but they are explicitly opt-in. See the per-cloud guides for the exact variables.

## CI/CD Defaults

- GitHub Actions workflow: `.github/workflows/build-images.yml`.
- Default registry: **GHCR** (best for forks and quick demos).
- Production recommendation: **ECR (AWS)** or **ACR (Azure)** for cloud‑native auth, private networking, and compliance-friendly ops.
- Optional overrides: provide `REGISTRY_USERNAME` / `REGISTRY_PASSWORD` secrets for custom registries, or use workflow dispatch inputs for registry/image prefix.

## Registry Overrides (ECR / ACR)

See `docs/ops/runbook-release.md` for copy/paste registry override steps. The workflow supports:
- **ECR** via registry host `*.dkr.ecr.<region>.amazonaws.com`
- **ACR** via registry host `<registry>.azurecr.io`

If you keep GHCR private, wire registry credentials in the Terraform blueprints:
- **AWS ECS**: set `registry_server`, `registry_username`, `registry_password` (provisions a Secrets Manager credential for ECS pulls).
- **Azure Container Apps**: set `registry_server`, `registry_username`, `registry_password`.
