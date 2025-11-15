# Starter CLI Environment Inventory

This file enumerates every backend environment variable exposed by `app.core.config.Settings`, notes its default, and flags whether the Starter CLI setup wizard currently prompts for it explicitly. Regenerate this inventory at any time with `starter_cli config dump-schema --format table` (or `--format json` for automation).

Legend: `✅` = prompted during wizard, `⚠️` = optional/backfilled warning, `❌` = not yet collected.

## Auth & policy

| Env Var | Type | Default | Wizard? | Description |
| --- | --- | --- | --- | --- |
| `AUTH_EMAIL_VERIFICATION_TOKEN_PEPPER` | `str` | local-email-verify-pepper | ✅ | Pepper used when hashing email verification token secrets. |
| `AUTH_IP_LOCKOUT_DURATION_MINUTES` | `int` | 10 | ❌ | Duration in minutes to block an IP/subnet after threshold breaches. |
| `AUTH_IP_LOCKOUT_THRESHOLD` | `int` | 50 | ❌ | Failed attempts per IP or /24 subnet per minute before throttling. |
| `AUTH_IP_LOCKOUT_WINDOW_MINUTES` | `int` | 10 | ❌ | Window in minutes used for IP-based throttling heuristics. |
| `AUTH_JWKS_CACHE_SECONDS` | `int` | 300 | ❌ | Cache max-age for /.well-known/jwks.json responses. |
| `AUTH_JWKS_ETAG_SALT` | `str` | local-jwks-salt | ❌ | Salt mixed into JWKS ETag derivation to avoid predictable hashes. |
| `AUTH_JWKS_MAX_AGE_SECONDS` | `int` | 300 | ❌ | Preferred Cache-Control max-age for JWKS responses. |
| `AUTH_LOCKOUT_DURATION_MINUTES` | `float` | 60.0 | ❌ | Automatic unlock window for locked users (minutes). |
| `AUTH_LOCKOUT_THRESHOLD` | `int` | 5 | ❌ | Failed login attempts allowed before locking the account. |
| `AUTH_LOCKOUT_WINDOW_MINUTES` | `float` | 60.0 | ❌ | Rolling window in minutes for lockout threshold calculations. |
| `AUTH_PASSWORD_HISTORY_COUNT` | `int` | 5 | ❌ | Number of historical password hashes retained per user. |
| `AUTH_PASSWORD_PEPPER` | `str` | local-dev-password-pepper | ✅ | Pepper prepended to human passwords prior to hashing. |
| `AUTH_PASSWORD_RESET_TOKEN_PEPPER` | `str` | local-reset-token-pepper | ✅ | Pepper used to hash password reset token secrets. |
| `AUTH_REFRESH_TOKEN_PEPPER` | `str` | local-dev-refresh-pepper | ✅ | Server-side pepper prepended when hashing refresh tokens. |
| `AUTH_REFRESH_TOKEN_TTL_MINUTES` | `int` | 43200 | ❌ | Default refresh token lifetime for human users (minutes). |
| `AUTH_SESSION_ENCRYPTION_KEY` | `str | None` | None | ✅ | Base64-compatible secret used to encrypt stored IP metadata for user sessions. |
| `AUTH_SESSION_IP_HASH_SALT` | `str | None` | None | ✅ | Salt blended into session IP hash derivation (defaults to SECRET_KEY). |
| `EMAIL_VERIFICATION_EMAIL_RATE_LIMIT_PER_HOUR` | `int` | 3 | ❌ | Verification email sends per account per hour. |
| `EMAIL_VERIFICATION_IP_RATE_LIMIT_PER_HOUR` | `int` | 10 | ❌ | Verification email sends per IP per hour. |
| `EMAIL_VERIFICATION_TOKEN_TTL_MINUTES` | `int` | 60 | ❌ | Email verification token lifetime in minutes. |
| `PASSWORD_RESET_EMAIL_RATE_LIMIT_PER_HOUR` | `int` | 5 | ❌ | Password reset requests allowed per email per hour. |
| `PASSWORD_RESET_IP_RATE_LIMIT_PER_HOUR` | `int` | 20 | ❌ | Password reset requests allowed per IP per hour. |
| `PASSWORD_RESET_TOKEN_TTL_MINUTES` | `int` | 30 | ❌ | Password reset token lifetime in minutes. |
| `STATUS_SUBSCRIPTION_EMAIL_RATE_LIMIT_PER_HOUR` | `int` | 5 | ❌ | Email subscription attempts per IP per hour. |
| `STATUS_SUBSCRIPTION_ENCRYPTION_KEY` | `str | None` | None | ❌ | Override secret used to encrypt subscription targets and webhook secrets. Defaults to SECRET_KEY when unset. |
| `STATUS_SUBSCRIPTION_IP_RATE_LIMIT_PER_HOUR` | `int` | 20 | ❌ | Webhook subscription attempts per IP per hour. |
| `STATUS_SUBSCRIPTION_TOKEN_PEPPER` | `str` | status-subscription-token-pepper | ❌ | Pepper used to hash status subscription verification tokens. |
| `STATUS_SUBSCRIPTION_TOKEN_TTL_MINUTES` | `int` | 60 | ❌ | Status subscription email verification token lifetime in minutes. |
| `STATUS_SUBSCRIPTION_WEBHOOK_TIMEOUT_SECONDS` | `int` | 5 | ❌ | HTTP timeout applied when delivering webhook challenges (seconds). |

## Billing & Stripe

| Env Var | Type | Default | Wizard? | Description |
| --- | --- | --- | --- | --- |
| `BILLING_EVENTS_REDIS_URL` | `str | None` | None | ✅ | Redis URL used for billing event pub/sub (defaults to REDIS_URL when unset) |
| `BILLING_RETRY_DEPLOYMENT_MODE` | `str` | inline | ✅ | Documented deployment target for the Stripe retry worker (inline/dedicated). |
| `ENABLE_BILLING` | `bool` | False | ✅ | Expose billing features and APIs once subscriptions are implemented |
| `ENABLE_BILLING_RETRY_WORKER` | `bool` | True | ✅ | Run the Stripe dispatch retry worker inside this process |
| `ENABLE_BILLING_STREAM` | `bool` | False | ✅ | Enable real-time billing event streaming endpoints |
| `ENABLE_BILLING_STREAM_REPLAY` | `bool` | True | ✅ | Replay processed Stripe events into Redis billing streams during startup |
| `STRIPE_PRODUCT_PRICE_MAP` | `dict` | PydanticUndefined | ✅ | Mapping of billing plan codes to Stripe price IDs. Provide as JSON or comma-delimited entries such as 'starter=price_123,pro=price_456'. |
| `STRIPE_SECRET_KEY` | `str | None` | None | ✅ | Stripe secret API key (sk_live_*/sk_test_*). |
| `STRIPE_WEBHOOK_SECRET` | `str | None` | None | ✅ | Stripe webhook signing secret (whsec_*). |

## Core runtime & network

| Env Var | Type | Default | Wizard? | Description |
| --- | --- | --- | --- | --- |
| `APP_PUBLIC_URL` | `str` | http://localhost:3000 | ✅ | Public base URL used when generating email links. |
| `ENVIRONMENT` | `str` | development | ✅ | Deployment environment label (development, staging, production, etc.) |
| `PORT` | `int` | 8000 | ✅ | FastAPI port used for the backend service. |
| `DEBUG` | `bool` | False | ✅ | Enable FastAPI debug mode. |
| `AUTO_RUN_MIGRATIONS` | `bool` | False | ✅ | Automatically run Alembic migrations on startup. |
| `SECRET_KEY` | `str` | your-secret-key-here-change-in-production | ✅ | Application SECRET_KEY used for signing tokens. |
| `ALLOWED_HOSTS` | `str` | localhost,localhost:8000,127.0.0.1,testserver,testclient | ✅ | Trusted hosts for FastAPI TrustedHostMiddleware. |
| `ALLOWED_ORIGINS` | `str` | http://localhost:3000,http://localhost:8000 | ✅ | CORS allowed origins (comma-separated). |
| `DATABASE_URL` | `str | None` | None | ✅ | Async SQLAlchemy URL for the primary Postgres database |
| `REDIS_URL` | `str` | redis://localhost:6379/0 | ✅ | Redis connection URL used across services. |

## AI providers & tools

| Env Var | Type | Default | Wizard? | Description |
| --- | --- | --- | --- | --- |
| `OPENAI_API_KEY` | `str | None` | None | ✅ | OpenAI API key used for Agents. |
| `ANTHROPIC_API_KEY` | `str | None` | None | ✅ | Anthropic API key (optional). |
| `GEMINI_API_KEY` | `str | None` | None | ✅ | Google Gemini API key (optional). |
| `XAI_API_KEY` | `str | None` | None | ✅ | xAI API key (optional). |
| `TAVILY_API_KEY` | `str | None` | None | ✅ | Tavily web search API key. |

## Signup policy

| Env Var | Type | Default | Wizard? | Description |
| --- | --- | --- | --- | --- |
| `ALLOW_PUBLIC_SIGNUP` | `bool` | True | ✅ | Allow unauthenticated tenants to self-register. |
| `ALLOW_SIGNUP_TRIAL_OVERRIDE` | `bool` | False | ✅ | Permit clients to request custom trial lengths. |
| `SIGNUP_RATE_LIMIT_PER_HOUR` | `int` | 20 | ✅ | Signup attempts per hour (per IP). |
| `SIGNUP_DEFAULT_PLAN_CODE` | `str | None` | starter | ✅ | Default plan code provisioned for new tenants. |
| `SIGNUP_DEFAULT_TRIAL_DAYS` | `int` | 14 | ✅ | Default trial length for new tenants. |

## Email delivery

| Env Var | Type | Default | Wizard? | Description |
| --- | --- | --- | --- | --- |
| `RESEND_API_KEY` | `str | None` | None | ✅ | Resend API key (re_...). Required when RESEND_EMAIL_ENABLED=true. |
| `RESEND_BASE_URL` | `str` | https://api.resend.com | ✅ | Override Resend API base URL for testing/sandbox environments. |
| `RESEND_DEFAULT_FROM` | `str | None` | None | ✅ | Fully-qualified From address (e.g., support@example.com) verified in Resend. |
| `RESEND_EMAIL_ENABLED` | `bool` | False | ✅ | When true, use Resend for transactional email delivery instead of the logging notifier. |
| `RESEND_EMAIL_VERIFICATION_TEMPLATE_ID` | `str | None` | None | ✅ | Optional Resend template ID for email verification messages. |
| `RESEND_PASSWORD_RESET_TEMPLATE_ID` | `str | None` | None | ✅ | Optional Resend template ID for password reset messages. |

## Observability & GeoIP

| Env Var | Type | Default | Wizard? | Description |
| --- | --- | --- | --- | --- |
| `GEOIP_IP2LOCATION_API_KEY` | `str | None` | None | ✅ | IP2Location API key when geoip_provider=ip2location. |
| `GEOIP_MAXMIND_LICENSE_KEY` | `str | None` | None | ✅ | MaxMind license key when geoip_provider=maxmind. |
| `GEOIP_PROVIDER` | `str` | none | ✅ | GeoIP provider selection (none, maxmind, ip2location). |
| `LOGGING_DATADOG_API_KEY` | `str | None` | None | ✅ | Datadog API key when logging_sink=datadog. |
| `LOGGING_DATADOG_SITE` | `str | None` | datadoghq.com | ✅ | Datadog site (datadoghq.com, datadoghq.eu, etc.). |
| `LOGGING_OTLP_ENDPOINT` | `str | None` | None | ✅ | OTLP/HTTP endpoint when logging_sink=otlp. |
| `LOGGING_OTLP_HEADERS` | `str | None` | None | ✅ | Optional OTLP headers JSON when logging_sink=otlp. |
| `LOGGING_SINK` | `str` | stdout | ✅ | Logging sink (stdout, datadog, otlp, or none). |

## Other

| Env Var | Type | Default | Wizard? | Description |
| --- | --- | --- | --- | --- |
| `REQUIRE_EMAIL_VERIFICATION` | `bool` | True | ❌ | Require verified email before accessing protected APIs. |
| `TENANT_DEFAULT_SLUG` | `str` | default | ✅ | Tenant slug recorded by the CLI when seeding the initial org. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `int` | 30 | ❌ | Access token expiration time in minutes |
| `ALLOWED_HEADERS` | `str` | * | ❌ | CORS allowed headers (comma-separated) |
| `ALLOWED_METHODS` | `str` | GET,POST,PUT,DELETE,OPTIONS | ❌ | CORS allowed methods (comma-separated) |
| `APP_DESCRIPTION` | `str` | anything-agents FastAPI microservice | ❌ | Application description |
| `APP_NAME` | `str` | anything-agents | ❌ | Application name |
| `APP_VERSION` | `str` | 1.0.0 | ❌ | Application version |
| `AUTH_AUDIENCE` | `list` | PydanticUndefined | ❌ | Ordered list of permitted JWT audiences. Provide as JSON array via AUTH_AUDIENCE environment variable; comma-separated strings are accepted when instantiating Settings directly. |
| `AUTH_KEY_SECRET_NAME` | `str | None` | None | ❌ | Secret-manager key/path storing keyset JSON when backend=secret-manager. |
| `AUTH_KEY_STORAGE_BACKEND` | `str` | file | ❌ | Key storage backend (file or secret-manager). |
| `AUTH_KEY_STORAGE_PATH` | `str` | var/keys/keyset.json | ❌ | Filesystem path for keyset JSON when using file backend. |
| `DATABASE_ECHO` | `bool` | False | ❌ | Enable SQLAlchemy engine echo for debugging |
| `DATABASE_HEALTH_TIMEOUT` | `float` | 5.0 | ❌ | Timeout for database health checks (seconds) |
| `DATABASE_MAX_OVERFLOW` | `int` | 10 | ❌ | Maximum overflow connections for the SQLAlchemy pool |
| `DATABASE_POOL_RECYCLE` | `int` | 1800 | ❌ | Seconds before recycling idle connections |
| `DATABASE_POOL_SIZE` | `int` | 5 | ❌ | SQLAlchemy async pool size |
| `DATABASE_POOL_TIMEOUT` | `float` | 30.0 | ❌ | Seconds to wait for a connection from the pool |
| `JWT_ALGORITHM` | `str` | HS256 | ❌ | JWT algorithm |
| `LOG_LEVEL` | `str` | INFO | ❌ | Logging level |

## Rate limiting

| Env Var | Type | Default | Wizard? | Description |
| --- | --- | --- | --- | --- |
| `BILLING_STREAM_CONCURRENT_LIMIT` | `int` | 3 | ❌ | Simultaneous billing stream connections allowed per tenant. |
| `BILLING_STREAM_RATE_LIMIT_PER_MINUTE` | `int` | 20 | ❌ | Maximum billing stream subscriptions allowed per tenant per minute. |
| `CHAT_RATE_LIMIT_PER_MINUTE` | `int` | 60 | ❌ | Maximum chat completions allowed per user per minute. |
| `CHAT_STREAM_CONCURRENT_LIMIT` | `int` | 5 | ❌ | Simultaneous streaming chat sessions allowed per user. |
| `CHAT_STREAM_RATE_LIMIT_PER_MINUTE` | `int` | 30 | ❌ | Maximum streaming chat sessions started per user per minute. |
| `RATE_LIMIT_KEY_PREFIX` | `str` | rate-limit | ❌ | Redis key namespace used by the rate limiter service. |
## Secrets providers

| Env Var | Type | Default | Wizard? | Description |
| --- | --- | --- | --- | --- |
| `SECRETS_PROVIDER` | `str` | vault_dev | ❌ | Active secrets implementation (`vault_dev`, `vault_hcp`, `infisical_cloud`, `infisical_self_host`, `aws_sm`, `azure_kv`). |
| `VAULT_NAMESPACE` | `str | None` | None | ❌ | Optional Vault namespace when using HCP or multi-tenant clusters. |
| `INFISICAL_BASE_URL` | `str | None` | None | ❌ | Base URL for Infisical API when using Infisical providers. |
| `INFISICAL_SERVICE_TOKEN` | `str | None` | None | ❌ | Infisical service token used for non-interactive secret access. |
| `INFISICAL_PROJECT_ID` | `str | None` | None | ❌ | Infisical project/workspace identifier tied to this deployment. |
| `INFISICAL_ENVIRONMENT` | `str | None` | None | ❌ | Infisical environment slug (dev/staging/prod) queried for secrets. |
| `INFISICAL_SECRET_PATH` | `str | None` | None | ❌ | Secret path (e.g., `/backend`) to read when seeding environment values. |
| `INFISICAL_CA_BUNDLE_PATH` | `str | None` | None | ❌ | Custom CA bundle path for self-hosted Infisical instances. |
| `INFISICAL_SIGNING_SECRET_NAME` | `str` | auth-service-signing-secret | ❌ | Infisical secret name holding the signing key used for service-account payloads. |
| `INFISICAL_CACHE_TTL_SECONDS` | `int` | 60 | ❌ | TTL (seconds) for Infisical secret cache entries. |
| `AWS_REGION` | `str | None` | None | ❌ | AWS region used for Secrets Manager operations. |
| `AWS_PROFILE` | `str | None` | None | ❌ | Named AWS profile to load when using credentials from ~/.aws. |
| `AWS_ACCESS_KEY_ID` | `str | None` | None | ❌ | Static AWS access key ID (used when not relying on profiles/IMDS). |
| `AWS_SECRET_ACCESS_KEY` | `str | None` | None | ❌ | Static AWS secret access key corresponding to the configured access key ID. |
| `AWS_SESSION_TOKEN` | `str | None` | None | ❌ | Optional AWS session token for temporary credentials. |
| `AWS_SM_SIGNING_SECRET_ARN` | `str | None` | None | ❌ | ARN or name of the Secrets Manager secret containing the signing secret value. |
| `AWS_SM_CACHE_TTL_SECONDS` | `int` | 60 | ❌ | TTL (seconds) for cached AWS Secrets Manager lookups. |
| `AZURE_KEY_VAULT_URL` | `str | None` | None | ❌ | Azure Key Vault base URL (https://<name>.vault.azure.net). |
| `AZURE_KV_SIGNING_SECRET_NAME` | `str | None` | None | ❌ | Key Vault secret name that stores the signing secret value. |
| `AZURE_TENANT_ID` | `str | None` | None | ❌ | Azure AD tenant ID used for service principal authentication. |
| `AZURE_CLIENT_ID` | `str | None` | None | ❌ | Azure AD application (client) ID used for Key Vault access. |
| `AZURE_CLIENT_SECRET` | `str | None` | None | ❌ | Azure AD application secret used when authenticating via client credentials. |
| `AZURE_MANAGED_IDENTITY_CLIENT_ID` | `str | None` | None | ❌ | User-assigned managed identity client ID for MSI authentication. |
| `AZURE_KV_CACHE_TTL_SECONDS` | `int` | 60 | ❌ | TTL (seconds) for cached Azure Key Vault secret reads. |
| `ENABLE_SECRETS_PROVIDER_TELEMETRY` | `bool` | False | ❌ | Emit structured telemetry about selected secrets providers (no payload contents). |


## Vault

| Env Var | Type | Default | Wizard? | Description |
| --- | --- | --- | --- | --- |
| `VAULT_ADDR` | `str | None` | None | ✅ | HashiCorp Vault address for Transit verification. |
| `VAULT_TOKEN` | `str | None` | None | ✅ | Vault token/AppRole secret with transit:verify capability. |
| `VAULT_TRANSIT_KEY` | `str` | auth-service | ✅ | Transit key name used for signing/verification. |
| `VAULT_VERIFY_ENABLED` | `bool` | False | ✅ | When true, enforce Vault Transit verification for service-account issuance. |
