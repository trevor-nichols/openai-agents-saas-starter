.
├── app/                                     # Next.js application directory containing pages, layouts, and API routes.
│   ├── (marketing)/                         # Public marketing routes grouped under a shared layout.
│   │   ├── layout.tsx                       # Marketing shell with header/footer navigation.
│   │   ├── page.tsx                         # Landing page showcasing product positioning.
│   │   ├── features/page.tsx                # Feature deep-dive placeholder.
│   │   └── pricing/page.tsx                 # Pricing tiers placeholder.
│   ├── (auth)/                              # Authentication flows with a centered card layout.
│   │   ├── layout.tsx                       # Gradient background + card wrapper shared by auth pages.
│   │   ├── login/page.tsx                   # Login page rendering the reusable LoginForm component.
│   │   ├── register/page.tsx                # Placeholder registration page.
│   │   ├── email/verify/page.tsx            # Placeholder email verification status view.
│   │   └── password/                        # Password management (forgot/reset) placeholders.
│   │       ├── forgot/page.tsx              # Placeholder request form for password reset emails.
│   │       └── reset/page.tsx               # Placeholder token redemption page.
│   ├── (app)/                               # Authenticated console with dedicated application shell.
│   │   ├── layout.tsx                       # Top navigation + account sidebar, includes SilentRefresh.
│   │   ├── page.tsx                         # Redirects to `/dashboard` by default.
│   │   ├── dashboard/page.tsx               # Placeholder KPI overview for tenants.
│   │   ├── conversations/page.tsx           # Placeholder conversations data table.
│   │   ├── agents/page.tsx                  # Placeholder agent roster.
│   │   ├── tools/page.tsx                   # Placeholder tool catalog.
│   │   ├── billing/                         # Billing-centric views.
│   │   │   ├── page.tsx                     # Billing summary placeholder.
│   │   │   └── plans/page.tsx               # Placeholder for plan upgrade/downgrade workflows.
│   │   ├── account/                         # Account and security settings placeholders.
│   │   │   ├── profile/page.tsx             # Placeholder profile page.
│   │   │   ├── security/page.tsx            # Placeholder security controls page.
│   │   │   ├── sessions/page.tsx            # Placeholder active sessions manager.
│   │   │   └── service-accounts/page.tsx    # Placeholder service account manager.
│   │   ├── settings/tenant/page.tsx         # Placeholder tenant settings hub.
│   │   └── (workspace)/                     # Workspace layouts (e.g., chat).
│   │       ├── layout.tsx                   # Minimal wrapper to keep workspace content full-height.
│   │       ├── chat/actions.ts              # Server Actions powering chat streaming + conversation list.
│   │       └── chat/page.tsx                # Full chat workspace (sidebar + chat interface + billing panel).
│   ├── actions/                             # Application-wide server actions.
│   │   ├── auth/                            # Auth-related server actions (email, password, sessions, signup).
│   │   └── auth.ts                          # Login, logout, and silent refresh actions.
│   ├── api/                                 # App Router route handlers proxying to the FastAPI backend.
│   │   ├── agents/                          # Agent inventory + status route handlers (with tests).
│   │   ├── auth/                            # Auth API proxies (email, logout, password, register, session, etc.).
│   │   ├── billing/                         # Billing proxy routes (plans, stream, tenant subscription/usage).
│   │   ├── chat/                            # Chat proxy routes (non-streaming + streaming SSE).
│   │   ├── conversations/                   # Conversation list/detail proxy routes.
│   │   ├── health/                          # Liveness + readiness probes.
│   │   └── tools/                           # Tool catalog proxy route.
│   ├── globals.css                          # Global Tailwind layer and CSS variables.
│   ├── layout.tsx                           # Root layout (fonts, global providers).
│   └── providers.tsx                        # React Query provider with devtools.
├── components/                              # Reusable React components (feature-specific placeholders remain here for now).
│   ├── agent/                               # Chat workspace components (to be promoted into feature modules).
│   │   ├── ChatInterface.tsx                # Chat transcript + composer.
│   │   └── ConversationSidebar.tsx          # Conversation list with Logout button.
│   ├── auth/                                # Authentication widgets.
│   │   ├── LoginForm.tsx                    # Form surfaces loginAction.
│   │   ├── LogoutButton.tsx                 # Button invoking logoutAction.
│   │   └── SilentRefresh.tsx                # Client hook wrapper to silently refresh sessions.
│   └── billing/                             # Billing panel components.
│       ├── BillingEventsPanel.tsx           # Renders SSE-driven billing updates.
│       └── __tests__/                       # Unit tests for billing components.
│           └── BillingEventsPanel.test.tsx  # BillingEventsPanel test suite.
├── eslint.config.mjs                        # ESLint configuration file.
├── hooks/                                   # Legacy / experimental hooks (scheduled for cleanup).
│   ├── useBillingStream.ts                  # Legacy hook (replaced by TanStack Query version).
│   └── useSilentRefresh.ts                  # Legacy hook (replaced by SilentRefresh component).
├── lib/                                     # Core logic, utilities, and typed API interactions.
│   ├── api/                                 # Client-side fetch helpers (HeyAPI SDK wrappers).
│   │   ├── __tests__/                       # Tests for API helpers.
│   │   ├── agents.ts                        # Fetch agent list and status.
│   │   ├── billing.ts                       # Connect to billing SSE stream.
│   │   ├── billingPlans.ts                  # Fetch billing plans.
│   │   ├── chat.ts                          # Send chat messages via backend REST endpoints.
│   │   ├── client/                          # Generated HeyAPI client core.
│   │   ├── config.ts                        # Shared configuration for API client.
│   │   ├── conversations.ts                 # Conversation fetch helpers.
│   │   ├── session.ts                       # Session fetch/refresh helpers.
│   │   └── tools.ts                         # Fetch tool metadata.
│   ├── auth/                                # Authentication utilities.
│   │   ├── clientMeta.ts                    # Read session metadata from cookies.
│   │   ├── cookies.ts                       # Cookie helpers for auth tokens.
│   │   └── session.ts                       # Exchange credentials, refresh, destroy sessions.
│   ├── chat/                                # Chat-specific hooks and types.
│   │   ├── __tests__/                       # Unit + integration tests for chat controller.
│   │   ├── types.ts                         # Shared chat types (messages, stream chunks).
│   │   └── useChatController.ts             # Core hook orchestrating chat state, streaming, persistence.
│   ├── config.ts                            # Global app configuration constants.
│   ├── queries/                             # TanStack Query hooks (agents, billing, chat, conversations, session, tools).
│   ├── server/                              # Server-side helpers and services used by route handlers/server actions.
│   │   ├── apiClient.ts                     # Authenticated server-side API client factory.
│   │   ├── services/                        # Domain-specific service layer for server usage.
│   │   └── streaming/                       # Streaming helpers (chat SSE).
│   ├── types/                               # Shared cross-feature TypeScript types.
│   └── utils.ts                             # Generic utility helpers (classnames, etc.).
├── middleware.ts                            # Middleware gating auth-required routes vs public marketing/auth routes.
├── next.config.ts                           # Next.js configuration.
├── openapi-ts.config.ts                     # HeyAPI client generation configuration.
├── playwright.config.ts                     # Playwright E2E test configuration.
├── pnpm-lock.yaml                           # PNPM dependency lockfile.
├── postcss.config.mjs                       # PostCSS configuration (Tailwind).
├── public/                                  # Static assets served directly.
│   ├── file.svg
│   ├── globe.svg
│   ├── next.svg
│   ├── vercel.svg
│   └── window.svg
├── tailwind.config.ts                       # Tailwind design tokens & plugins.
├── tests/                                   # End-to-end (Playwright) tests.
│   └── auth-smoke.spec.ts                   # Updated smoke test covering login → dashboard → chat → logout.
├── types/                                   # Shared domain types (agents, billing, conversations, session, tools).
├── vitest.config.ts                         # Vitest configuration.
└── vitest.setup.ts                          # Vitest setup importing DOM matchers.