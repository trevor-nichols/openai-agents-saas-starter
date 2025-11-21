# scripts/

Purpose-built utilities for CI and engineering guardrails. User/operator flows now live in the Starter CLI (`python -m starter_cli.app`); keep this directory lean and automation-friendly.

What stays here
- CI fences: `assert-billing-openapi.js`, `check_secrets.py`, `typecheck.py`, `cli/verify_env_inventory.py`.
- Architecture/inspection: `moduleviz.py` (service dependency graphs).
- Vault dev helpers: `vault/dev-init.sh`, `vault/wait-for-dev.sh`.
- Billing/eng stubs: `stripe/` is reserved for low-level Stripe tooling that may be invoked from CI; user-facing replay/ops commands now live under `starter_cli stripe dispatches`.

What does **not** belong here
- Operator tasks, wizards, provisioning, or data seeding — add them to `starter_cli` commands.
- Anything that requires interactive prompts or persistent state.
- Repo-specific business logic that should be part of the FastAPI app or CLI workflows.

Principles
- No side effects on import; scripts should be directly runnable by CI.
- Fail fast and loudly (non-zero exit on validation errors).
- Keep dependencies minimal; prefer standard library where possible.

If you add a new script, document it in this file, keep it headless, and consider whether it should instead be a CLI subcommand.
