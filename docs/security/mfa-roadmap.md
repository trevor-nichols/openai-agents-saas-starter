# MFA Status & Enablement Requirements

_Last updated: 11 Nov 2025_

Multi-factor authentication (MFA) is not enabled in this release. This document captures the requirements that any MFA enablement must satisfy so security and UX remain consistent across backend, web app, and console tooling.

## Required Factors
- Primary factor: passkeys (WebAuthn).
- Backup factor: TOTP recovery codes.

## Enrollment & Enforcement Requirements
- Enrollment must be scoped to tenant owners first; enforcement controls must be owner-gated.
- Enforcement must be role-aware (owner/admin/member scopes) and auditable.
- Onboarding and privileged actions must respect MFA enrollment state once enforcement is enabled.

## Audit & Telemetry Requirements
- Emit audit events for MFA enrollment/removal.
- Add structured logs and metrics for enrollment, enforcement toggles, and MFA challenge failures.

## Operational Guidance
- Provide CLI and dashboard flows for enrollment, recovery codes, and enforcement toggles.
- Document incident response steps and recovery flows in the security runbooks.

## Ownership
- Owner: Platform Foundations (Security & Auth pod)
