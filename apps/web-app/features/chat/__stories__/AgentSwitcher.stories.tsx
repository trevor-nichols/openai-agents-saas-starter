import type { Meta, StoryObj } from '@storybook/react';

import { AgentSwitcher } from '../components/AgentSwitcher';
import type { AgentSummary } from '@/types/agents';

const agents: AgentSummary[] = [
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
  {
    name: 'billing_agent',
    description: 'Understands invoices and ledger changes.',
    status: 'inactive',
    display_name: 'Billing Agent',
    model: 'gpt-4.1',
  },
];

const meta: Meta<typeof AgentSwitcher> = {
  title: 'Chat/AgentSwitcher',
  component: AgentSwitcher,
  args: {
    agents,
    selectedAgent: agents[0]?.name ?? 'triage_agent',
    onChange: (name: string) => console.log('agent change', name),
    isLoading: false,
    hasConversation: true,
    onShowDetails: () => console.log('open details'),
    onShowInsights: () => console.log('open insights'),
  },
};

export default meta;

type Story = StoryObj<typeof AgentSwitcher>;

export const Default: Story = {};

export const Loading: Story = {
  args: {
    isLoading: true,
  },
};

export const ErrorState: Story = {
  args: {
    error: new Error('Inventory unavailable'),
  },
};

export const Empty: Story = {
  args: {
    agents: [],
  },
};
