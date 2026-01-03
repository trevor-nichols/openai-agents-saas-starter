# Setup Wizard Hosting Presets

Use hosting presets to keep the setup wizard deterministic and auditable while still allowing overrides when needed. Presets only set defaults and prompt gating; you can still override values via answers files or follow-up runs.

## Presets

### local_docker
Use for local development and demo environments.

Defaults applied:
- `STARTER_LOCAL_DATABASE_MODE=compose`
- `REDIS_URL=redis://localhost:6379/0`
- `SECRETS_PROVIDER=vault_dev`
- `STORAGE_PROVIDER=minio`
- `ENABLE_BILLING=false`

Recommended for:
- Local demo or sandbox stacks
- Fresh checkouts that rely on Docker Compose

### cloud_managed
Use for staging/production on hosted infrastructure.

Defaults applied:
- `STARTER_LOCAL_DATABASE_MODE=external`
- `SECRETS_PROVIDER` and `STORAGE_PROVIDER` depend on `SETUP_CLOUD_PROVIDER`
- `ENABLE_BILLING=true`

Cloud provider mapping:
- `aws` -> `SECRETS_PROVIDER=aws_sm`, `STORAGE_PROVIDER=s3`
- `azure` -> `SECRETS_PROVIDER=azure_kv`, `STORAGE_PROVIDER=azure_blob`
- `gcp` -> `SECRETS_PROVIDER=gcp_sm`, `STORAGE_PROVIDER=gcs`
- `other` -> defaults to AWS mapping unless overridden

Notes:
- The `gcp` preset assumes Cloud Run + Secret Manager and requires the `gcp_sm` secrets provider.

Required follow-ups:
- Provide hosted `DATABASE_URL`
- Provide hosted `REDIS_URL`
- Provide provider credentials for secrets/storage

### enterprise_custom
Use when you want full control and no defaults beyond required prompts.

Recommended for:
- Complex or hybrid deployments
- Existing environments with bespoke infra

## Advanced prompts

The wizard asks whether to show advanced prompts (rate limits, cache TTLs, optional provider fields).
- Default is **off** for demo/dev profiles
- Default is **on** for staging/production profiles

You can override this via answers files with:
- `SETUP_SHOW_ADVANCED=true` or `SETUP_SHOW_ADVANCED=false`

## Artifacts

Each wizard run writes:
- `var/reports/setup-summary.json`
- `var/reports/cli-one-stop-summary.md`
- `var/reports/setup-snapshot.json` (redacted hashes)
- `var/reports/setup-diff.md` (changes since last run)

Use these for auditing and to confirm preset-driven defaults.

## Headless usage

Example answers file fragment:

```json
{
  "SETUP_HOSTING_PRESET": "cloud_managed",
  "SETUP_CLOUD_PROVIDER": "aws",
  "SETUP_SHOW_ADVANCED": "true"
}
```

Run:

```
starter-console setup wizard --non-interactive --answers-file ./answers.json
```

## Re-running the wizard

Re-run with the same profile and preset to update values; the diff artifact will show what changed. For one-off overrides, pass `--var KEY=VALUE` to avoid editing the answers file.
