# Authentication Review Brief (Draft)

**Status:** Ready for stakeholder review  
**Proposed Review Slot:** Friday, November 7, 2025 · 10:00–10:30 AM Pacific  
**Attendees:** Platform Security Guild, Backend Auth Pod, Billing Pod lead, Frontend Web representative, SRE liaison (optional)

---

## 1. Decisions Required

1. **JWT Consumer Alignment:** Approve proposed `auth_audience` identifiers and scope taxonomy updates outlined in `docs/security/jwt-consumer-matrix.md`.  
2. **Key Storage Guarantees:** Ratify Vault HA + sealed volume SLA assumptions captured in `MILESTONE_AUTH_EDDSA_TRACKER.md` and confirm rotation blackout windows.  
3. **Refresh Token Handling:** Confirm frontend refresh-token strategy (HTTP-only cookie vs. withheld) and client JWKS usage per §9 of `docs/architecture/authentication-ed25519.md`.  
4. **Service Account Issuance Flow:** Decide on token provisioning approach for analytics, billing workers, support console, and synthetic monitors (direct issuance vs. STS exchange).  
5. **Scope Enforcement Roadmap:** Approve sequencing for rolling `require_current_user` + scope checks across `/agents`, `/chat`, `/conversations`, `/tools`.  
6. **Observability Coverage:** Validate metrics/logging requirements (R17–R20 in `docs/security/auth-threat-model.md`) and assign owners for dashboard + alert buildout.

## 2. Success Metrics & Acceptance Criteria

- **Coverage:** 100% of production JWTs issued and verified with Ed25519 by AUTH-003 completion; legacy HS256 path disabled in prod.  
- **Key Hygiene:** Rotation completed within 30 days with overlap window ≤24 hours; no rotation-induced outages.  
- **Revocation Efficacy:** Refresh token misuse detected and revoked within 60 seconds; reconciliation jobs report <0.5% drift.  
- **Availability:** JWT issuance and verification maintain ≥99.9% success rate during rollout; Vault-related latency spikes stay <60 seconds with alerting in place.  
- **Observability:** Dashboards covering verification success/failure, key age, and revocation latency live before AUTH-005 sign-off; alerts actionable (<10 false positives per month).  
- **Documentation & Runbooks:** Rotation SOP, incident response playbooks, and consumer integration guides published prior to production cutover.

## 3. Milestone Sequencing & Proposed Owners

| Milestone | Summary | Proposed Owner(s) | Key Dependencies |
| --- | --- | --- | --- |
| AUTH-002 – Ed25519 Key Infrastructure | Implement `app/core/keys.py`, rotation CLI, secret-manager adapter, and JWK publication pipeline. | Backend Auth Pod (lead), Platform Security tooling support | Finalized SLA assumptions, consumer matrix decisions |
| AUTH-003 – JWT Service Refactor | Swap `app/core/security.py` to signer/validator interfaces, enforce claim schema, add revocation store integration & tests. | Backend Auth Pod (lead), QA for coverage | AUTH-002 deliverables, scope taxonomy approval |
| AUTH-004 – JWKS Distribution Surface | Ship JWKS endpoint, caching headers, Next.js integration tests, documentation for consumers. | Backend Auth + Frontend Web collaboration | AUTH-002 key publishing, consumer matrix sign-off |
| AUTH-005 – Observability & Alerts | Implement structured logs, Prometheus metrics, dashboards, alert thresholds, runbooks. | SRE liaison (lead) with Backend Auth support | AUTH-003 verification hooks, metrics requirements approval |
| AUTH-006 – Staged Rollout & Postmortem | Execute dual-signing canary, production cutover, retrospective documentation, lessons learned. | Platform Security Guild (lead) with cross-team participation | Successful completion of AUTH-002 → AUTH-005, meeting acceptance metrics |

## 4. Pre-read Materials

- `docs/security/auth-threat-model.md` (updated threat scenarios, controls, and resolved decisions)  
- `docs/architecture/authentication-ed25519.md` (architecture blueprint)  
- `docs/security/jwt-consumer-matrix.md` (consumer inventory & audiences)  
- `MILESTONE_AUTH_EDDSA_TRACKER.md` (milestone plan with SLA notes)

## 5. Agenda (30 Minutes)

1. **Opening & Objectives (5 min)** — Align on meeting goals, confirm attendees.  
2. **Threat Model & Architecture Highlights (10 min)** — Review key updates and decisions outstanding.  
3. **Consumer Matrix & SLA Review (10 min)** — Validate audiences, scopes, and operational constraints.  
4. **Decision Summary & Next Steps (5 min)** — Confirm owners, timelines, and action items post-meeting.

## Appendix A — Audience Identifier Glossary

- **`agent-api`** — Default audience for interactive API consumers (FastAPI routers, frontend application).  
- **`analytics-service`** — Proposed audience for batch analytics and ETL jobs running in the data environment.  
- **`billing-worker`** — Proposed audience for backend billing workers and webhook processors.  
- **`support-console`** — Proposed audience for internal support and operations tooling.  
- **`synthetic-monitor`** — Proposed audience for reliability/synthetic monitoring agents.

> Prepared by: Backend Auth Pod · November 6, 2025
