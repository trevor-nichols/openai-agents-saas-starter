// File Path: features/chat/components/ConversationSidebar.tsx
// Description: Glass-styled sidebar for managing conversations.

'use client';

import { Button } from '@/components/ui/button';
import { GlassPanel } from '@/components/ui/foundation';
import { EmptyState } from '@/components/ui/states';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import { formatRelativeTime } from '@/lib/utils/time';
import type { ConversationListItem } from '@/types/conversations';

interface ConversationSidebarProps {
  conversationList: ConversationListItem[];
  isLoadingConversations: boolean;
  currentConversationId: string | null;
  onSelectConversation: (conversationId: string) => void;
  onNewConversation: () => void;
  onDeleteConversation?: (conversationId: string) => void | Promise<void>;
  className?: string;
}

export function ConversationSidebar({
  conversationList,
  isLoadingConversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  className,
}: ConversationSidebarProps) {
  return (
    <GlassPanel className={cn('flex h-full w-full flex-col gap-4 p-5', className)}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-foreground/50">Conversations</p>
          <p className="text-sm text-foreground/70">Audit transcripts and jump back in.</p>
        </div>
        <Button size="sm" variant="ghost" className="border border-white/10" onClick={onNewConversation}>
          New
        </Button>
      </div>

      <ScrollArea className="flex-1 pr-2">
        {isLoadingConversations ? (
          <ul className="space-y-3">
            {Array.from({ length: 4 }).map((_, index) => (
              <li key={index} className="animate-pulse rounded-lg border border-white/5 bg-white/5 px-3 py-3">
                <div className="h-4 w-3/4 rounded-full bg-white/15" />
                <div className="mt-2 h-3 w-1/2 rounded-full bg-white/10" />
              </li>
            ))}
          </ul>
        ) : conversationList.length === 0 ? (
          <EmptyState
            title="No transcripts yet"
            description="Use the New control to start your first transcript."
          />
        ) : (
          <ul className="space-y-2">
            {conversationList.map((conversation) => (
              <li key={conversation.id}>
                <button
                  type="button"
                  onClick={() => onSelectConversation(conversation.id)}
                  className={cn(
                    'group flex w-full flex-col gap-1 rounded-lg border px-3 py-2 text-left transition duration-quick ease-apple',
                    currentConversationId === conversation.id
                      ? 'border-white/30 bg-white/15 text-foreground'
                      : 'border-white/5 bg-white/5 text-foreground/80 hover:border-white/15 hover:bg-white/10'
                  )}
                >
                  <div className="flex items-center justify-between gap-2 text-sm font-semibold">
                    <p className="truncate">
                      {conversation.title ?? `Conversation ${conversation.id.substring(0, 8)}…`}
                    </p>
                    <span className="text-xs text-foreground/50">{formatRelativeTime(conversation.updated_at)}</span>
                  </div>
                  {conversation.last_message_summary ? (
                    <p className="truncate text-xs text-foreground/60">{conversation.last_message_summary}</p>
                  ) : null}
                </button>
                {onDeleteConversation ? (
                  <div className="mt-1 flex justify-end">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-xs text-foreground/60"
                      onClick={(event) => {
                        event.stopPropagation();
                        void onDeleteConversation(conversation.id);
                      }}
                    >
                      Clear
                    </Button>
                  </div>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </ScrollArea>
    </GlassPanel>
  );
}
