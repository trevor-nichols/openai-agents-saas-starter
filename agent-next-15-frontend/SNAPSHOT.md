.
├── app/                         # Next.js app directory containing all routes and layouts
│   ├── (app)/                   # Route group for authenticated application pages
│   │   ├── (workspace)/         # Route group for multi-column workspace layouts (e.g., chat)
│   │   │   ├── chat/            # Chat interface route
│   │   │   │   ├── actions.ts   # Server Actions for chat streaming and conversation management
│   │   │   │   └── page.tsx     # Chat workspace page component
│   │   │   └── layout.tsx       # Layout for workspace views providing common structure
│   │   ├── account/             # Routes for user account management
│   │   │   ├── profile/         # User profile page route
│   │   │   │   └── page.tsx     # Page component for the user profile
│   │   │   ├── security/        # User security settings page route
│   │   │   │   └── page.tsx     # Page component for security settings
│   │   │   ├── service-accounts/ # Service account management page route
│   │   │   │   └── page.tsx     # Page component for managing service accounts
│   │   │   └── sessions/        # User session management page route
│   │   │       └── page.tsx     # Page component for managing active sessions
│   │   ├── agents/              # Agents overview page route
│   │   │   └── page.tsx         # Page component for the agents overview
│   │   ├── billing/             # Billing-related page routes
│   │   │   ├── page.tsx         # Main billing overview page component
│   │   │   └── plans/           # Billing plan management page route
│   │   │       └── page.tsx     # Page component for managing billing plans
│   │   ├── conversations/       # Conversation history/archive page route
│   │   │   └── page.tsx         # Page component for the conversations hub
│   │   ├── dashboard/           # Main dashboard page route for authenticated users
│   │   │   └── page.tsx         # Page component for the dashboard overview
│   │   ├── layout.tsx           # Main layout for the authenticated app (sidebar, header)
│   │   ├── page.tsx             # Root page for the authenticated app group, redirects to dashboard
│   │   ├── settings/            # Application settings routes
│   │   │   └── tenant/          # Tenant-specific settings route
│   │   │       └── page.tsx     # Page component for tenant settings
│   │   └── tools/               # Tool catalog page route
│   │       └── page.tsx         # Page component for the tools catalog
│   ├── (auth)/                  # Route group for authentication pages (login, register, etc.)
│   │   ├── _components/         # Private components for the auth layout
│   │   │   └── AuthCard.tsx     # A reusable card component for authentication forms
│   │   ├── email/               # Routes for email-related actions like verification
│   │   │   └── verify/          # Route for verifying a user's email address
│   │   │       ├── VerifyEmailClient.tsx # Client component with logic for email verification
│   │   │       └── page.tsx     # Page component for email verification
│   │   ├── error.tsx            # Error boundary for the authentication route group
│   │   ├── layout.tsx           # Layout for authentication pages (centered card with background)
│   │   ├── loading.tsx          # Loading UI for the authentication route group
│   │   ├── login/               # Login page route
│   │   │   └── page.tsx         # Page component for the login form
│   │   ├── password/            # Routes for password management
│   │   │   ├── forgot/          # "Forgot password" page route
│   │   │   │   └── page.tsx     # Page component for the forgot password form
│   │   │   └── reset/           # "Reset password" page route
│   │   │       └── page.tsx     # Page component for the reset password form
│   │   └── register/            # Registration page route
│   │       └── page.tsx         # Page component for the registration form
│   ├── (marketing)/             # Route group for public-facing marketing pages
│   │   ├── _components/         # Private components for marketing pages
│   │   │   ├── marketing-footer.tsx # Footer component for marketing pages
│   │   │   ├── marketing-header.tsx # Header component for marketing pages
│   │   │   └── nav-links.ts     # Defines navigation links for marketing pages
│   │   ├── features/            # Features page route
│   │   │   └── page.tsx         # Page component for the features overview
│   │   ├── layout.tsx           # Layout for marketing pages, including header and footer
│   │   ├── page.tsx             # The main landing page component
│   │   └── pricing/             # Pricing page route
│   │       └── page.tsx         # Page component for displaying pricing plans
│   ├── actions/                 # Server Actions used by client and server components
│   │   ├── auth/                # Authentication-related server actions
│   │   │   ├── email.ts       # Server actions for email verification
│   │   │   ├── passwords.ts   # Server actions for password management
│   │   │   ├── sessions.ts    # Server actions for session management
│   │   │   └── signup.ts      # Server action for new user/tenant registration
│   │   └── auth.ts              # Core authentication server actions (login, logout, refresh)
│   ├── api/                     # Next.js API route handlers acting as a proxy to the backend
│   │   ├── agents/              # API routes related to agents
│   │   │   ├── [agentName]/     # Dynamic routes for a specific agent
│   │   │   │   └── status/      # Route to get agent status
│   │   │   │       ├── route.test.ts # Test for the agent status API route
│   │   │   │       └── route.ts # API route handler to get an agent's status
│   │   │   ├── route.test.ts    # Test for the agent list API route
│   │   │   └── route.ts         # API route handler to list all agents
│   │   ├── auth/                # API routes for authentication and authorization
│   │   │   ├── email/           # Routes for email-related actions
│   │   │   │   ├── send/        # Route to send a verification email
│   │   │   │   │   ├── route.test.ts # Test for sending verification email
│   │   │   │   │   └── route.ts # API route handler to trigger sending verification email
│   │   │   │   └── verify/      # Route to verify an email token
│   │   │   │       ├── route.test.ts # Test for verifying email token
│   │   │   │       └── route.ts # API route handler to verify an email token
│   │   │   ├── logout/          # Routes for user logout
│   │   │   │   ├── all/         # Route to log out from all sessions
│   │   │   │   │   ├── route.test.ts # Test for logging out of all sessions
│   │   │   │   │   └── route.ts # API route handler to log out of all sessions
│   │   │   │   ├── route.test.ts # Test for logging out of a single session
│   │   │   │   └── route.ts     # API route handler to log out of a single session
│   │   │   ├── password/        # Routes for password management
│   │   │   │   ├── change/      # Route to change a user's password
│   │   │   │   │   ├── route.test.ts # Test for changing password
│   │   │   │   │   └── route.ts # API route handler for changing password
│   │   │   │   ├── confirm/     # Route to confirm a password reset with a token
│   │   │   │   │   ├── route.test.ts # Test for confirming password reset
│   │   │   │   │   └── route.ts # API route handler for confirming password reset
│   │   │   │   ├── forgot/      # Route to request a password reset
│   │   │   │   │   ├── route.test.ts # Test for requesting password reset
│   │   │   │   │   └── route.ts # API route handler for requesting a password reset
│   │   │   │   └── reset/       # Route for an admin to reset a user's password
│   │   │   │       ├── route.test.ts # Test for admin password reset
│   │   │   │       └── route.ts # API route handler for admin password reset
│   │   │   ├── refresh/         # Route to refresh an authentication session
│   │   │   │   └── route.ts     # API route handler for refreshing an access token
│   │   │   ├── register/        # Route for new user registration
│   │   │   │   ├── route.test.ts # Test for user registration
│   │   │   │   └── route.ts     # API route handler for user registration
│   │   │   ├── service-accounts/ # Routes for managing service accounts
│   │   │   │   └── issue/       # Route to issue a new service account token
│   │   │   │       ├── route.test.ts # Test for issuing a service account token
│   │   │   │       └── route.ts # API route handler for issuing a service account token
│   │   │   ├── session/         # Route to get current session information
│   │   │   │   └── route.ts     # API route handler for getting current session info
│   │   │   └── sessions/        # Routes for managing user sessions
│   │   │       ├── [sessionId]/ # Dynamic route for a specific session
│   │   │       │   ├── route.test.ts # Test for revoking a specific session
│   │   │       │   └── route.ts # API route handler to revoke a specific session
│   │   │       ├── route.test.ts # Test for listing user sessions
│   │   │       └── route.ts     # API route handler to list user sessions
│   │   ├── billing/             # API routes for billing information
│   │   │   ├── plans/           # Route to get available billing plans
│   │   │   │   └── route.ts     # API route handler to list billing plans
│   │   │   ├── stream/          # SSE route for billing events
│   │   │   │   └── route.ts     # API route handler for streaming billing events
│   │   │   └── tenants/         # Routes for tenant-specific billing
│   │   │       └── [tenantId]/  # Dynamic routes for a specific tenant
│   │   │           ├── subscription/ # Routes for managing a tenant's subscription
│   │   │           │   ├── cancel/ # Route to cancel a subscription
│   │   │           │   │   ├── route.test.ts # Test for canceling a subscription
│   │   │           │   │   └── route.ts # API route handler for canceling a subscription
│   │   │           │   ├── route.test.ts # Test for subscription management
│   │   │           │   └── route.ts # API route handlers to manage a subscription (GET, POST, PATCH)
│   │   │           └── usage/       # Route for reporting metered usage
│   │   │               ├── route.test.ts # Test for recording usage
│   │   │               └── route.ts # API route handler for recording usage
│   │   ├── chat/                # API routes for chat functionality
│   │   │   ├── route.test.ts    # Test for the non-streaming chat endpoint
│   │   │   ├── route.ts         # API route handler for non-streaming chat messages
│   │   │   └── stream/          # SSE route for streaming chat messages
│   │   │       └── route.ts     # API route handler for streaming chat responses
│   │   ├── conversations/       # API routes for conversations
│   │   │   ├── [conversationId]/ # Dynamic routes for a specific conversation
│   │   │   │   ├── route.test.ts # Test for getting/deleting a conversation
│   │   │   │   └── route.ts     # API route handlers to get or delete a conversation
│   │   │   ├── route.test.ts    # Test for listing conversations
│   │   │   └── route.ts         # API route handler to list conversations
│   │   ├── health/              # API routes for health checks
│   │   │   ├── ready/           # Route for readiness probe
│   │   │   │   ├── route.test.ts # Test for the readiness probe
│   │   │   │   └── route.ts     # API route handler for the readiness probe
│   │   │   ├── route.test.ts    # Test for the liveness probe
│   │   │   └── route.ts         # API route handler for the liveness probe
│   │   └── tools/               # API routes for tools
│   │       └── route.ts         # API route handler to list available tools
│   ├── layout.tsx               # Root layout for the entire application
│   └── providers.tsx            # Client-side context providers (React Query, Theme, etc.)
├── components/                  # Shared, reusable UI components
│   ├── auth/                    # Components specific to authentication flows
│   │   ├── ForgotPasswordForm.tsx # Form for requesting a password reset
│   │   ├── LoginForm.tsx      # Form for user login
│   │   ├── LogoutButton.tsx   # Button component to trigger logout
│   │   ├── RegisterForm.tsx   # Form for new user registration
│   │   ├── ResetPasswordForm.tsx # Form for resetting password with a token
│   │   └── SilentRefresh.tsx  # Client component to handle silent token refresh
│   └── ui/                      # General-purpose UI components (e.g., from shadcn/ui)
│       ├── accordion.tsx        # Accordion component
│       ├── alert-dialog.tsx     # Alert dialog (modal) component
│       ├── alert.tsx            # Alert message component
│       ├── aspect-ratio.tsx     # Aspect ratio container component
│       ├── avatar.tsx           # Avatar component
│       ├── badge.tsx            # Badge component
│       ├── breadcrumb.tsx       # Breadcrumb navigation component
│       ├── button.tsx           # Button component
│       ├── card.tsx             # Card component
│       ├── carousel.tsx         # Carousel component
│       ├── checkbox.tsx         # Checkbox component
│       ├── collapsible.tsx      # Collapsible content component
│       ├── command.tsx          # Command palette component
│       ├── context-menu.tsx     # Context menu component
│       ├── dialog.tsx           # Dialog (modal) component
│       ├── dropdown-menu.tsx    # Dropdown menu component
│       ├── form.tsx             # React Hook Form components and context
│       ├── foundation/          # Custom, foundational UI components for the app's design system
│       │   ├── GlassPanel.tsx   # A panel with a frosted glass effect
│       │   ├── InlineTag.tsx    # A small, pill-shaped tag component
│       │   ├── KeyValueList.tsx # A component for displaying key-value pairs
│       │   ├── SectionHeader.tsx # A standardized header for content sections
│       │   ├── StatCard.tsx     # A card for displaying a single statistic or KPI
│       │   └── index.ts         # Barrel file exporting foundation components
│       ├── hover-card.tsx       # Hover card component
│       ├── input.tsx            # Input field component
│       ├── label.tsx            # Label component for form elements
│       ├── navigation-menu.tsx  # Navigation menu component
│       ├── pagination.tsx       # Pagination component
│       ├── popover.tsx          # Popover component
│       ├── progress.tsx         # Progress bar component
│       ├── radio-group.tsx      # Radio group component
│       ├── resizable.tsx        # Resizable panel component
│       ├── scroll-area.tsx      # Scroll area component with custom scrollbars
│       ├── select.tsx           # Select (dropdown) component
│       ├── separator.tsx        # A horizontal or vertical separator line
│       ├── shadcn-io/           # Curated UI components from shadcn.io/ui and v0.dev
│       │   ├── ai/              # Components specifically designed for AI/chat interfaces
│       │   │   ├── actions.tsx  # Action buttons for chat messages
│       │   │   ├── branch.tsx   # Component for displaying multiple AI response branches
│       │   │   ├── code-block.tsx # A rich code block component with syntax highlighting
│       │   │   ├── conversation.tsx # A scrollable container for chat messages
│       │   │   ├── image.tsx    # Component for displaying AI-generated images
│       │   │   ├── inline-citation.tsx # Component for showing inline citations
│       │   │   ├── loader.tsx   # A loading spinner for AI actions
│       │   │   ├── message.tsx  # Component for rendering a single chat message
│       │   │   ├── prompt-input.tsx # A rich text input for user prompts
│       │   │   ├── reasoning.tsx # A collapsible section to show AI's reasoning steps
│       │   │   ├── response.tsx # Component for rendering Markdown AI responses
│       │   │   ├── source.tsx   # Component for displaying citation sources
│       │   │   ├── suggestion.tsx # Component for displaying suggested prompts
│       │   │   ├── task.tsx     # Component to display an AI's task execution status
│       │   │   ├── tool.tsx     # Component for displaying tool usage by the AI
│       │   │   └── web-preview.tsx # Component for previewing web pages within the UI
│       │   ├── animated-beam/       # Animated beam component for visualizing connections
│       │   │   └── index.tsx    # Main component for the animated beam effect
│       │   ├── animated-testimonials/ # Animated testimonials carousel
│       │   │   └── index.tsx    # Main component for animated testimonials
│       │   ├── animated-tooltip/    # Tooltip with animation effects
│       │   │   └── index.tsx    # Main component for the animated tooltip
│       │   ├── avatar-group/        # Component for displaying a group of avatars
│       │   │   └── index.tsx    # Main component for the avatar group
│       │   ├── code-block/          # A powerful code block component with Shiki for syntax highlighting
│       │   │   ├── index.tsx    # Client-side implementation of the code block
│       │   │   └── server.tsx   # Server-side implementation for pre-rendering highlighted code
│       │   ├── copy-button/         # A dedicated copy-to-clipboard button
│       │   │   └── index.tsx    # Main component for the copy button
│       │   ├── dropzone/            # File dropzone component
│       │   │   └── index.tsx    # Main component for the dropzone
│       │   ├── magnetic/            # Component that creates a magnetic effect on mouse hover
│       │   │   └── index.tsx    # Main component for the magnetic effect
│       │   ├── marquee/             # A scrolling marquee component
│       │   │   └── index.tsx    # Main component for the marquee
│       │   ├── navbar-05/           # A specific style of navigation bar
│       │   │   └── index.tsx    # Main component for the navbar style
│       │   ├── spinner/             # Various spinner and loader components
│       │   │   └── index.tsx    # Main component providing multiple spinner styles
│       │   ├── status/              # A status indicator component
│       │   │   └── index.tsx    # Main component for displaying status with an indicator
│       │   └── video-player/        # A video player component
│       │       └── index.tsx    # Main component for the video player
│       ├── shape-landing-hero.tsx # A hero section component with animated shapes
│       ├── sheet.tsx            # Sheet (slide-over panel) component
│       ├── skeleton.tsx         # Skeleton loader component
│       ├── sonner.tsx           # A wrapper for the Sonner toast notification library
│       ├── states/              # Components for representing different UI states
│       │   ├── EmptyState.tsx   # Component for displaying an empty state
│       │   ├── ErrorState.tsx   # Component for displaying an error state
│       │   ├── SkeletonPanel.tsx # A panel of skeleton loading placeholders
│       │   └── index.ts         # Barrel file exporting state components
│       ├── switch.tsx           # Switch toggle component
│       ├── table.tsx            # Table components (Table, THead, TBody, etc.)
│       ├── tabs.tsx             # Tabs component
│       ├── textarea.tsx         # Textarea component
│       ├── theme-toggle.tsx     # Button to toggle between light and dark themes
│       ├── toggle.tsx           # Toggle button component
│       └── tooltip.tsx          # Tooltip component
│       └── use-toast.ts         # A hook to simplify showing toast notifications
├── eslint.config.mjs            # ESLint configuration file
├── features/                    # High-level feature modules that compose UI components and logic
│   ├── account/                 # Feature components for account management
│   │   ├── ProfilePanel.tsx     # The main panel for the user profile page
│   │   ├── SecurityPanel.tsx    # The main panel for the security settings page
│   │   ├── ServiceAccountsPanel.tsx # The main panel for managing service accounts
│   │   ├── SessionsPanel.tsx    # The main panel for managing user sessions
│   │   └── index.ts             # Barrel file exporting account feature components
│   ├── agents/                  # Feature components for agent management
│   │   ├── AgentsOverview.tsx   # The main component for the agents overview page
│   │   └── index.ts             # Barrel file exporting agents feature components
│   ├── billing/                 # Feature components for billing
│   │   ├── BillingOverview.tsx  # The main component for the billing overview page
│   │   ├── PlanManagement.tsx   # Component for managing subscription plans
│   │   └── index.ts             # Barrel file exporting billing feature components
│   ├── chat/                    # Components that orchestrate the chat feature
│   │   ├── ChatWorkspace.tsx    # The main orchestrator component for the entire chat workspace
│   │   ├── components/          # Sub-components specific to the chat workspace
│   │   │   ├── AgentSwitcher.tsx # Component to select the active agent for a conversation
│   │   │   ├── BillingEventsPanel.tsx # A panel to display live billing events within the chat UI
│   │   │   ├── ChatInterface.tsx # The core chat UI with messages and input
│   │   │   ├── ConversationSidebar.tsx # Sidebar for listing and managing conversations
│   │   │   ├── ToolMetadataPanel.tsx # Panel showing metadata about available tools
│   │   │   └── __tests__/       # Tests for chat components
│   │   │       └── BillingEventsPanel.test.tsx # Test for the BillingEventsPanel component
│   │   └── index.ts             # Barrel file exporting chat feature components
│   ├── conversations/           # Feature components for browsing conversation history
│   │   ├── ConversationDetailDrawer.tsx # Drawer to show the full transcript and details of a conversation
│   │   ├── ConversationsHub.tsx # The main component for the conversations archive page
│   │   └── index.ts             # Barrel file exporting conversations feature components
│   ├── dashboard/               # Feature components for the main dashboard
│   │   ├── DashboardOverview.tsx # The main orchestrator for the dashboard view
│   │   ├── components/          # Sub-components specific to the dashboard
│   │   │   ├── BillingPreview.tsx # A card that shows a preview of billing status
│   │   │   ├── KpiGrid.tsx      # A grid of key performance indicator cards
│   │   │   ├── QuickActions.tsx # A set of quick action links for common tasks
│   │   │   └── RecentConversations.tsx # A list of the most recent conversations
│   │   ├── constants.ts         # Constants used within the dashboard feature
│   │   ├── hooks/               # Hooks specific to the dashboard feature
│   │   │   └── useDashboardData.tsx # Hook to fetch and compose all data needed for the dashboard
│   │   ├── index.ts             # Barrel file exporting dashboard components
│   │   └── types.ts             # Type definitions for the dashboard feature
│   ├── settings/                # Feature components for application settings
│   │   ├── TenantSettingsPanel.tsx # The main panel for tenant-level settings
│   │   └── index.ts             # Barrel file exporting settings feature components
│   └── tools/                   # Feature components for the tools catalog
│       ├── ToolsCatalog.tsx     # The main component for the tools catalog page
│       └── index.ts             # Barrel file exporting tools feature components
├── hooks/                       # Application-wide reusable React hooks
│   ├── useAuthForm.ts           # A generic hook for handling authentication form state and submission
│   ├── useBillingStream.ts      # Hook for subscribing to and managing the billing SSE stream
│   └── useSilentRefresh.ts      # Hook for handling silent authentication token refresh
├── lib/                         # Core logic, utilities, and external service interactions
│   ├── api/                     # Client-side functions for interacting with the application's API
│   │   ├── __tests__/           # Tests for API client functions
│   │   │   └── chat.test.ts     # Tests for the client-side chat API functions
│   │   ├── agents.ts            # Client-side API functions for fetching agent data
│   │   ├── billing.ts           # Client-side API function for connecting to the billing stream
│   │   ├── billingPlans.ts      # Client-side API function for fetching billing plans
│   │   ├── chat.ts              # Client-side API functions for chat, including streaming logic
│   │   ├── client/              # Auto-generated API client from an OpenAPI specification
│   │   │   ├── client/          # Core generated client files
│   │   │   │   ├── client.gen.ts # The main generated HTTP client logic
│   │   │   │   ├── index.ts     # Barrel file for client exports
│   │   │   │   ├── types.gen.ts # Generated type definitions for the client
│   │   │   │   └── utils.gen.ts # Generated utility functions for the client
│   │   │   ├── client.gen.ts    # Entry point for the generated client configuration
│   │   │   ├── core/            # Core utilities for the generated client
│   │   │   │   ├── auth.gen.ts  # Generated authentication helpers
│   │   │   │   ├── bodySerializer.gen.ts # Generated body serialization helpers
│   │   │   │   ├── params.gen.ts # Generated parameter building helpers
│   │   │   │   ├── pathSerializer.gen.ts # Generated path serialization helpers
│   │   │   │   ├── queryKeySerializer.gen.ts # Generated query key serialization helpers
│   │   │   │   ├── serverSentEvents.gen.ts # Generated Server-Sent Events client logic
│   │   │   │   ├── types.gen.ts # Generated core type definitions
│   │   │   │   └── utils.gen.ts # Generated core utility functions
│   │   │   ├── index.ts         # Barrel file exporting the generated client SDK and types
│   │   │   ├── sdk.gen.ts       # Generated functions for each API endpoint
│   │   │   └── types.gen.ts     # Generated TypeScript types from the OpenAPI schema
│   │   ├── config.ts            # Configuration for the generated API client
│   │   ├── conversations.ts     # Client-side API functions for fetching conversation data
│   │   ├── session.ts           # Client-side API functions for managing the user session
│   │   └── tools.ts             # Client-side API function for fetching tool data
│   ├── auth/                    # Authentication-related utilities and server-side logic
│   │   ├── clientMeta.ts        # Client-side helper to read session metadata from cookies
│   │   ├── cookies.ts           # Server-side helpers for managing authentication cookies
│   │   └── session.ts           # Server-side session management logic
│   ├── chat/                    # Core logic for the chat feature
│   │   ├── __tests__/           # Tests for chat hooks and utilities
│   │   │   ├── testUtils.tsx    # Test utilities for chat feature tests
│   │   │   ├── useChatController.integration.test.tsx # Integration test for the chat controller hook
│   │   │   └── useChatController.test.tsx # Unit tests for the chat controller hook
│   │   ├── types.ts             # Type definitions for chat functionality
│   │   └── useChatController.ts # The core hook that manages all chat state and logic
│   ├── config.ts                # Global application configuration constants
│   ├── queries/                 # TanStack Query hooks for data fetching and caching
│   │   ├── agents.ts            # Hooks for fetching agent data
│   │   ├── billing.ts           # Hook for managing the billing event stream (custom implementation)
│   │   ├── billingPlans.ts      # Hook for fetching billing plans
│   │   ├── billingSubscriptions.ts # Hooks for managing billing subscriptions
│   │   ├── chat.ts              # Mutation hook for sending chat messages
│   │   ├── conversations.ts     # Hooks for fetching and managing conversations
│   │   ├── keys.ts              # Centralized query keys for TanStack Query
│   │   ├── session.ts           # Hook for silent session refresh (custom implementation)
│   │   └── tools.ts             # Hook for fetching tool data
│   ├── server/                  # Server-side only logic
│   │   ├── apiClient.ts         # Factory for creating an authenticated API client for server-side use
│   │   ├── services/            # Service layer abstracting direct backend API calls
│   │   │   ├── agents.ts        # Service functions for agent-related API calls
│   │   │   ├── auth/            # Authentication-related service functions
│   │   │   │   ├── email.ts     # Service functions for email verification
│   │   │   │   ├── passwords.ts # Service functions for password management
│   │   │   │   ├── serviceAccounts.ts # Service functions for service accounts
│   │   │   │   ├── sessions.ts  # Service functions for session management
│   │   │   │   └── signup.ts    # Service functions for user registration
│   │   │   ├── auth.ts          # Top-level auth services (login, refresh, profile)
│   │   │   ├── billing.ts       # Service functions for billing-related API calls
│   │   │   ├── chat.ts          # Service functions for chat-related API calls
│   │   │   ├── conversations.ts # Service functions for conversation-related API calls
│   │   │   ├── health.ts        # Service functions for health checks
│   │   │   └── tools.ts         # Service functions for tool-related API calls
│   │   └── streaming/           # Server-side logic for handling streams
│   │       └── chat.ts          # Server-side helper to stream chat from the backend
│   ├── types/                   # Shared type definitions (mirrored in top-level `types/`)
│   │   ├── auth.ts              # Authentication-related types
│   │   └── billing.ts           # Billing-related types
│   ├── utils/                   # General utility functions
│   │   └── time.ts              # Time and date formatting utilities
│   └── utils.ts                 # Main utility file, contains `cn` for Tailwind class merging
├── middleware.ts                # Next.js middleware for handling authentication and redirects
├── next.config.ts               # Next.js configuration file
├── openapi-ts.config.ts         # Configuration for the OpenAPI to TypeScript client generator
├── playwright.config.ts         # Configuration file for Playwright end-to-end tests
├── pnpm-lock.yaml               # pnpm lockfile defining exact dependency versions
├── postcss.config.mjs           # PostCSS configuration file for Tailwind CSS
├── public/                      # Directory for static assets like images and fonts
├── tailwind.config.ts           # Tailwind CSS theme and plugin configuration
├── tests/                       # End-to-end tests
│   └── auth-smoke.spec.ts       # A smoke test for the authentication flow
├── types/                       # Global TypeScript type definitions for the application
│   ├── agents.ts                # Type definitions for agents
│   ├── billing.ts               # Type definitions for billing
│   ├── conversations.ts         # Type definitions for conversations
│   ├── session.ts               # Type definitions for user sessions
│   └── tools.ts                 # Type definitions for tools
├── vitest.config.ts             # Vitest configuration file for unit/integration tests
└── vitest.setup.ts              # Setup file for Vitest tests (e.g., global mocks)