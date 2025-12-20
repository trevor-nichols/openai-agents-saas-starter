"""Agent catalog endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies.auth import CurrentUser, require_verified_scopes
from app.api.v1.agents.schemas import AgentListResponse, AgentStatus
from app.services.agents import AgentService, get_agent_service
from app.services.agents.catalog import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=AgentListResponse)
async def list_available_agents(
    limit: int = Query(
        default=DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description="Maximum number of agents to return.",
    ),
    cursor: str | None = Query(
        default=None,
        description="Opaque pagination cursor from a previous page.",
    ),
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=256,
        description="Case-insensitive match against name, display_name, or description.",
    ),
    _current_user: CurrentUser = Depends(require_verified_scopes("tools:read")),
    agent_service: AgentService = Depends(get_agent_service),
) -> AgentListResponse:
    """Return a paginated list of available agents."""

    try:
        page = agent_service.list_available_agents_page(
            limit=limit, cursor=cursor, search=search
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return AgentListResponse(items=page.items, next_cursor=page.next_cursor, total=page.total)


@router.get("/{agent_name}/status", response_model=AgentStatus)
async def get_agent_status(
    agent_name: str,
    _current_user: CurrentUser = Depends(require_verified_scopes("tools:read")),
    agent_service: AgentService = Depends(get_agent_service),
) -> AgentStatus:
    """Return health/status details for a specific agent."""

    try:
        return agent_service.get_agent_status(agent_name)
    except ValueError as exc:  # pragma: no cover - value mapped to HTTP below
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
