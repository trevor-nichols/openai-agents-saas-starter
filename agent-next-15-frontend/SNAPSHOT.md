.
├── app/                                 # Next.js App Router directory, containing all routes and UI
│   ├── (app)/                           # Route group for authenticated application pages
│   │   ├── (workspace)/                 # Route group for multi-column, full-screen workspace layouts
│   │   │   ├── chat/                    # Chat interface route
│   │   │   │   ├── actions.ts           # Server Actions for chat streaming and conversation management
│   │   │   │   └── page.tsx             # Page component for the main chat workspace
│   │   │   └── layout.tsx               # Layout for workspace pages providing full-height content
│   │   ├── account/                     # Account management route
│   │   │   └── page.tsx                 # Page component for the user's account overview
│   │   ├── agents/                      # Agents management route
│   │   │   └── page.tsx                 # Page component for viewing available agents
│   │   ├── billing/                     # Billing management route
│   │   │   ├── page.tsx                 # Page component for the billing overview
│   │   │   └── plans/                   # Sub-route for managing billing plans
│   │   │       └── page.tsx             # Page component for plan selection and management
│   │   ├── conversations/               # Conversation history route
│   │   │   └── page.tsx                 # Page component for viewing and managing past conversations
│   │   ├── dashboard/                   # Main dashboard route for authenticated users
│   │   │   └── page.tsx                 # Page component for the dashboard overview
│   │   ├── layout.tsx                   # Main layout for the authenticated app, with sidebar and header
│   │   ├── page.tsx                     # Root page for the authenticated app, redirects to /dashboard
│   │   ├── settings/                    # Settings routes
│   │   │   └── tenant/                  # Tenant-specific settings route
│   │   │       └── page.tsx             # Page component for managing tenant settings
│   │   └── tools/                       # Tool catalog route
│   │       └── page.tsx                 # Page component for viewing the tool catalog
│   ├── (auth)/                          # Route group for authentication pages
│   │   ├── _components/                 # Private components for the authentication layout
│   │   │   └── AuthCard.tsx             # Reusable UI card for authentication forms
│   │   ├── email/                       # Routes for email-related actions
│   │   │   └── verify/                  # Email verification route
│   │   │       ├── VerifyEmailClient.tsx # Client component with logic for verifying an email token
│   │   │       └── page.tsx             # Page component for email verification
│   │   ├── error.tsx                    # Error boundary for authentication routes
│   │   ├── layout.tsx                   # Layout for authentication pages, providing a centered card UI
│   │   ├── loading.tsx                  # Loading UI for authentication routes
│   │   ├── login/                       # Login route
│   │   │   └── page.tsx                 # Page component for the login form
│   │   ├── password/                    # Routes for password management
│   │   │   ├── forgot/                  # Forgot password route
│   │   │   │   └── page.tsx             # Page component for the forgot password form
│   │   │   └── reset/                   # Reset password route
│   │   │       └── page.tsx             # Page component for the password reset form
│   │   └── register/                    # User registration route
│   │       └── page.tsx                 # Page component for the user registration form
│   ├── (marketing)/                     # Route group for public-facing marketing pages
│   │   ├── _components/                 # Private components for the marketing layout
│   │   │   ├── marketing-footer.tsx     # Footer component for marketing pages
│   │   │   ├── marketing-header.tsx     # Header component for marketing pages
│   │   │   └── nav-links.ts             # Defines navigation links for marketing pages
│   │   ├── features/                    # Marketing page for product features
│   │   │   └── page.tsx                 # Page component displaying product features
│   │   ├── layout.tsx                   # Layout for marketing pages, with a public header and footer
│   │   ├── page.tsx                     # The main public landing page for the application
│   │   ├── pricing/                     # Marketing page for pricing information
│   │   │   └── page.tsx                 # Page component displaying pricing tiers
│   │   └── status/                      # Public status page
│   │       └── page.tsx                 # Page component displaying service health status
│   ├── actions/                         # Contains Next.js Server Actions
│   │   ├── auth/                        # Grouped Server Actions for authentication
│   │   │   ├── email.ts                 # Server Actions for email verification
│   │   │   ├── passwords.ts             # Server Actions for password management (reset, change)
│   │   │   ├── sessions.ts              # Server Actions for managing user sessions (list, revoke)
│   │   │   └── signup.ts                # Server Action for user and tenant registration
│   │   └── auth.ts                      # Top-level Server Actions for login, logout, and silent refresh
│   ├── api/                             # API routes (Route Handlers) acting as a backend-for-frontend
│   │   ├── agents/                      # API routes for agent management
│   │   │   ├── [agentName]/             # Dynamic route for a specific agent
│   │   │   │   └── status/              # Agent status route
│   │   │   │       ├── route.test.ts    # Tests for the agent status API route
│   │   │   │       └── route.ts         # API route to get a specific agent's status
│   │   │   ├── route.test.ts            # Tests for the list agents API route
│   │   │   └── route.ts                 # API route to list available agents
│   │   ├── auth/                        # API routes for authentication and authorization
│   │   │   ├── email/                   # Routes for email-related actions
│   │   │   │   ├── send/                # Route to send a verification email
│   │   │   │   │   ├── route.test.ts    # Tests for the send verification email route
│   │   │   │   │   └── route.ts         # API route to trigger sending a verification email
│   │   │   │   └── verify/              # Route to verify an email token
│   │   │   │       ├── route.test.ts    # Tests for the email verification route
│   │   │   │       └── route.ts         # API route to verify an email using a token
│   │   │   ├── logout/                  # Routes for session termination
│   │   │   │   ├── all/                 # Route to log out from all sessions
│   │   │   │   │   ├── route.test.ts    # Tests for the log out all sessions route
│   │   │   │   │   └── route.ts         # API route to log out the user from all devices
│   │   │   │   ├── route.test.ts        # Tests for the single session logout route
│   │   │   │   └── route.ts             # API route to log out the current session
│   │   │   ├── password/                # Routes for password management
│   │   │   │   ├── change/              # Route for changing the current password
│   │   │   │   │   ├── route.test.ts    # Tests for the password change route
│   │   │   │   │   └── route.ts         # API route to handle user password changes
│   │   │   │   ├── confirm/             # Route for confirming a password reset
│   │   │   │   │   ├── route.test.ts    # Tests for the password reset confirmation route
│   │   │   │   │   └── route.ts         # API route to confirm a password reset with a token
│   │   │   │   ├── forgot/              # Route to request a password reset
│   │   │   │   │   ├── route.test.ts    # Tests for the forgot password route
│   │   │   │   │   └── route.ts         # API route to initiate a password reset flow
│   │   │   │   └── reset/               # Route for admin-initiated password reset
│   │   │   │       ├── route.test.ts    # Tests for the admin password reset route
│   │   │   │       └── route.ts         # API route for an admin to reset a user's password
│   │   │   ├── refresh/                 # Route to refresh the auth session
│   │   │   │   └── route.ts             # API route to refresh an access token using a refresh token
│   │   │   ├── register/                # Route for new user registration
│   │   │   │   ├── route.test.ts        # Tests for the user registration route
│   │   │   │   └── route.ts             # API route to handle new user and tenant registration
│   │   │   ├── service-accounts/        # Routes for managing service account tokens
│   │   │   │   ├── browser-issue/       # Route for issuing tokens from the browser
│   │   │   │   │   ├── route.test.ts    # Tests for the browser-based token issuance route
│   │   │   │   │   └── route.ts         # API route to issue a service account token from the browser
│   │   │   │   ├── issue/               # Route for issuing tokens with Vault credentials
│   │   │   │   │   └── route.ts         # API route to issue a service account token via Vault
│   │   │   │   └── tokens/              # Routes for listing and revoking tokens
│   │   │   │       ├── [jti]/           # Dynamic route for a specific token by its JWT ID
│   │   │   │       │   └── revoke/      # Route to revoke a specific token
│   │   │   │       │       ├── route.test.ts # Tests for the token revocation route
│   │   │   │       │       └── route.ts     # API route to revoke a service account token
│   │   │   │       ├── route.test.ts    # Tests for the list tokens route
│   │   │   │       └── route.ts         # API route to list service account tokens
│   │   │   ├── session/                 # Route for getting current session info
│   │   │   │   └── route.ts             # API route to get information about the current user's session
│   │   │   └── sessions/                # Routes for managing all user sessions
│   │   │       ├── [sessionId]/         # Dynamic route for a specific session
│   │   │       │   ├── route.test.ts    # Tests for revoking a specific session
│   │   │       │   └── route.ts         # API route to revoke a specific user session by ID
│   │   │       ├── route.test.ts        # Tests for listing user sessions
│   │   │       └── route.ts             # API route to list all active sessions for the current user
│   │   ├── billing/                     # API routes for billing
│   │   │   ├── plans/                   # Route for billing plans
│   │   │   │   └── route.ts             # API route to list available billing plans
│   │   │   ├── stream/                  # Route for the billing event stream
│   │   │   │   └── route.ts             # API route providing a Server-Sent Events stream for billing
│   │   │   └── tenants/                 # Routes for tenant-specific billing
│   │   │       └── [tenantId]/          # Dynamic route for a specific tenant
│   │   │           ├── subscription/    # Routes for the tenant's subscription
│   │   │           │   ├── cancel/      # Route to cancel a subscription
│   │   │           │   │   ├── route.test.ts # Tests for the subscription cancellation route
│   │   │           │   │   └── route.ts     # API route to cancel a tenant's subscription
│   │   │           │   ├── route.test.ts # Tests for the subscription management route
│   │   │           │   └── route.ts     # API route to get, create, or update a tenant's subscription
│   │   │           └── usage/           # Route for reporting tenant usage
│   │   │               ├── route.test.ts # Tests for the usage reporting route
│   │   │               └── route.ts     # API route to record metered usage for a tenant
│   │   ├── chat/                        # API routes for chat functionality
│   │   │   ├── route.test.ts            # Tests for the non-streaming chat route
│   │   │   ├── route.ts                 # API route for single-shot chat messages
│   │   │   └── stream/                  # Route for streaming chat responses
│   │   │       └── route.ts             # API route providing a Server-Sent Events stream for chat
│   │   ├── conversations/               # API routes for conversation history
│   │   │   ├── [conversationId]/        # Dynamic route for a specific conversation
│   │   │   │   ├── route.test.ts        # Tests for getting/deleting a conversation
│   │   │   │   └── route.ts             # API route to get or delete a specific conversation
│   │   │   ├── route.test.ts            # Tests for the list conversations route
│   │   │   └── route.ts                 # API route to list all conversations for the user
│   │   ├── health/                      # API routes for health checks
│   │   │   ├── ready/                   # Readiness probe route
│   │   │   │   ├── route.test.ts        # Tests for the readiness probe
│   │   │   │   └── route.ts             # API route for readiness checks (e.g., database connection)
│   │   │   ├── route.test.ts            # Tests for the liveness probe
│   │   │   └── route.ts                 # API route for basic liveness checks
│   │   └── tools/                       # API routes for tools
│   │       └── route.ts                 # API route to list available tools
│   ├── layout.tsx                       # Root layout for the entire application
│   └── providers.tsx                    # Client-side providers (React Query, Theme, etc.)
├── components/                          # Reusable React components directory
│   ├── auth/                            # Authentication-related components
│   │   ├── ForgotPasswordForm.tsx       # Form component for the "forgot password" flow
│   │   ├── LoginForm.tsx                # Form component for user login
│   │   ├── LogoutButton.tsx             # A simple button to trigger the logout action
│   │   ├── RegisterForm.tsx             # Form component for new user registration
│   │   ├── ResetPasswordForm.tsx        # Form component for resetting a password with a token
│   │   └── SilentRefresh.tsx            # Component to handle silent authentication token refresh
│   └── ui/                              # General-purpose UI components (from shadcn/ui)
├── eslint.config.mjs                    # ESLint configuration file
├── features/                            # High-level feature modules that orchestrate components and data
│   ├── account/                         # Feature module for account management
│   │   ├── AccountOverview.tsx          # Main component for the account page, handling tab navigation
│   │   ├── ProfilePanel.tsx             # Panel for displaying and editing user profile information
│   │   ├── SecurityPanel.tsx            # Panel for managing security settings like passwords
│   │   ├── ServiceAccountsPanel.tsx     # Panel for managing service account tokens
│   │   ├── SessionsPanel.tsx            # Panel for viewing and managing active user sessions
│   │   ├── __tests__/                   # Tests for the account feature
│   │   │   └── serviceAccountIssueHelpers.test.ts # Unit tests for service account token issuance helpers
│   │   ├── index.ts                     # Barrel file exporting account feature components
│   │   └── serviceAccountIssueHelpers.ts # Helper functions for the service account issuance form
│   ├── agents/                          # Feature module for agent management
│   │   ├── AgentsOverview.tsx           # Main component for the agents page
│   │   └── index.ts                     # Barrel file for the agents feature
│   ├── billing/                         # Feature module for billing
│   │   ├── BillingOverview.tsx          # Main component for the billing overview page
│   │   ├── PlanManagement.tsx           # Component for managing subscription plans
│   │   └── index.ts                     # Barrel file for the billing feature
│   ├── chat/                            # Feature module for the chat workspace
│   │   ├── ChatWorkspace.tsx            # Orchestrator component for the entire chat UI
│   │   ├── components/                  # Sub-components specific to the chat feature
│   │   │   ├── AgentSwitcher.tsx        # Dropdown for selecting the active agent
│   │   │   ├── BillingEventsPanel.tsx   # Panel to display live billing events in the chat workspace
│   │   │   ├── ChatInterface.tsx        # The main chat message and input interface
│   │   │   ├── ConversationDetailDrawer.tsx # Drawer showing details for a specific conversation
│   │   │   ├── ConversationSidebar.tsx  # Sidebar for listing and navigating conversations
│   │   │   ├── ToolMetadataPanel.tsx    # Panel displaying available tools for the current agent
│   │   │   └── __tests__/               # Tests for chat components
│   │   │       └── BillingEventsPanel.test.tsx # Tests for the BillingEventsPanel component
│   │   └── index.ts                     # Barrel file for the chat feature
│   ├── conversations/                   # Feature module for conversation history
│   │   ├── ConversationDetailDrawer.tsx # Drawer to show full details of a conversation
│   │   ├── ConversationsHub.tsx         # Main component for the conversation archive page
│   │   └── index.ts                     # Barrel file for the conversations feature
│   ├── dashboard/                       # Feature module for the main dashboard
│   │   ├── DashboardOverview.tsx        # Main component for the dashboard page
│   │   ├── components/                  # Sub-components for the dashboard
│   │   │   ├── BillingPreview.tsx       # A small preview of billing status
│   │   │   ├── KpiGrid.tsx              # Grid of Key Performance Indicators (KPIs)
│   │   │   ├── QuickActions.tsx         # A set of quick action links
│   │   │   └── RecentConversations.tsx  # A list of recent conversations
│   │   ├── constants.ts                 # Constants used in the dashboard feature
│   │   ├── hooks/                       # Hooks specific to the dashboard feature
│   │   │   └── useDashboardData.tsx     # Hook to fetch and orchestrate all data for the dashboard
│   │   ├── index.ts                     # Barrel file for the dashboard feature
│   │   └── types.ts                     # TypeScript types for the dashboard feature
│   ├── settings/                        # Feature module for settings
│   │   ├── TenantSettingsPanel.tsx      # Component for managing tenant-level settings
│   │   └── index.ts                     # Barrel file for the settings feature
│   └── tools/                           # Feature module for the tool catalog
│       ├── ToolsCatalog.tsx             # Main component for the tool catalog page
│       └── index.ts                     # Barrel file for the tools feature
├── hooks/                               # Directory for globally reusable custom React hooks
│   ├── __tests__/                       # Tests for custom hooks
│   │   └── noLegacyHooks.test.ts        # A test ensuring certain legacy hooks are not re-introduced
│   └── useAuthForm.ts                   # Custom hook for handling authentication form logic and state
├── lib/                                 # Core logic, utilities, and external service integrations
│   ├── api/                             # Client-side functions for making API requests
│   │   ├── __tests__/                   # Tests for API layer functions
│   │   │   └── chat.test.ts             # Tests for the chat API client functions
│   │   ├── account.ts                   # API functions for fetching account and tenant data
│   │   ├── accountSecurity.ts           # API functions related to account security (e.g., password change)
│   │   ├── accountServiceAccounts.ts    # API functions for managing service account tokens
│   │   ├── accountSessions.ts           # API functions for managing user sessions
│   │   ├── agents.ts                    # API functions for fetching agent data
│   │   ├── billing.ts                   # API functions for connecting to the billing SSE stream
│   │   ├── billingPlans.ts              # API functions for fetching billing plans
│   │   ├── billingSubscriptions.ts      # API functions for managing tenant subscriptions
│   │   ├── chat.ts                      # API functions for sending chat messages and streaming responses
│   │   ├── client/                      # Auto-generated API client from OpenAPI specification
│   │   │   ├── client/                  # Core client logic generated by openapi-ts
│   │   │   │   ├── client.gen.ts        # The main generated API client instance
│   │   │   │   ├── index.ts             # Barrel file for the core client
│   │   │   │   ├── types.gen.ts         # Generated TypeScript types for the client
│   │   │   │   └── utils.gen.ts         # Generated utility functions for the client
│   │   │   ├── client.gen.ts            # Entrypoint for the generated client configuration
│   │   │   ├── core/                    # Core utilities for the generated client
│   │   │   │   ├── auth.gen.ts          # Authentication helpers
│   │   │   │   ├── bodySerializer.gen.ts # Body serialization logic
│   │   │   │   ├── params.gen.ts        # Parameter handling logic
│   │   │   │   ├── pathSerializer.gen.ts # Path serialization logic
│   │   │   │   ├── queryKeySerializer.gen.ts # Query key serialization for caching
│   │   │   │   ├── serverSentEvents.gen.ts # SSE client logic
│   │   │   │   ├── types.gen.ts         # Core type definitions
│   │   │   │   └── utils.gen.ts         # Core utility functions
│   │   │   ├── index.ts                 # Barrel file exporting generated types and SDK
│   │   │   ├── sdk.gen.ts               # Generated SDK functions for each API endpoint
│   │   │   └── types.gen.ts             # Generated TypeScript types from the OpenAPI schema
│   │   ├── config.ts                    # Configuration re-export for the generated API client
│   │   ├── conversations.ts             # API functions for fetching and managing conversations
│   │   ├── session.ts                   # API functions for managing the user session (fetch, refresh)
│   │   └── tools.ts                     # API functions for fetching tool data
│   ├── auth/                            # Authentication-related utilities
│   │   ├── clientMeta.ts                # Client-side helper to read session metadata from cookies
│   │   ├── cookies.ts                   # Server-side helpers for getting/setting auth cookies
│   │   └── session.ts                   # Server-side session management functions (login, refresh, destroy)
│   ├── chat/                            # Core logic for the chat feature
│   │   ├── __tests__/                   # Tests for chat logic and hooks
│   │   │   ├── testUtils.tsx            # Test utilities for chat feature tests
│   │   │   ├── useChatController.integration.test.tsx # Integration tests for the chat controller hook
│   │   │   └── useChatController.test.tsx # Unit tests for the chat controller hook
│   │   ├── types.ts                     # TypeScript types for the chat feature
│   │   └── useChatController.ts         # The main custom hook orchestrating chat state and logic
│   ├── config.ts                        # Global application configuration constants
│   ├── queries/                         # TanStack Query hooks and keys
│   │   ├── __tests__/                   # Tests for TanStack Query hooks
│   │   │   └── accountSessions.test.ts  # Tests for the account sessions query hook
│   │   ├── account.ts                   # Query hooks for account profile and tenant data
│   │   ├── accountSecurity.ts           # Mutation hooks for account security actions
│   │   ├── accountServiceAccounts.ts    # Query and mutation hooks for service accounts
│   │   ├── accountSessions.ts           # Query and mutation hooks for user sessions
│   │   ├── agents.ts                    # Query hooks for fetching agent data
│   │   ├── billing.ts                   # Custom hook for the real-time billing event stream
│   │   ├── billingPlans.ts              # Query hook for fetching billing plans
│   │   ├── billingSubscriptions.ts      # Query and mutation hooks for managing subscriptions
│   │   ├── chat.ts                      # Mutation hook for sending chat messages
│   │   ├── conversations.ts             # Query hooks for fetching conversation lists and details
│   │   ├── keys.ts                      # Centralized definitions for all TanStack Query keys
│   │   ├── session.ts                   # Custom hook for managing silent session refresh
│   │   └── tools.ts                     # Query hook for fetching tool data
│   ├── server/                          # Server-side only logic
│   │   ├── apiClient.ts                 # Helper to create an authenticated API client for server-side use
│   │   ├── services/                    # Service layer abstracting backend API calls
│   │   │   ├── agents.ts                # Service functions for interacting with the agent API
│   │   │   ├── auth/                    # Grouped services for authentication
│   │   │   │   ├── email.ts             # Service functions for email verification
│   │   │   │   ├── passwords.ts         # Service functions for password management
│   │   │   │   ├── serviceAccounts.ts   # Service functions for service accounts
│   │   │   │   ├── sessions.ts          # Service functions for user sessions
│   │   │   │   └── signup.ts            # Service function for user registration
│   │   │   ├── auth.ts                  # Service functions for core authentication (login, refresh, profile)
│   │   │   ├── billing.ts               # Service functions for billing and subscriptions
│   │   │   ├── chat.ts                  # Service functions for chat interactions
│   │   │   ├── conversations.ts         # Service functions for managing conversations
│   │   │   ├── health.ts                # Service functions for health checks
│   │   │   └── tools.ts                 # Service functions for interacting with the tools API
│   │   └── streaming/                   # Server-side logic for handling streams
│   │       └── chat.ts                  # Server-side helper to proxy chat streams from the backend
│   ├── types/                           # Shared internal TypeScript types
│   │   ├── auth.ts                      # TypeScript types for authentication
│   │   └── billing.ts                   # TypeScript types for billing
│   └── utils/                           # General utility functions
│       └── time.ts                      # Utility functions for time and date formatting
│   └── utils.ts                         # Main utility file, includes `cn` for class name merging
├── middleware.ts                        # Next.js middleware for handling authentication and routing
├── next.config.ts                       # Next.js configuration file
├── openapi-ts.config.ts                 # Configuration for generating the API client from an OpenAPI spec
├── playwright.config.ts                 # Configuration for Playwright end-to-end tests
├── pnpm-lock.yaml                       # PNPM lockfile for dependency management
├── postcss.config.mjs                   # PostCSS configuration for Tailwind CSS
├── public/                              # Directory for static assets (images, fonts, etc.)
├── tailwind.config.ts                   # Tailwind CSS theme and plugin configuration
├── tests/                               # Directory for end-to-end tests
│   └── auth-smoke.spec.ts               # A Playwright smoke test for the authentication flow
├── types/                               # Global TypeScript type definitions for the application
│   ├── account.ts                       # Types related to user accounts and profiles
│   ├── agents.ts                        # Types related to AI agents
│   ├── billing.ts                       # Types related to billing, plans, and subscriptions
│   ├── conversations.ts                 # Types related to chat conversations
│   ├── serviceAccounts.ts               # Types related to service accounts and their tokens
│   ├── session.ts                       # Types related to user sessions
│   └── tools.ts                         # Types related to agent tools
├── vitest.config.ts                     # Vitest (unit/integration test runner) configuration
└── vitest.setup.ts                      # Setup file for Vitest tests