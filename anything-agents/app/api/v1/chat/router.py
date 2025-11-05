"""Chat-related API endpoints."""

import json
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.v1.chat.schemas import AgentChatRequest, AgentChatResponse, StreamingChatResponse
from app.services.agent_service import agent_service


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=AgentChatResponse)
async def chat_with_agent(request: AgentChatRequest) -> AgentChatResponse:
    """Send a message to the agent framework and receive a full response."""

    try:
        return await agent_service.chat(request)
    except Exception as exc:  # noqa: BLE001 - map to HTTP
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat request: {exc}",
        ) from exc


@router.post("/stream")
async def stream_chat_with_agent(request: AgentChatRequest) -> StreamingResponse:
    """Provide an SSE stream for real-time agent responses."""

    async def _event_stream() -> AsyncIterator[str]:
        try:
            async for chunk in agent_service.chat_stream(request):
                payload = StreamingChatResponse(
                    chunk=chunk.chunk,
                    conversation_id=chunk.conversation_id,
                    is_complete=chunk.is_complete,
                    agent_used=chunk.agent_used,
                )
                yield f"data: {payload.model_dump_json()}\n\n"

                if payload.is_complete:
                    break
        except Exception as exc:  # noqa: BLE001 - map to structured SSE error
            error_payload = {
                "error": str(exc),
                "conversation_id": request.conversation_id or "unknown",
                "is_complete": True,
                "chunk": "",
            }
            yield f"data: {json.dumps(error_payload)}\n\n"

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "text/event-stream",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "*",
    }

    return StreamingResponse(
        _event_stream(),
        media_type="text/event-stream",
        headers=headers,
    )
