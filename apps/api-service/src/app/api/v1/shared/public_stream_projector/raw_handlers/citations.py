from __future__ import annotations

from urllib.parse import urlencode

from app.domain.ai.models import AgentStreamEvent

from ...streaming import (
    ContainerFileCitation,
    FileCitation,
    MessageCitationEvent,
    PublicCitation,
    PublicSseEventBase,
    ToolStatusEvent,
    UrlCitation,
    WebSearchTool,
)
from ..builders import EventBuilder
from ..scopes import item_scope_from_raw, tool_scope
from ..state import ProjectionState, ToolState
from ..tooling import as_search_status
from ..utils import as_dict


def project_citations(
    state: ProjectionState,
    builder: EventBuilder,
    event: AgentStreamEvent,
) -> list[PublicSseEventBase]:
    if (
        event.kind != "raw_response_event"
        or event.raw_type != "response.output_text.annotation.added"
    ):
        return []

    raw = as_dict(event.raw_event) or {}
    scope = item_scope_from_raw(raw)
    raw_content_index = raw.get("content_index")
    content_index = raw_content_index if isinstance(raw_content_index, int) else None
    if scope and content_index is not None:
        message_item_id, message_output_index = scope
    else:
        message_item_id = None
        message_output_index = None

    out: list[PublicSseEventBase] = []
    for ann in event.annotations or []:
        citation_type = ann.get("type")
        if citation_type == "url_citation":
            citation: PublicCitation = UrlCitation.model_validate(ann)
            if isinstance(citation, UrlCitation) and state.last_web_search_tool_call_id:
                tool_call_id = state.last_web_search_tool_call_id
                web_state = state.tool_state.setdefault(
                    tool_call_id,
                    ToolState(tool_type="web_search"),
                )
                sources = web_state.sources or []
                if citation.url not in sources:
                    web_state.sources = [*sources, citation.url]
                    # Citations can arrive after the tool status is already marked completed.
                    # Emit an updated tool.status so the UI can display gathered sources.
                    tool_item_scope = tool_scope(tool_call_id, state=state)
                    if tool_item_scope:
                        tool_item_id, tool_output_index = tool_item_scope
                        out.append(
                            ToolStatusEvent(
                                **builder.item(
                                    kind="tool.status",
                                    item_id=tool_item_id,
                                    output_index=tool_output_index,
                                    provider_seq=event.sequence_number,
                                ),
                                tool=WebSearchTool(
                                    tool_type="web_search",
                                    tool_call_id=tool_call_id,
                                    status=as_search_status(web_state.last_status or "completed"),
                                    query=web_state.query,
                                    sources=web_state.sources,
                                ),
                            )
                        )
        elif citation_type == "container_file_citation":
            citation = ContainerFileCitation.model_validate(ann)
            if not getattr(citation, "url", None) and citation.container_id and citation.file_id:
                qs: dict[str, str] = {"conversation_id": builder.conversation_id}
                if citation.filename:
                    qs["filename"] = citation.filename
                url = (
                    f"/api/v1/openai/containers/{citation.container_id}"
                    f"/files/{citation.file_id}/download"
                )
                citation = citation.model_copy(update={"url": f"{url}?{urlencode(qs)}"})
        else:
            citation = FileCitation.model_validate(ann)

        if (
            message_item_id is not None
            and message_output_index is not None
            and content_index is not None
        ):
            out.append(
                MessageCitationEvent(
                    **builder.item(
                        kind="message.citation",
                        item_id=message_item_id,
                        output_index=message_output_index,
                        provider_seq=event.sequence_number,
                    ),
                    content_index=content_index,
                    citation=citation,
                )
            )

    return out
