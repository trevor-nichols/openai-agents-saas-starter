```
.
├── app/                                 # Next.js app directory containing all routes and UI
│   ├── (app)/                           # Route group for the authenticated main application
│   │   ├── (workspace)/                 # Route group for multi-column workspace layouts like chat
│   │   │   ├── chat/                    # Contains the main chat interface feature
│   │   │   │   ├── actions.ts           # Server Actions for chat streaming and fetching conversations
│   │   │   │   └── page.tsx             # Page component for the chat workspace
│   │   │   └── layout.tsx               # Layout for workspace pages providing shared structure
│   │   ├── account/                     # Route group for user account management pages
│   │   │   ├── profile/                 # User profile page and settings
│   │   │   │   └── page.tsx             # Page component for the user profile
│   │   │   ├── security/                # Security settings page
│   │   │   │   └── page.tsx             # Page component for security settings
│   │   │   ├── service-accounts/        # Page for managing API service accounts
│   │   │   │   └── page.tsx             # Page component for service account management
│   │   │   └── sessions/                # Page for managing active user sessions
│   │   │       └── page.tsx             # Page component for session management
│   │   ├── agents/                      # Page for viewing and managing AI agents
│   │   │   └── page.tsx                 # Page component for the agents overview
│   │   ├── billing/                     # Route group for billing and subscription management
│   │   │   ├── page.tsx                 # Page component for the main billing overview
│   │   │   └── plans/                   # Page for viewing and changing subscription plans
│   │   │       └── page.tsx             # Page component for plan management
│   │   ├── conversations/               # Page for viewing past conversation transcripts
│   │   │   └── page.tsx                 # Page component for the conversations hub
│   │   ├── dashboard/                   # The main dashboard page for authenticated users
│   │   │   └── page.tsx                 # Page component for the dashboard overview
│   │   ├── layout.tsx                   # Main layout for the authenticated app (sidebar, header)
│   │   ├── page.tsx                     # Root page for the authenticated app, redirects to dashboard
│   │   ├── settings/                    # Route group for application settings
│   │   │   └── tenant/                  # Tenant-specific settings
│   │   │       └── page.tsx             # Page component for tenant settings
│   │   └── tools/                       # Page for browsing available agent tools
│   │       └── page.tsx                 # Page component for the tools catalog
│   ├── (auth)/                          # Route group for authentication pages (login, register)
│   │   ├── email/                       # Routes for email-related actions
│   │   │   └── verify/                  # Email verification route
│   │   │       └── page.tsx             # Page component for email verification
│   │   ├── layout.tsx                   # Layout for authentication pages with a centered card UI
│   │   ├── login/                       # Login route
│   │   │   └── page.tsx                 # Page component for the user login form
│   │   ├── password/                    # Routes for password management
│   │   │   ├── forgot/                  # Forgot password route
│   │   │   │   └── page.tsx             # Page component to request a password reset
│   │   │   └── reset/                   # Reset password route
│   │   │       └── page.tsx             # Page component to reset password with a token
│   │   └── register/                    # User registration route
│   │       └── page.tsx                 # Page component for user and tenant registration
│   ├── (marketing)/                     # Route group for public-facing marketing pages
│   │   ├── _components/                 # Private components for the marketing layout
│   │   │   ├── marketing-footer.tsx     # Footer component for marketing pages
│   │   │   ├── marketing-header.tsx     # Header component for marketing pages
│   │   │   └── nav-links.ts             # Navigation link definitions for marketing pages
│   │   ├── features/                    # Marketing page describing product features
│   │   │   └── page.tsx                 # Page component for the features page
│   │   ├── layout.tsx                   # Layout for marketing pages, including header and footer
│   │   ├── page.tsx                     # The main public landing page
│   │   └── pricing/                     # Marketing page for subscription plans and pricing
│   │       └── page.tsx                 # Page component for the pricing page
│   ├── actions/                         # Server Actions used by client components
│   │   ├── auth/                        # Authentication-related Server Actions
│   │   │   ├── email.ts                 # Server Actions for email verification
│   │   │   ├── passwords.ts             # Server Actions for password management
│   │   │   ├── sessions.ts              # Server Actions for session management
│   │   │   └── signup.ts                # Server Action for user/tenant registration
│   │   └── auth.ts                      # Core authentication Server Actions (login, logout)
│   ├── api/                             # Next.js API Routes (Route Handlers)
│   │   ├── agents/                      # API routes for agent management
│   │   │   ├── [agentName]/             # Dynamic route for a specific agent
│   │   │   │   └── status/              # Agent status endpoint
│   │   │   │       ├── route.test.ts    # Tests for the agent status API route
│   │   │   │       └── route.ts         # API route handler to get a specific agent's status
│   │   │   ├── route.test.ts            # Tests for the list agents API route
│   │   │   └── route.ts                 # API route handler to list available agents
│   │   ├── auth/                        # API routes for authentication and session management
│   │   │   ├── email/                   # API routes for email actions
│   │   │   │   ├── send/                # API route to send verification emails
│   │   │   │   │   ├── route.test.ts    # Tests for the send verification email API route
│   │   │   │   │   └── route.ts         # API route handler to send a verification email
│   │   │   │   └── verify/              # API route to verify an email token
│   │   │   │       ├── route.test.ts    # Tests for the verify email API route
│   │   │   │       └── route.ts         # API route handler to verify an email with a token
│   │   │   ├── logout/                  # API routes for user logout
│   │   │   │   ├── all/                 # API route to log out from all sessions
│   │   │   │   │   ├── route.test.ts    # Tests for the logout all sessions API route
│   │   │   │   │   └── route.ts         # API route handler to log out from all sessions
│   │   │   │   ├── route.test.ts        # Tests for the single session logout API route
│   │   │   │   └── route.ts             # API route handler to log out a single session
│   │   │   ├── password/                # API routes for password management
│   │   │   │   ├── change/              # API route for changing a password
│   │   │   │   │   ├── route.test.ts    # Tests for the password change API route
│   │   │   │   │   └── route.ts         # API route handler for password changes
│   │   │   │   ├── confirm/             # API route to confirm a password reset
│   │   │   │   │   ├── route.test.ts    # Tests for the password reset confirmation API route
│   │   │   │   │   └── route.ts         # API route handler to confirm a password reset
│   │   │   │   ├── forgot/              # API route to request a password reset
│   │   │   │   │   ├── route.test.ts    # Tests for the forgot password API route
│   │   │   │   │   └── route.ts         # API route handler to request a password reset
│   │   │   │   └── reset/               # API route for admin-initiated password resets
│   │   │   │       ├── route.test.ts    # Tests for the admin password reset API route
│   │   │   │       └── route.ts         # API route handler for admin password resets
│   │   │   ├── refresh/                 # API route to refresh an access token
│   │   │   │   └── route.ts             # API route handler to refresh a session token
│   │   │   ├── register/                # API route for user registration
│   │   │   │   ├── route.test.ts        # Tests for the user registration API route
│   │   │   │   └── route.ts             # API route handler for user registration
│   │   │   ├── service-accounts/        # API routes for service accounts
│   │   │   │   └── issue/               # API route to issue a service account token
│   │   │   │       ├── route.test.ts    # Tests for the service account token issuance API route
│   │   │   │       └── route.ts         # API route handler to issue a service account token
│   │   │   ├── session/                 # API route to get current session info
│   │   │   │   └── route.ts             # API route handler to get current session details
│   │   │   └── sessions/                # API routes for managing user sessions
│   │   │       ├── [sessionId]/         # Dynamic route for a specific session
│   │   │       │   ├── route.test.ts    # Tests for the specific session management API route
│   │   │       │   └── route.ts         # API route handler to delete a specific session
│   │   │       ├── route.test.ts        # Tests for the list sessions API route
│   │   │       └── route.ts             # API route handler to list user sessions
│   │   ├── billing/                     # API routes for billing management
│   │   │   ├── plans/                   # API route to list billing plans
│   │   │   │   └── route.ts             # API route handler to fetch billing plans
│   │   │   ├── stream/                  # API route for the billing event stream
│   │   │   │   └── route.ts             # API route handler for real-time billing events (SSE)
│   │   │   └── tenants/                 # API routes for tenant-specific billing
│   │   │       └── [tenantId]/          # Dynamic route for a specific tenant
│   │   │           ├── subscription/    # Tenant subscription management
│   │   │           │   ├── cancel/      # API route to cancel a subscription
│   │   │           │   │   ├── route.test.ts # Tests for the subscription cancellation API route
│   │   │           │   │   └── route.ts # API route handler to cancel a subscription
│   │   │           │   ├── route.test.ts # Tests for the subscription management API routes
│   │   │           │   └── route.ts     # API route handlers for GET, POST, PATCH on subscriptions
│   │   │           └── usage/           # API route to record metered usage
│   │   │               ├── route.test.ts # Tests for the usage recording API route
│   │   │               └── route.ts     # API route handler to record metered usage
│   │   ├── chat/                        # API routes for chat functionality
│   │   │   ├── route.test.ts            # Tests for the non-streaming chat API route
│   │   │   ├── route.ts                 # API route handler for non-streaming chat messages
│   │   │   └── stream/                  # API route for streaming chat responses
│   │   │       └── route.ts             # API route handler for streaming chat (SSE)
│   │   ├── conversations/               # API routes for conversation history
│   │   │   ├── [conversationId]/        # Dynamic route for a specific conversation
│   │   │   │   ├── route.test.ts        # Tests for specific conversation API routes (GET, DELETE)
│   │   │   │   └── route.ts             # API route handlers for getting or deleting a conversation
│   │   │   ├── route.test.ts            # Tests for the list conversations API route
│   │   │   └── route.ts                 # API route handler to list all conversations
│   │   ├── health/                      # API routes for health checks
│   │   │   ├── ready/                   # Readiness probe endpoint
│   │   │   │   ├── route.test.ts        # Tests for the readiness probe API route
│   │   │   │   └── route.ts             # API route handler for the readiness probe
│   │   │   ├── route.test.ts            # Tests for the liveness probe API route
│   │   │   └── route.ts                 # API route handler for the liveness probe
│   │   └── tools/                       # API routes for agent tools
│   │       └── route.ts                 # API route handler to list available tools
│   ├── layout.tsx                       # Root layout for the entire application
│   └── providers.tsx                    # Client-side context providers (React Query, Theme)
├── components/                          # Reusable UI components for the application
│   ├── auth/                            # Components specific to authentication flows
│   │   ├── LoginForm.tsx                # The user login form component
│   │   ├── LogoutButton.tsx             # A button to trigger the logout server action
│   │   └── SilentRefresh.tsx            # A client component to handle silent token refresh
│   └── ui/                              # General-purpose UI components (mostly from shadcn/ui)
├── eslint.config.mjs                    # ESLint configuration file
├── features/                            # Contains high-level feature components or "feature slices"
│   ├── account/                         # Components for the account management feature
│   │   ├── ProfilePanel.tsx             # Panel displaying user profile information
│   │   ├── SecurityPanel.tsx            # Panel for user security settings
│   │   ├── ServiceAccountsPanel.tsx     # Panel for managing service accounts
│   │   ├── SessionsPanel.tsx            # Panel for managing user sessions
│   │   └── index.ts                     # Barrel file for exporting account feature components
│   ├── agents/                          # Components for the agents feature
│   │   ├── AgentsOverview.tsx           # Main component for the agents overview page
│   │   └── index.ts                     # Barrel file for exporting agents feature components
│   ├── billing/                         # Components for the billing feature
│   │   ├── BillingOverview.tsx          # Main component for the billing overview page
│   │   ├── PlanManagement.tsx           # Component for managing subscription plans
│   │   └── index.ts                     # Barrel file for exporting billing feature components
│   ├── chat/                            # Components for the chat workspace feature
│   │   ├── ChatWorkspace.tsx            # The main orchestrator component for the chat workspace
│   │   ├── components/                  # Sub-components used within the chat workspace
│   │   │   ├── AgentSwitcher.tsx        # Component to switch between different AI agents
│   │   │   ├── BillingEventsPanel.tsx   # Panel to display live billing events during a chat
│   │   │   ├── ChatInterface.tsx        # The core chat message and input interface
│   │   │   ├── ConversationSidebar.tsx  # Sidebar for listing and managing conversations
│   │   │   ├── ToolMetadataPanel.tsx    # Panel to display metadata about available tools
│   │   │   └── __tests__/               # Tests for chat components
│   │   │       └── BillingEventsPanel.test.tsx # Test for the BillingEventsPanel component
│   │   └── index.ts                     # Barrel file for exporting chat feature components
│   ├── conversations/                   # Components for the conversations feature
│   │   ├── ConversationsHub.tsx         # Main component for browsing conversation history
│   │   └── index.ts                     # Barrel file for exporting conversations feature components
│   ├── dashboard/                       # Components for the main dashboard feature
│   │   ├── DashboardOverview.tsx        # Main orchestrator component for the dashboard
│   │   ├── components/                  # Sub-components used within the dashboard
│   │   │   ├── BillingPreview.tsx       # A small preview of the current billing status
│   │   │   ├── KpiGrid.tsx              # A grid of key performance indicators (KPIs)
│   │   │   ├── QuickActions.tsx         # A set of quick action links
│   │   │   └── RecentConversations.tsx  # A list of recent conversations
│   │   ├── constants.ts                 # Constants used within the dashboard feature
│   │   ├── hooks/                       # Hooks specific to the dashboard feature
│   │   │   └── useDashboardData.tsx     # Hook to fetch and aggregate all data for the dashboard
│   │   ├── index.ts                     # Barrel file for exporting dashboard components
│   │   └── types.ts                     # Type definitions for the dashboard feature
│   ├── settings/                        # Components for the settings feature
│   │   ├── TenantSettingsPanel.tsx      # Panel for managing tenant-specific settings
│   │   └── index.ts                     # Barrel file for exporting settings components
│   └── tools/                           # Components for the tools feature
│       ├── ToolsCatalog.tsx             # Main component for the tools catalog page
│       └── index.ts                     # Barrel file for exporting tools components
├── hooks/                               # Application-wide custom React hooks
│   ├── useBillingStream.ts              # Custom hook to manage the SSE billing stream connection
│   └── useSilentRefresh.ts              # An older implementation of the silent refresh hook
├── lib/                                 # Core application logic, utilities, and API communication
│   ├── api/                             # Client-side logic for interacting with APIs
│   │   ├── __tests__/                   # Tests for API helpers
│   │   │   └── chat.test.ts             # Tests for the chat API functions
│   │   ├── agents.ts                    # Functions for fetching agent data
│   │   ├── billing.ts                   # Functions for connecting to the billing SSE stream
│   │   ├── billingPlans.ts              # Functions for fetching billing plan data
│   │   ├── chat.ts                      # Functions for sending chat messages (streaming and non-streaming)
│   │   ├── client/                      # Auto-generated API client from @hey-api/openapi-ts
│   │   │   ├── client/                  # Core client implementation files
│   │   │   │   ├── client.gen.ts        # The main generated client logic
│   │   │   │   ├── index.ts             # Barrel file for client exports
│   │   │   │   ├── types.gen.ts         # Generated type definitions for the client
│   │   │   │   └── utils.gen.ts         # Generated utility functions for the client
│   │   │   ├── client.gen.ts            # Entry point for the generated client configuration
│   │   │   ├── core/                    # Core utilities for the generated client
│   │   │   │   ├── auth.gen.ts          # Generated authentication helpers
│   │   │   │   ├── bodySerializer.gen.ts # Generated body serialization helpers
│   │   │   │   ├── params.gen.ts        # Generated parameter handling logic
│   │   │   │   ├── pathSerializer.gen.ts # Generated path serialization helpers
│   │   │   │   ├── queryKeySerializer.gen.ts # Generated query key serialization helpers
│   │   │   │   ├── serverSentEvents.gen.ts # Generated SSE client logic
│   │   │   │   ├── types.gen.ts         # Generated core type definitions
│   │   │   │   └── utils.gen.ts         # Generated core utility functions
│   │   │   ├── index.ts                 # Barrel file for the generated client SDK
│   │   │   ├── sdk.gen.ts               # The main generated SDK with all API methods
│   │   │   └── types.gen.ts             # Generated type definitions from the OpenAPI schema
│   │   ├── config.ts                    # Configuration for the generated API client
│   │   ├── conversations.ts             # Functions for fetching and managing conversation data
│   │   ├── session.ts                   # Functions for fetching and refreshing the user session
│   │   └── tools.ts                     # Functions for fetching tool data
│   ├── auth/                            # Client- and server-side authentication helpers
│   │   ├── clientMeta.ts                # Client-side utility to read session metadata from cookies
│   │   ├── cookies.ts                   # Server-side utilities for managing auth cookies
│   │   └── session.ts                   # Server-side session management functions
│   ├── chat/                            # Client-side logic for the chat feature
│   │   ├── __tests__/                   # Tests for the chat controller hook
│   │   │   ├── testUtils.tsx            # Utility functions for chat tests
│   │   │   ├── useChatController.integration.test.tsx # Integration tests for the chat controller
│   │   │   └── useChatController.test.tsx # Unit tests for the chat controller
│   │   ├── types.ts                     # Type definitions for chat functionality
│   │   └── useChatController.ts         # The core state management hook for the chat interface
│   ├── config.ts                        # Global application configuration variables
│   ├── queries/                         # TanStack Query hooks for data fetching
│   │   ├── agents.ts                    # TanStack Query hooks for agent data
│   │   ├── billing.ts                   # TanStack Query hook for the billing stream (custom implementation)
│   │   ├── billingPlans.ts              # TanStack Query hook for billing plans
│   │   ├── billingSubscriptions.ts      # TanStack Query hooks for billing subscriptions
│   │   ├── chat.ts                      # TanStack Query mutation for sending chat messages
│   │   ├── conversations.ts             # TanStack Query hooks for conversation data
│   │   ├── keys.ts                      # Centralized query keys for TanStack Query
│   │   ├── session.ts                   # Custom hook for silent session refresh
│   │   └── tools.ts                     # TanStack Query hook for tool data
│   ├── server/                          # Server-side-only logic and helpers
│   │   ├── apiClient.ts                 # Factory function for creating an authenticated server-side API client
│   │   ├── services/                    # Service layer abstracting backend API calls
│   │   │   ├── agents.ts                # Service functions for agent-related API calls
│   │   │   ├── auth/                    # Service functions for authentication API calls
│   │   │   │   ├── email.ts             # Services for email verification APIs
│   │   │   │   ├── passwords.ts         # Services for password management APIs
│   │   │   │   ├── serviceAccounts.ts   # Services for service account APIs
│   │   │   │   ├── sessions.ts          # Services for session management APIs
│   │   │   │   └── signup.ts            # Services for registration/signup APIs
│   │   │   ├── auth.ts                  # Core authentication service functions (login, refresh)
│   │   │   ├── billing.ts               # Service functions for billing-related API calls
│   │   │   ├── chat.ts                  # Service functions for chat-related API calls
│   │   │   ├── conversations.ts         # Service functions for conversation-related API calls
│   │   │   ├── health.ts                # Service functions for health check API calls
│   │   │   └── tools.ts                 # Service functions for tool-related API calls
│   │   └── streaming/                   # Helpers for handling streaming responses on the server
│   │       └── chat.ts                  # Server-side helper to stream chat from the backend
│   ├── types/                           # Shared type definitions for the application
│   │   ├── auth.ts                      # Type definitions for authentication
│   │   └── billing.ts                   # Type definitions for billing
│   ├── utils/                           # General utility functions
│   │   └── time.ts                      # Utility functions for formatting time and dates
│   └── utils.ts                         # Utility function `cn` for combining Tailwind CSS classes
├── middleware.ts                        # Next.js middleware for route protection and authentication checks
├── next.config.ts                       # Next.js configuration file
├── openapi-ts.config.ts                 # Configuration for the OpenAPI TypeScript client generator
├── playwright.config.ts                 # Configuration for Playwright end-to-end tests
├── pnpm-lock.yaml                       # PNPM lockfile for dependency versioning
├── postcss.config.mjs                   # PostCSS configuration for tools like Tailwind CSS
├── public/                              # Directory for static assets like images and fonts
├── tailwind.config.ts                   # Tailwind CSS theme and plugin configuration
├── tests/                               # Directory for end-to-end tests
│   └── auth-smoke.spec.ts               # A smoke test for the authentication flow
├── types/                               # Global type definitions for core application concepts
│   ├── agents.ts                        # Type definitions for agents
│   ├── billing.ts                       # Type definitions for billing
│   ├── conversations.ts                 # Type definitions for conversations
│   ├── session.ts                       # Type definitions for user sessions
│   └── tools.ts                         # Type definitions for tools
├── vitest.config.ts                     # Vitest configuration for unit and integration tests
└── vitest.setup.ts                      # Setup file for Vitest tests, e.g., importing jest-dom