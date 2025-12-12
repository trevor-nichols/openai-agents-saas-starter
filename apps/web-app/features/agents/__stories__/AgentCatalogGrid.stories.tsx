'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { AgentCatalogGrid } from '../components/AgentCatalogGrid';
import { agentSummaries, toolsByAgent, toolsSummary } from './fixtures';

const defaultPages = [
  {
    items: agentSummaries.slice(0, 6),
    next_cursor: null,
    total: agentSummaries.length,
  },
];

const meta: Meta<typeof AgentCatalogGrid> = {
  title: 'Agents/AgentCatalogGrid',
  component: AgentCatalogGrid,
  args: {
    onRefreshTools: () => console.log('refresh tools'),
    onRefreshAgents: () => console.log('refresh agents'),
    onNextPage: () => console.log('next page'),
    onPrevPage: () => console.log('prev page'),
    onPageSelect: (index: number) => console.log('page select', index),
  },
};

export default meta;

type Story = StoryObj<typeof AgentCatalogGrid>;

export const Default: Story = {
  args: {
    agentsPages: defaultPages,
    visiblePageIndex: 0,
    totalAgents: agentSummaries.length,
    hasNextPage: false,
    hasPrevPage: false,
    isFetchingNextPage: false,
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
    agentsPages: [],
    visiblePageIndex: 0,
    totalAgents: 0,
    hasNextPage: false,
    hasPrevPage: false,
    isFetchingNextPage: false,
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
    agentsPages: [],
    visiblePageIndex: 0,
    totalAgents: 0,
    hasNextPage: false,
    hasPrevPage: false,
    isFetchingNextPage: false,
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
    agentsPages: [],
    visiblePageIndex: 0,
    totalAgents: 0,
    hasNextPage: false,
    hasPrevPage: false,
    isFetchingNextPage: false,
    toolsByAgent: {},
    summary: toolsSummary,
    isLoadingAgents: false,
    isLoadingTools: false,
    errorMessage: null,
    selectedAgent: null,
    onSelectAgent: () => {},
  },
};
