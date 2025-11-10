.
├── app/                                        # Next.js App Router directory containing all routes and layouts.
│   ├── (app)/                                  # Route group for authenticated application pages.
│   │   ├── (workspace)/                        # Route group for workspace-style layouts (e.g., chat).
│   │   │   ├── chat/                           # Chat feature route directory.
│   │   │   │   ├── actions.ts                  # Server Actions for chat streaming and conversation listing.
│   │   │   │   └── page.tsx                    # Page component for the `/chat` route.
│   │   │   └── layout.tsx                      # Layout for workspace pages providing a full-height container.
│   │   ├── account/                            # Routes for user account management.
│   │   │   ├── profile/                        # User profile page route.
│   │   │   │   └── page.tsx                    # Page component for the user profile.
│   │   │   ├── security/                       # User security settings route.
│   │   │   │   └── page.tsx                    # Page component for security settings.
│   │   │   ├── service-accounts/               # Service accounts management route.
│   │   │   │   └── page.tsx                    # Page component for managing service accounts.
│   │   │   └── sessions/                       # Active user sessions route.
│   │   │       └── page.tsx                    # Page component for managing user sessions.
│   │   ├── agents/                             # Agents overview route.
│   │   │   └── page.tsx                        # Page component for viewing agents.
│   │   ├── billing/                            # Billing management routes.
│   │   │   ├── page.tsx                        # Page component for the main billing overview.
│   │   │   └── plans/                          # Billing plans management route.
│   │   │       └── page.tsx                    # Page component for managing billing plans.
│   │   ├── conversations/                      # Conversations history route.
│   │   │   └── page.tsx                        # Page component for listing conversations.
│   │   ├── dashboard/                          # Main dashboard route for authenticated users.
│   │   │   └── page.tsx                        # Page component for the dashboard.
│   │   ├── layout.tsx                          # Main layout for the authenticated app shell with navigation.
│   │   ├── page.tsx                            # Root page for the authenticated app, redirects to dashboard.
│   │   ├── settings/                           # Settings routes.
│   │   │   └── tenant/                         # Tenant settings route.
│   │   │       └── page.tsx                    # Page component for tenant settings.
│   │   └── tools/                              # Tools catalog route.
│   │       └── page.tsx                        # Page component for viewing available tools.
│   ├── (auth)/                                 # Route group for authentication pages.
│   │   ├── email/                              # Email-related auth routes.
│   │   │   └── verify/                         # Email verification route.
│   │   │       └── page.tsx                    # Page component for handling email verification.
│   │   ├── layout.tsx                          # Layout for auth pages, providing a centered card UI.
│   │   ├── login/                              # Login route.
│   │   │   └── page.tsx                        # Page component for the user login form.
│   │   ├── password/                           # Password management routes.
│   │   │   ├── forgot/                         # Forgot password route.
│   │   │   │   └── page.tsx                    # Page component for requesting a password reset.
│   │   │   └── reset/                          # Reset password route.
│   │   │       └── page.tsx                    # Page component for resetting password with a token.
│   │   └── register/                           # Registration route.
│   │       └── page.tsx                        # Page component for user and tenant registration.
│   ├── (marketing)/                            # Route group for public marketing pages.
│   │   ├── features/                           # Product features page route.
│   │   │   └── page.tsx                        # Page component detailing product features.
│   │   ├── layout.tsx                          # Layout for marketing pages with a public header/footer.
│   │   ├── page.tsx                            # The main product landing page component.
│   │   └── pricing/                            # Product pricing page route.
│   │       └── page.tsx                        # Page component for displaying pricing plans.
│   ├── actions/                                # Next.js Server Actions.
│   │   ├── auth/                               # Server actions related to authentication.
│   │   │   ├── email.ts                      # Server actions for email verification.
│   │   │   ├── passwords.ts                  # Server actions for password management.
│   │   │   ├── sessions.ts                   # Server actions for session management.
│   │   │   └── signup.ts                     # Server action for user/tenant registration.
│   │   └── auth.ts                             # Core authentication server actions (login, logout).
│   ├── api/                                    # API route handlers (Next.js App Router).
│   │   ├── agents/                             # API routes for agent management.
│   │   │   ├── [agentName]/                    # Dynamic route for a specific agent.
│   │   │   │   └── status/                     # Agent status endpoint.
│   │   │   │       ├── route.test.ts           # Tests for the agent status API endpoint.
│   │   │   │       └── route.ts                # API route handler to get a specific agent's status.
│   │   │   ├── route.test.ts                   # Tests for the list agents API endpoint.
│   │   │   └── route.ts                        # API route handler to list all available agents.
│   │   ├── auth/                               # API routes for authentication.
│   │   │   ├── email/                          # Email verification API routes.
│   │   │   │   ├── send/                       # API endpoint for sending verification emails.
│   │   │   │   │   ├── route.test.ts           # Tests for the send verification email endpoint.
│   │   │   │   │   └── route.ts                # API route handler to send a verification email.
│   │   │   │   └── verify/                     # API endpoint for verifying an email.
│   │   │   │       ├── route.test.ts           # Tests for the email verification endpoint.
│   │   │   │       └── route.ts                # API route handler to verify an email token.
│   │   │   ├── logout/                         # User logout API routes.
│   │   │   │   ├── all/                        # API endpoint to log out from all sessions.
│   │   │   │   │   ├── route.test.ts           # Tests for the logout all sessions endpoint.
│   │   │   │   │   └── route.ts                # API route handler to log out from all user sessions.
│   │   │   │   ├── route.test.ts               # Tests for the single session logout endpoint.
│   │   │   │   └── route.ts                    # API route handler to log out from the current session.
│   │   │   ├── password/                       # Password management API routes.
│   │   │   │   ├── change/                     # API endpoint for changing a password.
│   │   │   │   │   ├── route.test.ts           # Tests for the password change endpoint.
│   │   │   │   │   └── route.ts                # API route handler for a user to change their own password.
│   │   │   │   ├── confirm/                    # API endpoint to confirm a password reset.
│   │   │   │   │   ├── route.test.ts           # Tests for the password reset confirmation endpoint.
│   │   │   │   │   └── route.ts                # API route handler to confirm a password reset with a token.
│   │   │   │   ├── forgot/                     # API endpoint to request a password reset.
│   │   │   │   │   ├── route.test.ts           # Tests for the forgot password endpoint.
│   │   │   │   │   └── route.ts                # API route handler to initiate a password reset.
│   │   │   │   └── reset/                      # API endpoint for admin-initiated password resets.
│   │   │   │       ├── route.test.ts           # Tests for the admin password reset endpoint.
│   │   │   │       └── route.ts                # API route handler for an admin to reset a user's password.
│   │   │   ├── refresh/                        # API endpoint to refresh an access token.
│   │   │   │   └── route.ts                    # API route handler to refresh an authentication session.
│   │   │   ├── register/                       # API endpoint for user/tenant registration.
│   │   │   │   ├── route.test.ts               # Tests for the registration endpoint.
│   │   │   │   └── route.ts                    # API route handler to register a new user and tenant.
│   │   │   ├── service-accounts/               # API routes for service accounts.
│   │   │   │   └── issue/                      # API endpoint to issue a new service account token.
│   │   │   │       ├── route.test.ts           # Tests for the service account token issuance endpoint.
│   │   │   │       └── route.ts                # API route handler to issue a service account token.
│   │   │   ├── session/                        # API endpoint for the current session.
│   │   │   │   └── route.ts                    # API route handler to get current session information.
│   │   │   └── sessions/                       # API routes for managing user sessions.
│   │   │       ├── [sessionId]/                # Dynamic route for a specific session.
│   │   │       │   ├── route.test.ts           # Tests for the specific session management endpoint.
│   │   │       │   └── route.ts                # API route handler to revoke a specific user session.
│   │   │       ├── route.test.ts               # Tests for the list sessions endpoint.
│   │   │       └── route.ts                    # API route handler to list all of a user's sessions.
│   │   ├── billing/                            # API routes for billing.
│   │   │   ├── plans/                          # API endpoint for billing plans.
│   │   │   │   └── route.ts                    # API route handler to list available billing plans.
│   │   │   ├── stream/                         # API endpoint for the billing event stream.
│   │   │   │   └── route.ts                    # Server-Sent Events (SSE) route for real-time billing events.
│   │   │   └── tenants/                        # API routes for tenant-specific billing.
│   │   │       └── [tenantId]/                 # Dynamic route for a specific tenant.
│   │   │           ├── subscription/           # API routes for a tenant's subscription.
│   │   │           │   ├── cancel/             # API endpoint to cancel a subscription.
│   │   │           │   │   ├── route.test.ts   # Tests for the subscription cancellation endpoint.
│   │   │           │   │   └── route.ts        # API route handler to cancel a tenant's subscription.
│   │   │           │   ├── route.test.ts       # Tests for the subscription management endpoint.
│   │   │           │   └── route.ts            # API route handlers for managing a tenant's subscription (GET, POST, PATCH).
│   │   │           └── usage/                  # API endpoint to record metered usage.
│   │   │               ├── route.test.ts       # Tests for the usage recording endpoint.
│   │   │               └── route.ts            # API route handler to record metered usage for a tenant.
│   │   ├── chat/                               # API routes for chat functionality.
│   │   │   ├── route.test.ts                   # Tests for the non-streaming chat endpoint.
│   │   │   ├── route.ts                        # API route handler for single-shot chat messages.
│   │   │   └── stream/                         # API endpoint for streaming chat responses.
│   │   │       └── route.ts                    # Server-Sent Events (SSE) route for real-time chat responses.
│   │   ├── conversations/                      # API routes for conversations.
│   │   │   ├── [conversationId]/               # Dynamic route for a specific conversation.
│   │   │   │   ├── route.test.ts               # Tests for the specific conversation endpoint.
│   │   │   │   └── route.ts                    # API route handlers to get or delete a specific conversation.
│   │   │   ├── route.test.ts                   # Tests for the list conversations endpoint.
│   │   │   └── route.ts                        # API route handler to list all conversations.
│   │   ├── health/                             # API routes for health checks.
│   │   │   ├── ready/                          # Readiness probe endpoint.
│   │   │   │   ├── route.test.ts               # Tests for the readiness probe endpoint.
│   │   │   │   └── route.ts                    # API route handler for readiness checks.
│   │   │   ├── route.test.ts                   # Tests for the liveness probe endpoint.
│   │   │   └── route.ts                        # API route handler for liveness checks.
│   │   └── tools/                              # API routes for tools.
│   │       └── route.ts                        # API route handler to list available tools.
│   ├── layout.tsx                              # Root layout component for the entire application.
│   └── providers.tsx                           # Client-side providers, primarily for React Query.
├── components/                                 # Reusable React components.
│   ├── auth/                                   # Authentication-related components.
│   │   ├── LoginForm.tsx                       # Login form component using Server Actions.
│   │   ├── LogoutButton.tsx                    # Client-side button to trigger the logout action.
│   │   └── SilentRefresh.tsx                   # Component to trigger the silent token refresh hook.
│   └── ui/                                     # UI components, mostly from Shadcn/ui.
├── eslint.config.mjs                           # ESLint configuration file.
├── features/                                   # High-level feature components (feature-sliced design).
│   ├── account/                                # Components for the account management feature.
│   │   ├── ProfilePanel.tsx                  # The main panel for the user profile page.
│   │   ├── SecurityPanel.tsx                 # The main panel for the security settings page.
│   │   ├── ServiceAccountsPanel.tsx          # The main panel for managing service accounts.
│   │   ├── SessionsPanel.tsx                 # The main panel for managing active user sessions.
│   │   └── index.ts                          # Barrel file exporting all account feature components.
│   ├── agents/                                 # Components for the agents feature.
│   │   ├── AgentsOverview.tsx                # The main component for the agents overview page.
│   │   └── index.ts                          # Barrel file exporting agents feature components.
│   ├── billing/                                # Components for the billing feature.
│   │   ├── BillingOverview.tsx               # The main component for the billing overview page.
│   │   ├── PlanManagement.tsx                # The main component for the plan management page.
│   │   └── index.ts                          # Barrel file exporting billing feature components.
│   ├── chat/                                   # Components for the chat feature.
│   │   ├── ChatWorkspace.tsx                 # The main orchestrator component for the entire chat workspace.
│   │   ├── components/                         # Sub-components specific to the chat feature.
│   │   │   ├── BillingEventsPanel.tsx        # Panel to display real-time billing events during a chat.
│   │   │   ├── ChatInterface.tsx             # The main chat UI with messages and input form.
│   │   │   ├── ConversationSidebar.tsx       # Sidebar for listing and managing conversations.
│   │   │   └── __tests__/                      # Tests for chat sub-components.
│   │   │       └── BillingEventsPanel.test.tsx # Unit test for the BillingEventsPanel component.
│   │   └── index.ts                          # Barrel file exporting chat feature components.
│   ├── conversations/                          # Components for the conversations feature.
│   │   ├── ConversationsHub.tsx              # The main component for the conversations list page.
│   │   └── index.ts                          # Barrel file exporting conversations feature components.
│   ├── dashboard/                              # Components for the dashboard feature.
│   │   ├── DashboardOverview.tsx             # The main component for the dashboard overview page.
│   │   └── index.ts                          # Barrel file exporting dashboard feature components.
│   ├── settings/                               # Components for the settings feature.
│   │   ├── TenantSettingsPanel.tsx           # The main panel for the tenant settings page.
│   │   └── index.ts                          # Barrel file exporting settings feature components.
│   └── tools/                                  # Components for the tools feature.
│       ├── ToolsCatalog.tsx                  # The main component for the tools catalog page.
│       └── index.ts                          # Barrel file exporting tools feature components.
├── hooks/                                      # Custom React hooks (likely deprecated in favor of lib/queries).
│   ├── useBillingStream.ts                     # An older implementation of the billing stream hook.
│   └── useSilentRefresh.ts                     # An older implementation of the silent session refresh hook.
├── lib/                                        # Core logic, utilities, and API communication.
│   ├── api/                                    # Client-side functions for interacting with the API.
│   │   ├── __tests__/                          # Tests for API layer functions.
│   │   │   └── chat.test.ts                  # Tests for the chat API functions.
│   │   ├── agents.ts                         # Functions to fetch agent data.
│   │   ├── billing.ts                        # Function to connect to the billing SSE stream.
│   │   ├── billingPlans.ts                   # Function to fetch billing plans.
│   │   ├── chat.ts                           # Functions for sending and streaming chat messages.
│   │   ├── client/                           # Auto-generated API client from OpenAPI schema.
│   │   │   ├── client/                       # Core client generation logic.
│   │   │   │   ├── client.gen.ts             # Generated client factory function.
│   │   │   │   ├── index.ts                  # Barrel file for client core exports.
│   │   │   │   ├── types.gen.ts              # Generated core client types.
│   │   │   │   └── utils.gen.ts              # Generated client utility functions.
│   │   │   ├── client.gen.ts                 # Main generated client instance.
│   │   │   ├── core/                         # Core utilities for the generated client.
│   │   │   │   ├── auth.gen.ts               # Generated authentication helpers.
│   │   │   │   ├── bodySerializer.gen.ts     # Generated body serialization helpers.
│   │   │   │   ├── params.gen.ts             # Generated parameter building helpers.
│   │   │   │   ├── pathSerializer.gen.ts     # Generated path serialization helpers.
│   │   │   │   ├── queryKeySerializer.gen.ts # Generated query key serialization helpers.
│   │   │   │   ├── serverSentEvents.gen.ts   # Generated SSE client logic.
│   │   │   │   ├── types.gen.ts              # Generated core utility types.
│   │   │   │   └── utils.gen.ts              # Generated core general utilities.
│   │   │   ├── index.ts                      # Barrel file exporting generated types and SDK.
│   │   │   ├── sdk.gen.ts                    # Generated SDK functions for each API endpoint.
│   │   │   └── types.gen.ts                  # Generated TypeScript types from the OpenAPI schema.
│   │   ├── config.ts                         # Re-exports the generated API client.
│   │   ├── conversations.ts                  # Functions to fetch and manage conversation data.
│   │   ├── session.ts                        # Functions to manage the user session (fetch, refresh).
│   │   └── tools.ts                          # Function to fetch the tool registry.
│   ├── auth/                                   # Authentication-related logic.
│   │   ├── clientMeta.ts                     # Client-side utility to read session metadata from cookies.
│   │   ├── cookies.ts                        # Server-side utilities for handling auth cookies.
│   │   └── session.ts                        # Server-side session management functions.
│   ├── chat/                                   # Client-side logic for the chat feature.
│   │   ├── __tests__/                          # Tests for the chat controller hook.
│   │   │   ├── testUtils.tsx                 # Test utilities for chat feature tests.
│   │   │   ├── useChatController.integration.test.tsx # Integration test for the chat controller hook.
│   │   │   └── useChatController.test.tsx    # Unit tests for the chat controller hook.
│   │   ├── types.ts                          # TypeScript types specific to the chat feature.
│   │   └── useChatController.ts              # The primary hook for managing chat state and logic.
│   ├── config.ts                               # Global application configuration constants.
│   ├── queries/                                # TanStack Query hooks for data fetching.
│   │   ├── agents.ts                         # Hook for fetching agent data.
│   │   ├── billing.ts                        # Hook for the real-time billing event stream.
│   │   ├── billingPlans.ts                   # Hook for fetching billing plans.
│   │   ├── billingSubscriptions.ts           # Hooks for managing tenant subscriptions.
│   │   ├── chat.ts                           # Hook for the chat mutation (sending messages).
│   │   ├── conversations.ts                  # Hook for fetching and managing the conversation list.
│   │   ├── keys.ts                           # Centralized query keys for TanStack Query.
│   │   ├── session.ts                        # Hook for managing silent session refresh.
│   │   └── tools.ts                          # Hook for fetching the tool registry.
│   ├── server/                                 # Server-side only logic.
│   │   ├── apiClient.ts                      # Factory for creating an authenticated server-side API client.
│   │   ├── services/                         # Service layer wrapping API client calls.
│   │   │   ├── agents.ts                   # Service functions for agent-related operations.
│   │   │   ├── auth/                       # Authentication-related service functions.
│   │   │   │   ├── email.ts                # Service functions for email verification.
│   │   │   │   ├── passwords.ts            # Service functions for password management.
│   │   │   │   ├── serviceAccounts.ts      # Service function for issuing service account tokens.
│   │   │   │   ├── sessions.ts             # Service functions for managing user sessions.
│   │   │   │   └── signup.ts               # Service function for user registration.
│   │   │   ├── auth.ts                     # Core authentication service functions (login, refresh, profile).
│   │   │   ├── billing.ts                  # Service functions for billing operations.
│   │   │   ├── chat.ts                     # Service functions for chat operations.
│   │   │   ├── conversations.ts            # Service functions for conversation management.
│   │   │   ├── health.ts                   # Service functions for health checks.
│   │   │   └── tools.ts                    # Service function for listing tools.
│   │   └── streaming/                        # Server-side helpers for handling streaming responses.
│   │       └── chat.ts                     # Server-side function to stream chat responses.
│   ├── types/                                  # Shared TypeScript types for the application.
│   │   ├── auth.ts                           # Authentication-related types.
│   │   └── billing.ts                        # Billing-related types.
│   └── utils.ts                                # General utility functions, like `cn` for classnames.
├── middleware.ts                               # Next.js middleware for authentication and route protection.
├── next.config.ts                              # Next.js configuration file.
├── openapi-ts.config.ts                        # Configuration for the OpenAPI TypeScript client generator.
├── playwright.config.ts                        # Configuration for Playwright end-to-end tests.
├── pnpm-lock.yaml                              # PNPM lockfile defining exact dependency versions.
├── postcss.config.mjs                          # PostCSS configuration for Tailwind CSS.
├── public/                                     # Directory for static assets like images and fonts.
├── tailwind.config.ts                          # Tailwind CSS theme and plugin configuration.
├── tests/                                      # Directory for end-to-end tests.
│   └── auth-smoke.spec.ts                      # A Playwright smoke test for the login-chat-logout flow.
├── types/                                      # Directory for globally shared TypeScript types.
│   ├── agents.ts                               # Types related to agents.
│   ├── billing.ts                              # Types related to billing.
│   ├── conversations.ts                        # Types related to conversations.
│   ├── session.ts                              # Types related to user sessions.
│   └── tools.ts                                # Types related to tools.
├── vitest.config.ts                            # Vitest configuration for unit and integration testing.
└── vitest.setup.ts                             # Setup file for Vitest, e.g., for extending matchers.