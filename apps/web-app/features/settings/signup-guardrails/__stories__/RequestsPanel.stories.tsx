'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { RequestsPanel } from '../components/RequestsPanel';

const meta: Meta<typeof RequestsPanel> = {
  title: 'Settings/Signup Guardrails/Requests Panel',
  component: RequestsPanel,
};

export default meta;

type Story = StoryObj<typeof RequestsPanel>;

export const Default: Story = {};
