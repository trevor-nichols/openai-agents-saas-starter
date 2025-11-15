# Secrets Provider Options & Runbooks

**Last Updated:** 2025-11-15  
**Owners:** Platform Foundations · Backend Auth Pod

## 1. Supported Providers

| Provider | Use Cases | Status | Notes |
| --- | --- | --- | --- |
| Vault Dev (Docker) | Local development and smoke tests | ✅ Available | `make vault-up`, static root token, no TLS. Never expose to production traffic. |
| HCP Vault (Dedicated/SaaS) | Production/staging Vault Transit | ✅ Available | Requires Transit engine + namespace. CLI onboarding collects addr/token/namespace. |
| Infisical Cloud | Managed secrets + signing for cost-sensitive tenants | ✅ Available | Service token + workspace metadata stored in env. Uses HMAC-SHA256 signing secret. |
| Infisical Self-Hosted | Enterprises needing VPC-only installs | ✅ Available | Same flow as cloud plus optional CA bundle path. |
| AWS Secrets Manager | Cloud-native fallback | ✅ Available | Uses Secrets Manager-stored HMAC secret; CLI validates IAM access. |
| Azure Key Vault | Cloud-native fallback | ✅ Available | Uses Key Vault secret as HMAC key; supports SPN + managed identity. |

## 2. Environment Variables

| Env Var | Vault Dev/HCP | Infisical | AWS SM | Description |
| --- | --- | --- | --- | --- |
| `SECRETS_PROVIDER` | `vault_dev` / `vault_hcp` | `infisical_cloud` / `infisical_self_host` | `aws_sm` | Selected provider. |
| `VAULT_ADDR` | ✅ | — | — | Vault base URL (http://127.0.0.1:18200 for dev). |
| `VAULT_TOKEN` | ✅ | — | — | Vault token/AppRole secret for Transit. |
| `VAULT_TRANSIT_KEY` | ✅ | — | — | Transit key used for signing/verification. |
| `VAULT_NAMESPACE` | Optional | — | — | HCP namespaces (default `admin`). |
| `VAULT_VERIFY_ENABLED` | ✅ | — | — | Enables signature verification. |
| `INFISICAL_BASE_URL` | — | ✅ | — | Infisical API URL. |
| `INFISICAL_SERVICE_TOKEN` | — | ✅ | — | Service token with read access to signing secret. |
| `INFISICAL_PROJECT_ID` | — | ✅ | — | Workspace / project identifier. |
| `INFISICAL_ENVIRONMENT` | — | ✅ | — | Environment slug (dev/staging/prod). |
| `INFISICAL_SECRET_PATH` | — | ✅ | — | Secret path (e.g., `/backend`). |
| `INFISICAL_SIGNING_SECRET_NAME` | — | ✅ | — | Secret name containing signing key material. |
| `INFISICAL_CA_BUNDLE_PATH` | — | Optional | — | Custom CA bundle for self-hosted Infisical. |
| `INFISICAL_CACHE_TTL_SECONDS` | — | Optional | — | Local cache TTL for secrets. |
| `AWS_REGION` | — | — | ✅ | AWS region for Secrets Manager. |
| `AWS_PROFILE` | — | — | Optional | Named profile for CLI/backend (alternatively static keys or IMDS). |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_SESSION_TOKEN` | — | — | Optional | Static credentials when not using profile/IMDS. |
| `AWS_SM_SIGNING_SECRET_ARN` | — | — | ✅ | ARN/name of Secrets Manager secret storing the HMAC value. |
| `AWS_SM_CACHE_TTL_SECONDS` | — | — | Optional | Local cache TTL for AWS secrets. |
| `AZURE_KEY_VAULT_URL` | — | — | ✅ | Key Vault URL (https://...vault.azure.net). |
| `AZURE_KV_SIGNING_SECRET_NAME` | — | — | ✅ | Secret name storing HMAC value. |
| `AZURE_TENANT_ID` | — | — | Optional | Tenant for service principal auth. |
| `AZURE_CLIENT_ID` / `AZURE_CLIENT_SECRET` | — | — | Optional | Service principal credentials. |
| `AZURE_MANAGED_IDENTITY_CLIENT_ID` | — | — | Optional | User-assigned managed identity client ID. |
| `AZURE_KV_CACHE_TTL_SECONDS` | — | — | Optional | Local cache TTL for Azure secrets. |

## 3. Operational Runbooks

### 3.1 Vault Dev

1. Run `make vault-up`. Script enables Transit and prints env exports.  
2. Update `.env.local`/`.env.compose` with printed values.  
3. Boot FastAPI (`make api`) and run `make verify-vault` to smoke test CLI issuance.  
4. Tear down with `make vault-down`. Remember storage is memory-only and root token is static.

### 3.2 HCP Vault

1. Provision HCP Vault Development/Dedicated cluster.  
2. Enable Transit engine and create `auth-service` key (or configure CLI-specified name).  
3. Create a scoped token/AppRole with `transit:sign` + `transit:verify` capabilities.  
4. Run `starter_cli secrets onboard --provider vault_hcp` to capture env vars.  
5. Update backend/CLI env files and run `make verify-vault` (pointed at HCP address).  
6. Rotate Transit keys via Vault policies; update `VAULT_TRANSIT_KEY` if names change.

### 3.3 Infisical Cloud/Self-Host

1. Create a workspace + environment in Infisical; generate a service token scoped to the required path.  
2. Store a random signing secret (e.g., 32 bytes) at `INFISICAL_SIGNING_SECRET_NAME`.  
3. Run `starter_cli secrets onboard --provider infisical_cloud` (or `infisical_self_host`) to gather base URL, project ID, env slug, secret path, signing secret, and optional CA bundle.  
4. Command performs a live probe of `/api/v4/secrets/<name>` to validate access; investigate warnings if probe fails.  
5. The CLI enables `VAULT_VERIFY_ENABLED=true` automatically so service-account issuance requires signatures.  
6. Add env vars to backend + CLI, redeploy FastAPI.  
7. For self-host, deploy via Infisical’s Docker/K8s instructions and supply internal base URL + CA bundle path.

### 3.4 AWS Secrets Manager

1. Ensure an IAM role or user has `secretsmanager:GetSecretValue` and `secretsmanager:DescribeSecret` permissions for the signing secret ARN.
2. Store a high-entropy HMAC secret (e.g., 32+ bytes) in Secrets Manager; note its ARN.
3. Run `starter_cli secrets onboard --provider aws_sm` to capture region, secret ARN, cache TTL, and auth method (profile, static keys, or default credentials). The CLI probes AWS immediately to validate access.
4. CLI onboarding sets `VAULT_VERIFY_ENABLED=true` automatically so FastAPI enforces signatures.
5. Add the emitted env vars to `.env` / `.env.local` and redeploy FastAPI plus any CLI shells.
6. For compute environments with instance profiles/ECS task roles, omit profile/keys and rely on IMDS automatically.
7. Rotate the signing secret via Secrets Manager; FastAPI will pick up the new value once the cache TTL expires (default 60s).

## 4. Telemetry & Health Hooks

- Backend `SecretProviderHealth` now surfaces provider status; `/health/ready` will surface provider errors once the provider is initialized.
- Enable `ENABLE_SECRETS_PROVIDER_TELEMETRY=true` to log the active provider at startup (no payload data, just provider name).
- CLI onboarding can emit anonymous telemetry (`STARTER_CLI_TELEMETRY_OPT_IN=true`) summarizing provider selection success/failure in stdout logs.

## 5. Future Provider Checklists

### AWS Secrets Manager
- [x] Use Secrets Manager-stored HMAC secret with TTL caching.  
- [x] Implement AWS SDK client + CLI onboarding with validation.  
- [x] Document IAM policy requirements.  
- [ ] Optional: support KMS asymmetric keys for server-side signing.

### 3.5 Azure Key Vault

1. Create or reuse a Key Vault; ensure the operator identity has `get` permissions on secrets.
2. Store a strong random string secret named per `AZURE_KV_SIGNING_SECRET_NAME`.
3. Run `starter_cli secrets onboard --provider azure_kv` and choose auth method:  
   - **Service principal:** provide tenant ID, client ID, and client secret.  
   - **Managed identity:** supply the managed identity client ID (blank for system-assigned).  
   The CLI uses the Azure SDK to fetch the secret and confirms access.
4. CLI onboarding sets `VAULT_VERIFY_ENABLED=true` automatically so FastAPI enforces signatures.
5. Apply the emitted env vars to backend + CLI and redeploy.
6. Rotate the signing secret via Key Vault; FastAPI picks up the new value when the cache TTL expires.

### AWS Secrets Manager
- [x] Use Secrets Manager-stored HMAC secret with TTL caching.  
- [x] Implement AWS SDK client + CLI onboarding with validation.  
- [x] Document IAM policy requirements.  
- [ ] Optional: support KMS asymmetric keys for server-side signing.

### Azure Key Vault
- [x] Use Key Vault secrets as the signing source with TTL cache.  
- [x] Support service principal + managed identity auth in CLI onboarding.  
- [x] Document RBAC requirements.  
- [ ] Optional: support Key Vault Keys (RSA/ECDSA) for asymmetric signing.

---

For questions ping #proj-secrets-provider or open issues under BE-007. Update this document whenever a provider workflow or default changes.***
