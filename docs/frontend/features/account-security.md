# Account Security UX & Implementation Spec

Updated: 11 Nov 2025  
Owner: Frontend Platform (Account & Security workstream)

## 1. Context & Goals

- Route: `app/(app)/account/security/page.tsx`
- Objective: provide a trustworthy surface for password maintenance, upcoming MFA, and recent authentication activity using the shared glass UI.
- Success signals:
  - Password change flows re-use the existing server actions with inline validation + toasts.
  - MFA placeholder explains roadmap + owner requirements without promising functionality that isn’t live.
  - Recent activity summarizes last-login data and deep-links to the full Sessions page.
  - Page reuses `components/ui/foundation` + `components/ui/states` with consistent empty/error handling.

## 2. User Stories

1. **Change password** – “As a user, I need to rotate my password and know all other sessions were revoked.”
2. **MFA awareness** – “As an admin, I want to understand when MFA is coming, what form it will take, and what prerequisites exist.”
3. **Recent auth activity** – “I want a quick glance at my last login and session risk indicators with a link to the full sessions table.”
4. **Security messaging** – “I should see copy about password policy, best practices, and links to docs/support.”

## 3. Data Sources & Hooks

| Need | Source | Hook/Action | Notes |
| ---- | ------ | ----------- | ----- |
| Password change | `app/api/auth/password/change` server action | `useChangePasswordMutation` (new) | Wraps existing se rver action + toasts, revokes sessions server-side automatically. |
| MFA status placeholder | Static copy (until backend lands) | N/A | Document roadmap + CLI flag hook-ups. |
| Recent session summary | `/api/auth/session` + `/api/auth/sessions?limit=5` | `useSessionSummaryQuery` (optional) / reuse `useAccountProfileQuery` data | For now, show last login timestamp from profile session data; link to `/account/sessions`. |
| Docs/support links | `docs/security/` content | Static links | Keep copy light; point to runbook. |

Implementation notes:
- Password form uses `react-hook-form` + `zod` (or existing form helper) with client-side validation aligned with policy copy.
- Skeleton states via `components/ui/states/SkeletonPanel`.
- Errors surface inline per panel, plus fallback to route-group `error.tsx` once added.

## 4. Component Layout (Desktop)

```
———————————————————————————————————————————
| Password Panel (GlassPanel) | MFA Panel (GlassPanel) |
|------------------------------------------------------|
| Recent Activity panel (full width)                   |
———————————————————————————————————————————
```

### 4.1 Password Panel
- `SectionHeader` with “Password & Sign-in”
- `Form` inputs: Current password, New password, Confirm new password.
- Inline policy reminder (14+ chars, multi-class, zxcvbn≥3).
- Submit button triggers mutation, disables while pending, shows success/error toasts.
- Helper copy indicating all sessions revoke after change.

### 4.2 MFA Panel
- Copy describing upcoming MFA (TOTP + passkey roadmap), CTA button disabled (“Coming soon”) with tooltip.
- `InlineTag` for status (e.g., “Planned Q1 2026”).
- Additional copy linking to docs/support for enterprise SSO.

### 4.3 Recent Activity Panel
- `KeyValueList` showing last login timestamp, session expiry, count of active sessions (optional).
- Link buttons to `/account/sessions` and `/account/service-accounts`.
- If data fetch fails, show inline `ErrorState` or `Alert` with retry.

## 5. Interaction & State Handling

- Password form:
  - Client validation ensures required fields + match before hitting server.
  - On success, reset form + show success toast: “Password updated. Other sessions were signed out.”
  - On failure, display error toast + inline helper text from backend.
- Skeletons render while session summary loads.
- `useAccountProfileQuery` reuse: pass down session expiry + last login (from token payload when available).
- Analytics hook (future): track `account_security_action` events for change password + MFA interest.

## 6. Acceptance & Test Plan

- **Manual checklist**
  - Invalid form states show validation copy.
  - Success resets fields and shows toast.
  - MFA panel clearly indicates placeholder.
  - Recent activity shows data or graceful fallback.
- **Automated**
  - RTL test for `SecurityPasswordForm` covering success/error paths (mock mutation).
  - Snapshot test for MFA panel (ensures copy/tags rendered).
  - Hook test for `useChangePasswordMutation` verifying error propagation.

## 7. Decisions & Follow-Ups

1. **Password strength meter** – Defer client-side zxcvbn meter. Enforce matching fields + show policy copy, rely on backend `password_policy` errors for strength feedback. Revisit when product wants inline scoring.
2. **Recent activity data** – Keep the panel lightweight (last login + session expiry from the session payload) and deep-link to `/account/sessions` for detailed device history. No extra fetch until the Sessions page ships.
3. **Logout-all control** – Leave the “Sign out of other devices” button on the Sessions page only. Security panel copy can reference that location.
4. **MFA roadmap link** – Link to a repo doc (`docs/security/mfa-roadmap.md` or similar) so the CTA remains stable and version-controlled instead of pointing to Notion.

> Update this spec + tracker if any of these decisions change once MFA/backend features land.
