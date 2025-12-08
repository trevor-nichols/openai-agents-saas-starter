import type { Meta, StoryObj } from '@storybook/react';

import { ToolMetadataPanel } from '../components/ToolMetadataPanel';
import type { ToolRegistry } from '@/types/tools';

const registry: ToolRegistry = {
  total_tools: 4,
  categories: ['search', 'code_interpreter'],
  tool_names: ['file_search', 'web_search', 'code_interpreter', 'browser'],
};

const meta: Meta<typeof ToolMetadataPanel> = {
  title: 'Chat/ToolMetadataPanel',
  component: ToolMetadataPanel,
  args: {
    selectedAgent: 'triage_agent',
    tools: registry,
    isLoading: false,
    error: null,
    onRefresh: () => console.log('refresh tools'),
  },
};

export default meta;

type Story = StoryObj<typeof ToolMetadataPanel>;

export const Default: Story = {};

export const Loading: Story = {
  args: {
    isLoading: true,
  },
};

export const ErrorState: Story = {
  args: {
    error: 'Failed to fetch tools',
  },
};

export const Empty: Story = {
  args: {
    tools: {
      total_tools: 0,
      categories: [],
      tool_names: [],
    },
  },
};
