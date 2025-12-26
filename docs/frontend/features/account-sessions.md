# Account Sessions UX & Implementation Spec

Updated: 11 Nov 2025  
Owner: Frontend Platform (Account & Security workstream)

## 1. Context & Goals

- Route: `app/(app)/(shell)/account/page.tsx` (tab `sessions`)
- Panel: `features/account/components/SessionsPanel.tsx`
- Objective: provide a transparent, actionable list of active sessions/devices with revoke controls that mirror backend capabilities.
- Success signals:
  - Users can see device/location metadata, last activity, and whether a session is the current one.
  - Revoking a single session updates the table immediately (TanStack cache).
  - “Sign out everywhere” drives the logout-all endpoint with clear confirmation copy.
  - Empty/error states reuse `components/ui/states` and the glass layout.

## 2. User Stories

1. **Audit sessions** – “As a user, I want to see where I’m signed in, including device, IP, location, and last activity.”
2. **Revoke a single device** – “If I don’t recognize a session, I can revoke it instantly and get confirmation.”
3. **Sign out everywhere** – “After a password change or incident, I can sign out of all other sessions from one button.”
4. **Understand limits** – “I can see retention (e.g., last 30 sessions) and know that revoked sessions move out of the active list.”

## 3. Data Sources & Hooks

| Need | Source | Hook/Action | Notes |
| ---- | ------ | ----------- | ----- |
| Session list | `/api/v1/auth/sessions` (GET) | `useUserSessionsQuery` | Accepts pagination params (offset/limit) + optional include_revoked toggle; Sessions UI uses `limit=50`. |
| Revoke session | `/api/v1/auth/sessions/{id}` (DELETE) | `useRevokeSessionMutation` | Takes session ID and invalidates the query cache. |
| Logout all | `/api/v1/auth/logout/all` (POST) | `useLogoutAllSessionsMutation` | After success, table refetches. |
| Current session ID | `useAccountProfileQuery` / session payload | `useAccountProfileQuery` | Highlight current session row. |

Implementation notes:
- API helper under `lib/api/accountSessions.ts` to wrap the above endpoints.
- Query helpers in `lib/queries/accountSessions.ts` using TanStack Query.
- Data-table columns: device (fallback from user agent), IP/geo, last active, created, status, actions.
- Pagination: the UI uses a fixed limit and does not render pagination controls. Limit/offset are available if paging is required.

## 4. Component Layout

```
———————————————————————————————————————————
| Sessions summary (cards: active count, last logout-all) |
|--------------------------------------------------------|
| Sessions Data Table (GlassPanel + DataTable kit)       |
|  - Toolbar (tenant filter + logout-all btn) |
———————————————————————————————————————————
```

### 4.1 Summary Cards
- Use `GlassPanel` with `SectionHeader`.
- `InlineTag` showing “Active sessions: N”.
- Optional `KeyValueList` entries (current session, last logout-all timestamp if payload provides).

### 4.2 Data Table
- Reuse `components/ui/data-table`.
- Columns:
  - Device (user agent summary + `Tooltip` for full string).
  - IP / location (use provided city/state fields; fallback to “Unknown”).
  - Last active (formatted date).
  - Created (formatted date).
  - Status (Active / Revoked with `InlineTag` tone).
  - Actions (revoke button, disabled on current session).
- Toolbar:
  - Tenant filter: All tenants / Current tenant / Specific tenant ID.
  - `Button` variant `destructive` labeled “Sign out everywhere”, triggers logout-all mutation (with confirm dialog).

### 4.3 Empty/Error States
- If no sessions, show `EmptyState` with copy “No active sessions—sign in from another device to see it here.”
- Error → `ErrorState` with retry.

## 5. Interaction & State Handling

- `useUserSessionsQuery` uses limit/offset parameters; the Sessions UI passes a fixed limit.
- Revoking a row invalidates the sessions query and refetches.
- Logout-all clears the table via refetch; show success toast (“Signed out of X sessions” using response payload).
- Current session rows are marked by the backend `current` flag and disable revoke.
- Confirmations: show `AlertDialog` before calling logout-all.
- Analytics events for revoke/logout-all are not emitted in this release.

## 6. Acceptance & Test Plan

- Manual:
  - Table renders sessions with correct formatting.
  - Revoke button removes row + shows toast.
  - Logout-all button disabled while mutation pending; success resets table.
  - Empty state shown when no sessions.
  - Current session row renders “Current device” badge and disables revoke.
- Automated:
  - Hook tests for `useUserSessionsQuery` (ensures query key + pagination).
  - RTL test for `SessionsTable` covering revoke action + disabled state for current session.
  - Snapshot or DOM test for empty/error states.

## 7. Decisions & Follow-Ups

1. **Tenant scope** – The toolbar allows filtering by all tenants, the current tenant, or a specific tenant ID. Session queries pass `tenantId` accordingly.
2. **Revoked sessions** – Hidden in this release (`include_revoked=false`). Audit-mode visibility is intentionally not exposed in the UI.
3. **Single-session confirmation** – No modal; a direct click + toast is sufficient. Logout-all retains the confirmation dialog.
4. **Logout-all feedback** – Use the `{ revoked: number }` payload from `/api/v1/auth/logout/all` to show the exact count in the success toast.

Keep this spec aligned with backend capabilities.
