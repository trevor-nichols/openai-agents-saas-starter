'use client';

import { useEffect, useMemo, useState } from 'react';
import { Filter, RefreshCcw } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { useToast } from '@/components/ui/use-toast';
import { GlassPanel, SectionHeader, StatCard } from '@/components/ui/foundation';
import { usePlatformStatusQuery } from '@/lib/queries/status';
import { useResendIncidentMutation, useStatusSubscriptionsQuery } from '@/lib/queries/statusOps';
import type { StatusSubscriptionSummary } from '@/types/statusSubscriptions';

import { ResendIncidentPanel } from './components/ResendIncidentPanel';
import { SubscriptionsTable } from './components/SubscriptionsTable';
import { formatDateTime } from './utils';

interface StatusOpsWorkspaceProps {
  defaultTenantId?: string | null;
}

type ChannelFilter = 'all' | 'email' | 'webhook';
type StatusFilter = 'all' | 'active' | 'pending_verification' | 'revoked';
type SeverityFilter = 'any' | 'all' | 'major' | 'maintenance';

export function StatusOpsWorkspace({ defaultTenantId }: StatusOpsWorkspaceProps) {
  const [channelFilter, setChannelFilter] = useState<ChannelFilter>('all');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>('any');
  const [searchTerm, setSearchTerm] = useState('');
  const [tenantInput, setTenantInput] = useState<string>(defaultTenantId ?? '');
  const [appliedTenantId, setAppliedTenantId] = useState<string | null>(defaultTenantId ?? null);
  const [dispatchTenantScope, setDispatchTenantScope] = useState<string>(defaultTenantId ?? '');
  const [selectedSubscriptionId, setSelectedSubscriptionId] = useState<string | null>(null);
  const [selectedIncidentId, setSelectedIncidentId] = useState<string>('');
  const [severityForDispatch, setSeverityForDispatch] = useState<'all' | 'major' | 'maintenance'>('major');

  const toast = useToast();

  const subscriptionsQuery = useStatusSubscriptionsQuery({
    tenantId: appliedTenantId,
  });

  const statusQuery = usePlatformStatusQuery();
  const incidents = useMemo(() => statusQuery.status?.incidents ?? [], [statusQuery.status?.incidents]);

  useEffect(() => {
    if (!selectedIncidentId && incidents.length > 0) {
      const firstIncident = incidents[0];
      if (firstIncident) {
        setSelectedIncidentId(firstIncident.id);
      }
    }
  }, [incidents, selectedIncidentId]);

  const filteredSubscriptions = useMemo(() => {
    return subscriptionsQuery.subscriptions.filter((item) => {
      if (channelFilter !== 'all' && item.channel !== channelFilter) return false;
      if (statusFilter !== 'all' && item.status !== statusFilter) return false;
      if (severityFilter !== 'any' && item.severityFilter !== severityFilter) return false;

      if (searchTerm.trim()) {
        const search = searchTerm.toLowerCase();
        const haystack = `${item.targetMasked} ${item.createdBy}`.toLowerCase();
        if (!haystack.includes(search)) return false;
      }

      return true;
    });
  }, [subscriptionsQuery.subscriptions, channelFilter, statusFilter, severityFilter, searchTerm]);

  const metrics = useMemo(() => {
    const total = subscriptionsQuery.subscriptions.length;
    const active = subscriptionsQuery.subscriptions.filter((s) => s.status === 'active').length;
    const pending = subscriptionsQuery.subscriptions.filter((s) => s.status === 'pending_verification').length;
    const emailCount = subscriptionsQuery.subscriptions.filter((s) => s.channel === 'email').length;
    const webhookCount = subscriptionsQuery.subscriptions.filter((s) => s.channel === 'webhook').length;
    const tenantCount = new Set(
      subscriptionsQuery.subscriptions
        .filter((s) => s.tenantId)
        .map((s) => s.tenantId as string),
    ).size;

    return {
      total,
      active,
      pending,
      emailCount,
      webhookCount,
      tenantCount,
    };
  }, [subscriptionsQuery.subscriptions]);

  const resendMutation = useResendIncidentMutation();
  const [filtersOpen, setFiltersOpen] = useState(true);
  const [resendOpen, setResendOpen] = useState(false);

  const handleSelectSubscription = (subscription: StatusSubscriptionSummary) => {
    setSelectedSubscriptionId(subscription.id);
    if (subscription.tenantId) {
      setDispatchTenantScope(subscription.tenantId);
    }
  };

  const handleResetFilters = () => {
    setChannelFilter('all');
    setStatusFilter('all');
    setSeverityFilter('any');
    setSearchTerm('');
    setTenantInput('');
    setAppliedTenantId(null);
    setSelectedSubscriptionId(null);
    setDispatchTenantScope('');
  };

  const handleApplyTenantFilter = () => {
    const normalizedTenant = tenantInput.trim();
    setAppliedTenantId(normalizedTenant.length === 0 ? null : normalizedTenant);
    setSelectedSubscriptionId(null);
    setDispatchTenantScope(normalizedTenant);
  };

  const handleRefreshAll = async () => {
    await subscriptionsQuery.refetch();
    statusQuery.refetch();
  };

  const handleResend = async () => {
    if (!selectedIncidentId) {
      toast.info({
        title: 'Select an incident',
        description: 'Choose which incident to replay before dispatching alerts.',
      });
      return;
    }

    try {
      const tenantScope = dispatchTenantScope.trim();
      const response = await resendMutation.mutateAsync({
        incidentId: selectedIncidentId,
        severity: severityForDispatch,
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
      <SectionHeader
        eyebrow="Operations"
        title="Status console"
        description="Audit status alert subscribers and replay incident notifications without leaving the console."
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleRefreshAll}>
              <RefreshCcw className="h-4 w-4" aria-hidden />
              Refresh
            </Button>
          </div>
        }
      />

      <div className="grid gap-4 md:grid-cols-3">
        <StatCard
          label="Active subscriptions"
          value={metrics.active}
          helperText={`${metrics.pending} pending verification · ${metrics.total} loaded`}
        />
        <StatCard
          label="Delivery mix"
          value={`${metrics.emailCount} email · ${metrics.webhookCount} webhook`}
          helperText="Based on loaded rows"
        />
        <StatCard
          label="Tenant coverage"
          value={metrics.tenantCount > 0 ? `${metrics.tenantCount} tenants` : 'Global only'}
          helperText={appliedTenantId ? `Filtered by tenant ${appliedTenantId}` : 'All tenants'}
        />
      </div>

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
        <Sheet open={resendOpen} onOpenChange={setResendOpen}>
          <SheetTrigger asChild>
            <Button>Replay incident</Button>
          </SheetTrigger>
          <SheetContent side="right" className="w-full sm:max-w-lg">
            <SheetHeader>
              <SheetTitle>Replay incident</SheetTitle>
            </SheetHeader>
            <div className="mt-4">
              <ResendIncidentPanel
                incidents={incidents}
                isLoadingIncidents={statusQuery.isLoading}
                selectedIncidentId={selectedIncidentId}
                severity={severityForDispatch}
                tenantScope={dispatchTenantScope}
                onIncidentChange={setSelectedIncidentId}
                onSeverityChange={setSeverityForDispatch}
                onTenantScopeChange={setDispatchTenantScope}
                onClearTenantScope={() => setDispatchTenantScope('')}
                onSubmit={handleResend}
                isSubmitting={resendMutation.isPending}
              />
            </div>
          </SheetContent>
        </Sheet>
      </div>

      {filtersOpen ? (
        <GlassPanel className="space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <Select value={channelFilter} onValueChange={(value) => setChannelFilter(value as ChannelFilter)}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Channel" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All channels</SelectItem>
                <SelectItem value="email">Email</SelectItem>
                <SelectItem value="webhook">Webhook</SelectItem>
              </SelectContent>
            </Select>

            <Select value={statusFilter} onValueChange={(value) => setStatusFilter(value as StatusFilter)}>
              <SelectTrigger className="w-[170px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All statuses</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="pending_verification">Pending verification</SelectItem>
                <SelectItem value="revoked">Revoked</SelectItem>
              </SelectContent>
            </Select>

            <Select value={severityFilter} onValueChange={(value) => setSeverityFilter(value as SeverityFilter)}>
              <SelectTrigger className="w-[170px]">
                <SelectValue placeholder="Severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="any">Any severity</SelectItem>
                <SelectItem value="major">Major</SelectItem>
                <SelectItem value="maintenance">Maintenance</SelectItem>
                <SelectItem value="all">All</SelectItem>
              </SelectContent>
            </Select>

            <Input
              className="min-w-[200px] flex-1"
              placeholder="Search subscriber or creator"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
            />
          </div>

          <div className="flex flex-wrap items-end gap-2">
            <div className="flex flex-col gap-2">
              <Label htmlFor="tenant-filter">Tenant filter</Label>
              <div className="flex gap-2">
                <Input
                  id="tenant-filter"
                  placeholder="Tenant UUID (optional)"
                  value={tenantInput}
                  onChange={(event) => setTenantInput(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter') handleApplyTenantFilter();
                  }}
                />
                <Button variant="outline" onClick={handleApplyTenantFilter}>
                  Apply
                </Button>
                {appliedTenantId ? (
                  <Button
                    variant="ghost"
                    onClick={() => {
                      setTenantInput('');
                      setAppliedTenantId(null);
                      setDispatchTenantScope('');
                    }}
                  >
                    Clear
                  </Button>
                ) : null}
              </div>
            </div>

            <Button variant="ghost" onClick={handleResetFilters}>
              Reset filters
            </Button>
          </div>
        </GlassPanel>
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
