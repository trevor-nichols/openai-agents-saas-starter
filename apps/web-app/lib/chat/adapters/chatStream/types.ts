import type { MessageAttachment, StreamingChatEvent } from '@/lib/api/client/types.gen';

import type { ConversationLifecycleStatus, StreamChunk, ToolState, Annotation } from '../../types';

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
};

export interface StreamConsumeHandlers {
  onOutputItemAdded?: (update: OutputItemUpdate) => void;
  onOutputItemDone?: (update: OutputItemUpdate) => void;
  onTextDelta?: (update: TextDeltaUpdate) => void;
  onReasoningDelta?: (delta: string) => void;
  onToolStates?: (toolStates: ToolState[]) => void;
  onLifecycle?: (status: ConversationLifecycleStatus) => void;
  onAgentChange?: (agent: string) => void;
  onMemoryCheckpoint?: (
    event: Extract<StreamingChatEvent, { kind?: 'memory.checkpoint' }>,
  ) => void;
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

export type ConsumeChatStreamParams = {
  stream: AsyncIterable<StreamChunk>;
  handlers: StreamConsumeHandlers;
};

