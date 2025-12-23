# Azure Reference Blueprint (Container Apps)

This Terraform blueprint provisions a production-grade Azure foundation for the API + web apps:
- Container Apps environment
- Container Apps for API + web
- Azure Database for PostgreSQL Flexible Server
- Azure Cache for Redis
- Azure Blob Storage
- Azure Key Vault

> Default posture: this blueprint assumes **Azure Key Vault** (`SECRETS_PROVIDER=azure_kv`).
> Vault/Infisical are optional enterprise paths and require explicitly wiring their env vars via
> `api_env` / `api_secrets`.

## Usage

```bash
cd ops/infra/azure
terraform init
terraform apply \
  -var "project_name=agent-saas" \
  -var "environment=prod" \
  -var "api_image=<api-image>" \
  -var "web_image=<web-image>" \
  -var "secrets_provider=azure_kv" \
  -var "api_base_url=https://api.example.com" \
  -var "app_public_url=https://app.example.com" \
  -var "registry_server=ghcr.io" \
  -var "registry_username=<registry-user>" \
  -var "registry_password=<registry-token>" \
  # or: -var "registry_password_secret_id=<key-vault-secret-id>" \
  -var "db_admin_password=<secure-password>" \
  -var "storage_account_name=<unique-storage-name>" \
  -var "key_vault_name=<unique-kv-name>" \
  -var "log_analytics_name=<workspace-name>" \
  -var "auth_signing_secret_name=<signing-secret-name>" \
  -var "auth_key_secret_name=<keyset-secret-name>" \
  -var "auth_key_storage_provider=azure_kv"
```

Requires Terraform 1.14.x (pinned in `.tool-versions`).

## Environment Variables

The container apps inject base env vars aligned with the application defaults. Override or extend with `api_env`, `web_env`, `api_secrets`, and `web_secrets`.

### API base env
- `PORT=8000`
- `APP_PUBLIC_URL` (set via `app_public_url`; use your web app domain)
- `DATABASE_URL` (Postgres connection string). Omitted automatically when `api_secrets` includes `DATABASE_URL`.
- `REDIS_URL` (Redis TLS endpoint with access key). Omitted automatically when `api_secrets` includes `REDIS_URL`.
- `SECRETS_PROVIDER=azure_kv`
- `AZURE_KEY_VAULT_URL`
- `AZURE_KV_SIGNING_SECRET_NAME`
- `AUTH_KEY_STORAGE_BACKEND=secret-manager`
- `AUTH_KEY_STORAGE_PROVIDER` (defaults to `secrets_provider`)
- `AUTH_KEY_SECRET_NAME`
- `STORAGE_PROVIDER=azure_blob`
- `AZURE_BLOB_ACCOUNT_URL`
- `AZURE_BLOB_CONTAINER`
- `ALLOWED_HOSTS` (defaults to the API Container App FQDN; override when using custom domains)
- `ALLOWED_ORIGINS` (defaults to the web app URL; override if you have additional browser origins)

### Web base env
- `PORT=3000`
- `API_BASE_URL` (set via `api_base_url`; use your API domain)

For production, set secret values via `api_secrets` / `web_secrets` using Key Vault secret IDs (so Terraform state does not store values).
The blueprint requires `DATABASE_URL` and `REDIS_URL` to be stored in Key Vault and wired via `api_secrets` to avoid plaintext in container app env vars.
If your registry password is also stored in Key Vault, provide `registry_password_secret_id` instead of `registry_password`.

If you omit `api_base_url` / `app_public_url`, the blueprint defaults them to the Container Apps environment
FQDNs so the web app can reach the API without manual wiring.

## Security Defaults & Dev Overrides

This blueprint is secure-by-default:
- Private networking for Postgres + Redis (VNet + private endpoints).
- Redis TLS enabled (`rediss://`).
- Storage account enforces HTTPS-only and TLS 1.2+.

If you need a softer dev posture, override these variables:
- `enable_private_networking=false`
- `db_public_network_access_enabled=true`
- `redis_public_network_access_enabled=true`

## Notes
- Postgres + Redis default to private networking; set `enable_private_networking=false` only for dev/sandbox use.
- The API container app uses a system-assigned managed identity for Key Vault and Blob access.
- Create Key Vault secrets (e.g., `auth_signing_secret_name` and any `api_secrets`/`web_secrets`) before applying the container app configuration.
- The keyset secret (`auth_key_secret_name`) is created/updated by the API at runtime; ensure the API identity has `Set` permissions.
- For private registries (including GHCR/ACR), set `registry_server`, `registry_username`, and `registry_password` so Container Apps can pull images.

For app configuration details, see `docs/ops/hosting-azure.md`.
