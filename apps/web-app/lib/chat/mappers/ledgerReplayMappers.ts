import type { PublicSseEvent } from '@/lib/api/client/types.gen';
import type { GeneratedImageFrame } from '@/lib/streams/imageFrames';
import {
  applyChunkDelta as applyChunkDeltaShared,
  asDataUrlOrRawText,
  mimeFromImageFormat,
  takeChunk,
  type ChunkAccumulator,
  type ChunkKey,
} from '@/lib/streams/publicSseV1/chunks';
import { upgradeToolStatus, uiToolStatusFromProviderStatus, type UiToolStatus } from '@/lib/streams/publicSseV1/toolStatus';
import { parseTimestampMs } from '@/lib/utils/time';

import type { ChatMessage, ToolEventAnchors, ToolState } from '../types';

type ToolTimeline = {
  tools: ToolState[];
  anchors: ToolEventAnchors;
};

type MessageTimeIndex = {
  id: string;
  timestampMs: number;
};

const buildMessageTimeIndex = (messages: ChatMessage[]): MessageTimeIndex[] =>
  messages
    .filter((message) => message.kind !== 'memory_checkpoint')
    .map((message) => {
      const timestampMs = parseTimestampMs(message.timestamp ?? null);
      if (timestampMs === null) return null;
      return { id: message.id, timestampMs };
    })
    .filter((entry): entry is MessageTimeIndex => Boolean(entry))
    .sort((a, b) => a.timestampMs - b.timestampMs);

const findAnchorMessageId = (messageIndex: MessageTimeIndex[], toolTimestampMs: number): string | null => {
  if (messageIndex.length === 0) return null;
  const first = messageIndex[0];
  if (!first) return null;
  if (toolTimestampMs < first.timestampMs) return null;

  let low = 0;
  let high = messageIndex.length - 1;
  while (low <= high) {
    const mid = Math.floor((low + high) / 2);
    const entry = messageIndex[mid];
    if (!entry) break;
    if (entry.timestampMs === toolTimestampMs) {
      return entry.id;
    }
    if (entry.timestampMs < toolTimestampMs) {
      low = mid + 1;
    } else {
      high = mid - 1;
    }
  }

  const resolved = messageIndex[Math.max(0, high)];
  return resolved?.id ?? null;
};

function noteFirstSeen(firstSeenMs: Map<string, number>, toolId: string, timestamp: string | undefined | null) {
  const ts = parseTimestampMs(timestamp ?? null);
  if (ts === null) return;
  const existing = firstSeenMs.get(toolId);
  if (existing === undefined || ts < existing) firstSeenMs.set(toolId, ts);
}

export function extractMemoryCheckpointMarkers(events: PublicSseEvent[]): ChatMessage[] {
  const markers: ChatMessage[] = [];
  for (const event of events) {
    if (event.kind !== 'memory.checkpoint') continue;
    const streamId = event.stream_id;
    const eventId = event.event_id;
    markers.push({
      id: `memory-checkpoint-${streamId}-${eventId}`,
      role: 'assistant',
      kind: 'memory_checkpoint',
      content: '',
      timestamp: event.server_timestamp ?? undefined,
      checkpoint: event.checkpoint,
    });
  }
  return markers;
}

export function mapLedgerEventsToToolTimeline(events: PublicSseEvent[], messages: ChatMessage[]): ToolTimeline {
  if (events.length === 0 || messages.length === 0) {
    return { tools: [], anchors: {} };
  }

  const toolMap = new Map<string, ToolState>();
  const firstSeenMs = new Map<string, number>();

  const toolArgumentsTextById = new Map<string, string>();
  const toolCodeById = new Map<string, string>();

  const imageMetaByToolId = new Map<string, { format?: string | null; revisedPrompt?: string | null }>();
  const imageFramesByToolId = new Map<string, Map<number, GeneratedImageFrame>>();

  const chunksByTarget = new Map<ChunkKey, ChunkAccumulator>();

  const upsertTool = (toolId: string, patch: Partial<ToolState>) => {
    const existing =
      toolMap.get(toolId) ??
      ({
        id: toolId,
        status: 'input-streaming',
        errorText: null,
      } satisfies ToolState);

    const next: ToolState = {
      ...existing,
      ...patch,
      id: toolId,
      name: patch.name ?? existing.name,
      input: patch.input ?? existing.input,
      output: patch.output ?? existing.output,
      outputIndex: patch.outputIndex ?? existing.outputIndex,
      errorText: patch.errorText ?? existing.errorText,
      status: patch.status
        ? upgradeToolStatus(existing.status as UiToolStatus, patch.status as UiToolStatus)
        : existing.status,
    };

    toolMap.set(toolId, next);
  };

  const updateToolImageFrames = (toolId: string) => {
    const framesMap = imageFramesByToolId.get(toolId);
    if (!framesMap) return;
    const frames = Array.from(framesMap.entries())
      .sort(([a], [b]) => a - b)
      .map(([, frame]) => frame);
    if (frames.length === 0) return;
    upsertTool(toolId, { output: frames, name: 'image_generation' });
  };

  const applyChunkDone = (event: Extract<PublicSseEvent, { kind: 'chunk.done' }>) => {
    const chunk = takeChunk(chunksByTarget, event.target);
    if (!chunk) return;

    if (
      event.target.entity_kind === 'tool_call' &&
      event.target.field === 'partial_image_b64' &&
      typeof event.target.part_index === 'number'
    ) {
      const toolId = event.target.entity_id;
      const partIndex = event.target.part_index;
      const meta = imageMetaByToolId.get(toolId);
      const mime = mimeFromImageFormat(meta?.format ?? null);
      const src = asDataUrlOrRawText({ encoding: chunk.encoding, data: chunk.data, mimeType: mime });

      const frames = imageFramesByToolId.get(toolId) ?? new Map<number, GeneratedImageFrame>();
      frames.set(partIndex, {
        id: `${toolId}:${partIndex}`,
        src,
        status: 'partial_image',
        outputIndex: partIndex,
        revisedPrompt: meta?.revisedPrompt ?? undefined,
      });
      imageFramesByToolId.set(toolId, frames);
      updateToolImageFrames(toolId);
    }
  };

  for (const event of events) {
    switch (event.kind) {
      case 'tool.status': {
        const tool = event.tool;
        const toolId = tool.tool_call_id;
        noteFirstSeen(firstSeenMs, toolId, event.server_timestamp);

        const status = uiToolStatusFromProviderStatus(tool.status);
        const outputIndex = event.output_index;

        if (tool.tool_type === 'web_search') {
          upsertTool(toolId, {
            name: 'web_search',
            status,
            outputIndex,
            input: tool.query ?? undefined,
            output: tool.sources ?? undefined,
          });
          break;
        }

        if (tool.tool_type === 'file_search') {
          upsertTool(toolId, {
            name: 'file_search',
            status,
            outputIndex,
            input: tool.queries ?? undefined,
            output: tool.results ?? undefined,
          });
          break;
        }

        if (tool.tool_type === 'code_interpreter') {
          const code = toolCodeById.get(toolId);
          upsertTool(toolId, {
            name: 'code_interpreter',
            status,
            outputIndex,
            input: code ?? undefined,
          });
          break;
        }

        if (tool.tool_type === 'image_generation') {
          imageMetaByToolId.set(toolId, {
            format: tool.format ?? null,
            revisedPrompt: tool.revised_prompt ?? null,
          });
          upsertTool(toolId, {
            name: 'image_generation',
            status,
            outputIndex,
            input: tool.revised_prompt ?? undefined,
          });
          updateToolImageFrames(toolId);
          break;
        }

        if (tool.tool_type === 'function') {
          const includesArguments =
            (tool.arguments_json !== null && tool.arguments_json !== undefined) ||
            (tool.arguments_text !== null && tool.arguments_text !== undefined);
          upsertTool(toolId, {
            name: tool.name,
            status,
            outputIndex,
            input: includesArguments
              ? {
                  tool_type: 'function',
                  tool_name: tool.name,
                  arguments_text: tool.arguments_text ?? undefined,
                  arguments_json: tool.arguments_json ?? undefined,
                }
              : undefined,
            output: tool.output ?? undefined,
            errorText: tool.status === 'failed' ? 'Tool failed' : undefined,
          });
          break;
        }

        if (tool.tool_type === 'mcp') {
          const includesArguments =
            (tool.arguments_json !== null && tool.arguments_json !== undefined) ||
            (tool.arguments_text !== null && tool.arguments_text !== undefined);
          upsertTool(toolId, {
            name: tool.tool_name,
            status,
            outputIndex,
            input: includesArguments
              ? {
                  tool_type: 'mcp',
                  tool_name: tool.tool_name,
                  server_label: tool.server_label ?? null,
                  arguments_text: tool.arguments_text ?? undefined,
                  arguments_json: tool.arguments_json ?? undefined,
                }
              : undefined,
            output: tool.output ?? undefined,
            errorText: tool.status === 'failed' ? 'Tool failed' : undefined,
          });
        }
        break;
      }
      case 'tool.arguments.delta': {
        const existing = toolArgumentsTextById.get(event.tool_call_id) ?? '';
        const next = `${existing}${event.delta}`;
        toolArgumentsTextById.set(event.tool_call_id, next);
        noteFirstSeen(firstSeenMs, event.tool_call_id, event.server_timestamp);
        upsertTool(event.tool_call_id, {
          name: event.tool_name,
          status: 'input-streaming',
          outputIndex: event.output_index,
          input: { tool_type: event.tool_type, tool_name: event.tool_name, arguments_text: next },
        });
        break;
      }
      case 'tool.arguments.done': {
        toolArgumentsTextById.set(event.tool_call_id, event.arguments_text);
        noteFirstSeen(firstSeenMs, event.tool_call_id, event.server_timestamp);
        upsertTool(event.tool_call_id, {
          name: event.tool_name,
          status: 'input-available',
          outputIndex: event.output_index,
          input: {
            tool_type: event.tool_type,
            tool_name: event.tool_name,
            arguments_text: event.arguments_text,
            arguments_json: event.arguments_json ?? undefined,
          },
        });
        break;
      }
      case 'tool.code.delta': {
        const existing = toolCodeById.get(event.tool_call_id) ?? '';
        const next = `${existing}${event.delta}`;
        toolCodeById.set(event.tool_call_id, next);
        noteFirstSeen(firstSeenMs, event.tool_call_id, event.server_timestamp);
        upsertTool(event.tool_call_id, {
          name: 'code_interpreter',
          status: 'input-streaming',
          outputIndex: event.output_index,
          input: next,
        });
        break;
      }
      case 'tool.code.done': {
        toolCodeById.set(event.tool_call_id, event.code);
        noteFirstSeen(firstSeenMs, event.tool_call_id, event.server_timestamp);
        upsertTool(event.tool_call_id, {
          name: 'code_interpreter',
          status: 'input-available',
          outputIndex: event.output_index,
          input: event.code,
        });
        break;
      }
      case 'tool.output': {
        noteFirstSeen(firstSeenMs, event.tool_call_id, event.server_timestamp);
        upsertTool(event.tool_call_id, {
          status: 'output-available',
          outputIndex: event.output_index,
          output: event.output,
        });
        break;
      }
      case 'tool.approval': {
        noteFirstSeen(firstSeenMs, event.tool_call_id, event.server_timestamp);
        upsertTool(event.tool_call_id, {
          name: event.tool_name,
          status: 'output-available',
          outputIndex: event.output_index,
          output: {
            tool_type: event.tool_type,
            tool_name: event.tool_name,
            server_label: event.server_label ?? null,
            approved: event.approved,
            reason: event.reason ?? null,
            approval_request_id: event.approval_request_id ?? null,
          },
        });
        break;
      }
      case 'chunk.delta': {
        applyChunkDeltaShared(chunksByTarget, {
          target: event.target,
          encoding: event.encoding,
          chunkIndex: event.chunk_index,
          data: event.data,
        });
        break;
      }
      case 'chunk.done': {
        noteFirstSeen(firstSeenMs, event.target.entity_id, event.server_timestamp);
        applyChunkDone(event);
        break;
      }
      default:
        break;
    }
  }

  const orderedTools = Array.from(toolMap.values()).sort((a, b) => {
    const aMs = firstSeenMs.get(a.id) ?? Number.POSITIVE_INFINITY;
    const bMs = firstSeenMs.get(b.id) ?? Number.POSITIVE_INFINITY;
    if (aMs !== bMs) return aMs - bMs;
    return (a.outputIndex ?? Number.POSITIVE_INFINITY) - (b.outputIndex ?? Number.POSITIVE_INFINITY);
  });

  const messageIndex = buildMessageTimeIndex(messages);
  const anchors: ToolEventAnchors = {};
  for (const tool of orderedTools) {
    const ts = firstSeenMs.get(tool.id);
    if (ts === undefined) continue;
    const anchorId = findAnchorMessageId(messageIndex, ts);
    if (!anchorId) continue;
    anchors[anchorId] = [...(anchors[anchorId] ?? []), tool.id];
  }

  return { tools: orderedTools, anchors };
}
