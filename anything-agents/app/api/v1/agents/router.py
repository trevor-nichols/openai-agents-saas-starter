"""Agent catalog endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.api.v1.agents.schemas import AgentStatus, AgentSummary
from app.services.agent_service import agent_service

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=list[AgentSummary])
async def list_available_agents() -> list[AgentSummary]:
    """Return all agents registered with the platform."""

    return agent_service.list_available_agents()


@router.get("/{agent_name}/status", response_model=AgentStatus)
async def get_agent_status(agent_name: str) -> AgentStatus:
    """Return health/status details for a specific agent."""

    try:
        return agent_service.get_agent_status(agent_name)
    except ValueError as exc:  # pragma: no cover - value mapped to HTTP below
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
