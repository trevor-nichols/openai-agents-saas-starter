import { Loader2, MessageSquare, MoreVertical, Pencil, Trash2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import type { ConversationListItem } from '@/types/conversations';
import { cn } from '@/lib/utils';
import { formatConversationFallbackTitle } from '../../utils/formatters';

import type { DateGroup } from '../../utils/conversationGrouping';

interface ConversationItemProps {
  conversation: ConversationListItem;
  isActive: boolean;
  onSelect: () => void;
  onDelete?: () => void;
  onRename?: () => void;
}

export function ConversationItem({ conversation, isActive, onSelect, onDelete, onRename }: ConversationItemProps) {
  const title =
    conversation.title?.trim() ||
    conversation.topic_hint?.trim() ||
    formatConversationFallbackTitle(conversation.updated_at ?? conversation.created_at);
  const hasActions = Boolean(onDelete || onRename);

  return (
    <li className="group relative w-full min-w-0">
      <button
        type="button"
        onClick={onSelect}
        className={cn(
          'grid w-full grid-cols-1 gap-0.5 rounded-lg px-3 py-2.5 text-left transition-all duration-200',
          isActive ? 'bg-muted font-medium text-foreground' : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground',
        )}
      >
        <span className="block truncate text-sm leading-tight">{title}</span>
        <span className="block truncate text-xs font-normal text-muted-foreground/60">
          {conversation.last_message_preview || 'No messages'}
        </span>
      </button>

      {hasActions && (
        <div
          className={cn(
            'absolute right-1 top-1/2 -translate-y-1/2 opacity-0 transition-opacity duration-200 group-hover:opacity-100',
            isActive && 'opacity-100',
          )}
        >
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 rounded-md hover:bg-background/80"
                onClick={(e) => e.stopPropagation()}
              >
                <MoreVertical className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="sr-only">Options</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {onRename && (
                <DropdownMenuItem
                  onClick={(e) => {
                    e.stopPropagation();
                    onRename();
                  }}
                >
                  <Pencil className="mr-2 h-4 w-4" />
                  Rename
                </DropdownMenuItem>
              )}
              {onDelete && (
                <DropdownMenuItem
                  className="text-destructive focus:text-destructive"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete();
                  }}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      )}
    </li>
  );
}

export function ConversationListSkeleton() {
  return (
    <div className="space-y-4 px-2 pt-2">
      {Array.from({ length: 5 }).map((_, index) => (
        <div key={index} className="flex flex-col gap-2">
          <div className="h-4 w-3/4 animate-pulse rounded bg-muted/20" />
          <div className="h-3 w-1/2 animate-pulse rounded bg-muted/10" />
        </div>
      ))}
    </div>
  );
}

export function ConversationListEmpty({ onNewConversation }: { onNewConversation: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center px-4 py-10 text-center text-muted-foreground">
      <MessageSquare className="mb-2 h-8 w-8 opacity-20" />
      <p className="text-sm">No conversations</p>
      <Button variant="link" size="sm" onClick={onNewConversation} className="mt-2 h-auto p-0 text-xs">
        Start a new chat
      </Button>
    </div>
  );
}

export function ConversationSearchEmpty({ onClear }: { onClear: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center px-4 py-10 text-center text-muted-foreground">
      <p className="text-sm">No matches found.</p>
      <Button variant="link" size="sm" onClick={onClear} className="mt-2 h-auto p-0 text-xs">
        Clear search
      </Button>
    </div>
  );
}

interface ConversationGroupsProps {
  groupedConversations: Record<DateGroup, ConversationListItem[]>;
  groupOrder: DateGroup[];
  currentConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onDeleteConversation?: (id: string) => void;
  onRenameConversation?: (conversation: ConversationListItem) => void;
}

export function ConversationGroups({
  groupedConversations,
  groupOrder,
  currentConversationId,
  onSelectConversation,
  onDeleteConversation,
  onRenameConversation,
}: ConversationGroupsProps) {
  return (
    <div className="space-y-6 px-2">
      {groupOrder.map((group) => {
        const groupItems = groupedConversations[group];
        if (!groupItems?.length) return null;

        return (
          <div key={group}>
            <h3 className="mb-2 px-2 text-[10px] font-medium uppercase tracking-wider text-muted-foreground/50">{group}</h3>
            <ul className="space-y-0.5">
              {groupItems.map((conv) => (
                <ConversationItem
                  key={conv.id}
                  conversation={conv}
                  isActive={currentConversationId === conv.id}
                  onSelect={() => onSelectConversation(conv.id)}
                  onDelete={onDeleteConversation ? () => onDeleteConversation(conv.id) : undefined}
                  onRename={onRenameConversation ? () => onRenameConversation(conv) : undefined}
                />
              ))}
            </ul>
          </div>
        );
      })}
    </div>
  );
}

interface ConversationSearchResultsProps {
  items: ConversationListItem[];
  currentConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onDeleteConversation?: (id: string) => void;
  onRenameConversation?: (conversation: ConversationListItem) => void;
}

export function ConversationSearchResults({ items, currentConversationId, onSelectConversation, onDeleteConversation, onRenameConversation }: ConversationSearchResultsProps) {
  return (
    <ul className="space-y-1 px-2">
      {items.map((conv) => (
        <ConversationItem
          key={conv.id}
          conversation={conv}
          isActive={currentConversationId === conv.id}
          onSelect={() => onSelectConversation(conv.id)}
          onDelete={onDeleteConversation ? () => onDeleteConversation(conv.id) : undefined}
          onRename={onRenameConversation ? () => onRenameConversation(conv) : undefined}
        />
      ))}
    </ul>
  );
}

export function ConversationListLoader() {
  return (
    <div className="flex justify-center py-4">
      <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
    </div>
  );
}
