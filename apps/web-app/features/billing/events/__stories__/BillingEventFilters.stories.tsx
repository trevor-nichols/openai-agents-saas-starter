'use client';

import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';

import { BillingEventFilters } from '../components/BillingEventFilters';

function BillingEventFiltersPreview() {
  const [status, setStatus] = useState<'all' | 'received' | 'processed' | 'failed'>('all');
  const [eventType, setEventType] = useState('');

  return (
    <BillingEventFilters
      processingStatus={status}
      onProcessingStatusChange={setStatus}
      eventType={eventType}
      onEventTypeChange={setEventType}
    />
  );
}

const meta: Meta<typeof BillingEventFiltersPreview> = {
  title: 'Billing/BillingEventFilters',
  component: BillingEventFiltersPreview,
};

export default meta;

type Story = StoryObj<typeof BillingEventFiltersPreview>;

export const Default: Story = {};
