# Changelog

## v0.1.1 (Unreleased)
- Extracted `starter_contracts` package and removed `starter_shared`; aligned build/typecheck/lint pipelines to the new package.
- Added contract drift guards (snapshot tests for settings/enums) and import-boundary tests.
- Added CI guardrails: backend lint + platform smoke, CLI setup dry-run, frontend SDK drift check.
- Stubbed hermetic platform smoke (health, JWKS, stub agent registry) for CI.
- Activity log: refactored service/registry package, wired additional emitters (auth logout/password/service-account, workflow completion, billing bridge, vector sync, container lifecycle), added cleanup recipe/settings docs, and tests for registry/service.
- Activity log: added conversation.created instrumentation, repo pagination/filter tests, activity API + SSE contract tests, and emitter touchpoint tests (billing bridge, vector sync worker, container lifecycle); tracker/doc refreshed.
- Activity log: merged divergent Alembic heads into `20251202_120000` to unblock deployment; tracker rollout notes updated.

## v0.1.0
- Initial pre-release scaffold for FastAPI backend, Next.js frontend, and Starter CLI.
