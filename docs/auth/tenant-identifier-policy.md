# Tenant Identifier Policy

_Last updated: 2026-01-02_

## Purpose

Establish a clear, predictable, and maintainable standard for tenant identification across the
platform. This removes ambiguity, improves auditability, and ensures consistent behavior in
all services and clients.

## Core Principle

- **Canonical identifier:** `tenant_id` (UUID). Used everywhere internally.
- **Human alias:** `tenant_slug` (string). Used only at boundary inputs where humans interact.

## Scope

Applies to:
- API service (FastAPI)
- Web app (Next.js + API routes)
- SDK/clients
- Starter Console and scripts

## Rules

### 1) Canonical Internal Usage

- All internal logic, persistence, and inter-service calls must use `tenant_id`.
- Logs and events should prefer `tenant_id`. `tenant_slug` may be included as supplemental
  context but must never be the primary key.

### 2) Boundary Inputs Only for `tenant_slug`

`tenant_slug` is allowed only at boundary inputs such as:
- SSO entry flows (provider list/start)
- Signup/register (user-facing onboarding)
- Console/CLI flows where humans enter a tenant
- Admin UI selectors and marketing URLs

**Rule:** any boundary that accepts `tenant_slug` must resolve it to `tenant_id` before business
logic executes.

### 3) Explicitness (No Guessing)

- Auto-guessing or inference from a single free-form string is forbidden.
- Boundary APIs must accept **explicit fields**:
  - `tenant_id` **or** `tenant_slug`
  - If both are provided: **400/409** (invalid)
  - If neither is provided where required: **400**

### 4) Resolution Responsibility

- The API service is the source of truth for slug-to-ID resolution.
- Clients may assist UX, but they must submit explicit identifiers. No inference.

### 5) Type and Schema Enforcement

- Shared types must reflect mutual exclusivity:
  - `tenant_id?: string; tenant_slug?: never`
  - `tenant_slug?: string; tenant_id?: never`
- API validation must enforce the same rule at boundaries.

### 6) UI Guidance

- Labels must state **exactly** which identifier is expected.
- If both are allowed, the UI must make the choice explicit (separate inputs or a selector).

## Implementation Notes (Current Stack)

- Web app SSO surfaces must accept explicit `tenant_id` or `tenant_slug` without inference.
- Password login continues to accept `tenant_id` only unless the API is explicitly expanded.
- SSO list/start routes already enforce mutual exclusivity and are the reference behavior.

## Non-Goals

- Backward compatibility with ambiguous inputs.
- Accepting untyped “tenant” values anywhere inside service boundaries.
