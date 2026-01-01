# Roles & RBAC (Canonical)

**Status:** Active  
**Owner:** Platform Foundations  
**Last Updated:** 2025-12-31

This document is the single source of truth for role semantics in the starter.

## 1) Role Domains

We model **tenant roles** separately from **platform roles**.

### 1.1 TenantRole (tenant-scoped)

Canonical enum: `apps/api-service/src/app/domain/tenant_roles.py`

Values (low -> high):
- `viewer` - Read-only access to tenant data.
- `member` - Standard user access (create/update within assigned capabilities).
- `admin` - Tenant administration access (manage members, settings, billing flows).
- `owner` - Full tenant control (including irreversible or high-risk actions).

Rules:
- Every tenant membership has exactly one TenantRole.
- `member` is always >= `viewer` in role gates.
- Role ordering is authoritative for allow/deny checks.

### 1.2 PlatformRole (platform-scoped)

Canonical enum: `apps/api-service/src/app/domain/platform_roles.py`

Values:
- `platform_operator` - Internal operator role for cross-tenant support and incident response.

Rules:
- PlatformRole is stored on the user record and is **not** part of TenantRole.
- Platform operators may use explicit override headers where allowed by API design.

## 2) Token Claims

Access tokens include:
- `tenant_id` (active tenant context)
- `roles` (array of TenantRole values for the active tenant)
- `scopes` (granted scopes; not a substitute for TenantRole)

**Precedence:** When both are present, `roles` is authoritative. Scopes only infer a role if `roles` is missing.

## 3) Optional Down-Scoping Headers

Supported across many APIs:
- `X-Tenant-Id` (UUID)
- `X-Tenant-Role` (`viewer | member | admin | owner`)

Down-scoping is allowed only to **reduce** privileges relative to the authenticated token.

### 3.1 Operator Override Headers (platform-only)

Used for explicit, audited operator access when a tenant is suspended.

- `X-Operator-Override` (`true|1|yes|on`)  
- `X-Operator-Reason` (required, non-empty)

Rules:
- Requires operator scopes (`platform:operator` or `support:*`).
- Read-only only (safe methods such as `GET`).
- Never elevates tenant role; only bypasses suspended-tenant blocking for inspection.

## 4) Data Model Surface

- Tenant membership role: `tenant_user_memberships.role` (enum `tenant_role`)
- Platform role on user: `users.platform_role` (enum `platform_role`)

## 5) Change Policy

Any change to roles or ordering must update:
- `apps/api-service/src/app/domain/tenant_roles.py`
- `apps/api-service/src/app/domain/platform_roles.py`
- OpenAPI schemas and generated SDK
- This doc
