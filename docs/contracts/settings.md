# Settings Contract

> No legacy aliases; canonical only.

## Source of truth

This document is the public-facing environment variable contract for operators. The canonical
source of truth for API-service settings is `docs/contracts/settings.schema.json`. This file is
generated from the backend settings model and must be updated first; this document summarizes
and organizes that contract for human readers and cross-service operators.

## Canonical envs

These names are the stack-wide canonical knobs referenced across services:

- `API_BASE_URL` -- Backend base URL for BFF and tooling.
- `APP_PUBLIC_URL` -- Public site URL used for SEO, links, and callbacks.
- `ENABLE_BILLING` -- Backend billing feature flag; UI reads `/health/features`.
- `GCP_PROJECT_ID` -- Default GCP project scope for storage and Secret Manager fallback.
- `LOG_ROOT` -- Root directory for logs (API + console + web dev logs).
- `LOGGING_DATADOG_API_KEY` / `LOGGING_DATADOG_SITE` -- Datadog logging config.
- `SIGNUP_ACCESS_POLICY` -- `public` | `invite_only` | `approval`.
- `REDIS_URL` -- Primary Redis connection string.

## Required vs optional

The backend schema does not explicitly mark required settings. Use these rules:

- **Optional (default)** -- Any setting with a schema default is optional; the default applies when unset.
- **No default** -- Treat as required **when the associated feature is enabled** or in production.

Minimum production-critical settings (operator baseline):

- API service: `APP_PUBLIC_URL`, `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `OPENAI_API_KEY`.
- Web app: `API_BASE_URL`, `APP_PUBLIC_URL`.

## Defaults

Defaults are defined in `docs/contracts/settings.schema.json` (API service) and in
service `.env.example` templates for web/console. Use the templates for local development; do not
ship their placeholder secrets to production.

## Per-service notes

- **API service (FastAPI)**: Configures runtime behavior via `docs/contracts/settings.schema.json`.
  Feature toggles (`ENABLE_BILLING`, `ENABLE_BILLING_STREAM`, etc.) gate backend endpoints and
  downstream UI visibility through `/health/features`.
- **Web app (Next.js)**: Reads `API_BASE_URL` server-side; public/client-exposed values must be
  prefixed with `NEXT_PUBLIC_` (e.g., `NEXT_PUBLIC_AGENT_API_MOCK`). Billing UI gates are derived
  from `/api/health/features` and must not use frontend env flags.
- **Starter Console**: Emits canonical backend envs and uses console-specific logging envs
  (`CONSOLE_*`) for its own runtime. Avoid duplicating backend knobs.
- **Ops/Infra**: Terraform and collector configs consume the canonical names (e.g., `API_BASE_URL`,
  `LOGGING_DATADOG_*`, `GCP_PROJECT_ID`).
- **Tests**: Playwright and smoke harnesses include test-only envs; keep these isolated from
  production templates.

## Security classification

All settings are classified into one of three groups:

- **Public** -- Safe to expose to browsers (e.g., `NEXT_PUBLIC_*`, `APP_PUBLIC_URL`).
- **Internal** -- Non-secret operational config (URLs, toggles, limits, timeouts).
- **Secret** -- Credentials and sensitive material (keys, tokens, passwords, peppers, encryption keys).

**Rule of thumb:** If the name includes `SECRET`, `TOKEN`, `PASSWORD`, `API_KEY`, `PEPPER`,
`ENCRYPTION_KEY`, `ACCESS_KEY`, or is a credential-bearing URL like `DATABASE_URL`/`REDIS_URL`,
classify it as **Secret**.

## Full listing (canonical)

The table below is the consolidated, canonical list of environment variables used across the stack.
Defaults are pulled from `settings.schema.json` when available. "No default" indicates the value
must be supplied when that feature is enabled.

| Variable | Required? | Default | Classification | Purpose |
| --- | --- | --- | --- | --- |

| `ACCESS_TOKEN_EXPIRE_MINUTES` | no default |  | secret | Access token lifetime in minutes. |
| `ACTIVITY_EVENTS_CLEANUP_BATCH` | optional (default) | 10000 | internal | Batch size for activity event cleanup jobs |
| `ACTIVITY_EVENTS_CLEANUP_SLEEP_MS` | optional (default) | 0 | internal | Sleep time between activity cleanup batches (milliseconds) |
| `ACTIVITY_EVENTS_REDIS_URL` | optional (default) | null | internal | Redis URL for activity event streaming (defaults to `REDIS_URL`) |
| `ACTIVITY_EVENTS_TTL_DAYS` | optional (default) | 365 | internal | Retention period for activity events |
| `ACTIVITY_STREAM_MAX_LENGTH` | optional (default) | 2048 | internal | Maximum length of Redis stream for activity events |
| `ACTIVITY_STREAM_TTL_SECONDS` | optional (default) | 86400 | internal | TTL for activity stream keys |
| `AGENT_ALLOW_INSECURE_COOKIES` | no default |  | internal | Allow insecure cookies in Next.js (dev/demo). / If set to `true`, disables the `secure` flag on cookies even when `NODE_ENV` is production. |
| `AGENT_FORCE_SECURE_COOKIES` | no default |  | internal | Force secure cookies in Next.js. / If set to `true`, forces the `secure` flag on cookies even in non-production environments. |
| `AGENT_MODEL_CODE` | optional (default) | null | internal | Override model for code assistant agent |
| `AGENT_MODEL_DATA` | optional (default) | null | internal | Override model for data analyst agent |
| `AGENT_MODEL_DEFAULT` | optional (default) | "gpt-5.1" | internal | Default model for agents |
| `AGENT_MODEL_TRIAGE` | optional (default) | null | internal | Override model for triage agent |
| `ALLOW_ANON_FRONTEND_LOGS` | optional (default) | false | internal | Allow anonymous frontend log ingestion / Toggles anonymous frontend log ingestion. |
| `ALLOW_OPENAI_CONVERSATION_UUID_FALLBACK` | no default |  | internal | Policy flag for agent runtime conversation ID handling |
| `ALLOW_SIGNUP_TRIAL_OVERRIDE` | no default |  | internal | Allow callers to request specific trial periods during signup / Allow clients to request custom trial lengths. |
| `ALLOWED_HEADERS` | no default |  | internal | CORS allowed headers / Comma-separated list of allowed HTTP headers. |
| `ALLOWED_HOSTS` | no default |  | internal | Comma-separated list of allowed hostnames. / Trusted hosts for middleware / ... |
| `ALLOWED_METHODS` | no default |  | internal | CORS allowed methods / Comma-separated list of allowed HTTP methods. |
| `ALLOWED_ORIGINS` | no default |  | internal | CORS allowed origins / Comma-separated list of allowed CORS origins. / ... |
| `ANTHROPIC_API_KEY` | no default |  | secret | API key for Anthropic models / API key for Anthropic models. |
| `API_BASE_URL` | no default |  | internal | Base URL of the backend API. / Server-side fallback URL for the backend API. / ... |
| `APP_DESCRIPTION` | no default |  | internal | API service description / Application description for docs/metadata. |
| `APP_NAME` | no default |  | internal | API service name / Application display name. |
| `APP_PUBLIC_URL` | optional (default) | "http://localhost:3000" | public | Base URL for generating public links / Public base URL of the frontend application. / ... |
| `APP_VERSION` | no default |  | internal | API service version / Application version string. |
| `AUTH_AUDIENCE` | no default |  | internal | Expected audience claim in JWTs. / JWT audience(s). / ... |
| `AUTH_CACHE_REDIS_URL` | optional (default) | null | internal | Redis URL for auth caching (defaults to `REDIS_URL`) / Redis URL for auth/session caching. / ... |
| `AUTH_CLI_DEV_AUTH_MODE` | no default |  | internal | Development auth mode override (e.g. `demo`). |
| `AUTH_CLI_OUTPUT` | no default |  | internal | Default output format for auth CLI commands. |
| `AUTH_DUAL_SIGNING_ENABLED` | no default |  | internal | Toggles dual signing for key rotation support. |
| `AUTH_EMAIL_VERIFICATION_TOKEN_PEPPER` | optional (default) | "local-email-verify-pepper" | secret | Pepper for hashing email verification tokens / Pepper for email verification tokens. |
| `AUTH_IP_LOCKOUT_DURATION_MINUTES` | optional (default) | 10 | internal | Duration IP is blocked after threshold breach / Duration of IP lockout in minutes. |
| `AUTH_IP_LOCKOUT_THRESHOLD` | optional (default) | 50 | internal | Failed attempts before IP lockout. / Max failed logins per IP/subnet per window / ... |
| `AUTH_IP_LOCKOUT_WINDOW_MINUTES` | optional (default) | 10 | internal | Rolling window for IP throttling / Window for counting IP failures in minutes. |
| `AUTH_JWKS_CACHE_SECONDS` | optional (default) | 300 | internal | Cache duration for JWKS / Cache duration for JWKS. |
| `AUTH_JWKS_ETAG_SALT` | optional (default) | "local-jwks-salt" | secret | Salt used for JWKS ETag generation. / Salt for JWKS ETag generation / ... |
| `AUTH_JWKS_MAX_AGE_SECONDS` | optional (default) | 300 | internal | `Cache-Control` max-age for JWKS / Cache duration for JWKS endpoints. / ... |
| `AUTH_KEY_SECRET_NAME` | optional (default) | null | secret | Name of secret in secret manager storing keyset / Secret Manager key/path/name for the Ed25519 keyset JSON. / ... |
| `AUTH_KEY_STORAGE_BACKEND` | optional (default) | "file" | internal | Key storage backend type (`file` or `secret-manager`). / Storage backend for auth keys (`file` or `secret-manager`). / ... |
| `AUTH_KEY_STORAGE_PATH` | optional (default) | "var/keys/keyset.json" | internal | File path for authentication key storage during tests. / File path for auth keys when backend is `file`. / ... |
| `AUTH_KEY_STORAGE_PROVIDER` | optional (default) | null | internal | Provider for secret-manager key storage. / Specifies which provider is used for key storage. / ... |
| `AUTH_LOCKOUT_DURATION_MINUTES` | optional (default) | 60.0 | internal | Duration of user lockout in minutes. / Unlock window for locked user accounts / ... |
| `AUTH_LOCKOUT_THRESHOLD` | optional (default) | 5 | internal | Failed attempts before user lockout / Failed login attempts before user lockout / ... |
| `AUTH_LOCKOUT_WINDOW_MINUTES` | optional (default) | 60.0 | internal | Rolling window for user lockout calculation / Window for counting user failures in minutes. |
| `AUTH_PASSWORD_HISTORY_COUNT` | optional (default) | 5 | secret | Number of past passwords to retain / Number of previous passwords to remember. |
| `AUTH_PASSWORD_PEPPER` | optional (default) | "local-dev-password-pepper" | secret | Pepper for password hashing / Secret pepper for password hashing. / ... |
| `AUTH_PASSWORD_RESET_TOKEN_PEPPER` | optional (default) | "local-reset-token-pepper" | secret | Pepper for hashing password reset tokens / Pepper for password reset tokens. |
| `AUTH_REFRESH_TOKEN_PEPPER` | optional (default) | "local-dev-refresh-pepper" | secret | Pepper for hashing refresh tokens / Secret pepper for refresh token hashing. / ... |
| `AUTH_REFRESH_TOKEN_TTL_MINUTES` | optional (default) | 43200 | secret | Lifetime of refresh tokens / Refresh token lifetime in minutes. |
| `AUTH_SESSION_ENCRYPTION_KEY` | optional (default) | null | secret | Key for encrypting session IP metadata / Key for encrypting session data. |
| `AUTH_SESSION_IP_HASH_SALT` | optional (default) | null | secret | Salt for hashing session IP addresses. / Salt for session IP hashing (defaults to SECRET_KEY) |
| `AUTO_CREATE_VECTOR_STORE_FOR_FILE_SEARCH` | no default |  | internal | Automatically create vector stores for file search in tests. / Automatically create vector stores for tenants / ... |
| `AUTO_PURGE_EXPIRED_VECTOR_STORES` | no default |  | internal | Delete expired vector stores remotely |
| `AUTO_RUN_MIGRATIONS` | no default |  | internal | Automatically run DB migrations on startup. / Controls whether migrations run automatically during smoke tests. / ... |
| `AWS_ACCESS_KEY_ID` | optional (default) | null | secret | AWS Access Key / AWS Access Key ID. |
| `AWS_PROFILE` | optional (default) | null | internal | AWS CLI profile name |
| `AWS_REGION` | optional (default) | null | internal | AWS Region / AWS Region. / AWS region for resources. |
| `AWS_SECRET_ACCESS_KEY` | optional (default) | null | secret | AWS Secret Key / AWS Secret Access Key. |
| `AWS_SESSION_TOKEN` | optional (default) | null | secret | AWS Session Token |
| `AWS_SM_CACHE_TTL_SECONDS` | optional (default) | 60 | internal | Cache TTL for AWS Secrets Manager / Cache TTL for AWS Secrets Manager. |
| `AWS_SM_SIGNING_SECRET_ARN` | optional (default) | null | secret | ARN of signing secret in AWS Secrets Manager / ARN of the signing secret in AWS SM. / ... |
| `AZURE_BLOB_ACCOUNT_URL` | no default |  | internal | Azure Blob Storage account URL / Azure Blob Storage account URL. |
| `AZURE_BLOB_CONNECTION_STRING` | no default |  | internal | Azure Blob Storage connection string / Azure Blob Storage connection string. |
| `AZURE_BLOB_CONTAINER` | no default |  | internal | Azure Blob container name / Azure Blob Storage container name. / ... |
| `AZURE_CLIENT_ID` | optional (default) | null | internal | Azure Client ID |
| `AZURE_CLIENT_SECRET` | optional (default) | null | secret | Azure Client Secret |
| `AZURE_KEY_VAULT_URL` | optional (default) | null | internal | Azure Key Vault URL |
| `AZURE_KV_CACHE_TTL_SECONDS` | optional (default) | 60 | internal | Cache TTL for Azure Key Vault / Cache TTL for Azure Key Vault secrets. |
| `AZURE_KV_SIGNING_SECRET_NAME` | optional (default) | null | secret | Name of signing secret in Key Vault / Name of the signing secret in Key Vault. / ... |
| `AZURE_MANAGED_IDENTITY_CLIENT_ID` | optional (default) | null | internal | Azure Managed Identity Client ID / Managed Identity Client ID for Azure. |
| `AZURE_TENANT_ID` | optional (default) | null | internal | Azure Tenant ID |
| `BILLING_EVENTS_REDIS_URL` | optional (default) | null | internal | Redis URL for billing event streams. / Redis URL for billing events (defaults to `REDIS_URL`) / ... |
| `BILLING_RETRY_DEPLOYMENT_MODE` | optional (default) | "inline" | internal | Deployment mode for Stripe retry worker / Deployment mode for billing retry worker (`inline` or `dedicated`). |
| `BILLING_STREAM_CONCURRENT_LIMIT` | optional (default) | 3 | internal | Concurrent billing stream limit per tenant / Max concurrent billing streams. |
| `BILLING_STREAM_RATE_LIMIT_PER_MINUTE` | optional (default) | 20 | internal | Billing stream rate limit per tenant / Rate limit for billing streams per minute. |
| `CHAT_RATE_LIMIT_PER_MINUTE` | optional (default) | 60 | internal | Chat completion rate limit / Rate limit for chat completions per minute. |
| `CHAT_STREAM_CONCURRENT_LIMIT` | optional (default) | 5 | internal | Concurrent chat stream limit / Max concurrent chat streams. |
| `CHAT_STREAM_RATE_LIMIT_PER_MINUTE` | optional (default) | 30 | internal | Chat stream rate limit / Rate limit for chat streams per minute. |
| `CI` | no default |  | internal | Indicates if the tests are running in a CI environment. |
| `COMPOSE_FILE` | no default |  | internal | Path to docker-compose file. |
| `COMPOSE_PROJECT_NAME` | no default |  | internal | Docker compose project name. |
| `CONSOLE_LOG_LEVEL` | no default |  | internal | Logging level for console. |
| `CONSOLE_LOGGING_DUPLEX_ERROR_FILE` | no default |  | internal | Enable duplex error logging for console. |
| `CONSOLE_LOGGING_FILE_BACKUPS` | no default |  | internal | Number of console log backups to keep. |
| `CONSOLE_LOGGING_FILE_MAX_MB` | no default |  | internal | Max size of console log file in MB. |
| `CONSOLE_LOGGING_FILE_PATH` | no default |  | internal | Path to console log file. |
| `CONSOLE_LOGGING_MAX_DAYS` | no default |  | internal | Max days to keep console logs. |
| `CONSOLE_LOGGING_OTLP_ENDPOINT` | no default |  | internal | OTLP endpoint for console logs. |
| `CONSOLE_LOGGING_OTLP_HEADERS` | no default |  | internal | OTLP headers for console logs. |
| `CONSOLE_LOGGING_SINKS` | no default |  | internal | Logging sinks for console (`file`, `stdout`, etc). |
| `CONSOLE_SERVICE_NAME` | no default |  | internal | Service name for console telemetry. |
| `CONSOLE_TEXTUAL_LOG_LEVEL` | no default |  | internal | Log level for Textual framework logs. |
| `CONTACT_EMAIL_EMAIL_RATE_LIMIT_PER_HOUR` | optional (default) | 3 | internal | Contact form limit per email address |
| `CONTACT_EMAIL_IP_RATE_LIMIT_PER_HOUR` | optional (default) | 20 | internal | Contact form limit per IP |
| `CONTACT_EMAIL_SUBJECT_PREFIX` | optional (default) | "[Contact]" | internal | Prefix for contact emails |
| `CONTACT_EMAIL_TEMPLATE_ID` | optional (default) | null | internal | Resend template ID for contact emails |
| `CONTACT_EMAIL_TO` | no default |  | internal | Recipients for contact form submissions |
| `CONTAINER_ALLOWED_MEMORY_TIERS` | no default |  | internal | Allowed memory tiers for code interpreter |
| `CONTAINER_DEFAULT_AUTO_MEMORY` | no default |  | internal | Default memory for code interpreter containers |
| `CONTAINER_FALLBACK_TO_AUTO_ON_MISSING_BINDING` | no default |  | internal | Fallback behavior for container bindings |
| `CONTAINER_MAX_CONTAINERS_PER_TENANT` | no default |  | internal | Container limit per tenant |
| `DATABASE_ECHO` | no default |  | internal | Controls SQLAlchemy SQL logging to stdout. / Enable SQLAlchemy echo / ... |
| `DATABASE_HEALTH_TIMEOUT` | no default |  | internal | DB health check timeout / Database health check timeout in seconds. |
| `DATABASE_MAX_OVERFLOW` | no default |  | internal | Database pool max overflow. / SQLAlchemy pool overflow / ... |
| `DATABASE_POOL_RECYCLE` | no default |  | internal | Database pool recycle time in seconds. / SQLAlchemy pool recycle time / ... |
| `DATABASE_POOL_SIZE` | no default |  | internal | Database pool size. / SQLAlchemy pool size / ... |
| `DATABASE_POOL_TIMEOUT` | no default |  | internal | Database pool timeout in seconds. / SQLAlchemy pool timeout / ... |
| `DATABASE_URL` | optional (default) | null | secret | Configures the database connection URL for Alembic migrations. / Connection string for the primary database. / ... |
| `DEBUG` | no default |  | internal | Enable debug mode / Enable debug mode. / ... |
| `DEV_USER_EMAIL` | no default |  | internal | Default email for manual test login. |
| `DEV_USER_PASSWORD` | no default |  | secret | Default password for manual test login. |
| `DISABLE_PROVIDER_CONVERSATION_CREATION` | no default |  | internal | Disables upstream provider conversation syncing. / Policy flag to disable provider conversation usage |
| `EMAIL_VERIFICATION_EMAIL_RATE_LIMIT_PER_HOUR` | optional (default) | 3 | internal | Verification email limit per account / Verification emails per account per hour. |
| `EMAIL_VERIFICATION_IP_RATE_LIMIT_PER_HOUR` | optional (default) | 10 | internal | Verification email limit per IP / Verification emails per IP per hour. |
| `EMAIL_VERIFICATION_TOKEN_TTL_MINUTES` | optional (default) | 60 | secret | Email verification token lifetime. / Verification token lifetime / ... |
| `ENABLE_ACTIVITY_STREAM` | optional (default) | false | internal | Enable activity streaming / Toggles the user activity event stream. |
| `ENABLE_BILLING` | no default |  | internal | Backend feature flag to enable/disable billing logic. / Enable billing features / ... |
| `ENABLE_BILLING_RETRY_WORKER` | optional (default) | true | internal | Enable Stripe dispatch retry worker / Enable billing retry worker. / ... |
| `ENABLE_BILLING_STREAM` | optional (default) | false | internal | Enable billing event streaming / Toggles the SSE billing event stream. / ... |
| `ENABLE_BILLING_STREAM_REPLAY` | optional (default) | true | internal | Replay billing stream events on startup. / Replay billing stream events on startup |
| `ENABLE_FRONTEND_LOG_INGEST` | optional (default) | false | internal | Enable frontend log ingestion endpoint / Toggles the frontend log ingestion endpoint. / ... |
| `ENABLE_OTEL_COLLECTOR` | no default |  | internal | Enable bundled OpenTelemetry Collector. |
| `ENABLE_SECRETS_PROVIDER_TELEMETRY` | optional (default) | false | secret | Emit secrets provider telemetry / Enable telemetry for secrets provider. |
| `ENABLE_SLACK_STATUS_NOTIFICATIONS` | optional (default) | false | internal | Enable Slack notifications for status incidents. / Enable Slack status alerts |
| `ENABLE_USAGE_GUARDRAILS` | optional (default) | false | internal | Enable usage guardrails. / Toggles usage quota enforcement. / ... |
| `ENABLE_VECTOR_LIMIT_ENTITLEMENTS` | no default |  | internal | Add vector storage limits to entitlements. |
| `ENABLE_VECTOR_STORE_SYNC_WORKER` | no default |  | internal | Enable vector store sync background worker / Enable vector store sync worker (tests). |
| `ENVIRONMENT` | optional (default) | "development" | internal | Deployment environment (e.g., `production`, `development`). / Deployment environment label. / ... |
| `EXPECT_API_DOWN` | no default |  | internal | Suppress API probe failure in doctor. |
| `EXPECT_DB_DOWN` | no default |  | internal | Suppress Database probe failure in doctor. |
| `EXPECT_FRONTEND_DOWN` | no default |  | internal | Suppress Frontend probe failure in doctor. |
| `EXPECT_REDIS_DOWN` | no default |  | internal | Suppress Redis probe failure in doctor. |
| `FILE_SEARCH_LOCAL_FILE` | no default |  | internal | Local file path for file search upload test. |
| `FORCE_PROVIDER_SESSION_REBIND` | no default |  | internal | Policy flag to force provider session rebinding |
| `FRONTEND_LOG_SHARED_SECRET` | optional (default) | null | secret | Shared secret for anonymous frontend logs / Shared secret for signing frontend logs. |
| `GCP_PROJECT_ID` | no default |  | internal | Default GCP project ID for storage and Secret Manager fallback when `GCP_SM_PROJECT_ID` is unset. |
| `GCP_SM_CACHE_TTL_SECONDS` | optional (default) | 60 | internal | Cache TTL for GCP Secret Manager. |
| `GCP_SM_PROJECT_ID` | optional (default) | null | internal | GCP Project ID for Secret Manager. / GCP Project ID. / ... |
| `GCP_SM_SIGNING_SECRET_NAME` | optional (default) | null | secret | GCP Secret Manager secret name containing the signing secret. / Name of the signing secret in GCP Secret Manager. / ... |
| `GCS_BUCKET` | no default |  | internal | GCS bucket name for object storage. / Google Cloud Storage bucket / ... |
| `GCS_CREDENTIALS_JSON` | no default |  | secret | GCS Credentials JSON content / Inline GCS credentials JSON. |
| `GCS_CREDENTIALS_PATH` | no default |  | secret | Path to GCS credentials file / Path to GCS credentials JSON file. |
| `GCS_SIGNING_EMAIL` | no default |  | internal | GCS Service Account Email for signing / Service account email for signed URLs. |
| `GCS_UNIFORM_ACCESS` | no default |  | internal | Use Uniform Bucket Level Access for GCS. / Use uniform bucket-level access |
| `GEMINI_API_KEY` | no default |  | secret | API key for Google Gemini. / Google Gemini API key |
| `GEOIP_CACHE_MAX_ENTRIES` | optional (default) | 4096 | internal | Max entries in GeoIP cache / Max entries in GeoIP cache. |
| `GEOIP_CACHE_TTL_SECONDS` | optional (default) | 900.0 | internal | GeoIP cache TTL / TTL for GeoIP cache. |
| `GEOIP_HTTP_TIMEOUT_SECONDS` | optional (default) | 2.0 | internal | HTTP timeout for GeoIP lookups. / Timeout for GeoIP APIs / ... |
| `GEOIP_IP2LOCATION_API_KEY` | optional (default) | null | secret | API Key for IP2Location / API key for IP2Location. |
| `GEOIP_IP2LOCATION_DB_PATH` | optional (default) | null | internal | Path to IP2Location DB / Path to IP2Location database file. |
| `GEOIP_IPINFO_TOKEN` | optional (default) | null | secret | API token for IPinfo. / Token for IPinfo / ... |
| `GEOIP_MAXMIND_DB_PATH` | optional (default) | null | internal | Path to MaxMind DB / Path to MaxMind database file. |
| `GEOIP_MAXMIND_LICENSE_KEY` | optional (default) | null | internal | License key for MaxMind / License key for MaxMind. |
| `GEOIP_PROVIDER` | optional (default) | "none" | internal | GeoIP provider name. / GeoIP provider selection / ... |
| `HOST` | no default |  | internal | Server host binding |
| `IMAGE_ALLOWED_FORMATS` | no default |  | internal | Allowed image formats |
| `IMAGE_DEFAULT_BACKGROUND` | no default |  | internal | Default image background (auto, opaque, transparent). / Default image background setting / ... |
| `IMAGE_DEFAULT_COMPRESSION` | no default |  | internal | Default image compression level / Default image compression level (0-100). |
| `IMAGE_DEFAULT_FORMAT` | no default |  | internal | Default image format / Default image format (png, jpeg, webp). |
| `IMAGE_DEFAULT_QUALITY` | no default |  | internal | Default image quality / Default image quality (auto, low, medium, high). |
| `IMAGE_DEFAULT_SIZE` | no default |  | internal | Default image size / Default image size. |
| `IMAGE_MAX_PARTIAL_IMAGES` | no default |  | internal | Max partial images for streaming / Max partial images to stream. |
| `IMAGE_OUTPUT_MAX_MB` | no default |  | internal | Max decoded image size in MB. / Max size for image outputs / ... |
| `INFISICAL_BASE_URL` | optional (default) | null | internal | Base URL for Infisical. / Infisical API URL / ... |
| `INFISICAL_CA_BUNDLE_PATH` | optional (default) | null | internal | Path to CA bundle for Infisical / Path to CA bundle for Infisical. |
| `INFISICAL_CACHE_TTL_SECONDS` | optional (default) | 60 | internal | Cache TTL for Infisical secrets / Cache TTL for Infisical secrets. |
| `INFISICAL_ENVIRONMENT` | optional (default) | null | internal | Infisical environment slug / Infisical environment slug. |
| `INFISICAL_PROJECT_ID` | optional (default) | null | internal | Infisical project ID / Infisical project/workspace ID. |
| `INFISICAL_SECRET_PATH` | optional (default) | null | secret | Path to secrets in Infisical / Path within Infisical workspace. |
| `INFISICAL_SERVICE_TOKEN` | optional (default) | null | secret | Infisical service token / Infisical service token. |
| `INFISICAL_SIGNING_SECRET_NAME` | optional (default) | "auth-service-signing-secret" | secret | Name of signing secret in Infisical / Name of the signing secret in Infisical. |
| `JWT_ALGORITHM` | no default |  | internal | Algorithm for JWT signing / Algorithm used for JWT signing. |
| `LOG_LEVEL` | no default |  | internal | Application logging level / Global logging level. |
| `LOG_ROOT` | optional (default) | null | internal | Base directory for logs / Defines the root directory where dated log files are written. / ... |
| `LOGGING_DATADOG_API_KEY` | optional (default) | null | secret | Datadog API key / Datadog API key for log ingestion. / ... |
| `LOGGING_DATADOG_SITE` | optional (default) | "datadoghq.com" | internal | Datadog site / Datadog site for logs. |
| `LOGGING_DUPLEX_ERROR_FILE` | optional (default) | false | internal | Enable duplex error logging. / If true, writes errors to a separate file even if stdout is enabled. / ... |
| `LOGGING_FILE_BACKUPS` | optional (default) | 5 | internal | Number of log file backups / Number of rotated log files to keep. / ... |
| `LOGGING_FILE_MAX_MB` | optional (default) | 10 | internal | Max size of log files / Max size of a log file before rotation. / ... |
| `LOGGING_FILE_PATH` | optional (default) | "var/log/api-service.log" | internal | Path for log file / Specific path for a single log file (overrides daily rotation). / ... |
| `LOGGING_MAX_DAYS` | optional (default) | 0 | internal | Max age in days for daily log directories. / Max days to keep logs / ... |
| `LOGGING_OTLP_ENDPOINT` | optional (default) | null | internal | HTTP endpoint for OTLP log export. / OTLP endpoint for logs. / ... |
| `LOGGING_OTLP_HEADERS` | optional (default) | null | internal | Additional headers for OTLP export. / OTLP logging headers / ... |
| `LOGGING_SINKS` | optional (default) | "stdout" | internal | Comma-separated list of active logging destinations. / Enabled logging sinks. / ... |
| `MANUAL_ACCESS_TOKEN` | no default |  | secret | Pre-supplied token for manual tests. |
| `MANUAL_AGENT` | no default |  | internal | Agent key override for manual tests. |
| `MANUAL_MESSAGE` | no default |  | internal | Custom prompt message for manual tests. |
| `MANUAL_RECORD_STREAM_TO` | no default |  | internal | File path to record manual test SSE stream output. |
| `MANUAL_TENANT_ID` | no default |  | internal | Pre-supplied tenant ID for manual tests. |
| `MANUAL_TIMEOUT` | no default |  | internal | HTTP timeout for manual tests (seconds). |
| `MCP_TOOLS` | no default |  | internal | Hosted MCP tool configuration / JSON configuration for Model Context Protocol tools. |
| `MFA_CHALLENGE_TTL_MINUTES` | optional (default) | 5 | internal | TTL for MFA challenges |
| `MFA_VERIFY_RATE_LIMIT_PER_HOUR` | optional (default) | 10 | internal | MFA verification attempt limit |
| `MINIO_ACCESS_KEY` | no default |  | secret | MinIO Access Key / MinIO access key. |
| `MINIO_ENDPOINT` | no default |  | internal | MinIO Endpoint URL / MinIO endpoint URL. |
| `MINIO_REGION` | no default |  | internal | MinIO Region / MinIO region. |
| `MINIO_SECRET_KEY` | no default |  | secret | MinIO Secret Key / MinIO secret key. |
| `MINIO_SECURE` | no default |  | internal | Use SSL for MinIO / Use HTTPS for MinIO. / ... |
| `NEXT_PUBLIC_AGENT_API_MOCK` | no default |  | public | Client-side flag to enable mock API mode. |
| `NEXT_PUBLIC_LOG_LEVEL` | no default |  | public | Frontend log level. / Minimum log severity level to emit. |
| `NEXT_PUBLIC_LOG_SINK` | no default |  | public | Destination for log events. / Frontend log sink. |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | no default |  | public | Enables Stripe Elements for collecting payment methods. / Public key for Stripe Elements integration. |
| `NODE_ENV` | no default |  | internal | Determines environment mode. / Used to disable test fixture routes in production environments. / ... |
| `OPENAI_AGENTS_DISABLE_TRACING` | no default |  | internal | Disable OpenAI agents tracing (tests). / Disables internal tracing in the OpenAI Agents SDK. |
| `OPENAI_API_KEY` | no default |  | secret | API key for OpenAI. / API key for OpenAI services. / ... |
| `OTEL_EXPORTER_SENTRY_AUTH_HEADER` | no default |  | internal | Auth header for Sentry OTel exporter. |
| `OTEL_EXPORTER_SENTRY_ENDPOINT` | no default |  | internal | Sentry OTLP endpoint. |
| `OTEL_EXPORTER_SENTRY_HEADERS` | no default |  | internal | Extra headers for Sentry OTel exporter. |
| `PASSWORD_RESET_EMAIL_RATE_LIMIT_PER_HOUR` | optional (default) | 5 | secret | Password reset email limit per account / Password reset emails per account per hour. |
| `PASSWORD_RESET_IP_RATE_LIMIT_PER_HOUR` | optional (default) | 20 | secret | Password reset email limit per IP / Password reset emails per IP per hour. |
| `PASSWORD_RESET_TOKEN_TTL_MINUTES` | optional (default) | 30 | secret | Password reset token lifetime / Password reset token lifetime. |
| `PLAYWRIGHT_API_URL` | no default |  | internal | Primary override for the backend API URL when running seed fixtures. / The base URL for the backend API used during tests. |
| `PLAYWRIGHT_BASE_URL` | no default |  | internal | Base URL for Playwright tests. / The base URL for the frontend application (Real mode). |
| `PLAYWRIGHT_BILLING_EMAIL` | no default |  | internal | Email address used for billing plan change inputs in tests. |
| `PLAYWRIGHT_MOCK_BASE_URL` | no default |  | internal | The base URL for the frontend application (Mock mode). |
| `PLAYWRIGHT_OPERATOR_EMAIL` | no default |  | internal | Email address for the platform operator account. |
| `PLAYWRIGHT_OPERATOR_PASSWORD` | no default |  | secret | Password for the platform operator account. |
| `PLAYWRIGHT_OPERATOR_TENANT` | no default |  | internal | Tenant slug identifier for the operator organization. |
| `PLAYWRIGHT_REFRESH_STORAGE_STATE` | no default |  | internal | Forces authentication to refresh stored cookies/tokens. |
| `PLAYWRIGHT_SEED_FILE` | no default |  | internal | Path to the YAML specification file used for seeding data. |
| `PLAYWRIGHT_SEED_ON_START` | no default |  | internal | Triggers the database seed script before running tests. |
| `PLAYWRIGHT_SKIP_SEED` | no default |  | internal | Prevents the seed script from running. |
| `PLAYWRIGHT_SKIP_STORAGE_STATE` | no default |  | internal | Skips authentication/storage state generation. |
| `PLAYWRIGHT_SKIP_WEB_SERVER` | no default |  | internal | Skip starting the local web server. |
| `PLAYWRIGHT_TENANT_ADMIN_EMAIL` | no default |  | internal | Email address for the primary tenant admin account. / Email used for the mock user profile when `USE_API_MOCK` is active. |
| `PLAYWRIGHT_TENANT_ADMIN_PASSWORD` | no default |  | secret | Password for the primary tenant admin account. |
| `PLAYWRIGHT_TENANT_SLUG` | no default |  | internal | The tenant slug identifier for the primary test organization. |
| `PORT` | no default |  | internal | Fallback port if API URL is unset. / Port for the backend API. / ... |
| `POSTGRES_DB` | no default |  | internal | Local Postgres database name. / Used to validate that the `DATABASE_URL` matches the expected Postgres database name. / ... |
| `POSTGRES_PASSWORD` | no default |  | secret | Local Postgres password. |
| `POSTGRES_PORT` | no default |  | internal | Local Postgres port. |
| `POSTGRES_USER` | no default |  | internal | Local Postgres username. |
| `RATE_LIMIT_KEY_PREFIX` | optional (default) | "rate-limit" | internal | Redis key prefix for rate limiting. / Redis prefix for rate limiting |
| `RATE_LIMIT_REDIS_URL` | optional (default) | null | internal | Redis connection string for rate limiting. / Redis URL for rate limiting (defaults to `REDIS_URL`) / ... |
| `REDIS_URL` | no default |  | secret | Connection string for Redis. / Primary Redis connection string. / ... |
| `RELOAD` | no default |  | internal | Enable server reload |
| `REQUIRE_EMAIL_VERIFICATION` | optional (default) | true | internal | Enforce email verification / Require verified email for access. |
| `RESEND_API_KEY` | optional (default) | null | secret | API Key for Resend email delivery. / API key for Resend email service. / ... |
| `RESEND_BASE_URL` | optional (default) | "https://api.resend.com" | internal | Resend API Base URL / Resend API base URL. |
| `RESEND_DEFAULT_FROM` | optional (default) | null | internal | Default From address for Resend / Default From address for emails. / ... |
| `RESEND_EMAIL_ENABLED` | optional (default) | false | internal | Enable Resend for emails / Enable Resend email delivery. / ... |
| `RESEND_EMAIL_VERIFICATION_TEMPLATE_ID` | optional (default) | null | internal | Resend template for verification emails / Resend template ID for verification. |
| `RESEND_PASSWORD_RESET_TEMPLATE_ID` | optional (default) | null | secret | Resend template ID for password reset. / Resend template for password reset emails / ... |
| `RUN_EVENTS_CLEANUP_BATCH` | optional (default) | 10000 | internal | Batch size for run event cleanup |
| `RUN_EVENTS_CLEANUP_SLEEP_MS` | optional (default) | 0 | internal | Sleep time between run event cleanup batches |
| `RUN_EVENTS_TTL_DAYS` | optional (default) | 180 | internal | Retention period for run events |
| `S3_BUCKET` | no default |  | internal | S3 Bucket Name / S3 bucket name. / ... |
| `S3_ENDPOINT_URL` | no default |  | internal | Custom S3 Endpoint URL / Custom S3 endpoint URL. |
| `S3_FORCE_PATH_STYLE` | no default |  | internal | Force path-style addressing for S3 / Force path-style access for S3. |
| `S3_REGION` | no default |  | internal | AWS Region for S3 / S3 region. |
| `SECRET_KEY` | no default |  | secret | Flask/FastAPI session secret key (legacy support). / Main application secret key. / ... |
| `SECRETS_PROVIDER` | optional (default) | "vault_dev" | secret | Secrets provider backend / Specifies the active secrets backend. / ... |
| `SECURITY_TOKEN_REDIS_URL` | optional (default) | null | secret | Redis URL for security token storage (nonces, etc). / Redis URL for security tokens (defaults to `REDIS_URL`) / ... |
| `SHELL` | no default |  | internal | Specifies the shell executable to use within the virtual environment. |
| `SIGNUP_ACCESS_POLICY` | optional (default) | "invite_only" | internal | Controls user registration (`public`, `invite_only`, `approval`). / Signup access policy (`public`, `invite_only`, `approval`). / ... |
| `SIGNUP_CONCURRENT_REQUESTS_LIMIT` | optional (default) | 3 | internal | Concurrent signup requests per IP. / Max pending signup requests allowed per IP. / ... |
| `SIGNUP_DEFAULT_PLAN_CODE` | no default |  | internal | Default billing plan for new tenants / Default plan code for new signups. |
| `SIGNUP_DEFAULT_TRIAL_DAYS` | no default |  | internal | Default trial days for new tenants / Default trial days for new signups. |
| `SIGNUP_INVITE_RESERVATION_TTL_SECONDS` | optional (default) | 900 | internal | TTL for signup invite reservations |
| `SIGNUP_RATE_LIMIT_PER_DAY` | no default |  | internal | Global signup rate limit per day. |
| `SIGNUP_RATE_LIMIT_PER_DOMAIN_DAY` | optional (default) | 20 | internal | Signup limit per email domain / Signup rate limit per email domain per day. / ... |
| `SIGNUP_RATE_LIMIT_PER_EMAIL_DAY` | optional (default) | 3 | internal | Signup limit per email address / Signup rate limit per email address per day. / ... |
| `SIGNUP_RATE_LIMIT_PER_HOUR` | optional (default) | 20 | internal | Global signup rate limit per hour. / Signup limit per IP (hourly) / ... |
| `SIGNUP_RATE_LIMIT_PER_IP_DAY` | optional (default) | 100 | internal | Signup limit per IP (daily) / Signup rate limit per IP address per day. / ... |
| `SLACK_API_BASE_URL` | optional (default) | "https://slack.com/api" | internal | Slack API base URL |
| `SLACK_HTTP_TIMEOUT_SECONDS` | optional (default) | 5.0 | internal | Slack API timeout / Timeout for Slack API requests. |
| `SLACK_STATUS_BOT_TOKEN` | optional (default) | null | secret | Slack Bot Token / Slack bot token for status notifications. |
| `SLACK_STATUS_DEFAULT_CHANNELS` | no default |  | internal | Default Slack channels for notifications / Default Slack channels for status alerts. |
| `SLACK_STATUS_MAX_RETRIES` | optional (default) | 3 | internal | Max retries for Slack notifications / Max retries for Slack notifications. |
| `SLACK_STATUS_RATE_LIMIT_WINDOW_SECONDS` | optional (default) | 1.0 | internal | Rate limit window for Slack notifications / Rate limit window for Slack notifications. |
| `SLACK_STATUS_TENANT_CHANNEL_MAP` | no default |  | internal | Map of tenant IDs to Slack channels / Tenant-specific Slack channel overrides. |
| `SMOKE_BASE_URL` | no default |  | internal | Base URL for smoke tests. / Base URL for the API service during smoke tests. |
| `SMOKE_CONVERSATION_KEY` | no default |  | internal | Key for smoke test seed conversation. |
| `SMOKE_ENABLE_ACTIVITY_STREAM` | no default |  | internal | Enable activity stream smoke tests. |
| `SMOKE_ENABLE_AI` | no default |  | internal | Enable AI chat/workflow smoke tests. / Toggles AI features specifically for smoke tests. |
| `SMOKE_ENABLE_ASSETS` | no default |  | internal | Enable asset management smoke tests. |
| `SMOKE_ENABLE_AUTH_EXTENDED` | no default |  | internal | Enable extended auth (password change/reset) tests. |
| `SMOKE_ENABLE_AUTH_MFA` | no default |  | internal | Enable MFA flow smoke tests. |
| `SMOKE_ENABLE_AUTH_SIGNUP` | no default |  | internal | Enable signup flow smoke tests. |
| `SMOKE_ENABLE_AUTH_SSO` | no default |  | internal | Enable SSO flow smoke tests. |
| `SMOKE_ENABLE_BILLING` | no default |  | internal | Enable billing smoke tests. / Toggles billing features specifically for smoke tests. |
| `SMOKE_ENABLE_BILLING_STREAM` | no default |  | internal | Enable billing SSE stream smoke tests. |
| `SMOKE_ENABLE_CONTACT` | no default |  | internal | Enable contact form smoke tests. |
| `SMOKE_ENABLE_CONTAINERS` | no default |  | internal | Enable container management smoke tests. / Toggles container features specifically for smoke tests. |
| `SMOKE_ENABLE_OPENAI_FILES` | no default |  | internal | Enable OpenAI file proxy smoke tests. |
| `SMOKE_ENABLE_SERVICE_ACCOUNTS` | no default |  | internal | Enable service account smoke tests. |
| `SMOKE_ENABLE_STATUS_SUBSCRIPTIONS` | no default |  | internal | Enable status subscription smoke tests. |
| `SMOKE_ENABLE_VECTOR` | no default |  | internal | Enable vector store smoke tests. / Toggles vector features specifically for smoke tests. |
| `SMOKE_HTTP_TIMEOUT` | no default |  | internal | HTTP request timeout for smoke tests. |
| `SMOKE_MFA_EMAIL` | no default |  | internal | Email for MFA test user. |
| `SMOKE_OPENAI_FILE_ID` | no default |  | internal | Existing OpenAI file ID for download tests. |
| `SMOKE_OPERATOR_EMAIL` | no default |  | internal | Email for platform operator test user. |
| `SMOKE_PASSWORD_CHANGE_EMAIL` | no default |  | secret | Email for password change test user. |
| `SMOKE_PASSWORD_RESET_EMAIL` | no default |  | secret | Email for password reset test user. |
| `SMOKE_SSO_PROVIDER` | no default |  | internal | SSO provider key for smoke tests. |
| `SMOKE_TENANT_NAME` | no default |  | internal | Name for smoke test tenant. |
| `SMOKE_TENANT_SLUG` | no default |  | internal | Slug for smoke test tenant. |
| `SMOKE_UNVERIFIED_EMAIL` | no default |  | internal | Email for unverified test user. |
| `SMOKE_USE_STUB_PROVIDER` | no default |  | internal | Toggles the use of a stub provider during smoke tests. |
| `SMOKE_USER_EMAIL` | no default |  | internal | Admin email for smoke tests. |
| `SMOKE_USER_PASSWORD` | no default |  | secret | Password for smoke test users. |
| `SSO_<PROVIDER>_ALLOWED_DOMAINS` | no default |  | internal | Allowed email domains for SSO provider. |
| `SSO_<PROVIDER>_AUTO_PROVISION_POLICY` | no default |  | internal | Auto-provisioning policy for SSO provider. |
| `SSO_<PROVIDER>_CLIENT_ID` | no default |  | internal | Client ID for SSO provider. |
| `SSO_<PROVIDER>_CLIENT_SECRET` | no default |  | secret | Client Secret for SSO provider. |
| `SSO_<PROVIDER>_DEFAULT_ROLE` | no default |  | internal | Default role for auto-provisioned users. |
| `SSO_<PROVIDER>_DISCOVERY_URL` | no default |  | internal | OIDC Discovery URL for SSO provider. |
| `SSO_<PROVIDER>_ENABLED` | no default |  | internal | Enable SSO provider. |
| `SSO_<PROVIDER>_ID_TOKEN_ALGS` | no default |  | secret | Allowed ID token signing algorithms. |
| `SSO_<PROVIDER>_ISSUER_URL` | no default |  | internal | OIDC Issuer URL for SSO provider. |
| `SSO_<PROVIDER>_PKCE_REQUIRED` | no default |  | internal | Require PKCE for SSO provider. |
| `SSO_<PROVIDER>_SCOPE` | no default |  | internal | SSO configuration scope (`global` or `tenant`). |
| `SSO_<PROVIDER>_SCOPES` | no default |  | internal | OIDC Scopes for SSO provider. |
| `SSO_<PROVIDER>_TENANT_ID` | no default |  | internal | Tenant ID for tenant-scoped SSO. |
| `SSO_<PROVIDER>_TENANT_SLUG` | no default |  | internal | Tenant slug for tenant-scoped SSO. |
| `SSO_<PROVIDER>_TOKEN_AUTH_METHOD` | no default |  | secret | Token endpoint auth method for SSO. |
| `SSO_CALLBACK_RATE_LIMIT_PER_MINUTE` | optional (default) | 30 | internal | SSO callback rate limit |
| `SSO_CLIENT_SECRET_ENCRYPTION_KEY` | optional (default) | null | secret | Key for encrypting SSO client secrets / Key for encrypting SSO client secrets. |
| `SSO_CLOCK_SKEW_SECONDS` | optional (default) | 60 | internal | Clock skew tolerance for SSO tokens |
| `SSO_PROVIDERS` | no default |  | internal | Enabled SSO providers list. |
| `SSO_START_RATE_LIMIT_PER_MINUTE` | optional (default) | 30 | internal | SSO start rate limit |
| `SSO_STATE_TTL_MINUTES` | optional (default) | 10 | internal | TTL for SSO state |
| `STARTER_CONSOLE_SKIP_ENV` | no default |  | internal | Skip loading default .env files in CLI. / Skips environment checks in the starter console. / ... |
| `STARTER_CONSOLE_SKIP_VAULT_PROBE` | no default |  | internal | Skip Vault probe in CLI verification. / Skips Vault probing in the starter console. / ... |
| `STARTER_CONSOLE_TELEMETRY_OPT_IN` | no default |  | internal | Opt-in for CLI telemetry. |
| `STARTER_LOCAL_DATABASE_MODE` | no default |  | internal | Database mode for local development (`compose`/`external`). |
| `STARTER_OTLP_RECEIVE_TIMEOUT_SECONDS` | no default |  | internal | Timeout for OTLP collector tests. |
| `STATUS_API_TOKEN` | no default |  | secret | Auth token for Status API. |
| `STATUS_SUBSCRIPTION_EMAIL_RATE_LIMIT_PER_HOUR` | optional (default) | 5 | internal | Status email sub limit / Status subscription emails per hour. / ... |
| `STATUS_SUBSCRIPTION_ENCRYPTION_KEY` | optional (default) | null | secret | Encryption key for status subs / Key for encrypting status subscription data. / ... |
| `STATUS_SUBSCRIPTION_IP_RATE_LIMIT_PER_HOUR` | optional (default) | 20 | internal | Status IP sub limit / Status subscription attempts per IP per hour. / ... |
| `STATUS_SUBSCRIPTION_TOKEN_PEPPER` | optional (default) | "status-subscription-token-pepper" | secret | Pepper for status sub tokens / Pepper for status subscription tokens. / ... |
| `STATUS_SUBSCRIPTION_TOKEN_TTL_MINUTES` | optional (default) | 60 | secret | TTL for status sub tokens / Status subscription token lifetime. / ... |
| `STATUS_SUBSCRIPTION_WEBHOOK_TIMEOUT_SECONDS` | optional (default) | 5 | internal | Timeout for status webhooks / Timeout for status webhook delivery. |
| `STORAGE_ALLOWED_MIME_TYPES` | no default |  | internal | Allowed MIME types for storage |
| `STORAGE_BUCKET_PREFIX` | no default |  | internal | Prefix for storage buckets / Prefix for storage buckets. |
| `STORAGE_MAX_FILE_MB` | no default |  | internal | Max file size for storage |
| `STORAGE_PROVIDER` | optional (default) | "memory" | internal | Object storage provider. / Specifies the active storage backend. / ... |
| `STORAGE_SIGNED_URL_TTL_SECONDS` | no default |  | internal | TTL for presigned URLs |
| `STRIPE_PORTAL_RETURN_URL` | optional (default) | null | internal | Return URL for Stripe portal |
| `STRIPE_PRODUCT_PRICE_MAP` | no default |  | internal | Map of plan codes to Stripe Price IDs (e.g. `starter=price_123`). / Map of plans to Stripe prices / ... |
| `STRIPE_SECRET_KEY` | optional (default) | null | secret | Stripe API Secret Key. / Stripe Secret Key / ... |
| `STRIPE_WEBHOOK_SECRET` | optional (default) | null | secret | Stripe Webhook Signing Secret / Stripe Webhook Signing Secret. / ... |
| `TENANT_DEFAULT_SLUG` | optional (default) | "default" | internal | Default tenant slug / Default tenant slug for CLI context. |
| `TEXTUAL_LOG` | no default |  | internal | Path for Textual debug log. |
| `TEXTUAL_LOG_LEVEL` | no default |  | internal | Log level for Textual debug log. |
| `USAGE_GUARDRAIL_CACHE_BACKEND` | optional (default) | "redis" | internal | Cache backend for usage guardrails / Usage cache backend (`redis`/`memory`). |
| `USAGE_GUARDRAIL_CACHE_TTL_SECONDS` | optional (default) | 30 | internal | TTL for usage cache. / TTL for usage guardrail cache / ... |
| `USAGE_GUARDRAIL_REDIS_URL` | optional (default) | null | internal | Redis URL for usage counters/guardrails. / Redis URL for usage guardrails (defaults to `REDIS_URL`) / ... |
| `USAGE_GUARDRAIL_SOFT_LIMIT_MODE` | optional (default) | "warn" | internal | Enforcement mode for soft limits / Behavior on soft limit (`warn`/`block`). / ... |
| `USAGE_PLAN_CODES` | no default |  | internal | Comma-separated list of plan codes for usage. |
| `USAGE_{PLAN}_{DIMENSION}_{TYPE}_LIMIT` | no default |  | internal | Usage limit for a plan/dimension/type (soft/hard). |
| `USE_REAL_POSTGRES` | no default |  | internal | Toggles Postgres integration tests. |
| `USE_TEST_FIXTURES` | optional (default) | false | internal | Enable test fixture endpoints / Enables the use of test fixtures (data seeding). / ... |
| `VAULT_ADDR` | optional (default) | null | internal | HashiCorp Vault Address. / Vault address. / ... |
| `VAULT_NAMESPACE` | optional (default) | null | internal | HashiCorp Vault Namespace / Vault namespace (HCP). |
| `VAULT_TOKEN` | optional (default) | null | secret | HashiCorp Vault Token / Vault token. / ... |
| `VAULT_TRANSIT_KEY` | optional (default) | "auth-service" | internal | Vault Transit Key Name / Vault Transit engine key name. / ... |
| `VAULT_VERIFY_ENABLED` | optional (default) | false | internal | Enforce Vault signature verification / Toggles Vault signature verification. / ... |
| `VECTOR_ALLOWED_MIME_TYPES` | no default |  | internal | Allowed MIME types for vector stores |
| `VECTOR_MAX_FILE_MB` | no default |  | internal | Max file size for vector stores / Max file size for vector stores in MB. / ... |
| `VECTOR_MAX_FILES_PER_STORE` | no default |  | internal | Max files per vector store / Max files per vector store. / ... |
| `VECTOR_MAX_STORES_PER_TENANT` | no default |  | internal | Max stores per vector store / Max vector stores per tenant. / ... |
| `VECTOR_MAX_TOTAL_BYTES` | no default |  | internal | Max total bytes for vector stores / Max total bytes for vector storage per tenant. / ... |
| `VECTOR_STORE_SYNC_BATCH_SIZE` | no default |  | internal | Batch size for vector store sync |
| `VECTOR_STORE_SYNC_POLL_SECONDS` | no default |  | internal | Poll interval for vector store sync |
| `VERCEL_GIT_COMMIT_TIMESTAMP` | no default |  | internal | Git commit timestamp provided by Vercel. / Used to determine the `lastModified` date for sitemap entries. / ... |
| `WORKERS` | no default |  | internal | Number of Uvicorn workers |
| `WORKFLOW_MIN_PURGE_AGE_HOURS` | optional (default) | 0 | internal | Minimum age for hard deleting workflows |
| `XAI_API_KEY` | no default |  | secret | API key for xAI. / xAI API Key |
