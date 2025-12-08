import type { Meta, StoryObj } from '@storybook/react';

import { ToolEventsPanel } from '../components/chat-interface/ToolEventsPanel';
import type { ToolState } from '@/lib/chat/types';

const tools: ToolState[] = [
  {
    id: 'tool-1',
    name: 'web_search',
    status: 'input-available',
    input: { query: 'latest billing updates' },
  },
  {
    id: 'tool-2',
    name: 'file_search',
    status: 'output-available',
    input: ['ledger', 'invoice'],
    output: [
      {
        file_id: 'file-1',
        filename: 'ledger.csv',
        score: 0.91,
        vector_store_id: 'vs-1',
      },
    ],
  },
];

const meta: Meta<typeof ToolEventsPanel> = {
  title: 'Chat/ToolEventsPanel',
  component: ToolEventsPanel,
  args: {
    tools,
  },
};

export default meta;

type Story = StoryObj<typeof ToolEventsPanel>;

export const Default: Story = {};

export const Empty: Story = {
  args: {
    tools: [],
  },
};
