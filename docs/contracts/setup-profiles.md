# Setup Profiles Contract (v1)

This document defines the profile policy contract used by the Starter Console setup wizard.
Profiles are data-driven policies that control defaults, requirements, and automation behavior
without duplicating wizard or TUI logic.

## Goals

- Provide default profiles (demo, staging, production).
- Allow teams to add custom profiles in-repo.
- Support portable configuration across machines.
- Enable auto-detection for a reasonable default profile.
- Keep wizard logic DRY by centralizing profile policy in one contract.

## Non-goals

- Replace `schema.yaml` prompt dependency logic.
- Replace `.env` files as the source of runtime configuration.
- Introduce backward-compatibility shims (repo is pre-release).

## File Locations

- Built-in profiles (source of truth):
  - `packages/starter_contracts/src/starter_contracts/profiles/profiles.yaml`
- Project override/extension file (portable, versionable):
  - `config/starter-console.profile.yaml`
  - Use `--profiles-path <path>` to load an alternate profile file.
- Optional run manifest (audit trail):
  - `var/reports/profile-manifest.json`

## Precedence and Auto-detect

1. Explicit CLI flag: `starter-console setup wizard --profile <id>`
2. `config/starter-console.profile.yaml` with `active_profile`
3. Environment override: `STARTER_PROFILE`
4. Auto-detect rules in profile definitions
5. Fallback: `demo`

## Contract Overview (YAML)

```yaml
version: 1
profiles:
  <profile_id>:
    label: "Human readable name"
    description: "Short intent statement"
    extends: "base"            # optional, for DRY inheritance
    detect:                    # optional auto-detect rules
      priority: 50             # lower = higher priority
      any:                     # any rule matching is a hit
        - env: { key: ENVIRONMENT, equals: production }
        - env: { key: APP_PUBLIC_URL, contains: "localhost" }
    wizard:
      hosting_preset_default: local_docker | cloud_managed | enterprise_custom
      cloud_provider_default: aws | azure | gcp | other
      show_advanced_default: true | false
      automation:
        allow: [infra, secrets, stripe, sso, migrations, redis, geoip, dev_user, demo_token]
        defaults:
          infra: true
          secrets: true
          stripe: false
          sso: false
          migrations: true
          redis: true
          geoip: false
          dev_user: true
          demo_token: true
    env:
      defaults:
        backend:
          DEBUG: "true"
          AUTO_RUN_MIGRATIONS: "true"
          SECRETS_PROVIDER: "vault_dev"
          STORAGE_PROVIDER: "minio"
          ENABLE_BILLING: "false"
        frontend:
          AGENT_ALLOW_INSECURE_COOKIES: "true"
      required:
        backend: [OPENAI_API_KEY, REDIS_URL]
        frontend: []
      optional:
        backend: [VAULT_ADDR, VAULT_TOKEN, VAULT_TRANSIT_KEY]
        frontend: []
      hidden:
        backend: []
        frontend: []
      locked:
        backend: [AUTH_KEY_STORAGE_BACKEND]
        frontend: []
    choices:
      secrets_provider: [vault_dev, vault_hcp, infisical, aws_sm, azure_kv, gcp_sm]
      storage_provider: [minio, s3, gcs, azure_blob]
      key_storage_backend: [file, secret-manager]
      billing_retry_mode: [inline, dedicated]
      geoip_provider: [none, ipinfo, ip2location, ip2location_db, maxmind_db]
    rules:
      require_vault: true | false
      require_database_url: true | false
      redis_tls_required: true | false
      stripe_webhook_auto_allowed: true | false
      dev_user_allowed: true | false
      geoip_required_mode: "warn" | "error" | "disabled"
      frontend_log_ingest_requires_confirmation: true | false
      migrations_prompt_default: true | false
```

### Field semantics

- `extends`: merges parent profile fields, with child values overriding. Arrays are
  replaced unless explicitly documented as mergeable.
- `detect`: a profile matches if any `any` rule matches. Each rule supports:
  - `env.key` + `equals` or `contains`, or `present: true`
- `wizard`: defaults for wizard UX and automation policy.
- `env.defaults`: values written into `.env` when not already set.
- `env.required/optional`: drives checklist output and audit status.
- `env.hidden`: hides prompts in TUI/CLI; values come from existing env or profile defaults.
- `env.locked`: values enforced by profile (see locking model below).
- `choices`: per-domain allowed values for prompt choices.
- `rules`: non-env behavior gates used by sections (e.g., TLS required for Redis).
- `wizard.automation.allow`: when omitted (`null`), all automation phases are allowed; an explicit empty list (`[]`) disables all automation phases.

## Locking Model (recommended)

Use locked values **sparingly** for security/compliance-critical settings.
Locked values are applied automatically and not prompted. If an existing env value
differs from the profile default, it is treated as an override and recorded in
`var/reports/profile-manifest.json` for auditability.

This keeps the system safe-by-default while still giving developers an escape hatch.

## Proposed Default Profiles (aligned with current behavior)

### demo

- `wizard.hosting_preset_default`: `local_docker`
- `wizard.show_advanced_default`: `false`
- `wizard.automation.allow`: all phases
- `wizard.automation.defaults`: migrations/redis/dev_user/demo_token enabled
- `rules`:
  - `require_vault=false`
  - `require_database_url=false` (local compose allowed)
  - `redis_tls_required=false`
  - `stripe_webhook_auto_allowed=true`
  - `dev_user_allowed=true`
  - `geoip_required_mode=disabled`
  - `frontend_log_ingest_requires_confirmation=false`
  - `migrations_prompt_default=false`
- `env.defaults`:
  - `DEBUG=true`
  - `AUTO_RUN_MIGRATIONS=true`
  - `SECRETS_PROVIDER=vault_dev`
  - `STORAGE_PROVIDER=minio`
  - `ENABLE_BILLING=false`
  - `BILLING_RETRY_DEPLOYMENT_MODE=inline`

### staging

- `wizard.hosting_preset_default`: `cloud_managed`
- `wizard.show_advanced_default`: `true`
- `wizard.automation.allow`: stripe/sso/migrations/redis/geoip
- `wizard.automation.defaults`: migrations/redis enabled
- `rules`:
  - `require_vault=true`
  - `require_database_url=true`
  - `redis_tls_required=true`
  - `stripe_webhook_auto_allowed=false`
  - `dev_user_allowed=false`
  - `geoip_required_mode=warn`
  - `frontend_log_ingest_requires_confirmation=false`
  - `migrations_prompt_default=true`
- `env.defaults`:
  - `DEBUG=false`
  - `AUTO_RUN_MIGRATIONS=false`
  - `ENABLE_BILLING=true`
  - `BILLING_RETRY_DEPLOYMENT_MODE=dedicated`
  - `AUTH_KEY_STORAGE_BACKEND=secret-manager` (locked)

### production

Same as staging, but:

- `ENVIRONMENT=production` defaults
- `frontend_log_ingest_requires_confirmation=true`

## Portability

- The recommended portable artifact is `config/starter-console.profile.yaml`.
- The wizard still writes `.env` files as the canonical runtime config.
- `var/reports/profile-manifest.json` provides a traceable audit record, including
  any locked-value overrides under `locked.overrides`.

## Contract Ownership

This contract lives in `starter_contracts` to keep console and backend aligned.
Any changes require updating this doc, the default profile YAML, and related tests.
