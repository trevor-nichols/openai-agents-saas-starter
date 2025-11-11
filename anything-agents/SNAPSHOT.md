.
├── app/                                 # Next.js App Router directory containing all routes and UI.
│   ├── (app)/                           # Route group for authenticated application pages.
│   │   ├── (workspace)/                 # Route group for multi-column workspace layouts like the chat UI.
│   │   │   ├── chat/                    # Contains pages and server actions for the chat feature.
│   │   │   │   ├── actions.ts           # Server Actions for streaming chat and listing conversations.
│   │   │   │   └── page.tsx             # Renders the main chat workspace page.
│   │   │   └── layout.tsx               # Provides a consistent layout wrapper for workspace pages.
│   │   ├── account/                     # Contains pages for user account management.
│   │   │   ├── profile/                 # Contains the user profile page.
│   │   │   │   └── page.tsx             # Renders the user's profile settings page.
│   │   │   ├── security/                # Contains the user security settings page.
│   │   │   │   └── page.tsx             # Renders the user's security settings page.
│   │   │   ├── service-accounts/        # Contains the service account management page.
│   │   │   │   └── page.tsx             # Renders the service account management page.
│   │   │   └── sessions/                # Contains the user session management page.
│   │   │       └── page.tsx             # Renders the user's active sessions page.
│   │   ├── agents/                      # Contains the agent management pages.
│   │   │   └── page.tsx                 # Renders the agent overview and catalog page.
│   │   ├── billing/                     # Contains pages related to billing and subscriptions.
│   │   │   ├── page.tsx                 # Renders the main billing overview page.
│   │   │   └── plans/                   # Contains the subscription plan management page.
│   │   │       └── page.tsx             # Renders the subscription plan management page.
│   │   ├── conversations/               # Contains pages for viewing conversation history.
│   │   │   └── page.tsx                 # Renders the main conversations hub/archive page.
│   │   ├── dashboard/                   # Contains the main user dashboard page.
│   │   │   └── page.tsx                 # Renders the main dashboard for authenticated users.
│   │   ├── layout.tsx                   # Main layout for authenticated users with sidebar and header.
│   │   ├── page.tsx                     # Root page for the authenticated app, redirects to the dashboard.
│   │   ├── settings/                    # Contains application and tenant settings pages.
│   │   │   └── tenant/                  # Contains tenant-specific settings pages.
│   │   │       └── page.tsx             # Renders the tenant settings page.
│   │   └── tools/                       # Contains pages related to agent tools.
│   │       └── page.tsx                 # Renders the tool catalog page.
│   ├── (auth)/                          # Route group for authentication-related pages.
│   │   ├── _components/                 # Private components for the auth layout.
│   │   │   └── AuthCard.tsx             # Reusable UI card component for authentication forms.
│   │   ├── email/                       # Contains email-related action pages.
│   │   │   └── verify/                  # Contains the email verification flow pages.
│   │   │       ├── VerifyEmailClient.tsx # Client component handling the logic for email verification.
│   │   │       └── page.tsx             # Renders the email verification page.
│   │   ├── error.tsx                    # Custom error boundary for authentication routes.
│   │   ├── layout.tsx                   # Provides a centered, styled layout for authentication forms.
│   │   ├── loading.tsx                  # Loading skeleton UI for authentication routes.
│   │   ├── login/                       # Contains the user login page.
│   │   │   └── page.tsx                 # Renders the user login page.
│   │   ├── password/                    # Contains pages for password management flows.
│   │   │   ├── forgot/                  # Contains the forgot password page.
│   │   │   │   └── page.tsx             # Renders the "forgot password" form.
│   │   │   └── reset/                   # Contains the password reset page.
│   │   │       └── page.tsx             # Renders the password reset form using a token.
│   │   └── register/                    # Contains the user registration page.
│   │       └── page.tsx                 # Renders the user and tenant registration page.
│   ├── (marketing)/                     # Route group for public-facing marketing pages.
│   │   ├── _components/                 # Private components for the marketing layout.
│   │   │   ├── marketing-footer.tsx     # Footer component for marketing pages, including API status.
│   │   │   ├── marketing-header.tsx     # Header component for marketing pages with navigation.
│   │   │   └── nav-links.ts             # Defines link constants for marketing navigation.
│   │   ├── features/                    # Contains the marketing features page.
│   │   │   └── page.tsx                 # Renders a page detailing product features.
│   │   ├── layout.tsx                   # Provides the header and footer layout for marketing pages.
│   │   ├── page.tsx                     # Renders the main marketing landing page.
│   │   └── pricing/                     # Contains the marketing pricing page.
│   │       └── page.tsx                 # Renders the product pricing page.
│   ├── actions/                         # Contains Next.js Server Actions used by client components.
│   │   ├── auth/                        # Grouped server actions related to authentication.
│   │   │   ├── email.ts                 # Server actions for email verification.
│   │   │   ├── passwords.ts             # Server actions for password management (forgot, reset, change).
│   │   │   ├── sessions.ts              # Server actions for managing user sessions (list, revoke).
│   │   │   └── signup.ts                # Server action for user and tenant registration.
│   │   └── auth.ts                      # Core authentication server actions (login, logout, refresh).
│   ├── api/                             # API routes (route handlers) that proxy requests to the backend.
│   │   ├── agents/                      # API routes for agent management and status.
│   │   │   ├── [agentName]/             # Dynamic routes for a specific agent.
│   │   │   │   └── status/              # Agent status-related routes.
│   │   │   │       ├── route.test.ts    # Tests for the agent status API route.
│   │   │   │       └── route.ts         # GET route to fetch an agent's status.
│   │   │   ├── route.test.ts            # Tests for the list agents API route.
│   │   │   └── route.ts                 # GET route to list all available agents.
│   │   ├── auth/                        # API routes for authentication and session management.
│   │   │   ├── email/                   # Email verification related API routes.
│   │   │   │   ├── send/                # Route to trigger sending a verification email.
│   │   │   │   │   ├── route.test.ts    # Tests for the send verification email route.
│   │   │   │   │   └── route.ts         # POST route to send a verification email.
│   │   │   │   └── verify/              # Route to verify an email token.
│   │   │   │       ├── route.test.ts    # Tests for the email verification route.
│   │   │   │       └── route.ts         # POST route to verify an email token.
│   │   │   ├── logout/                  # API routes for user logout.
│   │   │   │   ├── all/                 # Route to log out from all sessions.
│   │   │   │   │   ├── route.test.ts    # Tests for the logout-all-sessions route.
│   │   │   │   │   └── route.ts         # POST route to log out of all user sessions.
│   │   │   │   ├── route.test.ts        # Tests for the single-session logout route.
│   │   │   │   └── route.ts             # POST route to log out of the current session.
│   │   │   ├── password/                # API routes for password management.
│   │   │   │   ├── change/              # Route for changing a user's password.
│   │   │   │   │   ├── route.test.ts    # Tests for the change password route.
│   │   │   │   │   └── route.ts         # POST route to change the current user's password.
│   │   │   │   ├── confirm/             # Route to confirm a password reset with a token.
│   │   │   │   │   ├── route.test.ts    # Tests for the password reset confirmation route.
│   │   │   │   │   └── route.ts         # POST route to confirm a password reset.
│   │   │   │   ├── forgot/              # Route to request a password reset link.
│   │   │   │   │   ├── route.test.ts    # Tests for the forgot password route.
│   │   │   │   │   └── route.ts         # POST route to request a password reset email.
│   │   │   │   └── reset/               # Route for admin-initiated password reset.
│   │   │   │       ├── route.test.ts    # Tests for the admin password reset route.
│   │   │   │       └── route.ts         # POST route for an admin to reset a user's password.
│   │   │   ├── refresh/                 # API route for refreshing an authentication session.
│   │   │   │   └── route.ts             # POST route to refresh the session using a refresh token.
│   │   │   ├── register/                # API route for user registration.
│   │   │   │   ├── route.test.ts        # Tests for the user registration route.
│   │   │   │   └── route.ts             # POST route to register a new user and tenant.
│   │   │   ├── service-accounts/        # API routes for service account management.
│   │   │   │   └── issue/               # Route to issue a new service account token.
│   │   │   │       ├── route.test.ts    # Tests for the service account token issuance route.
│   │   │   │       └── route.ts         # POST route to issue a new service account token.
│   │   │   ├── routes_service_account_tokens.py # GET list + POST revoke endpoints for service-account tokens.
│   │   │   ├── session/                 # API route to get current session info.
│   │   │   │   └── route.ts             # GET route to retrieve current user session information.
│   │   │   └── sessions/                # API routes for managing user sessions.
│   │   │       ├── [sessionId]/         # Dynamic route for a specific session.
│   │   │       │   ├── route.test.ts    # Tests for the single session management route.
│   │   │       │   └── route.ts         # DELETE route to revoke a specific user session.
│   │   │       ├── route.test.ts        # Tests for the list sessions route.
│   │   │       └── route.ts             # GET route to list all sessions for the current user.
│   │   ├── billing/                     # API routes for billing, plans, and usage.
│   │   │   ├── plans/                   # Route to get available billing plans.
│   │   │   │   └── route.ts             # GET route to list available billing plans.
│   │   │   ├── stream/                  # Route for the real-time billing event stream.
│   │   │   │   └── route.ts             # GET route to establish a Server-Sent Events (SSE) stream for billing.
│   │   │   └── tenants/                 # Routes for tenant-specific billing information.
│   │   │       └── [tenantId]/          # Dynamic route for a specific tenant.
│   │   │           ├── subscription/    # Routes for managing a tenant's subscription.
│   │   │           │   ├── cancel/      # Route to cancel a subscription.
│   │   │           │   │   ├── route.test.ts # Tests for the cancel subscription route.
│   │   │           │   │   └── route.ts # POST route to cancel a tenant's subscription.
│   │   │           │   ├── route.test.ts # Tests for the subscription management routes.
│   │   │           │   └── route.ts     # GET, POST, PATCH routes for tenant subscription management.
│   │   │           └── usage/           # Route to record metered usage for a tenant.
│   │   │               ├── route.test.ts # Tests for the usage recording route.
│   │   │               └── route.ts     # POST route to record metered usage for a tenant.
│   │   ├── chat/                        # API routes for chat functionality.
│   │   │   ├── route.test.ts            # Tests for the non-streaming chat route.
│   │   │   ├── route.ts                 # POST route for non-streaming chat requests.
│   │   │   └── stream/                  # Route for real-time streaming chat responses.
│   │   │       └── route.ts             # POST route to establish a Server-Sent Events (SSE) stream for chat.
│   │   ├── conversations/               # API routes for managing conversation history.
│   │   │   ├── [conversationId]/        # Dynamic route for a specific conversation.
│   │   │   │   ├── route.test.ts        # Tests for single conversation management routes.
│   │   │   │   └── route.ts             # GET and DELETE routes for a specific conversation.
│   │   │   ├── route.test.ts            # Tests for the list conversations route.
│   │   │   └── route.ts                 # GET route to list all conversations.
│   │   ├── health/                      # API routes for health and readiness probes.
│   │   │   ├── ready/                   # Route for the readiness probe.
│   │   │   │   ├── route.test.ts        # Tests for the readiness probe route.
│   │   │   │   └── route.ts             # GET route for the application readiness check.
│   │   │   ├── route.test.ts            # Tests for the health check route.
│   │   │   └── route.ts                 # GET route for the application health check.
│   │   └── tools/                       # API route for agent tools.
│   │       └── route.ts                 # GET route to list available agent tools.
│   ├── layout.tsx                     # Root application layout, setting up HTML structure and global providers.
│   └── providers.tsx                  # Client-side providers for theming, data fetching, and notifications.
├── components/                          # Reusable UI components shared across the application.
│   ├── auth/                            # Components used specifically for authentication forms.
│   │   ├── ForgotPasswordForm.tsx       # The 'Forgot Password' form component.
│   │   ├── LoginForm.tsx                # The user login form component.
│   │   ├── LogoutButton.tsx             # A client component button to trigger the logout server action.
│   │   ├── RegisterForm.tsx             # The user and tenant registration form component.
│   │   ├── ResetPasswordForm.tsx        # The 'Reset Password' form component.
│   │   └── SilentRefresh.tsx            # A client component that triggers the silent session refresh hook.
│   └── ui/                              # General-purpose UI components, many from shadcn/ui.
├── eslint.config.mjs                    # ESLint configuration for the project.
├── features/                            # High-level feature modules that orchestrate UI components.
│   ├── account/                         # Components that form the account management feature.
│   │   ├── ProfilePanel.tsx             # The main panel for the user profile page.
│   │   ├── SecurityPanel.tsx            # The main panel for the account security page.
│   │   ├── ServiceAccountsPanel.tsx     # The main panel for the service accounts page.
│   │   ├── SessionsPanel.tsx            # The main panel for the user sessions page.
│   │   └── index.ts                     # Barrel file exporting all account feature components.
│   ├── agents/                          # Components that form the agent management feature.
│   │   ├── AgentsOverview.tsx           # The main component for displaying an overview of all agents.
│   │   └── index.ts                     # Barrel file exporting the agents feature components.
│   ├── billing/                         # Components for the billing feature.
│   │   ├── BillingOverview.tsx          # The main component for the billing overview page.
│   │   ├── PlanManagement.tsx           # The main component for managing subscription plans.
│   │   └── index.ts                     # Barrel file exporting billing feature components.
│   ├── chat/                            # The main chat workspace feature.
│   │   ├── ChatWorkspace.tsx            # Orchestrator component for the entire chat interface.
│   │   ├── components/                  # Sub-components used within the ChatWorkspace.
│   │   │   ├── AgentSwitcher.tsx        # A dropdown to select the active agent for a chat.
│   │   │   ├── BillingEventsPanel.tsx   # A panel to display real-time billing events.
│   │   │   ├── ChatInterface.tsx        # The core chat message and input interface.
│   │   │   ├── ConversationSidebar.tsx  # The sidebar for managing and navigating conversations.
│   │   │   ├── ToolMetadataPanel.tsx    # A panel displaying metadata about available tools.
│   │   │   └── __tests__/               # Tests for chat components.
│   │   │       └── BillingEventsPanel.test.tsx # Unit test for the BillingEventsPanel component.
│   │   └── index.ts                     # Barrel file exporting chat feature components.
│   ├── conversations/                   # Components for the conversation history feature.
│   │   ├── ConversationDetailDrawer.tsx # A drawer/sheet to show detailed conversation history.
│   │   ├── ConversationsHub.tsx         # The main component for browsing and searching conversations.
│   │   └── index.ts                     # Barrel file exporting conversations feature components.
│   ├── dashboard/                       # Components that make up the main user dashboard.
│   │   ├── DashboardOverview.tsx        # The main orchestrator component for the dashboard.
│   │   ├── components/                  # Sub-components used within the DashboardOverview.
│   │   │   ├── BillingPreview.tsx       # A component showing a summary of billing status.
│   │   │   ├── KpiGrid.tsx              # A grid for displaying key performance indicators (KPIs).
│   │   │   ├── QuickActions.tsx         # A set of cards for quick navigation to key features.
│   │   │   └── RecentConversations.tsx  # A list of recently updated conversations.
│   │   ├── constants.ts                 # Defines constant data for the dashboard, like quick actions.
│   │   ├── hooks/                       # Custom hooks for the dashboard feature.
│   │   │   └── useDashboardData.tsx     # A hook to fetch and aggregate all data needed for the dashboard.
│   │   ├── index.ts                     # Barrel file exporting the dashboard feature component.
│   │   └── types.ts                     # Type definitions specific to the dashboard feature.
│   ├── settings/                        # Components for the settings feature.
│   │   ├── TenantSettingsPanel.tsx      # The main panel for managing tenant settings.
│   │   └── index.ts                     # Barrel file exporting settings feature components.
│   └── tools/                           # Components for the tools catalog feature.
│       ├── ToolsCatalog.tsx             # The main component for displaying the tool catalog.
│       └── index.ts                     # Barrel file exporting the tools feature component.
├── hooks/                               # Reusable custom React hooks.
│   ├── useAuthForm.ts                   # A custom hook to manage authentication form logic and validation.
│   ├── useBillingStream.ts              # A hook for connecting to the server-sent events billing stream.
│   └── useSilentRefresh.ts              # A hook to handle silent session token refreshing.
├── lib/                                 # Utilities, helpers, and core application logic.
│   ├── api/                             # Abstraction layer for making API calls to the backend.
│   │   ├── __tests__/                   # Tests for the API abstraction layer.
│   │   │   └── chat.test.ts             # Unit tests for the chat API client functions.
│   │   ├── agents.ts                    # Client-side functions for fetching agent data.
│   │   ├── billing.ts                   # Client-side functions for connecting to the billing stream.
│   │   ├── billingPlans.ts              # Client-side functions for fetching billing plan data.
│   │   ├── chat.ts                      # Client-side functions for sending chat messages and streaming responses.
│   │   ├── client/                      # Auto-generated API client from OpenAPI specification.
│   │   │   ├── client/                  # Core files for the generated client.
│   │   │   │   ├── client.gen.ts        # Generated API client instance and configuration.
│   │   │   │   ├── index.ts             # Barrel file exporting client utilities.
│   │   │   │   ├── types.gen.ts         # Generated core types for the API client.
│   │   │   │   └── utils.gen.ts         # Generated utility functions for the API client.
│   │   │   ├── client.gen.ts            # Generated API client initialization.
│   │   │   ├── core/                    # Core utilities and types for the generated API client.
│   │   │   │   ├── auth.gen.ts          # Generated authentication helpers.
│   │   │   │   ├── bodySerializer.gen.ts # Generated body serialization helpers.
│   │   │   │   ├── params.gen.ts        # Generated parameter building helpers.
│   │   │   │   ├── pathSerializer.gen.ts # Generated path serialization helpers.
│   │   │   │   ├── queryKeySerializer.gen.ts # Generated query key serialization helpers.
│   │   │   │   ├── serverSentEvents.gen.ts # Generated SSE client helpers.
│   │   │   │   ├── types.gen.ts         # Generated core types for the client.
│   │   │   │   └── utils.gen.ts         # Generated core utility functions.
│   │   │   ├── index.ts                 # Barrel file for the generated client, exporting types and SDK.
│   │   │   ├── sdk.gen.ts               # Generated SDK functions for each API endpoint.
│   │   │   └── types.gen.ts             # Generated TypeScript types from the OpenAPI schema.
│   │   ├── config.ts                    # Exports the configured generated API client instance.
│   │   ├── conversations.ts             # Client-side functions for fetching conversation data.
│   │   ├── session.ts                   # Client-side functions for managing the user session.
│   │   └── tools.ts                     # Client-side functions for fetching tool data.
│   ├── auth/                            # Client-side and server-side authentication helpers.
│   │   ├── clientMeta.ts                # Client-side utility to read session metadata from cookies.
│   │   ├── cookies.ts                   # Server-side helpers for managing session cookies.
│   │   └── session.ts                   # Server-side logic for session management (exchange, refresh, destroy).
│   ├── chat/                            # Logic for the chat feature.
│   │   ├── __tests__/                   # Tests for chat hooks and utilities.
│   │   │   ├── testUtils.tsx            # Test utilities for chat feature tests.
│   │   │   ├── useChatController.integration.test.tsx # Integration tests for the chat controller hook.
│   │   │   └── useChatController.test.tsx # Unit tests for the chat controller hook.
│   │   ├── types.ts                     # Type definitions for the chat feature.
│   │   └── useChatController.ts         # The core state management hook for the entire chat experience.
│   ├── config.ts                        # Application-wide configuration constants.
│   ├── queries/                         # TanStack Query hooks for data fetching.
│   │   ├── agents.ts                    # TanStack Query hooks for fetching agent data.
│   │   ├── billing.ts                   # Custom hook for the real-time billing event stream.
│   │   ├── billingPlans.ts              # TanStack Query hook for fetching billing plans.
│   │   ├── billingSubscriptions.ts      # TanStack Query hooks and mutations for managing subscriptions.
│   │   ├── chat.ts                      # TanStack Query mutation for sending chat messages.
│   │   ├── conversations.ts             # TanStack Query hooks for fetching and managing conversations.
│   │   ├── keys.ts                      # Centralized, typed query keys for TanStack Query.
│   │   ├── session.ts                   # Custom hook for handling silent session refresh.
│   │   └── tools.ts                     # TanStack Query hook for fetching available tools.
│   ├── server/                          # Server-side logic (for Server Components, Actions, and API Routes).
│   │   ├── apiClient.ts                 # Creates an authenticated API client instance for server-side use.
│   │   ├── services/                    # Server-side functions that call the backend API.
│   │   │   ├── agents.ts                # Server-side service for fetching agent data.
│   │   │   ├── auth/                    # Server-side services for authentication flows.
│   │   │   │   ├── email.ts             # Service functions for email verification.
│   │   │   │   ├── passwords.ts         # Service functions for password management.
│   │   │   │   ├── serviceAccounts.ts   # Service functions for service account management.
│   │   │   │   ├── sessions.ts          # Service functions for user session management.
│   │   │   │   └── signup.ts            # Service function for user/tenant registration.
│   │   │   ├── auth.ts                  # Service functions for core authentication (login, refresh, profile).
│   │   │   ├── billing.ts               # Service functions for interacting with the billing API.
│   │   │   ├── chat.ts                  # Service functions for interacting with the chat API.
│   │   │   ├── conversations.ts         # Service functions for interacting with the conversations API.
│   │   │   ├── health.ts                # Service functions for checking backend health.
│   │   │   └── tools.ts                 # Service functions for interacting with the tools API.
│   │   └── streaming/                   # Server-side logic for handling streaming responses.
│   │       └── chat.ts                  # Server-side helper to stream chat responses directly.
│   ├── types/                           # Application-specific type definitions.
│   │   ├── auth.ts                      # Type definitions for authentication and sessions.
│   │   └── billing.ts                   # Type definitions for billing-related data structures.
│   ├── utils/                           # General utility functions.
│   │   └── time.ts                      # Utility functions for formatting time and dates.
│   └── utils.ts                         # Utility function (`cn`) for merging Tailwind CSS classes.
├── middleware.ts                        # Next.js middleware for authentication and route protection.
├── next.config.ts                       # Next.js framework configuration.
├── openapi-ts.config.ts                 # Configuration for generating the TypeScript API client from an OpenAPI spec.
├── playwright.config.ts                 # Playwright end-to-end testing configuration.
├── pnpm-lock.yaml                       # PNPM lockfile for reproducible dependency installations.
├── postcss.config.mjs                   # PostCSS configuration, primarily for Tailwind CSS.
├── public/                              # Directory for static assets like images and fonts.
├── tailwind.config.ts                   # Tailwind CSS theme and plugin configuration.
├── tests/                               # Directory for end-to-end tests.
│   └── auth-smoke.spec.ts               # A Playwright smoke test for the authentication flow.
├── types/                               # Global type definitions for application entities.
│   ├── agents.ts                        # Type definitions for agent-related data.
│   ├── billing.ts                       # Type definitions for billing-related data.
│   ├── conversations.ts                 # Type definitions for conversation-related data.
│   ├── session.ts                       # Type definitions for session-related data.
│   └── tools.ts                         # Type definitions for tool-related data.
├── vitest.config.ts                     # Vitest unit and integration test runner configuration.
└── vitest.setup.ts                      # Setup file for Vitest tests, extending Jest DOM matchers.
