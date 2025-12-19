import type { MessageAttachment, StreamingChatEvent } from '@/lib/api/client/types.gen';
import type { PublicSseEvent } from '@/lib/api/client/types.gen';
import type { ReasoningPart } from '@/lib/streams/publicSseV1/reasoningParts';

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
  onEvent?: (event: PublicSseEvent) => void;
  onOutputItemAdded?: (update: OutputItemUpdate) => void;
  onOutputItemDone?: (update: OutputItemUpdate) => void;
  onTextDelta?: (update: TextDeltaUpdate) => void;
  onReasoningDelta?: (delta: string) => void;
  onReasoningParts?: (parts: ReasoningPart[]) => void;
  onToolStates?: (toolStates: ToolState[]) => void;
  onLifecycle?: (status: ConversationLifecycleStatus) => void;
  onAgentChange?: (agent: string) => void;
  onAgentUpdated?: (event: Extract<StreamingChatEvent, { kind?: 'agent.updated' }>) => void;
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
