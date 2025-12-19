"""Workflow catalog helpers kept separate from workflow execution."""

from __future__ import annotations

import base64
import json
from collections.abc import Iterable
from dataclasses import dataclass

from app.workflows._shared.registry import WorkflowRegistry
from app.workflows._shared.specs import WorkflowDescriptor

DEFAULT_PAGE_SIZE = 24
MAX_PAGE_SIZE = 100


@dataclass(slots=True)
class WorkflowCatalogPage:
    items: list[WorkflowDescriptor]
    next_cursor: str | None
    total: int


class WorkflowCatalogService:
    """Read-only catalog for available workflows."""

    def __init__(self, registry: WorkflowRegistry) -> None:
        self._registry = registry

    def list_workflows(self) -> list[WorkflowDescriptor]:
        """Return all workflows registered with the platform."""

        descriptors = list(self._registry.list_descriptors())
        # Belt-and-suspenders: ensure deterministic ordering even if registry
        # implementation changes in the future.
        return sorted(descriptors, key=lambda desc: desc.key)

    def list_workflows_page(
        self, *, limit: int | None, cursor: str | None, search: str | None
    ) -> WorkflowCatalogPage:
        """
        Return a paginated slice of workflows.

        - limit: maximum number of items to return (None uses DEFAULT_PAGE_SIZE)
        - cursor: opaque position token from a previous response
        - search: optional case-insensitive match against key, display_name, description
        """

        descriptors = self.list_workflows()
        filtered = self._apply_search(descriptors, search)

        page_size = self._normalize_limit(limit)
        start_index = self._resolve_start_index(filtered, cursor)
        end_index = start_index + page_size
        page_descriptors = filtered[start_index:end_index]

        next_cursor = (
            self._encode_cursor(page_descriptors[-1].key)
            if end_index < len(filtered)
            else None
        )

        return WorkflowCatalogPage(
            items=page_descriptors,
            next_cursor=next_cursor,
            total=len(filtered),
        )

    @staticmethod
    def _apply_search(
        descriptors: Iterable[WorkflowDescriptor], search: str | None
    ) -> list[WorkflowDescriptor]:
        if not search:
            return list(descriptors)

        needle = search.lower()

        def _matches(desc: WorkflowDescriptor) -> bool:
            fields = [desc.key, desc.display_name, desc.description]
            return any(val and needle in val.lower() for val in fields)

        return [desc for desc in descriptors if _matches(desc)]

    @staticmethod
    def _normalize_limit(limit: int | None) -> int:
        if limit is None:
            return DEFAULT_PAGE_SIZE
        if limit < 1:
            raise ValueError("limit must be at least 1")
        return min(limit, MAX_PAGE_SIZE)

    def _resolve_start_index(
        self, descriptors: list[WorkflowDescriptor], cursor: str | None
    ) -> int:
        if cursor is None:
            return 0
        target = self._decode_cursor(cursor)
        for idx, descriptor in enumerate(descriptors):
            if descriptor.key == target:
                return idx + 1
        raise ValueError("Invalid pagination cursor")

    @staticmethod
    def _encode_cursor(workflow_key: str) -> str:
        payload = {"workflow": workflow_key}
        raw = json.dumps(payload).encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("utf-8")

    @staticmethod
    def _decode_cursor(cursor: str) -> str:
        try:
            data = json.loads(base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8"))
            workflow = data.get("workflow")
            if not isinstance(workflow, str) or not workflow:
                raise ValueError("Invalid pagination cursor")
            return workflow
        except Exception as exc:  # pragma: no cover - defensive
            raise ValueError("Invalid pagination cursor") from exc


__all__ = [
    "WorkflowCatalogPage",
    "WorkflowCatalogService",
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
]
