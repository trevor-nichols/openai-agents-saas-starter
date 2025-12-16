import type {
  AgentRunOptions,
  MessageAttachment,
  StreamingChatEvent,
  UrlCitation,
  ContainerFileCitation,
  FileCitation,
} from '@/lib/api/client/types.gen';

export type { UrlCitation, ContainerFileCitation, FileCitation } from '@/lib/api/client/types.gen';

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
  runOptions?: AgentRunOptions | null;
}

export type StreamChunk =
  | { type: 'event'; event: StreamingChatEvent }
  | { type: 'error'; payload: string; conversationId?: string };

export type ToolState = {
  id: string;
  name?: string | null;
  outputIndex?: number | null;
  status: 'input-streaming' | 'input-available' | 'output-available' | 'output-error';
  input?: unknown;
  output?: unknown;
  errorText?: string | null;
};

export type ToolEventAnchors = Record<string, string[]>;

export type ConversationLifecycleStatus =
  | 'idle'
  | 'queued'
  | 'in_progress'
  | 'completed'
  | 'incomplete'
  | 'failed'
  | 'cancelled'
  | 'refused';

export type Annotation = UrlCitation | ContainerFileCitation | FileCitation;

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  isStreaming?: boolean;
  attachments?: MessageAttachment[] | null;
  structuredOutput?: unknown | null;
  citations?: Annotation[] | null;
}
