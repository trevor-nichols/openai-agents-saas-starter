```
.
├── app/                                 # Next.js App Router directory containing all routes and UI
│   ├── (app)/                           # Route group for authenticated application pages
│   │   ├── (workspace)/                 # Route group for multi-column workspace layouts (e.g., chat)
│   │   │   ├── chat/                    # Chat feature pages
│   │   │   │   ├── actions.ts          # Server Actions for chat streaming and conversation management
│   │   │   │   └── page.tsx            # Main page for the chat workspace
│   │   │   ├── layout.tsx               # Layout for workspace views, providing specific styling
│   │   ├── account/                     # Pages for user account management
│   │   │   ├── profile/                 # User profile page
│   │   │   │   └── page.tsx            # Renders the user's profile panel
│   │   │   ├── security/                # User security settings page
│   │   │   │   └── page.tsx            # Renders the security settings panel
│   │   │   ├── service-accounts/        # Service account management page
│   │   │   │   └── page.tsx            # Renders the service accounts panel
│   │   │   └── sessions/                # Active user sessions page
│   │   │       └── page.tsx            # Renders the user sessions panel
│   │   ├── agents/                      # Agents overview page
│   │   │   └── page.tsx                 # Renders the agents overview feature
│   │   ├── billing/                     # Billing management pages
│   │   │   ├── page.tsx                 # Renders the main billing overview
│   │   │   └── plans/                   # Page for managing subscription plans
│   │   │       └── page.tsx             # Renders the plan management feature
│   │   ├── conversations/               # Conversation history page
│   │   │   └── page.tsx                 # Renders the conversation hub feature
│   │   ├── dashboard/                   # Main dashboard page for authenticated users
│   │   │   └── page.tsx                 # Renders the dashboard overview feature
│   │   ├── layout.tsx                   # Main layout for the authenticated app (sidebar, header)
│   │   ├── page.tsx                     # Root page for the authenticated app, redirects to /dashboard
│   │   ├── settings/                    # Application settings pages
│   │   │   └── tenant/                  # Tenant-specific settings
│   │   │       └── page.tsx             # Renders the tenant settings panel
│   │   └── tools/                       # Tool catalog page
│   │       └── page.tsx                 # Renders the tool catalog feature
│   ├── (auth)/                          # Route group for authentication pages
│   │   ├── email/                       # Email-related auth pages
│   │   │   └── verify/                  # Email verification page
│   │   │       └── page.tsx             # Page for handling email verification tokens
│   │   ├── layout.tsx                   # Layout for auth pages with a centered card UI
│   │   ├── login/                       # Login page
│   │   │   └── page.tsx                 # Renders the login form
│   │   ├── password/                    # Password management pages
│   │   │   ├── forgot/                  # "Forgot password" page
│   │   │   │   └── page.tsx             # Renders the forgot password form
│   │   │   └── reset/                   # "Reset password" page
│   │   │       └── page.tsx             # Page for handling password reset tokens
│   │   └── register/                    # User registration page
│   │       └── page.tsx                 # Renders the registration/signup form
│   ├── (marketing)/                     # Route group for public-facing marketing pages
│   │   ├── features/                    # Product features page
│   │   │   └── page.tsx                 # Displays an overview of product features
│   │   ├── layout.tsx                   # Layout for marketing pages (header, footer)
│   │   ├── page.tsx                     # The main product landing page
│   │   └── pricing/                     # Product pricing page
│   │       └── page.tsx                 # Displays subscription plans and pricing
│   ├── actions/                         # Server Actions used across the application
│   │   ├── auth/                        # Authentication-related Server Actions
│   │   │   ├── email.ts                # Actions for sending and verifying emails
│   │   │   ├── passwords.ts            # Actions for password management (reset, change)
│   │   │   ├── sessions.ts             # Actions for listing and revoking user sessions
│   │   │   └── signup.ts               # Action for new user/tenant registration
│   │   └── auth.ts                      # Core authentication actions like login, logout, and refresh
│   ├── api/                             # API Route Handlers (proxy layer to a backend service)
│   │   ├── agents/                      # API routes for agents
│   │   │   ├── [agentName]/             # Dynamic route for a specific agent
│   │   │   │   └── status/              # Agent status endpoint
│   │   │   │       ├── route.test.ts   # Tests for the agent status API endpoint
│   │   │   │       └── route.ts        # GET endpoint to fetch status for a specific agent
│   │   │   ├── route.test.ts            # Tests for the agent list API endpoint
│   │   │   └── route.ts                 # GET endpoint to list all available agents
│   │   ├── auth/                        # API routes for authentication and authorization
│   │   │   ├── email/                   # Endpoints for email verification
│   │   │   │   ├── send/               # Endpoint to trigger sending a verification email
│   │   │   │   │   ├── route.test.ts   # Tests for the send verification email endpoint
│   │   │   │   │   └── route.ts        # POST endpoint to send a verification email
│   │   │   │   └── verify/             # Endpoint to verify an email token
│   │   │   │       ├── route.test.ts   # Tests for the email verification endpoint
│   │   │   │       └── route.ts        # POST endpoint to verify an email token
│   │   │   ├── logout/                  # Endpoints for logging out
│   │   │   │   ├── all/                # Endpoint to log out all sessions for a user
│   │   │   │   │   ├── route.test.ts   # Tests for the logout all sessions endpoint
│   │   │   │   │   └── route.ts        # POST endpoint to log out all user sessions
│   │   │   │   ├── route.test.ts        # Tests for the single session logout endpoint
│   │   │   │   └── route.ts             # POST endpoint to log out the current session
│   │   │   ├── password/                # Endpoints for password management
│   │   │   │   ├── change/             # Endpoint for changing a user's password
│   │   │   │   │   ├── route.test.ts   # Tests for the change password endpoint
│   │   │   │   │   └── route.ts        # POST endpoint for a user to change their own password
│   │   │   │   ├── confirm/            # Endpoint for confirming a password reset
│   │   │   │   │   ├── route.test.ts   # Tests for the password reset confirmation endpoint
│   │   │   │   │   └── route.ts        # POST endpoint to confirm a password reset with a token
│   │   │   │   ├── forgot/             # Endpoint for initiating a password reset
│   │   │   │   │   ├── route.test.ts   # Tests for the forgot password endpoint
│   │   │   │   │   └── route.ts        # POST endpoint to request a password reset email
│   │   │   │   └── reset/              # Endpoint for admin-initiated password resets
│   │   │   │       ├── route.test.ts   # Tests for the admin password reset endpoint
│   │   │   │       └── route.ts        # POST endpoint for an admin to reset a user's password
│   │   │   ├── refresh/                 # Endpoint for refreshing an access token
│   │   │   │   └── route.ts             # POST endpoint to refresh an authentication session
│   │   │   ├── register/                # Endpoint for user registration
│   │   │   │   ├── route.test.ts        # Tests for the registration endpoint
│   │   │   │   └── route.ts             # POST endpoint to register a new user and tenant
│   │   │   ├── service-accounts/        # Endpoints for service accounts
│   │   │   │   └── issue/               # Endpoint to issue a token for a service account
│   │   │   │       ├── route.test.ts   # Tests for the service account token issuance endpoint
│   │   │   │       └── route.ts        # POST endpoint to issue a service account token
│   │   │   ├── session/                 # Endpoint to get current session info
│   │   │   │   └── route.ts             # GET endpoint to retrieve the current user's session details
│   │   │   └── sessions/                # Endpoints for managing user sessions
│   │   │       ├── [sessionId]/         # Dynamic route for a specific session
│   │   │       │   ├── route.test.ts   # Tests for revoking a specific session
│   │   │       │   └── route.ts        # DELETE endpoint to revoke a specific user session
│   │   │       ├── route.test.ts        # Tests for listing user sessions
│   │   │       └── route.ts             # GET endpoint to list all of a user's sessions
│   │   ├── billing/                     # API routes for billing
│   │   │   ├── plans/                   # Endpoint for billing plans
│   │   │   │   └── route.ts             # GET endpoint to list available billing plans
│   │   │   ├── stream/                  # Endpoint for real-time billing events
│   │   │   │   └── route.ts             # GET endpoint to open a Server-Sent Events stream for billing
│   │   │   └── tenants/                 # Endpoints for tenant-specific billing
│   │   │       └── [tenantId]/          # Dynamic route for a specific tenant
│   │   │           ├── subscription/    # Endpoints for managing a tenant's subscription
│   │   │           │   ├── cancel/     # Endpoint to cancel a subscription
│   │   │           │   │   ├── route.test.ts # Tests for the subscription cancellation endpoint
│   │   │           │   │   └── route.ts    # POST endpoint to cancel a tenant's subscription
│   │   │           │   ├── route.test.ts   # Tests for subscription management endpoints
│   │   │           │   └── route.ts        # GET, PATCH, and POST endpoints for subscription management
│   │   │           └── usage/           # Endpoint for recording metered usage
│   │   │               ├── route.test.ts # Tests for the usage recording endpoint
│   │   │               └── route.ts      # POST endpoint to record metered usage for a tenant
│   │   ├── chat/                        # API routes for chat functionality
│   │   │   ├── route.test.ts            # Tests for the non-streaming chat endpoint
│   │   │   ├── route.ts                 # POST endpoint for single-shot (non-streaming) chat messages
│   │   │   └── stream/                  # Endpoint for streaming chat responses
│   │   │       └── route.ts             # POST endpoint to initiate a streaming chat session
│   │   ├── conversations/               # API routes for conversation history
│   │   │   ├── [conversationId]/        # Dynamic route for a specific conversation
│   │   │   │   ├── route.test.ts        # Tests for specific conversation GET/DELETE endpoints
│   │   │   │   └── route.ts             # GET and DELETE endpoints for a specific conversation
│   │   │   ├── route.test.ts            # Tests for the conversation list endpoint
│   │   │   └── route.ts                 # GET endpoint to list conversations for the current user
│   │   ├── health/                      # API routes for health checks
│   │   │   ├── ready/                   # Endpoint for the readiness probe
│   │   │   │   ├── route.test.ts        # Tests for the readiness probe endpoint
│   │   │   │   └── route.ts             # GET endpoint to check service readiness
│   │   │   ├── route.test.ts            # Tests for the liveness probe endpoint
│   │   │   └── route.ts                 # GET endpoint to check service liveness (health)
│   │   └── tools/                       # API routes for tools
│   │       └── route.ts                 # GET endpoint to list available tools
│   ├── layout.tsx                       # Root layout for the entire application
│   └── providers.tsx                    # Client-side providers (e.g., React Query)
├── components/                          # Reusable UI components
│   ├── auth/                            # Authentication-related components
│   │   ├── LoginForm.tsx              # Login form component using a server action
│   │   ├── LogoutButton.tsx           # Button component to trigger logout
│   │   └── SilentRefresh.tsx          # Component to handle silent auth token refreshing
│   └── ui/                              # General-purpose UI components, likely from shadcn/ui
├── eslint.config.mjs                    # ESLint configuration file
├── features/                            # High-level components that orchestrate product features
│   ├── account/                         # Components for the account management feature
│   │   ├── ProfilePanel.tsx           # UI panel for user profile information
│   │   ├── SecurityPanel.tsx          # UI panel for security settings
│   │   ├── ServiceAccountsPanel.tsx   # UI panel for managing service accounts
│   │   ├── SessionsPanel.tsx          # UI panel for managing user sessions
│   │   └── index.ts                   # Exports all account feature components
│   ├── agents/                          # Components for the agents feature
│   │   ├── AgentsOverview.tsx         # Main component for the agents overview page
│   │   └── index.ts                   # Exports agents feature components
│   ├── billing/                         # Components for the billing feature
│   │   ├── BillingOverview.tsx        # Main component for the billing overview page
│   │   ├── PlanManagement.tsx         # Component for managing subscription plans
│   │   └── index.ts                   # Exports billing feature components
│   ├── chat/                            # Components for the main chat workspace feature
│   │   ├── ChatWorkspace.tsx          # Main orchestrator component for the chat UI
│   │   ├── components/                # Sub-components used within the chat workspace
│   │   │   ├── AgentSwitcher.tsx       # Component for selecting the active agent
│   │   │   ├── BillingEventsPanel.tsx  # Panel to display real-time billing events
│   │   │   ├── ChatInterface.tsx       # The core chat message and input interface
│   │   │   ├── ConversationSidebar.tsx # Sidebar for listing and managing conversations
│   │   │   ├── ToolMetadataPanel.tsx   # Panel to display available tools for the agent
│   │   │   └── __tests__/              # Tests for chat components
│   │   │       └── BillingEventsPanel.test.tsx # Test for the BillingEventsPanel component
│   │   └── index.ts                     # Exports chat feature components
│   ├── conversations/                   # Components for the conversation history feature
│   │   ├── ConversationsHub.tsx       # Main component for viewing conversation history
│   │   └── index.ts                   # Exports conversation feature components
│   ├── dashboard/                       # Components for the main application dashboard
│   │   ├── DashboardOverview.tsx      # Main orchestrator for the dashboard view
│   │   ├── components/                # Sub-components used within the dashboard
│   │   │   ├── BillingPreview.tsx      # A small preview of billing status
│   │   │   ├── KpiGrid.tsx             # A grid of key performance indicators
│   │   │   ├── QuickActions.tsx        # A set of quick action links
│   │   │   └── RecentConversations.tsx # A list of recent conversations
│   │   ├── constants.ts                 # Constants used in the dashboard feature
│   │   ├── hooks/                       # Hooks specific to the dashboard feature
│   │   │   └── useDashboardData.tsx    # Hook to fetch and aggregate all data for the dashboard
│   │   ├── index.ts                     # Exports dashboard feature components
│   │   └── types.ts                     # TypeScript types for the dashboard feature
│   ├── settings/                        # Components for the settings feature
│   │   ├── TenantSettingsPanel.tsx    # UI panel for tenant-specific settings
│   │   └── index.ts                   # Exports settings feature components
│   └── tools/                           # Components for the tools feature
│       ├── ToolsCatalog.tsx           # Main component for the tool catalog page
│       └── index.ts                   # Exports tools feature components
├── hooks/                               # DEPRECATED: Custom React hooks (logic moved to lib/queries)
│   ├── useBillingStream.ts              # (Old) Hook to subscribe to real-time billing events
│   └── useSilentRefresh.ts              # (Old) Hook for silent authentication token refresh
├── lib/                                 # Core application logic, utilities, and API helpers
│   ├── api/                             # Client-side logic for making API requests to internal routes
│   │   ├── __tests__/                   # Tests for API layer helpers
│   │   │   └── chat.test.ts             # Tests for the chat API client functions
│   │   ├── agents.ts                    # Functions for fetching agent data
│   │   ├── billing.ts                   # Function to connect to the billing SSE stream
│   │   ├── billingPlans.ts              # Function for fetching billing plans
│   │   ├── chat.ts                      # Functions for sending/streaming chat messages
│   │   ├── client/                      # Auto-generated API client from OpenAPI specification
│   │   │   ├── client/                  # Core client generation files
│   │   │   │   ├── client.gen.ts       # Generated core HTTP client logic
│   │   │   │   ├── index.ts            # Exports for the core client logic
│   │   │   │   ├── types.gen.ts        # Generated core client type definitions
│   │   │   │   └── utils.gen.ts        # Generated utilities for the core client
│   │   │   ├── client.gen.ts            # Generated client configuration
│   │   │   ├── core/                    # Core utilities for the generated client
│   │   │   │   ├── auth.gen.ts         # Authentication helper for the generated client
│   │   │   │   ├── bodySerializer.gen.ts # Body serialization logic
│   │   │   │   ├── params.gen.ts       # Parameter building logic
│   │   │   │   ├── pathSerializer.gen.ts # Path serialization logic
│   │   │   │   ├── queryKeySerializer.gen.ts # Query key serialization for caching
│   │   │   │   ├── serverSentEvents.gen.ts # SSE client logic
│   │   │   │   ├── types.gen.ts        # Core generated types
│   │   │   │   └── utils.gen.ts        # Core generated utilities
│   │   │   ├── index.ts                 # Main export for the generated client SDK and types
│   │   │   ├── sdk.gen.ts               # Generated SDK functions for each API endpoint
│   │   │   └── types.gen.ts             # Generated TypeScript types for API requests and responses
│   │   ├── config.ts                    # Exports the auto-generated API client instance
│   │   ├── conversations.ts             # Functions for fetching conversation data
│   │   ├── session.ts                   # Functions for managing the client-side session state
│   │   └── tools.ts                     # Function for fetching tool data
│   ├── auth/                            # Authentication logic (client and server)
│   │   ├── clientMeta.ts                # Client-side helper to read session metadata from cookies
│   │   ├── cookies.ts                   # Server-side helpers for managing authentication cookies
│   │   └── session.ts                   # Server-side session management (login, refresh, destroy)
│   ├── chat/                            # Core chat logic and hooks
│   │   ├── __tests__/                   # Tests for the chat controller hook
│   │   │   ├── testUtils.tsx            # Test utilities for chat feature tests
│   │   │   ├── useChatController.integration.test.tsx # Integration tests for the chat controller hook
│   │   │   └── useChatController.test.tsx # Unit tests for the chat controller hook
│   │   ├── types.ts                     # TypeScript types for the chat feature
│   │   └── useChatController.ts         # The primary hook managing chat state and interactions
│   ├── config.ts                        # Global application configuration constants
│   ├── queries/                         # TanStack Query hooks for data fetching
│   │   ├── agents.ts                    # TanStack Query hooks for agent data
│   │   ├── billing.ts                   # Custom hook for the real-time billing event stream
│   │   ├── billingPlans.ts              # TanStack Query hook for billing plans
│   │   ├── billingSubscriptions.ts      # TanStack Query hooks for managing subscriptions
│   │   ├── chat.ts                      # TanStack Query mutation for sending chat messages
│   │   ├── conversations.ts             # TanStack Query hook for managing conversation lists
│   │   ├── keys.ts                      # Centralized query keys for TanStack Query
│   │   ├── session.ts                   # Custom hook for silent session token refresh
│   │   └── tools.ts                     # TanStack Query hook for tool data
│   ├── server/                          # Server-only logic and helpers
│   │   ├── apiClient.ts                 # Helper to create an authenticated backend API client on the server
│   │   ├── services/                    # Service layer wrapping the generated API client for server use
│   │   │   ├── agents.ts               # Server-side service for agent-related operations
│   │   │   ├── auth/                   # Server-side services for authentication
│   │   │   │   ├── email.ts            # Service for email verification logic
│   │   │   │   ├── passwords.ts        # Service for password management logic
│   │   │   │   ├── serviceAccounts.ts  # Service for service account logic
│   │   │   │   ├── sessions.ts         # Service for session management logic
│   │   │   │   └── signup.ts           # Service for user registration logic
│   │   │   ├── auth.ts                  # Service for core authentication operations
│   │   │   ├── billing.ts               # Service for billing operations
│   │   │   ├── chat.ts                  # Service for chat operations
│   │   │   ├── conversations.ts         # Service for conversation history operations
│   │   │   ├── health.ts                # Service for health check operations
│   │   │   └── tools.ts                 # Service for tool-related operations
│   │   └── streaming/                   # Helpers for server-side streaming
│   │       └── chat.ts                  # Server-side helper to stream chat responses from the backend
│   ├── types/                           # Shared application-level type definitions
│   │   ├── auth.ts                      # Types related to authentication and sessions
│   │   └── billing.ts                   # Types related to billing subscriptions and payloads
│   ├── utils/                           # General utility functions
│   │   └── time.ts                      # Time and date formatting utilities
│   └── utils.ts                         # `cn` utility for merging Tailwind CSS classes
├── middleware.ts                        # Next.js middleware for authentication and routing protection
├── next.config.ts                       # Next.js configuration file
├── openapi-ts.config.ts                 # Configuration for the OpenAPI TypeScript client generator
├── playwright.config.ts                 # Configuration file for Playwright end-to-end tests
├── pnpm-lock.yaml                       # PNPM lockfile for managing dependencies
├── postcss.config.mjs                   # PostCSS configuration for CSS processing
├── public/                              # Directory for static assets like images and fonts
├── tailwind.config.ts                   # Tailwind CSS configuration file
├── tests/                               # End-to-end tests directory
│   └── auth-smoke.spec.ts               # A Playwright smoke test for the authentication flow
├── types/                               # Global TypeScript type definitions
│   ├── agents.ts                        # Types for AI agents
│   ├── billing.ts                       # Types for billing, plans, and events
│   ├── conversations.ts                 # Types for conversations and messages
│   ├── session.ts                       # Types for user sessions
│   └── tools.ts                         # Types for agent tools
├── vitest.config.ts                     # Vitest (unit/integration test runner) configuration
└── vitest.setup.ts                      # Setup file for Vitest tests (e.g., importing jest-dom)