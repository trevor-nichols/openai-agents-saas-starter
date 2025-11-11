# Account Service Accounts UX & Implementation Spec

Updated: 11 Nov 2025  
Owner: Frontend Platform (Account & Security workstream)

> **Status – 11 Nov 2025:** The account navigation no longer exposes this surface. Until backend list/revoke APIs exist, operators must continue using `starter_cli auth tokens issue-service-account`. Re-enable the UI only after FE-016 is unblocked.

## 1. Context & Goals

- Route: `app/(app)/account/service-accounts/page.tsx`
- Objective: expose a self-serve way to list existing service-account tokens and issue/revoke them without touching the CLI.
- Success signals:
  - Operators can see existing service-account refresh tokens (name, scopes, last used, created).
  - Issuing a token runs through the existing `/api/auth/service-accounts/issue` endpoint with success copy + copy-to-clipboard moment.
  - Revoking tokens updates the table immediately.
  - Empty/error states reuse shared components; no bespoke UI.

## 2. User Stories

1. **Audit service accounts** – “As a tenant owner, I can see which automation tokens exist, when they were created, and their scopes.”
2. **Issue token** – “I can mint a new service-account token for CI/CD, copy it once, and understand that it won't be shown again.”
3. **Revoke token** – “If I suspect a leak, I can revoke a token immediately.”
4. **Understand scope** – “I can see what scopes a token grants so I can follow least-privilege practices.”

## 3. Data Sources & Hooks

| Need | Source | Hook/Action | Notes |
| ---- | ------ | ----------- | ----- |
| List service accounts | `/api/auth/service-accounts` (assumed) or spec'd endpoint | `useServiceAccountsQuery` (new) | Confirm backend route; if not present, rely on CLI output? Need to verify actual API. |
| Issue token | `/api/auth/service-accounts/issue` | `useIssueServiceAccountMutation` | Already exposed in `app/actions/.../service-accounts`; wrap in client helper. |
| Revoke token | `/api/auth/service-accounts/revoke` or similar | `useRevokeServiceAccountMutation` | Need to confirm backend support for revocation endpoint. |
| Token copy-to-clipboard | Client-only | `useClipboard` or built-in navigator | Provide one-time display after issuance. |

Implementation notes:
- Reuse `lib/api/accountSecurity` pattern: new `lib/api/accountServiceAccounts.ts` + queries.
- Data-table columns: name/account, scopes (badges), last used, created, status, actions.
- Modal for issuing tokens uses `Dialog` + `Form` components with account name, optional description, scopes multi-select.
- On success, show token string + warning (copy now, not stored).

## 4. Component Layout

```
———————————————————————————————————————————
| Summary panel (count, last issued) + “Issue token” button |
|----------------------------------------------------------|
| Data table of service accounts                           |
|  - Columns as described above                             |
|----------------------------------------------------------|
| Issue token dialog (form + success state)                |
———————————————————————————————————————————
```

### 4.1 Summary Panel
- `GlassPanel` with total tokens count and small copy about when to use service accounts.
- Inline CTA button “Issue token” opening the dialog.

### 4.2 Data Table
- `DataTable` component.
- Actions column: `Button` to revoke (with confirmation dialog) and optional “Copy scopes” helper.
- If no tokens, `EmptyState` with CTA to issue first token.

### 4.3 Issue Token Dialog
- Form fields:
  - Account label (required).
  - Optional description.
  - Scopes multi-select (list from backend or constants).
  - Optional expiration/lifetime minutes.
- On submit, call mutation and render success view with token string in a copyable input + warning copy.

## 5. Interaction & State Handling

- Query invalidation after issue/revoke.
- Toasts for success/error.
- Revoke confirmation via `AlertDialog`.
- Copy token button uses `navigator.clipboard.writeText`.
- Success view instructs user to store the token; close button returns to table.
- Scope chips use `InlineTag`.

## 6. Acceptance & Test Plan

- Manual:
  - Table loads existing tokens.
  - Issuing new token shows success state + prevents closing without acknowledging copy.
  - Revoke action removes row + shows toast.
  - Empty state appears when no tokens.
- Automated:
  - Hook tests for `useServiceAccountsQuery` + issue/revoke mutations.
  - RTL test covering issue dialog flow (form validation + success view).
  - Snapshot for table row rendering (scopes, statuses).

## 7. Decisions & Follow-Ups

1. **Listing endpoint** – Add `GET /api/v1/auth/service-accounts` that returns `service_account_tokens` data (account, tenant, scopes, created, last_used, revoked). UI will block on this endpoint shipping.
2. **Revoke endpoint** – Add `DELETE /api/v1/auth/service-accounts/{token_id}` wired to `AuthService.revoke_service_account_token`. Frontend will call this for row actions.
3. **Tenant context** – Issuance always uses the current tenant (derived from the session). Cross-tenant issuance stays in the CLI.
4. **Scopes list** – Use the service-account catalog (`service_accounts.yaml`) as the source of truth; expose it via the listing endpoint or a lightweight catalog endpoint so the UI doesn’t hard-code scopes forever.
5. **Success acknowledgement** – Require an explicit “I copied it” confirmation before closing the issuance dialog since tokens are only shown once.

> Update tracker/spec again if backend capabilities differ when implemented.
