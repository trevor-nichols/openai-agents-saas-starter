<!-- SECTION: Title -->
# Frontend UI Foundation Milestone — Refresh

_Last updated: November 17, 2025_

## Objective
Re-align the frontend tracker with the current state of the Next.js 15 surface, capturing what already shipped, what remains in flight, and the concrete steps required to graduate the UI foundation into polish mode.

## Current Health Snapshot
| Area | Status | Notes |
| --- | --- | --- |
| Routing & shell | ✅ Complete | App Router groups (`(marketing)`, `(auth)`, `(app)`) with middleware + SilentRefresh. |
| Auth flows | ✅ Complete | Login/register/reset + email verification powered by server actions; Playwright smoke test exists. |
| Chat workspace | ✅ Complete | Streaming chat, conversation drawers, billing/tool sidecars all wired. |
| Dashboard & billing | ⚠️ Needs polish | KPI grid + plan management functional; add richer analytics + guardrails around plan mutations. |
| Conversations archive | ✅ Complete | Searchable table w/ prefetch + drawer export hooks shipped. |
| Agents & tools | ✅ Complete | Agents page now hosts the consolidated workspace (catalog + chat + tools + archive). |
| Account & security | ✅ Complete | Profile/security/sessions/service-accounts fully wired with TanStack Query. |
| Tenant settings | ✅ Complete | Billing contacts, webhook, metadata, and flag controls shipped. |
| Marketing surfaces | ✅ Complete | Landing, pricing, features, docs, and `/status` now share the finalized copy matrices, analytics wiring, and status-alert UX. |
| QA coverage | ✅ Complete | Playwright suite now exercises billing plan changes, usage/SSE, service accounts, tenant settings, transcript export, and archive management. |

## Completed Work
- **Architecture**: Route groups, middleware, and layout structure mirror the IA in the archived tracker.
- **Data layer**: All client data flows adhere to the documented layering (server services → `/api` routes → `lib/api` → `lib/queries`).
- **Core features**: Chat workspace, dashboard widgets, billing stream hook, conversations archive, account/security suite, and status page are production-ready.
- **Feature directories**: Chat, account, billing, and dashboard modules now follow the orchestrator/components/hooks pattern (FE-001 closed).

## Outstanding Gaps & Risks
All tracked gaps for this milestone are closed. Keep monitoring UX polish in dashboard/billing, but no blockers remain for milestone completion.

## Next Actions
| # | Task | Owner | Status | Target |
| - | ---- | ----- | ------ | ------ |
| 1 | Lock marketing copy + CTA matrix across landing, features, pricing, docs (constants + FAQs). | Platform Foundations | Completed | Nov 17 |
| 2 | Instrument every marketing CTA/link with `useMarketingAnalytics` (hero buttons, plan cards, nav pills, resource links). | Platform Foundations | Completed | Nov 17 |
| 3 | Polish the status alert funnel (shared `StatusAlertsCard`, `/status` verification banners, helper text) and document the API contract. | Platform Foundations | Completed | Nov 17 |
| 4 | Document marketing voice + analytics taxonomy in `docs/marketing/README.md` so future changes stay aligned. | Platform Foundations | Completed | Nov 17 |
| 5 | Expand Playwright suite to cover billing plan changes, service-account issue/revoke, and chat transcript export once UI polish ships. | Platform Foundations | Completed | Nov 19 |
| 6 | Maintain the weekly tracker review ritual (15 mins in Frontend Sync) to keep status current. | Platform Foundations | Scheduled | Ongoing |

## Risk Log
- **Workspace onboarding**: The consolidated agents surface adds cognitive load; we still need onboarding copy/video to guide customers. _Mitigation_: Add inline coach marks + docs once analytics prove adoption.
- **Admin blind spots**: Newly shipped tenant settings lack inline guidance and guardrails, so CS/Ops could misconfigure plan metadata or webhooks. _Mitigation_: Layer contextual copy, validation states, and ship the companion runbook.
- **Regression exposure**: Minimal E2E coverage increases risk as more enterprise flows ship. _Mitigation_: Task #5 (Playwright expansion) remains the next deliverable; ensure specs land before Dec 4.

## Changelog
- **2025-11-17**: Marketing copy matrices, analytics instrumentation, status-alert UX/docs, and the marketing voice guide completed; milestone now blocks solely on the Playwright expansion (Task #5).
- **2025-11-19**: Playwright milestone (Flows 3–8) landed, closing Task #5 and bringing QA coverage to parity with the UI foundation scope.
- **2025-11-13**: Agents workspace now bundles catalog, chat, tools panel, and conversation archive; removed standalone `/tools` + `/conversations` routes.
- **2025-11-13**: Tracker reset to reflect current implementation; previous tracker archived under `docs/trackers/complete/MILESTONE_FRONTEND_UI_FOUNDATION_2025-11-13.md`.
- **2025-11-13**: Landing, pricing, features, and docs routes now use feature modules with TanStack data + CTA instrumentation (status alert lead capture live on `/`).
- **2025-11-13**: Tenant settings surface ships with billing contacts, webhook, plan metadata, and feature flag forms backed by the new FastAPI `/tenants/settings` endpoints.


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
- **Authenticated sidebar** – 280px glass panel with sections: Dashboard, Chat, Agents (now the command center), Billing, Account (nesting Profile, Security, Sessions, Service Accounts). Collapsed mode becomes an icon rail with tooltip labels; mobile variants reuse the marketing sheet for parity.
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
<!-- SECTION: Design Decisions -->
## Design System Decisions (2025-11-10)

- **Visual Language Tokens** – Adopt a graphite-to-porcelain palette (`#0F1115` primary, `#181B21` shell, elevated glass `rgba(255,255,255,0.06)`, stroke `rgba(255,255,255,0.08)`, accent `#6EB5FF`). Typography stack `SF Pro Display, SF Pro Text, Inter, -apple-system`. Set radii `--radius-xs:4px`, `--radius-sm:8px`, `--radius-lg:16px`, `--radius-pill:999px`. Motion tokens `--ease-apple: cubic-bezier(0.32,0.72,0,1)`, with durations `150ms` (hover), `220ms` (content), `320ms` (modal/sheet). Define CSS variables in `app/globals.css` and mirror them inside `tailwind.config.ts` theme tokens.
- **Layout Behavior** – `app/(marketing)` uses a translucent top nav over full-width hero; `app/(auth)` centers a frosted card (max 480px) with glow; `app/(app)` keeps a 280px frosted sidebar that collapses to an icon rail ≤1024px plus a 64px top bar for breadcrumbs/actions. Workspace routes (chat) stretch edge-to-edge with resizable panels; admin/settings/billing routes constrain content width to 1200px for readability.
- **Component Coverage** – Create a foundation kit under `components/ui/foundation/` (`GlassPanel`, `StatCard`, `SectionHeader`, `KeyValueList`, `InlineTag`) composed from existing Shadcn primitives. If needed primitives (e.g., `navigation-menu`) are missing, add them via the shadcn CLI and log the addition in `docs/frontend/ui/shadcn.md`.
- **State Patterns** – Centralize skeletons/empty/error components under `components/ui/states/`. Styling: soft gradient background (`linear-gradient(135deg, rgba(255,255,255,0.08), rgba(110,181,255,0.12))`), thin border using the stroke token, and rounded corners derived from the new radii. Every feature route replaces ad-hoc placeholders with these shared components.
- **Motion & Micro-Interactions** – Apply `--ease-apple` globally. Buttons gain subtle color fade + 2px press translation; the sidebar collapses over 240ms; modals/sheets fade & slide over 320ms with blur transitions. Hover states lighten the surface by ~6% and add a restrained shadow (`0 8px 24px rgba(0,0,0,0.25)`). Reserve parallax for marketing hero sections only.
- **Content Density Guardrails** – Use an 8/12/20/32 spacing scale. Dashboards keep generous outer padding (32px) with denser card internals (16px). Tables default to 48px rows, with a compact 40px variant for billing/sessions. Chat transcripts maintain roomy bubbles, while metadata drawers use condensed typography with hairline separators (`rgba(255,255,255,0.08)`), balancing the Johnny Ive aesthetic with enterprise readability.
