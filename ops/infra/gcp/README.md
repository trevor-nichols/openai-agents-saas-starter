# GCP Reference Blueprint (Cloud Run)

This Terraform blueprint provisions a production-grade GCP foundation for the API + web apps:
- VPC + Serverless VPC Access connector
- Cloud Run services (API, web, optional worker)
- Cloud SQL (Postgres)
- Memorystore (Redis)
- GCS bucket for object storage
- Secret Manager wiring for runtime secrets and signing

> Default posture: this blueprint assumes **GCP Secret Manager** (`SECRETS_PROVIDER=gcp_sm`).
> Vault/Infisical are optional enterprise paths and require explicitly wiring their env vars via
> `api_env` / `api_secrets`.

## Usage

```bash
cd ops/infra/gcp
terraform init
terraform apply \
  -var "project_name=agent-saas" \
  -var "environment=prod" \
  -var "project_id=<gcp-project-id>" \
  -var "gcp_sm_project_id=<secrets-project-id>" \
  -var "region=us-central1" \
  -var "api_image=<api-image>" \
  -var "web_image=<web-image>" \
  -var "api_base_url=https://api.example.com" \
  -var "app_public_url=https://app.example.com" \
  -var "gcp_sm_signing_secret_name=<signing-secret-name>" \
  -var "auth_key_secret_name=<keyset-secret-name>" \
  -var "db_password=<secure-password>" \
  -var "storage_bucket_name=<unique-bucket-name>" \
  -var 'api_secrets={DATABASE_URL="projects/<project>/secrets/db-url",REDIS_URL="projects/<project>/secrets/redis-url"}'
```

Requires Terraform 1.14.x (pinned in `.tool-versions`).

## Environment Variables

Cloud Run injects a base set of env vars aligned with the API/web defaults. Override or extend with
`api_env`, `web_env`, `api_secrets`, and `web_secrets`.

### API base env
- `PORT=8000`
- `ENVIRONMENT`
- `APP_PUBLIC_URL` (required input)
- `ALLOWED_HOSTS` / `ALLOWED_ORIGINS`
- `SECRETS_PROVIDER=gcp_sm`
- `GCP_SM_PROJECT_ID` (defaults to `project_id` when unset), `GCP_SM_SIGNING_SECRET_NAME`
- `AUTH_KEY_STORAGE_BACKEND=secret-manager`
- `AUTH_KEY_STORAGE_PROVIDER` (defaults to `secrets_provider`)
- `AUTH_KEY_SECRET_NAME`
- `STORAGE_PROVIDER=gcs`
- `GCS_BUCKET`, `GCS_PROJECT_ID`

### Web base env
- `PORT=3000`
- `API_BASE_URL` (required input)

The blueprint expects `DATABASE_URL` and `REDIS_URL` to be provided via `api_secrets` (Secret Manager)
so values are never stored in plain Terraform variables.

## Notes
- `api_base_url` and `app_public_url` are required for Cloud Run to avoid cyclic dependencies and
  ensure CORS/host validation is correct.
- Set `enable_worker_service=true` to deploy a dedicated billing retry worker (uses `worker_image`
  when provided, otherwise `api_image`).
- `enable_project_services=true` (default) enables Cloud Run, Cloud SQL, Secret Manager, Memorystore,
  Storage, IAM, VPC Access, and Service Networking APIs for the project.
- Cloud Run uses the shared runtime service account; IAM roles are scoped to Secret Manager, Cloud SQL,
  and Storage.

For app configuration details, see `docs/ops/hosting-gcp.md`.
