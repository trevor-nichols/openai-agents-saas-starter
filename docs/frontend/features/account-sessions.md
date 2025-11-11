# Account Sessions UX & Implementation Spec

Updated: 11 Nov 2025  
Owner: Frontend Platform (Account & Security workstream)

## 1. Context & Goals

- Route: `app/(app)/account/sessions/page.tsx`
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
| Session list | `/api/auth/sessions` (GET) | `useUserSessionsQuery` (new) | Accepts pagination params (offset/limit) + optional include_revoked toggle; default limit 10. |
| Revoke session | `/api/auth/sessions/{id}` (DELETE) | `useRevokeSessionMutation` | Takes session ID, optimistic update removes row. |
| Logout all | `/api/auth/logout/all` (POST) | `useLogoutAllSessionsMutation` | After success, table refetches. |
| Current session ID | `useAccountProfileQuery` / session payload | `useAccountProfileQuery` | Highlight current session row. |

Implementation notes:
- API helper under `lib/api/accountSessions.ts` to wrap the above endpoints.
- Query helpers in `lib/queries/accountSessions.ts` using TanStack Query.
- Data-table columns: device (fallback from user agent), IP/geo, last active, created, status, actions.
- Pagination: simple `limit=10`, `offset` via data-table pagination controls; start with client-side state since API already supports limit/offset.

## 4. Component Layout

```
———————————————————————————————————————————
| Sessions summary (cards: active count, last logout-all) |
|--------------------------------------------------------|
| Sessions Data Table (GlassPanel + DataTable kit)       |
|  - Toolbar (search/filter placeholder, logout-all btn) |
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
  - `Button` variant `destructive` labeled “Sign out everywhere”, triggers logout-all mutation (with confirm dialog).
  - Search box placeholder (wired later once API supports filtering).

### 4.3 Empty/Error States
- If no sessions, show `EmptyState` with copy “No active sessions—sign in from another device to see it here.”
- Error → `ErrorState` with retry.

## 5. Interaction & State Handling

- `useUserSessionsQuery` manages pagination state (`page`, `pageSize`).
- Revoking a row triggers optimistic update: remove the session locally, then refetch on success.
- Logout-all clears the table via refetch; show success toast (“Signed out of X sessions” using response payload).
- Current session row uses `profile.raw.session?.session_id` for highlighting and disables revoke action.
- Confirmations: show `AlertDialog` before calling logout-all.
- Analytics stub (`account_sessions_action`) for revoke/logout-all events (future).

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

1. **Filtering/search** – Deferred. Keep toolbar hooks ready but don’t ship client-side filtering until the API exposes first-party query params.
2. **Revoked sessions** – Hide them for v1 (keep `include_revoked=false`). We’ll add a toggle + grayed-out rows when audit mode is prioritized.
3. **Single-session confirmation** – No modal; a direct click + toast is sufficient. Logout-all retains the confirmation dialog.
4. **Logout-all feedback** – Use the `{ revoked: number }` payload from `/auth/logout/all` to show the exact count in the success toast.

> Update tracker/spec if these assumptions change once backend capabilities expand.
