# Release & Operations Runbook

This runbook covers production deployments and safe rollbacks. It is cloud-agnostic and works with the AWS/Azure reference blueprints.

## Pre-Deploy Checklist

- Build and publish container images (API + web).
- Confirm secrets are stored in the target secrets manager.
- Ensure `DATABASE_URL` and `REDIS_URL` are injected via secret references (required for the reference blueprints).
- Verify database backups and Redis snapshot policies are enabled.
- Confirm the billing worker topology (inline vs dedicated).

## Deploy Steps (Summary)

1. **Migrations** (one-off job/task)
   - Run `just migrate` or `starter-console release db` against the production database.
   - Keep `AUTO_RUN_MIGRATIONS=false` on the API service.
2. **Deploy API container**
   - Update the API service to the new image tag.
   - Verify health endpoint: `GET /health/ready`.
3. **Deploy Web container**
   - Update the web service to the new image tag.
   - Verify health endpoint: `GET /api/health/ready`.
4. **Post-deploy smoke checks**
   - Validate auth flow (signup/login) and a basic chat run.

## Billing Worker Topology

If running more than one API replica, move billing retries to a dedicated service to prevent duplicate retries:
- API: `ENABLE_BILLING_RETRY_WORKER=false`
- Worker: `ENABLE_BILLING_RETRY_WORKER=true`, `BILLING_RETRY_DEPLOYMENT_MODE=dedicated`

## Rollback Strategy

- Revert the API + web deployments to the last known good image tag.
- Do not roll back database migrations unless absolutely necessary.
- If a rollback is required, restore the database from the last snapshot and redeploy a prior image.

## Secrets Rotation

- Rotate signing keys and provider secrets in the secrets manager.
- Redeploy services to pick up new values.
- Validate JWT issuance and refresh token flows after rotation.

## Registry Overrides (ECR / ACR)

The CI workflow defaults to GHCR but supports custom registries with minimal setup.

### GHCR (private)

Use GHCR in production only if you want to manage registry credentials yourself. For AWS/Azure, prefer ECR/ACR.

1. Create a GitHub PAT or fine-grained token with `read:packages`.
2. Add GitHub secrets:
   - `REGISTRY_USERNAME` = GitHub username or bot account
   - `REGISTRY_PASSWORD` = PAT/token
3. Use workflow dispatch with:
   - `registry` = `ghcr.io`
   - `image_prefix` = `<owner>/<repo>` or a custom org/repo path

Example:
```
registry: ghcr.io
image_prefix: my-org/agent-saas
```

### AWS ECR (copy/paste)

1. Create an ECR repo for each image (`api`, `web`).
2. Add GitHub secrets:
   - `AWS_ACCESS_KEY_ID` = AWS access key ID
   - `AWS_SECRET_ACCESS_KEY` = AWS secret access key
   - `AWS_SESSION_TOKEN` = (optional) session token for temporary creds
3. Use workflow dispatch with:
   - `registry` = `<account>.dkr.ecr.<region>.amazonaws.com`
   - `image_prefix` = `<ecr-repo-prefix>` (e.g., `agent-saas`)

Example (manual dispatch inputs):
```
registry: 123456789012.dkr.ecr.us-east-1.amazonaws.com
image_prefix: agent-saas
```

### Azure ACR (copy/paste)

1. Create an ACR registry and enable admin user (or use a service principal).
2. Add GitHub secrets:
   - `REGISTRY_USERNAME` = ACR username
   - `REGISTRY_PASSWORD` = ACR password
3. Use workflow dispatch with:
   - `registry` = `<registry>.azurecr.io`
   - `image_prefix` = `<repo-prefix>`

Example:
```
registry: myregistry.azurecr.io
image_prefix: agent-saas
```
