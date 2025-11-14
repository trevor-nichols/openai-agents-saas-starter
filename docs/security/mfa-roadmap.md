# MFA Roadmap

_Last updated: 11 Nov 2025_

This document captures the staged rollout for tenant-wide multi-factor authentication.

## Phase 1 — Foundations (Complete)
- Identify target factors: primary passkeys (WebAuthn) with TOTP backup codes.
- Extend auth token payload to track MFA enrollment + enforcement intent.
- Document UX flows (dashboard + CLI) and threat model updates.

## Phase 2 — Admin Preview (Target: Jan 2026)
- Allow tenant owners to self-enroll in passkeys and generate recovery codes.
- Surface enforcement toggle (owner-only) but keep it soft-disabled until monitoring stabilizes.
- Add audit events + analytics for MFA enrollment/removal.

## Phase 3 — Tenant Enforcement (Target: Feb 2026)
- Enable hard enforcement per tenant/role (owner/admin/member scopes).
- Update onboarding/signup to require MFA for privileged roles.
- Wire CLI + service-account issuance workflows to respect MFA enrollment state.

## Phase 4 — Enterprise Enhancements (Target: Mar 2026)
- Add optional hardware key requirement.
- Integrate with future IdP/SAML adapters for customers that centralize MFA elsewhere.
- Ship runbooks + incident response guidance.

### Tracking & Status
- Owner: Platform Foundations (Security & Auth pod)
- Epic: `SEC-MFA-001` in Linear
- Dependencies: Auth service support for passkeys, dashboard UI for enrollment, CLI prompts.

For questions or design proposals, open a discussion in `docs/security/` or reach out in #platform-security.
