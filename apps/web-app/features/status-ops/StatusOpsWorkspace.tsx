'use client';

import { useMemo, useState } from 'react';
import { Filter } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';
import { GlassPanel } from '@/components/ui/foundation';
import { usePlatformStatusQuery } from '@/lib/queries/status';
import { useResendIncidentMutation, useStatusSubscriptionsQuery } from '@/lib/queries/statusOps';
import type { StatusSubscriptionSummary } from '@/types/statusSubscriptions';

import { IncidentReplaySheet } from './components/IncidentReplaySheet';
import { StatusOpsFiltersPanel } from './components/StatusOpsFiltersPanel';
import { StatusOpsHeader } from './components/StatusOpsHeader';
import { StatusOpsStatsRow } from './components/StatusOpsStatsRow';
import { SubscriptionsTable } from './components/SubscriptionsTable';
import { useIncidentReplayState } from './hooks/useIncidentReplayState';
import { useStatusOpsFilters } from './hooks/useStatusOpsFilters';
import { useStatusOpsMetrics } from './hooks/useStatusOpsMetrics';
import { formatDateTime } from './utils';

interface StatusOpsWorkspaceProps {
  defaultTenantId?: string | null;
}

export function StatusOpsWorkspace({ defaultTenantId }: StatusOpsWorkspaceProps) {
  const [selectedSubscriptionId, setSelectedSubscriptionId] = useState<string | null>(null);
  const [appliedTenantId, setAppliedTenantId] = useState<string | null>(defaultTenantId ?? null);
  const toast = useToast();

  const subscriptionsQuery = useStatusSubscriptionsQuery({
    tenantId: appliedTenantId,
  });

  const statusQuery = usePlatformStatusQuery();
  const incidents = useMemo(() => statusQuery.status?.incidents ?? [], [statusQuery.status?.incidents]);

  const metrics = useStatusOpsMetrics(subscriptionsQuery.subscriptions);

  const {
    channelFilter,
    statusFilter,
    severityFilter,
    searchTerm,
    tenantInput,
    filteredSubscriptions,
    setChannelFilter,
    setStatusFilter,
    setSeverityFilter,
    setSearchTerm,
    setTenantInput,
    applyTenantFilter,
    resetFilters,
  } = useStatusOpsFilters({
    subscriptions: subscriptionsQuery.subscriptions,
    appliedTenantId,
    defaultTenantId,
    onAppliedTenantChange: setAppliedTenantId,
  });

  const incidentReplayState = useIncidentReplayState(incidents, defaultTenantId ?? '');
  const [filtersOpen, setFiltersOpen] = useState(true);
  const [resendOpen, setResendOpen] = useState(false);

  const resendMutation = useResendIncidentMutation();

  const handleSelectSubscription = (subscription: StatusSubscriptionSummary) => {
    setSelectedSubscriptionId(subscription.id);
    if (subscription.tenantId) {
      incidentReplayState.setTenantScope(subscription.tenantId);
    }
  };

  const handleResetFilters = () => {
    setSelectedSubscriptionId(null);
    incidentReplayState.setTenantScope('');
    resetFilters();
  };

  const handleApplyTenantFilter = () => {
    const nextTenant = applyTenantFilter();
    setSelectedSubscriptionId(null);
    incidentReplayState.setTenantScope(nextTenant ?? '');
  };

  const handleRefreshAll = async () => {
    await subscriptionsQuery.refetch();
    statusQuery.refetch();
  };

  const handleResend = async () => {
    if (!incidentReplayState.activeIncidentId) {
      toast.info({
        title: 'Select an incident',
        description: 'Choose which incident to replay before dispatching alerts.',
      });
      return;
    }

    try {
      const tenantScope = incidentReplayState.tenantScope.trim();
      const response = await resendMutation.mutateAsync({
        incidentId: incidentReplayState.activeIncidentId,
        severity: incidentReplayState.severity,
        tenantId: tenantScope || null,
      });
      toast.success({
        title: 'Incident resent',
        description: `Dispatched to ${response.dispatched} subscription(s).`,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to resend incident.';
      toast.error({
        title: 'Dispatch failed',
        description: message,
      });
    }
  };

  return (
    <section className="space-y-8">
      <StatusOpsHeader onRefresh={handleRefreshAll} />

      <StatusOpsStatsRow metrics={metrics} appliedTenantId={appliedTenantId} />

      {statusQuery.error ? (
        <GlassPanel className="border border-destructive/30 bg-destructive/5">
          <p className="text-sm text-destructive">Status snapshot failed to load. {statusQuery.error.message}</p>
          <div className="mt-2">
            <Button variant="outline" size="sm" onClick={() => statusQuery.refetch()}>
              Retry status fetch
            </Button>
          </div>
        </GlassPanel>
      ) : null}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="ghost" onClick={() => setFiltersOpen((open) => !open)}>
            <Filter className="h-4 w-4" aria-hidden />
            {filtersOpen ? 'Hide filters' : 'Show filters'}
          </Button>
        </div>
        <IncidentReplaySheet
          open={resendOpen}
          onOpenChange={setResendOpen}
          incidents={incidents}
          isLoadingIncidents={statusQuery.isLoading}
          selectedIncidentId={incidentReplayState.activeIncidentId}
          severity={incidentReplayState.severity}
          tenantScope={incidentReplayState.tenantScope}
          onIncidentChange={(incidentId) => {
            setSelectedSubscriptionId(null);
            incidentReplayState.setSelectedIncidentId(incidentId);
          }}
          onSeverityChange={incidentReplayState.setSeverity}
          onTenantScopeChange={incidentReplayState.setTenantScope}
          onClearTenantScope={incidentReplayState.clearTenantScope}
          onSubmit={handleResend}
          isSubmitting={resendMutation.isPending}
        />
      </div>

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
          onApplyTenantFilter={handleApplyTenantFilter}
          onClearTenantFilter={() => {
            setTenantInput('');
            setAppliedTenantId(null);
            incidentReplayState.setTenantScope('');
          }}
          onResetFilters={handleResetFilters}
        />
      ) : null}

      <SubscriptionsTable
        subscriptions={filteredSubscriptions}
        isLoading={subscriptionsQuery.isLoading}
        isError={subscriptionsQuery.isError}
        error={subscriptionsQuery.error?.message}
        onRetry={() => subscriptionsQuery.refetch()}
        onRowSelect={handleSelectSubscription}
        selectedId={selectedSubscriptionId}
      />

      <div className="flex items-center justify-between">
        <div className="text-sm text-foreground/60">
          Showing {filteredSubscriptions.length} of {subscriptionsQuery.subscriptions.length} loaded · Last refresh{' '}
          {statusQuery.status ? formatDateTime(statusQuery.status.generatedAt) : '—'}
        </div>
        {subscriptionsQuery.hasNextPage ? (
          <Button
            variant="outline"
            onClick={() => subscriptionsQuery.fetchNextPage()}
            disabled={subscriptionsQuery.isFetchingNextPage}
          >
            {subscriptionsQuery.isFetchingNextPage ? 'Loading…' : 'Load more'}
          </Button>
        ) : null}
      </div>
    </section>
  );
}
