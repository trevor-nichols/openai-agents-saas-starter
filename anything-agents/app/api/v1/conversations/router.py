"""Conversation management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.dependencies.auth import CurrentUser, require_verified_scopes
from app.api.v1.conversations.schemas import ConversationHistory, ConversationSummary
from app.services.agent_service import agent_service

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationSummary])
async def list_conversations(
    _current_user: CurrentUser = Depends(require_verified_scopes("conversations:read")),
) -> list[ConversationSummary]:
    """List stored conversations ordered by recency."""

    return await agent_service.list_conversations()


@router.get("/{conversation_id}", response_model=ConversationHistory)
async def get_conversation(
    conversation_id: str,
    _current_user: CurrentUser = Depends(require_verified_scopes("conversations:read")),
) -> ConversationHistory:
    """Return the full conversation history for a specific conversation."""

    try:
        return await agent_service.get_conversation_history(conversation_id)
    except ValueError as exc:  # pragma: no cover - turned into HTTP below
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    _current_user: CurrentUser = Depends(require_verified_scopes("conversations:delete")),
) -> Response:
    """Remove all stored messages for the given conversation."""

    await agent_service.clear_conversation(conversation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
