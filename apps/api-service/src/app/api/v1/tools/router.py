"""Tool catalogue endpoints."""

from fastapi import APIRouter, Depends

from app.api.dependencies.auth import CurrentUser, require_verified_scopes
from app.api.v1.tools.schemas import ToolCatalogResponse
from app.services.agents import AgentService, get_agent_service

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("", response_model=ToolCatalogResponse)
async def list_available_tools(
    _current_user: CurrentUser = Depends(require_verified_scopes("tools:read")),
    agent_service: AgentService = Depends(get_agent_service),
) -> ToolCatalogResponse:
    """Return metadata about registered tools."""

    return ToolCatalogResponse.model_validate(agent_service.get_tool_information())
