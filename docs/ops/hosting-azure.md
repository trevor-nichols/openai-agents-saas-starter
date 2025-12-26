# Azure Hosting Guide

This guide describes the production-ready Azure deployment pattern for the starter.

## Reference Blueprint

Terraform blueprint lives in `ops/infra/azure/` and provisions:
- Container Apps environment
- Container Apps for API + web
- Azure Database for PostgreSQL Flexible Server
- Azure Cache for Redis
- Azure Blob Storage
- Azure Key Vault

## Required Azure Services

- **Container Apps** for containers
- **Azure Database for PostgreSQL**
- **Azure Cache for Redis**
- **Azure Blob Storage**
- **Azure Key Vault** for signing secret + runtime secrets (required for the default Azure blueprint; optional only if you use Vault/Infisical instead)

## Quickstart (non‑technical)

1. **Build + publish images**: run the GitHub Actions workflow (`.github/workflows/build-images.yml`)
   and note the `api_image` and `web_image` tags you want to deploy. The release runbook has copy/paste
   commands for GHCR/ACR.  
2. **Create secrets** in Key Vault:
   - Signing secret named by `AZURE_KV_SIGNING_SECRET_NAME`.
   - (Optional) pre‑create the keyset secret named by `AUTH_KEY_SECRET_NAME`. If you skip this,
     the API will create/update it at first key rotation as long as it has `set` permission.  
   - Required for the default blueprint: secrets for `DATABASE_URL` and `REDIS_URL` so app credentials are injected via Key Vault references instead of plain env vars.  
3. **Run Terraform** in `ops/infra/azure/` with the required variables (see the README).  
4. **Wire environment variables**: use the Terraform outputs to set `APP_PUBLIC_URL` (web) and
   `API_BASE_URL` (web app), plus the required `SECRETS_PROVIDER` and key‑storage values.  
5. **Run migrations** once per deploy (see “Migrations”).  
6. **Verify health**: hit `/health/ready` on the API and `/api/health/ready` on the web app.

## Environment Variables

### API (minimal)
- `ENVIRONMENT` (deployment environment label)
- `DATABASE_URL` (Postgres endpoint)
- `REDIS_URL` (Redis TLS endpoint, `rediss://` with access key)
- `APP_PUBLIC_URL` (web URL)
- `SECRETS_PROVIDER` (defaults to `azure_kv`; can be `vault_hcp`, `infisical_cloud`, etc. for enterprise setups)
- `AZURE_KEY_VAULT_URL`, `AZURE_KV_SIGNING_SECRET_NAME` (required when `SECRETS_PROVIDER=azure_kv`)
- `AUTH_KEY_STORAGE_BACKEND=secret-manager`, `AUTH_KEY_STORAGE_PROVIDER`, `AUTH_KEY_SECRET_NAME`
  (store Ed25519 keyset in the configured secret manager)
- `STORAGE_PROVIDER=azure_blob`
- `AZURE_BLOB_ACCOUNT_URL`, `AZURE_BLOB_CONTAINER`
- `ALLOWED_HOSTS` (set to your API domain or Container App FQDN)
- `ALLOWED_ORIGINS` (set to your web app origin if browser clients call the API directly)

If you use Infisical or Vault for signing or key storage, `SECRETS_PROVIDER` and
`AUTH_KEY_STORAGE_PROVIDER` can differ. See `docs/security/secrets-providers.md` for the full matrix.

> Manual deployments must set `AUTH_KEY_STORAGE_PROVIDER` explicitly when using
> `AUTH_KEY_STORAGE_BACKEND=secret-manager` (Terraform defaults it to `SECRETS_PROVIDER`).

> Note: the **default** Azure blueprint assumes Key Vault. Vault/Infisical are optional enterprise
> paths and require explicitly wiring their env vars via `api_env` / `api_secrets`.

### Web (minimal)
- `API_BASE_URL` (API URL)

For the full list, see `docs/trackers/CONSOLE_ENV_INVENTORY.md`.

### Terraform → Env Mapping (core)

| Terraform input | Env var | Notes |
| --- | --- | --- |
| `environment` | `ENVIRONMENT` | Used for production safety checks. |
| `secrets_provider` | `SECRETS_PROVIDER` | Defaults to `azure_kv`; set to Vault/Infisical if used. |
| `auth_signing_secret_name` | `AZURE_KV_SIGNING_SECRET_NAME` | Key Vault secret name for signing (required when `secrets_provider=azure_kv`). |
| `auth_key_secret_name` | `AUTH_KEY_SECRET_NAME` | Ed25519 keyset stored in secret manager (Key Vault when provider is `azure_kv`). |
| `auth_key_storage_provider` | `AUTH_KEY_STORAGE_PROVIDER` | Key storage provider (defaults to `secrets_provider`). |
| `storage_account_name` | `AZURE_BLOB_ACCOUNT_URL` | Resolved by the platform from the storage account. |
| `storage_container_name` | `AZURE_BLOB_CONTAINER` | Blob container used for object storage. |

## DNS + HTTPS (Azure DNS + Managed Certificates)

Use custom domains like `api.example.com` and `app.example.com`. Container Apps provides HTTPS, but you must bind a custom domain and certificate.

1. **Create DNS zone (if needed)**:
   ```bash
   az network dns zone create --resource-group <dns-rg> --name example.com
   ```
2. **Point CNAME records to the Container App FQDNs** (from Terraform outputs `api_url` / `web_url`):
   ```bash
   az network dns record-set cname set-record \
     --resource-group <dns-rg> --zone-name example.com \
     --record-set-name api --cname <api-fqdn>

   az network dns record-set cname set-record \
     --resource-group <dns-rg> --zone-name example.com \
     --record-set-name app --cname <web-fqdn>
   ```
3. **Bind custom domains + certificates**:
   - Azure Portal: Container App → **Custom domains** → **Add**.
   - Choose **managed certificate** and follow the validation prompt. Azure will show a validation CNAME/TXT record—copy/paste that into Azure DNS.
4. **Wire variables/envs**:
   - Terraform: set `api_base_url=https://api.example.com`, `app_public_url=https://app.example.com`.
   - App env: set `ALLOWED_HOSTS=api.example.com`.

## Managed Identity & Access

- API container app uses a system-assigned managed identity.
- Grant the identity access to Key Vault secrets and Blob storage (Get/List/Set for the keyset secret).
- For presigned uploads/downloads, the identity needs both **Storage Blob Data Contributor** and **Storage Blob Delegator** on the storage account.
- `api_secrets` / `web_secrets` should be wired as Key Vault secret IDs so Container Apps resolve them at runtime without storing secret values in Terraform state.
- Ensure the Key Vault secret named in `AZURE_KV_SIGNING_SECRET_NAME` exists before deploying the API.
- The blueprint requires `DATABASE_URL` and `REDIS_URL` to be provided via `api_secrets` so credentials never appear in app env. Terraform state still stores DB admin passwords if Terraform creates the DB; use a secure remote backend or provision DB creds outside Terraform if that is a concern.
- To fetch a Key Vault secret ID:
  ```bash
  az keyvault secret show --vault-name <vault> --name <secret> --query id -o tsv
  ```

## Billing Worker Topology

When running more than one API replica, move billing retries into a dedicated service:
- API: `ENABLE_BILLING_RETRY_WORKER=false`
- Worker: `ENABLE_BILLING_RETRY_WORKER=true`, `BILLING_RETRY_DEPLOYMENT_MODE=dedicated`

## Migrations

Run migrations as a pre-deploy job or one-off task:

```bash
just migrate
# or
starter-console release db
```

## Rollback Notes

- **Fast rollback**: update the Container App revision to a previous image tag (or scale replicas to 0).
- **Infrastructure rollback**: `terraform destroy` will tear down resources. Private networking and
  managed services are enabled by default; for dev/sandbox teardown, set
  `enable_private_networking=false` and allow public network access first if needed.
- **Secrets**: if you rotate secrets during rollback, update `AZURE_KV_SIGNING_SECRET_NAME` and the
  keyset secret in Key Vault accordingly.

## Notes

- Container Apps provides HTTPS by default; set `APP_PUBLIC_URL` to the HTTPS domain.
- If you omit `api_base_url` / `app_public_url` in Terraform, the blueprint defaults them to the Container Apps environment FQDNs so the web app can reach the API without manual wiring.
- Secure-by-default: the Terraform blueprint enables private networking for Postgres/Redis. Use `enable_private_networking=false` only for dev/sandbox environments.
- If you disable private networking, also set `db_public_network_access_enabled=true` and `redis_public_network_access_enabled=true` for connectivity.
- For production, prefer **ACR** so Container Apps can use native registry auth; if you use private GHCR, set `registry_server`, `registry_username`, and `registry_password` in the Terraform blueprint.
- If the registry password lives in Key Vault, set `registry_password_secret_id` instead of `registry_password`.

## Registry Overrides (ACR)

The CI workflow can publish to ACR when you provide registry credentials and dispatch the workflow with custom inputs.

Copy/paste (GitHub Actions manual run):
```
registry: <registry>.azurecr.io
image_prefix: agent-saas
```

Set GitHub secrets:
- `REGISTRY_USERNAME` = ACR username
- `REGISTRY_PASSWORD` = ACR password

## GHCR Example (private)

Use GHCR only if you want to manage registry credentials yourself (ACR is preferred on Azure).

GitHub Actions manual run:
```
registry: ghcr.io
image_prefix: <owner>/<repo>
```

Terraform inputs (Container Apps pulls):
```
registry_server = "ghcr.io"
registry_username = "<github-username-or-bot>"
registry_password = "<ghcr-pat>"
```
