'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { WorkflowRunPanel } from '../components/canvas/WorkflowRunPanel';

const meta: Meta<typeof WorkflowRunPanel> = {
  title: 'Workflows/Workflow Run Panel',
  component: WorkflowRunPanel,
};

export default meta;

type Story = StoryObj<typeof WorkflowRunPanel>;

const baseArgs = {
  selectedKey: 'triage-and-summary',
  onRun: async (payload: { workflowKey: string; message: string; shareLocation?: boolean; location?: unknown }) => {
    console.log('run', payload);
  },
  runError: null,
  isRunning: false,
  isLoadingWorkflows: false,
};

export const ReadyToRun: Story = {
  args: {
    ...baseArgs,
  },
};

export const Running: Story = {
  args: {
    ...baseArgs,
    isRunning: true,
    streamStatus: 'streaming',
  },
};

export const WithError: Story = {
  args: {
    ...baseArgs,
    runError: 'The workflow failed to start. Please retry.',
  },
};

export const LoadingWorkflows: Story = {
  args: {
    ...baseArgs,
    selectedKey: null,
    isLoadingWorkflows: true,
  },
};

export const NoSelection: Story = {
  args: {
    ...baseArgs,
    selectedKey: null,
  },
};
