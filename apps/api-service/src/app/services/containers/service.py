"""Service layer for OpenAI containers used by the Code Interpreter tool."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from datetime import datetime
from http import HTTPStatus
from time import perf_counter
from typing import Any

from openai import AsyncOpenAI, BadRequestError, NotFoundError
from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.settings import Settings, get_settings
from app.infrastructure.db import get_async_sessionmaker
from app.infrastructure.persistence.containers.models import AgentContainer, Container
from app.observability.metrics import (
    CONTAINER_OPERATION_DURATION_SECONDS,
    CONTAINER_OPERATIONS_TOTAL,
)
from app.services.activity import activity_service

logger = logging.getLogger(__name__)


class ContainerNotFoundError(RuntimeError):
    pass


class ContainerQuotaError(RuntimeError):
    pass


class ContainerNameConflictError(RuntimeError):
    pass


class ContainerService:
    """Coordinates OpenAI container API calls with local persistence."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        settings_factory: Callable[[], Settings],
        *,
        get_tenant_api_key: Callable[[uuid.UUID, Settings], str] | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._settings_factory = settings_factory
        self._get_tenant_api_key = get_tenant_api_key
        self._binding_cache: dict[tuple[uuid.UUID, str], str] = {}

    # -------- Public API --------
    async def create_container(
        self,
        *,
        tenant_id: uuid.UUID,
        owner_user_id: uuid.UUID | None,
        name: str,
        memory_limit: str | None = None,
        expires_after: dict[str, Any] | None = None,
        file_ids: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Container:
        settings = self._settings_factory()
        memory = memory_limit or settings.container_default_auto_memory
        self._enforce_memory_limit(memory, settings)
        await self._enforce_container_limit(tenant_id, settings)
        await self._ensure_unique_name(tenant_id, name)

        client = self._openai_client(tenant_id)
        t0 = perf_counter()
        payload: dict[str, Any] = {"name": name, "memory_limit": memory}
        if expires_after is not None:
            payload["expires_after"] = expires_after
        if file_ids:
            payload["file_ids"] = file_ids
        try:
            remote = await client.containers.create(**payload)
            self._observe("create", "success", t0)
        except Exception as exc:
            self._observe("create", "error", t0)
            logger.warning(
                "container.create.failed",
                exc_info=exc,
                extra={"tenant_id": str(tenant_id)},
            )
            raise

        status = getattr(remote, "status", None) or "running"
        last_active_at = _coerce_ts(getattr(remote, "last_active_at", None))
        openai_id = getattr(remote, "id", None)
        if not openai_id:
            raise RuntimeError("OpenAI container response missing id")

        async with self._session_factory() as session:
            container = Container(
                id=uuid.uuid4(),
                openai_id=openai_id,
                tenant_id=tenant_id,
                owner_user_id=owner_user_id,
                name=name,
                memory_limit=memory,
                status=status,
                expires_after=expires_after,
                last_active_at=last_active_at,
                metadata_json=metadata or {},
            )
            session.add(container)
            try:
                await session.commit()
            except IntegrityError as exc:
                await session.rollback()
                await self._safe_delete_remote(client, openai_id)
                message = str(exc)
                if "uq_containers_tenant_name" in message:
                    raise ContainerNameConflictError(
                        "A container with this name already exists"
                    ) from exc
                raise
            except Exception:
                await session.rollback()
                await self._safe_delete_remote(client, openai_id)
                raise
            await session.refresh(container)
        try:
            await activity_service.record(
                tenant_id=str(tenant_id),
                action="container.lifecycle",
                actor_id=str(owner_user_id) if owner_user_id else None,
                actor_type="user" if owner_user_id else "system",
                object_type="container",
                object_id=str(container.id),
                status="success",
                metadata={"container_id": str(container.id), "event": "created"},
                source="api",
            )
        except Exception:  # pragma: no cover - best effort
            logger.debug("activity.container.create.skipped", exc_info=True)
        return container

    async def list_containers(
        self, *, tenant_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> tuple[list[Container], int]:
        async with self._session_factory() as session:
            total = await session.scalar(
                select(func.count())
                .select_from(Container)
                .where(Container.tenant_id == tenant_id, Container.deleted_at.is_(None))
            )
            result = await session.scalars(
                select(Container)
                .where(Container.tenant_id == tenant_id, Container.deleted_at.is_(None))
                .order_by(Container.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            return list(result), int(total or 0)

    async def get_container(self, *, container_id: uuid.UUID, tenant_id: uuid.UUID) -> Container:
        container = await self._get_container(container_id, tenant_id)
        return container

    async def delete_container(self, *, container_id: uuid.UUID, tenant_id: uuid.UUID) -> None:
        container = await self._get_container(container_id, tenant_id)
        client = self._openai_client(tenant_id)
        t0 = perf_counter()
        try:
            await client.containers.delete(container.openai_id)
            self._observe("delete", "success", t0)
        except NotFoundError:
            # Treat missing remote as success so local cleanup can proceed.
            self._observe("delete", "success", t0)
        except BadRequestError as exc:
            # Some clients return 404/410 as BadRequest; check status.
            status = getattr(exc, "status_code", None)
            if status in {HTTPStatus.NOT_FOUND, HTTPStatus.GONE}:
                self._observe("delete", "success", t0)
            else:
                self._observe("delete", "error", t0)
                logger.warning(
                    "container.delete.failed",
                    exc_info=exc,
                    extra={"tenant_id": str(tenant_id), "container_id": str(container_id)},
                )
                raise
        except Exception as exc:
            self._observe("delete", "error", t0)
            logger.warning(
                "container.delete.failed",
                exc_info=exc,
                extra={"tenant_id": str(tenant_id), "container_id": str(container_id)},
            )
            raise

        async with self._session_factory() as session:
            agent_keys = list(
                await session.scalars(
                    select(AgentContainer.agent_key).where(
                        AgentContainer.container_id == container_id,
                        AgentContainer.tenant_id == tenant_id,
                    )
                )
            )
            await session.execute(
                sa_delete(AgentContainer).where(
                    AgentContainer.container_id == container_id,
                    AgentContainer.tenant_id == tenant_id,
                )
            )
            db_container = await session.get(Container, container_id)
            if db_container:
                db_container.deleted_at = datetime.utcnow()
                db_container.status = "deleted"
            await session.commit()

        for agent_key in agent_keys:
            self._binding_cache.pop((tenant_id, agent_key), None)
        try:
            await activity_service.record(
                tenant_id=str(tenant_id),
                action="container.lifecycle",
                actor_id=str(container.owner_user_id) if container.owner_user_id else None,
                actor_type="user" if container.owner_user_id else "system",
                object_type="container",
                object_id=str(container.id),
                status="success",
                metadata={"container_id": str(container.id), "event": "deleted"},
                source="api",
            )
        except Exception:  # pragma: no cover - best effort
            logger.debug("activity.container.delete.skipped", exc_info=True)

    async def bind_agent(
        self, *, tenant_id: uuid.UUID, agent_key: str, container_id: uuid.UUID
    ) -> None:
        container = await self._get_container(container_id, tenant_id)
        async with self._session_factory() as session:
            # Ensure single binding per agent/tenant by removing existing rows
            await session.execute(
                sa_delete(AgentContainer).where(
                    AgentContainer.agent_key == agent_key,
                    AgentContainer.tenant_id == tenant_id,
                )
            )
            binding = AgentContainer(
                agent_key=agent_key,
                container_id=container.id,
                tenant_id=tenant_id,
            )
            session.add(binding)
            await session.commit()
        self._binding_cache[(tenant_id, agent_key)] = container.openai_id
        try:
            await activity_service.record(
                tenant_id=str(tenant_id),
                action="container.lifecycle",
                actor_type="system",
                object_type="container",
                object_id=str(container.id),
                status="success",
                metadata={
                    "container_id": str(container.id),
                    "event": "bound",
                    "agent_key": agent_key,
                },
                source="api",
            )
        except Exception:  # pragma: no cover - best effort
            logger.debug("activity.container.bind.skipped", exc_info=True)

    async def unbind_agent(self, *, tenant_id: uuid.UUID, agent_key: str) -> None:
        async with self._session_factory() as session:
            container_id = await session.scalar(
                select(AgentContainer.container_id).where(
                    AgentContainer.agent_key == agent_key,
                    AgentContainer.tenant_id == tenant_id,
                )
            )
            await session.execute(
                sa_delete(AgentContainer).where(
                    AgentContainer.agent_key == agent_key,
                    AgentContainer.tenant_id == tenant_id,
                )
            )
            await session.commit()
        self._binding_cache.pop((tenant_id, agent_key), None)
        try:
            if container_id:
                await activity_service.record(
                    tenant_id=str(tenant_id),
                    action="container.lifecycle",
                    actor_type="system",
                    object_type="container",
                    object_id=str(container_id),
                    status="success",
                    metadata={
                        "container_id": str(container_id),
                        "event": "unbound",
                        "agent_key": agent_key,
                    },
                    source="api",
                )
        except Exception:  # pragma: no cover - best effort
            logger.debug("activity.container.unbind.skipped", exc_info=True)

    async def resolve_agent_container_openai_id(
        self, *, tenant_id: uuid.UUID, agent_key: str
    ) -> str | None:
        cache_key = (tenant_id, agent_key)
        if cache_key in self._binding_cache:
            return self._binding_cache[cache_key]
        async with self._session_factory() as session:
            result = await session.execute(
                select(Container.openai_id)
                .join(AgentContainer, AgentContainer.container_id == Container.id)
                .where(
                    AgentContainer.agent_key == agent_key,
                    AgentContainer.tenant_id == tenant_id,
                    Container.deleted_at.is_(None),
                )
            )
            openai_id = result.scalar_one_or_none()
            if openai_id:
                self._binding_cache[cache_key] = openai_id
            return openai_id

    async def list_agent_bindings(self, *, tenant_id: uuid.UUID) -> dict[str, str]:
        """Return agent_key -> openai_container_id for a tenant (excludes deleted containers)."""

        async with self._session_factory() as session:
            result = await session.execute(
                select(AgentContainer.agent_key, Container.openai_id)
                .join(Container, Container.id == AgentContainer.container_id)
                .where(
                    AgentContainer.tenant_id == tenant_id,
                    Container.deleted_at.is_(None),
                )
            )
            bindings = {row[0]: row[1] for row in result.fetchall()}
            # refresh cache
            for agent_key, openai_id in bindings.items():
                self._binding_cache[(tenant_id, agent_key)] = openai_id
            return bindings

    # -------- Internal helpers --------
    async def _get_container(self, container_id: uuid.UUID, tenant_id: uuid.UUID) -> Container:
        async with self._session_factory() as session:
            container = await session.get(Container, container_id)
            if (
                not container
                or container.deleted_at is not None
                or container.tenant_id != tenant_id
            ):
                raise ContainerNotFoundError(f"Container {container_id} not found")
            return container

    async def _ensure_unique_name(self, tenant_id: uuid.UUID, name: str) -> None:
        async with self._session_factory() as session:
            existing = await session.scalar(
                select(Container).where(
                    Container.tenant_id == tenant_id,
                    Container.name == name,
                    Container.deleted_at.is_(None),
                )
            )
            if existing:
                raise ContainerNameConflictError("A container with this name already exists")

    async def _enforce_container_limit(self, tenant_id: uuid.UUID, settings: Settings) -> None:
        async with self._session_factory() as session:
            total = await session.scalar(
                select(func.count())
                .select_from(Container)
                .where(Container.tenant_id == tenant_id, Container.deleted_at.is_(None))
            )
            if int(total or 0) >= settings.container_max_containers_per_tenant:
                raise ContainerQuotaError("Maximum containers reached for tenant")

    def _enforce_memory_limit(self, memory_limit: str, settings: Settings) -> None:
        allowed = set(settings.container_allowed_memory_tiers or [])
        if memory_limit not in allowed:
            raise ContainerQuotaError("Memory tier not allowed for containers")

    def _openai_client(self, tenant_id: uuid.UUID) -> AsyncOpenAI:
        settings = self._settings_factory()
        api_key = (
            self._get_tenant_api_key(tenant_id, settings)
            if self._get_tenant_api_key
            else settings.openai_api_key
        )
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        return AsyncOpenAI(api_key=api_key)

    def _observe(self, operation: str, result: str, start_time: float) -> None:
        duration = max(perf_counter() - start_time, 0.0)
        CONTAINER_OPERATIONS_TOTAL.labels(operation=operation, result=result).inc()
        CONTAINER_OPERATION_DURATION_SECONDS.labels(operation=operation, result=result).observe(
            duration
        )

    async def _safe_delete_remote(self, client: AsyncOpenAI, remote_id: str) -> None:
        try:
            await client.containers.delete(remote_id)
        except Exception as exc:  # pragma: no cover - defensive cleanup
            logger.warning(
                "container.cleanup_failed",
                exc_info=exc,
                extra={"remote_id": remote_id},
            )


def _coerce_ts(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromtimestamp(int(value))
    except Exception:
        return None


# Singleton helpers ---------------------------------------------------------
_SERVICE_SINGLETON: ContainerService | None = None


def get_container_service() -> ContainerService:
    global _SERVICE_SINGLETON
    if _SERVICE_SINGLETON is None:
        settings = get_settings()
        _SERVICE_SINGLETON = ContainerService(get_async_sessionmaker(), lambda: settings)
    return _SERVICE_SINGLETON


class _ContainerServiceHandle:
    def __getattr__(self, name: str):
        return getattr(get_container_service(), name)


container_service = _ContainerServiceHandle()


__all__ = [
    "ContainerService",
    "ContainerNotFoundError",
    "ContainerQuotaError",
    "ContainerNameConflictError",
    "get_container_service",
    "container_service",
]
