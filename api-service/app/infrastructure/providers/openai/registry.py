"""Agent registry and tool wiring for the OpenAI provider."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime
from typing import Any, ClassVar

from agents import Agent, function_tool, handoff
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions

from app.core.settings import Settings
from app.domain.ai import AgentDescriptor
from app.services.agents.context import get_current_actor
from app.utils.tools import ToolRegistry, initialize_tools


class OpenAIAgentRegistry:
    """Maintains concrete Agent instances and metadata."""

    _AGENT_CAPABILITIES: ClassVar[dict[str, tuple[str, ...]]] = {
        "triage": ("general", "search", "handoff"),
        "code_assistant": ("code", "search"),
        "data_analyst": ("analysis", "search"),
    }

    def __init__(
        self,
        *,
        settings_factory: Callable[[], Settings],
        conversation_searcher,
    ) -> None:
        self._settings_factory = settings_factory
        self._conversation_searcher = conversation_searcher
        self._tool_registry: ToolRegistry = initialize_tools()
        self._agents: dict[str, Agent] = {}
        self._descriptors: dict[str, AgentDescriptor] = {}
        self._register_builtin_tools()
        self._build_default_agents()

    @property
    def default_agent_key(self) -> str:
        return "triage"

    def get_agent_handle(self, agent_key: str) -> Agent | None:
        return self._agents.get(agent_key)

    def get_descriptor(self, agent_key: str) -> AgentDescriptor | None:
        return self._descriptors.get(agent_key)

    def list_descriptors(self) -> Sequence[AgentDescriptor]:
        return [self._descriptors[name] for name in sorted(self._descriptors.keys())]

    def tool_overview(self) -> dict[str, Any]:
        return {
            "total_tools": len(self._tool_registry.list_tool_names()),
            "tool_names": self._tool_registry.list_tool_names(),
            "categories": self._tool_registry.list_categories(),
        }

    def resolve_agent(self, preferred_key: str | None) -> AgentDescriptor:
        key = preferred_key or self.default_agent_key
        descriptor = self.get_descriptor(key)
        if descriptor:
            return descriptor
        fallback = self.get_descriptor(self.default_agent_key)
        if not fallback:
            raise RuntimeError("No default agent configured for OpenAI provider.")
        return fallback

    def _register_builtin_tools(self) -> None:
        self._tool_registry.register_tool(
            self._build_current_time_tool(),
            category="utility",
            metadata={
                "description": "Return the current UTC timestamp.",
                "core": True,
                "capabilities": ["general"],
            },
        )
        self._tool_registry.register_tool(
            self._build_conversation_search_tool(),
            category="conversation",
            metadata={
                "description": "Search cached conversation history.",
                "core": True,
                "capabilities": ["conversation", "search"],
            },
        )

    def _build_current_time_tool(self):
        @function_tool
        async def get_current_time() -> str:
            return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        return get_current_time

    def _build_conversation_search_tool(self):
        conversation_searcher = self._conversation_searcher

        @function_tool
        async def search_conversations(query: str) -> str:
            actor = get_current_actor()
            if actor is None:
                return "Conversation search is unavailable until tenant context is established."
            results = await conversation_searcher(tenant_id=actor.tenant_id, query=query)
            if hasattr(results, "items"):
                # ConversationService.search returns a SearchPage
                results = results.items
            if not results:
                return "No conversations contained the requested text."
            top_matches = "\n".join(
                f"{result.conversation_id}: {result.preview}" for result in results[:5]
            )
            return f"Found {len(results)} matching conversations:\n{top_matches}"

        return search_conversations

    def _build_default_agents(self) -> None:
        settings = self._settings_factory()
        triage_tools = self._select_tools("triage")
        code_tools = self._select_tools("code_assistant")
        data_tools = self._select_tools("data_analyst")

        code_assistant = Agent(
            name="Code Assistant",
            instructions="""
            You specialise in software engineering guidance. Focus on code
            quality, architecture, and modern best practices. Provide
            step-by-step reasoning when helpful.
            """,
            handoff_description="Handles software engineering questions and code reviews.",
            model=self._resolve_agent_model(settings, "code_assistant"),
            tools=code_tools,
        )
        data_analyst = Agent(
            name="Data Analyst",
            instructions="""
            You specialise in data interpretation, statistical analysis, and
            communicating insights clearly. When applicable, propose visual
            summaries or sanity checks.
            """,
            handoff_description="Supports analytical and quantitative queries.",
            model=self._resolve_agent_model(settings, "data_analyst"),
            tools=data_tools,
        )
        triage_instructions = prompt_with_handoff_instructions(
            """
            You are the primary triage assistant. Handle general inquiries
            with a helpful, professional tone and decide when to leverage
            specialised teammates. Provide concise, actionable answers, and
            hand off to the code or data analyst agents when they are better
            suited to respond.
            """
        )
        triage_agent = Agent(
            name="Triage Assistant",
            instructions=triage_instructions,
            model=self._resolve_agent_model(settings, "triage"),
            tools=triage_tools,
            handoffs=[handoff(code_assistant), handoff(data_analyst)],
        )

        self._register_agent(
            "code_assistant",
            code_assistant,
            "Handles software engineering questions and code reviews.",
        )
        self._register_agent(
            "data_analyst",
            data_analyst,
            "Supports analytical and quantitative queries.",
        )
        self._register_agent(
            "triage",
            triage_agent,
            "Primary triage assistant orchestrating handoffs.",
        )

    def _register_agent(self, key: str, agent: Agent, description: str) -> None:
        capabilities = self._AGENT_CAPABILITIES.get(key, ())
        self._agents[key] = agent
        self._descriptors[key] = AgentDescriptor(
            key=key,
            display_name=agent.name,
            description=description.strip(),
            model=str(agent.model),
            capabilities=capabilities,
        )

    def _select_tools(self, agent_key: str) -> list[Any]:
        capabilities = self._AGENT_CAPABILITIES.get(agent_key, ())
        return self._tool_registry.get_tools_for_agent(
            agent_key, capabilities=capabilities
        )

    def _resolve_agent_model(self, settings: Settings, agent_key: str) -> str:
        overrides = {
            "triage": settings.agent_triage_model,
            "code_assistant": settings.agent_code_model,
            "data_analyst": settings.agent_data_model,
        }
        return overrides.get(agent_key) or settings.agent_default_model


__all__ = ["OpenAIAgentRegistry"]
