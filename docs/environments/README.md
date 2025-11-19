# Environment Answer Files

Use this directory to version **templates** for the Starter CLI answer files. Actual staging or production credentials must never be committed—copy the template you need, fill in the values off-repo (or in a secure secrets bucket), and point the Make targets at that file.

## Workflow

1. Copy the appropriate template:
   ```bash
   cp docs/environments/staging.answers.template.json ~/secrets/staging.answers.json
   cp docs/environments/production.answers.template.json ~/secrets/production.answers.json
   ```
2. Replace every `CHANGE_ME`/placeholder value with the real secret, URL, or ID for that environment.
3. Export the path when running the automation targets:
   ```bash
   SETUP_STAGING_ANSWERS=~/secrets/staging.answers.json make setup-staging
   SETUP_PRODUCTION_ANSWERS=~/secrets/production.answers.json make setup-production
   ```

### Template Conventions

- String booleans (`"true"`/`"false"`) match what the headless wizard expects.
- Nested JSON values (e.g., `STRIPE_PRODUCT_PRICE_MAP`, `SLACK_STATUS_TENANT_CHANNEL_MAP`) are pre-escaped strings because the underlying env vars must stay JSON.
- Secrets should be rotated regularly; placeholders such as `"vault-secret-token"` are **not** safe defaults.

Feel free to add environment-specific files in this folder—`.gitignore` ensures anything ending in `.answers.json` stays out of version control.
