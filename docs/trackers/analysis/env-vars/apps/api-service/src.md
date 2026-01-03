## apps/api-service/src

| Variable Name | Purpose | Location | Required | Default | Format | Sensitivity |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ACTIVITY_EVENTS_CLEANUP_BATCH` | Batch size for activity event cleanup jobs | `app/core/settings/retention.py` | No | 10000 | Integer | Config |
| `ACTIVITY_EVENTS_CLEANUP_SLEEP_MS` | Sleep time between activity cleanup batches (milliseconds) | `app/core/settings/retention.py` | No | 0 | Integer | Config |
| `ACTIVITY_EVENTS_REDIS_URL` | Redis URL for activity event streaming (defaults to `REDIS_URL`) | `app/core/settings/activity.py` | No | `None` | URL | Sensitive |
| `ACTIVITY_EVENTS_TTL_DAYS` | Retention period for activity events | `app/core/settings/retention.py` | No | 365 | Integer | Config |
| `ACTIVITY_STREAM_MAX_LENGTH` | Maximum length of Redis stream for activity events | `app/core/settings/activity.py` | No | 2048 | Integer | Config |
| `ACTIVITY_STREAM_TTL_SECONDS` | TTL for activity stream keys | `app/core/settings/activity.py` | No | 86400 | Integer | Config |
| `AGENT_MODEL_CODE` | Override model for code assistant agent | `app/core/settings/ai.py` | No | `None` | String | Config |
| `AGENT_MODEL_DATA` | Override model for data analyst agent | `app/core/settings/ai.py` | No | `None` | String | Config |
| `AGENT_MODEL_DEFAULT` | Default model for agents | `app/core/settings/ai.py` | No | `gpt-5.1` | String | Config |
| `AGENT_MODEL_TRIAGE` | Override model for triage agent | `app/core/settings/ai.py` | No | `None` | String | Config |
| `ALLOW_ANON_FRONTEND_LOGS` | Allow anonymous frontend log ingestion | `app/core/settings/observability.py` | No | `False` | Bool | Config |
| `ALLOW_OPENAI_CONVERSATION_UUID_FALLBACK` | Policy flag for agent runtime conversation ID handling | `app/services/agents/policy.py` (via `os.getenv`) | No | `False` | Bool | Config |
| `ALLOW_PUBLIC_SIGNUP` | Enable public registration (overridden by `SIGNUP_ACCESS_POLICY` logic) | `app/core/settings/signup.py` | No | `True` | Bool | Config |
| `ALLOW_SIGNUP_TRIAL_OVERRIDE` | Allow callers to request specific trial periods during signup | `app/core/settings/signup.py` | No | `False` | Bool | Config |
| `ALLOWED_HEADERS` | CORS allowed headers | `app/core/settings/application.py` | No | `*` | String (CSV) | Config |
| `ALLOWED_HOSTS` | Trusted hosts for middleware | `app/core/settings/application.py` | No | `localhost,...` | String (CSV) | Config |
| `ALLOWED_METHODS` | CORS allowed methods | `app/core/settings/application.py` | No | `GET,POST...` | String (CSV) | Config |
| `ALLOWED_ORIGINS` | CORS allowed origins | `app/core/settings/application.py` | No | `http://localhost...` | String (CSV) | Config |
| `ANTHROPIC_API_KEY` | API key for Anthropic models | `app/core/settings/ai.py` | No | `None` | String | Secret |
| `APP_DESCRIPTION` | API service description | `app/core/settings/application.py` | No | `api-service...` | String | Config |
| `APP_NAME` | API service name | `app/core/settings/application.py` | No | `api-service` | String | Config |
| `APP_PUBLIC_URL` | Base URL for generating public links | `app/core/settings/application.py` | No | `http://localhost:3000` | URL | Config |
| `APP_VERSION` | API service version | `app/core/settings/application.py` | No | `1.0.0` | String | Config |
| `AUTH_AUDIENCE` | Permitted JWT audiences | `app/core/settings/security.py` | No | `[...]` | JSON Array or CSV | Config |
| `AUTH_CACHE_REDIS_URL` | Redis URL for auth caching (defaults to `REDIS_URL`) | `app/core/settings/redis.py` | No | `None` | URL | Sensitive |
| `AUTH_EMAIL_VERIFICATION_TOKEN_PEPPER` | Pepper for hashing email verification tokens | `app/core/settings/security.py` | No | `local-email...` | String | Secret |
| `AUTH_IP_LOCKOUT_DURATION_MINUTES` | Duration IP is blocked after threshold breach | `app/core/settings/security.py` | No | 10 | Integer | Config |
| `AUTH_IP_LOCKOUT_THRESHOLD` | Max failed logins per IP/subnet per window | `app/core/settings/security.py` | No | 50 | Integer | Config |
| `AUTH_IP_LOCKOUT_WINDOW_MINUTES` | Rolling window for IP throttling | `app/core/settings/security.py` | No | 10 | Integer | Config |
| `AUTH_JWKS_CACHE_SECONDS` | Cache duration for JWKS | `app/core/settings/security.py` | No | 300 | Integer | Config |
| `AUTH_JWKS_ETAG_SALT` | Salt for JWKS ETag generation | `app/core/settings/security.py` | No | `local-jwks...` | String | Secret |
| `AUTH_JWKS_MAX_AGE_SECONDS` | `Cache-Control` max-age for JWKS | `app/core/settings/security.py` | No | 300 | Integer | Config |
| `AUTH_KEY_SECRET_NAME` | Name of secret in secret manager storing keyset | `app/core/settings/security.py` | Conditional | `None` | String | Config |
| `AUTH_KEY_STORAGE_BACKEND` | Storage backend for keys (`file` or `secret-manager`) | `app/core/settings/security.py` | No | `file` | String | Config |
| `AUTH_KEY_STORAGE_PATH` | File path for keyset (if using file backend) | `app/core/settings/security.py` | No | `var/keys...` | Path | Config |
| `AUTH_KEY_STORAGE_PROVIDER` | Secret provider for key storage (if using secret-manager) | `app/core/settings/security.py` | Conditional | `None` | String | Config |
| `AUTH_LOCKOUT_DURATION_MINUTES` | Unlock window for locked user accounts | `app/core/settings/security.py` | No | 60.0 | Float | Config |
| `AUTH_LOCKOUT_THRESHOLD` | Failed login attempts before user lockout | `app/core/settings/security.py` | No | 5 | Integer | Config |
| `AUTH_LOCKOUT_WINDOW_MINUTES` | Rolling window for user lockout calculation | `app/core/settings/security.py` | No | 60.0 | Float | Config |
| `AUTH_PASSWORD_HISTORY_COUNT` | Number of past passwords to retain | `app/core/settings/security.py` | No | 5 | Integer | Config |
| `AUTH_PASSWORD_PEPPER` | Pepper for password hashing | `app/core/settings/security.py` | No | `local-dev...` | String | Secret |
| `AUTH_PASSWORD_RESET_TOKEN_PEPPER` | Pepper for hashing password reset tokens | `app/core/settings/security.py` | No | `local-reset...` | String | Secret |
| `AUTH_REFRESH_TOKEN_PEPPER` | Pepper for hashing refresh tokens | `app/core/settings/security.py` | No | `local-dev...` | String | Secret |
| `AUTH_REFRESH_TOKEN_TTL_MINUTES` | Lifetime of refresh tokens | `app/core/settings/security.py` | No | 43200 | Integer | Config |
| `AUTH_SESSION_ENCRYPTION_KEY` | Key for encrypting session IP metadata | `app/core/settings/security.py` | No | `None` | String | Secret |
| `AUTH_SESSION_IP_HASH_SALT` | Salt for session IP hashing (defaults to SECRET_KEY) | `app/core/settings/security.py` | No | `None` | String | Secret |
| `AUTO_CREATE_VECTOR_STORE_FOR_FILE_SEARCH` | Automatically create vector stores for tenants | `app/core/settings/ai.py` | No | `True` | Bool | Config |
| `AUTO_PURGE_EXPIRED_VECTOR_STORES` | Delete expired vector stores remotely | `app/core/settings/ai.py` | No | `False` | Bool | Config |
| `AUTO_RUN_MIGRATIONS` | Run DB migrations on startup | `app/core/settings/database.py` | No | `False` | Bool | Config |
| `AWS_ACCESS_KEY_ID` | AWS Access Key | `app/core/settings/providers.py` | No | `None` | String | Secret |
| `AWS_PROFILE` | AWS CLI profile name | `app/core/settings/providers.py` | No | `None` | String | Config |
| `AWS_REGION` | AWS Region | `app/core/settings/providers.py` | Conditional | `None` | String | Config |
| `AWS_SECRET_ACCESS_KEY` | AWS Secret Key | `app/core/settings/providers.py` | No | `None` | String | Secret |
| `AWS_SESSION_TOKEN` | AWS Session Token | `app/core/settings/providers.py` | No | `None` | String | Secret |
| `AWS_SM_CACHE_TTL_SECONDS` | Cache TTL for AWS Secrets Manager | `app/core/settings/providers.py` | No | 60 | Integer | Config |
| `AWS_SM_SIGNING_SECRET_ARN` | ARN of signing secret in AWS Secrets Manager | `app/core/settings/providers.py` | Conditional | `None` | String | Config |
| `AZURE_BLOB_ACCOUNT_URL` | Azure Blob Storage account URL | `app/core/settings/storage.py` | Conditional | `None` | URL | Config |
| `AZURE_BLOB_CONNECTION_STRING` | Azure Blob Storage connection string | `app/core/settings/storage.py` | Conditional | `None` | String | Secret |
| `AZURE_BLOB_CONTAINER` | Azure Blob container name | `app/core/settings/storage.py` | Conditional | `None` | String | Config |
| `AZURE_CLIENT_ID` | Azure Client ID | `app/core/settings/providers.py` | No | `None` | String | Config |
| `AZURE_CLIENT_SECRET` | Azure Client Secret | `app/core/settings/providers.py` | No | `None` | String | Secret |
| `AZURE_KEY_VAULT_URL` | Azure Key Vault URL | `app/core/settings/providers.py` | Conditional | `None` | URL | Config |
| `AZURE_KV_CACHE_TTL_SECONDS` | Cache TTL for Azure Key Vault | `app/core/settings/providers.py` | No | 60 | Integer | Config |
| `AZURE_KV_SIGNING_SECRET_NAME` | Name of signing secret in Key Vault | `app/core/settings/providers.py` | Conditional | `None` | String | Config |
| `AZURE_MANAGED_IDENTITY_CLIENT_ID` | Azure Managed Identity Client ID | `app/core/settings/providers.py` | No | `None` | String | Config |
| `AZURE_TENANT_ID` | Azure Tenant ID | `app/core/settings/providers.py` | No | `None` | String | Config |
| `BILLING_EVENTS_REDIS_URL` | Redis URL for billing events (defaults to `REDIS_URL`) | `app/core/settings/database.py` | No | `None` | URL | Sensitive |
| `BILLING_RETRY_DEPLOYMENT_MODE` | Deployment mode for Stripe retry worker | `app/core/settings/database.py` | No | `inline` | String | Config |
| `BILLING_STREAM_CONCURRENT_LIMIT` | Concurrent billing stream limit per tenant | `app/core/settings/rate_limits.py` | No | 3 | Integer | Config |
| `BILLING_STREAM_RATE_LIMIT_PER_MINUTE` | Billing stream rate limit per tenant | `app/core/settings/rate_limits.py` | No | 20 | Integer | Config |
| `CHAT_RATE_LIMIT_PER_MINUTE` | Chat completion rate limit | `app/core/settings/rate_limits.py` | No | 60 | Integer | Config |
| `CHAT_STREAM_CONCURRENT_LIMIT` | Concurrent chat stream limit | `app/core/settings/rate_limits.py` | No | 5 | Integer | Config |
| `CHAT_STREAM_RATE_LIMIT_PER_MINUTE` | Chat stream rate limit | `app/core/settings/rate_limits.py` | No | 30 | Integer | Config |
| `CONTACT_EMAIL_EMAIL_RATE_LIMIT_PER_HOUR` | Contact form limit per email address | `app/core/settings/security.py` | No | 3 | Integer | Config |
| `CONTACT_EMAIL_IP_RATE_LIMIT_PER_HOUR` | Contact form limit per IP | `app/core/settings/security.py` | No | 20 | Integer | Config |
| `CONTACT_EMAIL_SUBJECT_PREFIX` | Prefix for contact emails | `app/core/settings/security.py` | No | `[Contact]` | String | Config |
| `CONTACT_EMAIL_TEMPLATE_ID` | Resend template ID for contact emails | `app/core/settings/security.py` | No | `None` | String | Config |
| `CONTACT_EMAIL_TO` | Recipients for contact form submissions | `app/core/settings/security.py` | No | `support@...` | CSV or JSON | Config |
| `CONTAINER_ALLOWED_MEMORY_TIERS` | Allowed memory tiers for code interpreter | `app/core/settings/ai.py` | No | `[...]` | JSON/List | Config |
| `CONTAINER_DEFAULT_AUTO_MEMORY` | Default memory for code interpreter containers | `app/core/settings/ai.py` | No | `1g` | String | Config |
| `CONTAINER_FALLBACK_TO_AUTO_ON_MISSING_BINDING` | Fallback behavior for container bindings | `app/core/settings/ai.py` | No | `True` | Bool | Config |
| `CONTAINER_MAX_CONTAINERS_PER_TENANT` | Container limit per tenant | `app/core/settings/ai.py` | No | 10 | Integer | Config |
| `DATABASE_ECHO` | Enable SQLAlchemy echo | `app/core/settings/database.py` | No | `False` | Bool | Config |
| `DATABASE_HEALTH_TIMEOUT` | DB health check timeout | `app/core/settings/database.py` | No | 5.0 | Float | Config |
| `DATABASE_MAX_OVERFLOW` | SQLAlchemy pool overflow | `app/core/settings/database.py` | No | 10 | Integer | Config |
| `DATABASE_POOL_RECYCLE` | SQLAlchemy pool recycle time | `app/core/settings/database.py` | No | 1800 | Integer | Config |
| `DATABASE_POOL_SIZE` | SQLAlchemy pool size | `app/core/settings/database.py` | No | 5 | Integer | Config |
| `DATABASE_POOL_TIMEOUT` | SQLAlchemy pool timeout | `app/core/settings/database.py` | No | 30.0 | Float | Config |
| `DATABASE_URL` | Database connection string | `app/core/settings/database.py` | Conditional | `None` | URL | Sensitive |
| `DEBUG` | Enable debug mode | `app/core/settings/application.py` | No | `False` | Bool | Config |
| `DISABLE_PROVIDER_CONVERSATION_CREATION` | Policy flag to disable provider conversation usage | `app/services/agents/policy.py` (via `os.getenv`) | No | `False` | Bool | Config |
| `EMAIL_VERIFICATION_EMAIL_RATE_LIMIT_PER_HOUR` | Verification email limit per account | `app/core/settings/security.py` | No | 3 | Integer | Config |
| `EMAIL_VERIFICATION_IP_RATE_LIMIT_PER_HOUR` | Verification email limit per IP | `app/core/settings/security.py` | No | 10 | Integer | Config |
| `EMAIL_VERIFICATION_TOKEN_TTL_MINUTES` | Verification token lifetime | `app/core/settings/security.py` | No | 60 | Integer | Config |
| `ENABLE_ACTIVITY_STREAM` | Enable activity streaming | `app/core/settings/activity.py` | No | `False` | Bool | Config |
| `ENABLE_BILLING` | Enable billing features | `app/core/settings/database.py` | No | `False` | Bool | Config |
| `ENABLE_BILLING_RETRY_WORKER` | Enable Stripe dispatch retry worker | `app/core/settings/database.py` | No | `True` | Bool | Config |
| `ENABLE_BILLING_STREAM` | Enable billing event streaming | `app/core/settings/database.py` | No | `False` | Bool | Config |
| `ENABLE_BILLING_STREAM_REPLAY` | Replay billing events on startup | `app/core/settings/database.py` | No | `True` | Bool | Config |
| `ENABLE_FRONTEND_LOG_INGEST` | Enable frontend log ingestion endpoint | `app/core/settings/observability.py` | No | `False` | Bool | Config |
| `ENABLE_SECRETS_PROVIDER_TELEMETRY` | Emit secrets provider telemetry | `app/core/settings/providers.py` | No | `False` | Bool | Config |
| `ENABLE_SLACK_STATUS_NOTIFICATIONS` | Enable Slack status alerts | `app/core/settings/integrations.py` | No | `False` | Bool | Config |
| `ENABLE_USAGE_GUARDRAILS` | Enable usage limit enforcement | `app/core/settings/usage.py` | No | `False` | Bool | Config |
| `ENABLE_VECTOR_STORE_SYNC_WORKER` | Enable vector store sync background worker | `app/core/settings/ai.py` | No | `True` | Bool | Config |
| `ENVIRONMENT` | Deployment environment name | `app/core/settings/application.py` | No | `development` | String | Config |
| `FORCE_PROVIDER_SESSION_REBIND` | Policy flag to force provider session rebinding | `app/services/agents/policy.py` (via `os.getenv`) | No | `False` | Bool | Config |
| `FRONTEND_LOG_SHARED_SECRET` | Shared secret for anonymous frontend logs | `app/core/settings/observability.py` | No | `None` | String | Secret |
| `GCS_BUCKET` | Google Cloud Storage bucket | `app/core/settings/storage.py` | Conditional | `None` | String | Config |
| `GCS_CREDENTIALS_JSON` | GCS Credentials JSON content | `app/core/settings/storage.py` | No | `None` | JSON | Secret |
| `GCS_CREDENTIALS_PATH` | Path to GCS credentials file | `app/core/settings/storage.py` | No | `None` | Path | Config |
| `GCS_PROJECT_ID` | GCP Project ID | `app/core/settings/storage.py` | Conditional | `None` | String | Config |
| `GCS_SIGNING_EMAIL` | GCS Service Account Email for signing | `app/core/settings/storage.py` | No | `None` | String | Config |
| `GCS_SM_CACHE_TTL_SECONDS` | Cache TTL for GCP Secret Manager | `app/core/settings/providers.py` | No | 60 | Integer | Config |
| `GCS_SM_PROJECT_ID` | GCP Project ID for Secret Manager | `app/core/settings/providers.py` | Conditional | `None` | String | Config |
| `GCS_SM_SIGNING_SECRET_NAME` | Name of signing secret in GCP Secret Manager | `app/core/settings/providers.py` | Conditional | `None` | String | Config |
| `GCS_UNIFORM_ACCESS` | Use uniform bucket-level access | `app/core/settings/storage.py` | No | `True` | Bool | Config |
| `GEMINI_API_KEY` | Google Gemini API key | `app/core/settings/ai.py` | No | `None` | String | Secret |
| `GEOIP_CACHE_MAX_ENTRIES` | Max entries in GeoIP cache | `app/core/settings/observability.py` | No | 4096 | Integer | Config |
| `GEOIP_CACHE_TTL_SECONDS` | GeoIP cache TTL | `app/core/settings/observability.py` | No | 900.0 | Float | Config |
| `GEOIP_HTTP_TIMEOUT_SECONDS` | Timeout for GeoIP APIs | `app/core/settings/observability.py` | No | 2.0 | Float | Config |
| `GEOIP_IP2LOCATION_API_KEY` | API Key for IP2Location | `app/core/settings/observability.py` | Conditional | `None` | String | Secret |
| `GEOIP_IP2LOCATION_DB_PATH` | Path to IP2Location DB | `app/core/settings/observability.py` | Conditional | `None` | Path | Config |
| `GEOIP_IPINFO_TOKEN` | Token for IPinfo | `app/core/settings/observability.py` | Conditional | `None` | String | Secret |
| `GEOIP_MAXMIND_DB_PATH` | Path to MaxMind DB | `app/core/settings/observability.py` | Conditional | `None` | Path | Config |
| `GEOIP_MAXMIND_LICENSE_KEY` | License key for MaxMind | `app/core/settings/observability.py` | No | `None` | String | Secret |
| `GEOIP_PROVIDER` | GeoIP provider selection | `app/core/settings/observability.py` | No | `none` | String | Config |
| `HOST` | Server host binding | `run.py` (via `os.getenv`) | No | `127.0.0.1` | String | Config |
| `IMAGE_ALLOWED_FORMATS` | Allowed image formats | `app/core/settings/ai.py` | No | `[...]` | List | Config |
| `IMAGE_DEFAULT_BACKGROUND` | Default image background setting | `app/core/settings/ai.py` | No | `auto` | String | Config |
| `IMAGE_DEFAULT_COMPRESSION` | Default image compression level | `app/core/settings/ai.py` | No | `None` | Integer | Config |
| `IMAGE_DEFAULT_FORMAT` | Default image format | `app/core/settings/ai.py` | No | `png` | String | Config |
| `IMAGE_DEFAULT_QUALITY` | Default image quality | `app/core/settings/ai.py` | No | `high` | String | Config |
| `IMAGE_DEFAULT_SIZE` | Default image size | `app/core/settings/ai.py` | No | `1024x1024` | String | Config |
| `IMAGE_MAX_PARTIAL_IMAGES` | Max partial images for streaming | `app/core/settings/ai.py` | No | 3 | Integer | Config |
| `IMAGE_OUTPUT_MAX_MB` | Max size for image outputs | `app/core/settings/ai.py` | No | 6 | Integer | Config |
| `INFISICAL_BASE_URL` | Infisical API URL | `app/core/settings/providers.py` | Conditional | `None` | URL | Config |
| `INFISICAL_CACHE_TTL_SECONDS` | Cache TTL for Infisical secrets | `app/core/settings/providers.py` | No | 60 | Integer | Config |
| `INFISICAL_CA_BUNDLE_PATH` | Path to CA bundle for Infisical | `app/core/settings/providers.py` | No | `None` | Path | Config |
| `INFISICAL_ENVIRONMENT` | Infisical environment slug | `app/core/settings/providers.py` | Conditional | `None` | String | Config |
| `INFISICAL_PROJECT_ID` | Infisical project ID | `app/core/settings/providers.py` | Conditional | `None` | String | Config |
| `INFISICAL_SECRET_PATH` | Path to secrets in Infisical | `app/core/settings/providers.py` | No | `None` | String | Config |
| `INFISICAL_SERVICE_TOKEN` | Infisical service token | `app/core/settings/providers.py` | Conditional | `None` | String | Secret |
| `INFISICAL_SIGNING_SECRET_NAME` | Name of signing secret in Infisical | `app/core/settings/providers.py` | No | `...` | String | Config |
| `JWT_ALGORITHM` | Algorithm for JWT signing | `app/core/settings/security.py` | No | `HS256` | String | Config |
| `LOG_LEVEL` | Application logging level | `app/core/settings/application.py` | No | `INFO` | String | Config |
| `LOG_ROOT` | Base directory for logs | `app/core/settings/observability.py` | No | `None` | Path | Config |
| `LOGGING_DATADOG_API_KEY` | Datadog API key | `app/core/settings/observability.py` | Conditional | `None` | String | Secret |
| `LOGGING_DATADOG_SITE` | Datadog site | `app/core/settings/observability.py` | No | `datadoghq.com` | String | Config |
| `LOGGING_DUPLEX_ERROR_FILE` | Write errors to file even if stdout enabled | `app/core/settings/observability.py` | No | `False` | Bool | Config |
| `LOGGING_FILE_BACKUPS` | Number of log file backups | `app/core/settings/observability.py` | No | 5 | Integer | Config |
| `LOGGING_FILE_MAX_MB` | Max size of log files | `app/core/settings/observability.py` | No | 10 | Integer | Config |
| `LOGGING_FILE_PATH` | Path for log file | `app/core/settings/observability.py` | No | `...` | Path | Config |
| `LOGGING_MAX_DAYS` | Max days to keep logs | `app/core/settings/observability.py` | No | 0 | Integer | Config |
| `LOGGING_OTLP_ENDPOINT` | OTLP logging endpoint | `app/core/settings/observability.py` | Conditional | `None` | URL | Config |
| `LOGGING_OTLP_HEADERS` | OTLP logging headers | `app/core/settings/observability.py` | No | `None` | JSON | Config |
| `LOGGING_SINKS` | Logging sinks configuration | `app/core/settings/observability.py` | No | `stdout` | CSV | Config |
| `MCP_TOOLS` | Hosted MCP tool configuration | `app/core/settings/mcp.py` | No | `[]` | JSON | Config |
| `MFA_CHALLENGE_TTL_MINUTES` | TTL for MFA challenges | `app/core/settings/security.py` | No | 5 | Integer | Config |
| `MFA_VERIFY_RATE_LIMIT_PER_HOUR` | MFA verification attempt limit | `app/core/settings/security.py` | No | 10 | Integer | Config |
| `MINIO_ACCESS_KEY` | MinIO Access Key | `app/core/settings/storage.py` | Conditional | `None` | String | Secret |
| `MINIO_ENDPOINT` | MinIO Endpoint URL | `app/core/settings/storage.py` | Conditional | `None` | URL | Config |
| `MINIO_REGION` | MinIO Region | `app/core/settings/storage.py` | No | `None` | String | Config |
| `MINIO_SECRET_KEY` | MinIO Secret Key | `app/core/settings/storage.py` | Conditional | `None` | String | Secret |
| `MINIO_SECURE` | Use SSL for MinIO | `app/core/settings/storage.py` | No | `True` | Bool | Config |
| `OPENAI_API_KEY` | OpenAI API Key | `app/core/settings/ai.py` | No | `None` | String | Secret |
| `PASSWORD_RESET_EMAIL_RATE_LIMIT_PER_HOUR` | Password reset email limit per account | `app/core/settings/security.py` | No | 5 | Integer | Config |
| `PASSWORD_RESET_IP_RATE_LIMIT_PER_HOUR` | Password reset email limit per IP | `app/core/settings/security.py` | No | 20 | Integer | Config |
| `PASSWORD_RESET_TOKEN_TTL_MINUTES` | Password reset token lifetime | `app/core/settings/security.py` | No | 30 | Integer | Config |
| `PORT` | Server port | `app/core/settings/application.py` | No | 8000 | Integer | Config |
| `RATE_LIMIT_KEY_PREFIX` | Redis prefix for rate limiting | `app/core/settings/rate_limits.py` | No | `rate-limit` | String | Config |
| `RATE_LIMIT_REDIS_URL` | Redis URL for rate limiting (defaults to `REDIS_URL`) | `app/core/settings/redis.py` | No | `None` | URL | Sensitive |
| `REDIS_URL` | Primary Redis URL | `app/core/settings/redis.py` | No | `redis://...` | URL | Sensitive |
| `RELOAD` | Enable server reload | `run.py` (via `os.getenv`) | No | `true` | Bool | Config |
| `REQUIRE_EMAIL_VERIFICATION` | Enforce email verification | `app/core/settings/security.py` | No | `True` | Bool | Config |
| `RESEND_API_KEY` | Resend API Key | `app/core/settings/security.py` | Conditional | `None` | String | Secret |
| `RESEND_BASE_URL` | Resend API Base URL | `app/core/settings/security.py` | No | `https://api.resend.com` | URL | Config |
| `RESEND_DEFAULT_FROM` | Default From address for Resend | `app/core/settings/security.py` | Conditional | `None` | String | Config |
| `RESEND_EMAIL_ENABLED` | Enable Resend for emails | `app/core/settings/security.py` | No | `False` | Bool | Config |
| `RESEND_EMAIL_VERIFICATION_TEMPLATE_ID` | Resend template for verification emails | `app/core/settings/security.py` | No | `None` | String | Config |
| `RESEND_PASSWORD_RESET_TEMPLATE_ID` | Resend template for password reset emails | `app/core/settings/security.py` | No | `None` | String | Config |
| `RUN_EVENTS_CLEANUP_BATCH` | Batch size for run event cleanup | `app/core/settings/retention.py` | No | 10000 | Integer | Config |
| `RUN_EVENTS_CLEANUP_SLEEP_MS` | Sleep time between run event cleanup batches | `app/core/settings/retention.py` | No | 0 | Integer | Config |
| `RUN_EVENTS_TTL_DAYS` | Retention period for run events | `app/core/settings/retention.py` | No | 180 | Integer | Config |
| `S3_BUCKET` | S3 Bucket Name | `app/core/settings/storage.py` | Conditional | `None` | String | Config |
| `S3_ENDPOINT_URL` | Custom S3 Endpoint URL | `app/core/settings/storage.py` | No | `None` | URL | Config |
| `S3_FORCE_PATH_STYLE` | Force path-style addressing for S3 | `app/core/settings/storage.py` | No | `False` | Bool | Config |
| `S3_REGION` | AWS Region for S3 | `app/core/settings/storage.py` | No | `None` | String | Config |
| `SECRET_KEY` | Primary application secret key | `app/core/settings/security.py` | No | `...` | String | Secret |
| `SECRETS_PROVIDER` | Secrets provider backend | `app/core/settings/providers.py` | No | `vault_dev` | String | Config |
| `SECURITY_TOKEN_REDIS_URL` | Redis URL for security tokens (defaults to `REDIS_URL`) | `app/core/settings/redis.py` | No | `None` | URL | Sensitive |
| `SIGNUP_ACCESS_POLICY` | Signup policy (`public`, `invite_only`, `approval`) | `app/core/settings/signup.py` | No | `invite_only` | String | Config |
| `SIGNUP_CONCURRENT_REQUESTS_LIMIT` | Max pending signup requests per IP | `app/core/settings/signup.py` | No | 3 | Integer | Config |
| `SIGNUP_DEFAULT_PLAN_CODE` | Default billing plan for new tenants | `app/core/settings/signup.py` | No | `starter` | String | Config |
| `SIGNUP_DEFAULT_TRIAL_DAYS` | Default trial days for new tenants | `app/core/settings/signup.py` | No | 14 | Integer | Config |
| `SIGNUP_INVITE_RESERVATION_TTL_SECONDS` | TTL for signup invite reservations | `app/core/settings/signup.py` | No | 900 | Integer | Config |
| `SIGNUP_RATE_LIMIT_PER_DOMAIN_DAY` | Signup limit per email domain | `app/core/settings/signup.py` | No | 20 | Integer | Config |
| `SIGNUP_RATE_LIMIT_PER_EMAIL_DAY` | Signup limit per email address | `app/core/settings/signup.py` | No | 3 | Integer | Config |
| `SIGNUP_RATE_LIMIT_PER_HOUR` | Signup limit per IP (hourly) | `app/core/settings/signup.py` | No | 20 | Integer | Config |
| `SIGNUP_RATE_LIMIT_PER_IP_DAY` | Signup limit per IP (daily) | `app/core/settings/signup.py` | No | 100 | Integer | Config |
| `SLACK_API_BASE_URL` | Slack API base URL | `app/core/settings/integrations.py` | No | `...` | URL | Config |
| `SLACK_HTTP_TIMEOUT_SECONDS` | Slack API timeout | `app/core/settings/integrations.py` | No | 5.0 | Float | Config |
| `SLACK_STATUS_BOT_TOKEN` | Slack Bot Token | `app/core/settings/integrations.py` | Conditional | `None` | String | Secret |
| `SLACK_STATUS_DEFAULT_CHANNELS` | Default Slack channels for notifications | `app/core/settings/integrations.py` | Conditional | `[]` | List/CSV | Config |
| `SLACK_STATUS_MAX_RETRIES` | Max retries for Slack notifications | `app/core/settings/integrations.py` | No | 3 | Integer | Config |
| `SLACK_STATUS_RATE_LIMIT_WINDOW_SECONDS` | Rate limit window for Slack notifications | `app/core/settings/integrations.py` | No | 1.0 | Float | Config |
| `SLACK_STATUS_TENANT_CHANNEL_MAP` | Map of tenant IDs to Slack channels | `app/core/settings/integrations.py` | No | `{}` | JSON | Config |
| `SSO_CALLBACK_RATE_LIMIT_PER_MINUTE` | SSO callback rate limit | `app/core/settings/security.py` | No | 30 | Integer | Config |
| `SSO_CLIENT_SECRET_ENCRYPTION_KEY` | Key for encrypting SSO client secrets | `app/core/settings/sso.py` | No | `None` | String | Secret |
| `SSO_CLOCK_SKEW_SECONDS` | Clock skew tolerance for SSO tokens | `app/core/settings/sso.py` | No | 60 | Integer | Config |
| `SSO_START_RATE_LIMIT_PER_MINUTE` | SSO start rate limit | `app/core/settings/security.py` | No | 30 | Integer | Config |
| `SSO_STATE_TTL_MINUTES` | TTL for SSO state | `app/core/settings/sso.py` | No | 10 | Integer | Config |
| `STATUS_SUBSCRIPTION_EMAIL_RATE_LIMIT_PER_HOUR` | Status email sub limit | `app/core/settings/security.py` | No | 5 | Integer | Config |
| `STATUS_SUBSCRIPTION_ENCRYPTION_KEY` | Encryption key for status subs | `app/core/settings/security.py` | No | `None` | String | Secret |
| `STATUS_SUBSCRIPTION_IP_RATE_LIMIT_PER_HOUR` | Status IP sub limit | `app/core/settings/security.py` | No | 20 | Integer | Config |
| `STATUS_SUBSCRIPTION_TOKEN_PEPPER` | Pepper for status sub tokens | `app/core/settings/security.py` | No | `...` | String | Secret |
| `STATUS_SUBSCRIPTION_TOKEN_TTL_MINUTES` | TTL for status sub tokens | `app/core/settings/security.py` | No | 60 | Integer | Config |
| `STATUS_SUBSCRIPTION_WEBHOOK_TIMEOUT_SECONDS` | Timeout for status webhooks | `app/core/settings/security.py` | No | 5 | Integer | Config |
| `STORAGE_ALLOWED_MIME_TYPES` | Allowed MIME types for storage | `app/core/settings/storage.py` | No | `[...]` | List | Config |
| `STORAGE_BUCKET_PREFIX` | Prefix for storage buckets | `app/core/settings/storage.py` | No | `agent-data` | String | Config |
| `STORAGE_MAX_FILE_MB` | Max file size for storage | `app/core/settings/storage.py` | No | 512 | Integer | Config |
| `STORAGE_PROVIDER` | Storage backend provider | `app/core/settings/storage.py` | No | `memory` | String | Config |
| `STORAGE_SIGNED_URL_TTL_SECONDS` | TTL for presigned URLs | `app/core/settings/storage.py` | No | 900 | Integer | Config |
| `STRIPE_PORTAL_RETURN_URL` | Return URL for Stripe portal | `app/core/settings/database.py` | No | `None` | URL | Config |
| `STRIPE_PRODUCT_PRICE_MAP` | Map of plans to Stripe prices | `app/core/settings/database.py` | Conditional | `{}` | JSON/CSV | Config |
| `STRIPE_SECRET_KEY` | Stripe Secret Key | `app/core/settings/database.py` | Conditional | `None` | String | Secret |
| `STRIPE_WEBHOOK_SECRET` | Stripe Webhook Signing Secret | `app/core/settings/database.py` | Conditional | `None` | String | Secret |
| `TENANT_DEFAULT_SLUG` | Default tenant slug | `app/core/settings/signup.py` | No | `default` | String | Config |
| `USAGE_GUARDRAIL_CACHE_BACKEND` | Cache backend for usage guardrails | `app/core/settings/usage.py` | No | `redis` | String | Config |
| `USAGE_GUARDRAIL_CACHE_TTL_SECONDS` | TTL for usage guardrail cache | `app/core/settings/usage.py` | No | 30 | Integer | Config |
| `USAGE_GUARDRAIL_REDIS_URL` | Redis URL for usage guardrails (defaults to `REDIS_URL`) | `app/core/settings/redis.py` | No | `None` | URL | Sensitive |
| `USAGE_GUARDRAIL_SOFT_LIMIT_MODE` | Enforcement mode for soft limits | `app/core/settings/usage.py` | No | `warn` | String | Config |
| `USE_TEST_FIXTURES` | Enable test fixture endpoints | `app/core/settings/application.py` | No | `False` | Bool | Config |
| `VAULT_ADDR` | HashiCorp Vault Address | `app/core/settings/providers.py` | Conditional | `None` | URL | Config |
| `VAULT_NAMESPACE` | HashiCorp Vault Namespace | `app/core/settings/providers.py` | No | `None` | String | Config |
| `VAULT_TOKEN` | HashiCorp Vault Token | `app/core/settings/providers.py` | Conditional | `None` | String | Secret |
| `VAULT_TRANSIT_KEY` | Vault Transit Key Name | `app/core/settings/providers.py` | Conditional | `auth-service` | String | Config |
| `VAULT_VERIFY_ENABLED` | Enforce Vault signature verification | `app/core/settings/providers.py` | No | `False` | Bool | Config |
| `VECTOR_ALLOWED_MIME_TYPES` | Allowed MIME types for vector stores | `app/core/settings/ai.py` | No | `[...]` | List | Config |
| `VECTOR_MAX_FILE_MB` | Max file size for vector stores | `app/core/settings/ai.py` | No | 512 | Integer | Config |
| `VECTOR_MAX_FILES_PER_STORE` | Max files per vector store | `app/core/settings/ai.py` | No | 5000 | Integer | Config |
| `VECTOR_MAX_STORES_PER_TENANT` | Max vector stores per tenant | `app/core/settings/ai.py` | No | 10 | Integer | Config |
| `VECTOR_MAX_TOTAL_BYTES` | Max total bytes for vector stores | `app/core/settings/ai.py` | No | `None` | Integer | Config |
| `VECTOR_STORE_SYNC_BATCH_SIZE` | Batch size for vector store sync | `app/core/settings/ai.py` | No | 20 | Integer | Config |
| `VECTOR_STORE_SYNC_POLL_SECONDS` | Poll interval for vector store sync | `app/core/settings/ai.py` | No | 60.0 | Float | Config |
| `WORKERS` | Number of Uvicorn workers | `run.py` (via `os.getenv`) | No | 1 | Integer | Config |
| `WORKFLOW_MIN_PURGE_AGE_HOURS` | Minimum age for hard deleting workflows | `app/core/settings/retention.py` | No | 0 | Integer | Config |
| `XAI_API_KEY` | xAI API Key | `app/core/settings/ai.py` | No | `None` | String | Secret |


## apps/api-service/scripts

| Name | Purpose | Used in (File:Line) | Required? | Default | Format | Sensitivity |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ALLOW_PUBLIC_SIGNUP` | Configures public signup availability for the smoke test environment. | `smoke_http.sh`:15 | Optional | `true` | boolean (string) | Config |
| `AUTH_CACHE_REDIS_URL` | Redis connection string for auth caching. | `smoke_http.sh`:11 | Optional | `$REDIS_URL` | URL | Secret |
| `AUTH_KEY_STORAGE_PATH` | File path for authentication key storage during tests. | `smoke_http.sh`:50 | Optional | `.../test_keyset.json` | File path | Config |
| `AUTO_RUN_MIGRATIONS` | Controls whether migrations run automatically during smoke tests. | `smoke_http.sh`:5 | Optional | `true` | boolean (string) | Config |
| `DATABASE_ECHO` | Controls SQLAlchemy SQL logging to stdout. | `seed_dev_user.py`:155<br>`seed_sso_provider.py`:338<br>`sso_status.py`:155<br>`stripe_dispatch.py`:144 | Optional (Set by script) | `false` (in scripts) | boolean (string) | Config |
| `DATABASE_URL` | Database connection string. | `check_alembic_version.py`:88, 62<br>`smoke_http.sh`:8 | **Required** (Python)<br>Optional (Shell) | `sqlite+aiosqlite:///...` (Shell) | URL | Secret |
| `DEBUG` | Enables debug mode for the application/tests. | `smoke_http.sh`:7 | Optional | `false` | boolean (string) | Config |
| `ENABLE_BILLING` | Toggles billing features. | `smoke_http.sh`:13<br>`export_openapi.py`:57 | Optional | `false` | boolean (string) | Config |
| `ENABLE_BILLING_RETRY_WORKER` | Toggles the billing retry worker. | `smoke_http.sh`:14 | Optional | `false` | boolean (string) | Config |
| `ENABLE_FRONTEND_LOG_INGEST` | Toggles frontend log ingestion. | `smoke_http.sh`:16 | Optional | `true` | boolean (string) | Config |
| `ENABLE_RESEND_EMAIL_DELIVERY` | Toggles email delivery via Resend. | `smoke_http.sh`:15 | Optional | `false` | boolean (string) | Config |
| `OPENAI_API_KEY` | API key for OpenAI services. | `smoke_http.sh`:17 | Optional | `dummy-smoke-key` | String | Key |
| `POSTGRES_DB` | Used to validate that the `DATABASE_URL` matches the expected Postgres database name. | `check_alembic_version.py`:61 | Optional | `""` | String | Config |
| `RATE_LIMIT_REDIS_URL` | Redis connection string for rate limiting. | `smoke_http.sh`:10 | Optional | `$REDIS_URL` | URL | Secret |
| `REDIS_URL` | Primary Redis connection string. | `smoke_http.sh`:9 | Optional | `redis://localhost:6379/0` | URL | Secret |
| `SECURITY_TOKEN_REDIS_URL` | Redis connection string for security tokens. | `smoke_http.sh`:12 | Optional | `$REDIS_URL` | URL | Secret |
| `SHELL` | Specifies the shell executable to use within the virtual environment. | `enter.sh`:30 | Optional | `/bin/bash` | File path | Config |
| `SMOKE_BASE_URL` | Base URL for the API service during smoke tests. | `smoke_http.sh`:20 | Optional | `http://localhost:8000` | URL | Config |
| `SMOKE_ENABLE_AI` | Toggles AI features specifically for smoke tests. | `smoke_http.sh`:22 | Optional | `0` | int/bool | Config |
| `SMOKE_ENABLE_BILLING` | Toggles billing features specifically for smoke tests. | `smoke_http.sh`:21 | Optional | `0` | int/bool | Config |
| `SMOKE_ENABLE_CONTAINERS` | Toggles container features specifically for smoke tests. | `smoke_http.sh`:24 | Optional | `0` | int/bool | Config |
| `SMOKE_ENABLE_VECTOR` | Toggles vector features specifically for smoke tests. | `smoke_http.sh`:23 | Optional | `0` | int/bool | Config |
| `SMOKE_USE_STUB_PROVIDER` | Toggles the use of a stub provider during smoke tests. | `smoke_http.sh`:25 | Optional | `1` | int/bool | Config |
| `STARTER_CONSOLE_SKIP_ENV` | Skips environment checks in the starter console. | `smoke_http.sh`:18 | Optional | `true` | boolean (string) | Config |
| `STARTER_CONSOLE_SKIP_VAULT_PROBE` | Skips Vault probing in the starter console. | `smoke_http.sh`:19 | Optional | `true` | boolean (string) | Config |
| `USAGE_GUARDRAIL_REDIS_URL` | Redis connection string for usage guardrails. | `smoke_http.sh`:13 | Optional | `$REDIS_URL` | URL | Secret |
| `USE_TEST_FIXTURES` | Enables the use of test fixtures (data seeding). | `smoke_http.sh`:4<br>`export_openapi.py`:59 | Optional | `true` | boolean (string) | Config |