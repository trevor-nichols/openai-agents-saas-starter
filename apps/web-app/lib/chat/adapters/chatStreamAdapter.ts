import type {
  MessageAttachment,
  StreamingChatEvent,
} from '@/lib/api/client/types.gen';
import type { GeneratedImageFrame } from '@/lib/streams/imageFrames';
import type {
  ConversationLifecycleStatus,
  StreamChunk,
  ToolState,
  Annotation,
} from '../types';

export type OutputItemUpdate = {
  itemId: string;
  outputIndex: number;
  itemType: string;
  role?: string | null;
  status?: string | null;
};

export type TextDeltaUpdate = {
  channel: 'message' | 'refusal';
  itemId: string;
  outputIndex: number;
  contentIndex: number;
  delta: string;
  accumulatedText: string;
  textWithCursor: string;
};

export interface StreamConsumeHandlers {
  onOutputItemAdded?: (update: OutputItemUpdate) => void;
  onOutputItemDone?: (update: OutputItemUpdate) => void;
  onTextDelta?: (update: TextDeltaUpdate) => void;
  onReasoningDelta?: (delta: string) => void;
  onToolStates?: (toolStates: ToolState[]) => void;
  onLifecycle?: (status: ConversationLifecycleStatus) => void;
  onAgentChange?: (agent: string) => void;
  onAgentNotice?: (notice: string) => void;
  onAttachments?: (attachments: MessageAttachment[] | null) => void;
  onStructuredOutput?: (data: unknown) => void;
  onError?: (errorText: string) => void;
  onConversationId?: (conversationId: string) => void;
}

export interface StreamConsumeResult {
  finalContent: string;
  conversationId: string | null;
  responseId: string | null;
  attachments: MessageAttachment[] | null;
  structuredOutput: unknown | null;
  lifecycleStatus: ConversationLifecycleStatus;
  citations: Annotation[] | null;
  terminalSeen: boolean;
  errored: boolean;
}

const statusRank: Record<ToolState['status'], number> = {
  'input-streaming': 0,
  'input-available': 1,
  'output-available': 2,
  'output-error': 3,
};

const upgradeStatus = (
  current: ToolState['status'],
  next: ToolState['status'],
): ToolState['status'] => (statusRank[next] > statusRank[current] ? next : current);

function toolUiStatusFromProviderStatus(status: string): ToolState['status'] {
  if (status === 'completed') return 'output-available';
  if (status === 'failed') return 'output-error';
  return 'input-available';
}

function mimeFromImageFormat(format: string | null | undefined): string {
  if (!format) return 'image/png';
  const normalized = format.toLowerCase();
  if (normalized.includes('png')) return 'image/png';
  if (normalized.includes('jpg') || normalized.includes('jpeg')) return 'image/jpeg';
  if (normalized.includes('webp')) return 'image/webp';
  return `image/${normalized}`;
}

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

type ChunkKey = string;

function chunkKeyFor(
  target: { entity_kind: string; entity_id: string; field: string; part_index?: number | null },
): ChunkKey {
  return `${target.entity_kind}:${target.entity_id}:${target.field}:${target.part_index ?? ''}`;
}

type ChunkAccumulator = {
  encoding: 'base64' | 'utf8' | undefined;
  parts: Map<number, string>;
};

type TextParts = Map<number, string>;

function assembledText(parts: TextParts | undefined): string {
  if (!parts || parts.size === 0) return '';
  return Array.from(parts.entries())
    .sort(([a], [b]) => a - b)
    .map(([, value]) => value)
    .join('');
}

function appendDelta(
  store: Map<string, TextParts>,
  update: { itemId: string; contentIndex: number; delta: string },
): string {
  const { itemId, contentIndex, delta } = update;
  const parts = store.get(itemId) ?? new Map<number, string>();
  const existing = parts.get(contentIndex) ?? '';
  parts.set(contentIndex, `${existing}${delta}`);
  store.set(itemId, parts);
  return assembledText(parts);
}

function replaceText(
  store: Map<string, TextParts>,
  update: { itemId: string; contentIndex: number; text: string },
): string {
  const { itemId, contentIndex, text } = update;
  const parts = store.get(itemId) ?? new Map<number, string>();
  parts.set(contentIndex, text);
  store.set(itemId, parts);
  return assembledText(parts);
}

export async function consumeChatStream(
  stream: AsyncIterable<StreamChunk>,
  handlers: StreamConsumeHandlers,
): Promise<StreamConsumeResult> {
  const messageTextByItemId = new Map<string, TextParts>();
  const refusalTextByItemId = new Map<string, TextParts>();
  let activeTextChannel: 'message' | 'refusal' = 'message';
  let lastTextItemId: string | null = null;

  let reasoningSummaryText = '';

  const toolMap = new Map<string, ToolState>();
  const toolArgumentsTextById = new Map<string, string>();
  const toolCodeById = new Map<string, string>();

  const imageMetaByToolId = new Map<
    string,
    { format?: string | null; revisedPrompt?: string | null }
  >();
  const imageFramesByToolId = new Map<string, Map<number, GeneratedImageFrame>>();

  const chunksByTarget = new Map<ChunkKey, ChunkAccumulator>();

  let terminalSeen = false;
  let streamErrored = false;
  let streamedAttachments: MessageAttachment[] | null = null;
  let streamedStructuredOutput: unknown | null = null;
  let responseTextOverride: unknown | null = null;
  let lastAgentNotice: string | null = null;
  let finalConversationId: string | null = null;
  let finalResponseId: string | null = null;
  let lifecycleStatus: ConversationLifecycleStatus = 'idle';

  const citationsByItemId = new Map<string, Annotation[]>();

  const emitAgentNotice = (agent: string, prefix: 'Switched to') => {
    if (agent === lastAgentNotice) return;
    lastAgentNotice = agent;
    handlers.onAgentNotice?.(`${prefix} ${agent}`);
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
      status: patch.status ? upgradeStatus(existing.status, patch.status) : existing.status,
    };

    toolMap.set(toolId, next);
    const sorted = Array.from(toolMap.values()).sort(
      (a, b) => (a.outputIndex ?? Number.POSITIVE_INFINITY) - (b.outputIndex ?? Number.POSITIVE_INFINITY),
    );
    handlers.onToolStates?.(sorted);
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

  const applyToolStatus = (event: Extract<StreamingChatEvent, { kind?: 'tool.status' }>) => {
    const tool = event.tool;
    const toolId = tool.tool_call_id;
    const status = toolUiStatusFromProviderStatus(tool.status);
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
      const includesArguments =
        tool.arguments_json !== null &&
        tool.arguments_json !== undefined ||
        tool.arguments_text !== null &&
        tool.arguments_text !== undefined;

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
      const includesArguments =
        tool.arguments_json !== null &&
        tool.arguments_json !== undefined ||
        tool.arguments_text !== null &&
        tool.arguments_text !== undefined;

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

  const applyToolArgumentsDelta = (
    event: Extract<StreamingChatEvent, { kind?: 'tool.arguments.delta' }>,
  ) => {
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

  const applyToolArgumentsDone = (
    event: Extract<StreamingChatEvent, { kind?: 'tool.arguments.done' }>,
  ) => {
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

  const applyToolCodeDelta = (
    event: Extract<StreamingChatEvent, { kind?: 'tool.code.delta' }>,
  ) => {
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

  const applyToolCodeDone = (
    event: Extract<StreamingChatEvent, { kind?: 'tool.code.done' }>,
  ) => {
    toolCodeById.set(event.tool_call_id, event.code);
    upsertTool(event.tool_call_id, {
      name: 'code_interpreter',
      status: 'input-available',
      outputIndex: event.output_index,
      input: event.code,
    });
  };

  const applyToolOutput = (
    event: Extract<StreamingChatEvent, { kind?: 'tool.output' }>,
  ) => {
    upsertTool(event.tool_call_id, {
      status: 'output-available',
      outputIndex: event.output_index,
      output: event.output,
    });
  };

  const applyChunkDelta = (
    event: Extract<StreamingChatEvent, { kind?: 'chunk.delta' }>,
  ) => {
    const key = chunkKeyFor(event.target);
    const existing = chunksByTarget.get(key) ?? {
      encoding: event.encoding,
      parts: new Map<number, string>(),
    };
    if (!existing.encoding) existing.encoding = event.encoding;
    existing.parts.set(event.chunk_index, event.data);
    chunksByTarget.set(key, existing);
  };

  const applyChunkDone = (event: Extract<StreamingChatEvent, { kind?: 'chunk.done' }>) => {
    const key = chunkKeyFor(event.target);
    const acc = chunksByTarget.get(key);
    if (!acc) return;
    chunksByTarget.delete(key);

    const assembled = Array.from(acc.parts.entries())
      .sort(([a], [b]) => a - b)
      .map(([, value]) => value)
      .join('');

    if (
      event.target.entity_kind === 'tool_call' &&
      event.target.field === 'partial_image_b64' &&
      typeof event.target.part_index === 'number'
    ) {
      const toolId = event.target.entity_id;
      const partIndex = event.target.part_index;
      const meta = imageMetaByToolId.get(toolId);
      const mime = mimeFromImageFormat(meta?.format ?? null);
      const src =
        acc.encoding === 'base64' ? `data:${mime};base64,${assembled}` : assembled;

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

  for await (const chunk of stream) {
    if (chunk.type === 'error') {
      handlers.onError?.(chunk.payload);
      streamErrored = true;
      break;
    }

    const event = chunk.event;
    const kind = event.kind;
    if (!kind) {
      handlers.onError?.('Stream event missing kind');
      streamErrored = true;
      break;
    }

    if (event.conversation_id) {
      if (finalConversationId !== event.conversation_id) {
        finalConversationId = event.conversation_id;
        handlers.onConversationId?.(event.conversation_id);
      }
    }

    if (event.response_id) {
      finalResponseId = event.response_id;
    }

    if (event.agent && event.agent !== lastAgentNotice) {
      emitAgentNotice(event.agent, 'Switched to');
      handlers.onAgentChange?.(event.agent);
    }

    if (kind === 'lifecycle') {
      lifecycleStatus = event.status;
      handlers.onLifecycle?.(lifecycleStatus);
      continue;
    }

    if (kind === 'output_item.added' || kind === 'output_item.done') {
      const update: OutputItemUpdate = {
        itemId: event.item_id,
        outputIndex: event.output_index,
        itemType: event.item_type,
        role: event.role ?? null,
        status: event.status ?? null,
      };
      if (kind === 'output_item.added') {
        handlers.onOutputItemAdded?.(update);
        const placeholder = toolPlaceholderNameFromItemType(event.item_type);
        if (placeholder) {
          const existing = toolMap.get(event.item_id);
          if (!existing) {
            upsertTool(event.item_id, {
              name: placeholder,
              status: 'input-streaming',
              outputIndex: event.output_index,
            });
          } else if (existing.outputIndex === undefined || existing.outputIndex === null) {
            upsertTool(event.item_id, { outputIndex: event.output_index });
          }
        }
      } else {
        handlers.onOutputItemDone?.(update);
      }
      continue;
    }

    if (kind === 'message.delta') {
      const accumulated = appendDelta(messageTextByItemId, {
        itemId: event.item_id,
        contentIndex: event.content_index,
        delta: event.delta,
      });
      lastTextItemId = event.item_id;
      activeTextChannel = 'message';
      handlers.onTextDelta?.({
        channel: 'message',
        itemId: event.item_id,
        outputIndex: event.output_index,
        contentIndex: event.content_index,
        delta: event.delta,
        accumulatedText: accumulated,
        textWithCursor: `${accumulated}▋`,
      });
      continue;
    }

    if (kind === 'message.citation') {
      const existing = citationsByItemId.get(event.item_id) ?? [];
      citationsByItemId.set(event.item_id, [...existing, event.citation as Annotation]);
      continue;
    }

    if (kind === 'reasoning_summary.delta') {
      reasoningSummaryText += event.delta;
      handlers.onReasoningDelta?.(event.delta);
      continue;
    }

    if (kind === 'refusal.delta') {
      const accumulated = appendDelta(refusalTextByItemId, {
        itemId: event.item_id,
        contentIndex: event.content_index,
        delta: event.delta,
      });
      lastTextItemId = event.item_id;
      if (activeTextChannel === 'refusal' || messageTextByItemId.size === 0) {
        activeTextChannel = 'refusal';
        handlers.onTextDelta?.({
          channel: 'refusal',
          itemId: event.item_id,
          outputIndex: event.output_index,
          contentIndex: event.content_index,
          delta: event.delta,
          accumulatedText: accumulated,
          textWithCursor: `${accumulated}▋`,
        });
      }
      continue;
    }

    if (kind === 'refusal.done') {
      const accumulated = replaceText(refusalTextByItemId, {
        itemId: event.item_id,
        contentIndex: event.content_index,
        text: event.refusal_text,
      });
      lastTextItemId = event.item_id;
      if (activeTextChannel === 'refusal' || messageTextByItemId.size === 0) {
        activeTextChannel = 'refusal';
        handlers.onTextDelta?.({
          channel: 'refusal',
          itemId: event.item_id,
          outputIndex: event.output_index,
          contentIndex: event.content_index,
          delta: '',
          accumulatedText: accumulated,
          textWithCursor: `${accumulated}▋`,
        });
      }
      continue;
    }

    if (kind === 'tool.status') {
      applyToolStatus(event);
      continue;
    }

    if (kind === 'tool.arguments.delta') {
      applyToolArgumentsDelta(event);
      continue;
    }

    if (kind === 'tool.arguments.done') {
      applyToolArgumentsDone(event);
      continue;
    }

    if (kind === 'tool.code.delta') {
      applyToolCodeDelta(event);
      continue;
    }

    if (kind === 'tool.code.done') {
      applyToolCodeDone(event);
      continue;
    }

    if (kind === 'tool.output') {
      applyToolOutput(event);
      continue;
    }

    if (kind === 'chunk.delta') {
      applyChunkDelta(event);
      continue;
    }

    if (kind === 'chunk.done') {
      applyChunkDone(event);
      continue;
    }

    if (kind === 'error') {
      handlers.onError?.(event.error.message);
      streamErrored = true;
      terminalSeen = true;
      lifecycleStatus = 'failed';
      break;
    }

    if (kind === 'final') {
      terminalSeen = true;
      lifecycleStatus = event.final.status;

      responseTextOverride =
        event.final.response_text ??
        (event.final.status === 'refused' ? event.final.refusal_text : null) ??
        null;

      streamedStructuredOutput =
        event.final.structured_output !== undefined ? event.final.structured_output : null;
      streamedAttachments = event.final.attachments ?? null;

      if (event.final.reasoning_summary_text && event.final.reasoning_summary_text.length > reasoningSummaryText.length) {
        const delta = event.final.reasoning_summary_text.slice(reasoningSummaryText.length);
        if (delta) {
          reasoningSummaryText = event.final.reasoning_summary_text;
          handlers.onReasoningDelta?.(delta);
        }
      }

      handlers.onStructuredOutput?.(streamedStructuredOutput);
      handlers.onAttachments?.(streamedAttachments);
      break;
    }
  }

  if (streamErrored) {
    return {
      finalContent: '',
      conversationId: finalConversationId,
      responseId: finalResponseId,
      attachments: streamedAttachments ?? null,
      structuredOutput: streamedStructuredOutput,
      lifecycleStatus,
      citations: null,
      terminalSeen,
      errored: true,
    };
  }

  const finalContent = (() => {
    if (responseTextOverride !== null && responseTextOverride !== undefined) {
      if (typeof responseTextOverride === 'string') return responseTextOverride;
      try {
        return JSON.stringify(responseTextOverride);
      } catch {
        return String(responseTextOverride);
      }
    }
    if (!lastTextItemId) return '';
    const store = activeTextChannel === 'refusal' ? refusalTextByItemId : messageTextByItemId;
    return assembledText(store.get(lastTextItemId));
  })();

  const citations = (() => {
    if (lastTextItemId && activeTextChannel === 'message') {
      const forMessage = citationsByItemId.get(lastTextItemId);
      return forMessage?.length ? forMessage : null;
    }
    const all = Array.from(citationsByItemId.values()).flat();
    return all.length ? all : null;
  })();

  if (!terminalSeen) {
    const anyRefusal = Array.from(refusalTextByItemId.values()).some((parts) => assembledText(parts).length > 0);
    lifecycleStatus = anyRefusal ? 'refused' : lifecycleStatus;
  }

  return {
    finalContent,
    conversationId: finalConversationId,
    responseId: finalResponseId,
    attachments: streamedAttachments ?? null,
    structuredOutput: streamedStructuredOutput ?? null,
    lifecycleStatus,
    citations,
    terminalSeen,
    errored: false,
  };
}
