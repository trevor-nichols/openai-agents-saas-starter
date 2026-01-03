## packages/starter_console

| Name | Purpose | Location | Required | Default | Format | Sensitivity |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime in minutes. | `src/starter_console/workflows/setup/_wizard/sections/security.py` | Optional | 30 | Integer | Config |
| `AGENT_ALLOW_INSECURE_COOKIES` | Allow insecure cookies in Next.js (dev/demo). | `src/starter_console/workflows/setup/_wizard/sections/frontend.py` | Optional | false | Boolean | Config |
| `AGENT_FORCE_SECURE_COOKIES` | Force secure cookies in Next.js. | `src/starter_console/workflows/setup/_wizard/sections/frontend.py` | Optional | true | Boolean | Config |
| `NEXT_PUBLIC_AGENT_API_MOCK` | Client + server flag to enable mock API mode. | `src/starter_console/workflows/setup/_wizard/sections/frontend.py` | Optional | false | Boolean | Config |
| `ALLOWED_HEADERS` | Comma-separated list of allowed HTTP headers. | `src/starter_console/workflows/setup/_wizard/sections/core.py` | Optional | * | String (CSV) | Config |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hostnames. | `src/starter_console/workflows/setup/_wizard/sections/core.py` | Required | localhost... | String (CSV) | Config |
| `ALLOWED_METHODS` | Comma-separated list of allowed HTTP methods. | `src/starter_console/workflows/setup/_wizard/sections/core.py` | Optional | GET,POST... | String (CSV) | Config |
| `ALLOWED_ORIGINS` | Comma-separated list of allowed CORS origins. | `src/starter_console/workflows/setup/_wizard/sections/core.py` | Required | http://localhost... | String (CSV) | Config |
| `ALLOW_SIGNUP_TRIAL_OVERRIDE` | Allow clients to request custom trial lengths. | `src/starter_console/workflows/setup/_wizard/sections/signup.py` | Optional | false | Boolean | Config |
| `ANTHROPIC_API_KEY` | API key for Anthropic models. | `src/starter_console/workflows/setup/_wizard/sections/providers/ai.py` | Optional | - | String | Secret |
| `API_BASE_URL` | Base URL of the backend API. | `src/starter_console/workflows/setup/_wizard/sections/core.py` | Required | http://127.0.0.1:8000 | URL | Config |
| `APP_DESCRIPTION` | Application description for docs/metadata. | `src/starter_console/workflows/setup/_wizard/sections/core.py` | Optional | api-service... | String | Config |
| `APP_NAME` | Application display name. | `src/starter_console/workflows/setup/_wizard/sections/core.py` | Optional | api-service | String | Config |
| `APP_PUBLIC_URL` | Public base URL of the frontend application. | `src/starter_console/workflows/setup/_wizard/sections/core.py` | Required | http://localhost:3000 | URL | Config |
| `APP_VERSION` | Application version string. | `src/starter_console/workflows/setup/_wizard/sections/core.py` | Optional | 1.0.0 | String | Config |
| `AUTH_AUDIENCE` | JWT audience(s). | `src/starter_console/workflows/setup/_wizard/sections/core.py` | Required | agent-api... | CSV or JSON array | Config |
| `AUTH_CACHE_REDIS_URL` | Redis URL for auth/session caching. | `src/starter_console/workflows/setup/_wizard/sections/providers/redis.py` | Optional | - | Redis URL | Secret |
| `AUTH_CLI_DEV_AUTH_MODE` | Development auth mode override (e.g. `demo`). | `src/starter_console/services/auth/security/signing.py` | Optional | vault | String | Config |
| `AUTH_CLI_OUTPUT` | Default output format for auth CLI commands. | `src/starter_console/services/auth/tokens.py` | Optional | json | json/text/env | Config |
| `AUTH_EMAIL_VERIFICATION_TOKEN_PEPPER` | Pepper for email verification tokens. | `src/starter_console/workflows/setup/_wizard/sections/secrets.py` | Required | - | String | Secret |
| `AUTH_IP_LOCKOUT_DURATION_MINUTES` | Duration of IP lockout in minutes. | `src/starter_console/workflows/setup/_wizard/sections/security.py` | Optional | 10 | Integer | Config |
| `AUTH_IP_LOCKOUT_THRESHOLD` | Failed attempts before IP lockout. | `src/starter_console/workflows/setup/_wizard/sections/security.py` | Optional | 50 | Integer | Config |
| `AUTH_IP_LOCKOUT_WINDOW_MINUTES` | Window for counting IP failures in minutes. | `src/starter_console/workflows/setup/_wizard/sections/security.py` | Optional | 10 | Integer | Config |
| `AUTH_JWKS_CACHE_SECONDS` | Cache duration for JWKS. | `src/starter_console/workflows/setup/_wizard/sections/security.py` | Optional | 300 | Integer | Config |
| `AUTH_JWKS_ETAG_SALT` | Salt for generating JWKS ETags. | `src/starter_console/workflows/setup/_wizard/sections/security.py` | Optional | - | String | Secret |
| `AUTH_JWKS_MAX_AGE_SECONDS` | JWKS Cache-Control max-age. | `src/starter_console/workflows/setup/_wizard/sections/security.py` | Optional | 300 | Integer | Config |
| `AUTH_KEY_SECRET_NAME` | Secret name in external manager for signing keys. | `src/starter_console/workflows/setup/_wizard/sections/core.py` | Optional | - | String | Config |
| `AUTH_KEY_STORAGE_BACKEND` | Key storage backend type (`file` or `secret-manager`). | `src/starter_console/workflows/setup/_wizard/sections/core.py` | Required | file | String | Config |
| `AUTH_KEY_STORAGE_PATH` | File path for local key storage. | `src/starter_console/workflows/setup/_wizard/sections/core.py` | Optional | var/keys/keyset.json | Path | Config |
| `AUTH_KEY_STORAGE_PROVIDER` | Provider for secret-manager key storage. | `src/starter_console/workflows/setup/_wizard/sections/core.py` | Optional | - | String | Config |
| `AUTH_LOCKOUT_DURATION_MINUTES` | Duration of user lockout in minutes. | `src/starter_console/workflows/setup/_wizard/sections/security.py` | Optional | 60 | Integer | Config |
| `AUTH_LOCKOUT_THRESHOLD` | Failed attempts before user lockout. | `src/starter_console/workflows/setup/_wizard/sections/security.py` | Optional | 5 | Integer | Config |
| `AUTH_LOCKOUT_WINDOW_MINUTES` | Window for counting user failures in minutes. | `src/starter_console/workflows/setup/_wizard/sections/security.py` | Optional | 60 | Integer | Config |
| `AUTH_PASSWORD_HISTORY_COUNT` | Number of previous passwords to remember. | `src/starter_console/workflows/setup/_wizard/sections/security.py` | Optional | 5 | Integer | Config |
| `AUTH_PASSWORD_PEPPER` | Pepper for password hashing. | `src/starter_console/workflows/setup/_wizard/sections/secrets.py` | Required | - | String | Secret |
| `AUTH_PASSWORD_RESET_TOKEN_PEPPER` | Pepper for password reset tokens. | `src/starter_console/workflows/setup/_wizard/sections/secrets.py` | Required | - | String | Secret |
| `AUTH_REFRESH_TOKEN_PEPPER` | Pepper for refresh tokens. | `src/starter_console/workflows/setup/_wizard/sections/secrets.py` | Required | - | String | Secret |
| `AUTH_REFRESH_TOKEN_TTL_MINUTES` | Refresh token lifetime in minutes. | `src/starter_console/workflows/setup/_wizard/sections/security.py` | Optional | 43200 | Integer | Config |
| `AUTH_SESSION_ENCRYPTION_KEY` | Key for encrypting session data. | `src/starter_console/workflows/setup/_wizard/sections/secrets.py` | Required | - | String | Secret |
| `AUTH_SESSION_IP_HASH_SALT` | Salt for hashing session IP addresses. | `src/starter_console/workflows/setup/_wizard/sections/secrets.py` | Optional | - | String | Secret |
| `AUTO_CREATE_VECTOR_STORE_FOR_FILE_SEARCH` | Automatically create vector stores for file search in tests. | `tests/conftest.py` | Optional | false | Boolean | Config |
| `AUTO_RUN_MIGRATIONS` | Automatically run DB migrations on startup. | `src/starter_console/workflows/setup/_wizard/sections/core.py` | Optional | false | Boolean | Config |
| `AWS_ACCESS_KEY_ID` | AWS Access Key ID. | `src/starter_console/workflows/secrets/providers/aws.py` | Optional | - | String | Secret |
| `AWS_PROFILE` | AWS CLI profile name. | `src/starter_console/workflows/secrets/providers/aws.py` | Optional | - | String | Config |
| `AWS_REGION` | AWS Region. | `src/starter_console/workflows/secrets/providers/aws.py` | Required | us-east-1 | String | Config |
| `AWS_SECRET_ACCESS_KEY` | AWS Secret Access Key. | `src/starter_console/workflows/secrets/providers/aws.py` | Optional | - | String | Secret |
| `AWS_SESSION_TOKEN` | AWS Session Token. | `src/starter_console/workflows/secrets/providers/aws.py` | Optional | - | String | Secret |
| `AWS_SM_CACHE_TTL_SECONDS` | Cache TTL for AWS Secrets Manager. | `src/starter_console/workflows/secrets/providers/aws.py` | Optional | 60 | Integer | Config |
| `AWS_SM_SIGNING_SECRET_ARN` | ARN of the signing secret in AWS SM. | `src/starter_console/workflows/secrets/providers/aws.py` | Required | - | String | Config |
| `AZURE_BLOB_ACCOUNT_URL` | Azure Blob Storage account URL. | `src/starter_console/workflows/setup/_wizard/sections/storage.py` | Required | - | URL | Config |
| `AZURE_BLOB_CONNECTION_STRING` | Azure Blob Storage connection string. | `src/starter_console/workflows/setup/_wizard/sections/storage.py` | Optional | - | String | Secret |
| `AZURE_BLOB_CONTAINER` | Azure Blob Storage container name. | `src/starter_console/workflows/setup/_wizard/sections/storage.py` | Required | - | String | Config |
| `AZURE_CLIENT_ID` | Azure Client ID. | `src/starter_console/workflows/secrets/providers/azure.py` | Optional | - | String | Config |
| `AZURE_CLIENT_SECRET` | Azure Client Secret. | `src/starter_console/workflows/secrets/providers/azure.py` | Optional | - | String | Secret |
| `AZURE_KEY_VAULT_URL` | Azure Key Vault URL. | `src/starter_console/workflows/secrets/providers/azure.py` | Required | - | URL | Config |
| `AZURE_KV_CACHE_TTL_SECONDS` | Cache TTL for Azure Key Vault secrets. | `src/starter_console/core/inventory.py` | Optional | - | Integer | Config |
| `AZURE_KV_SIGNING_SECRET_NAME` | Name of the signing secret in Key Vault. | `src/starter_console/workflows/secrets/providers/azure.py` | Required | auth-signing-secret | String | Config |
| `AZURE_MANAGED_IDENTITY_CLIENT_ID` | Managed Identity Client ID for Azure. | `src/starter_console/workflows/secrets/providers/azure.py` | Optional | - | String | Config |
| `AZURE_TENANT_ID` | Azure Tenant ID. | `src/starter_console/workflows/secrets/providers/azure.py` | Optional | - | String | Config |
| `BILLING_EVENTS_REDIS_URL` | Redis URL for billing events. | `src/starter_console/workflows/setup/_wizard/sections/providers/redis.py` | Optional | - | Redis URL | Secret |
| `BILLING_RETRY_DEPLOYMENT_MODE` | Deployment mode for billing retry worker (`inline` or `dedicated`). | `src/starter_console/workflows/setup/_wizard/sections/signup.py` | Required | - | String | Config |
| `BILLING_STREAM_CONCURRENT_LIMIT` | Max concurrent billing streams. | `src/starter_console/workflows/setup/_wizard/sections/security.py` | Optional | 3 | Integer | Config |
| `BILLING_STREAM_RATE_LIMIT_PER_MINUTE` | Rate limit for billing streams per minute. | `src/starter_console/workflows/setup/_wizard/sections/security.py` | Optional | 20 | Integer | Config |
| `CHAT_RATE_LIMIT_PER_MINUTE` | Rate limit for chat completions per minute. | `src/starter_console/workflows/setup/_wizard/sections/security.py` | Optional | 60 | Integer | Config |
| `CHAT_STREAM_CONCURRENT_LIMIT` | Max concurrent chat streams. | `src/starter_console/workflows/setup/_wizard/sections/security.py` | Optional | 5 | Integer | Config |
| `CHAT_STREAM_RATE_LIMIT_PER_MINUTE` | Rate limit for chat streams per minute. | `src/starter_console/workflows/setup/_wizard/sections/security.py` | Optional | 30 | Integer | Config |
| `COMPOSE_FILE` | Path to docker-compose file. | `src/starter_console/services/infra/stack_ops.py` | Optional | - | Path | Config |
| `COMPOSE_PROJECT_NAME` | Docker compose project name. | `tests/unit/commands/stop/test_stop_command.py` | Optional | - | String | Config |
| `CONSOLE_LOGGING_DUPLEX_ERROR_FILE` | Enable duplex error logging for console. | `src/starter_console/observability/logging.py` | Optional | false | Boolean | Config |
| `CONSOLE_LOGGING_FILE_BACKUPS` | Number of console log backups to keep. | `src/starter_console/observability/logging.py` | Optional | 5 | Integer | Config |
| `CONSOLE_LOGGING_FILE_MAX_MB` | Max size of console log file in MB. | `src/starter_console/observability/logging.py` | Optional | 10 | Integer | Config |
| `CONSOLE_LOGGING_FILE_PATH` | Path to console log file. | `src/starter_console/observability/logging.py` | Optional | var/log/starter-console.log | Path | Config |
| `CONSOLE_LOGGING_MAX_DAYS` | Max days to keep console logs. | `src/starter_console/observability/logging.py` | Optional | 0 | Integer | Config |
| `CONSOLE_LOGGING_OTLP_ENDPOINT` | OTLP endpoint for console logs. | `src/starter_console/observability/logging.py` | Optional | - | URL | Config |
| `CONSOLE_LOGGING_OTLP_HEADERS` | OTLP headers for console logs. | `src/starter_console/observability/logging.py` | Optional | - | JSON | Secret |
| `CONSOLE_LOGGING_SINKS` | Logging sinks for console (`file`, `stdout`, etc). | `src/starter_console/observability/logging.py` | Optional | file | CSV | Config |
| `CONSOLE_LOG_LEVEL` | Logging level for console. | `src/starter_console/observability/logging.py` | Optional | INFO | String | Config |
| `CONSOLE_SERVICE_NAME` | Service name for console telemetry. | `src/starter_console/observability/logging.py` | Optional | starter-console | String | Config |
| `CONSOLE_TEXTUAL_LOG_LEVEL` | Log level for Textual framework logs. | `src/starter_console/observability/logging.py` | Optional | - | String | Config |
| `DATABASE_ECHO` | Enable SQLAlchemy echo logging. | `src/starter_console/workflows/setup/_wizard/sections/core.py` | Optional | false | Boolean | Config |
| `DATABASE_HEALTH_TIMEOUT` | Database health check timeout in seconds. | `src/starter_console/workflows/setup/_wizard/sections/core.py` | Optional | 5.0 | Float | Config |
| `DATABASE_MAX_OVERFLOW` | Database pool max overflow. | `src/starter_console/workflows/setup/_wizard/sections/core.py` | Optional | 10 | Integer | Config |
| `DATABASE_POOL_RECYCLE` | Database pool recycle time in seconds. | `src/starter_console/workflows/setup/_wizard/sections/core.py` | Optional | 1800 | Integer | Config |
| `DATABASE_POOL_SIZE` | Database pool size. | `src/starter_console/workflows/setup/_wizard/sections/core.py` | Optional | 5 | Integer | Config |
| `DATABASE_POOL_TIMEOUT` | Database pool timeout in seconds. | `src/starter_console/workflows/setup/_wizard/sections/core.py` | Optional | 30.0 | Float | Config |
| `DATABASE_URL` | Postgres connection URL. | `src/starter_console/workflows/setup/_wizard/sections/providers/database.py` | Required | - | URL | Secret |
| `DEBUG` | Enable debug mode. | `src/starter_console/workflows/setup/_wizard/sections/core.py` | Optional | false | Boolean | Config |
| `EMAIL_VERIFICATION_EMAIL_RATE_LIMIT_PER_HOUR` | Verification emails per account per hour. | `src/starter_console/workflows/setup/_wizard/sections/security.py` | Optional | 3 | Integer | Config |
| `EMAIL_VERIFICATION_IP_RATE_LIMIT_PER_HOUR` | Verification emails per IP per hour. | `src/starter_console/workflows/setup/_wizard/sections/security.py` | Optional | 10 | Integer | Config |
| `EMAIL_VERIFICATION_TOKEN_TTL_MINUTES` | Email verification token lifetime. | `src/starter_console/workflows/setup/_wizard/sections/security.py` | Optional | 60 | Integer | Config |
| `ENABLE_BILLING` | Enable billing features. | `src/starter_console/workflows/setup/_wizard/sections/providers/billing.py` | Optional | false | Boolean | Config |
| `ENABLE_BILLING_RETRY_WORKER` | Enable billing retry worker. | `src/starter_console/workflows/setup/_wizard/sections/signup.py` | Optional | - | Boolean | Config |
| `ENABLE_BILLING_STREAM` | Enable billing stream via Redis. | `src/starter_console/workflows/setup/_wizard/sections/providers/billing.py` | Optional | false | Boolean | Config |
| `ENABLE_BILLING_STREAM_REPLAY` | Replay billing stream events on startup. | `src/starter_console/workflows/setup/_wizard/sections/signup.py` | Optional | true | Boolean | Config |
| `ENABLE_FRONTEND_LOG_INGEST` | Enable frontend log ingestion endpoint. | `src/starter_console/workflows/setup/_wizard/sections/observability.py` | Optional | - | Boolean | Config |
| `ENABLE_OTEL_COLLECTOR` | Enable bundled OpenTelemetry Collector. | `src/starter_console/workflows/setup/_wizard/sections/observability.py` | Optional | - | Boolean | Config |
| `ENABLE_SECRETS_PROVIDER_TELEMETRY` | Enable telemetry for secrets provider. | `src/starter_console/workflows/setup/_wizard/sections/secrets.py` | Optional | false | Boolean | Config |
| `ENABLE_SLACK_STATUS_NOTIFICATIONS` | Enable Slack notifications for status incidents. | `src/starter_console/workflows/setup/_wizard/sections/integrations.py` | Optional | false | Boolean | Config |
| `ENABLE_USAGE_GUARDRAILS` | Enable usage guardrails. | `src/starter_console/workflows/setup/_wizard/sections/usage.py` | Optional | false | Boolean | Config |
| `ENABLE_VECTOR_LIMIT_ENTITLEMENTS` | Add vector storage limits to entitlements. | `src/starter_console/workflows/setup/_wizard/sections/usage.py` | Optional | true | Boolean | Config |
| `ENABLE_VECTOR_STORE_SYNC_WORKER` | Enable vector store sync worker (tests). | `tests/conftest.py` | Optional | false | Boolean | Config |
| `ENVIRONMENT` | Deployment environment label. | `src/starter_console/workflows/setup/_wizard/sections/core.py` | Required | development | String | Config |
| `EXPECT_API_DOWN` | Suppress API probe failure in doctor. | `src/starter_console/workflows/home/doctor.py` | Optional | - | Boolean | Config |
| `EXPECT_DB_DOWN` | Suppress Database probe failure in doctor. | `src/starter_console/workflows/home/doctor.py` | Optional | - | Boolean | Config |
| `EXPECT_FRONTEND_DOWN` | Suppress Frontend probe failure in doctor. | `src/starter_console/workflows/home/doctor.py` | Optional | - | Boolean | Config |
| `EXPECT_REDIS_DOWN` | Suppress Redis probe failure in doctor. | `src/starter_console/workflows/home/doctor.py` | Optional | - | Boolean | Config |
| `GCP_SM_CACHE_TTL_SECONDS` | Cache TTL for GCP Secret Manager. | `src/starter_console/workflows/secrets/providers/gcp.py` | Optional | 60 | Integer | Config |
| `GCP_SM_PROJECT_ID` | GCP Project ID. | `src/starter_console/workflows/secrets/providers/gcp.py` | Optional | - | String | Config |
| `GCP_SM_SIGNING_SECRET_NAME` | Name of the signing secret in GCP SM. | `src/starter_console/workflows/secrets/providers/gcp.py` | Required | auth-signing-secret | String | Config |
| `GCS_BUCKET` | Google Cloud Storage bucket name. | `src/starter_console/workflows/setup/_wizard/sections/storage.py` | Required | - | String | Config |
| `GCS_CREDENTIALS_JSON` | Inline GCS credentials JSON. | `src/starter_console/workflows/setup/_wizard/sections/storage.py` | Optional | - | JSON | Secret |
| `GCS_CREDENTIALS_PATH` | Path to GCS credentials JSON file. | `src/starter_console/workflows/setup/_wizard/sections/storage.py` | Optional | - | Path | Config |
| `GCP_PROJECT_ID` | GCP project ID for GCS operations. | `src/starter_console/workflows/setup/_wizard/sections/storage.py` | Required | - | String | Config |
| `GCS_SIGNING_EMAIL` | Service account email for signed URLs. | `src/starter_console/workflows/setup/_wizard/sections/storage.py` | Optional | - | Email | Config |
| `GCS_UNIFORM_ACCESS` | Use Uniform Bucket Level Access for GCS. | `src/starter_console/workflows/setup/_wizard/sections/storage.py` | Optional | true | Boolean | Config |
| `GEMINI_API_KEY` | API key for Google Gemini. | `src/starter_console/workflows/setup/_wizard/sections/providers/ai.py` | Optional | - | String | Secret |
| `GEOIP_CACHE_MAX_ENTRIES` | Max entries in GeoIP cache. | `src/starter_console/workflows/setup/_wizard/sections/observability.py` | Optional | 4096 | Integer | Config |
| `GEOIP_CACHE_TTL_SECONDS` | TTL for GeoIP cache. | `src/starter_console/workflows/setup/_wizard/sections/observability.py` | Optional | 900 | Integer | Config |
| `GEOIP_HTTP_TIMEOUT_SECONDS` | HTTP timeout for GeoIP lookups. | `src/starter_console/workflows/setup/_wizard/sections/observability.py` | Optional | 2.0 | Float | Config |
| `GEOIP_IP2LOCATION_API_KEY` | API key for IP2Location. | `src/starter_console/workflows/setup/_wizard/sections/observability.py` | Optional | - | String | Secret |
| `GEOIP_IP2LOCATION_DB_PATH` | Path to IP2Location database file. | `src/starter_console/workflows/setup/_wizard/sections/observability.py` | Optional | var/geoip/IP2LOCATION-LITE-DB3.BIN | Path | Config |
| `GEOIP_IPINFO_TOKEN` | API token for IPinfo. | `src/starter_console/workflows/setup/_wizard/sections/observability.py` | Optional | - | String | Secret |
| `GEOIP_MAXMIND_DB_PATH` | Path to MaxMind database file. | `src/starter_console/workflows/setup/_wizard/sections/observability.py` | Optional | var/geoip/GeoLite2-City.mmdb | Path | Config |
| `GEOIP_MAXMIND_LICENSE_KEY` | License key for MaxMind. | `src/starter_console/workflows/setup/_wizard/sections/observability.py` | Optional | - | String | Secret |
| `GEOIP_PROVIDER` | GeoIP provider name. | `src/starter_console/workflows/setup/_wizard/sections/observability.py` | Required | none | String | Config |
| `IMAGE_DEFAULT_BACKGROUND` | Default image background (auto, opaque, transparent). | `src/starter_console/workflows/setup/_wizard/sections/storage.py` | Required | auto | String | Config |
| `IMAGE_DEFAULT_COMPRESSION` | Default image compression level (0-100). | `src/starter_console/workflows/setup/_wizard/sections/storage.py` | Optional | - | Integer | Config |
| `IMAGE_DEFAULT_FORMAT` | Default image format (png, jpeg, webp). | `src/starter_console/workflows/setup/_wizard/sections/storage.py` | Required | png | String | Config |
| `IMAGE_DEFAULT_QUALITY` | Default image quality (auto, low, medium, high). | `src/starter_console/workflows/setup/_wizard/sections/storage.py` | Required | high | String | Config |
| `IMAGE_DEFAULT_SIZE` | Default image size. | `src/starter_console/workflows/setup/_wizard/sections/storage.py` | Required | 1024x1024 | String | Config |
| `IMAGE_MAX_PARTIAL_IMAGES` | Max partial images to stream. | `src/starter_console/workflows/setup/_wizard/sections/storage.py` | Required | 2 | Integer | Config |
| `IMAGE_OUTPUT_MAX_MB` | Max decoded image size in MB. | `src/starter_console/workflows/setup/_wizard/sections/storage.py` | Required | 6 | Integer | Config |
| `INFISICAL_BASE_URL` | Base URL for Infisical. | `src/starter_console/workflows/secrets/providers/infisical.py` | Required | - | URL | Config |
| `INFISICAL_CACHE_TTL_SECONDS` | Cache TTL for Infisical secrets. | `src/starter_console/core/inventory.py` | Optional | - | Integer | Config |
| `INFISICAL_CA_BUNDLE_PATH` | Path to CA bundle for Infisical. | `src/starter_console/workflows/secrets/providers/infisical.py` | Optional | - | Path | Config |
| `INFISICAL_ENVIRONMENT` | Infisical environment slug. | `src/starter_console/workflows/secrets/providers/infisical.py` | Required | dev | String | Config |
| `INFISICAL_PROJECT_ID` | Infisical project/workspace ID. | `src/starter_console/workflows/secrets/providers/infisical.py` | Required | - | String | Config |
| `INFISICAL_SECRET_PATH` | Path within Infisical workspace. | `src/starter_console/workflows/secrets/providers/infisical.py` | Required | / | String | Config |
| `INFISICAL_SERVICE_TOKEN` | Infisical service token. | `src/starter_console/workflows/secrets/providers/infisical.py` | Required | - | String | Secret |
| `INFISICAL_SIGNING_SECRET_NAME` | Name of the signing secret in Infisical. | `src/starter_console/workflows/secrets/providers/infisical.py` | Required | auth-service-signing-secret | String | Config |
| `JWT_ALGORITHM` | Algorithm used for JWT signing. | `src/starter_console/workflows/setup/_wizard/sections/core.py` | Optional | HS256 | String | Config |
| `LOG_LEVEL` | Global logging level. | `src/starter_console/workflows/setup/_wizard/sections/core.py` | Optional | INFO | String | Config |
| `LOG_ROOT` | Root directory for application logs. | `src/starter_console/services/infra/ops_models.py` | Optional | var/log | Path | Config |
| `LOGGING_DATADOG_API_KEY` | Datadog API key for logs. | `src/starter_console/workflows/setup/_wizard/sections/observability.py` | Optional | - | String | Secret |
| `LOGGING_DATADOG_SITE` | Datadog site for logs. | `src/starter_console/workflows/setup/_wizard/sections/observability.py` | Optional | datadoghq.com | String | Config |
| `LOGGING_DUPLEX_ERROR_FILE` | Enable duplex error logging. | `src/starter_console/observability/logging.py` | Optional | false | Boolean | Config |
| `LOGGING_FILE_BACKUPS` | Number of log file backups. | `src/starter_console/workflows/setup/_wizard/sections/observability.py` | Optional | 5 | Integer | Config |
| `LOGGING_FILE_MAX_MB` | Max size of log file in MB. | `src/starter_console/workflows/setup/_wizard/sections/observability.py` | Optional | 10 | Integer | Config |
| `LOGGING_FILE_PATH` | Path to application log file. | `src/starter_console/workflows/setup/_wizard/sections/observability.py` | Optional | var/log/api-service.log | Path | Config |
| `LOGGING_MAX_DAYS` | Max days to keep logs. | `src/starter_console/observability/logging.py` | Optional | 0 | Integer | Config |
| `LOGGING_OTLP_ENDPOINT` | OTLP endpoint for logs. | `src/starter_console/workflows/setup/_wizard/sections/observability.py` | Optional | - | URL | Config |
| `LOGGING_OTLP_HEADERS` | OTLP headers for logs. | `src/starter_console/workflows/setup/_wizard/sections/observability.py` | Optional | - | JSON | Secret |
| `LOGGING_SINKS` | Enabled logging sinks. | `src/starter_console/workflows/setup/_wizard/sections/observability.py` | Required | stdout | CSV | Config |
| `MINIO_ACCESS_KEY` | MinIO access key. | `src/starter_console/workflows/setup/_wizard/sections/storage.py` | Required | - | String | Secret |
| `MINIO_ENDPOINT` | MinIO endpoint URL. | `src/starter_console/workflows/setup/_wizard/sections/storage.py` | Required | - | URL | Config |
| `MINIO_REGION` | MinIO region. | `src/starter_console/workflows/setup/_wizard/sections/storage.py` | Optional | - | String | Config |
| `MINIO_SECRET_KEY` | MinIO secret key. | `src/starter_console/workflows/setup/_wizard/sections/storage.py` | Required | - | String | Secret |
| `MINIO_SECURE` | Use HTTPS for MinIO. | `src/starter_console/workflows/setup/_wizard/sections/storage.py` | Optional | - | Boolean | Config |
| `NEXT_PUBLIC_LOG_LEVEL` | Frontend log level. | `src/starter_console/workflows/setup/_wizard/sections/frontend.py` | Required | info | String | Config |
| `NEXT_PUBLIC_LOG_SINK` | Frontend log sink. | `src/starter_console/workflows/setup/_wizard/sections/frontend.py` | Required | console | String | Config |
| `OPENAI_AGENTS_DISABLE_TRACING` | Disable OpenAI agents tracing (tests). | `tests/conftest.py` | Optional | true | Boolean | Config |
| `OPENAI_API_KEY` | OpenAI API key. | `src/starter_console/workflows/setup/_wizard/sections/providers/ai.py` | Required | - | String | Secret |
| `OTEL_EXPORTER_SENTRY_AUTH_HEADER` | Auth header for Sentry OTel exporter. | `src/starter_console/workflows/setup/_wizard/sections/observability.py` | Optional | - | String | Secret |
| `OTEL_EXPORTER_SENTRY_ENDPOINT` | Sentry OTLP endpoint. | `src/starter_console/workflows/setup/_wizard/sections/observability.py` | Optional | - | URL | Config |
| `OTEL_EXPORTER_SENTRY_HEADERS` | Extra headers for Sentry OTel exporter. | `src/starter_console/workflows/setup/_wizard/sections/observability.py` | Optional | - | JSON | Secret |
| `PASSWORD_RESET_EMAIL_RATE_LIMIT_PER_HOUR` | Password reset emails per account per hour. | `src/starter_console/workflows/setup/_wizard/sections/security.py` | Optional | 5 | Integer | Config |
| `PASSWORD_RESET_IP_RATE_LIMIT_PER_HOUR` | Password reset emails per IP per hour. | `src/starter_console/workflows/setup/_wizard/sections/security.py` | Optional | 20 | Integer | Config |
| `PASSWORD_RESET_TOKEN_TTL_MINUTES` | Password reset token lifetime. | `src/starter_console/workflows/setup/_wizard/sections/security.py` | Optional | 30 | Integer | Config |
| `PLAYWRIGHT_BASE_URL` | Base URL for Playwright tests. | `src/starter_console/workflows/setup/_wizard/sections/frontend.py` | Required | http://localhost:3000 | URL | Config |
| `PORT` | Port for the backend API. | `src/starter_console/workflows/setup/_wizard/sections/core.py` | Required | 8000 | Integer | Config |
| `POSTGRES_DB` | Local Postgres database name. | `src/starter_console/workflows/home/probes/db_config.py` | Optional | saas_starter_db | String | Config |
| `POSTGRES_PASSWORD` | Local Postgres password. | `src/starter_console/workflows/home/probes/db_config.py` | Optional | postgres | String | Secret |
| `POSTGRES_PORT` | Local Postgres port. | `src/starter_console/workflows/home/probes/db_config.py` | Optional | 5432 | Integer | Config |
| `POSTGRES_USER` | Local Postgres username. | `src/starter_console/workflows/home/probes/db_config.py` | Optional | postgres | String | Config |
| `RATE_LIMIT_KEY_PREFIX` | Redis key prefix for rate limiting. | `src/starter_console/workflows/setup/_wizard/sections/security.py` | Required | rate-limit | String | Config |
| `RATE_LIMIT_REDIS_URL` | Redis URL for rate limiting. | `src/starter_console/workflows/home/probes/redis.py` | Optional | - | Redis URL | Secret |
| `REDIS_URL` | Primary Redis connection URL. | `src/starter_console/workflows/home/probes/redis.py` | Required | - | Redis URL | Secret |
| `REQUIRE_EMAIL_VERIFICATION` | Require verified email for access. | `src/starter_console/workflows/setup/_wizard/sections/core.py` | Optional | true | Boolean | Config |
| `RESEND_API_KEY` | API key for Resend email service. | `src/starter_console/workflows/setup/_wizard/sections/providers/email.py` | Optional | - | String | Secret |
| `RESEND_BASE_URL` | Resend API base URL. | `src/starter_console/workflows/setup/_wizard/sections/providers/email.py` | Required | https://api.resend.com | URL | Config |
| `RESEND_DEFAULT_FROM` | Default From address for emails. | `src/starter_console/workflows/setup/_wizard/sections/providers/email.py` | Optional | support@example.com | Email | Config |
| `RESEND_EMAIL_ENABLED` | Enable Resend email delivery. | `src/starter_console/workflows/setup/_wizard/sections/providers/email.py` | Optional | false | Boolean | Config |
| `RESEND_EMAIL_VERIFICATION_TEMPLATE_ID` | Resend template ID for verification. | `src/starter_console/workflows/setup/_wizard/sections/providers/email.py` | Optional | - | String | Config |
| `RESEND_PASSWORD_RESET_TEMPLATE_ID` | Resend template ID for password reset. | `src/starter_console/workflows/setup/_wizard/sections/providers/email.py` | Optional | - | String | Config |
| `S3_BUCKET` | S3 bucket name. | `src/starter_console/workflows/setup/_wizard/sections/storage.py` | Required | - | String | Config |
| `S3_ENDPOINT_URL` | Custom S3 endpoint URL. | `src/starter_console/workflows/setup/_wizard/sections/storage.py` | Optional | - | URL | Config |
| `S3_FORCE_PATH_STYLE` | Force path-style access for S3. | `src/starter_console/workflows/setup/_wizard/sections/storage.py` | Optional | false | Boolean | Config |
| `S3_REGION` | S3 region. | `src/starter_console/workflows/setup/_wizard/sections/storage.py` | Optional | - | String | Config |
| `SECRET_KEY` | Main application secret key. | `src/starter_console/workflows/setup/_wizard/sections/secrets.py` | Required | - | String | Secret |
| `SECRETS_PROVIDER` | Secrets provider backend. | `src/starter_console/workflows/home/probes/secrets.py` | Required | - | String | Config |
| `SECURITY_TOKEN_REDIS_URL` | Redis URL for security tokens. | `src/starter_console/workflows/setup/_wizard/sections/providers/redis.py` | Optional | - | Redis URL | Secret |
| `SIGNUP_ACCESS_POLICY` | Signup access policy (`public`, `invite_only`, `approval`). | `src/starter_console/workflows/setup/_wizard/sections/signup.py` | Required | invite_only | String | Config |
| `SIGNUP_CONCURRENT_REQUESTS_LIMIT` | Concurrent signup requests per IP. | `src/starter_console/workflows/setup/_wizard/sections/signup.py` | Required | 3 | Integer | Config |
| `SIGNUP_DEFAULT_PLAN_CODE` | Default plan code for new signups. | `src/starter_console/workflows/setup/_wizard/sections/signup.py` | Required | starter | String | Config |
| `SIGNUP_DEFAULT_TRIAL_DAYS` | Default trial days for new signups. | `src/starter_console/workflows/setup/_wizard/sections/signup.py` | Required | 14 | Integer | Config |
| `SIGNUP_RATE_LIMIT_PER_DOMAIN_DAY` | Signup rate limit per email domain per day. | `src/starter_console/workflows/setup/_wizard/sections/signup.py` | Required | 20 | Integer | Config |
| `SIGNUP_RATE_LIMIT_PER_EMAIL_DAY` | Signup rate limit per email address per day. | `src/starter_console/workflows/setup/_wizard/sections/signup.py` | Required | 3 | Integer | Config |
| `SIGNUP_RATE_LIMIT_PER_HOUR` | Signup rate limit per IP per hour. | `src/starter_console/workflows/setup/_wizard/sections/signup.py` | Required | 20 | Integer | Config |
| `SIGNUP_RATE_LIMIT_PER_IP_DAY` | Signup rate limit per IP per day. | `src/starter_console/workflows/setup/_wizard/sections/signup.py` | Required | 100 | Integer | Config |
| `SLACK_API_BASE_URL` | Slack API base URL. | `src/starter_console/workflows/setup/_wizard/sections/integrations.py` | Optional | https://slack.com/api | URL | Config |
| `SLACK_HTTP_TIMEOUT_SECONDS` | Timeout for Slack API requests. | `src/starter_console/workflows/setup/_wizard/sections/integrations.py` | Optional | 5.0 | Float | Config |
| `SLACK_STATUS_BOT_TOKEN` | Slack bot token for status notifications. | `src/starter_console/workflows/setup/_wizard/sections/integrations.py` | Required | - | String | Secret |
| `SLACK_STATUS_DEFAULT_CHANNELS` | Default Slack channels for status alerts. | `src/starter_console/workflows/setup/_wizard/sections/integrations.py` | Required | #incidents | String/JSON | Config |
| `SLACK_STATUS_MAX_RETRIES` | Max retries for Slack notifications. | `src/starter_console/core/inventory.py` | Optional | - | Integer | Config |
| `SLACK_STATUS_RATE_LIMIT_WINDOW_SECONDS` | Rate limit window for Slack notifications. | `src/starter_console/core/inventory.py` | Optional | - | Integer | Config |
| `SLACK_STATUS_TENANT_CHANNEL_MAP` | Tenant-specific Slack channel overrides. | `src/starter_console/workflows/setup/_wizard/sections/integrations.py` | Optional | - | JSON | Config |
| `SSO_<PROVIDER>_ALLOWED_DOMAINS` | Allowed email domains for SSO provider. | `src/starter_console/services/sso/config.py` | Optional | - | CSV | Config |
| `SSO_<PROVIDER>_AUTO_PROVISION_POLICY` | Auto-provisioning policy for SSO provider. | `src/starter_console/services/sso/config.py` | Optional | invite_only | String | Config |
| `SSO_<PROVIDER>_CLIENT_ID` | Client ID for SSO provider. | `src/starter_console/services/sso/config.py` | Required | - | String | Config |
| `SSO_<PROVIDER>_CLIENT_SECRET` | Client Secret for SSO provider. | `src/starter_console/services/sso/config.py` | Optional | - | String | Secret |
| `SSO_<PROVIDER>_DEFAULT_ROLE` | Default role for auto-provisioned users. | `src/starter_console/services/sso/config.py` | Optional | member | String | Config |
| `SSO_<PROVIDER>_DISCOVERY_URL` | OIDC Discovery URL for SSO provider. | `src/starter_console/services/sso/config.py` | Optional | - | URL | Config |
| `SSO_<PROVIDER>_ENABLED` | Enable SSO provider. | `src/starter_console/services/sso/config.py` | Optional | true | Boolean | Config |
| `SSO_<PROVIDER>_ID_TOKEN_ALGS` | Allowed ID token signing algorithms. | `src/starter_console/services/sso/config.py` | Optional | - | CSV | Config |
| `SSO_<PROVIDER>_ISSUER_URL` | OIDC Issuer URL for SSO provider. | `src/starter_console/services/sso/config.py` | Required | - | URL | Config |
| `SSO_<PROVIDER>_PKCE_REQUIRED` | Require PKCE for SSO provider. | `src/starter_console/services/sso/config.py` | Optional | true | Boolean | Config |
| `SSO_<PROVIDER>_SCOPE` | SSO configuration scope (`global` or `tenant`). | `src/starter_console/services/sso/config.py` | Optional | global | String | Config |
| `SSO_<PROVIDER>_SCOPES` | OIDC Scopes for SSO provider. | `src/starter_console/services/sso/config.py` | Optional | openid,email,profile | CSV | Config |
| `SSO_<PROVIDER>_TENANT_ID` | Tenant ID for tenant-scoped SSO. | `src/starter_console/services/sso/config.py` | Optional | - | String | Config |
| `SSO_<PROVIDER>_TENANT_SLUG` | Tenant slug for tenant-scoped SSO. | `src/starter_console/services/sso/config.py` | Optional | - | String | Config |
| `SSO_<PROVIDER>_TOKEN_AUTH_METHOD` | Token endpoint auth method for SSO. | `src/starter_console/services/sso/config.py` | Optional | client_secret_post | String | Config |
| `SSO_CLIENT_SECRET_ENCRYPTION_KEY` | Key for encrypting SSO client secrets. | `src/starter_console/workflows/home/probes/sso.py` | Required | - | String | Secret |
| `SSO_PROVIDERS` | Enabled SSO providers list. | `src/starter_console/workflows/home/probes/sso.py` | Required | - | CSV | Config |
| `STARTER_CONSOLE_SKIP_ENV` | Skip loading default .env files in CLI. | `src/starter_console/core/constants.py` | Optional | false | Boolean | Config |
| `STARTER_CONSOLE_SKIP_VAULT_PROBE` | Skip Vault probe in CLI verification. | `src/starter_console/workflows/setup/validators.py` | Optional | false | Boolean | Config |
| `STARTER_CONSOLE_TELEMETRY_OPT_IN` | Opt-in for CLI telemetry. | `src/starter_console/core/constants.py` | Optional | - | Boolean | Config |
| `STARTER_LOCAL_DATABASE_MODE` | Database mode for local development (`compose`/`external`). | `src/starter_console/workflows/home/probes/db_config.py` | Optional | compose | String | Config |
| `STATUS_API_TOKEN` | Auth token for Status API. | `src/starter_console/services/auth/status_ops.py` | Required | - | String | Secret |
| `STATUS_SUBSCRIPTION_EMAIL_RATE_LIMIT_PER_HOUR` | Status subscription emails per hour. | `src/starter_console/workflows/setup/_wizard/sections/security.py` | Optional | 5 | Integer | Config |
| `STATUS_SUBSCRIPTION_ENCRYPTION_KEY` | Key for encrypting status subscription data. | `src/starter_console/workflows/setup/_wizard/sections/security.py` | Required | - | String | Secret |
| `STATUS_SUBSCRIPTION_IP_RATE_LIMIT_PER_HOUR` | Status subscription attempts per IP per hour. | `src/starter_console/workflows/setup/_wizard/sections/security.py` | Optional | 20 | Integer | Config |
| `STATUS_SUBSCRIPTION_TOKEN_PEPPER` | Pepper for status subscription tokens. | `src/starter_console/workflows/setup/_wizard/sections/security.py` | Required | - | String | Secret |
| `STATUS_SUBSCRIPTION_TOKEN_TTL_MINUTES` | Status subscription token lifetime. | `src/starter_console/workflows/setup/_wizard/sections/security.py` | Optional | 60 | Integer | Config |
| `STATUS_SUBSCRIPTION_WEBHOOK_TIMEOUT_SECONDS` | Timeout for status webhook delivery. | `src/starter_console/workflows/setup/_wizard/sections/security.py` | Optional | 5 | Integer | Config |
| `STORAGE_BUCKET_PREFIX` | Prefix for storage buckets. | `src/starter_console/workflows/setup/_wizard/sections/storage.py` | Required | agent-data | String | Config |
| `STORAGE_PROVIDER` | Object storage provider. | `src/starter_console/workflows/home/probes/storage.py` | Required | minio | String | Config |
| `STRIPE_PRODUCT_PRICE_MAP` | Map of plan codes to Stripe price IDs. | `src/starter_console/services/stripe/stripe_status.py` | Required | - | JSON | Config |
| `STRIPE_SECRET_KEY` | Stripe Secret Key. | `src/starter_console/services/stripe/stripe_status.py` | Required | - | String | Secret |
| `STRIPE_WEBHOOK_SECRET` | Stripe Webhook Signing Secret. | `src/starter_console/services/stripe/stripe_status.py` | Required | - | String | Secret |
| `TENANT_DEFAULT_SLUG` | Default tenant slug for CLI context. | `src/starter_console/workflows/setup/_wizard/sections/observability.py` | Required | default | String | Config |
| `TEXTUAL_LOG` | Path for Textual debug log. | `src/starter_console/observability/logging.py` | Optional | - | Path | Config |
| `TEXTUAL_LOG_LEVEL` | Log level for Textual debug log. | `src/starter_console/observability/logging.py` | Optional | INFO | String | Config |
| `USAGE_GUARDRAIL_CACHE_BACKEND` | Usage cache backend (`redis`/`memory`). | `src/starter_console/workflows/setup/_wizard/sections/usage.py` | Optional | redis | String | Config |
| `USAGE_GUARDRAIL_CACHE_TTL_SECONDS` | TTL for usage cache. | `src/starter_console/workflows/setup/_wizard/sections/usage.py` | Optional | 30 | Integer | Config |
| `USAGE_GUARDRAIL_REDIS_URL` | Redis URL for usage guardrails. | `src/starter_console/workflows/setup/_wizard/sections/usage.py` | Optional | - | Redis URL | Secret |
| `USAGE_GUARDRAIL_SOFT_LIMIT_MODE` | Behavior on soft limit (`warn`/`block`). | `src/starter_console/workflows/setup/_wizard/sections/usage.py` | Optional | warn | String | Config |
| `USAGE_PLAN_CODES` | Comma-separated list of plan codes for usage. | `src/starter_console/workflows/setup/_wizard/sections/usage.py` | Required | starter,pro | CSV | Config |
| `USAGE_{PLAN}_{DIMENSION}_{TYPE}_LIMIT` | Usage limit for a plan/dimension/type (soft/hard). | `src/starter_console/workflows/setup/_wizard/sections/usage.py` | Optional | - | Integer | Config |
| `VAULT_ADDR` | Vault address. | `src/starter_console/services/auth/security/signing.py` | Required | - | URL | Config |
| `VAULT_NAMESPACE` | Vault namespace (HCP). | `src/starter_console/services/auth/security/signing.py` | Optional | - | String | Config |
| `VAULT_TOKEN` | Vault token. | `src/starter_console/services/auth/security/signing.py` | Required | - | String | Secret |
| `VAULT_TRANSIT_KEY` | Vault Transit key name. | `src/starter_console/services/auth/security/signing.py` | Required | auth-service | String | Config |
| `VAULT_VERIFY_ENABLED` | Enforce Vault verification. | `src/starter_console/services/auth/security/signing.py` | Optional | false | Boolean | Config |
| `VECTOR_MAX_FILE_MB` | Max file size for vector stores in MB. | `src/starter_console/workflows/setup/_wizard/sections/usage.py` | Optional | 512 | Integer | Config |
| `VECTOR_MAX_FILES_PER_STORE` | Max files per vector store. | `src/starter_console/workflows/setup/_wizard/sections/usage.py` | Optional | 5000 | Integer | Config |
| `VECTOR_MAX_STORES_PER_TENANT` | Max vector stores per tenant. | `src/starter_console/workflows/setup/_wizard/sections/usage.py` | Optional | 10 | Integer | Config |
| `VECTOR_MAX_TOTAL_BYTES` | Max total bytes for vector storage per tenant. | `src/starter_console/workflows/setup/_wizard/sections/usage.py` | Optional | - | Integer | Config |
| `XAI_API_KEY` | API key for xAI. | `src/starter_console/workflows/setup/_wizard/sections/providers/ai.py` | Optional | - | String | Secret |
