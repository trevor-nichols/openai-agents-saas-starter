# AWS Hosting Guide

This guide describes the production-ready AWS deployment pattern for the starter.

## Reference Blueprint

Terraform blueprint lives in `ops/infra/aws/` and provisions:
- VPC (public + private subnets, NAT)
- ECS Fargate cluster
- ALBs for API + web
- RDS Postgres
- ElastiCache Redis
- S3 bucket for object storage

## Required AWS Services

- **ECS Fargate** for containers
- **RDS Postgres** for database
- **ElastiCache Redis** for caches/streams
- **S3** for object storage (or compatible provider)
- **Secrets Manager** for API secrets (required for the default AWS blueprint; optional only if you use Vault/Infisical instead)
- **ACM** for HTTPS certificates (required when `enable_https=true`)

## Quickstart (non‑technical)

1. **Build + publish images**: run the GitHub Actions workflow (`.github/workflows/build-images.yml`)
   and note the `api_image` and `web_image` tags you want to deploy. The release runbook has copy/paste
   commands for GHCR/ECR.  
2. **Create secrets** in Secrets Manager:
   - Signing secret for `AWS_SM_SIGNING_SECRET_ARN`.
   - Keyset secret for `AUTH_KEY_SECRET_NAME` (Ed25519 keyset JSON).
   - Required for the default blueprint: secrets for `DATABASE_URL` and `REDIS_URL` so app credentials are injected via Secrets Manager instead of plain env vars.
3. **Run Terraform** in `ops/infra/aws/` with the required variables (see the README).  
4. **Wire environment variables**: use the Terraform outputs (or the optional `app_public_url` /
   `api_base_url` inputs) to set `APP_PUBLIC_URL` (web) and `API_BASE_URL` (web app), plus the
   required `SECRETS_PROVIDER` and key‑storage values.  
5. **Run migrations** once per deploy (see “Migrations”).  
6. **Verify health**: hit `/health/ready` on the API and `/api/health/ready` on the web app.

## Environment Variables

### API (minimal)
- `ENVIRONMENT` (deployment environment label)
- `DATABASE_URL` (RDS endpoint)
- `REDIS_URL` (ElastiCache endpoint, `rediss://` when TLS enabled)
- `APP_PUBLIC_URL` (web URL; derived from `app_public_url` when provided)
- `SECRETS_PROVIDER` (defaults to `aws_sm`; can be `vault_hcp`, `infisical_cloud`, etc. for enterprise setups)
- `AWS_REGION` (required when `SECRETS_PROVIDER=aws_sm`)
- `AWS_SM_SIGNING_SECRET_ARN` (required when `SECRETS_PROVIDER=aws_sm`)
- `AUTH_KEY_STORAGE_BACKEND=secret-manager`, `AUTH_KEY_STORAGE_PROVIDER`, `AUTH_KEY_SECRET_NAME`
  (store Ed25519 keyset in the configured secret manager; for AWS use an ARN for IAM scoping)
- `STORAGE_PROVIDER=s3`
- `S3_BUCKET` (bucket name)
- `ALLOWED_HOSTS` (set to your API domain or ALB DNS name)
- `ALLOWED_ORIGINS` (defaults to `APP_PUBLIC_URL`; override for additional origins)
- `REDIS_URL` should include the AUTH token if `redis_require_auth_token=true` in the Terraform blueprint.

If you use Infisical or Vault for signing or key storage, `SECRETS_PROVIDER` and
`AUTH_KEY_STORAGE_PROVIDER` can differ. See `docs/security/secrets-providers.md` for the full matrix.

> Manual deployments must set `AUTH_KEY_STORAGE_PROVIDER` explicitly when using
> `AUTH_KEY_STORAGE_BACKEND=secret-manager` (Terraform defaults it to `SECRETS_PROVIDER`).

> Note: the **default** AWS blueprint assumes Secrets Manager. Vault/Infisical are optional enterprise
> paths and require explicitly wiring their env vars via `api_env` / `api_secrets`.

### Web (minimal)
- `API_BASE_URL` (API URL)

For the full list, see `docs/trackers/CONSOLE_ENV_INVENTORY.md`.

### Terraform → Env Mapping (core)

| Terraform input | Env var | Notes |
| --- | --- | --- |
| `environment` | `ENVIRONMENT` | Used for production safety checks. |
| `api_base_url` | `API_BASE_URL` | Optional override for the web app API origin. |
| `app_public_url` | `APP_PUBLIC_URL` | Optional override for web origin + CORS derivation. |
| `region` | `AWS_REGION` | Required for AWS Secrets Manager. |
| `secrets_provider` | `SECRETS_PROVIDER` | Defaults to `aws_sm`; set to Vault/Infisical if used. |
| `aws_sm_signing_secret_arn` | `AWS_SM_SIGNING_SECRET_ARN` | Signing secret for service accounts (required when `secrets_provider=aws_sm`). |
| `auth_key_secret_arn` | `AUTH_KEY_SECRET_NAME` | Ed25519 keyset stored in Secrets Manager (required when `auth_key_storage_provider=aws_sm`). |
| `auth_key_secret_name` | `AUTH_KEY_SECRET_NAME` | Generic secret-manager key/path for non-AWS providers. |
| `auth_key_storage_provider` | `AUTH_KEY_STORAGE_PROVIDER` | Key storage provider (defaults to `secrets_provider`). |
| `storage_provider` | `STORAGE_PROVIDER` | Defaults to `s3` for this blueprint. |
| `storage_bucket_name` | `S3_BUCKET` | Object storage bucket. |

## DNS + HTTPS (Route53 + ACM)

Use custom domains like `api.example.com` and `app.example.com`. ACM certificates must be issued in the **same region** as the ALB.

1. **Request an ACM certificate** (replace domain names):
   ```bash
   aws acm request-certificate \
     --domain-name app.example.com \
     --subject-alternative-names api.example.com \
     --validation-method DNS \
     --region <aws-region>
   ```
2. **Fetch the DNS validation records**:
   ```bash
   aws acm describe-certificate \
     --certificate-arn <acm-certificate-arn> \
     --query "Certificate.DomainValidationOptions[].ResourceRecord"
   ```
3. **Create the validation records in Route53** (copy/paste the CNAMEs from step 2).
4. **Create ALIAS records for your domains** (Route53 → hosted zone → create record):
   - `api.example.com` → ALB DNS from the Terraform output `api_url`
   - `app.example.com` → ALB DNS from the Terraform output `web_url`

   If you prefer CLI, fetch the ALB hosted zone ID:
   ```bash
   aws elbv2 describe-load-balancers \
     --names <project-name>-<environment>-api \
     --query "LoadBalancers[0].CanonicalHostedZoneId" \
     --region <aws-region> --output text
   ```
5. **Wire variables/envs**:
   - Terraform: set `acm_certificate_arn` to the issued cert.
   - App env: set `APP_PUBLIC_URL=https://app.example.com`, `API_BASE_URL=https://api.example.com`.
   - App env: set `ALLOWED_HOSTS=api.example.com`.

## Secrets & IAM

- Create a Secrets Manager secret for signing keys and a second secret for the Ed25519 keyset JSON, then set `AUTH_KEY_STORAGE_BACKEND=secret-manager` and `AUTH_KEY_SECRET_NAME` (use the keyset secret ARN).
- Grant the ECS task role `secretsmanager:GetSecretValue` + `secretsmanager:PutSecretValue` on the signing secret and keyset secret, plus `s3:*` for the storage bucket.
- The blueprint requires `DATABASE_URL` and `REDIS_URL` to be provided via `api_secrets` so credentials never appear in task definitions. Terraform state still stores RDS admin passwords if Terraform creates the DB; use a secure remote backend or provision DB creds outside Terraform if that is a concern.
- Pass `auth_key_secret_arn` or `auth_key_secret_name` into the Terraform blueprint so IAM includes the keyset secret; do not rely solely on `api_env` for `AUTH_KEY_SECRET_NAME`.
- Set `AWS_REGION`, `AWS_SM_SIGNING_SECRET_ARN`, and any other secrets provider envs via secrets injection.
- Ensure the task role includes `s3:ListBucket` and `s3:HeadBucket` on the bucket for storage health checks.

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

- **Fast rollback**: update the ECS service to the previous image tag (or set desired count to 0).
- **Infrastructure rollback**: `terraform destroy` will tear down resources, but RDS deletion protection
  and final snapshots are enabled by default. For full teardown in dev/sandbox, set
  `db_deletion_protection=false` and `db_skip_final_snapshot=true` first.
- **Secrets**: if you rotate secrets during rollback, update `AWS_SM_SIGNING_SECRET_ARN` and the
  keyset secret in Secrets Manager accordingly.

## Notes

- HTTPS is enabled by default in the Terraform blueprint. Provide `acm_certificate_arn` and set `APP_PUBLIC_URL` to the HTTPS domain. Use `enable_https=false` only for dev/sandbox.
- For private-only deployments, attach ECS services to private subnets and use internal load balancers.
- Secure-by-default: the Terraform blueprint enables RDS encryption + deletion protection, Redis TLS + at-rest encryption, and blocks S3 public access. Use the variables in `ops/infra/aws/variables.tf` to relax these for dev-only environments.
- If you prefer secrets-only envs, override `REDIS_URL` via `api_secrets` with a Secrets Manager ARN and omit it from `api_env`.
- For production, prefer **ECR** over GHCR so ECS can use IAM-native pulls; if you use private GHCR, set `registry_server`, `registry_username`, and `registry_password` in the Terraform blueprint.

## Registry Overrides (ECR)

The CI workflow can publish to ECR when you provide registry credentials and dispatch the workflow with custom inputs.

Copy/paste (GitHub Actions manual run):
```
registry: <account>.dkr.ecr.<region>.amazonaws.com
image_prefix: agent-saas
```

Set GitHub secrets (for ECR auth):
- `AWS_ACCESS_KEY_ID` = AWS access key ID
- `AWS_SECRET_ACCESS_KEY` = AWS secret access key
- `AWS_SESSION_TOKEN` = (optional) session token for temporary creds

## GHCR Example (private)

Use GHCR only if you want to manage registry credentials yourself (ECR is preferred on AWS).

GitHub Actions manual run:
```
registry: ghcr.io
image_prefix: <owner>/<repo>
```

Terraform inputs (ECS pulls):
```
registry_server = "ghcr.io"
registry_username = "<github-username-or-bot>"
registry_password = "<ghcr-pat>"
```
