// File Path: features/chat/components/ChatInterface.tsx
// Description: Command-center chat interface aligned with the glass UI system.

'use client';

import React, { useEffect, useRef, useState, type FormEvent } from 'react';

import { Button } from '@/components/ui/button';
import { GlassPanel } from '@/components/ui/foundation';
import { EmptyState, SkeletonPanel } from '@/components/ui/states';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';
import { formatClockTime } from '@/lib/utils/time';
import type { ChatMessage } from '@/lib/chat/types';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  onSendMessage: (messageText: string) => Promise<void>;
  isSending: boolean;
  currentConversationId: string | null;
  onClearConversation?: () => void | Promise<void>;
  isClearingConversation?: boolean;
  isLoadingHistory?: boolean;
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
  className,
}: ChatInterfaceProps) {
  const [messageInput, setMessageInput] = useState('');
  const chatContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = chatContainerRef.current;
    if (!container) return;
    container.scrollTop = container.scrollHeight;
  }, [messages]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const value = messageInput.trim();
    if (!value || isSending || isLoadingHistory) return;
    setMessageInput('');
    await onSendMessage(value);
  };

  return (
    <GlassPanel className={cn('flex h-full flex-col overflow-hidden p-0', className)}>
      <div className="flex items-start justify-between border-b border-white/5 px-6 py-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-foreground/50">Conversation</p>
          <p className="text-lg font-semibold text-foreground">
            {currentConversationId ? `#${currentConversationId.substring(0, 12)}…` : 'New conversation'}
          </p>
          <p className="text-xs text-foreground/60">
            {isLoadingHistory
              ? 'Loading transcript…'
              : currentConversationId
                ? 'History synced from audit log.'
                : 'Send a message to start a new thread.'}
          </p>
        </div>
        {onClearConversation && currentConversationId ? (
          <Button
            variant="ghost"
            size="sm"
            className="border border-white/10"
            disabled={isClearingConversation || isLoadingHistory}
            onClick={() => {
              void onClearConversation();
            }}
          >
            {isClearingConversation ? 'Clearing…' : 'Clear chat'}
          </Button>
        ) : null}
      </div>

      <div ref={chatContainerRef} className="flex-1 space-y-4 overflow-y-auto px-6 py-6">
        {isLoadingHistory ? (
          <SkeletonPanel lines={8} />
        ) : messages.length === 0 ? (
          <EmptyState
            title="No messages yet"
            description="Compose a prompt below to brief your agent."
          />
        ) : (
          messages.map((message) => (
            <div key={message.id} className={cn('flex w-full', message.role === 'user' ? 'justify-end' : 'justify-start')}>
              <div
                className={cn(
                  'max-w-2xl rounded-2xl px-4 py-3 text-sm shadow-glass transition',
                  message.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-white/10 text-foreground'
                )}
              >
                <p>{message.content}</p>
                {message.timestamp && !message.isStreaming ? (
                  <p className="mt-2 text-[11px] uppercase tracking-wide text-foreground/50">
                    {formatClockTime(message.timestamp)}
                  </p>
                ) : null}
              </div>
            </div>
          ))
        )}
      </div>

      <form onSubmit={handleSubmit} className="border-t border-white/5 bg-white/5 px-6 py-4">
        <div className="flex flex-col gap-3 md:flex-row">
          <Textarea
            value={messageInput}
            onChange={(event) => setMessageInput(event.target.value)}
            placeholder={
              currentConversationId ? `Message ${currentConversationId.substring(0, 8)}…` : 'Ask your agent…'
            }
            disabled={isSending || isLoadingHistory}
            rows={2}
            className="flex-1 resize-none border-white/10 bg-transparent text-sm placeholder:text-foreground/40"
          />
          <Button
            type="submit"
            disabled={isSending || isLoadingHistory || !messageInput.trim()}
            className="md:min-w-[140px]"
          >
            {isSending ? 'Sending…' : 'Send'}
          </Button>
        </div>
      </form>
    </GlassPanel>
  );
}
