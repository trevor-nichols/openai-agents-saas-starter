'use client';

import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';

import { StatusOpsFiltersPanel } from '../components/StatusOpsFiltersPanel';
import type { ChannelFilter, SeverityFilter, StatusFilter } from '../constants';

function FiltersPreview() {
  const [channelFilter, setChannelFilter] = useState<ChannelFilter>('all');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>('any');
  const [searchTerm, setSearchTerm] = useState('');
  const [tenantInput, setTenantInput] = useState('');
  const [appliedTenantId, setAppliedTenantId] = useState<string | null>(null);

  return (
    <StatusOpsFiltersPanel
      channelFilter={channelFilter}
      statusFilter={statusFilter}
      severityFilter={severityFilter}
      searchTerm={searchTerm}
      tenantInput={tenantInput}
      appliedTenantId={appliedTenantId}
      onChannelChange={setChannelFilter}
      onStatusChange={setStatusFilter}
      onSeverityChange={setSeverityFilter}
      onSearchTermChange={setSearchTerm}
      onTenantInputChange={setTenantInput}
      onApplyTenantFilter={() => {
        const nextTenant = tenantInput.trim() || null;
        setAppliedTenantId(nextTenant);
        console.log('apply tenant filter', nextTenant);
      }}
      onClearTenantFilter={() => {
        setTenantInput('');
        setAppliedTenantId(null);
      }}
      onResetFilters={() => {
        setChannelFilter('all');
        setStatusFilter('all');
        setSeverityFilter('any');
        setSearchTerm('');
        setTenantInput('');
        setAppliedTenantId(null);
      }}
    />
  );
}

const meta: Meta<typeof FiltersPreview> = {
  title: 'Status Ops/FiltersPanel',
  component: FiltersPreview,
};

export default meta;

type Story = StoryObj<typeof FiltersPreview>;

export const Default: Story = {};
