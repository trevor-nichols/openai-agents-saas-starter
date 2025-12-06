import type {
  AgentRunOptions,
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
  runOptions?: AgentRunOptions | null;
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

// --- Enriched streaming payloads ---

export type UrlCitation = {
  type: 'url_citation';
  start_index: number;
  end_index: number;
  title?: string | null;
  url: string;
};

export type ContainerFileCitation = {
  type: 'container_file_citation';
  start_index: number;
  end_index: number;
  container_id: string;
  file_id: string;
  filename?: string | null;
  url?: string | null;
};

export type FileCitation = {
  type: 'file_citation';
  start_index?: number | null;
  end_index?: number | null;
  index?: number | null;
  file_id: string;
  filename?: string | null;
};

export type Annotation = UrlCitation | ContainerFileCitation | FileCitation;

export type WebSearchAction = {
  type: 'search';
  query: string;
  sources: string[] | null;
};

export type WebSearchCall = {
  id: string;
  type: 'web_search_call';
  status: 'in_progress' | 'completed';
  action: WebSearchAction | null;
};

export type ToolCallPayload =
  | {
      tool_type: 'web_search';
      web_search_call: WebSearchCall | null;
      code_interpreter_call?: undefined;
      file_search_call?: undefined;
    }
  | {
      tool_type: 'code_interpreter';
      code_interpreter_call: {
        id: string;
        type: 'code_interpreter_call';
        status: 'in_progress' | 'interpreting' | 'completed';
        code?: string | null;
        outputs?: unknown[] | null;
      } | null;
      web_search_call?: undefined;
      file_search_call?: undefined;
    }
  | {
      tool_type: 'file_search';
      file_search_call: {
        id: string;
        type: 'file_search_call';
        status: 'in_progress' | 'searching' | 'completed';
        queries?: string[] | null;
        results?: unknown[] | null;
      } | null;
      web_search_call?: undefined;
      code_interpreter_call?: undefined;
    }
  | {
      tool_type: string;
      // Future tool types fall back here
      [key: string]: unknown;
    };

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
