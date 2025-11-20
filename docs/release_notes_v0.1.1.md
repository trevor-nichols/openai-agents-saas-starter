# Release notes: v0.1.1 (Contracts hardening & CI guardrails)

Highlights
- Extracted `starter_contracts` package (replaces `starter_shared`), keeping the shared config/secret/key contracts side-effect free and versionable.
- Added contract drift guards: JSON snapshots for settings/enums plus import-boundary tests to prevent accidental cross-layer coupling.
- CI guardrails: backend lint + platform smoke (health/JWKS/stub agent), CLI setup dry-run, frontend SDK drift check (regenerate and fail on diff).
- Added SBOM + dependency audits: pip-audit and CycloneDX for Python, pnpm audit and CycloneDX for frontend.

Upgrade notes
- Update imports from `starter_shared.*` → `starter_contracts.*`.
- Run `pnpm generate` (frontend) after pulling; CI enforces SDK drift.
- For tests, ensure dev deps (fakeredis, etc.) are installed via `hatch env create`.

Tagging guidance
- Tag this commit as `v0.1.1` after CI is green.
- Publish artifacts: `hatch build -t wheel` (includes `starter_contracts`), attach backend OpenAPI artifact(s) if desired.
- Changelog entry lives in `CHANGELOG.md`.
