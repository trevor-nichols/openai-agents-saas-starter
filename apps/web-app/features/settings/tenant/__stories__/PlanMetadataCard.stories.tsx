'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { PlanMetadataCard } from '../components/PlanMetadataCard';
import { sampleTenantSettings } from './fixtures';

const meta: Meta<typeof PlanMetadataCard> = {
  title: 'Settings/Tenant/Plan Metadata Card',
  component: PlanMetadataCard,
  args: {
    planMetadata: sampleTenantSettings.planMetadata,
    isSaving: false,
    onSubmit: async (metadata) => {
      console.log('save metadata', metadata);
    },
  },
};

export default meta;

type Story = StoryObj<typeof PlanMetadataCard>;

export const Default: Story = {};

export const Saving: Story = {
  args: {
    isSaving: true,
  },
};

export const EmptyMetadata: Story = {
  args: {
    planMetadata: {},
  },
};
