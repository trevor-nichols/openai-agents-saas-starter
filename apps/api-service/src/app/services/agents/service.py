"""High-level facade for agent interactions."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from app.api.v1.agents.schemas import AgentStatus, AgentSummary
from app.api.v1.chat.schemas import AgentChatRequest, AgentChatResponse
from app.domain.ai.models import AgentStreamEvent
from app.domain.conversations import ConversationRepository
from app.services.agents.asset_linker import AssetLinker
from app.services.agents.attachments import AttachmentService
from app.services.agents.catalog import AgentCatalogPage, AgentCatalogService
from app.services.agents.chat_run import ChatRunOrchestrator
from app.services.agents.chat_stream import ChatStreamOrchestrator
from app.services.agents.container_context import ContainerContextService
from app.services.agents.context import ConversationActorContext
from app.services.agents.event_log import EventProjector
from app.services.agents.input_attachments import InputAttachmentService
from app.services.agents.interaction_context import InteractionContextBuilder
from app.services.agents.policy import AgentRuntimePolicy
from app.services.agents.provider_registry import AgentProviderRegistry
from app.services.agents.run_finalize import RunFinalizer
from app.services.agents.session_manager import SessionManager
from app.services.agents.usage import UsageService
from app.services.agents.user_input import UserInputResolver
from app.services.assets.service import AssetService
from app.services.containers import ContainerFilesGateway, ContainerService
from app.services.conversation_service import ConversationService
from app.services.storage.service import StorageService
from app.services.usage_counters import UsageCounterService
from app.services.usage_recorder import UsageRecorder
from app.services.vector_stores.service import VectorStoreService


class AgentService:
    """High-level facade that orchestrates agent interactions."""

    def __init__(
        self,
        *,
        conversation_service: ConversationService,
        provider_registry: AgentProviderRegistry,
        policy: AgentRuntimePolicy,
        conversation_repo: ConversationRepository | None = None,
        usage_recorder: UsageRecorder | None = None,
        usage_counter_service: UsageCounterService | None = None,
        container_service: ContainerService | None = None,
        container_files_gateway: ContainerFilesGateway | None = None,
        storage_service: StorageService | None = None,
        asset_service: AssetService | None = None,
        interaction_builder: InteractionContextBuilder | None = None,
        vector_store_service: VectorStoreService | None = None,
        session_manager: SessionManager | None = None,
        attachment_service: AttachmentService | None = None,
        input_attachment_service: InputAttachmentService | None = None,
        usage_service: UsageService | None = None,
        catalog_service: AgentCatalogService | None = None,
        event_projector: EventProjector | None = None,
        container_context_service: ContainerContextService | None = None,
        run_finalizer: RunFinalizer | None = None,
        input_resolver: UserInputResolver | None = None,
        asset_linker: AssetLinker | None = None,
    ) -> None:
        self._conversation_service = conversation_service
        if conversation_repo is not None:
            self._conversation_service.set_repository(conversation_repo)

        self._provider_registry = provider_registry
        self._policy = policy
        self._storage_service = storage_service
        self._asset_service = asset_service

        if session_manager is None:
            session_manager = SessionManager(self._conversation_service, self._policy)
        self._session_manager = session_manager

        if attachment_service is None:
            attachment_service = AttachmentService(
                self._require_storage_service,
                container_files_gateway_resolver=(
                    (lambda: container_files_gateway) if container_files_gateway else None
                ),
                asset_service_resolver=(lambda: asset_service) if asset_service else None,
            )
        self._attachment_service = attachment_service

        if input_attachment_service is None:
            input_attachment_service = InputAttachmentService(
                self._require_storage_service,
                asset_service_resolver=(lambda: asset_service) if asset_service else None,
            )
        self._input_attachment_service = input_attachment_service

        if interaction_builder is None:
            interaction_builder = InteractionContextBuilder(
                container_service=container_service,
                vector_store_service=vector_store_service,
            )
        self._interaction_builder = interaction_builder

        if container_context_service is None:
            container_context_service = ContainerContextService(container_service=container_service)
        self._container_context_service = container_context_service

        if event_projector is None:
            event_projector = EventProjector(self._conversation_service)
        self._event_projector = event_projector

        if usage_service is None:
            usage_service = UsageService(
                usage_recorder,
                usage_counter_service,
                self._conversation_service,
            )
        self._usage_service = usage_service

        if catalog_service is None:
            catalog_service = AgentCatalogService(self._provider_registry)
        self._catalog_service = catalog_service

        if input_resolver is None:
            input_resolver = UserInputResolver(self._input_attachment_service)
        self._input_resolver = input_resolver

        if asset_linker is None:
            asset_linker = AssetLinker(asset_service)
        self._asset_linker = asset_linker

        if run_finalizer is None:
            run_finalizer = RunFinalizer(
                session_manager=self._session_manager,
                usage_service=self._usage_service,
                container_context_service=self._container_context_service,
                event_projector=self._event_projector,
                conversation_service=self._conversation_service,
            )
        self._run_finalizer = run_finalizer

        self._chat_run = ChatRunOrchestrator(
            provider_registry=self._provider_registry,
            interaction_builder=self._interaction_builder,
            conversation_service=self._conversation_service,
            session_manager=self._session_manager,
            attachment_service=self._attachment_service,
            input_resolver=self._input_resolver,
            finalizer=self._run_finalizer,
            asset_linker=self._asset_linker,
        )
        self._chat_stream = ChatStreamOrchestrator(
            provider_registry=self._provider_registry,
            interaction_builder=self._interaction_builder,
            conversation_service=self._conversation_service,
            session_manager=self._session_manager,
            attachment_service=self._attachment_service,
            input_resolver=self._input_resolver,
            finalizer=self._run_finalizer,
            asset_linker=self._asset_linker,
        )

    async def chat(
        self, request: AgentChatRequest, *, actor: ConversationActorContext
    ) -> AgentChatResponse:
        return await self._chat_run.run(request, actor=actor)

    async def chat_stream(
        self, request: AgentChatRequest, *, actor: ConversationActorContext
    ) -> AsyncGenerator[AgentStreamEvent, None]:
        async for event in self._chat_stream.stream(request, actor=actor):
            yield event

    @property
    def conversation_repository(self):
        """Expose the underlying repository for integration/testing scenarios."""

        return self._conversation_service.repository

    def list_available_agents(self) -> list[AgentSummary]:
        """Return the first page of the catalog using default sizing."""

        return self._catalog_service.list_available_agents()

    def list_available_agents_page(
        self, *, limit: int | None, cursor: str | None, search: str | None
    ) -> AgentCatalogPage:
        """Paginated catalog listing."""

        page = self._catalog_service.list_available_agents_page(
            limit=limit,
            cursor=cursor,
            search=search,
        )
        return page

    def get_agent_status(self, agent_name: str) -> AgentStatus:
        return self._catalog_service.get_agent_status(agent_name)

    def get_tool_information(self) -> dict[str, Any]:
        provider = self._get_provider()
        return dict(provider.tool_overview())

    def _get_provider(self):
        try:
            return self._provider_registry.get_default()
        except RuntimeError as exc:
            raise RuntimeError(
                "No agent providers registered. Register a provider (e.g., build_openai_provider)"
                " before invoking AgentService, or use the test fixture that populates the"
                " AgentProviderRegistry."
            ) from exc

    def _require_storage_service(self) -> StorageService:
        if self._storage_service is None:
            raise RuntimeError("Storage service is not configured")
        return self._storage_service


__all__ = ["AgentService", "ConversationActorContext"]
