# Dev User Automation Milestone

_Last updated: November 20, 2025_

## Objective
Fold the local dev-user seeding flow into the Starter CLI setup wizard so operators never leave the TUI, keeping credentials safe and the experience consistent with existing automation phases.

## Scope & Exit Criteria
| Area | In Scope | Exit Criteria |
| --- | --- | --- |
| Wizard UX | Prompt for dev-user details inside the wizard; headless friendly. | New “Dev User” section runs in the TUI and headless modes without blocking for input. |
| Automation | Run seeding automatically after migrations, when enabled. | Automation phase `Dev User Seed` reports pending/running/success/failure like other phases. |
| Security | Password handling. | Password never written to disk; printed once to console when auto-generated; strength-checked. |
| Docs & Reports | Operator guidance and audit trail. | README + milestone summary mention the embedded seeding; Markdown/JSON summaries include status (not the password). |

## Phases
| Phase | Focus | Status | Target |
| --- | --- | --- | --- |
| P1 Tracker & design | Create tracker, outline approach. | ✅ Done | Nov 20 |
| P2 Implementation | Code + tests + docs updates. | ✅ Done | Nov 20 |
| P3 Verification | Manual happy-path run via `just setup-demo-lite`; update tracker. | ⏳ Pending | Nov 20 |

## Task List
- [x] Add automation phase `DEV_USER` with profile gating to `demo` and dependency on migrations.
- [x] Add “Dev User” section prompts (email, display, tenant slug/name, role, password/auto-generate).
- [x] Implement reusable `seed_dev_user(...)` helper inside `starter_cli` (no disk secret leaks).
- [x] Wire automation to run post-wizard, update UI + summary artifacts.
- [x] Remove post-wizard `just seed-dev-user` call from `setup-demo-lite/full`; keep standalone recipe.
- [x] Update docs: `starter_cli/README.md` and milestone tracker references.
- [x] Add unit test covering automation gating + invocation.
- [x] Add demo-token automation to mint a demo service-account token without starting the API.
- [x] Add catalog entry for `demo-bot` service account (chat:write, conversations:read).
- [x] Add unit test covering demo-token automation trigger.
- [x] Manual verification: `just setup-demo-lite` end-to-end run and confirm console password handling + demo token output.
- [ ] Fix CLI inventory parsing to tolerate generated format and re-run full CLI unit suite.

## Notes / Risks
- Avoid duplicating seeding when reruns happen; guard on existing email/tenant combo.
- Headless runs must not hang; auto-generate password when not provided via `--var`.
- Keep password out of JSON/Markdown artifacts to preserve audit hygiene.
