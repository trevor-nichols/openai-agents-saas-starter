# GCP Hosting Guide

This guide describes the production-grade GCP deployment pattern for the starter. The reference
blueprint lives in `ops/infra/gcp` and targets Cloud Run by default.

## Reference Blueprint

Terraform blueprint will live in `ops/infra/gcp/` and provision:
- VPC + Serverless VPC Access connector
- Cloud Run services for API + web + optional worker
- Cloud SQL for Postgres (private IP)
- Memorystore for Redis
- GCS bucket for object storage
- Secret Manager for runtime secrets and signing

## Required GCP Services

- **Cloud Run** for containers
- **Cloud SQL (Postgres)** for database
- **Memorystore** for Redis
- **GCS** for object storage
- **Secret Manager** for signing + runtime secrets
- **Cloud DNS** (optional, for custom domains)

If `enable_project_services=true` (default), Terraform will enable the required APIs. If you set it
to `false`, enable the APIs above manually before running `terraform apply`.

## Quickstart (non-technical)

1. **Build + publish images** using `.github/workflows/build-images.yml`.
2. **Create secrets** in Secret Manager:
   - Signing secret for `GCP_SM_SIGNING_SECRET_NAME`.
   - Keyset secret for `AUTH_KEY_SECRET_NAME` (Ed25519 keyset JSON).
   - Secrets for `DATABASE_URL` and `REDIS_URL` to be injected at runtime.
3. **Run Terraform** in `ops/infra/gcp/` with the required variables.
4. **Wire environment variables** using your chosen domains (or Cloud Run service URLs) for `APP_PUBLIC_URL` and `API_BASE_URL`.
5. **Run migrations** once per deploy (`just migrate` or `starter-console release db`).
6. **Verify health**: `/health/ready` (API) and `/api/health/ready` (web).

## Environment Variables

### API (minimal)
- `ENVIRONMENT`
- `APP_PUBLIC_URL`
- `SECRETS_PROVIDER=gcp_sm`
- `GCP_SM_SIGNING_SECRET_NAME` (secret name or full resource name)
- `GCP_SM_PROJECT_ID` (required when secret names are not fully qualified)
- `GCP_SM_CACHE_TTL_SECONDS` (optional; default 60s)
- `AUTH_KEY_STORAGE_BACKEND=secret-manager`
- `AUTH_KEY_STORAGE_PROVIDER` (defaults to `gcp_sm`)
- `AUTH_KEY_SECRET_NAME`
- `STORAGE_PROVIDER=gcs`
- `GCS_BUCKET`, `GCS_PROJECT_ID`
- `ALLOWED_HOSTS`, `ALLOWED_ORIGINS`

### Web (minimal)
- `API_BASE_URL`

### Auth / credentials
- Use Workload Identity or service account bindings.
- If needed for local tooling, set `GOOGLE_APPLICATION_CREDENTIALS` to a service account key file.

For the full list, see `docs/trackers/CONSOLE_ENV_INVENTORY.md`.

### Terraform -> Env Mapping (core)

| Terraform input | Env var | Notes |
| --- | --- | --- |
| `region` | — | GCP region for Cloud Run and managed services. |
| `project_id` | `GCP_SM_PROJECT_ID` | Used when secret names are not fully qualified. |
| `api_base_url` | `API_BASE_URL` | Required for Cloud Run; use a custom domain or the service URL. |
| `app_public_url` | `APP_PUBLIC_URL` | Required for Cloud Run; used for CORS + link generation. |
| `secrets_provider` | `SECRETS_PROVIDER` | Defaults to `gcp_sm`. |
| `gcp_sm_signing_secret_name` | `GCP_SM_SIGNING_SECRET_NAME` | Secret containing signing key material. |
| `auth_key_storage_provider` | `AUTH_KEY_STORAGE_PROVIDER` | Defaults to `secrets_provider`. |
| `auth_key_secret_name` | `AUTH_KEY_SECRET_NAME` | Ed25519 keyset secret name. |
| `storage_provider` | `STORAGE_PROVIDER` | Defaults to `gcs`. |
| `storage_bucket_name` | `GCS_BUCKET` | Object storage bucket. |

## DNS + HTTPS

Cloud Run provides HTTPS by default. For custom domains:
1. Add a domain mapping in Cloud Run.
2. Follow the DNS verification steps provided by Cloud Run.
3. Update `APP_PUBLIC_URL` and `API_BASE_URL` to the custom domains.

## IAM + Secrets

- Cloud Run service accounts need:
  - `roles/secretmanager.secretAccessor`
  - `roles/cloudsql.client`
  - `roles/storage.objectAdmin` (or narrower per bucket)
- Store `DATABASE_URL` and `REDIS_URL` in Secret Manager and inject via runtime secret references.
- Keep `AUTH_KEY_STORAGE_BACKEND=secret-manager` in hosted environments.

## Billing Worker Topology

When running more than one API replica, move billing retries into a dedicated worker:
- API: `ENABLE_BILLING_RETRY_WORKER=false`, `ENABLE_BILLING_STREAM_REPLAY=false`
- Worker: `ENABLE_BILLING_RETRY_WORKER=true`, `ENABLE_BILLING_STREAM_REPLAY=true`, `BILLING_RETRY_DEPLOYMENT_MODE=dedicated`

In the GCP Terraform blueprint, set `enable_worker_service=true` (and optionally `worker_image`)
to deploy the dedicated worker. The blueprint sets the billing env vars automatically.

## Migrations

Run migrations as a pre-deploy job or one-off task:

```bash
just migrate
# or
starter-console release db
```

## Rollback Notes

- **Fast rollback**: deploy previous image tags to Cloud Run revisions.
- **Infrastructure rollback**: `terraform destroy` will tear down resources, but Cloud SQL deletion
  protection and backups should be enabled for production.

## Notes

- Prefer private IP for Cloud SQL + Serverless VPC Access for Cloud Run.
- Use Artifact Registry for production images when possible. For GHCR/private registries, publish
  public images or front the registry with an Artifact Registry remote repository.

## Ops Checklist

- [ ] Secret Manager contains `DATABASE_URL`, `REDIS_URL`, and signing secrets.
- [ ] Cloud Run services use the correct service account and roles.
- [ ] Custom domains are mapped and DNS is verified (if applicable).
- [ ] Migrations ran successfully.
- [ ] Health checks are green for API and web.
