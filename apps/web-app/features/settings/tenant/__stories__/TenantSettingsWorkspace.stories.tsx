'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { TenantSettingsWorkspace } from '../TenantSettingsWorkspace';

const meta: Meta<typeof TenantSettingsWorkspace> = {
  title: 'Settings/Tenant/Workspace',
  component: TenantSettingsWorkspace,
};

export default meta;

type Story = StoryObj<typeof TenantSettingsWorkspace>;

export const Default: Story = {};
