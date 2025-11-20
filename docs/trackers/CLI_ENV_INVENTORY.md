# Starter CLI Environment Inventory

This file is generated via `python -m starter_cli.app config write-inventory`.
Last updated: 2025-11-20 00:00:00 UTC

Legend: `✅` = wizard prompts for it, blank = requires manual population.

| Env Var | Type | Default | Required | Wizard? | Description |
| --- | --- | --- | --- | --- | --- |
| ACCESS_TOKEN_EXPIRE_MINUTES | int | 30 |  | ✅ | Access token expiration time in minutes |
| AGENT_MODEL_CODE | str \| NoneType | — |  |  | Override for the code assistant model; defaults to agent_default_model. |
| AGENT_MODEL_DATA | str \| NoneType | — |  |  | Override for the data analyst model; defaults to agent_default_model. |
| AGENT_MODEL_DEFAULT | str | gpt-5.1 |  |  | Default reasoning model for triage and agent fallbacks. |
| AGENT_MODEL_TRIAGE | str \| NoneType | — |  |  | Override for the triage agent model; defaults to agent_default_model. |
| ALLOWED_HEADERS | str | * |  | ✅ | CORS allowed headers (comma-separated) |
| ALLOWED_HOSTS | str | localhost,localhost:8000,127.0.0.1,testserver,testclient |  | ✅ | Trusted hosts for FastAPI TrustedHostMiddleware (comma-separated host[:port] entries). |
| ALLOWED_METHODS | str | GET,POST,PUT,DELETE,OPTIONS |  | ✅ | CORS allowed methods (comma-separated) |
| ALLOWED_ORIGINS | str | http://localhost:3000,http://localhost:8000 |  | ✅ | CORS allowed origins (comma-separated) |
| ALLOW_PUBLIC_SIGNUP | bool | True |  | ✅ | Allow unauthenticated tenants to self-register via /auth/register. Derived from SIGNUP_ACCESS_POLICY. |
| ALLOW_SIGNUP_TRIAL_OVERRIDE | bool | False |  | ✅ | Permit /auth/register callers to request trial periods up to the plan/default cap. |
| ANTHROPIC_API_KEY | str \| NoneType | — |  | ✅ | Anthropic API key |
| APP_DESCRIPTION | str | api-service FastAPI microservice |  | ✅ | Application description |
| APP_NAME | str | api-service |  | ✅ | Application name |
| APP_PUBLIC_URL | str | http://localhost:3000 |  | ✅ | Public base URL used when generating email links. |
| APP_VERSION | str | 1.0.0 |  | ✅ | Application version |
| AUTH_AUDIENCE | list[str] | — |  | ✅ | Ordered list of permitted JWT audiences. Provide as JSON array via AUTH_AUDIENCE or comma-separated strings. |
| AUTH_CACHE_REDIS_URL | str \| NoneType | — |  | ✅ | Redis URL dedicated to auth/session caches like refresh tokens and lockouts. |
| AUTH_EMAIL_VERIFICATION_TOKEN_PEPPER | str | local-email-verify-pepper |  | ✅ | Pepper used when hashing email verification token secrets. |
| AUTH_IP_LOCKOUT_DURATION_MINUTES | int | 10 |  | ✅ | Duration in minutes to block an IP/subnet after threshold breaches. |
| AUTH_IP_LOCKOUT_THRESHOLD | int | 50 |  | ✅ | Failed attempts per IP or /24 subnet per minute before throttling. |
| AUTH_IP_LOCKOUT_WINDOW_MINUTES | int | 10 |  | ✅ | Window in minutes used for IP-based throttling heuristics. |
| AUTH_JWKS_CACHE_SECONDS | int | 300 |  | ✅ | Cache max-age for /.well-known/jwks.json responses. |
| AUTH_JWKS_ETAG_SALT | str | local-jwks-salt |  | ✅ | Salt mixed into JWKS ETag derivation to avoid predictable hashes. |
| AUTH_JWKS_MAX_AGE_SECONDS | int | 300 |  | ✅ | Preferred Cache-Control max-age for JWKS responses. |
| AUTH_KEY_SECRET_NAME | str \| NoneType | — |  | ✅ | Secret-manager key/path storing keyset JSON when backend=secret-manager. |
| AUTH_KEY_STORAGE_BACKEND | str | file |  | ✅ | Key storage backend (file or secret-manager). |
| AUTH_KEY_STORAGE_PATH | str | var/keys/keyset.json |  | ✅ | Filesystem path for keyset JSON when using file backend. |
| AUTH_LOCKOUT_DURATION_MINUTES | float | 60.0 |  | ✅ | Automatic unlock window for locked users (minutes). |
| AUTH_LOCKOUT_THRESHOLD | int | 5 |  | ✅ | Failed login attempts allowed before locking the account. |
| AUTH_LOCKOUT_WINDOW_MINUTES | float | 60.0 |  | ✅ | Rolling window in minutes for lockout threshold calculations. |
| AUTH_PASSWORD_HISTORY_COUNT | int | 5 |  | ✅ | Number of historical password hashes retained per user. |
| AUTH_PASSWORD_PEPPER | str | local-dev-password-pepper |  | ✅ | Pepper prepended to human passwords prior to hashing. |
| AUTH_PASSWORD_RESET_TOKEN_PEPPER | str | local-reset-token-pepper |  | ✅ | Pepper used to hash password reset token secrets. |
| AUTH_REFRESH_TOKEN_PEPPER | str | local-dev-refresh-pepper |  | ✅ | Server-side pepper prepended when hashing refresh tokens. |
| AUTH_REFRESH_TOKEN_TTL_MINUTES | int | 43200 |  | ✅ | Default refresh token lifetime for human users (minutes). |
| AUTH_SESSION_ENCRYPTION_KEY | str \| NoneType | — |  | ✅ | Base64-compatible secret used to encrypt stored IP metadata for user sessions. |
| AUTH_SESSION_IP_HASH_SALT | str \| NoneType | — |  | ✅ | Salt blended into session IP hash derivation (defaults to SECRET_KEY). |
| AUTO_RUN_MIGRATIONS | bool | False |  | ✅ | Automatically run Alembic migrations on startup (dev convenience) |
| AWS_ACCESS_KEY_ID | str \| NoneType | — |  | ✅ | AWS access key ID (overrides profile/IMDS when set). |
| AWS_PROFILE | str \| NoneType | — |  | ✅ | Named AWS profile to use when loading credentials. |
| AWS_REGION | str \| NoneType | — |  | ✅ | AWS region for Secrets Manager requests. |
| AWS_SECRET_ACCESS_KEY | str \| NoneType | — |  | ✅ | AWS secret access key. |
| AWS_SESSION_TOKEN | str \| NoneType | — |  | ✅ | AWS session token (for temporary credentials). |
| AWS_SM_CACHE_TTL_SECONDS | int | 60 |  | ✅ | TTL (seconds) for cached Secrets Manager values. |
| AWS_SM_SIGNING_SECRET_ARN | str \| NoneType | — |  | ✅ | Secrets Manager ARN/name containing the signing secret value. |
| AZURE_CLIENT_ID | str \| NoneType | — |  | ✅ | Azure AD application (client) ID. |
| AZURE_CLIENT_SECRET | str \| NoneType | — |  | ✅ | Azure AD application secret. |
| AZURE_KEY_VAULT_URL | str \| NoneType | — |  | ✅ | Azure Key Vault URL (https://<name>.vault.azure.net). |
| AZURE_KV_CACHE_TTL_SECONDS | int | 60 |  | ✅ | TTL (seconds) for cached Key Vault secret values. |
| AZURE_KV_SIGNING_SECRET_NAME | str \| NoneType | — |  | ✅ | Key Vault secret name containing the signing secret value. |
| AZURE_MANAGED_IDENTITY_CLIENT_ID | str \| NoneType | — |  | ✅ | User-assigned managed identity client ID (optional). |
| AZURE_TENANT_ID | str \| NoneType | — |  | ✅ | Azure AD tenant ID for service principal auth. |
| BILLING_EVENTS_REDIS_URL | str \| NoneType | — |  | ✅ | Redis URL used for billing event pub/sub (defaults to REDIS_URL when unset) |
| BILLING_RETRY_DEPLOYMENT_MODE | str | inline |  | ✅ | Documented deployment target for the Stripe retry worker (inline/dedicated). |
| BILLING_STREAM_CONCURRENT_LIMIT | int | 3 |  | ✅ | Simultaneous billing stream connections allowed per tenant. |
| BILLING_STREAM_RATE_LIMIT_PER_MINUTE | int | 20 |  | ✅ | Maximum billing stream subscriptions allowed per tenant per minute. |
| CHAT_RATE_LIMIT_PER_MINUTE | int | 60 |  | ✅ | Maximum chat completions allowed per user per minute. |
| CHAT_STREAM_CONCURRENT_LIMIT | int | 5 |  | ✅ | Simultaneous streaming chat sessions allowed per user. |
| CHAT_STREAM_RATE_LIMIT_PER_MINUTE | int | 30 |  | ✅ | Maximum streaming chat sessions started per user per minute. |
| DATABASE_ECHO | bool | False |  | ✅ | Enable SQLAlchemy engine echo for debugging |
| DATABASE_HEALTH_TIMEOUT | float | 5.0 |  | ✅ | Timeout for database health checks (seconds) |
| DATABASE_MAX_OVERFLOW | int | 10 |  | ✅ | Maximum overflow connections for the SQLAlchemy pool |
| DATABASE_POOL_RECYCLE | int | 1800 |  | ✅ | Seconds before recycling idle connections |
| DATABASE_POOL_SIZE | int | 5 |  | ✅ | SQLAlchemy async pool size |
| DATABASE_POOL_TIMEOUT | float | 30.0 |  | ✅ | Seconds to wait for a connection from the pool |
| DATABASE_URL | str \| NoneType | — |  | ✅ | Async SQLAlchemy URL for the primary Postgres database |
| DEBUG | bool | False |  | ✅ | Debug mode |
| EMAIL_VERIFICATION_EMAIL_RATE_LIMIT_PER_HOUR | int | 3 |  | ✅ | Verification email sends per account per hour. |
| EMAIL_VERIFICATION_IP_RATE_LIMIT_PER_HOUR | int | 10 |  | ✅ | Verification email sends per IP per hour. |
| EMAIL_VERIFICATION_TOKEN_TTL_MINUTES | int | 60 |  | ✅ | Email verification token lifetime in minutes. |
| ENABLE_BILLING | bool | False |  | ✅ | Expose billing features and APIs once subscriptions are implemented |
| ENABLE_BILLING_RETRY_WORKER | bool | True |  | ✅ | Run the Stripe dispatch retry worker inside this process |
| ENABLE_BILLING_STREAM | bool | False |  | ✅ | Enable real-time billing event streaming endpoints |
| ENABLE_BILLING_STREAM_REPLAY | bool | True |  | ✅ | Replay processed Stripe events into Redis billing streams during startup |
| ENABLE_FRONTEND_LOG_INGEST | bool | False |  | ✅ | Expose authenticated frontend log ingest endpoint. |
| ENABLE_SECRETS_PROVIDER_TELEMETRY | bool | False |  | ✅ | Emit structured metrics/logs about secrets provider selection (no payloads). |
| ENABLE_SLACK_STATUS_NOTIFICATIONS | bool | False |  | ✅ | Toggle Slack fan-out for status incidents. |
| ENABLE_USAGE_GUARDRAILS | bool | False |  | ✅ | If true, enforce plan usage limits before servicing chat requests. Requires billing to be enabled. |
| ENVIRONMENT | str | development |  | ✅ | Deployment environment label (development, staging, production, etc.) |
| GEMINI_API_KEY | str \| NoneType | — |  | ✅ | Google Gemini API key |
| GEOIP_CACHE_MAX_ENTRIES | int | 4096 |  |  | Maximum cached GeoIP lookups to retain in memory. |
| GEOIP_CACHE_TTL_SECONDS | float | 900.0 |  |  | TTL (seconds) for GeoIP lookup cache entries. |
| GEOIP_HTTP_TIMEOUT_SECONDS | float | 2.0 |  |  | HTTP timeout (seconds) for SaaS GeoIP providers. |
| GEOIP_IP2LOCATION_API_KEY | str \| NoneType | — |  | ✅ | IP2Location API key when geoip_provider=ip2location. |
| GEOIP_IP2LOCATION_DB_PATH | str \| NoneType | — |  |  | Filesystem path to the IP2Location BIN database. |
| GEOIP_IPINFO_TOKEN | str \| NoneType | — |  |  | IPinfo API token when geoip_provider=ipinfo. |
| GEOIP_MAXMIND_DB_PATH | str \| NoneType | — |  |  | Filesystem path to the MaxMind GeoIP2/GeoLite2 database. |
| GEOIP_MAXMIND_LICENSE_KEY | str \| NoneType | — |  | ✅ | MaxMind license key when geoip_provider=maxmind. |
| GEOIP_PROVIDER | str | none |  | ✅ | GeoIP provider selection (none, ipinfo, ip2location, maxmind_db, ip2location_db). |
| INFISICAL_BASE_URL | str \| NoneType | — |  | ✅ | Base URL for Infisical API (set when using Infisical providers). |
| INFISICAL_CACHE_TTL_SECONDS | int | 60 |  | ✅ | TTL (seconds) for Infisical secret cache entries. |
| INFISICAL_CA_BUNDLE_PATH | str \| NoneType | — |  | ✅ | Optional CA bundle path for self-hosted Infisical instances. |
| INFISICAL_ENVIRONMENT | str \| NoneType | — |  | ✅ | Infisical environment slug (e.g., dev, staging, prod). |
| INFISICAL_PROJECT_ID | str \| NoneType | — |  | ✅ | Infisical project identifier associated with this deployment. |
| INFISICAL_SECRET_PATH | str \| NoneType | — |  | ✅ | Secret path (e.g., /backend) to read when seeding env vars. |
| INFISICAL_SERVICE_TOKEN | str \| NoneType | — |  | ✅ | Infisical service token used for non-interactive secret access. |
| INFISICAL_SIGNING_SECRET_NAME | str | auth-service-signing-secret |  | ✅ | Infisical secret name holding the shared signing key for service-account payloads. |
| JWT_ALGORITHM | str | HS256 |  | ✅ | JWT algorithm |
| LOGGING_DATADOG_API_KEY | str \| NoneType | — |  | ✅ | Datadog API key when logging_sink=datadog. |
| LOGGING_DATADOG_SITE | str \| NoneType | datadoghq.com |  | ✅ | Datadog site (datadoghq.com, datadoghq.eu, etc.). |
| LOGGING_FILE_BACKUPS | int | 5 |  | ✅ | Rotated backup files to retain when logging_sink=file. |
| LOGGING_FILE_MAX_MB | int | 10 |  | ✅ | Maximum megabytes per log file when logging_sink=file. |
| LOGGING_FILE_PATH | str | var/log/api-service.log |  | ✅ | Filesystem path for file sink when logging_sink=file. |
| LOGGING_OTLP_ENDPOINT | str \| NoneType | — |  | ✅ | OTLP/HTTP endpoint when logging_sink=otlp. |
| LOGGING_OTLP_HEADERS | str \| NoneType | — |  | ✅ | Optional OTLP headers JSON when logging_sink=otlp. |
| LOGGING_SINK | str | stdout |  | ✅ | Logging sink (stdout, file, datadog, otlp, or none). |
| LOG_LEVEL | str | INFO |  | ✅ | Logging level |
| NEXT_PUBLIC_LOG_LEVEL | str | info |  | ✅ | Frontend log level (debug, info, warn, error). |
| NEXT_PUBLIC_LOG_SINK | str | console |  | ✅ | Frontend log sink (console, beacon, none). |
| OPENAI_API_KEY | str \| NoneType | — |  | ✅ | OpenAI API key |
| PASSWORD_RESET_EMAIL_RATE_LIMIT_PER_HOUR | int | 5 |  | ✅ | Password reset requests allowed per email per hour. |
| PASSWORD_RESET_IP_RATE_LIMIT_PER_HOUR | int | 20 |  | ✅ | Password reset requests allowed per IP per hour. |
| PASSWORD_RESET_TOKEN_TTL_MINUTES | int | 30 |  | ✅ | Password reset token lifetime in minutes. |
| PORT | int | 8000 |  | ✅ | Server port |
| RATE_LIMIT_KEY_PREFIX | str | rate-limit |  | ✅ | Redis key namespace used by the rate limiter service. |
| RATE_LIMIT_REDIS_URL | str \| NoneType | — |  | ✅ | Redis URL dedicated to rate limiting (defaults to REDIS_URL when unset). |
| REDIS_URL | str | redis://localhost:6379/0 |  | ✅ | Redis connection URL |
| REQUIRE_EMAIL_VERIFICATION | bool | True |  | ✅ | Require verified email before accessing protected APIs. |
| RESEND_API_KEY | str \| NoneType | — |  | ✅ | Resend API key (re_...). Required when RESEND_EMAIL_ENABLED=true. |
| RESEND_BASE_URL | str | https://api.resend.com |  | ✅ | Override Resend API base URL for testing/sandbox environments. |
| RESEND_DEFAULT_FROM | str \| NoneType | — |  | ✅ | Fully-qualified From address verified in Resend. |
| RESEND_EMAIL_ENABLED | bool | False |  | ✅ | When true, use Resend for transactional email delivery. |
| RESEND_EMAIL_VERIFICATION_TEMPLATE_ID | str \| NoneType | — |  | ✅ | Optional Resend template ID for email verification messages. |
| RESEND_PASSWORD_RESET_TEMPLATE_ID | str \| NoneType | — |  | ✅ | Optional Resend template ID for password reset messages. |
| SECRETS_PROVIDER | SecretsProviderLiteral | vault_dev |  | ✅ | Which secrets provider implementation to use (vault_dev, vault_hcp, infisical_cloud, infisical_self_host). |
| SECRET_KEY | str | your-secret-key-here-change-in-production |  | ✅ | JWT secret key |
| SECURITY_TOKEN_REDIS_URL | str \| NoneType | — |  | ✅ | Redis URL dedicated to nonce/email/password token stores (falls back to REDIS_URL). |
| SIGNUP_ACCESS_POLICY | public \| invite_only \| approval | invite_only |  | ✅ | Signup exposure posture: public, invite_only, or approval. |
| SIGNUP_CONCURRENT_REQUESTS_LIMIT | int | 3 |  | ✅ | Maximum pending signup requests allowed per IP before operators respond. |
| SIGNUP_DEFAULT_PLAN_CODE | str \| NoneType | starter |  | ✅ | Plan code automatically provisioned for new tenants when billing is enabled. |
| SIGNUP_DEFAULT_TRIAL_DAYS | int | 14 |  | ✅ | Fallback trial length (days) for tenants when processor metadata is unavailable. |
| SIGNUP_INVITE_RESERVATION_TTL_SECONDS | int | 900 |  |  | How long (seconds) a reserved invite remains valid while signup provisioning runs. |
| SIGNUP_RATE_LIMIT_PER_DOMAIN_DAY | int | 20 |  | ✅ | Maximum signup attempts permitted per email domain each day. |
| SIGNUP_RATE_LIMIT_PER_EMAIL_DAY | int | 3 |  | ✅ | Maximum signup attempts permitted per email address each day. |
| SIGNUP_RATE_LIMIT_PER_HOUR | int | 20 |  | ✅ | Maximum signup attempts permitted per IP address each hour. |
| SIGNUP_RATE_LIMIT_PER_IP_DAY | int | 100 |  | ✅ | Maximum signup attempts permitted per IP address each day. |
| SLACK_API_BASE_URL | str | https://slack.com/api |  | ✅ | Slack Web API base URL (override for tests). |
| SLACK_HTTP_TIMEOUT_SECONDS | float | 5.0 |  | ✅ | HTTP timeout for Slack API requests. |
| SLACK_STATUS_BOT_TOKEN | str \| NoneType | — |  | ✅ | OAuth bot token with chat:write scope. |
| SLACK_STATUS_DEFAULT_CHANNELS | list[str] | — |  | ✅ | Default Slack channel IDs (comma-separated or JSON list). |
| SLACK_STATUS_MAX_RETRIES | int | 3 |  | ✅ | Maximum retry attempts for Slack delivery failures. |
| SLACK_STATUS_RATE_LIMIT_WINDOW_SECONDS | float | 1.0 |  | ✅ | Per-channel throttle window for Slack posts. |
| SLACK_STATUS_TENANT_CHANNEL_MAP | dict[str, list[str]] | — |  | ✅ | JSON map of tenant_id → channel list overrides. |
| STATUS_SUBSCRIPTION_EMAIL_RATE_LIMIT_PER_HOUR | int | 5 |  | ✅ | Email subscription attempts per IP per hour. |
| STATUS_SUBSCRIPTION_ENCRYPTION_KEY | str \| NoneType | — |  | ✅ | Override secret used to encrypt subscription targets and webhook secrets. |
| STATUS_SUBSCRIPTION_IP_RATE_LIMIT_PER_HOUR | int | 20 |  | ✅ | Webhook subscription attempts per IP per hour. |
| STATUS_SUBSCRIPTION_TOKEN_PEPPER | str | status-subscription-token-pepper |  | ✅ | Pepper used to hash status subscription verification tokens. |
| STATUS_SUBSCRIPTION_TOKEN_TTL_MINUTES | int | 60 |  | ✅ | Status subscription email verification token lifetime in minutes. |
| STATUS_SUBSCRIPTION_WEBHOOK_TIMEOUT_SECONDS | int | 5 |  | ✅ | HTTP timeout applied when delivering webhook challenges (seconds). |
| STRIPE_PRODUCT_PRICE_MAP | dict[str, str] | — |  | ✅ | Mapping of billing plan codes to Stripe price IDs. Provide as JSON or comma-delimited entries such as 'starter=price_123,pro=price_456'. |
| STRIPE_SECRET_KEY | str \| NoneType | — |  | ✅ | Stripe secret API key (sk_live_*/sk_test_*). |
| STRIPE_WEBHOOK_SECRET | str \| NoneType | — |  | ✅ | Stripe webhook signing secret (whsec_*). |
| TAVILY_API_KEY | str \| NoneType | — |  | ✅ | Tavily web search API key |
| TENANT_DEFAULT_SLUG | str | default |  | ✅ | Tenant slug recorded by the CLI when seeding the initial org. |
| USAGE_GUARDRAIL_CACHE_BACKEND | memory \| redis | redis |  | ✅ | Cache backend for usage totals (`redis` or `memory`). |
| USAGE_GUARDRAIL_CACHE_TTL_SECONDS | int | 30 |  | ✅ | TTL for cached usage rollups (seconds). Set to 0 to disable caching. |
| USAGE_GUARDRAIL_REDIS_URL | str \| NoneType | — |  | ✅ | Redis URL dedicated to usage guardrail caches (defaults to REDIS_URL). |
| USAGE_GUARDRAIL_SOFT_LIMIT_MODE | warn \| block | warn |  | ✅ | How to react when soft limits are exceeded: 'warn' logs a warning but allows the request, while 'block' treats soft limits like hard caps. |
| USE_TEST_FIXTURES | bool | False |  |  | Enable fixture overrides for tests/local runs. |
| VAULT_ADDR | str \| NoneType | — |  | ✅ | HashiCorp Vault address for Transit verification. |
| VAULT_NAMESPACE | str \| NoneType | — |  | ✅ | Optional Vault namespace for HCP or multi-tenant clusters. |
| VAULT_TOKEN | str \| NoneType | — |  | ✅ | Vault token/AppRole secret with transit:verify capability. |
| VAULT_TRANSIT_KEY | str | auth-service |  | ✅ | Transit key name used for signing/verification. |
| VAULT_VERIFY_ENABLED | bool | False |  | ✅ | When true, enforce Vault Transit verification for service-account issuance. |
| XAI_API_KEY | str \| NoneType | — |  | ✅ | xAI API key |
