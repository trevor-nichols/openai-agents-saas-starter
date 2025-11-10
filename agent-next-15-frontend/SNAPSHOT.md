.
├── app/                                 # Main Next.js application directory (App Router).
│   ├── (agent)/                         # Route group for the primary agent chat interface.
│   │   ├── actions.ts                   # Server Actions for chat streaming and conversation listing.
│   │   ├── layout.tsx                   # Layout for agent pages, includes silent session refresh.
│   │   └── page.tsx                     # Main page for the agent chat interface.
│   ├── (auth)/                          # Route group for authentication pages.
│   │   └── login/                       # Contains the login page route.
│   │       └── page.tsx                 # The user login page component.
│   ├── actions/                         # Contains globally available Server Actions.
│   │   └── auth.ts                      # Server Actions for user authentication (login, logout, refresh).
│   ├── api/                             # API route handlers (backend for the frontend).
│   │   ├── auth/                        # Authentication-related API endpoints.
│   │   │   ├── refresh/                 # Endpoint for refreshing authentication tokens.
│   │   │   │   └── route.ts             # Route handler for POST /api/auth/refresh.
│   │   │   └── session/                 # Endpoint for fetching current session data.
│   │   │       └── route.ts             # Route handler for GET /api/auth/session.
│   │   ├── billing/                     # Billing-related API endpoints.
│   │   │   ├── plans/                   # Endpoint for listing billing plans.
│   │   │   │   └── route.ts             # Route handler for GET /api/billing/plans.
│   │   │   └── stream/                  # Endpoint for streaming billing events.
│   │   │       └── route.ts             # Route handler for GET /api/billing/stream (SSE).
│   │   ├── chat/                        # Chat-related API endpoints.
│   │   │   └── stream/                  # Endpoint for streaming chat messages.
│   │   │       └── route.ts             # Route handler for POST /api/chat/stream (SSE).
│   │   ├── conversations/               # Conversation-related API endpoints.
│   │   │   ├── route.test.ts            # Unit tests for the conversations API route.
│   │   │   └── route.ts                 # Route handler for GET /api/conversations.
│   │   └── tools/                       # Tool-related API endpoints.
│   │       └── route.ts                 # Route handler for GET /api/tools.
│   ├── layout.tsx                       # Root layout for the entire application.
│   └── providers.tsx                    # Client-side providers, sets up React Query.
├── components/                          # Reusable React components.
│   ├── agent/                           # Components for the agent chat interface.
│   │   ├── ChatInterface.tsx            # Component for displaying chat messages and the input form.
│   │   └── ConversationSidebar.tsx      # Sidebar component for listing and managing conversations.
│   ├── auth/                            # Authentication-related components.
│   │   ├── LoginForm.tsx                # The user login form component.
│   │   ├── LogoutButton.tsx             # Button to trigger the user logout action.
│   │   └── SilentRefresh.tsx            # Component to trigger the silent session refresh hook.
│   └── billing/                         # Billing-related components.
│       ├── BillingEventsPanel.tsx       # Panel to display real-time billing events from a stream.
│       └── __tests__/                   # Test suite for billing components.
│           └── BillingEventsPanel.test.tsx # Unit tests for the BillingEventsPanel component.
├── eslint.config.mjs                    # ESLint configuration file (flat config format).
├── hooks/                               # Custom React hooks (older implementations).
│   ├── useBillingStream.ts              # Custom hook to connect to and manage the billing SSE stream.
│   ├── useConversations.ts              # Custom hook to fetch and manage conversation list state.
│   └── useSilentRefresh.ts              # Custom hook to manage silent session token refreshing.
├── lib/                                 # Core application logic, utilities, and API services.
│   ├── api/                             # Client-side data fetching and API client configuration.
│   │   ├── billing.ts                   # Client-side function to connect to the billing events stream.
│   │   ├── billingPlans.ts              # Client-side function to fetch available billing plans.
│   │   ├── client/                      # Auto-generated API client from OpenAPI specification.
│   │   │   ├── client/                  # Core files for the generated client instance.
│   │   │   │   ├── client.gen.ts        # The main generated fetch client logic.
│   │   │   │   ├── index.ts             # Exports for the client core.
│   │   │   │   ├── types.gen.ts         # Type definitions for the client instance.
│   │   │   │   └── utils.gen.ts         # Utility functions for the client instance.
│   │   │   ├── client.gen.ts            # Instantiates and configures the auto-generated API client.
│   │   │   ├── core/                    # Low-level helpers for the auto-generated client.
│   │   │   │   ├── auth.gen.ts          # Authentication helpers for the API client.
│   │   │   │   ├── bodySerializer.gen.ts # Functions for serializing request bodies.
│   │   │   │   ├── params.gen.ts        # Utilities for building client parameters.
│   │   │   │   ├── pathSerializer.gen.ts # Functions for serializing URL path parameters.
│   │   │   │   ├── queryKeySerializer.gen.ts # Utilities for creating stable query keys.
│   │   │   │   ├── serverSentEvents.gen.ts # Helper for handling Server-Sent Events streams.
│   │   │   │   ├── types.gen.ts         # Core type definitions for the API client.
│   │   │   │   └── utils.gen.ts         # General utilities for the API client.
│   │   │   ├── index.ts                 # Main entry point for the auto-generated client SDK.
│   │   │   ├── sdk.gen.ts               # Auto-generated functions for each API endpoint (the SDK).
│   │   │   └── types.gen.ts             # Auto-generated TypeScript types from the OpenAPI schema.
│   │   ├── config.ts                    # Exports the configured auto-generated API client.
│   │   ├── conversations.ts             # API layer functions for fetching and managing conversations.
│   │   ├── session.ts                   # API layer functions for fetching and refreshing user sessions.
│   │   ├── streaming.ts                 # Client-side async generator to stream chat responses.
│   │   └── tools.ts                     # API layer function for fetching available tools.
│   ├── auth/                            # Authentication logic and utilities.
│   │   ├── clientMeta.ts                # Client-side utility to read session metadata from cookies.
│   │   ├── cookies.ts                   # Server-side helpers for managing authentication cookies.
│   │   └── session.ts                   # Server-side session management functions (login, refresh, etc.).
│   ├── chat/                            # Types related to chat functionality.
│   │   └── types.ts                     # TypeScript types for chat streaming.
│   ├── config.ts                        # Global application configuration constants.
│   ├── queries/                         # Reusable TanStack Query hooks.
│   │   ├── billing.ts                   # Hook for managing the real-time billing event stream.
│   │   ├── billingPlans.ts              # TanStack Query hook for fetching billing plans.
│   │   ├── conversations.ts             # TanStack Query hook for fetching and managing conversations.
│   │   ├── keys.ts                      # Centralized definitions for TanStack Query keys.
│   │   ├── session.ts                   # Hook for managing silent session token refresh logic.
│   │   └── tools.ts                     # TanStack Query hook for fetching available tools.
│   ├── server/                          # Server-side only logic and services.
│   │   ├── apiClient.ts                 # Factory for creating an authenticated server-side API client.
│   │   ├── services/                    # Service layer abstracting backend API calls.
│   │   │   ├── auth.ts                  # Server-side services for authentication endpoints.
│   │   │   ├── billing.ts               # Server-side services for billing endpoints.
│   │   │   ├── chat.ts                  # Server-side services for chat endpoints.
│   │   │   ├── conversations.ts         # Server-side service for conversations endpoint.
│   │   │   └── tools.ts                 # Server-side service for tools endpoint.
│   │   └── streaming/                   # Server-side logic for handling streams.
│   │       └── chat.ts                  # Server-side helper to stream chat from backend to client.
│   ├── types/                           # Shared application-level type definitions.
│   │   └── auth.ts                      # TypeScript types for authentication tokens and sessions.
│   └── utils.ts                         # General utility functions (e.g., `cn` for classnames).
├── middleware.ts                        # Next.js middleware for route protection and authentication checks.
├── next.config.ts                       # Next.js configuration file.
├── openapi-ts.config.ts                 # Configuration for the openapi-ts API client generator.
├── playwright.config.ts                 # Configuration file for Playwright end-to-end tests.
├── pnpm-lock.yaml                       # PNPM lockfile for dependency management.
├── postcss.config.mjs                   # PostCSS configuration, used for Tailwind CSS.
├── public/                              # Static assets that are publicly accessible.
│   ├── file.svg                         # SVG icon asset.
│   ├── globe.svg                        # SVG icon asset.
│   ├── next.svg                         # Next.js logo SVG.
│   ├── vercel.svg                       # Vercel logo SVG.
│   └── window.svg                       # SVG icon asset.
├── tailwind.config.ts                   # Tailwind CSS theme and plugin configuration.
├── tests/                               # End-to-end tests directory.
│   └── auth-smoke.spec.ts               # Playwright test for the user login, chat, and logout flow.
├── types/                               # Global TypeScript type definitions for the application.
│   ├── billing.ts                       # TypeScript types related to billing.
│   ├── conversations.ts                 # TypeScript types related to conversations.
│   ├── session.ts                       # TypeScript types related to user sessions.
│   └── tools.ts                         # TypeScript types related to agent tools.
├── vitest.config.ts                     # Vitest configuration for unit and component testing.
└── vitest.setup.ts                      # Setup file for Vitest tests (e.g., importing jest-dom).