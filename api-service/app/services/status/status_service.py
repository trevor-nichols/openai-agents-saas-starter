"""Service façade for platform status snapshots."""

from __future__ import annotations

from app.domain.status import PlatformStatusRepository, PlatformStatusSnapshot
from app.infrastructure.status.repository import InMemoryStatusRepository


class StatusService:
    """Orchestrate retrieval of platform status snapshots."""

    def __init__(self, repository: PlatformStatusRepository | None = None) -> None:
        self._repository: PlatformStatusRepository = repository or InMemoryStatusRepository()

    def set_repository(self, repository: PlatformStatusRepository) -> None:
        """Inject a different repository (used by tests)."""

        self._repository = repository

    async def get_platform_status(self) -> PlatformStatusSnapshot:
        """Return the latest status snapshot."""

        return await self._repository.fetch_snapshot()


_status_service = StatusService()


def get_status_service() -> StatusService:
    """Return the singleton status service."""

    return _status_service


status_service = _status_service
