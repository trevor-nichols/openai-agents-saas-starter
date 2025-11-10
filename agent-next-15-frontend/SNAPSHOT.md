.
├── app/                         # Next.js App Router directory containing all routes and UI.
│   ├── (app)/                   # Route group for the authenticated sections of the application.
│   │   ├── (workspace)/         # Route group for workspace-style layouts (e.g., chat).
│   │   │   ├── chat/            # Contains pages and server actions for the chat interface.
│   │   │   │   ├── actions.ts   # Server Actions for chat streaming and fetching conversations.
│   │   │   │   └── page.tsx     # The main chat interface page component.
│   │   │   ├── layout.tsx       # Layout for workspace views like chat, providing spacing.
│   │   ├── account/             # Pages for user account management.
│   │   │   ├── profile/         # User profile page.
│   │   │   │   └── page.tsx     # User profile page.
│   │   │   ├── security/        # User security settings page.
│   │   │   │   └── page.tsx     # User security settings page.
│   │   │   ├── service-accounts/# Service account management page.
│   │   │   │   └── page.tsx     # Page for managing service account API keys.
│   │   │   ├── sessions/        # User session management page.
│   │   │   │   └── page.tsx     # Page for viewing and managing active user sessions.
│   │   ├── agents/              # Agent management pages.
│   │   │   └── page.tsx         # Page for listing and managing AI agents.
│   │   ├── billing/             # Billing management pages.
│   │   │   ├── page.tsx         # Main billing overview page.
│   │   │   └── plans/           # Subscription plan management page.
│   │   │       └── page.tsx     # Page for managing subscription plans.
│   │   ├── conversations/       # Conversation history pages.
│   │   │   └── page.tsx         # Page for viewing all user conversations.
│   │   ├── dashboard/           # Main user dashboard page.
│   │   │   └── page.tsx         # The main user dashboard after login.
│   │   ├── layout.tsx           # Main application shell layout for authenticated users.
│   │   ├── page.tsx             # Root page for the authenticated app, redirects to /dashboard.
│   │   ├── settings/            # Application settings pages.
│   │   │   └── tenant/          # Tenant-specific settings page.
│   │   │       └── page.tsx     # Page for managing tenant-specific settings.
│   │   └── tools/               # Tool management pages.
│   │       └── page.tsx         # Page for listing available agent tools.
│   ├── (auth)/                  # Route group for authentication pages (login, registration, etc.).
│   │   ├── email/               # Email-related authentication pages.
│   │   │   └── verify/          # Email verification page.
│   │   │       └── page.tsx     # Page for handling email verification links.
│   │   ├── layout.tsx           # Layout for authentication pages (login, register, etc.).
│   │   ├── login/               # Login page.
│   │   │   └── page.tsx         # The user login page.
│   │   ├── password/            # Password management pages.
│   │   │   ├── forgot/          # "Forgot password" page to request a reset link.
│   │   │   │   └── page.tsx     # "Forgot password" page to request a reset link.
│   │   │   └── reset/           # Page for resetting a password using a token.
│   │   │       └── page.tsx     # Page for resetting a password using a token.
│   │   └── register/            # User registration page.
│   │       └── page.tsx         # User and tenant registration page.
│   ├── (marketing)/             # Route group for public-facing marketing pages.
│   │   ├── features/            # Product features page.
│   │   │   └── page.tsx         # A public page detailing product features.
│   │   ├── layout.tsx           # Layout for public marketing pages with header and footer.
│   │   ├── page.tsx             # The main public landing page.
│   │   └── pricing/             # Product pricing page.
│   │       └── page.tsx         # The public pricing page.
│   ├── actions/                 # Server Actions for handling form submissions and mutations.
│   │   ├── auth.ts              # Core authentication server actions (login, logout, refresh).
│   │   └── auth/                # Authentication-specific Server Actions.
│   │       ├── email.ts         # Server actions for email verification.
│   │       ├── passwords.ts     # Server actions for password management.
│   │       ├── sessions.ts      # Server actions for managing user sessions.
│   │       └── signup.ts        # Server action for user/tenant registration.
│   ├── api/                     # API Route Handlers acting as a backend-for-frontend (BFF).
│   │   ├── agents/              # API routes for agent management.
│   │   │   ├── [agentName]/     # API routes for a specific agent.
│   │   │   │   └── status/      # API routes for agent status.
│   │   │   │       ├── route.test.ts # Tests for the agent status API route.
│   │   │   │       └── route.ts   # API route to get a specific agent's status.
│   │   │   ├── route.test.ts    # Tests for the list agents API route.
│   │   │   └── route.ts         # API route to list available agents.
│   │   ├── auth/                # API routes for authentication.
│   │   │   ├── email/           # API routes for email verification.
│   │   │   │   ├── send/        # API route to trigger sending verification emails.
│   │   │   │   │   ├── route.test.ts # Tests for the send verification email route.
│   │   │   │   │   └── route.ts   # API route to send a verification email.
│   │   │   │   └── verify/      # API route to verify an email token.
│   │   │   │       ├── route.test.ts # Tests for the verify email route.
│   │   │   │       └── route.ts   # API route to verify an email token.
│   │   │   ├── logout/          # API routes for user logout.
│   │   │   │   ├── all/         # API route to log out all user sessions.
│   │   │   │   │   ├── route.test.ts # Tests for the logout all sessions route.
│   │   │   │   │   └── route.ts   # API route to log out all user sessions.
│   │   │   │   ├── route.test.ts # Tests for the single session logout route.
│   │   │   │   └── route.ts     # API route to log out a single session.
│   │   │   ├── password/        # API routes for password management.
│   │   │   │   ├── change/      # API route for password changes.
│   │   │   │   │   ├── route.test.ts # Tests for the password change route.
│   │   │   │   │   └── route.ts   # API route for changing the current user's password.
│   │   │   │   ├── confirm/     # API route to confirm a password reset.
│   │   │   │   │   ├── route.test.ts # Tests for the confirm password reset route.
│   │   │   │   │   └── route.ts   # API route to confirm a password reset.
│   │   │   │   ├── forgot/      # API route to request a password reset.
│   │   │   │   │   ├── route.test.ts # Tests for the forgot password route.
│   │   │   │   │   └── route.ts   # API route to request a password reset.
│   │   │   │   └── reset/       # API route for admin-initiated password resets.
│   │   │   │       ├── route.test.ts # Tests for the admin password reset route.
│   │   │   │       └── route.ts   # API route for admin-initiated password resets.
│   │   │   ├── refresh/         # API route for refreshing session tokens.
│   │   │   │   └── route.ts     # API route to refresh an access token.
│   │   │   ├── register/        # API route for user registration.
│   │   │   │   ├── route.test.ts # Tests for the registration route.
│   │   │   │   └── route.ts     # API route for user and tenant registration.
│   │   │   ├── service-accounts/# API routes for service accounts.
│   │   │   │   └── issue/       # API route to issue service account tokens.
│   │   │   │       ├── route.test.ts # Tests for the service account token issuance route.
│   │   │   │       └── route.ts   # API route to issue a service account token.
│   │   │   ├── session/         # API routes for session information.
│   │   │   │   └── route.ts     # API route to get current session information.
│   │   │   └── sessions/        # API routes for managing user sessions.
│   │   │       ├── [sessionId]/ # API routes for a specific user session.
│   │   │       │   ├── route.test.ts # Tests for the revoke session route.
│   │   │       │   └── route.ts   # API route to revoke a specific session by ID.
│   │   │       ├── route.test.ts # Tests for the list sessions route.
│   │   │       └── route.ts     # API route to list user sessions.
│   │   ├── billing/             # API routes for billing.
│   │   │   ├── plans/           # API route for billing plans.
│   │   │   │   └── route.ts     # API route to list available billing plans.
│   │   │   ├── stream/          # SSE API route for billing events.
│   │   │   │   └── route.ts     # Server-Sent Events (SSE) route for billing events.
│   │   │   └── tenants/         # API routes for tenant-specific billing.
│   │   │       └── [tenantId]/  # API routes for a specific tenant.
│   │   │           ├── subscription/# API routes for tenant subscription management.
│   │   │           │   ├── cancel/  # API route to cancel a subscription.
│   │   │           │   │   ├── route.test.ts # Tests for the cancel subscription route.
│   │   │           │   │   └── route.ts   # API route to cancel a subscription.
│   │   │           │   ├── route.test.ts # Tests for the subscription management routes.
│   │   │           │   └── route.ts   # API routes for managing a tenant's subscription.
│   │   │           └── usage/     # API route to report usage.
│   │   │               ├── route.test.ts # Tests for the usage reporting route.
│   │   │               └── route.ts   # API route for reporting metered usage.
│   │   ├── chat/                # API routes for chat functionality.
│   │   │   ├── route.test.ts    # Tests for the single-shot chat route.
│   │   │   ├── route.ts         # API route for single-shot chat messages.
│   │   │   └── stream/          # SSE API route for streaming chat responses.
│   │   │       └── route.ts     # Server-Sent Events (SSE) route for streaming chat responses.
│   │   ├── conversations/       # API routes for conversations.
│   │   │   ├── [conversationId]/# API routes for a specific conversation.
│   │   │   │   ├── route.test.ts # Tests for the specific conversation routes.
│   │   │   │   └── route.ts     # API routes to get or delete a specific conversation.
│   │   │   ├── route.test.ts    # Tests for the list conversations route.
│   │   │   └── route.ts         # API route to list all conversations.
│   │   ├── health/              # API routes for health checks.
│   │   │   ├── ready/           # API route for readiness checks.
│   │   │   │   ├── route.test.ts # Tests for the readiness health check route.
│   │   │   │   └── route.ts     # API route for the readiness health check.
│   │   │   ├── route.test.ts    # Tests for the liveness health check route.
│   │   │   └── route.ts         # API route for the liveness health check.
│   │   └── tools/               # API routes for agent tools.
│   │       └── route.ts         # API route to list available tools.
│   ├── layout.tsx               # Root application layout, sets up HTML structure and providers.
│   └── providers.tsx            # Client-side providers, primarily for React Query.
├── components/                  # Reusable React components.
│   ├── agent/                   # Components for the AI agent chat interface.
│   │   ├── ChatInterface.tsx    # Renders the chat message list and input form.
│   │   └── ConversationSidebar.tsx # Renders the sidebar with a list of conversations.
│   ├── auth/                    # Components used in authentication flows.
│   │   ├── LoginForm.tsx        # The user login form component.
│   │   ├── LogoutButton.tsx     # A button component to trigger the logout action.
│   │   └── SilentRefresh.tsx    # A component to handle silent session token refreshing.
│   ├── billing/                 # Components related to billing UI.
│   │   ├── BillingEventsPanel.tsx # Displays real-time billing events from an SSE stream.
│   │   └── __tests__/           # Tests for billing components.
│   │       └── BillingEventsPanel.test.tsx # Tests for the BillingEventsPanel component.
│   └── ui/                      # Core UI components, based on shadcn/ui.
├── eslint.config.mjs            # ESLint configuration file.
├── hooks/                       # Custom React hooks for application logic.
│   ├── useBillingStream.ts      # Custom hook for connecting to the real-time billing event stream.
│   └── useSilentRefresh.ts      # Custom hook for silent session token refreshing.
├── lib/                         # Core logic, utilities, and API communication layers.
│   ├── api/                     # Client-side functions for making API calls to Next.js routes.
│   │   ├── __tests__/           # Tests for the client-side API layer.
│   │   │   └── chat.test.ts     # Unit tests for the client-side chat API functions.
│   │   ├── agents.ts            # Client-side API functions for fetching agent data.
│   │   ├── billing.ts           # Client-side function to connect to the billing SSE stream.
│   │   ├── billingPlans.ts      # Client-side API function for fetching billing plans.
│   │   ├── chat.ts              # Client-side API functions for chat, including streaming.
│   │   ├── client/              # Auto-generated API client from the OpenAPI specification.
│   │   │   ├── client/          # Core files for the generated API client.
│   │   │   │   ├── client.gen.ts # The main generated API client logic.
│   │   │   │   ├── index.ts     # Barrel file for the generated client.
│   │   │   │   ├── types.gen.ts # Generated request and response types for the client.
│   │   │   │   └── utils.gen.ts # Generated utilities for the client.
│   │   │   ├── client.gen.ts    # Main generated API client configuration.
│   │   │   ├── core/            # Core utilities for the generated API client.
│   │   │   │   ├── auth.gen.ts  # Generated authentication helpers.
│   │   │   │   ├── bodySerializer.gen.ts # Generated body serialization helpers.
│   │   │   │   ├── params.gen.ts # Generated parameter building helpers.
│   │   │   │   ├── pathSerializer.gen.ts # Generated path serialization helpers.
│   │   │   │   ├── queryKeySerializer.gen.ts # Generated query key serialization helpers.
│   │   │   │   ├── serverSentEvents.gen.ts # Generated SSE client helpers.
│   │   │   │   ├── types.gen.ts # Generated core client types.
│   │   │   │   └── utils.gen.ts # Generated core client utilities.
│   │   │   ├── index.ts         # Barrel file re-exporting generated client parts.
│   │   │   ├── sdk.gen.ts       # Generated SDK functions for each API endpoint.
│   │   │   └── types.gen.ts     # Generated TypeScript types from the OpenAPI schema.
│   │   ├── config.ts            # Re-exports the generated API client configuration.
│   │   ├── conversations.ts     # Client-side API functions for managing conversations.
│   │   ├── session.ts           # Client-side API functions for managing user sessions.
│   │   └── tools.ts             # Client-side API function for fetching available tools.
│   ├── auth/                    # Authentication-related helpers and utilities.
│   │   ├── clientMeta.ts        # Client-side utility to read and parse session metadata cookie.
│   │   ├── cookies.ts           # Server-side utilities for managing auth cookies.
│   │   └── session.ts           # Server-side session management logic.
│   ├── chat/                    # Client-side logic and hooks for the chat feature.
│   │   ├── __tests__/           # Tests for the chat controller and utilities.
│   │   │   ├── testUtils.tsx    # Utility functions for chat-related tests.
│   │   │   ├── useChatController.integration.test.tsx # Integration tests for the useChatController hook.
│   │   │   └── useChatController.test.tsx # Unit tests for the useChatController hook.
│   │   ├── types.ts             # TypeScript types and interfaces for the chat feature.
│   │   └── useChatController.ts # Core state management hook for the chat interface.
│   ├── config.ts                # Application-wide configuration constants.
│   ├── queries/                 # TanStack Query hooks for data fetching and caching.
│   │   ├── agents.ts            # React Query hooks for fetching agent data.
│   │   ├── billing.ts           # React Query hook for the billing event stream.
│   │   ├── billingPlans.ts      # React Query hooks for fetching billing plans.
│   │   ├── billingSubscriptions.ts # React Query hooks for managing tenant subscriptions.
│   │   ├── chat.ts              # React Query mutation hook for sending chat messages.
│   │   ├── conversations.ts     # React Query hooks for fetching and managing conversations.
│   │   ├── keys.ts              # Centralized TanStack Query keys for cache management.
│   │   ├── session.ts           # Hook for managing silent session refresh.
│   │   └── tools.ts             # React Query hooks for fetching tools.
│   ├── server/                  # Server-side logic, intended for Server Components and Actions.
│   │   ├── apiClient.ts         # Creates an authenticated API client for server-side use.
│   │   ├── services/            # Service layer for interacting with the backend API from the server.
│   │   │   ├── agents.ts        # Server-side service for agent-related API calls.
│   │   │   ├── auth.ts          # Server-side service for core authentication API calls.
│   │   │   ├── auth/            # Server-side services for authentication API calls.
│   │   │   │   ├── email.ts     # Server-side service for email verification API calls.
│   │   │   │   ├── passwords.ts # Server-side service for password management API calls.
│   │   │   │   ├── serviceAccounts.ts # Server-side service for service account API calls.
│   │   │   │   ├── sessions.ts  # Server-side service for session management API calls.
│   │   │   │   └── signup.ts    # Server-side service for user/tenant registration API calls.
│   │   │   ├── billing.ts       # Server-side service for billing-related API calls.
│   │   │   ├── chat.ts          # Server-side service for chat-related API calls.
│   │   │   ├── conversations.ts # Server-side service for conversation-related API calls.
│   │   │   ├── health.ts        # Server-side service for health check API calls.
│   │   │   └── tools.ts         # Server-side service for tool-related API calls.
│   │   └── streaming/           # Server-side logic for handling streaming data.
│   │       └── chat.ts          # Server-side logic for handling chat streaming in Server Actions.
│   ├── types/                   # Shared type definitions for the application.
│   │   ├── auth.ts              # Type definitions for authentication tokens and sessions.
│   │   └── billing.ts           # Type definitions for billing entities.
│   └── utils.ts                 # General utility functions, including Tailwind class merging.
├── middleware.ts                # Next.js middleware for authentication and route protection.
├── next.config.ts               # Next.js project configuration.
├── openapi-ts.config.ts         # Configuration for generating the API client from an OpenAPI spec.
├── playwright.config.ts         # Playwright end-to-end testing configuration.
├── pnpm-lock.yaml               # PNPM lockfile for dependency version management.
├── postcss.config.mjs           # PostCSS configuration for CSS processing, including Tailwind CSS.
├── public/                      # Static assets like images, fonts, and icons.
├── tailwind.config.ts           # Tailwind CSS theme and plugin configuration.
├── tests/                       # End-to-end tests using Playwright.
│   └── auth-smoke.spec.ts       # End-to-end smoke test for the authentication flow.
├── types/                       # Global TypeScript type definitions for the application.
│   ├── agents.ts                # TypeScript types for AI agents.
│   ├── billing.ts               # TypeScript types for billing entities and events.
│   ├── conversations.ts         # TypeScript types for conversations and messages.
│   ├── session.ts               # TypeScript types for user sessions.
│   └── tools.ts                 # TypeScript types for agent tools.
├── vitest.config.ts             # Vitest unit and component testing configuration.
└── vitest.setup.ts              # Setup file for Vitest tests, extending Jest DOM matchers.