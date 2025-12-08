import type { Meta, StoryObj } from '@storybook/react';

import type { ConversationListItem } from '@/types/conversations';
import { DATE_GROUP_ORDER } from '../../utils/conversationGrouping';
import { ConversationSidebarView } from './ConversationSidebarView';

const baseConversations: ConversationListItem[] = [
  {
    id: 'conv-1',
    title: 'Pricing updates',
    last_message_preview: 'Can you summarize our billing deltas?',
    updated_at: '2025-12-05T09:00:00Z',
  },
  {
    id: 'conv-2',
    title: 'Incident retro',
    last_message_preview: 'Draft the postmortem outline',
    updated_at: '2025-12-04T18:30:00Z',
  },
];

const grouped: Record<typeof DATE_GROUP_ORDER[number], ConversationListItem[]> = {
  Today: [baseConversations[0]!],
  Yesterday: [baseConversations[1]!],
  'Previous 7 Days': [],
  'Previous 30 Days': [],
  Older: [],
};

const noop = () => {};

const meta: Meta<typeof ConversationSidebarView> = {
  title: 'Chat/ConversationSidebar',
  component: ConversationSidebarView,
  args: {
    variant: 'default',
    className: 'w-[340px] h-[520px]',
    tab: 'recent',
    onTabChange: noop,
    searchTerm: '',
    onSearchChange: noop,
    onClearSearch: noop,
    showTabs: false,
    groupedConversations: grouped,
    groupOrder: DATE_GROUP_ORDER,
    recentLoading: false,
    recentCount: baseConversations.length,
    searchResults: [],
    isSearching: false,
    showSearchEmpty: false,
    currentConversationId: 'conv-1',
    onSelectConversation: noop,
    onDeleteConversation: noop,
    onNewConversation: noop,
  },
};

export default meta;

type Story = StoryObj<typeof ConversationSidebarView>;

export const GroupedRecent: Story = {};

export const LoadingRecent: Story = {
  args: {
    recentLoading: true,
    recentCount: 0,
    groupedConversations: {
      Today: [],
      Yesterday: [],
      'Previous 7 Days': [],
      'Previous 30 Days': [],
      Older: [],
    },
  },
};

export const EmptyRecent: Story = {
  args: {
    recentLoading: false,
    recentCount: 0,
    groupedConversations: {
      Today: [],
      Yesterday: [],
      'Previous 7 Days': [],
      'Previous 30 Days': [],
      Older: [],
    },
  },
};

export const SearchEmpty: Story = {
  args: {
    tab: 'search',
    showTabs: true,
    searchTerm: 'billing',
    searchResults: [],
    isSearching: false,
    showSearchEmpty: true,
  },
};

export const SearchResults: Story = {
  args: {
    tab: 'search',
    showTabs: true,
    searchTerm: 'billing',
    searchResults: [
      {
        id: 'conv-3',
        title: 'Billing investigations',
        last_message_preview: 'Found 3 anomalies in October',
        updated_at: '2025-12-03T12:00:00Z',
      },
    ],
  },
};
