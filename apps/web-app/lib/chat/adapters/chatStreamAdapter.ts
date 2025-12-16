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

export interface StreamConsumeHandlers {
  onTextDelta?: (contentWithCursor: string, accumulated: string) => void;
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

export async function consumeChatStream(
  stream: AsyncIterable<StreamChunk>,
  handlers: StreamConsumeHandlers,
): Promise<StreamConsumeResult> {
  let accumulatedMessageText = '';
  let accumulatedRefusalText = '';
  let activeTextChannel: 'message' | 'refusal' = 'message';

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

  let lastMessageId: string | null = null;
  const citationsByMessageId = new Map<string, Annotation[]>();

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
      errorText: patch.errorText ?? existing.errorText,
      status: patch.status ? upgradeStatus(existing.status, patch.status) : existing.status,
    };

    toolMap.set(toolId, next);
    handlers.onToolStates?.(Array.from(toolMap.values()));
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

    if (tool.tool_type === 'web_search') {
      upsertTool(toolId, {
        name: 'web_search',
        status,
        input: tool.query ?? undefined,
        output: tool.sources ?? undefined,
      });
      return;
    }

    if (tool.tool_type === 'file_search') {
      upsertTool(toolId, {
        name: 'file_search',
        status,
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
      input: event.code,
    });
  };

  const applyToolOutput = (
    event: Extract<StreamingChatEvent, { kind?: 'tool.output' }>,
  ) => {
    upsertTool(event.tool_call_id, {
      status: 'output-available',
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

    if (kind === 'message.delta') {
      lastMessageId = event.message_id;
      accumulatedMessageText += event.delta;
      activeTextChannel = 'message';
      handlers.onTextDelta?.(
        `${accumulatedMessageText}▋`,
        accumulatedMessageText,
      );
      continue;
    }

    if (kind === 'message.citation') {
      const existing = citationsByMessageId.get(event.message_id) ?? [];
      citationsByMessageId.set(event.message_id, [...existing, event.citation as Annotation]);
      continue;
    }

    if (kind === 'reasoning_summary.delta') {
      reasoningSummaryText += event.delta;
      handlers.onReasoningDelta?.(event.delta);
      continue;
    }

    if (kind === 'refusal.delta') {
      accumulatedRefusalText += event.delta;
      if (activeTextChannel === 'refusal' || accumulatedMessageText.length === 0) {
        activeTextChannel = 'refusal';
        handlers.onTextDelta?.(
          `${accumulatedRefusalText}▋`,
          accumulatedRefusalText,
        );
      }
      continue;
    }

    if (kind === 'refusal.done') {
      accumulatedRefusalText = event.refusal_text;
      if (activeTextChannel === 'refusal' || accumulatedMessageText.length === 0) {
        activeTextChannel = 'refusal';
        handlers.onTextDelta?.(
          `${accumulatedRefusalText}▋`,
          accumulatedRefusalText,
        );
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
    return activeTextChannel === 'refusal' ? accumulatedRefusalText : accumulatedMessageText;
  })();

  const citations = (() => {
    if (lastMessageId) {
      const forMessage = citationsByMessageId.get(lastMessageId);
      return forMessage?.length ? forMessage : null;
    }
    const all = Array.from(citationsByMessageId.values()).flat();
    return all.length ? all : null;
  })();

  if (!terminalSeen) {
    lifecycleStatus = accumulatedRefusalText.length > 0 ? 'refused' : lifecycleStatus;
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
