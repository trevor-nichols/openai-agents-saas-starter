<!-- SECTION: Title -->
# Frontend UI Foundation Milestone

<!-- SECTION: Objective -->
## Objective
Deliver a production-quality page architecture and component plan that maps every surfaced backend capability to a coherent Next.js App Router experience. This milestone establishes the navigation, route groups, and Shadcn-driven component inventory so the design/implementation teams can focus on visual polish without reworking data or auth flows.

<!-- SECTION: Scope -->
## In Scope
- Define the full page IA (marketing, auth, application) aligned with existing API surfaces.
- Specify route group structure and layout composition for the App Router.
- Identify Shadcn UI components (existing vs. to add) per page.
- Capture UX narratives for core flows (onboarding, chat, billing, account/security).
- Document open questions and dependencies for design handoff.

<!-- SECTION: Out of Scope -->
## Out of Scope
- Visual design, theming, and spacing decisions (handled by the UI team).
- Net-new backend endpoints or schema changes.
- Storybook/visual regression setup (track separately if needed).
- Copywriting for marketing content (placeholder text acceptable for now).

<!-- SECTION: Deliverables -->
## Deliverables
- Page architecture table covering routes, purpose, data sources, auth requirements.
- Proposed route-group/layout diagram referencing `app/` structure.
- Component inventory mapping (Shadcn primitives, custom wrappers).
- Workstream checklist with owners, status, and dependencies.
- Risks + mitigation notes for sequencing UI work.

<!-- SECTION: Architecture -->
## Proposed Information Architecture

| Route | Area | Description | Data Sources | Auth |
| ----- | ---- | ----------- | ------------ | ---- |
| `/` | Marketing | SaaS landing page (hero, CTA, feature highlights) | Static content + optional metrics | Public |
| `/pricing` | Marketing | Subscription tiers, usage limits, FAQ | `GET /api/v1/billing/plans` (public view) | Public |
| `/features` (optional) | Marketing | Deep dive into agent/billing capabilities, tooling | Static/MDX | Public |
| `/docs` or `/guides` (optional) | Marketing | Quick-start docs; links to external docs | Static/MDX | Public |
| `/(auth)/login` | Auth | Username/password login | `loginAction` | Public |
| `/(auth)/register` | Auth | Tenant signup form | `registerAction` / `/auth/register` | Public |
| `/(auth)/password/forgot` | Auth | Request password reset | `/auth/password/forgot` | Public |
| `/(auth)/password/reset` | Auth | Redeem reset token | `/auth/password/confirm` | Public |
| `/(auth)/email/verify` | Auth | Verification status + resend | `/auth/email/send` | Public |
| `/(app)/dashboard` | Application | High-level snapshot (conversation stats, quick actions) | `/api/agents`, `/api/conversations`, `/api/billing/stream` (summary) | Auth |
| `/(app)/chat` | Application | Core chat workspace (existing) with agent selector/tools | `/api/chat`, `/api/chat/stream`, `/api/conversations` | Auth |
| `/(app)/conversations` | Application | Conversation list + detail (audit view, exports) | `/api/conversations/*` | Auth |
| `/(app)/agents` | Application | Agent inventory + status telemetry | `/api/agents`, `/api/agents/{name}/status` | Auth |
| `/(app)/tools` | Application | Tool catalog with categories/capabilities | `/api/tools` | Auth |
| `/(app)/billing` | Application | Subscription summary, invoices, usage | `/api/billing/tenants/*`, `/api/billing/stream` | Auth (tenant-level) |
| `/(app)/billing/plans` | Application | Self-serve upgrade/downgrade flow | `/api/billing/plans`, `/api/billing/tenants/*` | Auth |
| `/(app)/account/profile` | Account | Profile info, email verification state | `/api/auth/session`, `/api/auth/me` | Auth |
| `/(app)/account/security` | Account | Password change, MFA placeholder, recent auth events | `/api/auth/password/change`, `/api/auth/sessions` | Auth |
| `/(app)/account/sessions` | Account | Device/session management (revoke flows) | `/api/auth/sessions/*`, `/api/auth/logout/all` | Auth |
| `/(app)/account/service-accounts` | Account/Admin | Issue/revoke service account tokens | `/api/auth/service-accounts/issue` | Auth (admin scope) |
| `/(app)/settings/tenant` (optional) | Admin | Tenant metadata, plan, webhook settings | `/api/billing/tenants/*` | Auth (owner scope) |

> Notes  
> - Routes marked optional should be validated with product; keep placeholders or redirect until content is ready.  
> - Consolidate `/features` & `/docs` into landing if scope shrinks.

<!-- SECTION: Layout Strategy -->
## Route Group & Layout Strategy
- `app/(marketing)/` for public pages sharing a light-weight layout (header/nav/footer).
- Existing `app/(auth)/` remains for auth forms; add nested layouts for multi-step flows.
- Introduce `app/(app)/` as the authenticated shell (sidebar/header). Split child layouts:
  - `app/(app)/layout.tsx` – wraps all authenticated pages (top nav, command palette, toasts).  
  - `app/(app)/(workspace)/chat/page.tsx` – dedicated chat workspace (reuse current implementation).  
  - `app/(app)/(account)/` – settings-area layout with secondary nav.
- Leverage Next.js `loading.tsx` and `error.tsx` per section for skeletons/error boundaries.

<!-- SECTION: Component Inventory -->
## Component Inventory (Shadcn + Custom)

| Component | Usage | Status |
| --------- | ----- | ------ |
| `navigation-menu`, `sheet`, `command` | Marketing nav, mobile menus, quick actions | To add |
| `hero`, `callout`, `badge`, `button` variants | Landing & pricing CTAs | To add |
| `card`, `tabs`, `accordion` | Pricing plans, FAQ, dashboard widgets | To add/extend |
| `data-table` (with tanstack) | Conversations list, sessions, billing usage | To install |
| `alert`, `toast`, `tooltip` | Global feedback, inline notices | Toast already via controller? evaluate |
| `form`, `input`, `select`, `textarea`, `password` | Auth & account forms | Exists partially; normalize |
| `dialog`, `popover`, `dropdown-menu` | Agent selector, delete confirmations | To add |
| `badge`, `status-dot` (custom) | Agent/billing status indicators | Custom wrapper |
| `stat-widget` (custom) | Dashboard KPI summary | Custom |
| `chart` (community) | Usage trends (optional; coordinate with design) | Evaluate |

<!-- SECTION: Component Architecture -->
## Component Architecture Pattern

- **Feature-centric directories** live under `features/<domain>/` (e.g., `features/chat`, `features/billing`, `features/account`). Each exports a single orchestrator consumed by the page.
- **Directory shape per feature:**

  ```
  features/chat/
    index.ts              // public exports for the feature
    ChatWorkspace.tsx     // orchestrator/container (client component)
    components/
      MessageList.tsx
      MessageInput.tsx
      ConversationHeader.tsx
      index.ts
    constants.ts          // copy, layout config, status labels
    types.ts              // view-specific types (domain types remain in /types)
    hooks/
      useMessageFocus.ts  // purely view-level composition
      index.ts
    utils/
      formatMessage.ts    // pure helpers scoped to this feature
  ```

- **Pages stay lean:** `app/.../page.tsx` imports the feature orchestrator and handles only layout/metadata. Shared chrome for a route group belongs in `_components/` next to the layout, while the feature content stays within `features/**`.
- **Data layer remains centralized:** Continue using `lib/api`, `lib/queries`, `lib/chat`, and `/types` for network/data contracts. Feature hooks only compose those primitives; anything broadly useful graduates to `components/ui/` or `components/shared/`.
- **Ownership split:** Engineering owns the shared hooks/services in `lib/**`; the design/UI team iterates inside `features/<domain>/components` using those hooks. Any new cross-feature logic graduates back into `lib/**` so other surfaces stay consistent.
- **Testing:** Colocate unit/interaction tests with the orchestrator (`ChatWorkspace.test.tsx`). Promote reusable test helpers to existing shared testing utilities when multiple features need them.

<!-- SECTION: Workstreams -->
## Workstreams & Tasks

- **IA & Navigation**
  - [ ] Confirm marketing page set (landing, pricing, docs/FAQ) with product.
  - [ ] Design global header/footer IA (desktop + mobile).
  - [ ] Define authenticated shell nav structure (primary tabs, quick actions).
- **Auth UX Enhancements**
  - [ ] Add register, forgot/reset, email verification pages using existing actions.
  - [ ] Implement form validation, error surfacing, success states.
  - [ ] Ensure route guards redirect correctly (middleware + per-page metadata).
- **Chat Workspace Evolution**
  - [ ] Promote current `app/(agent)/page.tsx` into `/(app)/chat` with shell layout.
  - [ ] Add agent switcher, tool metadata sidebar, transcript export placeholder.
  - [ ] Plan skeleton states and error toasts for streaming failures.
- **Conversations & Audit Trails**
  - [ ] Build `/(app)/conversations` list view (filter/sort, search).
  - [ ] Add detail drawer/page with metadata, delete/export actions.
  - [ ] Wire to existing conversation endpoints + `useChatController`.
- **Agent & Tool Catalog**
  - [ ] Create agent roster page with status badges and model metadata.
  - [ ] Display tool categories, usage instructions, and availability per agent.
- **Billing & Subscription Hub**
  - [ ] Surface subscription summary, next invoice, usage charts.
  - [ ] Provide upgrade/downgrade controls (Shadcn dialog + form).
  - [ ] List recent billing events (reuse `BillingEventsPanel`, enhance styling).
- **Account & Security**
  - [ ] Profile page (user info, tenant data, email verification state).
  - [ ] Security page (password change form, MFA placeholder, last login).
  - [ ] Sessions table with revoke controls, service account token issuance flow.
- **Shared Systems**
  - [ ] Toast/notification framework (centralized provider).
  - [ ] Loading skeleton components (marketing + app).
  - [ ] Error boundary surfaces per route group.

<!-- SECTION: Risks -->
## Risks & Mitigations
- **Scope Creep:** Marketing content may expand; keep optional routes feature-flagged until content lands.  
- **Component Drift:** Without a centralized palette, teams might add ad-hoc components. Track Shadcn additions in a dedicated registry doc.  
- **Auth Edge Cases:** Additional flows (MFA, invite-only signup) could change IA—capture as future enhancements, keep layouts flexible.  
- **Billing Complexity:** Self-serve billing requires careful UX; prototype flows before binding to Stripe endpoints.

<!-- SECTION: Exit Criteria -->
## Exit Criteria
- Page IA table validated by product/design.  
- Route group skeletons scaffolded (layouts, placeholder pages, nav).  
- Shadcn component install list approved + added to backlog.  
- Workstream checklist populated with owners/ETA and tracked via Linear/Jira.  
- `pnpm lint`, `pnpm type-check`, `pnpm vitest run` pass after scaffolding updates.


