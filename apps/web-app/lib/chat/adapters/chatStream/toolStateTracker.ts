import type { StreamingChatEvent } from '@/lib/api/client/types.gen';
import type { GeneratedImageFrame } from '@/lib/streams/imageFrames';
import {
  applyChunkDelta as applyChunkDeltaShared,
  asDataUrlOrRawText,
  mimeFromImageFormat,
  takeChunk,
  type ChunkKey,
  type ChunkAccumulator,
} from '@/lib/streams/publicSseV1/chunks';
import {
  uiToolStatusFromProviderStatus,
  upgradeToolStatus,
  type UiToolStatus,
} from '@/lib/streams/publicSseV1/toolStatus';

import type { ToolState } from '../../types';

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

type ToolStateTrackerParams = {
  onToolStates?: (toolStates: ToolState[]) => void;
};

export type ToolStateTracker = {
  ensurePlaceholderForOutputItem: (params: { itemId: string; itemType: string; outputIndex: number }) => void;
  applyToolStatus: (event: Extract<StreamingChatEvent, { kind?: 'tool.status' }>) => void;
  applyToolArgumentsDelta: (event: Extract<StreamingChatEvent, { kind?: 'tool.arguments.delta' }>) => void;
  applyToolArgumentsDone: (event: Extract<StreamingChatEvent, { kind?: 'tool.arguments.done' }>) => void;
  applyToolCodeDelta: (event: Extract<StreamingChatEvent, { kind?: 'tool.code.delta' }>) => void;
  applyToolCodeDone: (event: Extract<StreamingChatEvent, { kind?: 'tool.code.done' }>) => void;
  applyToolOutput: (event: Extract<StreamingChatEvent, { kind?: 'tool.output' }>) => void;
  applyChunkDelta: (event: Extract<StreamingChatEvent, { kind?: 'chunk.delta' }>) => void;
  applyChunkDone: (event: Extract<StreamingChatEvent, { kind?: 'chunk.done' }>) => void;
  getToolsSorted: () => ToolState[];
};

export function createToolStateTracker(params: ToolStateTrackerParams): ToolStateTracker {
  const toolMap = new Map<string, ToolState>();
  const toolArgumentsTextById = new Map<string, string>();
  const toolCodeById = new Map<string, string>();

  const imageMetaByToolId = new Map<string, { format?: string | null; revisedPrompt?: string | null }>();
  const imageFramesByToolId = new Map<string, Map<number, GeneratedImageFrame>>();

  const chunksByTarget = new Map<ChunkKey, ChunkAccumulator>();

  const getToolsSorted = (): ToolState[] =>
    Array.from(toolMap.values()).sort(
      (a, b) =>
        (a.outputIndex ?? Number.POSITIVE_INFINITY) - (b.outputIndex ?? Number.POSITIVE_INFINITY),
    );

  const emitToolStates = () => {
    params.onToolStates?.(getToolsSorted());
  };

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
    emitToolStates();
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

  const ensurePlaceholderForOutputItem: ToolStateTracker['ensurePlaceholderForOutputItem'] = (params) => {
    const placeholder = toolPlaceholderNameFromItemType(params.itemType);
    if (!placeholder) return;

    const existing = toolMap.get(params.itemId);
    if (!existing) {
      upsertTool(params.itemId, {
        name: placeholder,
        status: 'input-streaming',
        outputIndex: params.outputIndex,
      });
      return;
    }
    if (existing.outputIndex === undefined || existing.outputIndex === null) {
      upsertTool(params.itemId, { outputIndex: params.outputIndex });
    }
  };

  const applyToolStatus: ToolStateTracker['applyToolStatus'] = (event) => {
    const tool = event.tool;
    const toolId = tool.tool_call_id;
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
      const hasArgsJson = tool.arguments_json !== null && tool.arguments_json !== undefined;
      const hasArgsText = tool.arguments_text !== null && tool.arguments_text !== undefined;
      const includesArguments = hasArgsJson || hasArgsText;

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
      return;
    }

    if (tool.tool_type === 'mcp') {
      const hasArgsJson = tool.arguments_json !== null && tool.arguments_json !== undefined;
      const hasArgsText = tool.arguments_text !== null && tool.arguments_text !== undefined;
      const includesArguments = hasArgsJson || hasArgsText;

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
  };

  const applyToolArgumentsDelta: ToolStateTracker['applyToolArgumentsDelta'] = (event) => {
    const existing = toolArgumentsTextById.get(event.tool_call_id) ?? '';
    const next = `${existing}${event.delta}`;
    toolArgumentsTextById.set(event.tool_call_id, next);
    upsertTool(event.tool_call_id, {
      name: event.tool_name,
      status: 'input-streaming',
      outputIndex: event.output_index,
      input: { tool_type: event.tool_type, tool_name: event.tool_name, arguments_text: next },
    });
  };

  const applyToolArgumentsDone: ToolStateTracker['applyToolArgumentsDone'] = (event) => {
    toolArgumentsTextById.set(event.tool_call_id, event.arguments_text);
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
  };

  const applyToolCodeDelta: ToolStateTracker['applyToolCodeDelta'] = (event) => {
    const existing = toolCodeById.get(event.tool_call_id) ?? '';
    const next = `${existing}${event.delta}`;
    toolCodeById.set(event.tool_call_id, next);
    upsertTool(event.tool_call_id, {
      name: 'code_interpreter',
      status: 'input-streaming',
      outputIndex: event.output_index,
      input: next,
    });
  };

  const applyToolCodeDone: ToolStateTracker['applyToolCodeDone'] = (event) => {
    toolCodeById.set(event.tool_call_id, event.code);
    upsertTool(event.tool_call_id, {
      name: 'code_interpreter',
      status: 'input-available',
      outputIndex: event.output_index,
      input: event.code,
    });
  };

  const applyToolOutput: ToolStateTracker['applyToolOutput'] = (event) => {
    upsertTool(event.tool_call_id, {
      status: 'output-available',
      outputIndex: event.output_index,
      output: event.output,
    });
  };

  const applyChunkDelta: ToolStateTracker['applyChunkDelta'] = (event) => {
    applyChunkDeltaShared(chunksByTarget, {
      target: event.target,
      encoding: event.encoding,
      chunkIndex: event.chunk_index,
      data: event.data,
    });
  };

  const applyChunkDone: ToolStateTracker['applyChunkDone'] = (event) => {
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

  return {
    ensurePlaceholderForOutputItem,
    applyToolStatus,
    applyToolArgumentsDelta,
    applyToolArgumentsDone,
    applyToolCodeDelta,
    applyToolCodeDone,
    applyToolOutput,
    applyChunkDelta,
    applyChunkDone,
    getToolsSorted,
  };
}

