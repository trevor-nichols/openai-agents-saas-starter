// File Path: features/chat/components/ChatInterface.tsx
// Description: Command-center chat interface aligned with the glass UI system.

'use client';

import { useMemo, useState, useCallback, type FormEvent } from 'react';
import type { ChatStatus } from 'ai';

import { GlassPanel, InlineTag, SectionHeader, type SectionHeaderProps } from '@/components/ui/foundation';
import { EmptyState, SkeletonPanel } from '@/components/ui/states';
import { cn } from '@/lib/utils';
import { formatClockTime } from '@/lib/utils/time';
import { Banner, BannerClose, BannerTitle } from '@/components/ui/banner';
import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from '@/components/ui/ai/conversation';
import { Actions, Action } from '@/components/ui/ai/actions';
import { Loader } from '@/components/ui/ai/loader';
import { Message, MessageAvatar, MessageContent } from '@/components/ui/ai/message';
import { Response } from '@/components/ui/ai/response';
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
import { FileSearchResults } from '@/components/ui/ai/file-search-results';
import { Image } from '@/components/ui/ai/image';
import type { ToolUIPart } from 'ai';
import { CodeBlock } from '@/components/ui/ai/code-block';
import { LocationOptIn } from '@/components/ui/location';
import { getAttachmentDownloadUrl } from '@/lib/api/storage';
import { createLogger } from '@/lib/logging';
import { useToast } from '@/components/ui/use-toast';
import {
  useChatMessages,
  useChatToolEvents,
  useChatAgentNotices,
  useChatLifecycle,
  useChatSelector,
} from '@/lib/chat';
import type { ChatMessage, ToolState, ConversationLifecycleStatus } from '@/lib/chat/types';
import { CopyIcon } from 'lucide-react';
import type { FileSearchResult, ImageGenerationCall } from '@/lib/api/client/types.gen';

const log = createLogger('chat-ui');

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

  const messages = messagesProp ?? messagesFromStore;
  const toolEvents = toolsProp ?? toolEventsFromStore;
  const agentNotices = agentNoticesProp ?? agentNoticesFromStore;
  const lifecycleStatus = lifecycleStatusProp ?? lifecycleFromStore;
  const activeAgent = activeAgentProp ?? activeAgentFromStore;
  const reasoningText = reasoningTextProp ?? reasoningFromStore;
  const isSending = isSendingProp ?? isSendingFromStore;
  const isClearingConversation = isClearingConversationProp ?? isClearingFromStore;
  const isLoadingHistory = isLoadingHistoryProp ?? isLoadingHistoryFromStore;
  const [messageInput, setMessageInput] = useState('');
  const [attachmentState, setAttachmentState] = useState<
    Record<string, { url?: string; error?: string; loading?: boolean }>
  >({});
  const { error: showErrorToast, success: showSuccessToast } = useToast();
  const formatAttachmentSize = (size?: number | null) => {
    if (!size || size <= 0) return '';
    if (size < 1024) return `${size} B`;
    const kb = size / 1024;
    if (kb < 1024) return `${kb.toFixed(1)} KB`;
    return `${(kb / 1024).toFixed(1)} MB`;
  };

  const formatStructuredOutput = (value: unknown) => {
    try {
      return JSON.stringify(value, null, 2);
    } catch {
      return String(value);
    }
  };

  const resolveAttachment = async (objectId: string) => {
    setAttachmentState((prev) => ({
      ...prev,
      [objectId]: { ...prev[objectId], loading: true, error: undefined },
    }));
    try {
      const presign = await getAttachmentDownloadUrl(objectId);
      setAttachmentState((prev) => ({
        ...prev,
        [objectId]: { ...prev[objectId], url: presign.download_url, loading: false },
      }));
      log.debug('Resolved attachment download', { objectId });
    } catch (error) {
      setAttachmentState((prev) => ({
        ...prev,
        [objectId]: {
          ...prev[objectId],
          loading: false,
          error: error instanceof Error ? error.message : 'Unable to fetch link',
        },
      }));
      log.debug('Attachment download failed', { objectId, error });
      showErrorToast({
        title: 'Attachment link unavailable',
        description:
          error instanceof Error ? error.message : 'Could not fetch a download link. Please try again.',
      });
    }
  };

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
    <GlassPanel className={cn('flex h-full flex-col overflow-hidden p-0', className)}>
      {headerProps && (
        <div className="border-b border-white/5 px-6 py-4">
          <SectionHeader {...headerProps} size="compact" />
        </div>
      )}
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
          ) : messages.length === 0 ? (
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
              {messages.map((message) => (
                <Message key={message.id} from={message.role}>
                  <MessageContent>
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2">
                        <InlineTag tone={message.role === 'user' ? 'positive' : 'default'}>
                          {message.role === 'user' ? 'You' : 'Agent'}
                        </InlineTag>
                        {message.isStreaming ? (
                          <div className="flex items-center gap-1 text-muted-foreground">
                            <Loader size={14} />
                            <span className="text-[11px] uppercase tracking-wide">Streaming</span>
                          </div>
                        ) : message.timestamp ? (
                          <span className="text-[11px] uppercase tracking-wide text-foreground/50">
                            {formatClockTime(message.timestamp)}
                          </span>
                        ) : (
                          <span className="text-[11px] uppercase tracking-wide text-foreground/40">
                            Pending
                          </span>
                        )}
                      </div>
                      <Actions>
                        <Action
                          tooltip="Copy message"
                          label="Copy message"
                          onClick={() => void handleCopyMessage(message.content)}
                        >
                          <CopyIcon size={14} />
                        </Action>
                      </Actions>
                    </div>
                    <Response
                      className="mt-2 leading-relaxed"
                      citations={message.citations ?? undefined}
                    >
                      {message.content}
                    </Response>
                    {message.structuredOutput ? (
                      <div className="mt-3 space-y-2">
                        <p className="text-xs font-semibold uppercase tracking-wide text-foreground/60">
                          Structured output
                        </p>
                        <CodeBlock
                          code={formatStructuredOutput(message.structuredOutput)}
                          language="json"
                        />
                      </div>
                    ) : null}
                    {message.attachments && message.attachments.length > 0 ? (
                      <div className="mt-3 space-y-2">
                        <p className="text-xs font-semibold uppercase tracking-wide text-foreground/60">
                          Attachments
                        </p>
                        <div className="space-y-2">
                          {message.attachments.map((attachment) => (
                            <div
                              key={attachment.object_id}
                              className="flex items-center justify-between gap-3 rounded-md border border-white/5 bg-white/5 px-3 py-2 text-xs"
                            >
                              <div className="flex flex-col">
                                <span className="font-medium text-foreground">{attachment.filename}</span>
                                <span className="text-foreground/60">
                                  {attachment.mime_type ?? 'file'}
                                  {attachment.size_bytes ? ` • ${formatAttachmentSize(attachment.size_bytes)}` : ''}
                                </span>
                              </div>
                              {(() => {
                                const state = attachmentState[attachment.object_id];
                                const effectiveUrl = attachment.url ?? state?.url;
                                if (effectiveUrl) {
                                  return (
                                    <a
                                      className="text-primary font-semibold hover:underline"
                                      href={effectiveUrl}
                                      target="_blank"
                                      rel="noreferrer"
                                    >
                                      Download
                                    </a>
                                  );
                                }

                                if (state?.loading) {
                                  return <span className="text-foreground/50">Fetching link…</span>;
                                }

                                return (
                                  <div className="flex flex-col items-end gap-1">
                                    <button
                                      type="button"
                                      className="text-primary font-semibold hover:underline disabled:text-foreground/40"
                                      onClick={() => void resolveAttachment(attachment.object_id)}
                                      disabled={isSending || isLoadingHistory}
                                    >
                                      Get link
                                    </button>
                                    {state?.error ? (
                                      <span className="text-[11px] text-destructive">{state.error}</span>
                                    ) : (
                                      <span className="text-foreground/50">Link not ready</span>
                                    )}
                                  </div>
                                );
                              })()}
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : null}
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

              {toolEvents.length > 0 ? (
                <div className="space-y-3">
                  {toolEvents.map((tool) => (
                    <Tool key={tool.id} defaultOpen={tool.status !== 'output-available'}>
                      <ToolHeader
                        type={`tool-${tool.name || 'call'}` as ToolUIPart['type']}
                        state={tool.status}
                      />
                      <ToolContent>
                        {tool.input ? <ToolInput input={tool.input} /> : null}
                        <ToolOutput
                          output={renderToolOutput(tool)}
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

      <PromptInput onSubmit={handleSubmit} className="border-t border-white/5 bg-white/5 rounded-none border-x-0 border-b-0">
        <PromptInputTextarea
          value={messageInput}
          onChange={(event) => setMessageInput(event.target.value)}
          placeholder={currentConversationId ? `Message ${currentConversationId.substring(0, 8)}…` : 'Ask your agent…'}
          disabled={isSending || isLoadingHistory}
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
              disabled={isSending || isLoadingHistory}
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

type ToolLike = {
  name?: string | null;
  output?: unknown;
};

const isFileSearchResults = (output: unknown): output is FileSearchResult[] =>
  Array.isArray(output) &&
  output.every(
    (item) =>
      typeof item === 'object' &&
      item !== null &&
      'file_id' in (item as Record<string, unknown>),
  );

const isImageGenerationCall = (value: unknown): value is ImageGenerationCall =>
  typeof value === 'object' &&
  value !== null &&
  'type' in value &&
  (value as { type?: string }).type === 'image_generation_call';

export const renderToolOutput = (tool: ToolLike) => {
  if (!tool.output) return undefined;

  if (isFileSearchResults(tool.output)) {
    return <FileSearchResults results={tool.output} />;
  }

  if (Array.isArray(tool.output) && tool.output.length && isImageGenerationCall(tool.output[0])) {
    return <Image frames={tool.output as ImageGenerationCall[]} className="max-w-xl" alt="Generated image" />;
  }

  if (isImageGenerationCall(tool.output)) {
    return <Image frames={[tool.output]} className="max-w-xl" alt="Generated image" />;
  }

  return <CodeBlock code={JSON.stringify(tool.output, null, 2)} language="json" />;
};
