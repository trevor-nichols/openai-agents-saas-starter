"""Streaming adapter that normalizes OpenAI SDK events into AgentStreamEvent."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Mapping
from typing import Any

from app.domain.ai import AgentRunUsage, AgentStreamEvent, AgentStreamingHandle
from openai.types.responses import ResponseTextDeltaEvent

from .lifecycle import LifecycleEventSink
from .tool_calls import (
    build_code_interpreter_tool_call,
    build_file_search_tool_call,
    build_image_generation_tool_call,
    build_web_search_tool_call,
    coerce_delta,
    extract_agent_name,
    extract_tool_info,
)
from .usage import convert_usage


class OpenAIStreamingHandle(AgentStreamingHandle):
    """Wraps the SDK streaming iterator to emit normalized events."""

    def __init__(
        self,
        *,
        stream,
        agent_key: str,
        metadata: Mapping[str, Any],
        lifecycle_bus: LifecycleEventSink | None = None,
    ) -> None:
        self._stream = stream
        self._agent_key = agent_key
        self.metadata = metadata
        self._lifecycle_bus = lifecycle_bus

    async def events(self) -> AsyncIterator[AgentStreamEvent]:
        if self._lifecycle_bus:
            async for ev in self._lifecycle_bus.drain():
                yield ev

        async for event in self._stream.stream_events():
            async for mapped in self._map_event(event):
                yield mapped
            if self._lifecycle_bus:
                async for ev in self._lifecycle_bus.drain():
                    yield ev

        # Emit a final structured-output event once the stream is complete.
        final_output = getattr(self._stream, "final_output", None)
        response_id = getattr(self._stream, "last_response_id", None)
        structured_output = None
        response_text = None
        if final_output is not None:
            if isinstance(final_output, str):
                response_text = final_output
            else:
                structured_output = final_output
                try:
                    response_text = json.dumps(final_output, ensure_ascii=False)
                except Exception:  # pragma: no cover
                    response_text = str(final_output)
            yield AgentStreamEvent(
                kind="run_item_stream_event",
                response_id=response_id,
                is_terminal=True,
                payload={"structured_output": structured_output, "response_text": response_text},
                structured_output=structured_output,
                response_text=response_text,
                metadata=self.metadata,
                agent=self._agent_key,
            )

    async def _map_event(self, event) -> AsyncIterator[AgentStreamEvent]:
        if event.type == "raw_response_event":
            yield self._map_raw_response_event(event)
        elif event.type == "run_item_stream_event":
            yield self._map_run_item_event(event)
        elif event.type == "agent_updated_stream_event":
            new_agent = getattr(event, "new_agent", None)
            yield AgentStreamEvent(
                kind="agent_updated_stream_event",
                response_id=getattr(self._stream, "last_response_id", None),
                new_agent=extract_agent_name(new_agent),
                payload=AgentStreamEvent._to_mapping(new_agent),
                metadata=self.metadata,
            )

    def _map_raw_response_event(self, event) -> AgentStreamEvent:
        raw = event.data
        raw_type = getattr(raw, "type", None)
        sequence_number = getattr(raw, "sequence_number", None)
        raw_mapping = AgentStreamEvent._to_mapping(raw)
        item_id = getattr(raw, "item_id", None)

        text_delta: str | None = None
        reasoning_delta: str | None = None

        if isinstance(raw, ResponseTextDeltaEvent):
            text_delta = coerce_delta(getattr(raw, "delta", None))
        elif raw_type in {"response.reasoning_text.delta", "response.reasoning_summary_text.delta"}:
            reasoning_delta = coerce_delta(getattr(raw, "delta", None))

        annotations = None
        if raw_type == "response.output_text.annotation.added":
            annotation = AgentStreamEvent._to_mapping(getattr(raw, "annotation", None))
            if isinstance(annotation, Mapping) and annotation.get("type") in {
                "url_citation",
                "container_file_citation",
                "file_citation",
            }:
                annotations = [annotation]
        if annotations is None and isinstance(raw_mapping, Mapping):
            inline_annotations = raw_mapping.get("annotations")
            if isinstance(inline_annotations, list):
                filtered = [
                    ann
                    for ann in inline_annotations
                    if isinstance(ann, Mapping)
                    and ann.get("type")
                    in {"url_citation", "container_file_citation", "file_citation"}
                ]
                if filtered:
                    annotations = filtered

        container_id = None
        if isinstance(raw_mapping, Mapping):
            item_map = raw_mapping.get("item") if "item" in raw_mapping else raw_mapping
            if isinstance(item_map, Mapping):
                container_id = item_map.get("container_id") or item_map.get("container")
        container_mode = self.metadata.get("code_interpreter_mode") if self.metadata else None

        tool_call = self._maybe_build_tool_call_from_raw(
            raw_type=raw_type,
            raw_mapping=raw_mapping,
            raw=raw,
            item_id=item_id,
            container_id=container_id,
            container_mode=container_mode,
            annotations=annotations,
        )

        return AgentStreamEvent(
            kind="raw_response_event",
            response_id=getattr(self._stream, "last_response_id", None),
            sequence_number=sequence_number,
            raw_type=raw_type,
            text_delta=text_delta,
            reasoning_delta=reasoning_delta,
            is_terminal=False,
            payload=raw_mapping,
            metadata=self.metadata,
            raw_event=raw_mapping,
            tool_call=tool_call,
            annotations=annotations,
        )

    def _map_run_item_event(self, event) -> AgentStreamEvent:
        item = getattr(event, "item", None)
        agent_name = extract_agent_name(item)
        tool_call_id, tool_name = extract_tool_info(item)
        item_payload = AgentStreamEvent._to_mapping(item)
        annotations = None
        raw_ann = getattr(event, "annotations", None) or getattr(item, "annotations", None)
        if isinstance(raw_ann, list):
            filtered = [
                ann
                for ann in raw_ann
                if isinstance(ann, Mapping)
                and ann.get("type")
                in {"url_citation", "container_file_citation", "file_citation"}
            ]
            if filtered:
                annotations = filtered
        container_mode = self.metadata.get("code_interpreter_mode") if self.metadata else None

        tool_call = self._maybe_build_tool_call_from_item(
            item=item,
            annotations=annotations,
            container_mode=container_mode,
        )

        return AgentStreamEvent(
            kind="run_item_stream_event",
            response_id=getattr(self._stream, "last_response_id", None),
            run_item_name=getattr(event, "name", None),
            run_item_type=getattr(item, "type", None),
            agent=agent_name,
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            is_terminal=False,
            payload=item_payload,
            metadata=self.metadata,
            raw_event=item_payload,
            tool_call=tool_call,
        )

    @staticmethod
    def _maybe_build_tool_call_from_raw(
        *,
        raw_type: str | None,
        raw_mapping: Mapping[str, Any] | None,
        raw: Any,
        item_id: Any,
        container_id: str | None,
        container_mode: str | None,
        annotations: list[Mapping[str, Any]] | None,
    ):
        tool_call = None
        if isinstance(raw_type, str) and raw_type.startswith("response.web_search_call."):
            status_fragment = raw_type.rsplit(".", 1)[-1]
            status = "completed" if status_fragment == "completed" else "in_progress"
            tool_call = build_web_search_tool_call(
                item_id=item_id,
                status=status,
                action=None,
            )
        elif isinstance(raw_type, str) and raw_type.startswith("response.image_generation_call."):
            status_fragment = raw_type.rsplit(".", 1)[-1]
            status_map = {
                "in_progress": "in_progress",
                "generating": "generating",
                "partial_image": "partial_image",
                "completed": "completed",
            }
            status = status_map.get(status_fragment, "in_progress")

            raw_map = raw_mapping if isinstance(raw_mapping, Mapping) else None

            def _get(key: str, *, source: Mapping[str, Any] | None = raw_map):
                if source and key in source:
                    return source.get(key)
                item_obj = source.get("item") if source else None
                if isinstance(item_obj, Mapping):
                    return item_obj.get(key)
                return None

            tool_call = build_image_generation_tool_call(
                item_id=item_id,
                status=status,
                result=_get("result") or _get("b64_json"),
                revised_prompt=_get("revised_prompt"),
                image_format=_get("format") or _get("output_format"),
                size=_get("size"),
                quality=_get("quality"),
                background=_get("background"),
                output_index=_get("output_index"),
                partial_image_index=_get("partial_image_index"),
                partial_image_b64=_get("partial_image_b64") or _get("b64_json"),
            )
        elif isinstance(raw_type, str) and raw_type.startswith("response.code_interpreter_call."):
            status_fragment = raw_type.rsplit(".", 1)[-1]
            status = (
                "completed"
                if status_fragment == "completed"
                else "interpreting"
                if status_fragment == "interpreting"
                else "in_progress"
            )
            tool_call = build_code_interpreter_tool_call(
                item_id=item_id,
                status=status,
                code=None,
                outputs=None,
                container_id=container_id,
                container_mode=container_mode,
                annotations=annotations,
            )
        elif raw_type == "response.code_interpreter_call_code.delta":
            code_delta = getattr(raw, "delta", None)
            tool_call = build_code_interpreter_tool_call(
                item_id=item_id,
                status="in_progress",
                code=coerce_delta(code_delta),
                outputs=None,
                container_id=container_id,
                container_mode=container_mode,
                annotations=annotations,
            )
        elif isinstance(raw_type, str) and raw_type.startswith("response.file_search_call."):
            status_fragment = raw_type.rsplit(".", 1)[-1]
            status = "completed" if status_fragment == "completed" else "searching"
            tool_call = build_file_search_tool_call(
                item_id=item_id,
                status=status,
                queries=None,
                results=None,
            )
        elif (
            raw_type == "response.output_item.done"
            and isinstance(raw_mapping, Mapping)
            and raw_mapping.get("item", {}).get("type") == "file_search_call"
        ):
            item = raw_mapping.get("item", {}) or {}
            results = item.get("results")
            queries = item.get("queries")
            tool_call = build_file_search_tool_call(
                item_id=item.get("id"),
                status=item.get("status") or "completed",
                queries=queries,
                results=results,
            )
        elif (
            raw_type == "response.output_item.done"
            and isinstance(raw_mapping, Mapping)
            and raw_mapping.get("item", {}).get("type") == "image_generation_call"
        ):
            item = raw_mapping.get("item", {}) or {}
            tool_call = build_image_generation_tool_call(
                item_id=item.get("id"),
                status=item.get("status") or "completed",
                result=item.get("result") or item.get("b64_json"),
                revised_prompt=item.get("revised_prompt"),
                image_format=item.get("format") or item.get("output_format"),
                size=item.get("size"),
                quality=item.get("quality"),
                background=item.get("background"),
                output_index=item.get("output_index"),
                partial_image_index=item.get("partial_image_index"),
                partial_image_b64=item.get("partial_image_b64") or item.get("b64_json"),
            )
        elif (
            raw_type in {"response.output_item.added", "response.output_item.done"}
            and isinstance(raw_mapping, Mapping)
            and raw_mapping.get("item", {}).get("type") == "code_interpreter_call"
        ):
            item = raw_mapping.get("item", {}) or {}
            tool_call = build_code_interpreter_tool_call(
                item_id=item.get("id"),
                status=item.get("status"),
                code=item.get("code"),
                outputs=item.get("outputs"),
                container_id=item.get("container_id") or item.get("container"),
                container_mode=container_mode,
                annotations=annotations,
            )
        return tool_call

    @staticmethod
    def _maybe_build_tool_call_from_item(
        *,
        item,
        annotations: list[Mapping[str, Any]] | None,
        container_mode: str | None,
    ):
        tool_call = None
        if getattr(item, "type", None) == "web_search_call":
            tool_call = build_web_search_tool_call(
                item_id=getattr(item, "id", None),
                status=getattr(item, "status", None),
                action=AgentStreamEvent._to_mapping(getattr(item, "action", None)),
            )
        elif getattr(item, "type", None) == "code_interpreter_call":
            container_map = AgentStreamEvent._to_mapping(getattr(item, "container", None))
            container_id_for_item = getattr(item, "container_id", None)
            if container_id_for_item is None and isinstance(container_map, Mapping):
                container_id_for_item = container_map.get("id")
            tool_call = build_code_interpreter_tool_call(
                item_id=getattr(item, "id", None),
                status=getattr(item, "status", None),
                code=getattr(item, "code", None),
                outputs=AgentStreamEvent._to_mapping(getattr(item, "outputs", None)),
                container_id=container_id_for_item,
                container_mode=container_mode,
                annotations=annotations,
            )
        elif getattr(item, "type", None) == "file_search_call":
            tool_call = build_file_search_tool_call(
                item_id=getattr(item, "id", None),
                status=getattr(item, "status", None),
                queries=getattr(item, "queries", None),
                results=AgentStreamEvent._to_mapping(getattr(item, "results", None)),
            )
        elif getattr(item, "type", None) == "image_generation_call":
            tool_call = build_image_generation_tool_call(
                item_id=getattr(item, "id", None),
                status=getattr(item, "status", None),
                result=getattr(item, "result", None) or getattr(item, "b64_json", None),
                revised_prompt=getattr(item, "revised_prompt", None),
                image_format=getattr(item, "format", None) or getattr(item, "output_format", None),
                size=getattr(item, "size", None),
                quality=getattr(item, "quality", None),
                background=getattr(item, "background", None),
                output_index=getattr(item, "output_index", None),
                partial_image_index=getattr(item, "partial_image_index", None),
                partial_image_b64=getattr(item, "partial_image_b64", None)
                or getattr(item, "b64_json", None),
            )
        return tool_call

    @property
    def last_response_id(self) -> str | None:  # pragma: no cover - passthrough
        return getattr(self._stream, "last_response_id", None)

    @property
    def usage(self) -> AgentRunUsage | None:  # pragma: no cover - passthrough
        context = getattr(self._stream, "context_wrapper", None)
        if not context:
            return None
        return convert_usage(getattr(context, "usage", None))


__all__ = ["OpenAIStreamingHandle"]
