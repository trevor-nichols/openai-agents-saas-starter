# Changelog

## v0.1.1 (Unreleased)
- Extracted `starter_contracts` package and removed `starter_shared`; aligned build/typecheck/lint pipelines to the new package.
- Added contract drift guards (snapshot tests for settings/enums) and import-boundary tests.
- Added CI guardrails: backend lint + platform smoke, CLI setup dry-run, frontend SDK drift check.
- Stubbed hermetic platform smoke (health, JWKS, stub agent registry) for CI.

## v0.1.0
- Initial pre-release scaffold for FastAPI backend, Next.js frontend, and Starter CLI.
