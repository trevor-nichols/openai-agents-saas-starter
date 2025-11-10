.
├── app/                         # Next.js application directory containing routes and layouts
│   ├── (agent)/                 # Route group for the main agent chat interface
│   │   ├── actions.ts           # Server Actions for chat streaming and conversation management
│   │   ├── layout.tsx           # Layout for agent pages, handles silent session refresh
│   │   └── page.tsx             # The main agent chat page UI and client-side logic
│   ├── (auth)/                  # Route group for authentication pages
│   │   └── login/               # Contains the login route
│   │       └── page.tsx         # The login page component
│   ├── actions/                 # Contains global Server Actions
│   │   └── auth.ts              # Server Actions for login, logout, and session refresh
│   ├── api/                     # API route handlers (backend for frontend)
│   │   ├── auth/                # Authentication-related API routes
│   │   │   ├── refresh/         # Route for refreshing authentication tokens
│   │   │   │   └── route.ts     # API endpoint for handling token refresh requests
│   │   │   └── session/         # Route for fetching current session data
│   │   │       └── route.ts     # API endpoint for providing current session status
│   │   ├── billing/             # Billing-related API routes
│   │   │   └── stream/          # Route for the real-time billing event stream
│   │   │       └── route.ts     # Proxies the SSE stream for billing events from the backend
│   │   ├── chat/                # Chat-related API routes
│   │   │   └── stream/          # Route for the real-time chat message stream
│   │   │       └── route.ts     # Proxies the SSE stream for chat messages from the backend
│   │   ├── conversations/       # Conversation-related API routes
│   │   │   ├── route.test.ts    # Unit tests for the conversations list API endpoint
│   │   │   └── route.ts         # API endpoint for listing user conversations
│   ├── layout.tsx               # Root layout for the entire application
│   └── providers.tsx            # Client-side providers, primarily for React Query
├── components/                  # Reusable React components
│   ├── agent/                   # Components for the agent/chat interface
│   │   ├── ChatInterface.tsx    # Renders the chat message history and input form
│   │   └── ConversationSidebar.tsx # Sidebar for listing conversations and starting new ones
│   ├── auth/                    # Authentication-related components
│   │   ├── LoginForm.tsx        # The user login form component
│   │   ├── LogoutButton.tsx     # A button to trigger the user logout action
│   │   └── SilentRefresh.tsx    # Component to handle silent authentication token refresh
│   ├── billing/                 # Billing-related components
│   │   ├── BillingEventsPanel.tsx # Displays a real-time feed of billing events
│   │   └── __tests__/           # Contains tests for billing components
│   │       └── BillingEventsPanel.test.tsx # Unit test for the BillingEventsPanel component
├── eslint.config.mjs            # ESLint configuration file
├── hooks/                       # Legacy custom React hooks (functionality moved to lib/queries)
│   ├── useBillingStream.ts      # Hook for managing the real-time billing event stream
│   ├── useConversations.ts      # Hook for fetching and managing the list of conversations
│   └── useSilentRefresh.ts      # Hook for managing silent session token refresh logic
├── lib/                         # Core logic, API clients, and utilities
│   ├── api/                     # API abstraction layer
│   │   ├── billing.ts           # Functions for connecting to the billing event stream
│   │   ├── client/              # Auto-generated OpenAPI client directory
│   │   │   ├── client/          # Sub-directory for the core generated client
│   │   │   │   ├── client.gen.ts # The core generated fetch client implementation
│   │   │   │   ├── index.ts     # Exports core client types and utilities
│   │   │   │   ├── types.gen.ts # Generated core client type definitions
│   │   │   │   └── utils.gen.ts # Generated utility functions for the client
│   │   │   ├── client.gen.ts    # Main generated API client instance
│   │   │   ├── core/            # Generated core utilities for the API client
│   │   │   │   ├── auth.gen.ts  # Handles authentication scheme logic
│   │   │   │   ├── bodySerializer.gen.ts # Serializes request bodies
│   │   │   │   ├── params.gen.ts # Handles client-side parameter building
│   │   │   │   ├── pathSerializer.gen.ts # Serializes parameters into URL paths
│   │   │   │   ├── queryKeySerializer.gen.ts # Helper for creating stable query keys
│   │   │   │   ├── serverSentEvents.gen.ts # SSE client implementation
│   │   │   │   ├── types.gen.ts # Core generated types
│   │   │   │   └── utils.gen.ts # Core generated utility functions
│   │   │   ├── index.ts         # Main entrypoint for the generated SDK
│   │   │   ├── sdk.gen.ts       # Generated API methods for each endpoint
│   │   │   └── types.gen.ts     # TypeScript types generated from the OpenAPI schema
│   │   ├── config.ts            # Exports the configured auto-generated API client
│   │   ├── conversations.ts     # API functions for fetching and managing conversations
│   │   ├── session.ts           # API functions for fetching and refreshing sessions
│   │   └── streaming.ts         # API function for handling the chat SSE stream
│   ├── auth/                    # Authentication logic and utilities
│   │   ├── clientMeta.ts        # Client-side helper to read session metadata from cookies
│   │   ├── cookies.ts           # Server-side helpers for managing auth cookies
│   │   ├── http.ts              # Authenticated fetch wrapper for server-side use
│   │   └── session.ts           # Server-side session management functions
│   ├── config.ts                # Global application configuration and constants
│   ├── queries/                 # Modern data-fetching hooks using TanStack Query
│   │   ├── billing.ts           # Custom hook for managing the billing SSE stream
│   │   ├── conversations.ts     # TanStack Query hook for managing conversation data
│   │   ├── keys.ts              # Centralized query keys for TanStack Query
│   │   └── session.ts           # Custom hook for handling silent session refresh
│   ├── types/                   # Shared TypeScript type definitions
│   │   └── auth.ts              # Types related to authentication and user sessions
│   └── utils.ts                 # General utility functions (e.g., `cn` for classnames)
├── middleware.ts                # Next.js middleware for route protection
├── next.config.ts               # Next.js framework configuration
├── openapi-ts.config.ts         # Configuration for the openapi-ts client generator
├── playwright.config.ts         # Configuration for Playwright end-to-end tests
├── pnpm-lock.yaml               # PNPM lockfile for dependency management
├── postcss.config.mjs           # PostCSS configuration for Tailwind CSS
├── public/                      # Static assets served by the application
│   ├── file.svg                 # SVG icon asset
│   ├── globe.svg                # SVG icon asset
│   ├── next.svg                 # Next.js logo SVG
│   ├── vercel.svg               # Vercel logo SVG
│   └── window.svg               # SVG icon asset
├── tailwind.config.ts           # Tailwind CSS theme and plugin configuration
├── tests/                       # End-to-end tests directory
│   └── auth-smoke.spec.ts       # Playwright test for the login, chat, and logout flow
├── types/                       # Global TypeScript type definitions
│   ├── billing.ts               # Types for billing events and data structures
│   ├── conversations.ts         # Types for conversation data structures
│   └── session.ts               # Types for session-related data
├── vitest.config.ts             # Vitest (unit testing framework) configuration
└── vitest.setup.ts              # Setup file for Vitest tests, e.g., for jest-dom matchers