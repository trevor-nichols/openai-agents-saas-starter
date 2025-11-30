import type { MessageAttachment } from '@/lib/api/client/types.gen';
import type {
  ConversationLifecycleStatus,
  StreamChunk,
  ToolState,
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
  onError?: (errorText: string) => void;
  onConversationId?: (conversationId: string) => void;
}

export interface StreamConsumeResult {
  finalContent: string;
  conversationId: string | null;
  attachments: MessageAttachment[] | null;
  structuredOutput: unknown | null;
  lifecycleStatus: ConversationLifecycleStatus;
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
  let lifecycleStatus: ConversationLifecycleStatus = 'idle';

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

    if (event.kind === 'agent_update' && event.new_agent) {
      handlers.onAgentChange?.(event.new_agent);
      emitAgentNotice(event.new_agent, 'Switched to');
    }

    if (event.kind === 'raw_response') {
      if (event.raw_type === 'response.output_text.delta' && event.text_delta) {
        accumulatedContent += event.text_delta;
        handlers.onTextDelta?.(`${accumulatedContent}▋`, accumulatedContent);
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
    }

    if (event.kind === 'run_item' && event.run_item_name) {
      const toolId = event.tool_call_id || event.run_item_name;
      const existing = toolMap.get(toolId) || {
        id: toolId,
        name: event.tool_name || event.run_item_name,
        status: 'input-streaming' as const,
      };

      if (event.run_item_name === 'tool_called') {
        existing.status = 'input-available';
        existing.input = event.payload;
      } else if (event.run_item_name === 'tool_output') {
        existing.status = 'output-available';
        existing.output = event.payload;
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
      streamedAttachments = event.attachments;
      handlers.onAttachments?.(streamedAttachments ?? null);
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
      attachments: streamedAttachments ?? null,
      structuredOutput: streamedStructuredOutput,
      lifecycleStatus,
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
    attachments: streamedAttachments ?? null,
    structuredOutput: streamedStructuredOutput ?? null,
    lifecycleStatus,
    terminalSeen,
    errored: false,
  };
}
