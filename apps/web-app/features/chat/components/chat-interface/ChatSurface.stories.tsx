import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import type { ChatStatus } from 'ai';

import { ChatSurface } from './ChatSurface';
import type { ChatMessage, ToolState, ConversationLifecycleStatus } from '@/lib/chat/types';
import type { AttachmentState } from '../../hooks/useAttachmentResolver';
import type { MessageAttachment } from '@/lib/api/client/types.gen';

const baseHeader = {
  eyebrow: 'Workspace',
  title: 'Agent Chat',
  description: 'System glass UI demo surface',
};

const baseLocation = { city: 'San Francisco', region: 'CA', country: 'USA', timezone: 'America/Los_Angeles' } as const;
const onInputChange = (_value: string) => {};
const onToggle = (_value: boolean) => {};
const onLocationChange = (_field: 'city' | 'region' | 'country' | 'timezone', _value: string) => {};
const onSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
  event.preventDefault();
};

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

const meta: Meta<typeof ChatSurface> = {
  title: 'Chat/ChatSurface',
  component: ChatSurface,
  args: {
    className: 'max-w-5xl',
    headerProps: baseHeader,
    agentNotices: [],
    reasoningText: undefined,
    tools: [],
    chatStatus: undefined,
    lifecycleStatus: 'in_progress' as ConversationLifecycleStatus,
    activeAgent: 'gpt-5.1',
    isSending: false,
    isClearingConversation: false,
    isLoadingHistory: false,
    currentConversationId: 'conv-123',
    shareLocation: true,
    onShareLocationChange: onToggle,
    locationHint: baseLocation,
    onLocationHintChange: onLocationChange,
    onMessageInputChange: onInputChange,
    onSubmit,
    onCopyMessage: () => {},
    onClearConversation: () => {},
    attachmentState: {},
    resolveAttachment: async (_objectId: string) => {},
  },
};

export default meta;

type Story = StoryObj<typeof ChatSurface>;

export const Empty: Story = {
  args: {
    messages: [],
    tools: [],
    chatStatus: undefined as ChatStatus | undefined,
  },
};

export const Streaming: Story = {
  args: {
    messages: [
      ...defaultMessages,
      {
        id: 'm3',
        role: 'assistant',
        content: 'Streaming live response…',
        isStreaming: true,
      },
    ],
    tools: sampleTools,
    chatStatus: 'streaming' as ChatStatus,
    isSending: true,
    reasoningText: 'Thinking through the latest billing anomalies and validating figures.',
  },
};

export const AttachmentError: Story = {
  args: {
    messages: [
      {
        id: 'm4',
        role: 'assistant',
        content: 'Here is the attached report, but the link may not be ready yet.',
        attachments: sampleAttachments,
      },
    ],
    attachmentState: {
      'obj-1': { error: 'Link not ready', loading: false },
    } as AttachmentState,
    resolveAttachment: async (_objectId: string) => {},
    chatStatus: undefined,
    tools: [],
  },
};
