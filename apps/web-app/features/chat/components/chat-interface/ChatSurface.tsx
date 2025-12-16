import { FormEvent } from 'react';
import type { ChatStatus } from 'ai';

import { InlineTag, SectionHeader, type SectionHeaderProps } from '@/components/ui/foundation';
import { Banner, BannerClose, BannerTitle } from '@/components/ui/banner';
import { Conversation, ConversationContent, ConversationScrollButton } from '@/components/ui/ai/conversation';
import { EmptyState, SkeletonPanel } from '@/components/ui/states';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

import { MessageList } from './MessageList';
import { ReasoningPanel } from './ReasoningPanel';
import { PromptComposer } from './PromptComposer';
import type { ChatMessage, ConversationLifecycleStatus, ToolEventAnchors, ToolState } from '@/lib/chat/types';
import type { AttachmentState } from '../../hooks/useAttachmentResolver';

type MemoryModeOption = 'inherit' | 'none' | 'trim' | 'summarize' | 'compact';

interface ChatSurfaceProps {
  className?: string;
  headerProps?: SectionHeaderProps;
  agentNotices: { id: string; text: string }[];
  isLoadingHistory: boolean;
  messages: ChatMessage[];
  reasoningText?: string;
  tools: ToolState[];
  toolEventAnchors?: ToolEventAnchors;
  chatStatus?: ChatStatus;
  lifecycleStatus?: ConversationLifecycleStatus;
  activeAgent?: string;
  isSending: boolean;
  isClearingConversation: boolean;
  currentConversationId: string | null;
  hasOlderMessages: boolean;
  isLoadingOlderMessages: boolean;
  onLoadOlderMessages?: () => void | Promise<void>;
  onRetryMessages?: () => void;
  historyError?: string | null;
  errorMessage?: string | null;
  onClearError?: () => void;
  onClearHistory?: () => void;
  messageInput: string;
  onMessageInputChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => Promise<void> | void;
  onCopyMessage: (text: string) => void;
  onClearConversation?: () => void;
  attachmentState: AttachmentState;
  resolveAttachment: (objectId: string) => Promise<void>;
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

export function ChatSurface({
  className,
  headerProps,
  agentNotices,
  isLoadingHistory,
  messages,
  reasoningText,
  tools,
  toolEventAnchors,
  chatStatus,
  lifecycleStatus,
  activeAgent,
  isSending,
  isClearingConversation,
  currentConversationId,
  hasOlderMessages,
  isLoadingOlderMessages,
  onLoadOlderMessages,
  onRetryMessages,
  historyError,
  errorMessage,
  onClearError,
  onClearHistory,
  messageInput,
  onMessageInputChange,
  onSubmit,
  onCopyMessage,
  onClearConversation,
  attachmentState,
  resolveAttachment,
  shareLocation,
  onShareLocationChange,
  locationHint,
  onLocationHintChange,
  memoryMode,
  memoryInjection,
  onMemoryModeChange,
  onMemoryInjectionChange,
  isUpdatingMemory,
}: ChatSurfaceProps) {
  const showEmpty = !isLoadingHistory && messages.length === 0;
  const isBusy = isSending || isLoadingHistory;

  return (
    <div className={cn('relative flex min-h-0 flex-1 flex-col overflow-hidden bg-background', className)}>
      {headerProps ? (
        <div className="border-b border-border/40 px-6 py-4">
          <SectionHeader {...headerProps} size="compact" />
        </div>
      ) : null}

      <Conversation className="flex-1">
        <ConversationContent className="mx-auto max-w-3xl space-y-6 px-4 py-8">
          {agentNotices.length > 0 ? (
            <div className="space-y-2">
              {agentNotices.map((notice) => (
                <Banner key={notice.id} variant="muted" inset>
                  <BannerTitle>{notice.text}</BannerTitle>
                  <InlineTag tone="default">Agent update</InlineTag>
                  <BannerClose aria-label="Dismiss agent update" />
                </Banner>
              ))}
            </div>
          ) : null}

          {isLoadingHistory ? (
            <SkeletonPanel lines={9} />
          ) : historyError ? (
            <Banner inset className="gap-3">
              <BannerTitle>{historyError}</BannerTitle>
              <InlineTag tone="warning">History</InlineTag>
              {onRetryMessages ? (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onRetryMessages()}
                  className="ml-auto"
                >
                  Retry
                </Button>
              ) : null}
              <BannerClose
                aria-label="Dismiss history error"
                onClick={() => {
                  onClearHistory?.();
                  onRetryMessages?.();
                }}
              />
            </Banner>
          ) : showEmpty ? (
            <div className="flex min-h-[360px] items-center justify-center py-4">
              <EmptyState
                variant="default"
                title="No messages yet"
                description="Compose a prompt below to brief your agent."
                className="max-w-lg text-foreground/80"
              />
            </div>
          ) : (
            <>
              {errorMessage ? (
                <Banner inset variant="muted" className="gap-3">
                  <BannerTitle>{errorMessage}</BannerTitle>
                  <InlineTag tone="warning">Chat</InlineTag>
                  <BannerClose
                    aria-label="Dismiss chat error"
                    onClick={() => {
                      onClearError?.();
                    }}
                  />
                </Banner>
              ) : null}
              {hasOlderMessages ? (
                <div className="flex justify-center pb-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={isLoadingOlderMessages}
                    onClick={() => {
                      void onLoadOlderMessages?.();
                    }}
                  >
                    {isLoadingOlderMessages ? 'Loading messages…' : 'Load earlier messages'}
                  </Button>
                </div>
              ) : null}

              <MessageList
                messages={messages}
                tools={tools}
                toolEventAnchors={toolEventAnchors}
                attachmentState={attachmentState}
                onResolveAttachment={resolveAttachment}
                isBusy={isBusy}
                onCopyMessage={onCopyMessage}
              />

              <ReasoningPanel reasoningText={reasoningText} isStreaming={isSending} />
            </>
          )}
        </ConversationContent>
        <ConversationScrollButton />
      </Conversation>

      <PromptComposer
        messageInput={messageInput}
        onChange={onMessageInputChange}
        onSubmit={onSubmit}
        onClearConversation={onClearConversation}
        isClearingConversation={isClearingConversation}
        isLoadingHistory={isLoadingHistory}
        isSending={isSending}
        chatStatus={chatStatus}
        lifecycleStatus={lifecycleStatus}
        activeAgent={activeAgent}
        currentConversationId={currentConversationId}
        shareLocation={shareLocation}
        onShareLocationChange={onShareLocationChange}
        locationHint={locationHint}
        onLocationHintChange={onLocationHintChange}
        memoryMode={memoryMode}
        memoryInjection={memoryInjection}
        onMemoryModeChange={onMemoryModeChange}
        onMemoryInjectionChange={onMemoryInjectionChange}
        isUpdatingMemory={isUpdatingMemory}
      />
    </div>
  );
}
