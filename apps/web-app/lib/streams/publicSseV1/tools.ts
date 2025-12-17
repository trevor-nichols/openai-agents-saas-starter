import type { PublicSseEvent, StreamingChatEvent, StreamingWorkflowEvent } from '@/lib/api/client/types.gen';
import type { GeneratedImageFrame } from '@/lib/streams/imageFrames';
import {
  applyChunkDelta as applyChunkDeltaShared,
  asDataUrlOrRawText,
  mimeFromImageFormat,
  takeChunk,
  type ChunkAccumulator,
  type ChunkKey,
} from '@/lib/streams/publicSseV1/chunks';
import {
  uiToolStatusFromProviderStatus,
  upgradeToolStatus,
  type UiToolStatus,
} from '@/lib/streams/publicSseV1/toolStatus';
import { parseTimestampMs } from '@/lib/utils/time';

export type PublicSseToolState = {
  id: string;
  name?: string | null;
  outputIndex?: number | null;
  status: 'input-streaming' | 'input-available' | 'output-available' | 'output-error';
  input?: unknown;
  output?: unknown;
  errorText?: string | null;
};

type ToolStateTrackerParams = {
  onToolStates?: (toolStates: PublicSseToolState[]) => void;
};

function toolPlaceholderNameFromItemType(itemType: string | undefined | null): string | null {
  if (!itemType) return null;
  if (itemType === 'web_search_call') return 'web_search';
  if (itemType === 'file_search_call') return 'file_search';
  if (itemType === 'code_interpreter_call') return 'code_interpreter';
  if (itemType === 'image_generation_call') return 'image_generation';
  if (itemType === 'mcp_call') return 'mcp';
  if (itemType === 'function_call' || itemType === 'custom_tool_call') return 'function';
  return null;
}

function noteFirstSeen(firstSeenMs: Map<string, number>, toolId: string, timestamp: string | undefined | null) {
  const ts = parseTimestampMs(timestamp ?? null);
  if (ts === null) return;
  const existing = firstSeenMs.get(toolId);
  if (existing === undefined || ts < existing) firstSeenMs.set(toolId, ts);
}

type CanonicalIds = {
  canonicalIdByAnyId: Map<string, string>;
};

function canonicalizeId(state: CanonicalIds, id: string): string {
  return state.canonicalIdByAnyId.get(id) ?? id;
}

function registerIdAlias(state: CanonicalIds, anyId: string, canonicalId: string): void {
  const resolvedCanonical = canonicalizeId(state, canonicalId);
  state.canonicalIdByAnyId.set(anyId, resolvedCanonical);
  state.canonicalIdByAnyId.set(resolvedCanonical, resolvedCanonical);
}

export type PublicSseToolAccumulator = {
  apply: (event: PublicSseEvent) => void;
  ensurePlaceholderForOutputItem: (params: { itemId: string; itemType: string; outputIndex: number }) => void;
  getToolsSorted: () => PublicSseToolState[];
  getToolById: (toolId: string) => PublicSseToolState | null;
  getFirstSeenMs: (toolId: string) => number | null;
};

export function createPublicSseToolAccumulator(params: ToolStateTrackerParams = {}): PublicSseToolAccumulator {
  const toolMap = new Map<string, PublicSseToolState>();
  const toolArgumentsTextById = new Map<string, string>();
  const toolArgumentsJsonById = new Map<string, unknown>();
  const toolCodeById = new Map<string, string>();
  const imageMetaByToolId = new Map<string, { format?: string | null; revisedPrompt?: string | null }>();
  const imageFramesByToolId = new Map<string, Map<number, GeneratedImageFrame>>();
  const chunksByTarget = new Map<ChunkKey, ChunkAccumulator>();
  const firstSeenMs = new Map<string, number>();
  const canonicalIds: CanonicalIds = { canonicalIdByAnyId: new Map() };

  const emitToolStates = () => {
    params.onToolStates?.(getToolsSorted());
  };

  const mergeToolState = (from: PublicSseToolState, to: PublicSseToolState): PublicSseToolState => {
    const status = upgradeToolStatus(
      to.status as UiToolStatus,
      from.status as UiToolStatus,
    ) as PublicSseToolState['status'];
    return {
      ...to,
      name: to.name ?? from.name,
      outputIndex: to.outputIndex ?? from.outputIndex,
      input: to.input ?? from.input,
      output: to.output ?? from.output,
      errorText: to.errorText ?? from.errorText,
      status,
    };
  };

  const bindAlias = (anyId: string, canonicalId: string) => {
    const fromId = canonicalizeId(canonicalIds, anyId);
    const toId = canonicalizeId(canonicalIds, canonicalId);
    if (fromId === toId) {
      registerIdAlias(canonicalIds, anyId, canonicalId);
      return;
    }

    registerIdAlias(canonicalIds, anyId, canonicalId);

    const existingFrom = toolMap.get(fromId);
    const existingTo = toolMap.get(toId);
    if (existingFrom) {
      if (existingTo) {
        toolMap.set(toId, mergeToolState(existingFrom, existingTo));
      } else {
        toolMap.set(toId, { ...existingFrom, id: toId });
      }
      toolMap.delete(fromId);
    }

    const argsFrom = toolArgumentsTextById.get(fromId);
    const argsTo = toolArgumentsTextById.get(toId);
    if (argsFrom !== undefined) {
      toolArgumentsTextById.set(toId, argsTo ?? argsFrom);
      toolArgumentsTextById.delete(fromId);
    }

    const argsJsonFrom = toolArgumentsJsonById.get(fromId);
    const argsJsonTo = toolArgumentsJsonById.get(toId);
    if (argsJsonFrom !== undefined) {
      toolArgumentsJsonById.set(toId, argsJsonTo ?? argsJsonFrom);
      toolArgumentsJsonById.delete(fromId);
    }

    const codeFrom = toolCodeById.get(fromId);
    const codeTo = toolCodeById.get(toId);
    if (codeFrom !== undefined) {
      toolCodeById.set(toId, codeTo ?? codeFrom);
      toolCodeById.delete(fromId);
    }

    const metaFrom = imageMetaByToolId.get(fromId);
    const metaTo = imageMetaByToolId.get(toId);
    if (metaFrom) {
      imageMetaByToolId.set(toId, metaTo ?? metaFrom);
      imageMetaByToolId.delete(fromId);
    }

    const framesFrom = imageFramesByToolId.get(fromId);
    const framesTo = imageFramesByToolId.get(toId);
    if (framesFrom) {
      imageFramesByToolId.set(toId, framesTo ?? framesFrom);
      imageFramesByToolId.delete(fromId);
    }

    const seenFrom = firstSeenMs.get(fromId);
    const seenTo = firstSeenMs.get(toId);
    if (seenFrom !== undefined) {
      if (seenTo === undefined || seenFrom < seenTo) firstSeenMs.set(toId, seenFrom);
      firstSeenMs.delete(fromId);
    }
  };

  const upsertTool = (toolIdRaw: string, patch: Partial<PublicSseToolState>) => {
    const toolId = canonicalizeId(canonicalIds, toolIdRaw);
    const existing =
      toolMap.get(toolId) ??
      ({
        id: toolId,
        status: 'input-streaming',
        errorText: null,
      } satisfies PublicSseToolState);

    const next: PublicSseToolState = {
      ...existing,
      ...patch,
      id: toolId,
      name: patch.name ?? existing.name,
      input: patch.input ?? existing.input,
      output: patch.output ?? existing.output,
      outputIndex: patch.outputIndex ?? existing.outputIndex,
      errorText: patch.errorText ?? existing.errorText,
      status: patch.status
        ? (upgradeToolStatus(existing.status as UiToolStatus, patch.status as UiToolStatus) as PublicSseToolState['status'])
        : existing.status,
    };

    toolMap.set(toolId, next);
    emitToolStates();
  };

  const updateToolImageFrames = (toolIdRaw: string) => {
    const toolId = canonicalizeId(canonicalIds, toolIdRaw);
    const framesMap = imageFramesByToolId.get(toolId);
    if (!framesMap) return;
    const frames = Array.from(framesMap.entries())
      .sort(([a], [b]) => a - b)
      .map(([, frame]) => frame);
    if (frames.length === 0) return;
    upsertTool(toolId, { output: frames, name: 'image_generation' });
  };

  const ensurePlaceholderForOutputItem: PublicSseToolAccumulator['ensurePlaceholderForOutputItem'] = (params) => {
    const placeholder = toolPlaceholderNameFromItemType(params.itemType);
    if (!placeholder) return;

    const toolId = canonicalizeId(canonicalIds, params.itemId);
    const existing = toolMap.get(toolId);
    if (!existing) {
      upsertTool(toolId, {
        name: placeholder,
        status: 'input-streaming',
        outputIndex: params.outputIndex,
      });
      return;
    }
    if (existing.outputIndex === undefined || existing.outputIndex === null) {
      upsertTool(toolId, { outputIndex: params.outputIndex });
    }
  };

  const applyChunkDone = (event: Extract<PublicSseEvent, { kind: 'chunk.done' }>) => {
    const chunk = takeChunk(chunksByTarget, event.target);
    if (!chunk) return;

    if (
      event.target.entity_kind === 'tool_call' &&
      event.target.field === 'partial_image_b64' &&
      typeof event.target.part_index === 'number'
    ) {
      const toolId = canonicalizeId(canonicalIds, event.target.entity_id);
      noteFirstSeen(firstSeenMs, toolId, event.server_timestamp);
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

  const applyToolStatus = (event: Extract<PublicSseEvent, { kind: 'tool.status' }>) => {
    const tool = event.tool;
    const outputIndex = event.output_index;

    // Establish aliases between event.item_id and tool.tool_call_id where possible.
    if (event.item_id && tool.tool_call_id && event.item_id !== tool.tool_call_id) {
      bindAlias(event.item_id, tool.tool_call_id);
    } else if (event.item_id) {
      bindAlias(event.item_id, event.item_id);
    }
    if (tool.tool_call_id) bindAlias(tool.tool_call_id, tool.tool_call_id);

    const toolId = canonicalizeId(canonicalIds, tool.tool_call_id ?? event.item_id);
    noteFirstSeen(firstSeenMs, toolId, event.server_timestamp);

    const status = uiToolStatusFromProviderStatus(tool.status);

    if (tool.tool_type === 'web_search') {
      upsertTool(toolId, {
        name: 'web_search',
        status,
        outputIndex,
        input: tool.query ?? undefined,
        output: tool.sources ?? undefined,
      });
      return;
    }

    if (tool.tool_type === 'file_search') {
      upsertTool(toolId, {
        name: 'file_search',
        status,
        outputIndex,
        input: tool.queries ?? undefined,
        output: tool.results ?? undefined,
      });
      return;
    }

    if (tool.tool_type === 'code_interpreter') {
      const code = toolCodeById.get(toolId);
      upsertTool(toolId, {
        name: 'code_interpreter',
        status,
        outputIndex,
        input: code ?? undefined,
        output: tool.container_id || tool.container_mode
          ? { container_id: tool.container_id ?? null, container_mode: tool.container_mode ?? null }
          : undefined,
      });
      return;
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
      return;
    }

    if (tool.tool_type === 'function') {
      const argsText = tool.arguments_text ?? toolArgumentsTextById.get(toolId);
      const argsJson = tool.arguments_json ?? toolArgumentsJsonById.get(toolId);
      const includesArguments =
        argsText !== null && argsText !== undefined && String(argsText).length > 0
          ? true
          : argsJson !== null && argsJson !== undefined;

      upsertTool(toolId, {
        name: tool.name,
        status,
        outputIndex,
        input: includesArguments
          ? {
              tool_type: 'function',
              tool_name: tool.name,
              arguments_text: argsText ?? undefined,
              arguments_json: argsJson ?? undefined,
            }
          : undefined,
        output: tool.output ?? undefined,
        errorText: tool.status === 'failed' ? 'Tool failed' : undefined,
      });
      return;
    }

    // MCP
    const argsText = tool.arguments_text ?? toolArgumentsTextById.get(toolId);
    const argsJson = tool.arguments_json ?? toolArgumentsJsonById.get(toolId);
    const includesArguments =
      argsText !== null && argsText !== undefined && String(argsText).length > 0
        ? true
        : argsJson !== null && argsJson !== undefined;

    upsertTool(toolId, {
      name: tool.tool_name,
      status,
      outputIndex,
      input: includesArguments
        ? {
            tool_type: 'mcp',
            tool_name: tool.tool_name,
            server_label: tool.server_label ?? null,
            arguments_text: argsText ?? undefined,
            arguments_json: argsJson ?? undefined,
          }
        : undefined,
      output: tool.output ?? undefined,
      errorText: tool.status === 'failed' ? 'Tool failed' : undefined,
    });
  };

  const applyToolArgumentsDelta = (event: Extract<PublicSseEvent, { kind: 'tool.arguments.delta' }>) => {
    bindAlias(event.item_id, event.tool_call_id);
    bindAlias(event.tool_call_id, event.tool_call_id);
    const toolId = canonicalizeId(canonicalIds, event.tool_call_id);

    noteFirstSeen(firstSeenMs, toolId, event.server_timestamp);

    const existing = toolArgumentsTextById.get(toolId) ?? '';
    const next = `${existing}${event.delta}`;
    toolArgumentsTextById.set(toolId, next);
    upsertTool(toolId, {
      name: event.tool_name,
      status: 'input-streaming',
      outputIndex: event.output_index,
      input: { tool_type: event.tool_type, tool_name: event.tool_name, arguments_text: next },
    });
  };

  const applyToolArgumentsDone = (event: Extract<PublicSseEvent, { kind: 'tool.arguments.done' }>) => {
    bindAlias(event.item_id, event.tool_call_id);
    bindAlias(event.tool_call_id, event.tool_call_id);
    const toolId = canonicalizeId(canonicalIds, event.tool_call_id);

    noteFirstSeen(firstSeenMs, toolId, event.server_timestamp);

    toolArgumentsTextById.set(toolId, event.arguments_text);
    if (event.arguments_json !== null && event.arguments_json !== undefined) {
      toolArgumentsJsonById.set(toolId, event.arguments_json);
    }
    upsertTool(toolId, {
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
  };

  const applyToolCodeDelta = (event: Extract<PublicSseEvent, { kind: 'tool.code.delta' }>) => {
    bindAlias(event.item_id, event.tool_call_id);
    bindAlias(event.tool_call_id, event.tool_call_id);
    const toolId = canonicalizeId(canonicalIds, event.tool_call_id);

    noteFirstSeen(firstSeenMs, toolId, event.server_timestamp);

    const existing = toolCodeById.get(toolId) ?? '';
    const next = `${existing}${event.delta}`;
    toolCodeById.set(toolId, next);
    upsertTool(toolId, {
      name: 'code_interpreter',
      status: 'input-streaming',
      outputIndex: event.output_index,
      input: next,
    });
  };

  const applyToolCodeDone = (event: Extract<PublicSseEvent, { kind: 'tool.code.done' }>) => {
    bindAlias(event.item_id, event.tool_call_id);
    bindAlias(event.tool_call_id, event.tool_call_id);
    const toolId = canonicalizeId(canonicalIds, event.tool_call_id);

    noteFirstSeen(firstSeenMs, toolId, event.server_timestamp);

    toolCodeById.set(toolId, event.code);
    upsertTool(toolId, {
      name: 'code_interpreter',
      status: 'input-available',
      outputIndex: event.output_index,
      input: event.code,
    });
  };

  const applyToolOutput = (event: Extract<PublicSseEvent, { kind: 'tool.output' }>) => {
    bindAlias(event.item_id, event.tool_call_id);
    bindAlias(event.tool_call_id, event.tool_call_id);
    const toolId = canonicalizeId(canonicalIds, event.tool_call_id);

    noteFirstSeen(firstSeenMs, toolId, event.server_timestamp);

    upsertTool(toolId, {
      status: 'output-available',
      outputIndex: event.output_index,
      output: event.output,
    });
  };

  const applyToolApproval = (event: Extract<PublicSseEvent, { kind: 'tool.approval' }>) => {
    bindAlias(event.item_id, event.tool_call_id);
    bindAlias(event.tool_call_id, event.tool_call_id);
    const toolId = canonicalizeId(canonicalIds, event.tool_call_id);

    noteFirstSeen(firstSeenMs, toolId, event.server_timestamp);

    upsertTool(toolId, {
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
  };

  const applyChunkDelta = (event: Extract<PublicSseEvent, { kind: 'chunk.delta' }>) => {
    applyChunkDeltaShared(chunksByTarget, {
      target: event.target,
      encoding: event.encoding,
      chunkIndex: event.chunk_index,
      data: event.data,
    });
  };

  const apply = (event: PublicSseEvent) => {
    if (event.kind === 'output_item.added') {
      ensurePlaceholderForOutputItem({ itemId: event.item_id, itemType: event.item_type, outputIndex: event.output_index });
      return;
    }

    switch (event.kind) {
      case 'tool.status':
        applyToolStatus(event);
        return;
      case 'tool.arguments.delta':
        applyToolArgumentsDelta(event);
        return;
      case 'tool.arguments.done':
        applyToolArgumentsDone(event);
        return;
      case 'tool.code.delta':
        applyToolCodeDelta(event);
        return;
      case 'tool.code.done':
        applyToolCodeDone(event);
        return;
      case 'tool.output':
        applyToolOutput(event);
        return;
      case 'tool.approval':
        applyToolApproval(event);
        return;
      case 'chunk.delta':
        applyChunkDelta(event);
        return;
      case 'chunk.done':
        applyChunkDone(event);
        return;
      default:
        return;
    }
  };

  const getToolsSorted = (): PublicSseToolState[] =>
    Array.from(toolMap.values()).sort(
      (a, b) => (a.outputIndex ?? Number.POSITIVE_INFINITY) - (b.outputIndex ?? Number.POSITIVE_INFINITY),
    );

  const getToolById = (toolIdRaw: string): PublicSseToolState | null => {
    const toolId = canonicalizeId(canonicalIds, toolIdRaw);
    return toolMap.get(toolId) ?? null;
  };

  const getFirstSeenMs = (toolIdRaw: string): number | null => {
    const toolId = canonicalizeId(canonicalIds, toolIdRaw);
    return firstSeenMs.get(toolId) ?? null;
  };

  return { apply, ensurePlaceholderForOutputItem, getToolsSorted, getToolById, getFirstSeenMs };
}

export function asPublicSseEvent(
  event: StreamingChatEvent | StreamingWorkflowEvent,
): PublicSseEvent {
  // The public contract is identical; `StreamingChatEvent` and `StreamingWorkflowEvent` are stream-scoped aliases.
  return event as unknown as PublicSseEvent;
}
