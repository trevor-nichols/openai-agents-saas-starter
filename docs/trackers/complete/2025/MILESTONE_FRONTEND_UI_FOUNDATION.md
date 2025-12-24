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

### Confirmed Navigation & Chrome Decisions (2025-11-11)
- **Marketing set** – `/`, `/pricing`, `/features`, and `/docs` all render live backend data (plans, metrics, testimonials). Each page follows the hero → proof → CTA → FAQ pattern so content can expand without new layouts. Optional cards pull from `/api/health` or other public endpoints to showcase real-time stats.
- **Desktop header** – Left-aligned logo plus primary links (`Features`, `Pricing`, `Docs`, `Login`); right rail includes the “Get Started” CTA button, the upcoming theme toggle, and InlineTag-based badges for announcements.
- **Mobile nav** – `navigation-menu` on desktop degrades to a `sheet`-driven drawer under 1024px with mirrored primary links, CTA, condensed footer links, and a `command` palette trigger for quick navigation.
- **Footer IA** – Three-column grid (Product, Company, Legal) composed from `SectionHeader` + `KeyValueList`, plus a live metrics card. Social/CTA rows reuse foundation components to avoid bespoke styling.
- **Authenticated sidebar** – 280px glass panel with sections: Dashboard, Chat, Conversations, Agents, Tools, Billing, Account (nesting Profile, Security, Sessions, Service Accounts). Collapsed mode becomes an icon rail with tooltip labels; mobile variants reuse the marketing sheet for parity.
- **Top bar** – Breadcrumb + InlineTag environment indicator on the left, center-aligned command palette/search, and right-aligned notification bell (Sonner-backed), theme toggle, and user dropdown (`dropdown-menu`). Quick actions (e.g., “New Conversation”) live next to the palette trigger.
- **Feedback systems** – `components/ui/sonner` becomes the global toast provider via `providers.tsx`, giving typed helpers for success/error/info. Route-group `error.tsx`/`loading.tsx` components reuse `components/ui/states/*` with tailored copy per section.
- **Theme toggle** – Adopt the Shadcn theme switcher once installed; hook into the existing CSS variables so marketing/auth/app shells inherit light/dark tokens consistently.

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

<!-- SECTION: Design Decisions -->
## Design System Decisions (2025-11-10)

- **Visual Language Tokens** – Adopt a graphite-to-porcelain palette (`#0F1115` primary, `#181B21` shell, elevated glass `rgba(255,255,255,0.06)`, stroke `rgba(255,255,255,0.08)`, accent `#6EB5FF`). Typography stack `SF Pro Display, SF Pro Text, Inter, -apple-system`. Set radii `--radius-xs:4px`, `--radius-sm:8px`, `--radius-lg:16px`, `--radius-pill:999px`. Motion tokens `--ease-apple: cubic-bezier(0.32,0.72,0,1)`, with durations `150ms` (hover), `220ms` (content), `320ms` (modal/sheet). Define CSS variables in `app/globals.css` and mirror them inside `tailwind.config.ts` theme tokens.
- **Layout Behavior** – `app/(marketing)` uses a translucent top nav over full-width hero; `app/(auth)` centers a frosted card (max 480px) with glow; `app/(app)` keeps a 280px frosted sidebar that collapses to an icon rail ≤1024px plus a 64px top bar for breadcrumbs/actions. Workspace routes (chat) stretch edge-to-edge with resizable panels; admin/settings/billing routes constrain content width to 1200px for readability.
- **Component Coverage** – Create a foundation kit under `components/ui/foundation/` (`GlassPanel`, `StatCard`, `SectionHeader`, `KeyValueList`, `InlineTag`) composed from existing Shadcn primitives. If needed primitives (e.g., `navigation-menu`) are missing, add them via the shadcn CLI and log the addition in `docs/frontend/ui/shadcn.md`.
- **State Patterns** – Centralize skeletons/empty/error components under `components/ui/states/`. Styling: soft gradient background (`linear-gradient(135deg, rgba(255,255,255,0.08), rgba(110,181,255,0.12))`), thin border using the stroke token, and rounded corners derived from the new radii. Every feature route replaces ad-hoc placeholders with these shared components.
- **Motion & Micro-Interactions** – Apply `--ease-apple` globally. Buttons gain subtle color fade + 2px press translation; the sidebar collapses over 240ms; modals/sheets fade & slide over 320ms with blur transitions. Hover states lighten the surface by ~6% and add a restrained shadow (`0 8px 24px rgba(0,0,0,0.25)`). Reserve parallax for marketing hero sections only.
- **Content Density Guardrails** – Use an 8/12/20/32 spacing scale. Dashboards keep generous outer padding (32px) with denser card internals (16px). Tables default to 48px rows, with a compact 40px variant for billing/sessions. Chat transcripts maintain roomy bubbles, while metadata drawers use condensed typography with hairline separators (`rgba(255,255,255,0.08)`), balancing the Johnny Ive aesthetic with enterprise readability.

<!-- SECTION: Progress -->
## Progress Update (2025-11-11)

- **Tokens & Foundation** – Global palette, motion, and radii tokens now live in `app/globals.css` + `tailwind.config.ts`, and the `components/ui/foundation` + `components/ui/states` kits power every refreshed route.
- **Dashboard & Chat** – `features/dashboard` and `features/chat` consume the new kit: KPI/stat cards, glass chat workspace, InlineTag agent telemetry, and shared loading/error/empty states are live under the authenticated shell.
- **Billing & Conversations** – `/billing` and `/conversations` now ship glass panels backed by live data (billing stream, TanStack conversations) with InlineTags, ScrollArea tables, and reusable Empty/Skeleton states, aligning all authenticated surfaces to the same Johnny Ive aesthetic.
- **Marketing Shell** – Desktop + mobile navigation, command palette, theme toggle, and the live `/api/health` footer card now power every marketing route, giving `/`, `/pricing`, `/features`, and `/docs` a consistent chrome for design to build on.
- **Docs hub** – `/docs` now bundles navigation-menu anchors, glass doc cards, KeyValueList stats, quick resource links, and curated playbooks so stakeholders can self-serve the latest guidance without chasing Notion decks.
- **Shared systems** – `components/ui/data-table` now wraps `@tanstack/react-table` with skeleton/error states and optional pagination while `useToast` + the `Toaster` provider centralizes feedback, so future account/billing tables can reuse the same patterns without importing Sonner directly.
- **Plan management** – `/billing/plans` now renders the plan catalog, opens a Shadcn dialog with billing metadata (email/seats/auto-renew), and invokes the start/update mutations tied to `useToast` so the billing summary stays in sync across the authenticated shell.

<!-- SECTION: Workstreams -->
## Workstreams & Tasks

- **IA & Navigation**
  - [x] Confirm marketing page set (landing, pricing, docs/FAQ) with product. *Decision: `/`, `/pricing`, `/features`, `/docs` all ship with live data sources and shared content hierarchy.*
  - [x] Design global header/footer IA (desktop + mobile). *Decision: desktop nav with CTA/theme toggle, mobile sheet + command palette, three-column footer with live metric card.*
  - [x] Define authenticated shell nav structure (primary tabs, quick actions). *Decision: 280px glass sidebar (Dashboard → Account subsections), top bar with breadcrumbs, command palette, toasts, theme toggle, and avatar menu.*
- **Auth UX Enhancements**
  - [x] Add register, forgot/reset, email verification pages using existing actions. *Status (2025-11-11): Shared `AuthCard` + `useAuthForm` cover all flows, wired to server actions with toast feedback.*
  - [x] Implement form validation, error surfacing, success states. *Status (2025-11-11): Zod + Shadcn forms now power login/register/forgot/reset/verify routes with shared toasts.*
  - [x] Ensure route guards redirect correctly (middleware + per-page metadata). *Status (2025-11-11): Middleware now redirects authenticated users away from auth routes and captures full redirect targets for guests; auth pages export metadata for better context.*
- **Chat Workspace Evolution**
  - [x] Promote current `app/(agent)/page.tsx` into `/(app)/chat` with shell layout.
  - [x] Add agent switcher, tool metadata sidebar, transcript export placeholder.
  - [x] Plan skeleton states and error toasts for streaming failures.
- **Conversations & Audit Trails**
  - [x] Build `/(app)/conversations` list view (filter/sort, search).
  - [x] Add detail drawer/page with metadata, delete/export actions. *Status (2025-11-11): Drawer now prefetches detail queries, supports JSON export placeholders, ID/message copy, and destructive delete wired to TanStack cache updates.*
  - [x] Wire to existing conversation endpoints + `useChatController`.
- **Agent & Tool Catalog**
  - [x] Create agent roster page with status badges and model metadata. *Status (2025-11-11): `AgentsOverview` now renders cards with model info, heartbeat timestamps, and status badges sourced from `useAgents()`. Hover states prefetch detail queries for future drawers.*
  - [x] Display tool categories, usage instructions, and availability per agent. *Status (2025-11-11): Cards show tool badges via `useTools()`, with JSON export placeholder + copy actions documented in data access notes.*
- **Billing & Subscription Hub**
  - [x] Surface subscription summary, next invoice, usage charts.
  - [x] Provide upgrade/downgrade controls (Shadcn dialog + form). *Status (2025-11-11): `/billing/plans` now presents the plan catalog, opens a `Dialog` with Shadcn forms, and drives `useStartSubscriptionMutation`/`useToast` for confirmations plus TanStack cache updates.*
  - [x] List recent billing events (reuse `BillingEventsPanel`, enhance styling).
- **Account & Security**
  - [x] Profile page (user info, tenant data, email verification state). *Status (2025-11-12): `features/account/ProfilePanel` now consumes `useAccountProfileQuery`, renders GlassPanel cards with `Avatar`, `InlineTag`, and `Alert` components, and wires resend verification via `useResendVerificationMutation`.*
  - [x] Security page (password change form, MFA placeholder, last login). *Status (2025-11-12): `features/account/SecurityPanel` ships a Shadcn `Form` + `Input` flow backed by `useChangePasswordMutation`, surfaces last-login metadata, and documents MFA via tooltip/CTA placeholders.*
  - [x] Sessions table with revoke controls, service account token issuance flow. *Status (2025-11-12): `features/account/SessionsPanel` + `ServiceAccountsPanel` reuse the shared `DataTable` kit for session management and bind issuance to `/api/auth/service-accounts/issue`, leaving only design polish for badges/modals.*
- **Marketing & Docs**
  - [x] Ship marketing `/docs` route (and `/status` stub). *Status (2025-11-12): `/docs` now renders hero nav anchors, doc stats via `KeyValueList`, resource + playbook panels, and FAQ accordion while `/status` consumes live TanStack hooks with InlineTag/Table fallbacks.*
- **Shared Systems**
  - [x] Toast/notification framework (centralized provider). *Status (2025-11-11): `app/providers.tsx` already mounts the `Toaster`, all features now import `useToast`, and we documented the expectation in `docs/frontend/data-access.md`.*
  - [x] Loading skeleton components (marketing + app).
  - [x] Error boundary surfaces per route group. *Status (2025-11-13): `app/(marketing)/error.tsx`, `app/(auth)/error.tsx`, and `app/(app)/error.tsx` now wrap `ErrorState` with contextual copy, reset buttons, and status/navigation fallbacks, satisfying the branded recovery requirement.*
  - [x] Data table kit (TanStack) for audits/sessions/billing. *Status (2025-11-11): `components/ui/data-table` now exposes `DataTable`/`DataTablePagination`; conversations hub already consumes it with row actions, pagination toggles, and shared states.*

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
