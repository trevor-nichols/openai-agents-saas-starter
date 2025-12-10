'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { InvitesPanel } from '../components/InvitesPanel';

const meta: Meta<typeof InvitesPanel> = {
  title: 'Settings/Signup Guardrails/Invites Panel',
  component: InvitesPanel,
};

export default meta;

type Story = StoryObj<typeof InvitesPanel>;

export const Default: Story = {};
