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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import type { ConversationLifecycleStatus } from '@/lib/chat/types';

type MemoryModeOption = 'inherit' | 'none' | 'trim' | 'summarize' | 'compact';

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
  memoryMode: MemoryModeOption;
  memoryInjection?: boolean;
  onMemoryModeChange: (mode: MemoryModeOption) => void;
  onMemoryInjectionChange: (value: boolean) => void;
  isUpdatingMemory: boolean;
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
  memoryMode,
  memoryInjection,
  onMemoryModeChange,
  onMemoryInjectionChange,
  isUpdatingMemory,
}: PromptComposerProps) {
  const disabled = isSending || isLoadingHistory;
  const memoryDisabled = disabled || !currentConversationId || isUpdatingMemory;

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
          <div className="flex flex-wrap items-center gap-2">
            <Select
              value={memoryMode}
              onValueChange={(value) =>
                onMemoryModeChange(value as MemoryModeOption)
              }
              disabled={memoryDisabled}
            >
              <SelectTrigger className="w-[150px] justify-between rounded-lg border border-white/10 bg-white/5 text-xs font-medium text-muted-foreground">
                <SelectValue placeholder="Memory strategy" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="inherit">Use defaults</SelectItem>
                <SelectItem value="none">None</SelectItem>
                <SelectItem value="trim">Trim</SelectItem>
                <SelectItem value="summarize">Summarize</SelectItem>
                <SelectItem value="compact">Compact</SelectItem>
              </SelectContent>
            </Select>
            <div className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-1">
              <span className="text-xs text-muted-foreground">Inject summary</span>
              <Switch
                checked={Boolean(memoryInjection)}
                disabled={memoryDisabled}
                onCheckedChange={(checked) => onMemoryInjectionChange(checked)}
              />
            </div>
          </div>
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
