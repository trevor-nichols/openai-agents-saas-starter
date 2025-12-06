// File Path: features/chat/components/ChatInterface.tsx
// Description: Chat interface container that wires store state into a modular surface.

'use client';

import { useCallback, useMemo, useState, type FormEvent } from 'react';
import type { ChatStatus } from 'ai';
import type { SectionHeaderProps } from '@/components/ui/foundation';

import { useToast } from '@/components/ui/use-toast';
import {
  useChatAgentNotices,
  useChatLifecycle,
  useChatMessages,
  useChatSelector,
  useChatToolEvents,
} from '@/lib/chat';
import type { ChatMessage, ConversationLifecycleStatus, ToolState } from '@/lib/chat/types';

import { ChatSurface } from './chat-interface/ChatSurface';
import { useAttachmentResolver } from '../hooks/useAttachmentResolver';

interface ChatInterfaceProps {
  onSendMessage: (messageText: string) => Promise<void>;
  currentConversationId: string | null;
  onClearConversation?: () => void | Promise<void>;
  messages?: ChatMessage[];
  tools?: ToolState[];
  agentNotices?: { id: string; text: string }[];
  reasoningText?: string;
  activeAgent?: string;
  lifecycleStatus?: ConversationLifecycleStatus;
  isSending?: boolean;
  isClearingConversation?: boolean;
  isLoadingHistory?: boolean;
  hasOlderMessages?: boolean;
  isLoadingOlderMessages?: boolean;
  onLoadOlderMessages?: () => void | Promise<void>;
  onRetryMessages?: () => void;
  historyError?: string | null;
  errorMessage?: string | null;
  onClearError?: () => void;
  onClearHistory?: () => void;
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
  headerProps?: SectionHeaderProps;
}

export function ChatInterface({
  onSendMessage,
  currentConversationId,
  onClearConversation,
  messages: messagesProp,
  tools: toolsProp,
  agentNotices: agentNoticesProp,
  reasoningText: reasoningTextProp,
  activeAgent: activeAgentProp,
  lifecycleStatus: lifecycleStatusProp,
  isSending: isSendingProp,
  isClearingConversation: isClearingConversationProp,
  isLoadingHistory: isLoadingHistoryProp,
  hasOlderMessages: hasOlderMessagesProp,
  isLoadingOlderMessages: isLoadingOlderMessagesProp,
  onLoadOlderMessages,
  onRetryMessages,
  historyError,
  errorMessage,
  onClearError,
  onClearHistory,
  shareLocation,
  onShareLocationChange,
  locationHint,
  onLocationHintChange,
  className,
  headerProps,
}: ChatInterfaceProps) {
  const messagesFromStore = useChatMessages();
  const toolEventsFromStore = useChatToolEvents();
  const agentNoticesFromStore = useChatAgentNotices();
  const lifecycleFromStore = useChatLifecycle();
  const activeAgentFromStore = useChatSelector((s) => s.activeAgent);
  const reasoningFromStore = useChatSelector((s) => s.reasoningText);
  const isSendingFromStore = useChatSelector((s) => s.isSending);
  const isClearingFromStore = useChatSelector((s) => s.isClearingConversation);
  const isLoadingHistoryFromStore = useChatSelector((s) => s.isLoadingHistory);
  const hasOlderMessagesFromStore = useChatSelector((s) => s.hasOlderMessages);
  const isLoadingOlderMessagesFromStore = useChatSelector((s) => s.isFetchingOlderMessages);

  const messages = messagesProp ?? messagesFromStore;
  const toolEvents = toolsProp ?? toolEventsFromStore;
  const agentNotices = agentNoticesProp ?? agentNoticesFromStore;
  const lifecycleStatus = lifecycleStatusProp ?? lifecycleFromStore;
  const activeAgent = activeAgentProp ?? activeAgentFromStore;
  const reasoningText = reasoningTextProp ?? reasoningFromStore;
  const isSending = isSendingProp ?? isSendingFromStore;
  const isClearingConversation = isClearingConversationProp ?? isClearingFromStore;
  const isLoadingHistory = isLoadingHistoryProp ?? isLoadingHistoryFromStore;
  const hasOlderMessages = hasOlderMessagesProp ?? hasOlderMessagesFromStore;
  const isLoadingOlderMessages = isLoadingOlderMessagesProp ?? isLoadingOlderMessagesFromStore;
  const historyErrorFromStore = useChatSelector((s) => s.historyError);
  const errorMessageFromStore = useChatSelector((s) => s.errorMessage);
  const loadOlderMessagesFromStore = useChatSelector((s) => s.loadOlderMessages);
  const retryMessagesFromStore = useChatSelector((s) => s.retryMessages);
  const clearHistoryErrorFromStore = useChatSelector((s) => s.clearHistoryError);
  const resolvedHistoryError = historyError ?? historyErrorFromStore ?? null;
  const resolvedErrorMessage = errorMessage ?? errorMessageFromStore ?? null;
  const resolvedLoadOlderMessages = onLoadOlderMessages ?? loadOlderMessagesFromStore;
  const resolvedRetryMessages = onRetryMessages ?? retryMessagesFromStore;
  const resolvedClearHistory = onClearHistory ?? clearHistoryErrorFromStore;

  const [messageInput, setMessageInput] = useState('');
  const { attachmentState, resolveAttachment } = useAttachmentResolver();
  const { error: showErrorToast, success: showSuccessToast } = useToast();

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

  const handleCopyMessage = useCallback(
    async (text: string) => {
      if (typeof navigator === 'undefined' || !navigator.clipboard?.writeText) {
        showErrorToast({
          title: 'Copy unavailable',
          description: 'Clipboard access is not supported in this environment.',
        });
        return;
      }
      try {
        await navigator.clipboard.writeText(text);
        showSuccessToast({ title: 'Copied to clipboard' });
      } catch (error) {
        showErrorToast({
          title: 'Copy failed',
          description: error instanceof Error ? error.message : 'Unable to copy message.',
        });
      }
    },
    [showErrorToast, showSuccessToast],
  );

  return (
    <ChatSurface
      className={className}
      headerProps={headerProps}
      agentNotices={agentNotices}
      isLoadingHistory={isLoadingHistory}
      messages={messages}
      reasoningText={reasoningText}
      tools={toolEvents}
      chatStatus={chatStatus}
      lifecycleStatus={lifecycleStatus}
      activeAgent={activeAgent}
      isSending={isSending}
      isClearingConversation={isClearingConversation}
      historyError={resolvedHistoryError}
      errorMessage={resolvedErrorMessage}
      onClearError={onClearError}
      onClearHistory={resolvedClearHistory}
      currentConversationId={currentConversationId}
      hasOlderMessages={hasOlderMessages}
      isLoadingOlderMessages={isLoadingOlderMessages}
      onLoadOlderMessages={resolvedLoadOlderMessages}
      onRetryMessages={resolvedRetryMessages}
      messageInput={messageInput}
      onMessageInputChange={setMessageInput}
      onSubmit={handleSubmit}
      onCopyMessage={handleCopyMessage}
      onClearConversation={onClearConversation}
      attachmentState={attachmentState}
      resolveAttachment={resolveAttachment}
      shareLocation={shareLocation}
      onShareLocationChange={onShareLocationChange}
      locationHint={locationHint}
      onLocationHintChange={onLocationHintChange}
    />
  );
}
