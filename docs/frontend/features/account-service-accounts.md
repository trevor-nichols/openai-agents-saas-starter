# Account Service Accounts UX & Implementation Spec

Updated: 11 Nov 2025  
Owner: Frontend Platform (Account & Security workstream)

> **Status – 12 Nov 2025:** Automation tab now lists, revokes, and issues tokens. The Issue Token dialog in `/account?tab=automation` calls `/app/api/auth/service-accounts/browser-issue`, which proxies the FastAPI bridge (`POST /api/v1/auth/service-accounts/browser-issue`) and requires a justification string for auditing.

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
| List service accounts | `/app/api/auth/service-accounts/tokens` → FastAPI `/api/v1/auth/service-accounts/tokens` | `useServiceAccountTokensQuery` + `DataTable` | Query params support `account`, `status`, pagination; response normalized to camelCase. |
| Revoke token | `/app/api/auth/service-accounts/tokens/{jti}/revoke` | `useRevokeServiceAccountTokenMutation` | Confirms via AlertDialog + optional reason piped to backend for audits. |
| Issue token | `/app/api/auth/service-accounts/browser-issue` → FastAPI `/api/v1/auth/service-accounts/browser-issue` | `useIssueServiceAccountTokenMutation` | Tenant admins enter account, scopes, optional metadata, and a justification. The bridge signs via Vault Transit and returns the refresh token once; the dialog renders the copy-once UX. |
| Token copy-to-clipboard | N/A (issuance deferred) | Future `useCopyToClipboard` helper | Only needed once web issuance is approved. |

Implementation notes:
- `lib/api/accountServiceAccounts.ts` proxies the Next routes so client components only ever call `/app/api/...` endpoints.
- `lib/server/services/auth/serviceAccounts.ts` centralizes SDK calls (list + revoke) with camelCase mapping for UI consumption.
- Automation tab uses `DataTable` + TanStack Query for caching, and an `AlertDialog` flow to capture optional revoke reasons.
- Issuance dialog uses the shared mutation + dialog component; copy guidance and telemetry auto-log via the backend bridge. Update the UI copy only if security requirements change.

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
