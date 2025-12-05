import { FormEvent } from 'react';
import type { ChatStatus } from 'ai';

import { GlassPanel, InlineTag, SectionHeader, type SectionHeaderProps } from '@/components/ui/foundation';
import { Banner, BannerClose, BannerTitle } from '@/components/ui/banner';
import { Conversation, ConversationContent, ConversationScrollButton } from '@/components/ui/ai/conversation';
import { EmptyState, SkeletonPanel } from '@/components/ui/states';
import { cn } from '@/lib/utils';

import { MessageList } from './MessageList';
import { ReasoningPanel } from './ReasoningPanel';
import { ToolEventsPanel } from './ToolEventsPanel';
import { PromptComposer } from './PromptComposer';
import type { ChatMessage, ConversationLifecycleStatus, ToolState } from '@/lib/chat/types';
import type { AttachmentState } from '../../hooks/useAttachmentResolver';

interface ChatSurfaceProps {
  className?: string;
  headerProps?: SectionHeaderProps;
  agentNotices: { id: string; text: string }[];
  isLoadingHistory: boolean;
  messages: ChatMessage[];
  reasoningText?: string;
  tools: ToolState[];
  chatStatus?: ChatStatus;
  lifecycleStatus?: ConversationLifecycleStatus;
  activeAgent?: string;
  isSending: boolean;
  isClearingConversation: boolean;
  currentConversationId: string | null;
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
}

export function ChatSurface({
  className,
  headerProps,
  agentNotices,
  isLoadingHistory,
  messages,
  reasoningText,
  tools,
  chatStatus,
  lifecycleStatus,
  activeAgent,
  isSending,
  isClearingConversation,
  currentConversationId,
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
}: ChatSurfaceProps) {
  const showEmpty = !isLoadingHistory && messages.length === 0;
  const isBusy = isSending || isLoadingHistory;

  return (
    <GlassPanel className={cn('flex h-full flex-col overflow-hidden p-0', className)}>
      {headerProps ? (
        <div className="border-b border-white/5 px-6 py-4">
          <SectionHeader {...headerProps} size="compact" />
        </div>
      ) : null}

      <Conversation className="flex-1">
        <ConversationContent className="space-y-4 px-6 py-6">
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
          ) : showEmpty ? (
            <div className="flex min-h-[360px] items-center justify-center py-4">
              <EmptyState
                variant="ghost"
                title="No messages yet"
                description="Compose a prompt below to brief your agent."
                className="max-w-lg text-foreground/80"
              />
            </div>
          ) : (
            <>
              <MessageList
                messages={messages}
                attachmentState={attachmentState}
                onResolveAttachment={resolveAttachment}
                isBusy={isBusy}
                onCopyMessage={onCopyMessage}
              />

              <ReasoningPanel reasoningText={reasoningText} isStreaming={isSending} />

              <ToolEventsPanel tools={tools} />
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
      />
    </GlassPanel>
  );
}
