'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { ContainerBindingsPanel } from '../components/ContainerBindingsPanel';
import { sampleContainers } from './fixtures';

const meta: Meta<typeof ContainerBindingsPanel> = {
  title: 'Agents/ContainerBindingsPanel',
  component: ContainerBindingsPanel,
  args: {
    onSelect: (id: string) => console.log('select container', id),
    onCreate: (name: string, memory?: string | null) => console.log('create container', { name, memory }),
    onDelete: (id: string) => console.log('delete container', id),
    onBind: (id: string) => console.log('bind container', id),
    onUnbind: () => console.log('unbind container'),
  },
};

export default meta;

type Story = StoryObj<typeof ContainerBindingsPanel>;

export const Default: Story = {
  args: {
    containers: sampleContainers,
    isLoading: false,
    error: null,
    selectedContainerId: sampleContainers[0]?.id ?? null,
    agentKey: 'triage_agent',
  },
};

export const Loading: Story = {
  args: {
    containers: [],
    isLoading: true,
    error: null,
    selectedContainerId: null,
    agentKey: 'triage_agent',
  },
};

export const Error: Story = {
  args: {
    containers: [],
    isLoading: false,
    error: new Error('Containers endpoint unavailable'),
    selectedContainerId: null,
    agentKey: 'triage_agent',
  },
};

export const Empty: Story = {
  args: {
    containers: [],
    isLoading: false,
    error: null,
    selectedContainerId: null,
    agentKey: 'triage_agent',
  },
};
