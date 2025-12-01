# Milestone: Resend Transactional Email Delivery

## Context
We need to replace the placeholder logging notifiers with a production-ready Resend integration for both email verification and password reset flows. The work must keep the existing FastAPI contracts, maintain Redis token storage, and meet the repo's reliability/observability standards.

## Success Criteria
- All verification/reset emails go through Resend in non-local environments, with graceful fallbacks for dev/test.
- Operators can configure sender domains, template IDs, and API keys solely via settings/env vars.
- Failures bubble up with actionable logs/metrics, and tests cover the new integration path.

## Task List
1. **Configuration surface** ✅
   - Extended `app/core/settings/security.py` with Resend settings (API key, base url, from address, optional template IDs, enable toggle).
   - Documented new env vars in `.env.local.example`, `.env.local`, and `README.md`.
2. **Resend client adapter** ✅
   - Introduced `app/infrastructure/notifications/resend.py` with an async-friendly wrapper over the Resend SDK, payload helpers, and logging hooks.
   - Added a cached `get_resend_email_adapter` factory for reuse and normalized recipient/tag handling.
3. **Notifier implementations & wiring** ✅
   - Implemented `ResendEmailVerificationNotifier` and `ResendPasswordResetNotifier`, including fallback HTML/text bodies when templates are absent.
   - Service builders now select the Resend notifier whenever `RESEND_EMAIL_ENABLED=true`, otherwise defaulting to logging-only mode.
4. **Template + content strategy** ✅
   - Added local template helpers under `app/presentation/emails/templates.py` that generate HTML/text bodies plus CTA links.
   - Introduced `APP_PUBLIC_URL` so operators control the base URL used in verification/reset links; env files + README updated.
5. **Observability & error handling** ✅
   - Adapter now records Prometheus counters/histograms plus structured logs, and routes translate delivery failures into HTTP 502 responses.
6. **Testing** ✅
   - Added unit tests for template helpers and adapter send paths, plus contract tests covering delivery failures.
7. **Documentation & cleanup** ✅
   - Added `docs/ops/resend-email-runbook.md` with environment setup, template previews, monitoring, and troubleshooting guidance.
   - Once merged, archive this tracker into `docs/trackers/complete/`.

## Current Status
- All tasks complete. After code review/verification, move this tracker to `docs/trackers/complete/`.
