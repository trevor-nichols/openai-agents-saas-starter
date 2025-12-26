# Account Security UX & Implementation Spec

Updated: 11 Nov 2025  
Owner: Frontend Platform (Account & Security workstream)

## 1. Context & Goals

- Route: `app/(app)/(shell)/account/page.tsx` (tab `security`)
- Panel: `features/account/components/SecurityPanel.tsx`
- Objective: provide a trustworthy surface for password maintenance, MFA status (not enabled in this release), recent authentication activity, and operator-led password resets using the shared glass UI.
- Success signals:
  - Password change flows re-use the existing server actions with inline validation + toasts.
  - MFA panel communicates that multi-factor authentication is not enabled in this release and lists prerequisites without over-promising.
  - Recent activity summarizes last-login data and deep-links to the full Sessions page.
  - Admin resets stay scope-gated (`support:read`), revoke sessions, and make audit expectations explicit.
  - Page reuses `components/ui/foundation` + `components/ui/states` with consistent empty/error handling.

## 2. User Stories

1. **Change password** – “As a user, I need to rotate my password and know all other sessions were revoked.”
2. **MFA awareness** – “As an admin, I want to understand MFA status, what form it will take, and what prerequisites exist.”
3. **Recent auth activity** – “I want a quick glance at my last login and session risk indicators with a link to the full sessions table.”
4. **Admin password reset** – “As a support operator, I can reset a tenant user’s password with copy that reinforces audit logging and policy compliance.”
5. **Security messaging** – “I should see copy about password policy, best practices, and links to docs/support.”

## 3. Data Sources & Hooks

| Need | Source | Hook/Action | Notes |
| ---- | ------ | ----------- | ----- |
| Password change | `/api/v1/auth/password/change` | `useChangePasswordMutation` | Wraps the BFF route + toasts, revokes sessions server-side automatically. |
| Admin password reset | `/api/v1/auth/password/reset` (scope-guarded proxy) | `useAdminResetPasswordMutation` | Requires `support:read` + tenant context; revokes sessions and expects operator audit trail. |
| MFA status | Static copy | N/A | MFA is not enabled in this release; provide requirements and links to security docs. |
| Recent session summary | `/api/v1/auth/me` | `useAccountProfileQuery` | Use session payload metadata (last login, expiry) and link to `/account?tab=sessions`. |
| Docs/support links | `docs/security/` content | Static links | Keep copy light; point to runbook. |

Implementation notes:
- Password form uses `react-hook-form` + `zod` (or existing form helper) with client-side validation aligned with policy copy.
- Skeleton states via `components/ui/states/SkeletonPanel`.
- Errors surface inline per panel, plus fallback to route-group `error.tsx`.

## 4. Component Layout (Desktop)

```
———————————————————————————————————————————
| Password Panel (GlassPanel) | MFA Panel (GlassPanel) |
|------------------------------------------------------|
| Admin Reset panel (full width, operator only)        |
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
- Copy explaining MFA is not enabled in this release and listing required prerequisites.
- `InlineTag` for status (e.g., “Not enabled”).
- Links to docs/support for enterprise SSO.

### 4.3 Admin Reset Panel
- `SectionHeader` “Admin password reset” with `InlineTag` “Requires support:read”.
- Visible only when `profile.session.scopes` contains `support:read`; otherwise render a restricted card with doc link to the auth threat model.
- CTA button opens a dialog collecting `user_id`, `new_password`, and confirmation. Inline policy bullets mirror backend requirements.
- Submissions call `useAdminResetPasswordMutation`, show success/error toasts, close on success, and remind operators that sessions were revoked and the reset was logged.

### 4.4 Recent Activity Panel
- `KeyValueList` showing last login timestamp, session expiry, count of active sessions (optional).
- Link buttons to `/account?tab=sessions` and `/account?tab=automation`.
- If data fetch fails, show inline `ErrorState` or `Alert` with retry.

## 5. Interaction & State Handling

- Password form:
  - Client validation ensures required fields + match before hitting server.
  - On success, reset form + show success toast: “Password updated. Other sessions were signed out.”
  - On failure, display error toast + inline helper text from backend.
- Skeletons render while session summary loads.
- `useAccountProfileQuery` reuse: pass down session expiry + last login (from token payload when available).
- Analytics events are not emitted in this release.

## 6. Acceptance & Test Plan

- **Manual checklist**
  - Invalid form states show validation copy.
  - Success resets fields and shows toast.
  - MFA panel clearly indicates that MFA is not enabled in this release.
  - Admin reset dialog validates user id/password, requires support scope, and closes after success while noting session revocation.
  - Recent activity shows data or graceful fallback.
- **Automated**
  - RTL test for `SecurityPasswordForm` covering success/error paths (mock mutation).
  - Snapshot test for MFA panel (ensures copy/tags rendered).
  - Hook test for `useChangePasswordMutation` verifying error propagation.
- Route/unit test for `app/api/v1/auth/password/reset` covering scope guard + error mapping.

## 7. Decisions & Follow-Ups

1. **Password strength meter** – No client-side zxcvbn meter. Enforce matching fields + show policy copy, rely on backend `password_policy` errors for strength feedback.
2. **Recent activity data** – Keep the panel lightweight (last login + session expiry from the session payload) and deep-link to `/account?tab=sessions` for detailed device history. No extra fetch.
3. **Logout-all control** – Leave the “Sign out of other devices” button on the Sessions page only. Security panel copy can reference that location.
4. **MFA docs link** – Link to `docs/security/mfa-roadmap.md` so the CTA remains stable and version-controlled instead of pointing to external docs.

Keep this spec aligned with backend capabilities.
