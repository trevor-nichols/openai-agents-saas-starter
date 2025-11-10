.
├── app/                                 # Main Next.js application directory with pages and layouts
│   ├── (agent)/                         # Route group for the main agent chat interface
│   │   ├── actions.ts                   # Server Actions for chat streaming and managing conversations
│   │   ├── layout.tsx                   # Layout for agent pages, including silent session refresh
│   │   └── page.tsx                     # The primary page for the agent chat interface
│   ├── (auth)/                          # Route group for authentication pages
│   │   └── login/                       # Directory for the login page
│   │       └── page.tsx                 # Renders the login form page
│   ├── actions/                         # Contains server-side actions callable from client components
│   │   ├── auth/                        # Server actions related to authentication
│   │   │   ├── email.ts                 # Server actions for sending and verifying emails
│   │   │   ├── passwords.ts             # Server actions for password management (reset, change)
│   │   │   ├── sessions.ts              # Server actions for managing user sessions (list, revoke)
│   │   │   └── signup.ts                # Server action for user/tenant registration
│   │   └── auth.ts                      # Core server actions for login, logout, and silent refresh
│   ├── api/                             # API routes (Next.js Route Handlers)
│   │   ├── agents/                      # API routes for agent-related data
│   │   │   ├── [agentName]/             # Dynamic routes for a specific agent
│   │   │   │   └── status/              # Route for getting an agent's status
│   │   │   │       ├── route.test.ts    # Tests for the agent status API route
│   │   │   │       └── route.ts         # API route to get the status of a specific agent
│   │   │   ├── route.test.ts            # Tests for the list agents API route
│   │   │   └── route.ts                 # API route to list all available agents
│   │   ├── auth/                        # API routes for authentication flows
│   │   │   ├── email/                   # API routes for email verification
│   │   │   │   ├── send/                # API route for sending verification emails
│   │   │   │   │   ├── route.test.ts    # Tests for the send verification email API route
│   │   │   │   │   └── route.ts         # API route to trigger sending a verification email
│   │   │   │   └── verify/              # API route for verifying an email token
│   │   │   │       ├── route.test.ts    # Tests for the email verification API route
│   │   │   │       └── route.ts         # API route to verify an email using a token
│   │   │   ├── logout/                  # API routes for user logout
│   │   │   │   ├── all/                 # API route for logging out of all sessions
│   │   │   │   │   ├── route.test.ts    # Tests for the logout all sessions API route
│   │   │   │   │   └── route.ts         # API route to log a user out of all active sessions
│   │   │   │   ├── route.test.ts        # Tests for the single session logout API route
│   │   │   │   └── route.ts             # API route to log a user out of the current session
│   │   │   ├── password/                # API routes for password management
│   │   │   │   ├── change/              # API route for changing a password
│   │   │   │   │   ├── route.test.ts    # Tests for the change password API route
│   │   │   │   │   └── route.ts         # API route to handle user password changes
│   │   │   │   ├── confirm/             # API route for confirming a password reset
│   │   │   │   │   ├── route.test.ts    # Tests for the confirm password reset API route
│   │   │   │   │   └── route.ts         # API route to confirm a password reset with a token
│   │   │   │   ├── forgot/              # API route for requesting a password reset
│   │   │   │   │   ├── route.test.ts    # Tests for the forgot password API route
│   │   │   │   │   └── route.ts         # API route to initiate the password reset process
│   │   │   │   └── reset/               # API route for admin-initiated password resets
│   │   │   │       ├── route.test.ts    # Tests for the admin password reset API route
│   │   │   │       └── route.ts         # API route for an admin to reset a user's password
│   │   │   ├── refresh/                 # API route for refreshing session tokens
│   │   │   │   └── route.ts             # API route to refresh an authentication session using a refresh token
│   │   │   ├── register/                # API route for user registration
│   │   │   │   ├── route.test.ts        # Tests for the user registration API route
│   │   │   │   └── route.ts             # API route to handle new user and tenant registration
│   │   │   ├── service-accounts/        # API routes for service accounts
│   │   │   │   └── issue/               # API route for issuing service account tokens
│   │   │   │       ├── route.test.ts    # Tests for issuing service account tokens
│   │   │   │       └── route.ts         # API route for issuing a token for a service account
│   │   │   ├── session/                 # API route for getting current session info
│   │   │   │   └── route.ts             # API route to get information about the current user's session
│   │   │   └── sessions/                # API routes for managing user sessions
│   │   │       ├── [sessionId]/         # Dynamic route for a specific session
│   │   │       │   ├── route.test.ts    # Tests for revoking a specific user session
│   │   │       │   └── route.ts         # API route to revoke a specific user session
│   │   │       ├── route.test.ts        # Tests for listing user sessions
│   │   │       └── route.ts             # API route to list all sessions for the current user
│   │   ├── billing/                     # API routes for billing
│   │   │   ├── plans/                   # API route for listing billing plans
│   │   │   │   └── route.ts             # API route to list available billing plans
│   │   │   ├── stream/                  # API route for the billing event stream
│   │   │   │   └── route.ts             # API route to stream real-time billing events via SSE
│   │   │   └── tenants/                 # API routes for tenant-specific billing
│   │   │       └── [tenantId]/          # Dynamic route for a specific tenant
│   │   │           ├── subscription/    # API routes for a tenant's subscription
│   │   │           │   ├── cancel/      # API route for cancelling a subscription
│   │   │           │   │   ├── route.test.ts # Tests for the subscription cancellation API route
│   │   │           │   │   └── route.ts     # API route to cancel a tenant's subscription
│   │   │           │   ├── route.test.ts    # Tests for tenant subscription management API routes (GET, POST, PATCH)
│   │   │           │   └── route.ts         # API routes to manage a tenant's subscription (get, start, update)
│   │   │           └── usage/           # API route for recording usage
│   │   │               ├── route.test.ts    # Tests for the usage recording API route
│   │   │               └── route.ts         # API route to record metered usage for a tenant
│   │   ├── chat/                        # API routes for chat functionality
│   │   │   ├── route.test.ts            # Tests for the non-streaming chat API route
│   │   │   ├── route.ts                 # API route for handling non-streaming chat messages
│   │   │   └── stream/                  # API route for streaming chat messages
│   │   │       └── route.ts             # API route to stream chat responses via SSE
│   │   ├── conversations/               # API routes for conversations
│   │   │   ├── [conversationId]/        # Dynamic route for a specific conversation
│   │   │   │   ├── route.test.ts        # Tests for getting/deleting a specific conversation
│   │   │   │   └── route.ts             # API route to get or delete a specific conversation
│   │   │   ├── route.test.ts            # Tests for the list conversations API route
│   │   │   └── route.ts                 # API route to list all conversations for the current user
│   │   ├── health/                      # API routes for health checks
│   │   │   ├── ready/                   # API route for readiness probe
│   │   │   │   ├── route.test.ts        # Tests for the readiness probe API route
│   │   │   │   └── route.ts             # API route for the application's readiness probe
│   │   │   ├── route.test.ts            # Tests for the liveness probe API route
│   │   │   └── route.ts                 # API route for the application's liveness probe
│   │   └── tools/                       # API routes for tools
│   │       └── route.ts                 # API route to list available tools
│   ├── layout.tsx                       # Root layout for the entire application
│   └── providers.tsx                    # Client-side providers, primarily for React Query
├── components/                          # Contains reusable React components
│   ├── agent/                           # Components for the agent chat interface
│   │   ├── ChatInterface.tsx            # Component for displaying messages and the input form
│   │   └── ConversationSidebar.tsx      # Component for listing and managing conversations
│   ├── auth/                            # Components for authentication UI
│   │   ├── LoginForm.tsx                # The user login form component
│   │   ├── LogoutButton.tsx             # A simple logout button component
│   │   └── SilentRefresh.tsx            # A component to trigger the silent session refresh hook
│   ├── billing/                         # Components related to billing information
│   │   ├── BillingEventsPanel.tsx       # Displays a real-time feed of billing events
│   │   └── __tests__/                   # Tests for billing components
│   │       └── BillingEventsPanel.test.tsx # Unit tests for the BillingEventsPanel component
├── eslint.config.mjs                    # ESLint configuration file
├── hooks/                               # Contains custom React hooks
│   ├── useBillingStream.ts              # Custom hook for connecting to the real-time billing event stream
│   ├── useConversations.ts              # Custom hook for fetching and managing the conversation list
│   └── useSilentRefresh.ts              # Custom hook to handle silent token refresh logic
├── lib/                                 # Core logic, utilities, and libraries
│   ├── api/                             # Client-side data fetching functions and API client
│   │   ├── agents.ts                    # Client-side functions for fetching agent data
│   │   ├── billing.ts                   # Client-side function for connecting to the billing SSE stream
│   │   ├── billingPlans.ts              # Client-side function for fetching billing plans
│   │   ├── chat.ts                      # (Empty) Potentially for client-side chat functions
│   │   ├── client/                      # Auto-generated API client from OpenAPI specification
│   │   │   ├── client/                  # Core implementation of the auto-generated client
│   │   │   │   ├── client.gen.ts        # The main auto-generated client factory function
│   │   │   │   ├── index.ts             # Re-exports core client utilities
│   │   │   │   ├── types.gen.ts         # Auto-generated types for the client's internal options and results
│   │   │   │   └── utils.gen.ts         # Auto-generated utilities for the client (URL building, config merging)
│   │   │   ├── client.gen.ts            # Auto-generated API client instance and configuration
│   │   │   ├── core/                    # Auto-generated core utilities for the API client
│   │   │   │   ├── auth.gen.ts          # Auto-generated authentication helpers
│   │   │   │   ├── bodySerializer.gen.ts # Auto-generated request body serialization logic
│   │   │   │   ├── params.gen.ts        # Auto-generated helpers for building request parameters
│   │   │   │   ├── pathSerializer.gen.ts # Auto-generated logic for serializing path parameters
│   │   │   │   ├── queryKeySerializer.gen.ts # Auto-generated helpers for serializing query keys
│   │   │   │   ├── serverSentEvents.gen.ts # Auto-generated logic for handling Server-Sent Events
│   │   │   │   ├── types.gen.ts         # Auto-generated core type definitions for the client
│   │   │   │   └── utils.gen.ts         # Auto-generated core utility functions
│   │   │   ├── index.ts                 # Main export file for the generated API client SDK
│   │   │   ├── sdk.gen.ts               # Auto-generated SDK functions for each API endpoint
│   │   │   └── types.gen.ts             # Auto-generated TypeScript types from the OpenAPI schema
│   │   ├── config.ts                    # Re-exports the generated API client for easy access
│   │   ├── conversations.ts             # Client-side functions for fetching and managing conversations
│   │   ├── session.ts                   # Client-side functions for fetching and refreshing session data
│   │   ├── streaming.ts                 # Client-side function for initiating a chat stream
│   │   └── tools.ts                     # Client-side function for fetching available tools
│   ├── auth/                            # Authentication-related utilities
│   │   ├── clientMeta.ts                # Client-side helper to read session metadata from cookies
│   │   ├── cookies.ts                   # Server-side helpers for managing authentication cookies
│   │   └── session.ts                   # Server-side logic for managing user sessions (login, refresh, destroy)
│   ├── chat/                            # Shared types and logic for chat
│   │   └── types.ts                     # TypeScript types for chat streaming
│   ├── config.ts                        # Application configuration constants
│   ├── queries/                         # TanStack Query hooks for data fetching
│   │   ├── agents.ts                    # TanStack Query hooks for fetching agent data
│   │   ├── billing.ts                   # Custom hook for the real-time billing event stream
│   │   ├── billingPlans.ts              # TanStack Query hook for fetching billing plans
│   │   ├── billingSubscriptions.ts      # TanStack Query hooks for managing tenant subscriptions
│   │   ├── chat.ts                      # TanStack Query mutation hook for sending chat messages
│   │   ├── conversations.ts             # TanStack Query hooks for managing conversations
│   │   ├── keys.ts                      # Centralized query keys for TanStack Query
│   │   ├── session.ts                   # Custom hook for managing silent session refresh
│   │   └── tools.ts                     # TanStack Query hook for fetching tools
│   ├── server/                          # Server-side only logic
│   │   ├── apiClient.ts                 # Server-side API client factory with authentication handling
│   │   ├── services/                    # Server-side business logic layer
│   │   │   ├── agents.ts                # Service functions for agent-related operations
│   │   │   ├── auth/                    # Services for authentication operations
│   │   │   │   ├── email.ts             # Service functions for email verification
│   │   │   │   ├── passwords.ts         # Service functions for password management
│   │   │   │   ├── serviceAccounts.ts   # Service function for issuing service account tokens
│   │   │   │   ├── sessions.ts          # Service functions for managing user sessions
│   │   │   │   └── signup.ts            # Service function for user/tenant registration
│   │   │   ├── auth.ts                  # Core authentication service functions (login, refresh, get profile)
│   │   │   ├── billing.ts               # Service functions for billing and subscription management
│   │   │   ├── chat.ts                  # Service functions for handling chat messages and streams
│   │   │   ├── conversations.ts         # Service functions for managing conversation data
│   │   │   ├── health.ts                # Service functions for checking backend health
│   │   │   └── tools.ts                 # Service function for listing available tools
│   │   └── streaming/                   # Server-side logic for streaming data
│   │       └── chat.ts                  # Server-side helper to stream chat chunks from the backend
│   ├── types/                           # Shared, high-level type definitions for the application
│   │   ├── auth.ts                      # Types for authentication tokens and session summaries
│   │   └── billing.ts                   # Types related to billing events, plans, and subscriptions
│   └── utils.ts                         # General utility functions, like `cn` for classnames
├── middleware.ts                        # Next.js middleware for handling authentication and routing protection
├── next.config.ts                       # Next.js project configuration
├── openapi-ts.config.ts                 # Configuration for generating the API client from an OpenAPI spec
├── playwright.config.ts                 # Playwright end-to-end testing configuration
├── pnpm-lock.yaml                       # Dependency lock file for pnpm
├── postcss.config.mjs                   # PostCSS configuration, used for Tailwind CSS
├── public/                              # Static assets publicly available
│   ├── file.svg                         # An SVG icon representing a file
│   ├── globe.svg                        # An SVG icon representing a globe
│   ├── next.svg                         # The Next.js logo
│   ├── vercel.svg                       # The Vercel logo
│   └── window.svg                       # An SVG icon representing a window
├── tailwind.config.ts                   # Tailwind CSS theme and plugin configuration
├── tests/                               # End-to-end tests directory
│   └── auth-smoke.spec.ts               # A Playwright smoke test for the login/chat/logout flow
├── types/                               # Root directory for shared application types
│   ├── agents.ts                        # Application-specific types for agents
│   ├── billing.ts                       # Application-specific types for billing
│   ├── conversations.ts                 # Application-specific types for conversations
│   ├── session.ts                       # Application-specific types for sessions
│   └── tools.ts                         # Application-specific types for tools
├── vitest.config.ts                     # Vitest unit/integration testing configuration
└── vitest.setup.ts                      # Setup file for Vitest tests, importing jest-dom matchers