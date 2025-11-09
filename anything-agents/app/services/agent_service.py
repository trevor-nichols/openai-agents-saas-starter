"""Core agent orchestration services."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any, ClassVar

from agents import Agent, function_tool, handoff, trace
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
from agents.extensions.memory.sqlalchemy_session import SQLAlchemySession
from openai.types.responses import ResponseTextDeltaEvent

from app.api.v1.agents.schemas import AgentStatus, AgentSummary
from app.api.v1.chat.schemas import AgentChatRequest, AgentChatResponse, StreamingChatResponse
from app.api.v1.conversations.schemas import ChatMessage, ConversationHistory, ConversationSummary
from app.core.config import get_settings
from app.domain.conversations import (
    ConversationMessage,
    ConversationMetadata,
    ConversationRepository,
    ConversationSessionState,
)
from app.infrastructure.openai import runner as agent_runner
from app.infrastructure.openai.sessions import build_conversation_session
from app.utils.tools import ToolRegistry, initialize_tools

from .conversation_service import conversation_service


@function_tool
async def get_current_time() -> str:
    """Return the current UTC timestamp."""

    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")


@function_tool
async def search_conversations(query: str) -> str:
    """Search cached conversations for a query string."""

    results = await conversation_service.search(query)
    if not results:
        return "No conversations contained the requested text."

    top_matches = "\n".join(f"{result.conversation_id}: {result.preview}" for result in results[:5])
    return f"Found {len(results)} matching conversations:\n{top_matches}"


class AgentRegistry:
    """Manage lifecycle of agent instances and their tool configuration."""

    _AGENT_CAPABILITIES: ClassVar[dict[str, tuple[str, ...]]] = {
        "triage": ("general", "search", "handoff"),
        "code_assistant": ("code", "search"),
        "data_analyst": ("analysis", "search"),
    }

    def __init__(self, tool_registry: ToolRegistry):
        self._settings = get_settings()
        self._tool_registry = tool_registry
        self._agents: dict[str, Agent] = {}
        self._register_builtin_tools()
        self._build_default_agents()

    def _register_builtin_tools(self) -> None:
        self._tool_registry.register_tool(
            get_current_time,
            category="utility",
            metadata={
                "description": "Return the current UTC timestamp.",
                "core": True,
                "capabilities": ["general"],
            },
        )
        self._tool_registry.register_tool(
            search_conversations,
            category="conversation",
            metadata={
                "description": "Search cached conversation history.",
                "core": True,
                "capabilities": ["conversation", "search"],
            },
        )

    def _build_default_agents(self) -> None:
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
            model="gpt-4.1-2025-04-14",
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
            model="gpt-4.1-2025-04-14",
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
            model="gpt-4.1-2025-04-14",
            tools=triage_tools,
            handoffs=[handoff(code_assistant), handoff(data_analyst)],
        )

        self._agents["code_assistant"] = code_assistant
        self._agents["data_analyst"] = data_analyst
        self._agents["triage"] = triage_agent

    def _select_tools(self, agent_key: str) -> list[Any]:
        capabilities = self._AGENT_CAPABILITIES.get(agent_key, ())
        return self._tool_registry.get_tools_for_agent(
            agent_key,
            capabilities=capabilities,
        )

    def get_agent(self, agent_name: str) -> Agent | None:
        return self._agents.get(agent_name)

    def list_agents(self) -> list[str]:
        return sorted(self._agents.keys())

    def tool_overview(self) -> dict[str, Any]:
        return {
            "total_tools": len(self._tool_registry.list_tool_names()),
            "tool_names": self._tool_registry.list_tool_names(),
            "categories": self._tool_registry.list_categories(),
        }


class AgentService:
    """Core façade that orchestrates agent interactions."""

    def __init__(self, conversation_repo: ConversationRepository | None = None):
        if conversation_repo is not None:
            conversation_service.set_repository(conversation_repo)

        self._tool_registry = initialize_tools()
        self._agent_registry = AgentRegistry(self._tool_registry)

    async def chat(self, request: AgentChatRequest) -> AgentChatResponse:
        conversation_id = request.conversation_id or str(uuid.uuid4())
        session_id, session_handle = await self._acquire_sdk_session(conversation_id)

        preferred_agent = request.agent_type or "triage"
        agent_name, agent = self._resolve_agent(preferred_agent)

        user_message = ConversationMessage(role="user", content=request.message)
        await conversation_service.append_message(
            conversation_id,
            user_message,
            metadata=ConversationMetadata(
                agent_entrypoint=preferred_agent,
                active_agent=None,
                sdk_session_id=session_id,
            ),
        )

        with trace(workflow_name="Agent Chat", group_id=conversation_id):
            result = await agent_runner.run(
                agent,
                request.message,
                session=session_handle,
                conversation_id=conversation_id,
            )

        assistant_message = ConversationMessage(
            role="assistant",
            content=str(result.final_output),
        )
        await conversation_service.append_message(
            conversation_id,
            assistant_message,
            metadata=ConversationMetadata(
                agent_entrypoint=preferred_agent,
                active_agent=agent_name,
                sdk_session_id=session_id,
            ),
        )
        await self._sync_session_state(conversation_id, session_id)

        return AgentChatResponse(
            response=str(result.final_output),
            conversation_id=conversation_id,
            agent_used=agent_name,
            handoff_occurred=False,
            metadata={
                "model_used": agent.model,
                "tools_available": self._tool_registry.list_tool_names(),
            },
        )

    async def chat_stream(
        self, request: AgentChatRequest
    ) -> AsyncGenerator[StreamingChatResponse, None]:
        conversation_id = request.conversation_id or str(uuid.uuid4())
        session_id, session_handle = await self._acquire_sdk_session(conversation_id)

        preferred_agent = request.agent_type or "triage"
        agent_name, agent = self._resolve_agent(preferred_agent)

        user_message = ConversationMessage(role="user", content=request.message)
        await conversation_service.append_message(
            conversation_id,
            user_message,
            metadata=ConversationMetadata(
                agent_entrypoint=preferred_agent,
                active_agent=None,
                sdk_session_id=session_id,
            ),
        )

        complete_response = ""

        with trace(workflow_name="Agent Chat Stream", group_id=conversation_id):
            stream = agent_runner.run_streamed(
                agent,
                request.message,
                session=session_handle,
                conversation_id=conversation_id,
            )

            async for event in stream.stream_events():
                if event.type == "raw_response_event" and isinstance(
                    event.data, ResponseTextDeltaEvent
                ):
                    chunk = event.data.delta
                    complete_response += chunk
                    yield StreamingChatResponse(
                        chunk=chunk,
                        conversation_id=conversation_id,
                        is_complete=False,
                        agent_used=agent_name,
                    )
                elif event.type == "run_item_stream_event" and (
                    event.item.type == "message_output_item"
                ):
                    yield StreamingChatResponse(
                        chunk="",
                        conversation_id=conversation_id,
                        is_complete=True,
                        agent_used=agent_name,
                    )

        assistant_message = ConversationMessage(
            role="assistant",
            content=complete_response,
        )
        await conversation_service.append_message(
            conversation_id,
            assistant_message,
            metadata=ConversationMetadata(
                agent_entrypoint=preferred_agent,
                active_agent=agent_name,
                sdk_session_id=session_id,
            ),
        )
        await self._sync_session_state(conversation_id, session_id)

    async def get_conversation_history(self, conversation_id: str) -> ConversationHistory:
        messages = await conversation_service.get_messages(conversation_id)
        if not messages:
            raise ValueError(f"Conversation {conversation_id} not found")

        api_messages = [self._to_chat_message(msg) for msg in messages]
        return ConversationHistory(
            conversation_id=conversation_id,
            messages=api_messages,
            created_at=messages[0].timestamp.isoformat(),
            updated_at=messages[-1].timestamp.isoformat(),
        )

    async def list_conversations(self) -> list[ConversationSummary]:
        summaries: list[ConversationSummary] = []

        for record in await conversation_service.iterate_conversations():
            if not record.messages:
                continue

            last_message = record.messages[-1]
            summaries.append(
                ConversationSummary(
                    conversation_id=record.conversation_id,
                    message_count=len(record.messages),
                    last_message=last_message.content[:120],
                    created_at=record.created_at.isoformat(),
                    updated_at=record.updated_at.isoformat(),
                )
            )

        summaries.sort(key=lambda item: item.updated_at, reverse=True)
        return summaries

    async def clear_conversation(self, conversation_id: str) -> None:
        await conversation_service.clear_conversation(conversation_id)

    @property
    def conversation_repository(self):
        """Expose the underlying repository for integration/testing scenarios."""

        return conversation_service.repository

    def list_available_agents(self) -> list[AgentSummary]:
        return [
            AgentSummary(
                name=name,
                status="active",
                description=f"Agent specialised for {name.replace('_', ' ')} tasks.",
            )
            for name in self._agent_registry.list_agents()
        ]

    def get_agent_status(self, agent_name: str) -> AgentStatus:
        agent = self._agent_registry.get_agent(agent_name)
        if not agent:
            raise ValueError(f"Agent '{agent_name}' not found")

        return AgentStatus(
            name=agent_name,
            status="active",
            last_used=None,
            total_conversations=0,
        )

    def get_tool_information(self) -> dict[str, Any]:
        return self._agent_registry.tool_overview()

    def _resolve_agent(self, preferred_name: str) -> tuple[str, Agent]:
        agent = self._agent_registry.get_agent(preferred_name)
        if agent:
            return preferred_name, agent

        fallback = self._agent_registry.get_agent("triage")
        if not fallback:
            raise RuntimeError("No triage agent configured.")
        return "triage", fallback

    async def _acquire_sdk_session(self, conversation_id: str) -> tuple[str, SQLAlchemySession]:
        state = await conversation_service.get_session_state(conversation_id)
        if state and state.sdk_session_id:
            session_id = state.sdk_session_id
        else:
            session_id = conversation_id
        session_handle = build_conversation_session(session_id)
        return session_id, session_handle

    async def _sync_session_state(self, conversation_id: str, session_id: str) -> None:
        await conversation_service.update_session_state(
            conversation_id,
            ConversationSessionState(
                sdk_session_id=session_id,
                last_session_sync_at=datetime.now(UTC),
            ),
        )

    @staticmethod
    def _to_chat_message(message: ConversationMessage) -> ChatMessage:
        return ChatMessage(
            role=message.role,
            content=message.content,
            timestamp=message.timestamp.isoformat(),
        )


agent_service = AgentService()
