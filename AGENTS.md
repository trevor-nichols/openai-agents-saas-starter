You are a professional engineer and developer in charge of the OpenAI Agent Starter Codebase. The OpenAI Agent Starter Codebase contains a Next.js frontend and a FastAPI backend. The FastAPI backend is based on the latest new OpenAI Agents SDK (v0.5.0)and uses the brand new GPT-5 model with reasoning. 

# Requirements
- You must maintain a professional clean architecture, referring to the documentations of the OpenAI Agents SDK and the `docs/openai-agents-sdk` directory whenever needed in order to ensure you abide by the latest API framework. 


# Notes
- Throughout the codebase, you will see `SNAPSHOT.md` files. `SNAPSHOT.md` files contain the full structure of the codebase at a given point in time. Refer to these files when you need understand the architecture or need help navigating the codebase.
- When applying database migrations or generating new ones, always use the Makefile targets (`make migrate`, `make migration-revision`) so your `.env.local`/`.env` secrets and `.env.compose` values are loaded consistently. These wrappers take care of wiring Alembic to the right Postgres instance (local Docker or remote) without manual exports.
- The frontend uses the HeyAPI SDK to generate the API client. The API client is generated into the `lib/api/client` directory.

# Codebase Patterns
openai-agents-starter/
├── pyproject.toml
├── run.py
├── agent-next-15-frontend/
│   ├── app/
│   │   ├── (agent)/
│   │   │   ├── actions.ts
│   │   │   ├── layout.tsx
│   │   │   └── page.tsx
│   │   ├── globals.css
│   │   └── layout.tsx
│   ├── components/
│   │   └── agent/
│   │       ├── ChatInterface.tsx
│   │       └── ConversationSidebar.tsx
│   ├── hooks/
│   │   └── useConversations.ts
│   ├── lib/
│   │   └── api/
│   │       ├── client/… (generated)
│   │       ├── config.ts
│   │       └── streaming.ts
│   ├── types/
│   │   └── generated/… (OpenAPI types)
│   └── config + tooling files (package.json, tailwind.config.ts, etc.)
├── anything-agents/
│   ├── app/
│   │   ├── core/ (config, security)
│   │   ├── middleware/ (logging)
│   │   ├── routers/ (agents, api, auth, health)
│   │   ├── schemas/ (agents, auth, common)
│   │   ├── services/ (agent_service.py)
│   │   └── utils/
│   │       └── tools/ (registry.py, web_search.py)
│   ├── main.py
│   ├── README.md
│   └── tests/
│       ├── test_agents.py
│       ├── test_health.py
│       ├── test_streaming.py
│       └── test_tools.py
└── docs/
    └── openai-agents-sdk/
        ├── agents/… (SDK docs)
        ├── examples/… (usage patterns)
        └── tracing/, memory/, handoffs/, etc.
