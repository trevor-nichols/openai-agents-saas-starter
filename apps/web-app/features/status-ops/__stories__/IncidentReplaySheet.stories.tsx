'use client';

import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';

import { IncidentReplaySheet } from '../components/IncidentReplaySheet';
import { mockIncidents } from './fixtures';

function IncidentReplaySheetPreview() {
  const [open, setOpen] = useState(true);
  const [selectedIncidentId, setSelectedIncidentId] = useState(mockIncidents[0]?.id ?? '');
  const [tenantScope, setTenantScope] = useState('');
  const [severity, setSeverity] = useState<'all' | 'major' | 'maintenance'>('major');

  return (
    <IncidentReplaySheet
      open={open}
      onOpenChange={setOpen}
      incidents={mockIncidents}
      isLoadingIncidents={false}
      selectedIncidentId={selectedIncidentId}
      severity={severity}
      tenantScope={tenantScope}
      onIncidentChange={setSelectedIncidentId}
      onSeverityChange={setSeverity}
      onTenantScopeChange={setTenantScope}
      onClearTenantScope={() => setTenantScope('')}
      onSubmit={() => console.log('replay', { selectedIncidentId, severity, tenantScope })}
      isSubmitting={false}
    />
  );
}

const meta: Meta<typeof IncidentReplaySheetPreview> = {
  title: 'Status Ops/IncidentReplaySheet',
  component: IncidentReplaySheetPreview,
};

export default meta;

type Story = StoryObj<typeof IncidentReplaySheetPreview>;

export const Default: Story = {};
