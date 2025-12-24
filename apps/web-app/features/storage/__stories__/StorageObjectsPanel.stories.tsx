'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { StorageObjectsPanel } from '../components';

const meta: Meta<typeof StorageObjectsPanel> = {
  title: 'Storage/StorageObjectsPanel',
  component: StorageObjectsPanel,
};

export default meta;

type Story = StoryObj<typeof StorageObjectsPanel>;

export const Default: Story = {};
