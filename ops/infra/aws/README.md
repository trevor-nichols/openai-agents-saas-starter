# AWS Reference Blueprint (ECS Fargate)

This Terraform blueprint provisions a production-grade AWS foundation for the API + web apps:
- VPC (public + private subnets, NAT)
- ECS Fargate cluster with separate API + web services
- Application Load Balancers for each service
- RDS Postgres
- ElastiCache Redis
- S3 bucket for object storage

> Default posture: this blueprint assumes **AWS Secrets Manager** (`SECRETS_PROVIDER=aws_sm`).
> Vault/Infisical are optional enterprise paths and require explicitly wiring their env vars via
> `api_env` / `api_secrets`.

## Usage

```bash
cd ops/infra/aws
terraform init
terraform apply \
  -var "project_name=agent-saas" \
  -var "environment=prod" \
  -var "api_image=<api-image>" \
  -var "web_image=<web-image>" \
  -var "api_base_url=https://api.example.com" \
  -var "app_public_url=https://app.example.com" \
  -var "secrets_provider=aws_sm" \
  -var "registry_server=ghcr.io" \
  -var "registry_username=<registry-user>" \
  -var "registry_password=<registry-token>" \
  -var "enable_https=true" \
  -var "acm_certificate_arn=<acm-cert-arn>" \
  -var "aws_sm_signing_secret_arn=<signing-secret-arn>" \
  -var "auth_key_secret_arn=<ed25519-keyset-arn>" \
  -var "auth_key_secret_name=<keyset-secret-name>" \
  -var "auth_key_storage_provider=aws_sm" \
  -var "db_password=<secure-password>" \
  -var "storage_bucket_name=<unique-bucket-name>" \
  -var "storage_provider=s3"
```

Requires Terraform 1.14.x (pinned in `.tool-versions`).

## Environment Variables

The task definitions inject a base set of env vars that align with the API/web apps. You should override or extend them with the `api_env`, `web_env`, `api_secrets`, and `web_secrets` variables.

### API base env
- `PORT=8000`
- `ENVIRONMENT` (deployment environment label)
- `APP_PUBLIC_URL` (defaults to web ALB URL; override via `app_public_url`)
- `DATABASE_URL` (RDS connection string). Omitted automatically when `api_secrets` includes `DATABASE_URL`.
- `REDIS_URL` (ElastiCache endpoint; `rediss://` when TLS enabled). Omitted automatically when `api_secrets` includes `REDIS_URL`.
- `SECRETS_PROVIDER=aws_sm`
- `AWS_REGION`
- `AWS_SM_SIGNING_SECRET_ARN`
- `AUTH_KEY_STORAGE_BACKEND=secret-manager`
- `AUTH_KEY_STORAGE_PROVIDER` (defaults to `secrets_provider`)
- `AUTH_KEY_SECRET_NAME` (Secrets Manager ARN for the Ed25519 keyset JSON; use ARN for IAM scoping on AWS)
- `STORAGE_PROVIDER=s3`
- `S3_BUCKET`
- `ALLOWED_HOSTS` (derived from the effective API base URL; override when needed)
- `ALLOWED_ORIGINS` (defaults to `APP_PUBLIC_URL`; override if you have additional browser origins)

### Web base env
- `PORT=3000`
- `API_BASE_URL` (defaults to API ALB URL; override via `api_base_url`)

For production, provide secrets via `api_secrets` / `web_secrets` (Secrets Manager ARNs). Recommended secrets include:
- `SECRET_KEY`, `AUTH_PASSWORD_PEPPER`, `AUTH_REFRESH_TOKEN_PEPPER`
- `OPENAI_API_KEY`, `STRIPE_SECRET_KEY`, etc.
The blueprint requires `DATABASE_URL` and `REDIS_URL` to be stored in Secrets Manager and wired via `api_secrets` to avoid plaintext in task definitions.

If you use Vault or Infisical for signing/key storage, set `secrets_provider` and
`auth_key_storage_provider` accordingly and pass the provider-specific env vars via
`api_env` / `api_secrets` (e.g., `VAULT_ADDR`, `INFISICAL_BASE_URL`).

## Security Defaults & Dev Overrides

This blueprint is secure-by-default:
- RDS encryption + deletion protection enabled.
- Final snapshot required on destroy (disable only for dev).
- Redis in-transit + at-rest encryption enabled (AUTH token required by default).
- S3 public access blocked + default encryption + versioning enabled.
- HTTPS is enabled on ALBs by default (requires `acm_certificate_arn`).

If you need a softer dev posture, override these variables:
- `db_deletion_protection=false`
- `db_skip_final_snapshot=true`
- `redis_require_auth_token=false`
- `s3_block_public_access=false` (not recommended)
- `s3_enable_encryption=false` (not recommended)
- `enable_https=false` (dev/sandbox only)

## Notes
- HTTPS is enabled by default; set `enable_https=false` only for dev/sandbox or when you intentionally run HTTP.
- When `enable_https=true`, the HTTP listeners redirect to HTTPS by default.
- RDS and Redis are provisioned in private subnets with security groups scoped to ECS tasks.
- The S3 bucket is optional; set `create_s3_bucket=false` if managing storage externally.
- The ECS task role must have `s3:ListBucket` and `s3:HeadBucket` on the configured bucket so the API health check can validate storage access.
- The ECS task role must allow `secretsmanager:GetSecretValue` + `secretsmanager:PutSecretValue` on both `aws_sm_signing_secret_arn` and the keyset secret (provide `auth_key_secret_arn` or `auth_key_secret_name` so IAM can include it).
- For private registries (including GHCR), set `registry_server`, `registry_username`, and `registry_password` to provision a Secrets Manager credential.
- Create the keyset secret (`auth_key_secret_arn` or `auth_key_secret_name`) ahead of time; the API writes updated key material during rotation.

For app configuration details, see `docs/ops/hosting-aws.md`.
