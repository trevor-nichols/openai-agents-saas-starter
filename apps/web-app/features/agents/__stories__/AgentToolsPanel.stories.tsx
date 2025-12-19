'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { AgentToolsPanel } from '../components/AgentToolsPanel';
import { agentSummaries, toolsByAgent, toolsSummary } from './fixtures';

const meta: Meta<typeof AgentToolsPanel> = {
  title: 'Agents/AgentToolsPanel',
  component: AgentToolsPanel,
  args: {
    onRefresh: () => console.log('refresh tools'),
  },
};

export default meta;

type Story = StoryObj<typeof AgentToolsPanel>;

export const Default: Story = {
  args: {
    summary: toolsSummary,
    toolsByAgent,
    selectedAgent: agentSummaries[0]?.name ?? null,
    isLoading: false,
    error: null,
  },
};

export const Loading: Story = {
  args: {
    summary: toolsSummary,
    toolsByAgent: {},
    selectedAgent: null,
    isLoading: true,
    error: null,
  },
};

export const Error: Story = {
  args: {
    summary: toolsSummary,
    toolsByAgent,
    selectedAgent: agentSummaries[1]?.name ?? null,
    isLoading: false,
    error: 'Tool registry unreachable',
  },
};

export const EmptyTools: Story = {
  args: {
    summary: { totalTools: 0, categories: [], toolNames: [] },
    toolsByAgent: {},
    selectedAgent: null,
    isLoading: false,
    error: null,
  },
};
