## packages/starter_console/tests

| Name | Purpose | Location | Required | Default | Format | Sensitivity |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ALLOW_ANON_FRONTEND_LOGS` | Toggles anonymous frontend log ingestion. | `unit/api/test_frontend_logs_route.py` | Optional | `False` | Bool | Config |
| `ALLOW_PUBLIC_SIGNUP` | **Legacy** toggle for public registration (replaced by `SIGNUP_ACCESS_POLICY`). | `unit/config/test_config.py` | Optional | `False` | Bool | Config |
| `ALLOWED_HOSTS` | Trusted hosts for the application. | `unit/config/test_config.py` | Optional | `localhost`, `127.0.0.1` | CSV String | Config |
| `ALLOWED_ORIGINS` | CORS allowed origins. | `unit/config/test_config.py` | Optional | `http://localhost:3000`... | CSV String | Config |
| `AUTH_AUDIENCE` | Expected audience claim in JWTs. | `unit/config/test_config.py` | Optional | List of services | JSON/CSV | Config |
| `AUTH_CACHE_REDIS_URL` | Redis URL for authentication caching. | `conftest.py`, `unit/config/test_config.py` | Optional | `redis_url` | Redis URL | Config |
| `AUTH_DUAL_SIGNING_ENABLED` | Toggles dual signing for key rotation support. | `conftest.py` | Optional | `False` | Bool | Config |
| `AUTH_JWKS_ETAG_SALT` | Salt used for JWKS ETag generation. | `conftest.py` | Optional | None | String | Secret |
| `AUTH_JWKS_MAX_AGE_SECONDS` | Cache duration for JWKS endpoints. | `conftest.py` | Optional | `300` | Int | Config |
| `AUTH_KEY_SECRET_NAME` | Name/Path of the secret in the provider (e.g., Vault path). | `unit/config/test_config.py` | Conditional | None | String | Config |
| `AUTH_KEY_STORAGE_BACKEND` | Storage backend for auth keys (`file` or `secret-manager`). | `conftest.py`, `unit/config/test_config.py` | Optional | `file` (dev) | String | Config |
| `AUTH_KEY_STORAGE_PATH` | File path for auth keys when backend is `file`. | `conftest.py` | Conditional | `keyset.json` | Path | Config |
| `AUTH_KEY_STORAGE_PROVIDER` | Provider for secret manager backend (e.g. `vault`). | `unit/config/test_config.py` | Conditional | None | String | Config |
| `AUTH_PASSWORD_PEPPER` | Secret pepper for password hashing. | `conftest.py`, `unit/config/test_secret_guard.py` | Required | Placeholder (dev) | String | Secret |
| `AUTH_REFRESH_TOKEN_PEPPER` | Secret pepper for refresh token hashing. | `conftest.py`, `unit/config/test_secret_guard.py` | Required | Placeholder (dev) | String | Secret |
| `AUTO_RUN_MIGRATIONS` | Whether to apply DB migrations on startup. | `conftest.py`, `contract/__init__.py` | Optional | `false` | Bool | Config |
| `BILLING_EVENTS_REDIS_URL` | Redis URL for billing event streams. | `unit/config/test_config.py` | Optional | `redis_url` | Redis URL | Config |
| `DATABASE_URL` | Connection string for the primary database. | `conftest.py`, `integration/test_postgres_migrations.py` | Required | None | Database URL | Secret |
| `DEBUG` | Toggles debug mode (verbose logging, auto-reload). | `unit/config/test_config.py` | Optional | `False` | Bool | Config |
| `DISABLE_PROVIDER_CONVERSATION_CREATION` | Disables upstream provider conversation syncing. | `unit/agents/service/test_agent_service_provider_conversations.py` | Optional | `False` | Bool | Config |
| `ENABLE_ACTIVITY_STREAM` | Toggles the user activity event stream. | `contract/test_activity_api.py` | Optional | `False` | Bool | Config |
| `ENABLE_BILLING` | Master toggle for billing features. | `conftest.py`, `unit/config/test_provider_validation.py` | Optional | `False` | Bool | Config |
| `ENABLE_BILLING_STREAM` | Toggles the SSE billing event stream. | `contract/test_openapi_contract.py` | Optional | `False` | Bool | Config |
| `ENABLE_FRONTEND_LOG_INGEST` | Toggles the frontend log ingestion endpoint. | `contract/test_openapi_contract.py` | Optional | `False` | Bool | Config |
| `ENABLE_USAGE_GUARDRAILS` | Toggles usage quota enforcement. | `conftest.py`, `utils/contract_env.py` | Optional | `False` | Bool | Config |
| `ENVIRONMENT` | Deployment environment (e.g., `production`, `development`). | `unit/config/test_config.py` | Optional | `development` | String | Config |
| `FRONTEND_LOG_SHARED_SECRET` | Shared secret for signing frontend logs. | `unit/api/test_frontend_logs_route.py` | Conditional | None | String | Secret |
| `GCP_SM_PROJECT_ID` | GCP Project ID for Secret Manager. | `unit/integrations/providers/gcp/test_gcp_provider.py` | Conditional | None | String | Config |
| `GCP_SM_SIGNING_SECRET_NAME` | Name of the signing secret in GCP Secret Manager. | `unit/integrations/providers/gcp/test_gcp_provider.py` | Conditional | None | String | Config |
| `LOG_ROOT` | Root directory for log files. | `unit/observability/test_logging.py` | Optional | `./var/log` | Path | Config |
| `LOGGING_DATADOG_API_KEY` | API Key for Datadog log sink. | `unit/observability/test_logging.py` | Conditional | None | String | Secret |
| `LOGGING_DUPLEX_ERROR_FILE` | If true, writes errors to a separate file even if stdout is enabled. | `unit/observability/test_logging.py` | Optional | `False` | Bool | Config |
| `LOGGING_FILE_BACKUPS` | Number of rotated log files to keep. | `unit/observability/test_logging.py` | Optional | `7` | Int | Config |
| `LOGGING_FILE_MAX_MB` | Max size of a log file before rotation. | `unit/observability/test_logging.py` | Optional | `10` | Int | Config |
| `LOGGING_FILE_PATH` | Specific path for a single log file (overrides daily rotation). | `unit/observability/test_logging.py` | Optional | None | Path | Config |
| `LOGGING_MAX_DAYS` | Max age in days for daily log directories. | `unit/observability/test_logging.py` | Optional | `30` | Int | Config |
| `LOGGING_OTLP_ENDPOINT` | HTTP endpoint for OTLP log export. | `integration/test_observability_collector.py` | Conditional | None | URL | Config |
| `LOGGING_SINKS` | Comma-separated list of log destinations (e.g., `stdout,file`). | `unit/observability/test_logging.py` | Optional | `stdout` | CSV String | Config |
| `MCP_TOOLS` | JSON configuration for Model Context Protocol tools. | `unit/config/test_settings_mcp.py` | Optional | `[]` | JSON | Config |
| `OPENAI_AGENTS_DISABLE_TRACING` | Disables internal tracing in the OpenAI Agents SDK. | `conftest.py`, `contract/test_openapi_contract.py` | Optional | `false` | Bool | Config |
| `OPENAI_API_KEY` | OpenAI API Key. | `conftest.py`, `unit/config/test_provider_validation.py` | Required | None | String | Secret |
| `RATE_LIMIT_REDIS_URL` | Redis URL for rate limiting. | `conftest.py`, `unit/config/test_config.py` | Optional | `redis_url` | Redis URL | Config |
| `REDIS_URL` | Primary Redis connection string. | `conftest.py` | Required | None | Redis URL | Secret |
| `RESEND_API_KEY` | API Key for Resend email delivery. | `unit/config/test_provider_validation.py` | Conditional | None | String | Secret |
| `RESEND_DEFAULT_FROM` | Default sender email address. | `unit/config/test_provider_validation.py` | Conditional | None | Email | Config |
| `RESEND_EMAIL_ENABLED` | Toggles Resend email integration. | `unit/notifications/test_contact_service.py` | Optional | `False` | Bool | Config |
| `SECRET_KEY` | Flask/FastAPI session secret key (legacy support). | `unit/config/test_secret_guard.py` | Required | Placeholder (dev) | String | Secret |
| `SECURITY_TOKEN_REDIS_URL` | Redis URL for security token storage (nonces, etc). | `conftest.py`, `unit/config/test_config.py` | Optional | `redis_url` | Redis URL | Config |
| `SIGNUP_ACCESS_POLICY` | Controls user registration (`public`, `invite_only`, `approval`). | `contract/test_auth_signup_register.py` | Optional | `invite_only` | String | Config |
| `SIGNUP_CONCURRENT_REQUESTS_LIMIT` | Max pending signup requests allowed per IP. | `unit/config/test_config.py` | Optional | `3` | Int | Config |
| `SIGNUP_RATE_LIMIT_PER_DAY` | Global signup rate limit per day. | `unit/config/test_config.py` | Optional | `100` | Int | Config |
| `SIGNUP_RATE_LIMIT_PER_DOMAIN_DAY` | Signup rate limit per email domain per day. | `unit/config/test_config.py` | Optional | `20` | Int | Config |
| `SIGNUP_RATE_LIMIT_PER_EMAIL_DAY` | Signup rate limit per email address per day. | `unit/config/test_config.py` | Optional | `3` | Int | Config |
| `SIGNUP_RATE_LIMIT_PER_HOUR` | Global signup rate limit per hour. | `unit/api/test_rate_limit_helpers.py` | Optional | `20` | Int | Config |
| `SIGNUP_RATE_LIMIT_PER_IP_DAY` | Signup rate limit per IP address per day. | `unit/config/test_config.py` | Optional | `20` | Int | Config |
| `STARTER_CONSOLE_SKIP_ENV` | Skips loading `.env` in the starter console (dev tool). | `conftest.py` | Optional | `false` | Bool | Config |
| `STARTER_CONSOLE_SKIP_VAULT_PROBE` | Skips Vault connectivity checks in the starter console. | `conftest.py` | Optional | `false` | Bool | Config |
| `STRIPE_PRODUCT_PRICE_MAP` | Map of plan codes to Stripe Price IDs (e.g. `starter=price_123`). | `unit/config/test_config.py` | Conditional | None | Map/String | Config |
| `STRIPE_SECRET_KEY` | Stripe API Secret Key. | `utils/contract_env.py` | Conditional | None | String | Secret |
| `STRIPE_WEBHOOK_SECRET` | Stripe Webhook Signing Secret. | `integration/test_stripe_webhook.py` | Conditional | None | String | Secret |
| `USAGE_GUARDRAIL_REDIS_URL` | Redis URL for usage counters/guardrails. | `conftest.py`, `utils/contract_env.py` | Optional | `redis_url` | Redis URL | Config |
| `USE_TEST_FIXTURES` | Enables the test fixture seeding endpoints (unsafe for prod). | `unit/api/test_test_fixture_router.py` | Optional | `false` | Bool | Config |
| `VAULT_ADDR` | HashiCorp Vault Address. | `unit/config/test_config.py` | Conditional | None | URL | Config |
| `VAULT_TOKEN` | HashiCorp Vault Token. | `unit/config/test_config.py` | Conditional | None | String | Secret |
| `VAULT_TRANSIT_KEY` | Vault Transit engine key name. | `unit/config/test_config.py` | Conditional | None | String | Config |
| `VAULT_VERIFY_ENABLED` | Toggles Vault signature verification. | `unit/config/test_config.py` | Optional | `False` | Bool | Config |

### Test Configuration
These variables are used exclusively within the `smoke/`, `manual/`, and `integration/` test directories to configure the test runner clients or environment.

| Name | Purpose | Location | Default |
| :--- | :--- | :--- | :--- |
| `DEV_USER_EMAIL` | Default email for manual test login. | `manual/test_code_interpreter_manual.py` | `dev@example.com` |
| `DEV_USER_PASSWORD` | Default password for manual test login. | `manual/test_code_interpreter_manual.py` | None |
| `FILE_SEARCH_LOCAL_FILE` | Local file path for file search upload test. | `manual/test_file_search_manual.py` | `utils/test.pdf` |
| `MANUAL_ACCESS_TOKEN` | Pre-supplied token for manual tests. | `manual/test_code_interpreter_manual.py` | None |
| `MANUAL_AGENT` | Agent key override for manual tests. | `manual/test_reasoning_summary_manual.py` | `triage` |
| `MANUAL_MESSAGE` | Custom prompt message for manual tests. | `manual/test_function_tool_manual.py` | Varies |
| `MANUAL_RECORD_STREAM_TO` | File path to record manual test SSE stream output. | `manual/test_code_interpreter_manual.py` | None |
| `MANUAL_TENANT_ID` | Pre-supplied tenant ID for manual tests. | `manual/test_code_interpreter_manual.py` | None |
| `MANUAL_TIMEOUT` | HTTP timeout for manual tests (seconds). | `manual/test_code_interpreter_manual.py` | `60` |
| `NEXT_PUBLIC_API_URL` | Base API URL for manual tests. | `manual/test_code_interpreter_manual.py` | `http://localhost:8000` |
| `PORT` | Fallback port if API URL is unset. | `manual/test_code_interpreter_manual.py` | `8000` |
| `SMOKE_BASE_URL` | Base URL for smoke tests. | `smoke/http/config.py` | `http://localhost:8000` |
| `SMOKE_CONVERSATION_KEY` | Key for smoke test seed conversation. | `smoke/http/config.py` | `seeded-smoke-convo` |
| `SMOKE_ENABLE_ACTIVITY_STREAM` | Enable activity stream smoke tests. | `smoke/http/config.py` | `False` |
| `SMOKE_ENABLE_AI` | Enable AI chat/workflow smoke tests. | `smoke/http/config.py` | `False` |
| `SMOKE_ENABLE_ASSETS` | Enable asset management smoke tests. | `smoke/http/config.py` | `False` |
| `SMOKE_ENABLE_AUTH_EXTENDED` | Enable extended auth (password change/reset) tests. | `smoke/http/config.py` | `False` |
| `SMOKE_ENABLE_AUTH_MFA` | Enable MFA flow smoke tests. | `smoke/http/config.py` | `False` |
| `SMOKE_ENABLE_AUTH_SIGNUP` | Enable signup flow smoke tests. | `smoke/http/config.py` | `False` |
| `SMOKE_ENABLE_AUTH_SSO` | Enable SSO flow smoke tests. | `smoke/http/config.py` | `False` |
| `SMOKE_ENABLE_BILLING` | Enable billing smoke tests. | `smoke/http/config.py` | `False` |
| `SMOKE_ENABLE_BILLING_STREAM` | Enable billing SSE stream smoke tests. | `smoke/http/config.py` | `False` |
| `SMOKE_ENABLE_CONTACT` | Enable contact form smoke tests. | `smoke/http/config.py` | `False` |
| `SMOKE_ENABLE_CONTAINERS` | Enable container management smoke tests. | `smoke/http/config.py` | `False` |
| `SMOKE_ENABLE_OPENAI_FILES` | Enable OpenAI file proxy smoke tests. | `smoke/http/config.py` | `False` |
| `SMOKE_ENABLE_SERVICE_ACCOUNTS` | Enable service account smoke tests. | `smoke/http/config.py` | `False` |
| `SMOKE_ENABLE_STATUS_SUBSCRIPTIONS` | Enable status subscription smoke tests. | `smoke/http/config.py` | `False` |
| `SMOKE_ENABLE_VECTOR` | Enable vector store smoke tests. | `smoke/http/config.py` | `False` |
| `SMOKE_HTTP_TIMEOUT` | HTTP request timeout for smoke tests. | `smoke/http/config.py` | `10` |
| `SMOKE_MFA_EMAIL` | Email for MFA test user. | `smoke/http/config.py` | `smoke-mfa@example.com` |
| `SMOKE_OPENAI_FILE_ID` | Existing OpenAI file ID for download tests. | `smoke/http/config.py` | None |
| `SMOKE_OPERATOR_EMAIL` | Email for platform operator test user. | `smoke/http/config.py` | `smoke-operator@example.com` |
| `SMOKE_PASSWORD_CHANGE_EMAIL` | Email for password change test user. | `smoke/http/config.py` | `smoke-password-change@example.com` |
| `SMOKE_PASSWORD_RESET_EMAIL` | Email for password reset test user. | `smoke/http/config.py` | `smoke-password-reset@example.com` |
| `SMOKE_SSO_PROVIDER` | SSO provider key for smoke tests. | `smoke/http/config.py` | `google` |
| `SMOKE_TENANT_NAME` | Name for smoke test tenant. | `smoke/http/config.py` | `Smoke Test Tenant` |
| `SMOKE_TENANT_SLUG` | Slug for smoke test tenant. | `smoke/http/config.py` | `smoke` |
| `SMOKE_UNVERIFIED_EMAIL` | Email for unverified test user. | `smoke/http/config.py` | `smoke-unverified@example.com` |
| `SMOKE_USER_EMAIL` | Admin email for smoke tests. | `smoke/http/config.py` | `smoke-admin@example.com` |
| `SMOKE_USER_PASSWORD` | Password for smoke test users. | `smoke/http/config.py` | `SmokeAdmin!234` |
| `STARTER_OTLP_RECEIVE_TIMEOUT_SECONDS` | Timeout for OTLP collector tests. | `integration/test_observability_collector.py` | `10` |
| `USE_REAL_POSTGRES` | Toggles Postgres integration tests. | `integration/test_postgres_migrations.py` | `false` |