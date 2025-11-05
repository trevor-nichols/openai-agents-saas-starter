"""Tool catalogue endpoints."""

from fastapi import APIRouter

from app.services.agent_service import agent_service

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("")
async def list_available_tools() -> dict[str, object]:
    """Return metadata about registered tools."""

    return agent_service.get_tool_information()
