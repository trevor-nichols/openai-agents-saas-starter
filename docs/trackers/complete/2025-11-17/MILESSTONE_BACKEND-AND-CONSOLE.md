## Current State (Nov 17, 2025)
- **Backend**: All core bounded contexts (auth, chat/agents, conversations, billing/Stripe, tenant settings, signup, status, observability) are implemented with async SQLAlchemy/Redis backends, Alembic migrations, dependency-injected services, and Prometheus + health endpoints.
- **Starter Console**: Wizard milestones M1–M4 plus supporting commands (auth/provider validation/infra/stripe/release/status/secrets) automate environment provisioning, secret rotation, dependency checks, and audit artifact generation under `var/reports`.
- **Testing & Docs**: Backend + CLI units cover major workflows (signup, wizard sections, providers), while shared docs (`docs/ops/provider-parity.md`, `docs/trackers/*`) capture current flows. Observability instrumentation is live.

## Blocking Items to Reach “Complete”
| ID | Area | Description | Owner | Status/Notes |
| --- | --- | --- | --- | --- |
| BCL-01 | Agents | Update `app/services/agent_service.py` to default to GPT‑5 reasoning models per product spec; make model IDs configurable via settings/env to avoid future code edits. | Backend Eng | DONE – `AGENT_MODEL_*` settings now default to GPT-5.1 reasoning models. |
| BCL-02 | Integrations | Slack notifier landed: settings + CLI collect bot tokens/channels, `StatusAlertDispatcher` fans out to Slack with retries/metrics, and docs live at `docs/integrations/slack.md`. | Backend Eng | DONE |
| BCL-03 | Ops Evidence | Capture and attach proof of successful `hatch run lint`, `hatch run typecheck`, representative backend test suite run, and a full CLI wizard execution (screenshots/log excerpts) to `docs/ops` or `var/reports` for compliance sign-off. | Platform Eng | DONE – artifacts stored under `var/reports/ops-evidence-20251117T225150Z-*`. |

## Optional / Nice-to-Have Enhancements
- **Conversation Search**: Upgrade `ConversationService.search` to leverage Postgres full-text or embedding search instead of linear substring scans.
- **Wizard UX**: Add progress indicator + elapsed time display and allow exporting headless answers as JSON for CI, improving operator experience.
- **Documentation Refresh**: Sync README + `docs/ops/provider-parity.md` with the latest automation/reporting behaviours introduced by the wizard.
- **Stripe Evidence Automation**: Extend `starter-console release db` to capture Stripe CLI transcript + seed artifacts automatically for auditors.

## Recent Analysis Notes
- Authentication stack includes password history, lockout counters (`RedisLockoutStore`), GeoIP-aware session logging, service-account issuance, Vault/HMAC signing, and CLI parity for key rotation.
- Billing/Stripe flow includes plan catalogs, usage metering, Redis SSE streaming, webhook dispatcher + retry worker, and provisioning helpers in the CLI (`stripe setup`, release workflow).
- Status subscriptions encrypt targets, send Resend/webhook notifications, and expose public APIs + RSS feeds; CLI `status` command surfaces operator management.
- Setup wizard orchestrates secrets, providers, observability, signup, and frontend envs with automation toggles for Docker/Vault/Stripe, writing both JSON + Markdown summaries plus verification artifacts.
