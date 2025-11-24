// File Path: features/chat/components/ChatInterface.tsx
// Description: Command-center chat interface aligned with the glass UI system.

'use client';

import { useMemo, useState, type FormEvent } from 'react';
import type { ChatStatus } from 'ai';

import { GlassPanel, InlineTag } from '@/components/ui/foundation';
import { EmptyState, SkeletonPanel } from '@/components/ui/states';
import { cn } from '@/lib/utils';
import { formatClockTime } from '@/lib/utils/time';
import type { ChatMessage, ConversationLifecycleStatus, ToolState } from '@/lib/chat/types';
import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from '@/components/ui/ai/conversation';
import { Message, MessageAvatar, MessageContent } from '@/components/ui/ai/message';
import {
  PromptInput,
  PromptInputButton,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputToolbar,
  PromptInputTools,
} from '@/components/ui/ai/prompt-input';
import { Reasoning, ReasoningContent, ReasoningTrigger } from '@/components/ui/ai/reasoning';
import { Tool, ToolContent, ToolHeader, ToolInput, ToolOutput } from '@/components/ui/ai/tool';
import type { ToolUIPart } from 'ai';
import { CodeBlock } from '@/components/ui/ai/code-block';
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from '@/components/ui/tooltip';
import { Info } from 'lucide-react';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  onSendMessage: (messageText: string) => Promise<void>;
  isSending: boolean;
  currentConversationId: string | null;
  onClearConversation?: () => void | Promise<void>;
  isClearingConversation?: boolean;
  isLoadingHistory?: boolean;
  tools?: ToolState[];
  reasoningText?: string;
  activeAgent?: string;
  lifecycleStatus?: ConversationLifecycleStatus;
  shareLocation: boolean;
  onShareLocationChange: (value: boolean) => void;
  locationHint: {
    city?: string | null;
    region?: string | null;
    country?: string | null;
    timezone?: string | null;
  };
  onLocationHintChange: (field: 'city' | 'region' | 'country' | 'timezone', value: string) => void;
  className?: string;
}

export function ChatInterface({
  messages,
  onSendMessage,
  isSending,
  currentConversationId,
  onClearConversation,
  isClearingConversation = false,
  isLoadingHistory = false,
  tools = [],
  reasoningText = '',
  activeAgent,
  lifecycleStatus,
  shareLocation,
  onShareLocationChange,
  locationHint,
  onLocationHintChange,
  className,
}: ChatInterfaceProps) {
  const [messageInput, setMessageInput] = useState('');
  const chatStatus = useMemo<ChatStatus | undefined>(() => {
    if (isClearingConversation || isLoadingHistory) return 'submitted';
    if (isSending) return 'streaming';
    return undefined;
  }, [isClearingConversation, isLoadingHistory, isSending]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const value = messageInput.trim();
    if (!value || isSending || isLoadingHistory) return;
    setMessageInput('');
    await onSendMessage(value);
  };

  return (
    <GlassPanel className={cn('flex h-full flex-col overflow-hidden p-0', className)}>
      <Conversation className="flex-1">
        <ConversationContent className="space-y-4 px-6 py-6">
          {isLoadingHistory ? (
            <SkeletonPanel lines={9} />
          ) : messages.length === 0 ? (
            <EmptyState
              title="No messages yet"
              description="Compose a prompt below to brief your agent."
              className="border border-white/5 bg-white/5"
            />
          ) : (
            <>
              {messages.map((message) => (
                <Message key={message.id} from={message.role}>
                  <MessageContent>
                    <div className="flex items-center justify-between gap-3">
                      <InlineTag tone={message.role === 'user' ? 'positive' : 'default'}>
                        {message.role === 'user' ? 'You' : 'Agent'}
                      </InlineTag>
                      {message.timestamp && !message.isStreaming ? (
                        <span className="text-[11px] uppercase tracking-wide text-foreground/50">
                          {formatClockTime(message.timestamp)}
                        </span>
                      ) : (
                        <span className="text-[11px] uppercase tracking-wide text-foreground/40">
                          {message.isStreaming ? 'Streaming…' : 'Pending'}
                        </span>
                      )}
                    </div>
                    <p className="mt-2 leading-relaxed whitespace-pre-wrap">{message.content}</p>
                  </MessageContent>
                  <MessageAvatar
                    src=""
                    name={message.role === 'user' ? 'You' : 'Agent'}
                  />
                </Message>
              ))}

              {reasoningText ? (
                <Reasoning isStreaming={isSending} defaultOpen className="rounded-lg border border-white/5 bg-white/5 px-4 py-3">
                  <ReasoningTrigger title="Reasoning" />
                  <ReasoningContent>{reasoningText}</ReasoningContent>
                </Reasoning>
              ) : null}

              {tools.length > 0 ? (
                <div className="space-y-3">
                  {tools.map((tool) => (
                    <Tool key={tool.id} defaultOpen={tool.status !== 'output-available'}>
                      <ToolHeader
                        type={`tool-${tool.name || 'call'}` as ToolUIPart['type']}
                        state={tool.status}
                      />
                      <ToolContent>
                        {tool.input ? <ToolInput input={tool.input} /> : null}
                        <ToolOutput
                          output={
                            tool.output ? (
                              <CodeBlock code={JSON.stringify(tool.output, null, 2)} language="json" />
                            ) : undefined
                          }
                          errorText={tool.errorText ?? undefined}
                        />
                      </ToolContent>
                    </Tool>
                  ))}
                </div>
              ) : null}
            </>
          )}
        </ConversationContent>
        <ConversationScrollButton />
      </Conversation>

      <PromptInput onSubmit={handleSubmit} className="border-t border-white/5 bg-white/5">
        <PromptInputTextarea
          value={messageInput}
          onChange={(event) => setMessageInput(event.target.value)}
          placeholder={currentConversationId ? `Message ${currentConversationId.substring(0, 8)}…` : 'Ask your agent…'}
          disabled={isSending || isLoadingHistory}
          rows={2}
        />
        <PromptInputToolbar className="flex flex-col gap-3 p-3 sm:flex-row sm:items-center sm:justify-between">
          <PromptInputTools className="flex flex-col gap-3">
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
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2">
                <Switch
                  id="share-location"
                  checked={shareLocation}
                  onCheckedChange={onShareLocationChange}
                  disabled={isSending || isLoadingHistory}
                />
                <Label
                  htmlFor="share-location"
                  className="text-xs font-medium text-foreground/80"
                >
                  Bias web search with approximate location
                </Label>
                <InlineTag tone="default">Optional</InlineTag>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        className="text-foreground/60 transition hover:text-foreground"
                        aria-label="How location is used"
                      >
                        <Info size={14} strokeWidth={1.75} />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="top">
                      City/region/country/timezone are trimmed, optional, and only sent when toggled on to bias web search.
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
              {shareLocation ? (
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                  <Input
                    placeholder="City"
                    value={locationHint.city ?? ''}
                    onChange={(event) => onLocationHintChange('city', event.target.value)}
                    disabled={isSending}
                  />
                  <Input
                    placeholder="Region/State"
                    value={locationHint.region ?? ''}
                    onChange={(event) => onLocationHintChange('region', event.target.value)}
                    disabled={isSending}
                  />
                  <Input
                    placeholder="Country"
                    value={locationHint.country ?? ''}
                    onChange={(event) => onLocationHintChange('country', event.target.value)}
                    disabled={isSending}
                  />
                  <Input
                    placeholder="Timezone (e.g., America/Chicago)"
                    value={locationHint.timezone ?? ''}
                    onChange={(event) => onLocationHintChange('timezone', event.target.value)}
                    disabled={isSending}
                    title="IANA timezone, e.g., America/Chicago"
                  />
                </div>
              ) : null}
            </div>
          </PromptInputTools>
          <div className="flex flex-wrap items-center gap-2">
            <InlineTag tone="default">{chatStatus ?? 'idle'}</InlineTag>
            {lifecycleStatus ? <InlineTag tone="default">{lifecycleStatus}</InlineTag> : null}
            {activeAgent ? <InlineTag tone="default">Agent: {activeAgent}</InlineTag> : null}
            <PromptInputSubmit
              status={chatStatus}
              disabled={isSending || isLoadingHistory || !messageInput.trim()}
            />
          </div>
        </PromptInputToolbar>
      </PromptInput>
    </GlassPanel>
  );
}
