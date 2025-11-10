.
├── app/                                 # Next.js application directory containing pages, layouts, and API routes.
│   ├── (agent)/                         # Next.js route group for the main agent chat interface.
│   │   ├── actions.ts                   # Server Actions for agent interactions (chat streaming, listing conversations).
│   │   ├── layout.tsx                   # Layout for the agent chat pages, includes silent session refresh.
│   │   └── page.tsx                     # The main agent chat page UI, combining sidebar and chat interface.
│   ├── (auth)/                          # Next.js route group for authentication pages.
│   │   └── login/                       # Contains the login page route.
│   │       └── page.tsx                 # The UI component for the login page.
│   ├── actions/                         # Contains application-wide Server Actions.
│   │   ├── auth/                        # Server Actions related to authentication.
│   │   │   ├── email.ts                 # Server Actions for email verification.
│   │   │   ├── passwords.ts             # Server Actions for password management (reset, change).
│   │   │   ├── sessions.ts              # Server Actions for managing user sessions (list, revoke).
│   │   │   └── signup.ts                # Server Action for new tenant and user registration.
│   │   └── auth.ts                      # Core authentication Server Actions (login, logout, silent refresh).
│   ├── api/                             # API routes (Route Handlers) that proxy requests to the backend.
│   │   ├── agents/                      # API routes related to agents.
│   │   │   ├── [agentName]/             # Dynamic route for a specific agent.
│   │   │   │   └── status/              # Agent status-specific routes.
│   │   │   │       ├── route.test.ts    # Tests for the agent status API route.
│   │   │   │       └── route.ts         # API route to get a specific agent's status.
│   │   │   ├── route.test.ts            # Tests for the list agents API route.
│   │   │   └── route.ts                 # API route to list all available agents.
│   │   ├── auth/                        # API routes for authentication and user management.
│   │   │   ├── email/                   # API routes for email operations.
│   │   │   │   ├── send/                # API route to send verification emails.
│   │   │   │   │   ├── route.test.ts    # Tests for the send verification email API route.
│   │   │   │   │   └── route.ts         # API route to trigger sending a verification email.
│   │   │   │   └── verify/              # API route to verify email with a token.
│   │   │   │       ├── route.test.ts    # Tests for the verify email token API route.
│   │   │   │       └── route.ts         # API route for verifying an email token.
│   │   │   ├── logout/                  # API routes for session termination.
│   │   │   │   ├── all/                 # API route to log out from all sessions.
│   │   │   │   │   ├── route.test.ts    # Tests for the logout-all API route.
│   │   │   │   │   └── route.ts         # API route to log out of all user sessions.
│   │   │   │   ├── route.test.ts        # Tests for the single session logout API route.
│   │   │   │   └── route.ts             # API route to log out of the current session.
│   │   │   ├── password/                # API routes for password management.
│   │   │   │   ├── change/              # API route for user-initiated password change.
│   │   │   │   │   ├── route.test.ts    # Tests for the password change API route.
│   │   │   │   │   └── route.ts         # API route for a user to change their password.
│   │   │   │   ├── confirm/             # API route to confirm a password reset with a token.
│   │   │   │   │   ├── route.test.ts    # Tests for the password reset confirmation API route.
│   │   │   │   │   └── route.ts         # API route to finalize a password reset.
│   │   │   │   ├── forgot/              # API route to request a password reset email.
│   │   │   │   │   ├── route.test.ts    # Tests for the forgot password API route.
│   │   │   │   │   └── route.ts         # API route to initiate a password reset.
│   │   │   │   └── reset/               # API route for admin-initiated password reset.
│   │   │   │       ├── route.test.ts    # Tests for the admin password reset API route.
│   │   │   │       └── route.ts         # API route for an admin to reset a user's password.
│   │   │   ├── refresh/                 # API route for session token refreshing.
│   │   │   │   └── route.ts             # API route to refresh an access token using a refresh token.
│   │   │   ├── register/                # API route for new user/tenant registration.
│   │   │   │   ├── route.test.ts        # Tests for the user registration API route.
│   │   │   │   └── route.ts             # API route to handle new user and tenant sign-ups.
│   │   │   ├── service-accounts/        # API routes for service account management.
│   │   │   │   └── issue/               # API route to issue service account tokens.
│   │   │   │       ├── route.test.ts    # Tests for the service account token issuance API route.
│   │   │   │       └── route.ts         # API route to issue a new service account token.
│   │   │   ├── session/                 # API route for current session information.
│   │   │   │   └── route.ts             # API route to get details of the current user's session.
│   │   │   └── sessions/                # API routes for managing multiple user sessions.
│   │   │       ├── [sessionId]/         # Dynamic route for a specific session.
│   │   │       │   ├── route.test.ts    # Tests for revoking a specific user session.
│   │   │       │   └── route.ts         # API route to revoke a specific user session by ID.
│   │   │       ├── route.test.ts        # Tests for the list user sessions API route.
│   │   │       └── route.ts             # API route to list all active sessions for the current user.
│   │   ├── billing/                     # API routes related to billing and subscriptions.
│   │   │   ├── plans/                   # API route for billing plans.
│   │   │   │   └── route.ts             # API route to list available billing plans.
│   │   │   ├── stream/                  # API route for the billing event stream.
│   │   │   │   └── route.ts             # Server-Sent Events (SSE) route for real-time billing updates.
│   │   │   └── tenants/                 # API routes for tenant-specific billing.
│   │   │       └── [tenantId]/          # Dynamic route for a specific tenant.
│   │   │           ├── subscription/    # API routes for a tenant's subscription.
│   │   │           │   ├── cancel/      # API route to cancel a subscription.
│   │   │           │   │   ├── route.test.ts # Tests for the subscription cancellation API route.
│   │   │           │   │   └── route.ts # API route to cancel a tenant's subscription.
│   │   │           │   ├── route.test.ts # Tests for managing a tenant's subscription.
│   │   │           │   └── route.ts     # API routes (GET, POST, PATCH) for subscription management.
│   │   │           └── usage/           # API route for reporting metered usage.
│   │   │               ├── route.test.ts # Tests for the usage recording API route.
│   │   │               └── route.ts     # API route to record metered usage for a tenant.
│   │   ├── chat/                        # API routes for chat functionality.
│   │   │   ├── route.test.ts            # Tests for the non-streaming chat API route.
│   │   │   ├── route.ts                 # API route for single request/response chat interactions.
│   │   │   └── stream/                  # API route for streaming chat.
│   │   │       └── route.ts             # Server-Sent Events (SSE) route for streaming chat responses.
│   │   ├── conversations/               # API routes for managing conversations.
│   │   │   ├── [conversationId]/        # Dynamic route for a specific conversation.
│   │   │   │   ├── route.test.ts        # Tests for getting and deleting a specific conversation.
│   │   │   │   └── route.ts             # API routes (GET, DELETE) for a specific conversation.
│   │   │   ├── route.test.ts            # Tests for the list conversations API route.
│   │   │   └── route.ts                 # API route to list all conversations for the current user.
│   │   ├── health/                      # API routes for health checks.
│   │   │   ├── ready/                   # API route for readiness probes.
│   │   │   │   ├── route.test.ts        # Tests for the readiness probe API route.
│   │   │   │   └── route.ts             # API route to check if the backend service is ready.
│   │   │   ├── route.test.ts            # Tests for the liveness probe API route.
│   │   │   └── route.ts                 # API route to check if the backend service is alive.
│   │   └── tools/                       # API routes for agent tools.
│   │       └── route.ts                 # API route to list available tools.
│   ├── layout.tsx                     # Root layout component for the entire application.
│   └── providers.tsx                  # Client-side providers, primarily for React Query setup.
├── components/                          # Reusable React components.
│   ├── agent/                           # Components for the agent chat interface.
│   │   ├── ChatInterface.tsx          # Component for the message display and input form.
│   │   └── ConversationSidebar.tsx    # Component for listing and managing conversations.
│   ├── auth/                            # Authentication-related components.
│   │   ├── LoginForm.tsx              # The login form component.
│   │   ├── LogoutButton.tsx           # A button component to trigger the logout action.
│   │   └── SilentRefresh.tsx          # Wrapper component for the silent session refresh hook.
│   └── billing/                         # Billing-related components.
│       ├── BillingEventsPanel.tsx       # Component to display real-time billing activity.
│       └── __tests__/                   # Tests for billing components.
│           └── BillingEventsPanel.test.tsx # Tests for the BillingEventsPanel component.
├── eslint.config.mjs                    # ESLint configuration file.
├── hooks/                               # Legacy/unused custom React hooks.
│   ├── useBillingStream.ts            # Unused custom hook for connecting to the billing stream.
│   └── useSilentRefresh.ts            # Unused custom hook for handling silent token refresh.
├── lib/                                 # Core logic, utilities, and API interactions.
│   ├── api/                             # Functions for making client-side API requests.
│   │   ├── __tests__/                   # Tests for API client-side functions.
│   │   │   └── chat.test.ts             # Tests for the client-side chat API helpers.
│   │   ├── agents.ts                    # Client-side API functions for fetching agent data.
│   │   ├── billing.ts                   # Client-side API function for connecting to the billing SSE stream.
│   │   ├── billingPlans.ts              # Client-side API function for fetching billing plans.
│   │   ├── chat.ts                      # Client-side API functions for chat (streaming and non-streaming).
│   │   ├── client/                      # Auto-generated API client from OpenAPI specification.
│   │   │   ├── client/                  # Core client implementation files.
│   │   │   │   ├── client.gen.ts        # The main generated fetch client logic.
│   │   │   │   ├── index.ts             # Re-exports core client utilities.
│   │   │   │   ├── types.gen.ts         # Generated TypeScript types for the client's internal options.
│   │   │   │   └── utils.gen.ts         # Generated utility functions for the client.
│   │   │   ├── client.gen.ts            # Generated client configuration and instantiation.
│   │   │   ├── core/                    # Low-level generated utilities for the client.
│   │   │   │   ├── auth.gen.ts          # Generated authentication helpers.
│   │   │   │   ├── bodySerializer.gen.ts # Generated request body serializers.
│   │   │   │   ├── params.gen.ts        # Generated logic for handling request parameters.
│   │   │   │   ├── pathSerializer.gen.ts # Generated logic for serializing path parameters.
│   │   │   │   ├── queryKeySerializer.gen.ts # Generated utilities for serializing query keys.
│   │   │   │   ├── serverSentEvents.gen.ts # Generated client for Server-Sent Events (SSE).
│   │   │   │   ├── types.gen.ts         # Generated core type definitions for the client.
│   │   │   │   └── utils.gen.ts         # Generated core utility functions.
│   │   │   ├── index.ts                 # Main export file for the generated client SDK.
│   │   │   ├── sdk.gen.ts               # Generated SDK functions for each API endpoint.
│   │   │   └── types.gen.ts             # Generated TypeScript types from the OpenAPI schema.
│   │   ├── config.ts                    # Configuration and re-export of the generated API client.
│   │   ├── conversations.ts             # Client-side API functions for managing conversations.
│   │   ├── session.ts                   # Client-side API functions for session management (fetch, refresh).
│   │   └── tools.ts                     # Client-side API function for fetching available tools.
│   ├── auth/                            # Authentication-related logic and utilities.
│   │   ├── clientMeta.ts                # Client-side utility to read session metadata from the cookie.
│   │   ├── cookies.ts                   # Server-side helpers for managing authentication cookies.
│   │   └── session.ts                   # Server-side session management logic (e.g., exchanging credentials).
│   ├── chat/                            # Contains chat-related hooks, types, and logic.
│   │   ├── __tests__/                   # Tests for the chat controller hook.
│   │   │   ├── testUtils.tsx            # Utilities for testing React Query hooks.
│   │   │   ├── useChatController.integration.test.tsx # Integration tests for the chat controller hook.
│   │   │   └── useChatController.test.tsx # Unit tests for the chat controller hook.
│   │   ├── types.ts                     # TypeScript types specific to the chat feature.
│   │   └── useChatController.ts         # Core React hook for managing chat state and interactions.
│   ├── config.ts                        # Global application configuration constants.
│   ├── queries/                         # TanStack Query hooks for data fetching and caching.
│   │   ├── agents.ts                    # React Query hooks for fetching agent data.
│   │   ├── billing.ts                   # Custom React hook for subscribing to the billing SSE stream.
│   │   ├── billingPlans.ts              # React Query hook for fetching billing plans.
│   │   ├── billingSubscriptions.ts      # React Query hooks for managing billing subscriptions.
│   │   ├── chat.ts                      # React Query mutation hook for sending chat messages.
│   │   ├── conversations.ts             # React Query hook for managing the list of conversations.
│   │   ├── keys.ts                      # Centralized query keys for TanStack Query.
│   │   ├── session.ts                   # Custom React hook for silent session refresh.
│   │   └── tools.ts                     # React Query hook for fetching tools.
│   ├── server/                          # Server-side only logic.
│   │   ├── apiClient.ts                 # Factory for creating an authenticated server-side API client.
│   │   ├── services/                    # Service layer abstracting backend API calls for server-side use.
│   │   │   ├── agents.ts                # Service functions for agent-related backend calls.
│   │   │   ├── auth/                    # Authentication-related service functions.
│   │   │   │   ├── email.ts             # Service functions for email verification.
│   │   │   │   ├── passwords.ts         # Service functions for password management.
│   │   │   │   ├── serviceAccounts.ts   # Service functions for managing service accounts.
│   │   │   │   ├── sessions.ts          # Service functions for managing user sessions.
│   │   │   │   └── signup.ts            # Service function for user registration.
│   │   │   ├── auth.ts                  # Core authentication services (login, refresh, get profile).
│   │   │   ├── billing.ts               # Service functions for billing-related backend calls.
│   │   │   ├── chat.ts                  # Service functions for chat-related backend calls.
│   │   │   ├── conversations.ts         # Service functions for conversation-related backend calls.
│   │   │   ├── health.ts                # Service functions for backend health checks.
│   │   │   └── tools.ts                 # Service function for fetching tools from the backend.
│   │   └── streaming/                   # Logic for handling server-side streaming.
│   │       └── chat.ts                  # Server-side helper to stream chat directly from the backend API.
│   ├── types/                           # Shared application-level types (distinct from generated API types).
│   │   ├── auth.ts                      # Shared types for authentication tokens and session summary.
│   │   └── billing.ts                   # Shared types for billing payloads and subscriptions.
│   └── utils.ts                         # General utility functions (e.g., `cn` for classnames).
├── middleware.ts                        # Next.js middleware for route protection and authentication checks.
├── next.config.ts                       # Next.js configuration file.
├── openapi-ts.config.ts                 # Configuration file for the OpenAPI to TypeScript client generator.
├── playwright.config.ts                 # Configuration file for Playwright end-to-end tests.
├── pnpm-lock.yaml                       # PNPM lockfile for dependency versioning.
├── postcss.config.mjs                   # PostCSS configuration, used by Tailwind CSS.
├── public/                              # Directory for static assets.
│   ├── file.svg                         # SVG icon.
│   ├── globe.svg                        # SVG icon.
│   ├── next.svg                         # Next.js logo SVG.
│   ├── vercel.svg                       # Vercel logo SVG.
│   └── window.svg                       # SVG icon.
├── tailwind.config.ts                   # Tailwind CSS theme and plugin configuration.
├── tests/                               # Contains end-to-end tests.
│   └── auth-smoke.spec.ts               # Playwright smoke test for the authentication and chat flow.
├── types/                               # Application-wide shared TypeScript definitions.
│   ├── agents.ts                        # Type definitions related to agents.
│   ├── billing.ts                       # Type definitions related to billing.
│   ├── conversations.ts                 # Type definitions related to conversations.
│   ├── session.ts                       # Type definitions related to user sessions.
│   └── tools.ts                         # Type definitions related to tools.
├── vitest.config.ts                     # Configuration file for the Vitest testing framework.
└── vitest.setup.ts                      # Setup file for Vitest, importing Jest DOM matchers.
