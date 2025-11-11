.
├── app/                        # Next.js app directory containing all routes and layouts
│   ├── (app)/                  # Route group for authenticated application pages
│   │   ├── (workspace)/        # Route group for multi-column workspace layouts (e.g., chat)
│   │   │   ├── chat/           # Chat workspace route
│   │   │   │   ├── actions.ts  # Server Actions for chat streaming and listing conversations
│   │   │   │   └── page.tsx    # Page component for the main chat interface
│   │   │   ├── layout.tsx      # Layout for workspace pages providing a flex container
│   │   ├── account/            # Account management pages
│   │   │   └── page.tsx        # Account overview page with tabbed navigation
│   │   ├── agents/             # Agent management pages
│   │   │   └── page.tsx        # Page to display the agent catalog
│   │   ├── billing/            # Billing and subscription pages
│   │   │   ├── page.tsx        # Main billing overview page
│   │   │   └── plans/          # Page for managing billing plans
│   │   │       └── page.tsx    # Renders the plan management interface
│   │   ├── conversations/      # Conversation history pages
│   │   │   └── page.tsx        # Page to display the conversation hub/archive
│   │   ├── dashboard/          # Main dashboard for authenticated users
│   │   │   └── page.tsx        # The primary dashboard page component
│   │   ├── layout.tsx          # Main application layout with sidebar navigation for authenticated users
│   │   ├── page.tsx            # Root page for the authenticated app, redirects to /dashboard
│   │   ├── settings/           # Application settings routes
│   │   │   └── tenant/         # Tenant-specific settings
│   │   │       └── page.tsx    # Page for managing tenant settings
│   │   └── tools/              # Tool management pages
│   │       └── page.tsx        # Page to display the tool catalog
│   ├── (auth)/                 # Route group for authentication pages (login, register, etc.)
│   │   ├── _components/        # Private components for the auth route group
│   │   │   └── AuthCard.tsx    # Reusable card component for authentication forms
│   │   ├── email/              # Routes for email-related actions
│   │   │   └── verify/         # Email verification route
│   │   │       ├── VerifyEmailClient.tsx # Client component handling email verification logic
│   │   │       └── page.tsx    # Page for email verification, reads token from URL
│   │   ├── error.tsx           # Error boundary for the authentication route group
│   │   ├── layout.tsx          # Layout for all authentication pages, providing a centered card UI
│   │   ├── loading.tsx         # Loading UI for authentication routes
│   │   ├── login/              # Login route
│   │   │   └── page.tsx        # The user login page
│   │   ├── password/           # Routes for password management
│   │   │   ├── forgot/         # "Forgot password" route
│   │   │   │   └── page.tsx    # Page for requesting a password reset link
│   │   │   └── reset/          # "Reset password" route
│   │   │       └── page.tsx    # Page for resetting password using a token
│   │   └── register/           # User registration route
│   │       └── page.tsx        # The user and tenant registration page
│   ├── (marketing)/            # Route group for public-facing marketing pages
│   │   ├── _components/        # Private components for the marketing route group
│   │   │   ├── marketing-footer.tsx # Footer component for marketing pages
│   │   │   ├── marketing-header.tsx # Header component with navigation for marketing pages
│   │   │   └── nav-links.ts    # Defines navigation links for marketing pages
│   │   ├── features/           # Marketing page for product features
│   │   │   └── page.tsx        # The "Features" page content
│   │   ├── layout.tsx          # Layout for marketing pages, including header and footer
│   │   ├── page.tsx            # The main marketing landing page
│   │   └── pricing/            # Marketing page for pricing plans
│   │       └── page.tsx        # The "Pricing" page content
│   ├── actions/                # Server Actions for client components
│   │   ├── auth/               # Authentication-related Server Actions
│   │   │   ├── email.ts      # Server Actions for sending and verifying emails
│   │   │   ├── passwords.ts  # Server Actions for password reset and change flows
│   │   │   ├── sessions.ts   # Server Actions for listing and revoking user sessions
│   │   │   └── signup.ts     # Server Action for user and tenant registration
│   │   └── auth.ts             # Main Server Actions for login, logout, and silent refresh
│   ├── api/                    # API routes (Next.js Route Handlers)
│   │   ├── agents/             # API routes related to agents
│   │   │   ├── [agentName]/    # Dynamic routes for a specific agent
│   │   │   │   └── status/     # Agent status routes
│   │   │   │       ├── route.test.ts # Tests for the agent status API route
│   │   │   │       └── route.ts      # API route to get status of a specific agent
│   │   │   ├── route.test.ts   # Tests for the list agents API route
│   │   │   └── route.ts        # API route to list available agents
│   │   ├── auth/               # API routes related to authentication
│   │   │   ├── email/          # Email verification routes
│   │   │   │   ├── send/       # Route to send a verification email
│   │   │   │   │   ├── route.test.ts # Tests for sending verification email
│   │   │   │   │   └── route.ts      # API route to trigger sending a verification email
│   │   │   │   └── verify/     # Route to verify an email token
│   │   │   │       ├── route.test.ts # Tests for verifying an email token
│   │   │   │       └── route.ts      # API route to handle email verification
│   │   │   ├── logout/         # Logout routes
│   │   │   │   ├── all/        # Route to log out from all sessions
│   │   │   │   │   ├── route.test.ts # Tests for logging out of all sessions
│   │   │   │   │   └── route.ts      # API route to log out from all sessions
│   │   │   │   ├── route.test.ts # Tests for logging out of a single session
│   │   │   │   └── route.ts    # API route to log out of the current session
│   │   │   ├── password/       # Password management routes
│   │   │   │   ├── change/     # Route to change the current password
│   │   │   │   │   ├── route.test.ts # Tests for the password change route
│   │   │   │   │   └── route.ts      # API route to change the current user's password
│   │   │   │   ├── confirm/    # Route to confirm a password reset
│   │   │   │   │   ├── route.test.ts # Tests for confirming password reset
│   │   │   │   │   └── route.ts      # API route to confirm a password reset with a token
│   │   │   │   ├── forgot/     # Route to request a password reset
│   │   │   │   │   ├── route.test.ts # Tests for the forgot password route
│   │   │   │   │   └── route.ts      # API route to request a password reset email
│   │   │   │   └── reset/      # Route for admin to reset a user's password
│   │   │   │       ├── route.test.ts # Tests for admin password reset
│   │   │   │       └── route.ts      # API route for an admin to reset a user password
│   │   │   ├── refresh/        # Route to refresh the session
│   │   │   │   └── route.ts    # API route to get a new access token using a refresh token
│   │   │   ├── register/       # User registration route
│   │   │   │   ├── route.test.ts # Tests for the registration route
│   │   │   │   └── route.ts    # API route for user and tenant registration
│   │   │   ├── session/        # Current session information route
│   │   │   │   └── route.ts    # API route to get info about the current user's session
│   │   │   └── sessions/       # Session management routes
│   │   │       ├── [sessionId]/ # Dynamic route for a specific session
│   │   │       │   ├── route.test.ts # Tests for revoking a specific session
│   │   │       │   └── route.ts      # API route to revoke a specific user session
│   │   │       ├── route.test.ts # Tests for listing user sessions
│   │   │       └── route.ts    # API route to list all sessions for the current user
│   │   ├── billing/            # API routes related to billing
│   │   │   ├── plans/          # Billing plans route
│   │   │   │   └── route.ts    # API route to list available billing plans
│   │   │   ├── stream/         # Billing event stream route
│   │   │   │   └── route.ts    # Server-Sent Events route for live billing events
│   │   │   └── tenants/        # Tenant-specific billing routes
│   │   │       └── [tenantId]/ # Dynamic route for a specific tenant
│   │   │           ├── subscription/ # Subscription management routes
│   │   │           │   ├── cancel/     # Route to cancel a subscription
│   │   │           │   │   ├── route.test.ts # Tests for subscription cancellation
│   │   │           │   │   └── route.ts      # API route to cancel a tenant's subscription
│   │   │           │   ├── route.test.ts # Tests for subscription management (GET, POST, PATCH)
│   │   │           │   └── route.ts    # API routes for managing a tenant's subscription
│   │   │           └── usage/      # Usage recording route
│   │   │               ├── route.test.ts # Tests for recording usage
│   │   │               └── route.ts    # API route to record metered usage for a tenant
│   │   ├── chat/               # API routes related to chat
│   │   │   ├── route.test.ts   # Tests for the non-streaming chat API
│   │   │   ├── route.ts        # API route for non-streaming chat messages
│   │   │   └── stream/         # Streaming chat route
│   │   │       └── route.ts    # Server-Sent Events route for streaming chat responses
│   │   ├── conversations/      # API routes related to conversations
│   │   │   ├── [conversationId]/ # Dynamic route for a specific conversation
│   │   │   │   ├── route.test.ts # Tests for GET/DELETE a specific conversation
│   │   │   │   └── route.ts    # API routes to get or delete a specific conversation
│   │   │   ├── route.test.ts   # Tests for listing conversations
│   │   │   └── route.ts        # API route to list all conversations for a user
│   │   ├── health/             # Health check routes
│   │   │   ├── ready/          # Readiness probe route
│   │   │   │   ├── route.test.ts # Tests for the readiness probe
│   │   │   │   └── route.ts    # API route for the readiness probe
│   │   │   ├── route.test.ts   # Tests for the liveness probe
│   │   │   └── route.ts        # API route for the liveness probe
│   │   └── tools/              # API routes related to tools
│   │       └── route.ts        # API route to list available tools
│   ├── layout.tsx              # Root layout for the entire application
│   └── providers.tsx           # Client-side providers (QueryClient, ThemeProvider)
├── components/                 # Reusable UI components
│   ├── auth/                   # Authentication-specific components
│   │   ├── ForgotPasswordForm.tsx # Form for requesting a password reset
│   │   ├── LoginForm.tsx       # The main login form component
│   │   ├── LogoutButton.tsx    # A simple button to log out the user
│   │   ├── RegisterForm.tsx    # Form for new user and tenant registration
│   │   ├── ResetPasswordForm.tsx # Form to set a new password using a reset token
│   │   └── SilentRefresh.tsx   # Client component to trigger silent token refresh
│   └── ui/                     # General-purpose UI components (from shadcn/ui and custom)
├── eslint.config.mjs           # ESLint configuration file
├── features/                   # High-level feature components (feature-sliced design)
│   ├── account/                # Components for the account management feature
│   │   ├── AccountOverview.tsx # Main component for the account page, managing tabs
│   │   ├── ProfilePanel.tsx    # Panel for viewing and editing user profile information
│   │   ├── SecurityPanel.tsx   # Panel for managing security settings like passwords
│   │   ├── SessionsPanel.tsx   # Panel for viewing and managing active user sessions
│   │   └── index.ts            # Barrel file exporting account feature components
│   ├── agents/                 # Components for the agent management feature
│   │   ├── AgentsOverview.tsx  # Main component displaying a catalog of available agents
│   │   └── index.ts            # Barrel file exporting the agents feature component
│   ├── billing/                # Components for the billing feature
│   │   ├── BillingOverview.tsx # Main dashboard for billing information
│   │   ├── PlanManagement.tsx  # Component for managing subscription plans
│   │   └── index.ts            # Barrel file exporting billing feature components
│   ├── chat/                   # Components for the main chat workspace feature
│   │   ├── ChatWorkspace.tsx   # Orchestrator component for the entire chat UI
│   │   ├── components/         # Sub-components for the chat feature
│   │   │   ├── AgentSwitcher.tsx # Dropdown to select the active AI agent
│   │   │   ├── BillingEventsPanel.tsx # Panel to display live billing events from the SSE stream
│   │   │   ├── ChatInterface.tsx # The core chat message display and input area
│   │   │   ├── ConversationSidebar.tsx # Sidebar for listing and managing conversations
│   │   │   ├── ToolMetadataPanel.tsx # Panel showing tools available to the selected agent
│   │   │   └── __tests__/      # Tests for chat components
│   │   │       └── BillingEventsPanel.test.tsx # Unit test for the BillingEventsPanel
│   │   └── index.ts            # Barrel file exporting chat feature components
│   ├── conversations/          # Components for the conversation history feature
│   │   ├── ConversationDetailDrawer.tsx # A slide-out drawer showing details of a conversation
│   │   ├── ConversationsHub.tsx # The main view for browsing and searching conversations
│   │   └── index.ts            # Barrel file exporting the conversations feature component
│   ├── dashboard/              # Components for the main dashboard feature
│   │   ├── DashboardOverview.tsx # The main orchestrator component for the dashboard
│   │   ├── components/         # Sub-components for the dashboard
│   │   │   ├── BillingPreview.tsx # Card showing a summary of billing status
│   │   │   ├── KpiGrid.tsx     # A grid of key performance indicator cards
│   │   │   ├── QuickActions.tsx # Cards for common user actions
│   │   │   └── RecentConversations.tsx # A list of recent conversations
│   │   ├── constants.ts        # Constants used within the dashboard feature
│   │   ├── hooks/              # Hooks specific to the dashboard feature
│   │   │   └── useDashboardData.tsx # Hook to fetch and aggregate all data for the dashboard
│   │   ├── index.ts            # Barrel file exporting the dashboard feature component
│   │   └── types.ts            # Type definitions for the dashboard feature
│   ├── settings/               # Components for the settings feature
│   │   ├── TenantSettingsPanel.tsx # Panel for managing tenant-level settings
│   │   └── index.ts            # Barrel file exporting the settings feature component
│   └── tools/                  # Components for the tool catalog feature
│       ├── ToolsCatalog.tsx    # The main component for displaying available tools
│       └── index.ts            # Barrel file exporting the tools feature component
├── hooks/                      # Global, reusable React hooks
│   ├── useAuthForm.ts          # A generic hook for handling authentication form logic
│   ├── useBillingStream.ts     # Hook to connect to and manage the billing SSE stream
│   └── useSilentRefresh.ts     # Hook to handle silent session token refreshing in the background
├── lib/                        # Core application logic, utilities, and API interactions
│   ├── api/                    # Functions for interacting with API routes and the backend
│   │   ├── __tests__/          # Tests for API layer functions
│   │   │   └── chat.test.ts    # Unit tests for chat API client functions
│   │   ├── account.ts          # API client functions for fetching account and tenant data
│   │   ├── accountSecurity.ts  # API client functions for security-related account actions
│   │   ├── accountSessions.ts  # API client functions for managing user sessions
│   │   ├── agents.ts           # API client functions for fetching agent data
│   │   ├── billing.ts          # API client function for connecting to the billing SSE stream
│   │   ├── billingPlans.ts     # API client function for fetching billing plans
│   │   ├── chat.ts             # API client functions for sending and streaming chat messages
│   │   ├── client/             # Auto-generated API client from OpenAPI spec
│   │   │   ├── client/         # Core client logic for the generated client
│   │   │   │   ├── client.gen.ts # The main generated client creation logic
│   │   │   │   ├── index.ts    # Barrel file exporting core client utilities
│   │   │   │   ├── types.gen.ts # Generated type definitions for the client's internal structure
│   │   │   │   └── utils.gen.ts # Generated utility functions for the client
│   │   │   ├── client.gen.ts   # Initializes and exports the generated API client instance
│   │   │   ├── core/           # Core utilities for the generated client
│   │   │   │   ├── auth.gen.ts # Auth helpers for the generated client
│   │   │   │   ├── bodySerializer.gen.ts # Body serialization logic
│   │   │   │   ├── params.gen.ts # Parameter building logic
│   │   │   │   ├── pathSerializer.gen.ts # Path serialization logic
│   │   │   │   ├── queryKeySerializer.gen.ts # Utilities for serializing values for query keys
│   │   │   │   ├── serverSentEvents.gen.ts # Logic for handling Server-Sent Events
│   │   │   │   ├── types.gen.ts # Core type definitions for the client
│   │   │   │   └── utils.gen.ts # Core utilities for URL building, etc.
│   │   │   ├── index.ts        # Barrel file exporting generated types and SDK functions
│   │   │   ├── sdk.gen.ts      # Generated SDK functions for each API endpoint
│   │   │   └── types.gen.ts    # Generated TypeScript types from the OpenAPI schema
│   │   ├── config.ts           # Exports the generated API client instance
│   │   ├── conversations.ts    # API client functions for fetching and managing conversations
│   │   ├── session.ts          # API client functions for fetching and refreshing user sessions
│   │   └── tools.ts            # API client function for fetching available tools
│   ├── auth/                   # Authentication-related logic
│   │   ├── clientMeta.ts       # Client-side utility to read session metadata from a cookie
│   │   ├── cookies.ts          # Server-side utilities for managing session cookies
│   │   └── session.ts          # Server-side logic for session management
│   ├── chat/                   # Client-side chat logic and hooks
│   │   ├── __tests__/          # Tests for chat hooks and utilities
│   │   │   ├── testUtils.tsx   # Test utilities, mocks, and wrappers for chat tests
│   │   │   ├── useChatController.integration.test.tsx # Integration test for the main chat hook
│   │   │   └── useChatController.test.tsx # Unit tests for the main chat hook
│   │   ├── types.ts            # TypeScript types for chat functionality
│   │   └── useChatController.ts # The core hook managing all client-side chat state and logic
│   ├── config.ts               # Global application configuration constants
│   ├── queries/                # TanStack Query hooks and keys
│   │   ├── account.ts          # TanStack Query hooks for account profile data
│   │   ├── accountSecurity.ts  # TanStack Query mutation hook for changing a password
│   │   ├── accountSessions.ts  # TanStack Query hooks for managing user sessions
│   │   ├── agents.ts           # TanStack Query hooks for fetching agent data
│   │   ├── billing.ts          # Custom hook for the billing SSE stream
│   │   ├── billingPlans.ts     # TanStack Query hook for fetching billing plans
│   │   ├── billingSubscriptions.ts # TanStack Query hooks for managing tenant subscriptions
│   │   ├── chat.ts             # TanStack Query mutation hook for sending chat messages
│   │   ├── conversations.ts    # TanStack Query hooks for managing conversations
│   │   ├── keys.ts             # Centralized definitions for all TanStack Query keys
│   │   ├── session.ts          # Custom hook for handling silent session refresh
│   │   └── tools.ts            # TanStack Query hook for fetching tools
│   ├── server/                 # Server-side only logic
│   │   ├── apiClient.ts        # Utilities for creating an authenticated API client instance on the server
│   │   ├── services/           # Service layer wrapping the generated API SDK
│   │   │   ├── agents.ts       # Service functions for agent-related operations
│   │   │   ├── auth/           # Authentication-related service functions
│   │   │   │   ├── email.ts    # Service functions for email verification
│   │   │   │   ├── passwords.ts # Service functions for password management
│   │   │   │   ├── sessions.ts # Service functions for session management
│   │   │   │   └── signup.ts   # Service function for user/tenant registration
│   │   │   ├── auth.ts         # Top-level auth services (login, refresh, get profile)
│   │   │   ├── billing.ts      # Service functions for billing operations
│   │   │   ├── chat.ts         # Service functions for chat operations
│   │   │   ├── conversations.ts # Service functions for conversation management
│   │   │   ├── health.ts       # Service functions for health checks
│   │   │   └── tools.ts        # Service function for listing tools
│   │   └── streaming/          # Server-side streaming helpers
│   │       └── chat.ts         # Server-side helper to stream chat responses from the backend
│   ├── types/                  # Shared TypeScript type definitions (might be legacy)
│   │   ├── auth.ts             # Types for authentication tokens and sessions
│   │   └── billing.ts          # Types related to billing subscriptions and usage
│   ├── utils/                  # General utility functions
│   │   └── time.ts             # Utility functions for formatting dates and times
│   └── utils.ts                # Main utility file, includes `cn` for Tailwind classes
├── middleware.ts               # Next.js middleware for authentication and route protection
├── next.config.ts              # Next.js configuration file
├── openapi-ts.config.ts        # Configuration for generating the API client from an OpenAPI spec
├── playwright.config.ts        # Configuration for Playwright end-to-end tests
├── pnpm-lock.yaml              # PNPM lockfile for dependency management
├── postcss.config.mjs          # PostCSS configuration file
├── public/                     # Directory for static assets (empty)
├── tailwind.config.ts          # Tailwind CSS configuration file
├── tests/                      # End-to-end tests
│   └── auth-smoke.spec.ts      # A Playwright smoke test for the login-chat-logout flow
├── types/                      # Global or domain-specific TypeScript type definitions
│   ├── account.ts              # Types related to user accounts and profiles
│   ├── agents.ts               # Types related to AI agents
│   ├── billing.ts              # Types related to billing events and plans
│   ├── conversations.ts        # Types related to conversations
│   ├── session.ts              # Types related to user sessions
│   └── tools.ts                # Types related to agent tools
├── vitest.config.ts            # Vitest configuration for unit and integration tests
└── vitest.setup.ts             # Setup file for Vitest tests, extends jest-dom matchers