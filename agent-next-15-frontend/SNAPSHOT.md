.
├── app/                           # Next.js App Router directory for pages, layouts, and API routes
│   ├── (agent)/                   # Route group for the main agent chat application UI
│   │   ├── actions.ts             # Server Actions for chat streaming and fetching conversations
│   │   ├── layout.tsx             # Layout for agent pages, includes silent token refresh
│   │   └── page.tsx               # Main page component for the agent chat interface
│   ├── (auth)/                    # Route group for authentication pages
│   │   └── login/                 # Contains the login page
│   │       └── page.tsx           # The login page component
│   ├── actions/                   # Contains global Server Actions
│   │   └── auth.ts                # Server Actions for login, logout, and silent refresh
│   ├── api/                       # API route handlers that run on the server
│   │   ├── auth/                  # Authentication-related API routes
│   │   │   ├── refresh/           # API route for refreshing access tokens
│   │   │   │   └── route.ts       # Route handler for POST /api/auth/refresh
│   │   │   └── session/           # API route for fetching session data
│   │   │       └── route.ts       # Route handler for GET /api/auth/session
│   │   ├── billing/               # Billing-related API routes
│   │   │   └── stream/            # API route for streaming billing events
│   │   │       └── route.ts       # Route handler for GET /api/billing/stream (SSE proxy)
│   │   ├── chat/                  # Chat-related API routes
│   │   │   └── stream/            # API route for streaming chat messages
│   │   │       └── route.ts       # Route handler for POST /api/chat/stream (SSE proxy)
│   └── layout.tsx                 # Root layout for the entire application
├── components/                    # Reusable React components
│   ├── agent/                     # Components for the agent chat interface
│   │   ├── ChatInterface.tsx      # Renders the chat message history and input form
│   │   └── ConversationSidebar.tsx # Renders the list of conversations and a new chat button
│   ├── auth/                      # Authentication-related components
│   │   ├── LoginForm.tsx          # The user login form component
│   │   ├── LogoutButton.tsx       # A button to trigger the logout action
│   │   └── SilentRefresh.tsx      # Component to trigger the silent auth token refresh hook
│   └── billing/                   # Billing-related components
│       ├── BillingEventsPanel.tsx # Displays real-time billing events from an SSE stream
│       └── __tests__/             # Tests for billing components
│           └── BillingEventsPanel.test.tsx # Unit test for the BillingEventsPanel component
├── eslint.config.mjs              # ESLint configuration for code linting
├── hooks/                         # Custom React hooks for shared logic
│   ├── useBillingStream.ts        # Hook to manage the Server-Sent Events stream for billing
│   ├── useConversations.ts        # Hook to fetch and manage the state of conversation lists
│   └── useSilentRefresh.ts        # Hook to handle automatic background session token refreshing
├── lib/                           # Core application logic, utilities, and API clients
│   ├── api/                       # API communication layer
│   │   ├── client/                # Auto-generated OpenAPI client code
│   │   │   ├── client/            # Core files for the generated API client
│   │   │   │   ├── client.gen.ts  # The main generated fetch client implementation
│   │   │   │   ├── index.ts       # Re-exports core client types and functions
│   │   │   │   ├── types.gen.ts   # Generated TypeScript types for the client's options and responses
│   │   │   │   └── utils.gen.ts   # Generated utility functions for the client (URL building, headers)
│   │   │   ├── client.gen.ts      # Generated API client instance and configuration
│   │   │   ├── core/              # Low-level generated utilities for the API client
│   │   │   │   ├── auth.gen.ts    # Generated authentication helpers
│   │   │   │   ├── bodySerializer.gen.ts # Generated request body serialization helpers
│   │   │   │   ├── params.gen.ts  # Generated parameter building helpers
│   │   │   │   ├── pathSerializer.gen.ts # Generated path parameter serialization helpers
│   │   │   │   ├── queryKeySerializer.gen.ts # Generated query key serialization helpers
│   │   │   │   ├── serverSentEvents.gen.ts # Generated Server-Sent Events handling logic
│   │   │   │   ├── types.gen.ts   # Generated core internal types for the client
│   │   │   │   └── utils.gen.ts   # Generated low-level utility functions
│   │   │   ├── index.ts           # Main entrypoint for the generated client, re-exporting SDK and types
│   │   │   ├── sdk.gen.ts         # Generated functions for each API endpoint
│   │   │   └── types.gen.ts       # Generated TypeScript types from the OpenAPI schema
│   │   ├── config.ts              # Exports the generated API client instance
│   │   └── streaming.ts           # Client-side logic for handling chat SSE stream
│   ├── auth/                      # Authentication-related utilities
│   │   ├── clientMeta.ts          # Client-side utility to read session metadata from cookies
│   │   ├── cookies.ts             # Server-side utilities for managing auth cookies
│   │   ├── http.ts                # Server-side utility for making authenticated API requests
│   │   └── session.ts             # Server-side functions for managing user sessions
│   ├── config.ts                  # Global configuration constants and environment variables
│   └── types/                     # Shared TypeScript type definitions
│       └── auth.ts                # Type definitions for authentication tokens and session data
├── middleware.ts                  # Next.js middleware for route protection
├── next.config.ts                 # Next.js framework configuration
├── openapi-ts.config.ts           # Configuration for the OpenAPI TypeScript client generator
├── playwright.config.ts           # Configuration for Playwright end-to-end tests
├── postcss.config.mjs             # PostCSS configuration, used by Tailwind CSS
├── tailwind.config.ts             # Tailwind CSS configuration
├── tests/                         # End-to-end tests
│   └── auth-smoke.spec.ts         # Playwright smoke test for the authentication flow
├── vitest.config.ts               # Vitest configuration for unit and component testing
└── vitest.setup.ts                # Setup file for Vitest, extending Jest DOM matchers