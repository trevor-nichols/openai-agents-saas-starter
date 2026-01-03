# Terraform tfvars Export (Starter Console)

The Starter Console can generate Terraform `*.tfvars` files for the reference
blueprints in `ops/infra/**`. This keeps app configuration and infra inputs
aligned without forcing teams into a specific workflow.

## Quick start

Generate a template with placeholders:

```bash
starter-console infra terraform export \
  --provider gcp \
  --mode template \
  --output var/infra/gcp/terraform.tfvars
```

Generate a filled tfvars (fails fast if required values are missing):

```bash
starter-console infra terraform export \
  --provider aws \
  --mode filled \
  --var project_name=agent-saas \
  --var environment=prod \
  --var api_image=ghcr.io/org/api:2026-01-03 \
  --var web_image=ghcr.io/org/web:2026-01-03 \
  --var storage_bucket_name=agent-saas-assets \
  --var db_password=change-me \
  --var api_secrets='{"DATABASE_URL":"arn:...","REDIS_URL":"arn:..."}' \
  --var enable_https=false \
  --var secrets_provider=vault_hcp \
  --var auth_key_secret_name=auth-key-secret \
  --var redis_require_auth_token=false
```

Export JSON instead of HCL:

```bash
starter-console infra terraform export \
  --provider azure \
  --format json \
  --output var/infra/azure/terraform.tfvars.json
```

## Input precedence

Values are merged in the following order (last wins):

1. `--var` overrides
2. `--answers-file` (JSON key/value pairs from the setup wizard)
3. `.env.local` files (defaults to `apps/api-service/.env.local` and `apps/web-app/.env.local`)

## Secrets

By default, sensitive values are **redacted** in the export. Use
`--include-secrets` only for trusted local workflows. For production, prefer
`TF_VAR_*` or CI/CD secret injection so secrets never land in a repo checkout.

## Advanced inputs

The export omits advanced tuning variables unless you request them:

```bash
starter-console infra terraform export --provider gcp --include-advanced
```

You can also include optional defaults with `--include-defaults`.

## Extra variables

If you need to pass variables not in the export schema, use:

```bash
starter-console infra terraform export \
  --provider aws \
  --extra-var custom_feature_flag=true
```

## Related docs

- `docs/ops/hosting-overview.md`
- `docs/ops/hosting-aws.md`
- `docs/ops/hosting-azure.md`
- `docs/ops/hosting-gcp.md`
