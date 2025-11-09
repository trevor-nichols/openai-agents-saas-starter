"""Tool catalogue endpoints."""

from fastapi import APIRouter, Depends

from app.api.dependencies.auth import CurrentUser, require_verified_scopes
from app.services.agent_service import agent_service

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("")
async def list_available_tools(
    _current_user: CurrentUser = Depends(require_verified_scopes("tools:read")),
) -> dict[str, object]:
    """Return metadata about registered tools."""

    return agent_service.get_tool_information()
