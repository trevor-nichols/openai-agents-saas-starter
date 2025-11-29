import type {
  MessageAttachment,
  StreamingChatEvent,
} from '@/lib/api/client/types.gen';

export interface StreamChatParams {
  message: string;
  conversationId?: string | null;
  agentType?: string | null;
  shareLocation?: boolean;
  location?: {
    city?: string | null;
    region?: string | null;
    country?: string | null;
    timezone?: string | null;
  } | null;
  runOptions?: RunOptionsInput;
}

export type StreamChunk =
  | { type: 'event'; event: StreamingChatEvent }
  | { type: 'error'; payload: string; conversationId?: string };

export type ToolState = {
  id: string;
  name?: string | null;
  status: 'input-streaming' | 'input-available' | 'output-available' | 'output-error';
  input?: unknown;
  output?: unknown;
  errorText?: string | null;
};

export type ConversationLifecycleStatus =
  | 'idle'
  | 'created'
  | 'in_progress'
  | 'completed'
  | 'incomplete'
  | 'failed';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  isStreaming?: boolean;
  attachments?: MessageAttachment[] | null;
  structuredOutput?: unknown | null;
}

export type RunOptionsInput = {
  maxTurns?: number | null;
  previousResponseId?: string | null;
  handoffInputFilter?: string | null;
  runConfig?: unknown | null;
};
