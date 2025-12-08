import { RefObject, useRef } from 'react';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { GlassPanel } from '@/components/ui/foundation';
import { cn } from '@/lib/utils';

import type { ConversationListItem } from '@/types/conversations';
import type { DateGroup } from '../../utils/conversationGrouping';
import { ConversationSidebarHeader } from './ConversationSidebarHeader';
import {
  ConversationGroups,
  ConversationListEmpty,
  ConversationListLoader,
  ConversationListSkeleton,
  ConversationSearchEmpty,
  ConversationSearchResults,
} from './ConversationList';
import type { ConversationSidebarTab } from '../../hooks/useConversationSidebarState';

interface ConversationSidebarViewProps {
  variant: 'default' | 'embedded';
  className?: string;
  tab: ConversationSidebarTab;
  onTabChange: (tab: ConversationSidebarTab) => void;
  searchTerm: string;
  onSearchChange: (value: string) => void;
  onClearSearch: () => void;
  showTabs: boolean;
  groupedConversations: Record<DateGroup, ConversationListItem[]>;
  groupOrder: DateGroup[];
  recentLoading: boolean;
  recentCount: number;
  searchResults: ConversationListItem[];
  isSearching: boolean;
  showSearchEmpty: boolean;
  currentConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onDeleteConversation?: (id: string) => void;
  onNewConversation: () => void;
  infiniteScrollRef?: RefObject<HTMLDivElement | null>;
}

export function ConversationSidebarView({
  variant,
  className,
  tab,
  onTabChange,
  searchTerm,
  onSearchChange,
  onClearSearch,
  showTabs,
  groupedConversations,
  groupOrder,
  recentLoading,
  recentCount,
  searchResults,
  isSearching,
  showSearchEmpty,
  currentConversationId,
  onSelectConversation,
  onDeleteConversation,
  onNewConversation,
  infiniteScrollRef,
}: ConversationSidebarViewProps) {
  const fallbackRef = useRef<HTMLDivElement | null>(null);
  const sentinelRef = infiniteScrollRef ?? fallbackRef;

  const showLoader = (tab === 'recent' ? recentLoading : isSearching) && (recentCount > 0 || searchResults.length > 0);

  const content = (
    <>
      <ConversationSidebarHeader
        searchTerm={searchTerm}
        onSearchChange={onSearchChange}
        onNewConversation={onNewConversation}
      />

      <Tabs
        value={tab}
        onValueChange={(value) => onTabChange(value as ConversationSidebarTab)}
        className="flex flex-1 flex-col overflow-hidden"
      >
        {showTabs && (
          <div className="px-4 pb-2">
            <TabsList className="grid h-8 w-full grid-cols-2 bg-muted/30 p-0.5">
              <TabsTrigger value="recent" className="h-7 text-xs">
                Recent
              </TabsTrigger>
              <TabsTrigger value="search" className="h-7 text-xs">
                Results
              </TabsTrigger>
            </TabsList>
          </div>
        )}

        <ScrollArea className="flex-1">
          <div className="flex w-full min-w-0 max-w-full flex-col py-2">
            {tab === 'recent' ? (
              recentLoading && recentCount === 0 ? (
                <ConversationListSkeleton />
              ) : recentCount === 0 ? (
                <ConversationListEmpty onNewConversation={onNewConversation} />
              ) : (
                <ConversationGroups
                  groupedConversations={groupedConversations}
                  groupOrder={groupOrder}
                  currentConversationId={currentConversationId}
                  onSelectConversation={onSelectConversation}
                  onDeleteConversation={onDeleteConversation}
                />
              )
            ) : isSearching && searchResults.length === 0 ? (
              <ConversationListSkeleton />
            ) : showSearchEmpty ? (
              <ConversationSearchEmpty onClear={onClearSearch} />
            ) : searchResults.length === 0 ? (
              <ConversationListEmpty onNewConversation={onNewConversation} />
            ) : (
              <ConversationSearchResults
                items={searchResults}
                currentConversationId={currentConversationId}
                onSelectConversation={onSelectConversation}
                onDeleteConversation={onDeleteConversation}
              />
            )}

            <div ref={sentinelRef}>
              {showLoader ? <ConversationListLoader /> : null}
            </div>
          </div>
        </ScrollArea>
      </Tabs>
    </>
  );

  if (variant === 'embedded') {
    return <div className={cn('flex h-full w-full flex-col overflow-hidden', className)}>{content}</div>;
  }

  return (
    <GlassPanel className={cn('flex h-full w-full flex-col overflow-hidden border-r bg-background/40 backdrop-blur-xl', className)}>
      {content}
    </GlassPanel>
  );
}
