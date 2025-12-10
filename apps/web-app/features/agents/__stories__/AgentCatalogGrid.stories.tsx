'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { AgentCatalogGrid } from '../components/AgentCatalogGrid';
import { agentSummaries, toolsByAgent, toolsSummary } from './fixtures';

const meta: Meta<typeof AgentCatalogGrid> = {
  title: 'Agents/AgentCatalogGrid',
  component: AgentCatalogGrid,
  args: {
    onRefreshTools: () => console.log('refresh tools'),
  },
};

export default meta;

type Story = StoryObj<typeof AgentCatalogGrid>;

export const Default: Story = {
  args: {
    agents: agentSummaries,
    toolsByAgent,
    summary: toolsSummary,
    isLoadingAgents: false,
    isLoadingTools: false,
    errorMessage: null,
    selectedAgent: 'triage_agent',
    onSelectAgent: (agentName: string) => console.log('select', agentName),
  },
};

export const Loading: Story = {
  args: {
    agents: [],
    toolsByAgent: {},
    summary: toolsSummary,
    isLoadingAgents: true,
    isLoadingTools: true,
    errorMessage: null,
    selectedAgent: null,
    onSelectAgent: () => {},
  },
};

export const Error: Story = {
  args: {
    agents: [],
    toolsByAgent: {},
    summary: toolsSummary,
    isLoadingAgents: false,
    isLoadingTools: false,
    errorMessage: 'Unable to reach agent registry',
    selectedAgent: null,
    onSelectAgent: () => {},
  },
};

export const Empty: Story = {
  args: {
    agents: [],
    toolsByAgent: {},
    summary: toolsSummary,
    isLoadingAgents: false,
    isLoadingTools: false,
    errorMessage: null,
    selectedAgent: null,
    onSelectAgent: () => {},
  },
};
