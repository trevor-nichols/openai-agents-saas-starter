import { FormEvent } from 'react';
import type { ChatStatus } from 'ai';

import {
  PromptInput,
  PromptInputButton,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputToolbar,
  PromptInputTools,
} from '@/components/ui/ai/prompt-input';
import { InlineTag } from '@/components/ui/foundation';
import { Loader } from '@/components/ui/ai/loader';
import { LocationOptIn } from '@/components/ui/location';
import type { ConversationLifecycleStatus } from '@/lib/chat/types';

interface PromptComposerProps {
  messageInput: string;
  onChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => Promise<void> | void;
  onClearConversation?: () => void;
  isClearingConversation: boolean;
  isLoadingHistory: boolean;
  isSending: boolean;
  chatStatus?: ChatStatus;
  lifecycleStatus?: ConversationLifecycleStatus;
  activeAgent?: string;
  currentConversationId: string | null;
  shareLocation: boolean;
  onShareLocationChange: (value: boolean) => void;
  locationHint: {
    city?: string | null;
    region?: string | null;
    country?: string | null;
    timezone?: string | null;
  };
  onLocationHintChange: (field: 'city' | 'region' | 'country' | 'timezone', value: string) => void;
}

export function PromptComposer({
  messageInput,
  onChange,
  onSubmit,
  onClearConversation,
  isClearingConversation,
  isLoadingHistory,
  isSending,
  chatStatus,
  lifecycleStatus,
  activeAgent,
  currentConversationId,
  shareLocation,
  onShareLocationChange,
  locationHint,
  onLocationHintChange,
}: PromptComposerProps) {
  const disabled = isSending || isLoadingHistory;

  return (
    <PromptInput onSubmit={onSubmit} className="border-t border-white/5 bg-white/5 rounded-none border-x-0 border-b-0">
      <PromptInputTextarea
        value={messageInput}
        onChange={(event) => onChange(event.target.value)}
        placeholder={currentConversationId ? `Message ${currentConversationId.substring(0, 8)}…` : 'Ask your agent…'}
        disabled={disabled}
        rows={2}
      />
      <PromptInputToolbar className="flex flex-col gap-3 p-3 sm:flex-row sm:items-center sm:justify-between">
        <PromptInputTools className="flex flex-col gap-3 [&_button:first-child]:rounded-lg">
          {onClearConversation && currentConversationId ? (
            <PromptInputButton
              variant="ghost"
              onClick={() => {
                void onClearConversation();
              }}
              disabled={isClearingConversation || isLoadingHistory}
            >
              {isClearingConversation ? 'Clearing…' : 'Clear chat'}
            </PromptInputButton>
          ) : null}
          <LocationOptIn
            shareLocation={shareLocation}
            onShareLocationChange={onShareLocationChange}
            location={locationHint}
            onLocationChange={onLocationHintChange}
            disabled={disabled}
          />
        </PromptInputTools>
        <div className="flex flex-wrap items-center gap-2">
          {chatStatus === 'streaming' ? (
            <div className="flex items-center gap-1 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-muted-foreground">
              <Loader size={14} />
              <span className="uppercase tracking-wide">Streaming</span>
            </div>
          ) : chatStatus ? (
            <InlineTag tone="default">{chatStatus}</InlineTag>
          ) : null}
          {lifecycleStatus ? <InlineTag tone="default">{lifecycleStatus}</InlineTag> : null}
          {activeAgent ? <InlineTag tone="default">Agent: {activeAgent}</InlineTag> : null}
          <PromptInputSubmit status={chatStatus} disabled={disabled || !messageInput.trim()} />
        </div>
      </PromptInputToolbar>
    </PromptInput>
  );
}
