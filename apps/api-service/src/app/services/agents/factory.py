"""Composition helpers for AgentService."""

from __future__ import annotations

from app.bootstrap.container import get_container, wire_asset_service, wire_storage_service
from app.core.settings import get_settings
from app.domain.conversations import ConversationRepository
from app.infrastructure.db import get_async_sessionmaker
from app.services.agents.policy import AgentRuntimePolicy
from app.services.agents.provider_registry import AgentProviderRegistry, get_provider_registry
from app.services.agents.service import AgentService
from app.services.assets.service import AssetService
from app.services.containers import (
    ContainerFilesGateway,
    ContainerService,
    OpenAIContainerFilesGateway,
)
from app.services.conversation_service import ConversationService, get_conversation_service
from app.services.storage.service import StorageService
from app.services.usage_counters import UsageCounterService, get_usage_counter_service
from app.services.usage_recorder import UsageRecorder
from app.services.vector_stores.service import VectorStoreService


def build_agent_service(
    *,
    conversation_service: ConversationService | None = None,
    conversation_repository: ConversationRepository | None = None,
    usage_recorder: UsageRecorder | None = None,
    usage_counter_service: UsageCounterService | None = None,
    provider_registry: AgentProviderRegistry | None = None,
    container_service: ContainerService | None = None,
    container_files_gateway: ContainerFilesGateway | None = None,
    storage_service: StorageService | None = None,
    asset_service: AssetService | None = None,
    policy: AgentRuntimePolicy | None = None,
    vector_store_service: VectorStoreService | None = None,
    catalog_service=None,
) -> AgentService:
    conversation_service = conversation_service or get_conversation_service()
    provider_registry = provider_registry or get_provider_registry()
    usage_counter_service = usage_counter_service or get_usage_counter_service()
    policy = policy or AgentRuntimePolicy.from_env()
    if container_files_gateway is None:
        container_files_gateway = OpenAIContainerFilesGateway(get_settings)

    return AgentService(
        conversation_service=conversation_service,
        conversation_repo=conversation_repository,
        usage_recorder=usage_recorder,
        usage_counter_service=usage_counter_service,
        provider_registry=provider_registry,
        container_service=container_service,
        container_files_gateway=container_files_gateway,
        storage_service=storage_service,
        asset_service=asset_service,
        policy=policy,
        vector_store_service=vector_store_service,
        catalog_service=catalog_service,
    )


def get_agent_service() -> AgentService:
    container = get_container()
    if container.session_factory is None:
        container.session_factory = get_async_sessionmaker()
    if container.agent_service is None:
        if container.storage_service is None:
            wire_storage_service(container)
        if container.asset_service is None:
            wire_asset_service(container)
        container.agent_service = build_agent_service(
            conversation_service=container.conversation_service,
            conversation_repository=None,
            usage_recorder=container.usage_recorder,
            usage_counter_service=get_usage_counter_service(),
            provider_registry=get_provider_registry(),
            container_service=container.container_service,
            storage_service=container.storage_service,
            asset_service=container.asset_service,
            vector_store_service=container.vector_store_service,
        )
    return container.agent_service


__all__ = ["AgentService", "build_agent_service", "get_agent_service"]
