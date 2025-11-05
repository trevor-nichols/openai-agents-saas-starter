.
├── app/                         # Contains application routes, pages, and layouts.
│   ├── (agent)/                 # Route group for agent-related pages and layouts.
│   │   ├── actions.ts           # Defines server actions for agent chat and conversation management.
│   │   ├── layout.tsx           # Layout component for the agent-specific pages.
│   │   └── page.tsx             # Main page component for the agent chat interface.
│   └── layout.tsx               # Root layout for the entire application.
├── components/                  # Contains reusable React components.
│   └── agent/                   # Components specific to the agent chat functionality.
│       ├── ChatInterface.tsx    # Renders the chat message area and input form.
│       └── ConversationSidebar.tsx # Displays the list of conversations and allows navigation.
├── eslint.config.mjs            # ESLint configuration for code linting.
├── hooks/                       # Contains custom React hooks.
│   └── useConversations.ts      # Custom hook for managing conversation list state and fetching.
├── lib/                         # Contains utility functions and API clients.
│   └── api-client.ts            # Client-side API utilities for streaming chat with FastAPI backend.
├── next.config.ts               # Configuration file for the Next.js framework.
├── postcss.config.mjs           # Configuration for PostCSS, used with Tailwind CSS.
├── tailwind.config.ts           # Configuration file for the Tailwind CSS utility-first framework.
└── types/                       # Contains TypeScript type definitions.
    └── generated/               # Directory for auto-generated type definitions.
        └── api.ts               # Auto-generated TypeScript types from the backend's OpenAPI spec.