'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { StorageAdmin } from '../StorageAdmin';

const meta: Meta<typeof StorageAdmin> = {
  title: 'Storage/StorageAdminPage',
  component: StorageAdmin,
};

export default meta;

type Story = StoryObj<typeof StorageAdmin>;

export const Default: Story = {};
