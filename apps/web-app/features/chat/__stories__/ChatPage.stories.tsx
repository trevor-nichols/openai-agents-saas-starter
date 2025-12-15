'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { ChatSurface } from '../components/chat-interface/ChatSurface';
import { AgentSwitcher } from '../components/AgentSwitcher';
import { BillingEventsPanel } from '../components/BillingEventsPanel';
import { ToolMetadataPanel } from '../components/ToolMetadataPanel';
import { ConversationSidebarView } from '../components/conversation-sidebar/ConversationSidebarView';
import type { ChatMessage, ToolState, ConversationLifecycleStatus } from '@/lib/chat/types';
import type { MessageAttachment } from '@/lib/api/client/types.gen';
import type { AgentSummary } from '@/types/agents';
import type { BillingEvent, BillingStreamStatus } from '@/types/billing';
import type { ToolRegistry } from '@/types/tools';
import type { ConversationListItem } from '@/types/conversations';
import { DATE_GROUP_ORDER } from '../utils/conversationGrouping';

const baseHeader = {
  eyebrow: 'Workspace',
  title: 'Agent Chat',
  description: 'System glass UI demo surface',
};

const baseLocation = { city: 'San Francisco', region: 'CA', country: 'USA', timezone: 'America/Los_Angeles' } as const;

const sampleAgents: AgentSummary[] = [
  {
    name: 'triage_agent',
    description: 'Routes requests and summarizes context.',
    status: 'active',
    display_name: 'Triage Agent',
    model: 'gpt-5.1',
  },
  {
    name: 'research_agent',
    description: 'Deep dives across docs and web.',
    status: 'active',
    display_name: 'Research Agent',
    model: 'gpt-5.1',
  },
];

const sampleAttachments: MessageAttachment[] = [
  {
    object_id: 'obj-1',
    filename: 'report.pdf',
    mime_type: 'application/pdf',
    size_bytes: 1_024_000,
  },
];

const sampleTools: ToolState[] = [
  {
    id: 'tool-1',
    name: 'file_search',
    status: 'output-available',
    output: [
      {
        file_id: 'file-123',
        filename: 'summary.txt',
        score: 0.88,
        vector_store_id: 'vs-1',
        text: 'Sample chunk of retrieved text',
      },
    ],
  },
];

const defaultMessages: ChatMessage[] = [
  {
    id: 'm1',
    role: 'user',
    content: 'Summarize the latest billing events.',
    timestamp: new Date().toISOString(),
  },
  {
    id: 'm2',
    role: 'assistant',
    content: 'I found 3 recent billing events. Want the full ledger?',
    timestamp: new Date().toISOString(),
  },
];

const billingEvents: BillingEvent[] = [
  {
    stripe_event_id: 'evt_1',
    event_type: 'invoice.created',
    occurred_at: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
    invoice: {
      invoice_id: 'inv_123',
      amount_due_cents: 4200,
      currency: 'USD',
      hosted_invoice_url: 'https://stripe.example/inv_123',
    },
    summary: 'Invoice created',
  } as BillingEvent,
];

const toolRegistry: ToolRegistry = {
  total_tools: 4,
  categories: ['search', 'code_interpreter'],
  tool_names: ['file_search', 'web_search', 'code_interpreter', 'browser'],
};

const conversations: ConversationListItem[] = [
  {
    id: 'conv-1',
    title: 'Pricing updates',
    last_message_preview: 'Can you summarize our billing deltas?',
    updated_at: new Date().toISOString(),
  },
  {
    id: 'conv-2',
    title: 'Incident retro',
    last_message_preview: 'Draft the postmortem outline',
    updated_at: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
  },
];

const groupedConversations: Record<(typeof DATE_GROUP_ORDER)[number], ConversationListItem[]> = {
  Today: [conversations[0]!],
  Yesterday: [conversations[1]!],
  'Previous 7 Days': [],
  'Previous 30 Days': [],
  Older: [],
};

type PageProps = {
  status: ConversationLifecycleStatus;
  streamStatus?: ChatMessage['isStreaming'];
  billingStatus?: BillingStreamStatus;
  includeAttachments?: boolean;
};

function ChatPage({ status, streamStatus, billingStatus = 'open', includeAttachments = false }: PageProps) {
  const messages =
    status === 'completed'
      ? defaultMessages
      : [
          ...defaultMessages,
          {
            id: 'm3',
            role: 'assistant',
            content: 'Streaming live response…',
            isStreaming: streamStatus ?? true,
            attachments: includeAttachments ? sampleAttachments : undefined,
          } as ChatMessage,
        ];

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
      <ChatSurface
        className="w-full"
        headerProps={baseHeader}
        messages={messages}
        reasoningText="Thinking through the latest billing anomalies and validating figures."
        tools={sampleTools}
        chatStatus={streamStatus ? 'streaming' : undefined}
        lifecycleStatus={status}
        activeAgent="gpt-5.1"
        isSending={streamStatus ?? false}
        isClearingConversation={false}
        isLoadingHistory={false}
        currentConversationId="conv-1"
        hasOlderMessages={false}
        isLoadingOlderMessages={false}
        onLoadOlderMessages={() => {}}
        onRetryMessages={() => {}}
        historyError={null}
        errorMessage={null}
        shareLocation
        onShareLocationChange={() => {}}
        locationHint={baseLocation}
        onLocationHintChange={() => {}}
        guardrailEvents={[]}
        onMessageInputChange={(value: string) => {
          console.log('input change', value);
        }}
        onSubmit={(e) => e.preventDefault()}
        onCopyMessage={() => {}}
        onClearConversation={() => {}}
        attachmentState={{}}
        resolveAttachment={async () => {}}
        messageInput=""
        memoryMode="inherit"
        memoryInjection={false}
        onMemoryModeChange={() => {}}
        onMemoryInjectionChange={() => {}}
        isUpdatingMemory={false}
        agentNotices={[]}
        onClearHistory={() => {}}
        onClearError={() => {}}
      />

      <div className="space-y-4">
        <AgentSwitcher
          agents={sampleAgents}
          selectedAgent={sampleAgents[0]?.name ?? 'triage_agent'}
          onChange={(name) => console.log('agent change', name)}
          isLoading={false}
          hasConversation
          onShowInsights={() => console.log('open insights')}
          onShowDetails={() => console.log('open details')}
        />

        <ConversationSidebarView
          variant="default"
          className="w-full h-[360px]"
          tab="recent"
          onTabChange={() => {}}
          searchTerm=""
          onSearchChange={() => {}}
          onClearSearch={() => {}}
          showTabs={false}
          groupedConversations={groupedConversations}
          groupOrder={DATE_GROUP_ORDER}
          recentLoading={false}
          recentFetchingMore={false}
          recentCount={conversations.length}
          searchResults={[]}
          isSearching={false}
          isFetchingMoreSearchResults={false}
          showSearchEmpty={false}
          currentConversationId="conv-1"
          onSelectConversation={() => {}}
          onDeleteConversation={() => {}}
          onNewConversation={() => {}}
        />

        <BillingEventsPanel events={billingEvents} status={billingStatus} />

        <ToolMetadataPanel
          selectedAgent="triage_agent"
          tools={toolRegistry}
          isLoading={false}
          error={null}
          onRefresh={() => console.log('refresh tools')}
        />
      </div>
    </div>
  );
}

const meta: Meta<typeof ChatPage> = {
  title: 'Chat/Page',
  component: ChatPage,
};

export default meta;

type Story = StoryObj<typeof ChatPage>;

export const Streaming: Story = {
  args: {
    status: 'in_progress',
    streamStatus: true,
    billingStatus: 'open',
  },
};

export const Completed: Story = {
  args: {
    status: 'completed',
    streamStatus: false,
    billingStatus: 'open',
    includeAttachments: true,
  },
};

export const ErrorBilling: Story = {
  args: {
    status: 'in_progress',
    streamStatus: false,
    billingStatus: 'error',
  },
};
