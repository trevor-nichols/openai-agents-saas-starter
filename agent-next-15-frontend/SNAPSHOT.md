.
├── app/                                 # Main Next.js application directory with routes and logic.
│   ├── (agent)/                         # Route group for the main agent/chat interface.
│   │   ├── actions.ts                   # Server Actions for chat streaming and fetching conversations.
│   │   ├── layout.tsx                   # Layout for agent pages, including silent auth refresh.
│   │   └── page.tsx                     # Main page component for the agent chat interface.
│   ├── (auth)/                          # Route group for authentication pages.
│   │   └── login/                       # Directory for the login page.
│   │       └── page.tsx                 # The login page UI component.
│   ├── actions/                         # Directory for application-wide Server Actions.
│   │   └── auth.ts                      # Server Actions for login, logout, and silent refresh.
│   ├── api/                             # API route handlers for the Next.js application.
│   │   ├── auth/                        # API routes related to authentication.
│   │   │   ├── refresh/                 # API route for refreshing session tokens.
│   │   │   │   └── route.ts             # Route handler for POSTing to refresh the session.
│   │   │   └── session/                 # API route for fetching current session info.
│   │   │       └── route.ts             # Route handler for GETting the current session.
│   │   ├── billing/                     # API routes for billing features.
│   │   │   └── stream/                  # API route for the billing event stream.
│   │   │       └── route.ts             # Route handler that proxies the billing SSE stream from the backend.
│   │   ├── chat/                        # API routes related to chat functionality.
│   │   │   └── stream/                  # API route for streaming chat messages.
│   │   │       └── route.ts             # Route handler that proxies the chat SSE stream from the backend.
│   │   ├── conversations/               # API routes for conversation management.
│   │   │   ├── route.test.ts            # Unit tests for the conversations API route.
│   │   │   └── route.ts                 # Route handler for listing conversations.
│   └── layout.tsx                       # Root layout for the entire application.
├── components/                          # Reusable React components.
│   ├── agent/                           # Components for the agent chat interface.
│   │   ├── ChatInterface.tsx            # Component for displaying messages and the input form.
│   │   └── ConversationSidebar.tsx      # Component for the sidebar listing conversations.
│   ├── auth/                            # Components related to authentication.
│   │   ├── LoginForm.tsx                # The UI component for the login form.
│   │   ├── LogoutButton.tsx             # A client component button to trigger the logout action.
│   │   └── SilentRefresh.tsx            # Component that triggers the silent session refresh hook.
│   └── billing/                         # Components related to billing information.
│       ├── BillingEventsPanel.tsx       # Displays a real-time stream of billing events.
│       └── __tests__/                   # Directory for billing component tests.
│           └── BillingEventsPanel.test.tsx # Unit tests for the BillingEventsPanel component.
├── eslint.config.mjs                    # ESLint configuration file for code linting.
├── hooks/                               # Custom React hooks for shared logic.
│   ├── useBillingStream.ts              # Hook to manage the real-time billing event stream.
│   ├── useConversations.ts              # Hook for fetching and managing the list of conversations.
│   └── useSilentRefresh.ts              # Hook to handle automatic background session refreshing.
├── lib/                                 # Shared libraries, helpers, and utilities.
│   ├── api/                             # Utilities and configuration for API communication.
│   │   ├── client/                      # Auto-generated OpenAPI client directory.
│   │   │   ├── client/                  # Core files for the generated API client.
│   │   │   │   ├── client.gen.ts        # Auto-generated core client creation logic.
│   │   │   │   ├── index.ts             # Auto-generated barrel file for client core files.
│   │   │   │   ├── types.gen.ts         # Auto-generated types for the client's internal options.
│   │   │   │   └── utils.gen.ts         # Auto-generated client utility functions.
│   │   │   ├── client.gen.ts            # Auto-generated client instance and configuration.
│   │   │   ├── core/                    # Auto-generated core utilities for the API client.
│   │   │   │   ├── auth.gen.ts          # Auto-generated authentication helpers.
│   │   │   │   ├── bodySerializer.gen.ts # Auto-generated request body serialization logic.
│   │   │   │   ├── params.gen.ts        # Auto-generated parameter handling logic.
│   │   │   │   ├── pathSerializer.gen.ts # Auto-generated path serialization logic.
│   │   │   │   ├── queryKeySerializer.gen.ts # Auto-generated query key serialization logic.
│   │   │   │   ├── serverSentEvents.gen.ts # Auto-generated Server-Sent Events handling logic.
│   │   │   │   ├── types.gen.ts         # Auto-generated core type definitions.
│   │   │   │   └── utils.gen.ts         # Auto-generated core utility functions.
│   │   │   ├── index.ts                 # Auto-generated barrel file exporting the SDK.
│   │   │   ├── sdk.gen.ts               # Auto-generated SDK functions for API endpoints.
│   │   │   └── types.gen.ts             # Auto-generated TypeScript types from the OpenAPI schema.
│   │   ├── config.ts                    # Exports the configured API client.
│   │   └── streaming.ts                 # Client-side utility for handling chat streaming via SSE.
│   ├── auth/                            # Authentication-related helpers and logic.
│   │   ├── clientMeta.ts                # Client-side utility for reading session metadata from cookies.
│   │   ├── cookies.ts                   # Server-side utilities for managing auth cookies.
│   │   ├── http.ts                      # Server-side authenticated fetch wrapper.
│   │   └── session.ts                   # Server-side session management functions (login, refresh).
│   ├── config.ts                        # Application-wide configuration and constants.
│   └── types/                           # Shared type definitions for the library.
│       └── auth.ts                      # TypeScript types for authentication data.
├── middleware.ts                        # Next.js middleware for route protection and redirection.
├── next.config.ts                       # Configuration file for the Next.js framework.
├── openapi-ts.config.ts                 # Configuration for the openapi-ts client generator.
├── playwright.config.ts                 # Configuration for Playwright end-to-end tests.
├── pnpm-lock.yaml                       # PNPM lockfile for reproducible dependency installation.
├── postcss.config.mjs                   # Configuration for PostCSS, used by Tailwind CSS.
├── public/                              # Directory for static assets.
│   ├── file.svg                         # Static SVG asset.
│   ├── globe.svg                        # Static SVG asset.
│   ├── next.svg                         # Static Next.js logo SVG.
│   ├── vercel.svg                       # Static Vercel logo SVG.
│   └── window.svg                       # Static SVG asset.
├── tailwind.config.ts                   # Configuration file for Tailwind CSS.
├── tests/                               # Directory for end-to-end tests.
│   └── auth-smoke.spec.ts               # Playwright smoke test for the authentication flow.
├── types/                               # Global TypeScript type definitions.
│   └── conversations.ts                 # Type definitions for conversation objects.
├── vitest.config.ts                     # Configuration file for the Vitest testing framework.
└── vitest.setup.ts                      # Setup file for Vitest, importing jest-dom matchers.