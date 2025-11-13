.
├── app/                                 # Next.js App Router root directory
│   ├── (app)/                           # Route group for authenticated application pages
│   │   ├── (workspace)/                 # Route group for multi-column workspace layouts
│   │   │   ├── chat/                    # Chat workspace feature pages
│   │   │   │   ├── actions.ts           # Server Actions for the chat feature (streaming, conversation list)
│   │   │   │   └── page.tsx             # The main chat workspace page component
│   │   │   ├── layout.tsx               # Layout providing spacing for workspace views like chat
│   │   ├── account/                     # Account management pages
│   │   │   ├── page.tsx                 # Renders the main account overview with tabbed navigation
│   │   ├── agents/                      # Agent management pages
│   │   │   ├── page.tsx                 # Renders the main agent workspace feature
│   │   ├── billing/                     # Billing and subscription management pages
│   │   │   ├── page.tsx                 # The main billing overview page
│   │   │   └── plans/                   # Subscription plan management pages
│   │   │       └── page.tsx             # Page for viewing and managing subscription plans
│   │   ├── dashboard/                   # Main dashboard for authenticated users
│   │   │   ├── page.tsx                 # The dashboard overview page component
│   │   ├── error.tsx                    # Custom error boundary for authenticated app routes
│   │   ├── layout.tsx                   # Main application shell with sidebar and header for authenticated users
│   │   ├── page.tsx                     # Root page for the authenticated app group, redirects to /dashboard
│   │   └── settings/                    # Application and tenant settings pages
│   │       └── tenant/                  # Tenant-specific settings
│   │           └── page.tsx             # Page for managing tenant settings
│   ├── (auth)/                          # Route group for authentication pages (login, register, etc.)
│   │   ├── _components/                 # Private components for the (auth) route group
│   │   │   └── AuthCard.tsx             # Reusable card component for authentication forms
│   │   ├── email/                       # Email-related authentication flows
│   │   │   └── verify/                  # Email verification flow
│   │   │       ├── VerifyEmailClient.tsx # Client component with logic for email verification
│   │   │       └── page.tsx             # Server component page for email verification
│   │   ├── error.tsx                    # Custom error boundary for authentication routes
│   │   ├── layout.tsx                   # Layout for auth pages, providing a centered, styled container
│   │   ├── loading.tsx                  # Loading UI skeleton for authentication routes
│   │   ├── login/                       # Login page route
│   │   │   └── page.tsx                 # The user login page component
│   │   ├── password/                    # Password management flows
│   │   │   ├── forgot/                  # Forgot password flow
│   │   │   │   └── page.tsx             # The "forgot password" page component
│   │   │   └── reset/                   # Reset password flow
│   │   │       └── page.tsx             # The "reset password" page component
│   │   └── register/                    # User registration route
│   │       └── page.tsx                 # The user and tenant registration page component
│   ├── (marketing)/                     # Route group for public-facing marketing pages
│   │   ├── _components/                 # Private components for the (marketing) route group
│   │   │   ├── marketing-footer.tsx     # Footer component for marketing pages
│   │   │   ├── marketing-header.tsx     # Header component for marketing pages
│   │   │   └── nav-links.ts             # Defines navigation links for marketing header and footer
│   │   ├── error.tsx                    # Custom error boundary for marketing routes
│   │   ├── features/                    # Product features page
│   │   │   └── page.tsx                 # A page detailing the product's features
│   │   ├── layout.tsx                   # Layout for marketing pages with a shared header and footer
│   │   ├── page.tsx                     # The main public landing page for the application
│   │   ├── pricing/                     # Product pricing page
│   │   │   └── page.tsx                 # A page displaying pricing plans
│   │   └── status/                      # Public platform status page
│   │       └── page.tsx                 # The public-facing system status page component
│   ├── actions/                         # Server-side logic (Next.js Server Actions)
│   │   ├── auth/                        # Authentication-related server actions
│   │   │   ├── email.ts                 # Server actions for handling email verification
│   │   │   ├── passwords.ts             # Server actions for password management (reset, change)
│   │   │   ├── sessions.ts              # Server actions for managing user sessions (list, revoke)
│   │   │   └── signup.ts                # Server action for handling new user/tenant registration
│   │   └── auth.ts                      # Top-level server actions for login, logout, and silent refresh
│   ├── api/                             # API route handlers (backend endpoints for the frontend)
│   │   ├── agents/                      # API routes related to AI agents
│   │   │   ├── [agentName]/             # Dynamic routes for a specific agent
│   │   │   │   └── status/              # Agent status-related routes
│   │   │   │       ├── route.test.ts    # Tests for the agent status API route
│   │   │   │       └── route.ts         # API route to get a specific agent's status
│   │   │   ├── route.test.ts            # Tests for the list agents API route
│   │   │   └── route.ts                 # API route to list all available agents
│   │   ├── auth/                        # Authentication-related API routes
│   │   │   ├── email/                   # Email verification API routes
│   │   │   │   ├── send/                # API route to send verification emails
│   │   │   │   │   ├── route.test.ts    # Tests for the send verification email API
│   │   │   │   │   └── route.ts         # API handler to trigger sending a verification email
│   │   │   │   └── verify/              # API route to verify an email token
│   │   │   │       ├── route.test.ts    # Tests for the email verification API
│   │   │   │       └── route.ts         # API handler to verify an email token
│   │   │   ├── logout/                  # User logout API routes
│   │   │   │   ├── all/                 # API route to log out all user sessions
│   │   │   │   │   ├── route.test.ts    # Tests for the logout-all API
│   │   │   │   │   └── route.ts         # API handler to log out from all devices
│   │   │   │   ├── route.test.ts        # Tests for the single-session logout API
│   │   │   │   └── route.ts             # API handler to log out the current session
│   │   │   ├── password/                # Password management API routes
│   │   │   │   ├── change/              # API route for changing a password
│   │   │   │   │   ├── route.test.ts    # Tests for the password change API
│   │   │   │   │   └── route.ts         # API handler for a user to change their own password
│   │   │   │   ├── confirm/             # API route to confirm a password reset
│   │   │   │   │   ├── route.test.ts    # Tests for the password reset confirmation API
│   │   │   │   │   └── route.ts         # API handler to confirm a password reset using a token
│   │   │   │   ├── forgot/              # API route to request a password reset
│   │   │   │   │   ├── route.test.ts    # Tests for the forgot password API
│   │   │   │   │   └── route.ts         # API handler to initiate a password reset flow
│   │   │   │   └── reset/               # API route for admin-initiated password resets
│   │   │   │       ├── route.test.ts    # Tests for the admin password reset API
│   │   │   │       └── route.ts         # API handler for an admin to reset a user's password
│   │   │   ├── refresh/                 # API route to refresh an access token
│   │   │   │   └── route.ts             # API handler for refreshing an authentication session
│   │   │   ├── register/                # API route for user registration
│   │   │   │   ├── route.test.ts        # Tests for the registration API
│   │   │   │   └── route.ts             # API handler for new user and tenant registration
│   │   │   ├── service-accounts/        # API routes for service account management
│   │   │   │   ├── browser-issue/       # API route to issue a token from the browser
│   │   │   │   │   ├── route.test.ts    # Tests for the browser token issuance API
│   │   │   │   │   └── route.ts         # API handler to issue a service account token via user session
│   │   │   │   ├── issue/               # API route to issue a token using Vault
│   │   │   │   │   └── route.ts         # API handler to issue a service account token via Vault
│   │   │   │   └── tokens/              # API routes for managing service account tokens
│   │   │   │       ├── [jti]/           # Dynamic route for a specific token by its JWT ID
│   │   │   │       │   └── revoke/      # API route to revoke a token
│   │   │   │       │       ├── route.test.ts # Tests for the token revocation API
│   │   │   │       │       └── route.ts     # API handler to revoke a specific service account token
│   │   │   │       ├── route.test.ts    # Tests for the list tokens API
│   │   │   │       └── route.ts         # API handler to list service account tokens
│   │   │   ├── session/                 # API route for the current user session
│   │   │   │   └── route.ts             # API handler to get current user session and profile info
│   │   │   └── sessions/                # API routes for managing user sessions
│   │   │       ├── [sessionId]/         # Dynamic route for a specific session
│   │   │       │   ├── route.test.ts    # Tests for the revoke session API
│   │   │       │   └── route.ts         # API handler to revoke a specific user session
│   │   │       ├── route.test.ts        # Tests for the list sessions API
│   │   │       └── route.ts             # API handler to list user sessions
│   │   ├── billing/                     # Billing-related API routes
│   │   │   ├── plans/                   # API route for billing plans
│   │   │   │   └── route.ts             # API handler to list available billing plans
│   │   │   ├── stream/                  # SSE route for billing events
│   │   │   │   └── route.ts             # API handler for the real-time billing event stream
│   │   │   └── tenants/                 # Tenant-specific billing routes
│   │   │       └── [tenantId]/          # Dynamic routes for a specific tenant
│   │   │           ├── subscription/    # Tenant subscription management routes
│   │   │           │   ├── cancel/      # API route to cancel a subscription
│   │   │           │   │   ├── route.test.ts # Tests for the cancel subscription API
│   │   │           │   │   └── route.ts     # API handler to cancel a tenant's subscription
│   │   │           │   ├── route.test.ts    # Tests for subscription management APIs (GET, POST, PATCH)
│   │   │           │   └── route.ts         # API handlers for getting, starting, and updating a subscription
│   │   │           └── usage/           # Tenant usage reporting routes
│   │   │               ├── route.test.ts    # Tests for the usage reporting API
│   │   │               └── route.ts         # API handler to record metered usage for a tenant
│   │   ├── chat/                        # Chat-related API routes
│   │   │   ├── route.test.ts            # Tests for the non-streaming chat API
│   │   │   ├── route.ts                 # API handler for non-streaming chat requests
│   │   │   └── stream/                  # SSE route for streaming chat
│   │   │       └── route.ts             # API handler for streaming chat responses
│   │   ├── conversations/               # Conversation history API routes
│   │   │   ├── [conversationId]/        # Dynamic routes for a specific conversation
│   │   │   │   ├── route.test.ts        # Tests for getting and deleting a conversation
│   │   │   │   └── route.ts             # API handlers to get or delete a specific conversation
│   │   │   ├── route.test.ts            # Tests for the list conversations API
│   │   │   └── route.ts                 # API handler to list conversations for the current user
│   │   ├── health/                      # Health check API routes
│   │   │   ├── ready/                   # Readiness probe route
│   │   │   │   ├── route.test.ts        # Tests for the readiness probe API
│   │   │   │   └── route.ts             # API handler for the readiness probe
│   │   │   ├── route.test.ts            # Tests for the liveness probe API
│   │   │   └── route.ts                 # API handler for the liveness probe
│   │   ├── status/                      # Public platform status API routes
│   │   │   ├── rss/                     # RSS feed for platform status
│   │   │   │   └── route.ts             # API handler to proxy the backend's status RSS feed
│   │   │   └── route.ts                 # API handler to get the platform status snapshot
│   │   ├── status-subscriptions/        # API routes for status page subscriptions
│   │   │   ├── unsubscribe/             # Unsubscribe from status updates
│   │   │   │   └── route.ts             # API handler to process an unsubscribe request
│   │   │   └── verify/                  # Verify a status subscription
│   │   │       └── route.ts             # API handler to process a subscription verification token
│   │   └── tools/                       # API routes for agent tools
│   │       └── route.ts                 # API handler to list available tools
│   ├── layout.tsx                     # Root layout for the entire application
│   └── providers.tsx                  # Client-side providers (React Query, NextThemes, Toaster)
├── components/                          # Shared React components used across features
│   ├── auth/                            # Components for authentication flows
│   │   ├── ForgotPasswordForm.tsx       # Form for requesting a password reset link
│   │   ├── LoginForm.tsx                # The user login form component
│   │   ├── LogoutButton.tsx             # A client component button for logging out
│   │   ├── RegisterForm.tsx             # The user registration form component
│   │   ├── ResetPasswordForm.tsx        # Form for setting a new password with a reset token
│   │   └── SilentRefresh.tsx            # Component to trigger the silent session refresh hook
│   ├── shared/                          # Components shared across multiple features
│   │   └── conversations/               # Components related to conversations
│   │       └── ConversationDetailDrawer.tsx # Drawer component to display detailed conversation history
│   └── ui/                              # General-purpose UI components (e.g., from shadcn/ui)
│       ├── accordion.tsx                # Accordion component implementation
│       ├── alert-dialog.tsx             # Alert dialog (modal) component
│       ├── alert.tsx                    # Alert message component
│       ├── aspect-ratio.tsx             # Aspect ratio container component
│       ├── avatar.tsx                   # Avatar component
│       ├── badge.tsx                    # Badge component
│       ├── breadcrumb.tsx               # Breadcrumb navigation component
│       ├── button.tsx                   # Button component
│       ├── card.tsx                     # Card component
│       ├── carousel.tsx                 # Carousel component
│       ├── checkbox.tsx                 # Checkbox component
│       ├── collapsible.tsx              # Collapsible content component
│       ├── command.tsx                  # Command menu (e.g., for Ctrl+K search)
│       ├── context-menu.tsx             # Context menu (right-click) component
│       ├── data-table/                  # Reusable data table component
│       │   └── index.tsx                # Main data table component using TanStack Table
│       ├── dialog.tsx                   # Dialog (modal) component
│       ├── dropdown-menu.tsx            # Dropdown menu component
│       ├── form.tsx                     # Components for building forms with react-hook-form
│       ├── foundation/                  # Custom, foundational UI components for the app's theme
│       │   ├── GlassPanel.tsx           # A panel with a blurred glass effect
│       │   ├── InlineTag.tsx            # A small tag-like component for status indicators
│       │   ├── KeyValueList.tsx         # Component for displaying key-value pairs
│       │   ├── SectionHeader.tsx        # A standardized section header component
│       │   ├── StatCard.tsx             # A card for displaying a single statistic or KPI
│       │   └── index.ts                 # Barrel file for exporting foundation components
│       ├── hover-card.tsx               # Hover card component
│       ├── input.tsx                    # Input field component
│       ├── label.tsx                    # Label component for forms
│       ├── navigation-menu.tsx          # Navigation menu component
│       ├── pagination.tsx               # Pagination component
│       ├── popover.tsx                  # Popover component
│       ├── progress.tsx                 # Progress bar component
│       ├── radio-group.tsx              # Radio group component
│       ├── resizable.tsx                # Resizable panel component
│       ├── scroll-area.tsx              # Scroll area component with custom scrollbars
│       ├── select.tsx                   # Select (dropdown) component
│       ├── separator.tsx                # Separator line component
│       ├── shadcn-io/                   # Components adapted from shadcn.io/ui examples
│       │   ├── ai/                      # Components specifically for AI/chat interfaces
│       │   │   ├── actions.tsx          # UI for action buttons in a chat message
│       │   │   ├── branch.tsx           # UI for switching between multiple AI response branches
│       │   │   ├── code-block.tsx       # A rich code block component with syntax highlighting
│       │   │   ├── conversation.tsx     # Components for structuring a conversation view
│       │   │   ├── image.tsx            # Component for displaying AI-generated images
│       │   │   ├── inline-citation.tsx  # UI for showing citations within an AI response
│       │   │   ├── loader.tsx           # A loading spinner component
│       │   │   ├── message.tsx          # Components for styling user and assistant messages
│       │   │   ├── prompt-input.tsx     # A comprehensive prompt input component with toolbar
│       │   │   ├── reasoning.tsx        # UI for showing the AI's "thought process" or reasoning
│       │   │   ├── response.tsx         # Component for rendering markdown from an AI response
│       │   │   ├── source.tsx           # UI for displaying sources used by the AI
│       │   │   ├── suggestion.tsx       # UI for showing suggested follow-up prompts
│       │   │   ├── task.tsx             # UI for displaying AI-driven tasks
│       │   │   ├── tool.tsx             # UI for displaying tool usage by the AI
│       │   │   └── web-preview.tsx      # A component for previewing web content
│       │   ├── animated-beam/           # Animated beam component for visualizations
│       │   │   └── index.tsx            # Implementation of the animated beam component
│       │   ├── animated-testimonials/   # Animated testimonials component
│       │   │   └── index.tsx            # Implementation of the animated testimonials component
│       │   ├── animated-tooltip/        # Animated tooltip component
│       │   │   └── index.tsx            # Implementation of the animated tooltip component
│       │   ├── avatar-group/            # Component to display a group of overlapping avatars
│       │   │   └── index.tsx            # Implementation of the avatar group component
│       │   ├── code-block/              # Advanced code block components
│       │   │   ├── index.tsx            # Client-side code block with syntax highlighting
│       │   │   └── server.tsx           # Server-side code block with syntax highlighting via Shiki
│       │   ├── copy-button/             # A button for copying text to the clipboard
│       │   │   └── index.tsx            # Implementation of the copy button component
│       │   ├── dropzone/                # File dropzone component
│       │   │   └── index.tsx            # Implementation of the dropzone component
│       │   ├── magnetic/                # A component with a magnetic mouse-follow effect
│       │   │   └── index.tsx            # Implementation of the magnetic component
│       │   ├── marquee/                 # A scrolling marquee component
│       │   │   └── index.tsx            # Implementation of the marquee component
│       │   ├── navbar-05/               # A specific navbar style example
│       │   │   └── index.tsx            # Implementation of the navbar-05 component
│       │   ├── spinner/                 # Various spinner components
│       │   │   └── index.tsx            # Implementation of different spinner styles
│       │   ├── status/                  # A component to display status with an indicator
│       │   │   └── index.tsx            # Implementation of the status component
│       │   └── video-player/            # A video player component
│       │       └── index.tsx            # Implementation of the video player component
│       ├── shape-landing-hero.tsx       # A geometric hero section component for landing pages
│       ├── sheet.tsx                    # Sheet (slide-over panel) component
│       ├── skeleton.tsx                 # Skeleton loader component
│       ├── sonner.tsx                   # Toaster component for notifications, integrated with next-themes
│       ├── states/                      # Components for different UI states (empty, error, loading)
│       │   ├── EmptyState.tsx           # A standardized component for empty states
│       │   ├── ErrorState.tsx           # A standardized component for error states
│       │   ├── SkeletonPanel.tsx        # A skeleton loader in the shape of a panel
│       │   └── index.ts                 # Barrel file for exporting state components
│       ├── switch.tsx                   # Switch toggle component
│       ├── table.tsx                    # Table layout components
│       ├── tabs.tsx                     # Tabs component
│       ├── textarea.tsx                 # Textarea component
│       ├── theme-toggle.tsx             # Button to toggle between light and dark themes
│       ├── toggle.tsx                   # Toggle button component
│       └── tooltip.tsx                  # Tooltip component
├── eslint.config.mjs                    # ESLint configuration file
├── features/                            # Feature-based modules combining components and logic
│   ├── account/                         # Contains components and logic for the account management feature
│   │   ├── AccountOverview.tsx          # Orchestrator component for the tabbed account management page
│   │   ├── ProfilePanel.tsx             # Panel for displaying and editing user profile information
│   │   ├── SecurityPanel.tsx            # Panel for managing security settings like passwords
│   │   ├── ServiceAccountsPanel.tsx     # Panel for managing service account tokens
│   │   ├── SessionsPanel.tsx            # Panel for viewing and managing active user sessions
│   │   ├── __tests__/                   # Tests for the account feature
│   │   │   └── serviceAccountIssueHelpers.test.ts # Unit tests for service account form helpers
│   │   ├── index.ts                     # Barrel file for exporting account feature components
│   │   └── serviceAccountIssueHelpers.ts # Helper functions for the service account token issuance form
│   ├── agents/                          # Contains components and logic for the agent workspace feature
│   │   ├── AgentWorkspace.tsx           # Main orchestrator component for the agent management workspace
│   │   ├── components/                  # Sub-components used within the AgentWorkspace
│   │   │   ├── AgentCatalogGrid.tsx     # Grid view of all available agents and their statuses
│   │   │   ├── AgentToolsPanel.tsx      # Panel displaying tools available to an agent
│   │   │   ├── AgentWorkspaceChatPanel.tsx # The central chat panel within the agent workspace
│   │   │   └── ConversationArchivePanel.tsx # Panel for viewing and searching past conversations
│   │   ├── constants.ts                 # Constants used within the agents feature
│   │   ├── hooks/                       # Custom hooks for the agents feature
│   │   │   └── useAgentWorkspaceData.ts # Hook to fetch and organize all data for the agent workspace
│   │   ├── index.ts                     # Barrel file for exporting the AgentWorkspace component
│   │   ├── types.ts                     # TypeScript types specific to the agents feature
│   │   └── utils/                       # Utility functions for the agents feature
│   │       └── toolTransforms.ts        # Functions to transform tool data for display
│   ├── billing/                         # Contains components and logic for the billing feature
│   │   ├── BillingOverview.tsx          # The main overview component for the billing page
│   │   ├── PlanManagement.tsx           # Component for managing subscription plans
│   │   └── index.ts                     # Barrel file for exporting billing feature components
│   ├── chat/                            # Contains components and logic for the dedicated chat feature
│   │   ├── ChatWorkspace.tsx            # Main orchestrator component for the dedicated chat page
│   │   ├── components/                  # Sub-components used within the ChatWorkspace
│   │   │   ├── AgentSwitcher.tsx        # Dropdown component to switch between agents in the chat
│   │   │   ├── BillingEventsPanel.tsx   # Panel to display real-time billing events
│   │   │   ├── ChatInterface.tsx        # The core chat UI component with messages and input
│   │   │   ├── ConversationSidebar.tsx  # Sidebar for listing and managing conversations
│   │   │   ├── ToolMetadataPanel.tsx    # Panel displaying metadata about available tools
│   │   │   └── __tests__/               # Tests for chat components
│   │   │       └── BillingEventsPanel.test.tsx # Unit tests for the BillingEventsPanel component
│   │   └── index.ts                     # Barrel file for exporting chat feature components
│   ├── dashboard/                       # Contains components and logic for the main dashboard
│   │   ├── DashboardOverview.tsx        # Main orchestrator component for the dashboard page
│   │   ├── components/                  # Sub-components used within the DashboardOverview
│   │   │   ├── BillingPreview.tsx       # A small card showing a preview of billing status
│   │   │   ├── KpiGrid.tsx              # A grid displaying key performance indicators (KPIs)
│   │   │   ├── QuickActions.tsx         # A grid of common actions a user can take
│   │   │   └── RecentConversations.tsx  # A list of recent conversations
│   │   ├── constants.ts                 # Constants for the dashboard feature, like quick action definitions
│   │   ├── hooks/                       # Custom hooks for the dashboard feature
│   │   │   └── useDashboardData.tsx     # Hook to fetch and aggregate all data for the dashboard
│   │   ├── index.ts                     # Barrel file for exporting the DashboardOverview component
│   │   └── types.ts                     # TypeScript types specific to the dashboard feature
│   └── settings/                        # Contains components and logic for settings pages
│       ├── TenantSettingsPanel.tsx      # A placeholder panel for tenant-specific settings
│       └── index.ts                     # Barrel file for exporting settings feature components
├── hooks/                               # Application-wide custom React hooks
│   ├── __tests__/                       # Tests for custom hooks
│   │   └── noLegacyHooks.test.ts        # A test to prevent re-introduction of old hook files
│   └── useAuthForm.ts                   # A generic hook for managing authentication forms with validation
├── lib/                                 # Core application logic, utilities, and API communication
│   ├── api/                             # Data fetching logic, organized by domain
│   │   ├── __tests__/                   # Tests for API layer functions
│   │   │   └── chat.test.ts             # Unit tests for chat API helpers
│   │   ├── account.ts                   # API functions for fetching account and profile data
│   │   ├── accountSecurity.ts           # API functions for account security operations (e.g., change password)
│   │   ├── accountServiceAccounts.ts    # API functions for managing service account tokens
│   │   ├── accountSessions.ts           # API functions for managing user sessions
│   │   ├── agents.ts                    # API functions for fetching agent data
│   │   ├── billing.ts                   # API functions for connecting to the billing SSE stream
│   │   ├── billingPlans.ts              # API functions for fetching billing plans
│   │   ├── billingSubscriptions.ts      # API functions for managing tenant subscriptions
│   │   ├── chat.ts                      # API functions for sending and streaming chat messages
│   │   ├── client/                      # Auto-generated API client from OpenAPI specification
│   │   │   ├── client/                  # Core client implementation files
│   │   │   │   ├── client.gen.ts        # The main generated API client factory
│   │   │   │   ├── index.ts             # Barrel file for the client subdirectory
│   │   │   │   ├── types.gen.ts         # Generated TypeScript types for the client
│   │   │   │   └── utils.gen.ts         # Generated utility functions for the client
│   │   │   ├── client.gen.ts            # Generated client configuration and instance
│   │   │   ├── core/                    # Core utilities for the generated client
│   │   │   │   ├── auth.gen.ts          # Generated authentication helpers
│   │   │   │   ├── bodySerializer.gen.ts # Generated body serialization helpers
│   │   │   │   ├── params.gen.ts        # Generated parameter building helpers
│   │   │   │   ├── pathSerializer.gen.ts # Generated path serialization helpers
│   │   │   │   ├── queryKeySerializer.gen.ts # Utilities for serializing values for query keys
│   │   │   │   ├── serverSentEvents.gen.ts # Generated SSE client logic
│   │   │   │   ├── types.gen.ts         # Generated core TypeScript types
│   │   │   │   └── utils.gen.ts         # Generated core utility functions
│   │   │   ├── index.ts                 # Main barrel file for the generated client
│   │   │   ├── sdk.gen.ts               # Generated SDK functions for each API endpoint
│   │   │   └── types.gen.ts             # Generated TypeScript types for API schemas
│   │   ├── config.ts                    # Exports the configured generated API client instance
│   │   ├── conversations.ts             # API functions for fetching and managing conversations
│   │   ├── session.ts                   # API functions for managing the user session (fetch, refresh)
│   │   ├── status.ts                    # API function for fetching the platform status snapshot
│   │   ├── statusSubscriptions.ts       # API functions for managing status page subscriptions
│   │   └── tools.ts                     # API function for fetching available tools
│   ├── auth/                            # Authentication-related utilities
│   │   ├── clientMeta.ts                # Client-side utility to read session metadata from cookies
│   │   ├── cookies.ts                   # Server-side utilities for managing authentication cookies
│   │   └── session.ts                   # Server-side logic for session management (login, refresh, etc.)
│   ├── chat/                            # Core logic for the chat feature
│   │   ├── __tests__/                   # Tests for chat logic and hooks
│   │   │   ├── testUtils.tsx            # Test utilities for chat feature tests
│   │   │   ├── useChatController.integration.test.tsx # Integration tests for the chat controller hook with streaming
│   │   │   └── useChatController.test.tsx # Unit tests for the chat controller hook
│   │   ├── types.ts                     # TypeScript types specific to the chat feature
│   │   └── useChatController.ts         # The core state management hook for the chat interface
│   ├── config.ts                        # Global application configuration and constants
│   ├── queries/                         # TanStack Query hooks for data fetching and caching
│   │   ├── __tests__/                   # Tests for TanStack Query hooks
│   │   │   └── accountSessions.test.ts  # Tests for the account sessions query hooks
│   │   ├── account.ts                   # TanStack Query hooks for account and profile data
│   │   ├── accountSecurity.ts           # TanStack Query mutation hook for changing password
│   │   ├── accountServiceAccounts.ts    # TanStack Query hooks for managing service accounts
│   │   ├── accountSessions.ts           # TanStack Query hooks for managing user sessions
│   │   ├── agents.ts                    # TanStack Query hooks for fetching agent data
│   │   ├── billing.ts                   # Custom hook for the real-time billing event stream
│   │   ├── billingPlans.ts              # TanStack Query hook for fetching billing plans
│   │   ├── billingSubscriptions.ts      # TanStack Query hooks for managing subscriptions
│   │   ├── chat.ts                      # TanStack Query mutation hook for sending chat messages
│   │   ├── conversations.ts             # TanStack Query hooks for managing conversations
│   │   ├── keys.ts                      # Centralized factory for generating TanStack Query keys
│   │   ├── session.ts                   # Custom hook for managing silent session refresh
│   │   ├── status.ts                    # TanStack Query hook for fetching platform status
│   │   └── tools.ts                     # TanStack Query hook for fetching available tools
│   ├── server/                          # Server-side only logic
│   │   ├── apiClient.ts                 # Factory for creating an authenticated API client on the server
│   │   └── services/                    # Server-side functions that call the backend API
│   │       ├── agents.ts                # Service functions for agent-related operations
│   │       ├── auth/                    # Authentication-related service functions
│   │       │   ├── email.ts             # Service functions for email verification
│   │       │   ├── passwords.ts         # Service functions for password management
│   │       │   ├── serviceAccounts.ts   # Service functions for service account management
│   │       │   ├── sessions.ts          # Service functions for session management
│   │       │   └── signup.ts            # Service function for user/tenant registration
│   │       ├── auth.ts                  # Service functions for core authentication (login, refresh)
│   │       ├── billing.ts               # Service functions for billing operations
│   │       ├── chat.ts                  # Service functions for chat operations
│   │       ├── conversations.ts         # Service functions for conversation management
│   │       ├── health.ts                # Service functions for health checks
│   │       ├── status.ts                # Service function for fetching platform status
│   │       ├── statusSubscriptions.ts   # Service functions for managing status subscriptions
│   │       └── tools.ts                 # Service function for fetching tools
│   └── types/                           # Shared TypeScript types used in the server-side library
│       ├── auth.ts                      # Types for authentication tokens and sessions
│       └── billing.ts                   # Types related to billing
├── middleware.ts                        # Next.js middleware for authentication and routing logic
├── next.config.ts                       # Next.js configuration file
├── openapi-ts.config.ts                 # Configuration for the OpenAPI to TypeScript client generator
├── playwright.config.ts                 # Configuration for Playwright end-to-end tests
├── pnpm-lock.yaml                       # PNPM lockfile for dependency management
├── postcss.config.mjs                   # PostCSS configuration for CSS processing
├── public/                              # Directory for static assets (images, etc.)
├── tailwind.config.ts                   # Tailwind CSS configuration and theme customization
├── tests/                               # End-to-end tests directory
│   └── auth-smoke.spec.ts               # A smoke test for the authentication flow
├── types/                               # Global application-specific TypeScript types
│   ├── account.ts                       # Types related to user accounts and profiles
│   ├── agents.ts                        # Types related to AI agents
│   ├── billing.ts                       # Types related to billing, plans, and events
│   ├── conversations.ts                 # Types related to chat conversations
│   ├── serviceAccounts.ts               # Types related to service accounts and their tokens
│   ├── session.ts                       # Types related to user sessions
│   ├── status.ts                        # Types related to platform status
│   └── tools.ts                         # Types related to agent tools
├── vitest.config.ts                     # Vitest (unit/integration testing) configuration
└── vitest.setup.ts                      # Setup file for Vitest tests, e.g., for polyfills or matchers