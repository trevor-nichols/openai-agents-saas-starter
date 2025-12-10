'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { WebhookSettingsCard } from '../components/WebhookSettingsCard';
import { sampleTenantSettings } from './fixtures';

const meta: Meta<typeof WebhookSettingsCard> = {
  title: 'Settings/Tenant/Webhook Settings Card',
  component: WebhookSettingsCard,
  args: {
    webhookUrl: sampleTenantSettings.billingWebhookUrl,
    isSaving: false,
    onSubmit: async (url) => {
      console.log('save webhook', url);
    },
  },
};

export default meta;

type Story = StoryObj<typeof WebhookSettingsCard>;

export const Default: Story = {};

export const EmptyUrl: Story = {
  args: {
    webhookUrl: null,
  },
};

export const Saving: Story = {
  args: {
    isSaving: true,
  },
};
