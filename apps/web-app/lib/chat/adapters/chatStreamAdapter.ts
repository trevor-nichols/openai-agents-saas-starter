import type { MessageAttachment, StreamingChatEvent } from '@/lib/api/client/types.gen';
import type {
  ConversationLifecycleStatus,
  StreamChunk,
  ToolState,
  Annotation,
  ToolCallPayload,
  WebSearchCall,
} from '../types';

const lifecycleMap: Record<string, ConversationLifecycleStatus> = {
  'response.created': 'created',
  'response.in_progress': 'in_progress',
  'response.completed': 'completed',
  'response.incomplete': 'incomplete',
  'response.failed': 'failed',
};

export interface StreamConsumeHandlers {
  onTextDelta?: (contentWithCursor: string, accumulated: string) => void;
  onReasoningDelta?: (delta: string) => void;
  onToolStates?: (toolStates: ToolState[]) => void;
  onLifecycle?: (status: ConversationLifecycleStatus) => void;
  onAgentChange?: (agent: string) => void;
  onAgentNotice?: (notice: string) => void;
  onAttachments?: (attachments: MessageAttachment[] | null) => void;
  onStructuredOutput?: (data: unknown) => void;
  onGuardrailEvents?: (events: StreamingChatEvent[]) => void;
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

export async function consumeChatStream(
  stream: AsyncIterable<StreamChunk>,
  handlers: StreamConsumeHandlers,
): Promise<StreamConsumeResult> {
  let accumulatedContent = '';
  const toolMap = new Map<string, ToolState>();
  let terminalSeen = false;
  let streamErrored = false;
  let streamedAttachments: MessageAttachment[] | null | undefined = undefined;
  let streamedStructuredOutput: unknown | null = null;
  let responseTextOverride: unknown | null = null;
  let lastAgentNotice: string | null = null;
  let finalConversationId: string | null = null;
  let finalResponseId: string | null = null;
  let lifecycleStatus: ConversationLifecycleStatus = 'idle';
  const collectedCitations: Annotation[] = [];
  const guardrailEvents: StreamingChatEvent[] = [];

  const isWebSearchToolCall = (
    payload: ToolCallPayload | undefined,
  ): payload is { tool_type: 'web_search'; web_search_call: WebSearchCall | null } =>
    Boolean(payload && payload.tool_type === 'web_search' && 'web_search_call' in payload);
  const isCodeInterpreterToolCall = (
    payload: ToolCallPayload | undefined,
  ): payload is {
    tool_type: 'code_interpreter';
    code_interpreter_call: {
      id: string;
      type: 'code_interpreter_call';
      status: 'in_progress' | 'interpreting' | 'completed';
      code?: string | null;
      outputs?: unknown[] | null;
    } | null;
  } => Boolean(payload && payload.tool_type === 'code_interpreter' && 'code_interpreter_call' in payload);
  const isFileSearchToolCall = (
    payload: ToolCallPayload | undefined,
  ): payload is {
    tool_type: 'file_search';
    file_search_call: {
      id: string;
      type: 'file_search_call';
      status: 'in_progress' | 'searching' | 'completed';
      queries?: string[] | null;
      results?: unknown[] | null;
    } | null;
  } => Boolean(payload && payload.tool_type === 'file_search' && 'file_search_call' in payload);

  const emitAgentNotice = (agent: string, prefix: 'Switched to' | 'Handed off to') => {
    if (agent === lastAgentNotice) return;
    lastAgentNotice = agent;
    handlers.onAgentNotice?.(`${prefix} ${agent}`);
  };

  for await (const chunk of stream) {
    if (chunk.type === 'error') {
      handlers.onError?.(chunk.payload);
      streamErrored = true;
      break;
    }

    const event = chunk.event;

    if (event.kind === 'agent_updated_stream_event' && event.new_agent) {
      handlers.onAgentChange?.(event.new_agent);
      emitAgentNotice(event.new_agent, 'Switched to');
    }

    if (event.kind === 'guardrail_result') {
      guardrailEvents.push(event);
      handlers.onGuardrailEvents?.([...guardrailEvents]);
    }

    if (event.kind === 'raw_response_event') {
      if (event.raw_type === 'response.output_text.delta' && event.text_delta) {
        accumulatedContent += event.text_delta;
        handlers.onTextDelta?.(`${accumulatedContent}▋`, accumulatedContent);
      }

      if (event.response_id) {
        finalResponseId = event.response_id;
      }

      if (
        (event.raw_type === 'response.reasoning_text.delta' ||
          event.raw_type === 'response.reasoning_summary_text.delta') &&
        event.reasoning_delta
      ) {
        handlers.onReasoningDelta?.(event.reasoning_delta);
      }

      if (event.raw_type) {
        const nextStatus = lifecycleMap[event.raw_type];
        if (nextStatus) {
          lifecycleStatus = nextStatus;
          handlers.onLifecycle?.(nextStatus);
        }

      }

      if (event.response_text !== undefined && event.response_text !== null) {
        responseTextOverride = event.response_text;
      }

      // Citations attached directly on the event (additive schema)
      const annotations = (event as unknown as { annotations?: Annotation[] }).annotations;
      if (annotations?.length) {
        collectedCitations.push(...annotations);
      } else if (event.raw_type === 'response.output_text.annotation.added') {
        // Fallback for upstreams that do not populate the additive annotations array
        const annotation = (event.payload as unknown as { annotation?: Annotation })?.annotation;
        if (annotation?.type === 'url_citation' || annotation?.type === 'container_file_citation') {
          collectedCitations.push(annotation);
        }
      }

      // Tool call payload (additive schema; currently web_search, code_interpreter, file_search)
      const toolCall = (event as unknown as { tool_call?: ToolCallPayload }).tool_call;
      if (isWebSearchToolCall(toolCall) && toolCall.web_search_call) {
        const call = toolCall.web_search_call;
        const toolId = call.id;
        const nextState: ToolState = {
          id: toolId,
          name: 'web_search',
          status: call.status === 'completed' ? 'output-available' : 'input-available',
          input: call.action?.query,
          output: call.action ? { action: call.action } : undefined,
        };
        const prev = toolMap.get(toolId);
        toolMap.set(toolId, { ...prev, ...nextState });
        handlers.onToolStates?.(Array.from(toolMap.values()));
      } else if (isCodeInterpreterToolCall(toolCall) && toolCall.code_interpreter_call) {
        const call = toolCall.code_interpreter_call;
        const toolId = call.id || 'code_interpreter';
        const status =
          call.status === 'completed'
            ? 'output-available'
            : call.status === 'interpreting'
              ? 'input-available'
              : 'input-streaming';
        const nextState: ToolState = {
          id: toolId,
          name: 'code_interpreter',
          status,
          input: call.code,
          output: call.outputs ?? undefined,
        };
        const prev = toolMap.get(toolId);
        toolMap.set(toolId, { ...prev, ...nextState });
        handlers.onToolStates?.(Array.from(toolMap.values()));
      } else if (isFileSearchToolCall(toolCall) && toolCall.file_search_call) {
        const call = toolCall.file_search_call;
        const toolId = call.id || 'file_search';
        const status =
          call.status === 'completed'
            ? 'output-available'
            : call.status === 'searching'
              ? 'input-available'
              : 'input-streaming';
        const nextState: ToolState = {
          id: toolId,
          name: 'file_search',
          status,
          input: call.queries,
          output: call.results ?? undefined,
        };
        const prev = toolMap.get(toolId);
        toolMap.set(toolId, { ...prev, ...nextState });
        handlers.onToolStates?.(Array.from(toolMap.values()));
      }
    }

    if (event.kind === 'run_item_stream_event' && event.run_item_name) {
      const isToolEvent =
        event.run_item_type === 'tool_call_item' ||
        event.run_item_type === 'tool_call_output_item' ||
        (event.run_item_name?.startsWith('tool_') ?? false);

      if (!isToolEvent) {
        // Ignore non-tool run items (e.g., agent messages) for tool state UI.
        if (
          (event.run_item_name === 'handoff_requested' || event.run_item_name === 'handoff_occured') &&
          event.agent
        ) {
          emitAgentNotice(event.agent, 'Handed off to');
          handlers.onAgentChange?.(event.agent);
        }
        continue;
      }

      const toolId = event.tool_call_id || event.run_item_name;
      const existing = toolMap.get(toolId) || {
        id: toolId,
        name:
          event.tool_name ||
          ((event.tool_call as ToolCallPayload | undefined)?.tool_type ?? event.run_item_name),
        status: 'input-streaming' as const,
      };

      if (event.run_item_name === 'tool_called') {
        existing.status = 'input-available';
        existing.input = event.payload;
      } else if (event.run_item_name === 'tool_output') {
        existing.status = 'output-available';
        const toolPayload = event.tool_call as ToolCallPayload | undefined;
        const hasOutputsField =
          typeof event.payload === 'object' &&
          event.payload !== null &&
          'outputs' in (event.payload as Record<string, unknown>);
        const hasResultsField =
          typeof event.payload === 'object' &&
          event.payload !== null &&
          'results' in (event.payload as Record<string, unknown>);

        if (toolPayload?.tool_type === 'code_interpreter' && hasOutputsField) {
          const maybeOutputs = (event.payload as { outputs?: unknown }).outputs;
          existing.output = maybeOutputs ?? event.payload;
        } else if (toolPayload?.tool_type === 'file_search' && hasResultsField) {
          const maybeResults = (event.payload as { results?: unknown }).results;
          existing.output = maybeResults ?? event.payload;
        } else {
          existing.output = event.payload;
        }
      }

      if (
        (event.run_item_name === 'handoff_requested' || event.run_item_name === 'handoff_occured') &&
        event.agent
      ) {
        emitAgentNotice(event.agent, 'Handed off to');
        handlers.onAgentChange?.(event.agent);
      }

      toolMap.set(toolId, existing);
      handlers.onToolStates?.(Array.from(toolMap.values()));
    }

    if (event.kind === 'error') {
      const errorText =
        typeof event.payload === 'object' && event.payload && 'error' in event.payload
          ? String(event.payload.error)
          : 'Stream error';
      handlers.onError?.(errorText);
      streamErrored = true;
      break;
    }

    if (event.conversation_id) {
      finalConversationId = event.conversation_id;
      handlers.onConversationId?.(event.conversation_id);
    }

    if (event.attachments && event.attachments.length > 0) {
      const attachments = event.attachments.filter(
        (att): att is MessageAttachment =>
          !!att && typeof att === 'object' && 'object_id' in att && 'filename' in att,
      );
      if (attachments.length > 0) {
        streamedAttachments = attachments;
        handlers.onAttachments?.(streamedAttachments ?? null);
      }
    }

    if (event.structured_output !== undefined) {
      streamedStructuredOutput = event.structured_output;
      handlers.onStructuredOutput?.(streamedStructuredOutput);
    }

    if (event.is_terminal) {
      terminalSeen = true;
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
      citations: collectedCitations.length ? collectedCitations : null,
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
    return accumulatedContent;
  })();

  if (terminalSeen && !['completed', 'failed', 'incomplete'].includes(lifecycleStatus)) {
    lifecycleStatus = 'completed';
  }

  return {
    finalContent,
    conversationId: finalConversationId,
    responseId: finalResponseId,
    attachments: streamedAttachments ?? null,
    structuredOutput: streamedStructuredOutput ?? null,
    lifecycleStatus,
    citations: collectedCitations.length ? collectedCitations : null,
    terminalSeen,
    errored: false,
  };
}
