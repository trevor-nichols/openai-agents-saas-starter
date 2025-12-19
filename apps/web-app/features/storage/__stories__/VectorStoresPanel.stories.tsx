'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { VectorStoresPanel } from '../components/VectorStoresPanel';

const meta: Meta<typeof VectorStoresPanel> = {
  title: 'Storage/VectorStoresPanel',
  component: VectorStoresPanel,
};

export default meta;

type Story = StoryObj<typeof VectorStoresPanel>;

export const Default: Story = {};
