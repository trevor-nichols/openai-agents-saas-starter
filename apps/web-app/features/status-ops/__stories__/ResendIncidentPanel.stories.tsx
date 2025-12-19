'use client';

import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';

import { ResendIncidentPanel } from '../components/ResendIncidentPanel';
import { mockIncidents } from './fixtures';

function ResendPanelPreview({ isLoadingIncidents = false, isEmpty = false }: { isLoadingIncidents?: boolean; isEmpty?: boolean }) {
  const incidents = isEmpty ? [] : mockIncidents;
  const [selectedIncidentId, setSelectedIncidentId] = useState<string>(incidents[0]?.id ?? '');
  const [severity, setSeverity] = useState<'all' | 'major' | 'maintenance'>('major');
  const [tenantScope, setTenantScope] = useState('');

  return (
    <ResendIncidentPanel
      incidents={incidents}
      isLoadingIncidents={isLoadingIncidents}
      selectedIncidentId={selectedIncidentId}
      severity={severity}
      tenantScope={tenantScope}
      onIncidentChange={setSelectedIncidentId}
      onSeverityChange={setSeverity}
      onTenantScopeChange={setTenantScope}
      onClearTenantScope={() => setTenantScope('')}
      onSubmit={() => console.log('resend', { selectedIncidentId, severity, tenantScope })}
      isSubmitting={false}
    />
  );
}

const meta: Meta<typeof ResendPanelPreview> = {
  title: 'Status Ops/ResendIncidentPanel',
  component: ResendPanelPreview,
};

export default meta;

type Story = StoryObj<typeof ResendPanelPreview>;

export const Default: Story = {};

export const Loading: Story = {
  args: {
    isLoadingIncidents: true,
  },
};

export const Empty: Story = {
  args: {
    isEmpty: true,
  },
};
