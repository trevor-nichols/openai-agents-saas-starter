.
├── app/                           # Next.js App Router directory for pages and layouts
│   ├── (agent)/                   # Route group for the main agent chat application UI
│   │   ├── actions.ts             # Server Actions for chat streaming and fetching conversations
│   │   ├── layout.tsx             # Layout for agent pages, handles silent auth refresh
│   │   └── page.tsx               # Main page for the chat agent interface
│   ├── (auth)/                    # Route group for authentication pages
│   │   └── login/                 # Directory for the login page
│   │       └── page.tsx           # The login page component
│   ├── actions/                   # Contains application-wide Server Actions
│   │   └── auth.ts                # Server Actions for handling login, logout, and refresh
│   ├── api/                       # API route handlers (Next.js backend)
│   │   ├── auth/                  # Authentication-related API routes
│   │   │   ├── refresh/           # API route for refreshing access tokens
│   │   │   │   └── route.ts       # Route handler for POSTing to refresh a session
│   │   │   └── session/           # API route to get current session info
│   │   │       └── route.ts       # Route handler for GETting the current session
│   │   └── chat/                  # Chat-related API routes
│   │       └── stream/            # API route for streaming chat responses
│   │           └── route.ts       # Route handler to proxy chat stream requests to the backend API
│   └── layout.tsx                 # Root layout for the entire application
├── components/                    # Reusable React components
│   ├── agent/                     # Components specific to the agent chat interface
│   │   ├── ChatInterface.tsx      # Component for displaying messages and the input form
│   │   └── ConversationSidebar.tsx# Component for the sidebar listing conversations
│   └── auth/                      # Authentication-related components
│       ├── LoginForm.tsx          # The user login form component
│       ├── LogoutButton.tsx       # Button component to trigger the logout action
│       └── SilentRefresh.tsx      # Client component to initiate silent token refresh
├── eslint.config.mjs              # ESLint configuration file
├── hooks/                         # Custom React hooks
│   ├── useConversations.ts        # Hook for managing conversation list state and fetching
│   └── useSilentRefresh.ts        # Hook to handle periodic, silent session token refreshing
├── lib/                           # Core logic, utilities, and libraries
│   ├── api/                       # Modules for interacting with the backend API
│   │   ├── client/                # Auto-generated API client from OpenAPI specification
│   │   │   ├── client/            # Core files for the generated client logic
│   │   │   │   ├── client.gen.ts  # Auto-generated core HTTP client logic
│   │   │   │   ├── index.ts       # Auto-generated entrypoint for client core utilities
│   │   │   │   ├── types.gen.ts   # Auto-generated core TypeScript types for the client
│   │   │   │   └── utils.gen.ts   # Auto-generated utility functions for the client
│   │   │   ├── client.gen.ts      # Auto-generated main client instance
│   │   │   ├── core/              # Low-level utilities for the generated client
│   │   │   │   ├── auth.gen.ts    # Auto-generated authentication helpers
│   │   │   │   ├── bodySerializer.gen.ts# Auto-generated request body serialization logic
│   │   │   │   ├── params.gen.ts  # Auto-generated parameter building logic
│   │   │   │   ├── pathSerializer.gen.ts# Auto-generated URL path serialization logic
│   │   │   │   ├── queryKeySerializer.gen.ts# Auto-generated query key serialization logic
│   │   │   │   ├── serverSentEvents.gen.ts# Auto-generated SSE client logic
│   │   │   │   ├── types.gen.ts   # Auto-generated core internal types
│   │   │   │   └── utils.gen.ts   # Auto-generated core internal utilities
│   │   │   ├── index.ts           # Auto-generated main entry point for the client SDK
│   │   │   ├── sdk.gen.ts         # Auto-generated functions for each API endpoint
│   │   │   └── types.gen.ts       # Auto-generated TypeScript types for API models
│   │   ├── config.ts              # Exports the auto-generated API client instance
│   │   └── streaming.ts           # Client-side utility for handling chat SSE streams
│   ├── auth/                      # Authentication logic modules
│   │   ├── cookies.ts             # Server-side utilities for managing auth cookies
│   │   ├── http.ts                # Server-side authenticated fetch wrapper for API calls
│   │   └── session.ts             # Server-side functions for session management (login, refresh)
│   ├── config.ts                  # Global application configuration constants
│   └── types/                     # Shared TypeScript type definitions
│       └── auth.ts                # Type definitions for authentication tokens and session
├── middleware.ts                  # Next.js middleware for route protection
├── next.config.ts                 # Next.js framework configuration
├── openapi-ts.config.ts           # Configuration for @hey-api/openapi-ts client generator
├── playwright.config.ts           # Configuration for Playwright end-to-end tests
├── postcss.config.mjs             # PostCSS configuration for Tailwind CSS
├── tailwind.config.ts             # Tailwind CSS configuration file
└── tests/                         # End-to-end and integration tests
    └── auth-smoke.spec.ts         # Playwright smoke test for the login/logout flow