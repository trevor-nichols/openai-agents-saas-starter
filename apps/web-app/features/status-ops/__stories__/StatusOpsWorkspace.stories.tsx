'use client';

import type { Meta, StoryObj } from '@storybook/react';
import { useMemo, useState } from 'react';
import { Filter } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { GlassPanel } from '@/components/ui/foundation';
import { StatusOpsFiltersPanel } from '../components/StatusOpsFiltersPanel';
import { StatusOpsHeader } from '../components/StatusOpsHeader';
import { StatusOpsStatsRow } from '../components/StatusOpsStatsRow';
import { SubscriptionsTable } from '../components/SubscriptionsTable';
import { IncidentReplaySheet } from '../components/IncidentReplaySheet';
import { applySubscriptionFilters } from '../hooks/useStatusOpsFilters';
import { deriveStatusOpsMetrics } from '../hooks/useStatusOpsMetrics';
import { useIncidentReplayState } from '../hooks/useIncidentReplayState';
import type { ChannelFilter, SeverityFilter, StatusFilter } from '../constants';
import { mockIncidents, mockMetrics, mockSubscriptions, defaultTenantId } from './fixtures';

type WorkspacePreviewProps = {
  isLoading?: boolean;
  isError?: boolean;
  showEmpty?: boolean;
};

function StatusOpsWorkspacePreview({ isLoading = false, isError = false, showEmpty = false }: WorkspacePreviewProps) {
  const [channelFilter, setChannelFilter] = useState<ChannelFilter>('all');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>('any');
  const [searchTerm, setSearchTerm] = useState('');
  const [tenantInput, setTenantInput] = useState(defaultTenantId ?? '');
  const [appliedTenantId, setAppliedTenantId] = useState<string | null>(defaultTenantId);
  const [filtersOpen, setFiltersOpen] = useState(true);
  const [resendOpen, setResendOpen] = useState(false);
  const [selectedSubscriptionId, setSelectedSubscriptionId] = useState<string | null>(null);

  const incidents = useMemo(() => (showEmpty ? [] : mockIncidents), [showEmpty]);
  const subscriptions = useMemo(() => (showEmpty ? [] : mockSubscriptions), [showEmpty]);
  const metrics = useMemo(() => (showEmpty ? deriveStatusOpsMetrics([]) : mockMetrics), [showEmpty]);

  const filteredSubscriptions = useMemo(
    () =>
      applySubscriptionFilters(subscriptions, {
        channelFilter,
        statusFilter,
        severityFilter,
        searchTerm,
        appliedTenantId,
      }),
    [appliedTenantId, channelFilter, searchTerm, severityFilter, statusFilter, subscriptions],
  );

  const incidentReplayState = useIncidentReplayState(incidents, defaultTenantId);

  return (
    <section className="space-y-8">
      <StatusOpsHeader onRefresh={() => console.log('refresh status')} />

      <StatusOpsStatsRow metrics={metrics} appliedTenantId={appliedTenantId} />

      <GlassPanel className="flex flex-wrap items-center justify-between gap-3">
        <Button variant="ghost" onClick={() => setFiltersOpen((open) => !open)}>
          <Filter className="h-4 w-4" aria-hidden />
          {filtersOpen ? 'Hide filters' : 'Show filters'}
        </Button>

        <IncidentReplaySheet
          open={resendOpen}
          onOpenChange={setResendOpen}
          incidents={incidents}
          isLoadingIncidents={isLoading}
          selectedIncidentId={incidentReplayState.activeIncidentId}
          severity={incidentReplayState.severity}
          tenantScope={incidentReplayState.tenantScope}
          onIncidentChange={(incidentId) => {
            incidentReplayState.setSelectedIncidentId(incidentId);
          }}
          onSeverityChange={incidentReplayState.setSeverity}
          onTenantScopeChange={incidentReplayState.setTenantScope}
          onClearTenantScope={incidentReplayState.clearTenantScope}
          onSubmit={() => console.log('resend incident', incidentReplayState)}
          isSubmitting={false}
        />
      </GlassPanel>

      {filtersOpen ? (
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
            const normalized = tenantInput.trim();
            const nextTenant = normalized.length === 0 ? null : normalized;
            setAppliedTenantId(nextTenant);
            incidentReplayState.setTenantScope(nextTenant ?? '');
          }}
          onClearTenantFilter={() => {
            setTenantInput('');
            setAppliedTenantId(null);
            incidentReplayState.clearTenantScope();
          }}
          onResetFilters={() => {
            setChannelFilter('all');
            setStatusFilter('all');
            setSeverityFilter('any');
            setSearchTerm('');
            setTenantInput('');
            setAppliedTenantId(null);
            incidentReplayState.clearTenantScope();
          setSelectedSubscriptionId(null);
          }}
        />
      ) : null}

      <SubscriptionsTable
        subscriptions={filteredSubscriptions}
        isLoading={isLoading}
        isError={isError}
        error={isError ? 'Failed to load subscriptions' : undefined}
        onRetry={() => console.log('retry fetch')}
        onRowSelect={(subscription) => {
          console.log('select subscription', subscription);
        setSelectedSubscriptionId(subscription.id);
          if (subscription.tenantId) {
            incidentReplayState.setTenantScope(subscription.tenantId);
          }
        }}
      selectedId={selectedSubscriptionId}
      />

      <div className="text-sm text-foreground/60">
        Showing {filteredSubscriptions.length} of {subscriptions.length} loaded · Tenant filter{' '}
        {appliedTenantId ?? 'All'}
      </div>
    </section>
  );
}

const meta: Meta<typeof StatusOpsWorkspacePreview> = {
  title: 'Status Ops/Page',
  component: StatusOpsWorkspacePreview,
};

export default meta;

type Story = StoryObj<typeof StatusOpsWorkspacePreview>;

export const Default: Story = {};

export const Loading: Story = {
  args: {
    isLoading: true,
  },
};

export const ErrorState: Story = {
  args: {
    isError: true,
  },
};

export const Empty: Story = {
  args: {
    showEmpty: true,
  },
};
