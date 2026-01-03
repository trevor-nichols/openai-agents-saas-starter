## packages/starter_contracts

**Note**: The following environment variables occur primarily in Terraform specification definitions (`env_aliases`) or validation error messages that guide configuration.

| Name | Purpose | Location | Required / Optional | Default | Format | Sensitivity |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **API_BASE_URL** | Public API base URL for the web app (e.g., https://api.example.com). | `src/starter_contracts/infra/terraform_spec/aws.py` (L59)<br>`azure.py` (L75)<br>`gcp.py` (L137) | Optional | `""` (Empty string) | URL String | Non-secret |
| **APP_PUBLIC_URL** | Public web URL used by the API service (e.g., https://app.example.com). | `src/starter_contracts/infra/terraform_spec/aws.py` (L68)<br>`azure.py` (L83)<br>`gcp.py` (L145) | Optional | `""` (Empty string) | URL String | Non-secret |
| **AUTH_KEY_SECRET_NAME** | Secret Manager key/path/name for the Ed25519 keyset JSON. | `src/starter_contracts/infra/terraform_spec/aws.py` (L97)<br>`azure.py` (L157)<br>`gcp.py` (L168) | Required (if using Secret Manager backend) | `""` (Empty string) | String | Non-secret (Pointer) |
| **AUTH_KEY_STORAGE_PROVIDER** | Specifies which provider is used for key storage. | `src/starter_contracts/infra/terraform_spec/aws.py` (L88)<br>`azure.py` (L166)<br>`gcp.py` (L160) | Optional | Defaults to `SECRETS_PROVIDER` | String (enum: `aws_sm`, `azure_kv`, `gcp_sm`) | Non-secret |
| **AWS_REGION** | AWS region for resources. | `src/starter_contracts/infra/terraform_spec/aws.py` (L38) | Optional | `us-east-1` | String | Non-secret |
| **AWS_SM_SIGNING_SECRET_ARN** | AWS Secrets Manager ARN for the signing secret. | `src/starter_contracts/infra/terraform_spec/aws.py` (L80) | Required (if provider is `aws_sm`) | `""` (Empty string) | String (ARN) | Non-secret (Pointer) |
| **AZURE_BLOB_CONTAINER** | Container name for object storage in Azure. | `src/starter_contracts/infra/terraform_spec/azure.py` (L125) | Optional | `assets` | String | Non-secret |
| **AZURE_KV_SIGNING_SECRET_NAME** | Key Vault secret name containing the signing secret. | `src/starter_contracts/infra/terraform_spec/azure.py` (L149) | Required (if provider is `azure_kv`) | `""` (Empty string) | String | Non-secret (Pointer) |
| **DATABASE_URL** | Connection string for the database. Referenced in validation rules to ensure it is passed via secrets, not plain env vars. | `src/starter_contracts/infra/terraform_spec/common.py` (L96, L107) | Required | `__REQUIRED__` (Template) | Connection String | Secret |
| **ENABLE_BILLING** | Feature flag to enable billing logic. | `src/starter_contracts/provider_validation.py` (L98) | Optional | `false` (implied) | Boolean string (`true`/`false`) | Non-secret |
| **ENVIRONMENT** | Deployment environment name (e.g., dev, staging, prod). | `src/starter_contracts/infra/terraform_spec/common.py` (L59) | Required | N/A | String | Non-secret |
| **GCP_SM_PROJECT_ID** | GCP project ID hosting the resources. | `src/starter_contracts/infra/terraform_spec/gcp.py` (L43) | Required | `__REQUIRED__` (Template) | String | Non-secret |
| **GCP_SM_SIGNING_SECRET_NAME** | GCP Secret Manager secret name containing the signing secret. | `src/starter_contracts/infra/terraform_spec/gcp.py` (L176) | Required (if provider is `gcp_sm`) | `""` (Empty string) | String | Non-secret (Pointer) |
| **GCS_BUCKET** | GCS bucket name for object storage. | `src/starter_contracts/infra/terraform_spec/gcp.py` (L189) | Optional | `assets` | String | Non-secret |
| **GCS_PROJECT_ID** | GCP project ID (Alias for `GCP_SM_PROJECT_ID`). | `src/starter_contracts/infra/terraform_spec/gcp.py` (L43) | Required | `__REQUIRED__` (Template) | String | Non-secret |
| **LOGGING_DATADOG_API_KEY** | Datadog API key for log ingestion. | `src/starter_contracts/observability/logging/sinks/datadog.py` (L53) | Required (if sink includes `datadog`) | N/A | String | Secret |
| **LOGGING_OTLP_ENDPOINT** | HTTP endpoint for OTLP log export. | `src/starter_contracts/observability/logging/sinks/otlp.py` (L54) | Required (if sink includes `otlp`) | N/A | URL String | Non-secret |
| **LOGGING_OTLP_HEADERS** | Additional headers for OTLP export (e.g., auth tokens). | `src/starter_contracts/observability/logging/sinks/otlp.py` (L79) | Optional | N/A | JSON String | Secret |
| **LOGGING_SINKS** | Comma-separated list of active logging destinations. | `src/starter_contracts/observability/logging/config.py` (L91) | Required | N/A | CSV String (`stdout`, `file`, `datadog`, `otlp`) | Non-secret |
| **OPENAI_API_KEY** | API key for OpenAI (Agent Runtime and Web Search). | `src/starter_contracts/provider_validation.py` (L144, L161) | Required | N/A | String | Secret |
| **REDIS_URL** | Connection string for Redis. Referenced in validation rules to ensure it is passed via secrets, not plain env vars. | `src/starter_contracts/infra/terraform_spec/common.py` (L96, L107) | Required | `__REQUIRED__` (Template) | Connection String | Secret |
| **RESEND_API_KEY** | API key for Resend email service. | `src/starter_contracts/provider_validation.py` (L118) | Required (if `RESEND_EMAIL_ENABLED` is true) | N/A | String | Secret |
| **RESEND_DEFAULT_FROM** | Default sender email address for Resend. | `src/starter_contracts/provider_validation.py` (L126) | Required (if `RESEND_EMAIL_ENABLED` is true) | N/A | Email String | Non-secret |
| **RESEND_EMAIL_ENABLED** | Feature flag to enable email delivery via Resend. | `src/starter_contracts/provider_validation.py` (L118, L126) | Optional | `false` (implied) | Boolean string (`true`/`false`) | Non-secret |
| **S3_BUCKET** | S3 bucket name for object storage. | `src/starter_contracts/infra/terraform_spec/aws.py` (L237) | Required | `__REQUIRED__` (Template) | String | Non-secret |
| **SECRETS_PROVIDER** | Specifies the active secrets backend. | `src/starter_contracts/infra/terraform_spec/aws.py` (L75)<br>`azure.py` (L70)<br>`gcp.py` (L153) | Optional | Provider specific (e.g., `aws_sm`) | String (enum: `aws_sm`, `azure_kv`, `gcp_sm`) | Non-secret |
| **STORAGE_PROVIDER** | Specifies the active storage backend. | `src/starter_contracts/infra/terraform_spec/aws.py` (L244)<br>`azure.py` (L129)<br>`gcp.py` (L183) | Optional | Provider specific (e.g., `s3`) | String (enum: `s3`, `azure_blob`, `gcs`) | Non-secret |