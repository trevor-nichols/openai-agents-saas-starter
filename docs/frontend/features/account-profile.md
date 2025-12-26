# Account Profile UX & Implementation Spec

Updated: 11 Nov 2025  
Owner: Frontend Platform (Account & Security workstream)

## 1. Context & Goals

- Route: `app/(app)/(shell)/account/page.tsx` (tab `profile`)
- Panel: `features/account/components/ProfilePanel.tsx`
- Objective: surface a trustworthy snapshot of the signed-in human + their tenant in the new glass UI while reusing the shared foundation kit.
- Success signals:
  - Users immediately see who is signed in, their plan/role, and whether their email is verified.
  - Tenant metadata (slug, seats, billing plan, created/updated timestamps) is visible without navigating to billing.
  - Verification nudges (resend email) are actionable with instant feedback; profile editing is intentionally disabled in this release.
  - Screen leverages `components/ui/foundation` + `components/ui/states`, no bespoke chroming.

## 2. User Stories

1. **Identity glance** – “As a signed-in user, I want to confirm my avatar, display name, and email so I know I’m operating in the right tenant.”
2. **Verification assurance** – “If my email isn’t verified, I see a call-to-action to fix it; once verified I see a confirmation badge.”
3. **Tenant awareness** – “I can see which tenant I’m in, what plan it’s on, seat usage, and when it was created/updated.”
4. **Role clarity** – “I can see my role (owner/admin/member) and understand the impact (e.g., who can issue service accounts).”
5. **Service-account discoverability** – “I can jump to sessions/service accounts for deeper management.”

## 3. Data Sources & Hooks

| Need | Source | Hook/Action | Notes |
| ---- | ------ | ----------- | ----- |
| Current session (user id, email, verified flag, tenant id) | `/api/v1/auth/me` | `useAccountProfileQuery` | Query key `['account', 'session']`. Hydrate during SSR when possible. |
| Rich user profile (display name, avatar URL, role, last login) | `getCurrentUserProfile` (existing server action or REST mirror) | same hook, merged response | Compose requests server-side if the REST endpoint already includes session data. |
| Tenant metadata (name, slug, plan tier, seats, created_at, updated_at) | `/api/billing/tenants/:id` or existing account service | `useAccountProfileQuery` dependent request | Omit usage metrics if the billing API does not provide stable fields. |
| Email verification resend | `app/actions/auth/email.ts#resendVerificationEmail` | `useResendVerificationMutation` | Wraps server action → `useToast` success/error. |
| Profile mutation (display name/photo) | Not supported in this release | N/A | The profile UI is read-only; no mutation hooks are exposed. |

Implementation Notes:
- House hooks in `web-app/lib/queries/account.ts`.
- Return structured data object `{ user, tenant, verification, meta }` so UI components stay simple.
- Skeleton: reuse `components/ui/states/SkeletonPanel`.
- Errors bubble to the route-level `error.tsx`, which renders `ErrorState` + a “Try again” button calling `router.refresh()`.

## 4. Component Layout (Desktop)

```
——————————————————————————————————————————————
| Identity GlassPanel (50%) | Tenant Snapshot GlassPanel (50%) |
| ----------------------------------------------------------- |
| Verification Alert (if needed) spans full width             |
| ----------------------------------------------------------- |
| Metadata Drawer (Collapsible/Accordion)                     |
——————————————————————————————————————————————
```

### 4.1 Identity Panel
- Wrapper: `GlassPanel` with `SectionHeader` title “Identity”.
- Content:
  - `Avatar` (48px) + text stack (name, email).
  - `InlineTag` tone=“positive” when verified, tone=“warning” otherwise.
  - `Button` variant=`secondary` labeled “Resend verification” (disabled after a successful resend).
  - “Edit profile” is not available in this release; keep the UI read-only.

### 4.2 Tenant Snapshot
- Wrapper: `GlassPanel` + `SectionHeader` (“Tenant”).
- `KeyValueList` entries: tenant name, slug, plan, seat usage, created, updated, role.
- `InlineTag` for plan tier (e.g., “Scale plan” accent color).
- CTA row with `Button` link to `/billing` and `/account?tab=automation`.

### 4.3 Verification Alert Row
- Component: `Alert` variant=`destructive` with copy about confirming email.
- Actions: `Button` (primary) to resend, `Button` (ghost) “Need help?” linking to docs.
- Hidden when `user.emailVerified === true`; replaced with `InlineTag` inside identity panel.

### 4.4 Metadata Drawer
- Use `accordion.tsx` or `collapsible.tsx`.
- Sections:
  1. **Recent activity** – list last login, device, IP using the existing session payload (no extra fetch).
  2. **Service accounts** – summary count + link to `/account?tab=automation`.
  3. **Session management** – link to `/account?tab=sessions`.
- Each section uses `SectionHeader` mini variant + `KeyValueList`.

## 5. Interaction & State Handling

- Queries load concurrently; display `SkeletonPanel` loading states for each GlassPanel until data resolves.
- Failed query → route error boundary; partial failures degrade gracefully (e.g., tenant call fails, still show user data with inline `ErrorState`).
- `useResendVerificationMutation` disables button while pending, success toast “Verification email sent to {email}”, error toast includes message from backend.
- Analytics events are not emitted in this release.
- Accessibility: ensure alert/InlineTag text provides screen-reader context (“Email verified”, “Email unverified – action required”).

## 6. Acceptance & Test Plan

- Storybook-like checklist:
  - Verified user snapshot matches Figma tokens (avatar fallback letters, InlineTag positive).
  - Unverified user sees alert row, resend button, success toast.
  - Tenant data renders correctly when partial fields missing (fallback text “—”).
  - Skeletons render on slow network.
  - Toasts triggered for resend success/error.
- Automated:
  - Jest/RTL test for `AccountIdentityPanel` covering verified/unverified states.
  - Integration test for `useAccountProfileQuery` verifying query key + data shaping.

## 7. Decisions & Follow-Ups

1. **Profile editing scope** – The profile tab is read-only in this release. Do not expose mutation hooks or editing flows.  
2. **Tenant metadata source** – `useAccountProfileQuery` fetches `/api/auth/session` for user+tenant IDs, then calls `/api/billing/tenants/:id` for plan tier, seats, and timestamps. Billing remains the source of truth for subscription context.  
3. **Usage visualization** – Stick to textual `KeyValueList` summaries (plan, seats, renewal date) and deep-link to `/billing` for detailed charts. No inline mini-charts in profile.  
4. **Last login/device data** – Show only the fields exposed by the existing sessions endpoint (last login timestamp) and point users to `/account?tab=sessions` for full history. The metadata drawer lists the latest timestamp and includes CTA links to the dedicated Sessions/Service Accounts tabs.

Keep this spec aligned with backend capabilities.
