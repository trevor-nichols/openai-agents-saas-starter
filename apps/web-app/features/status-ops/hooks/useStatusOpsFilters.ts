import { useCallback, useMemo, useState } from 'react';

import type { StatusSubscriptionSummary } from '@/types/statusSubscriptions';

import type { ChannelFilter, SeverityFilter, StatusFilter } from '../constants';

interface FiltersState {
  channelFilter: ChannelFilter;
  statusFilter: StatusFilter;
  severityFilter: SeverityFilter;
  searchTerm: string;
  appliedTenantId: string | null;
}

interface UseStatusOpsFiltersParams {
  subscriptions: StatusSubscriptionSummary[];
  appliedTenantId: string | null;
  defaultTenantId?: string | null;
  onAppliedTenantChange?: (tenantId: string | null) => void;
}

interface UseStatusOpsFiltersResult extends FiltersState {
  tenantInput: string;
  filteredSubscriptions: StatusSubscriptionSummary[];
  setChannelFilter: (value: ChannelFilter) => void;
  setStatusFilter: (value: StatusFilter) => void;
  setSeverityFilter: (value: SeverityFilter) => void;
  setSearchTerm: (value: string) => void;
  setTenantInput: (value: string) => void;
  applyTenantFilter: () => string | null;
  resetFilters: () => void;
}

export function applySubscriptionFilters(
  subscriptions: StatusSubscriptionSummary[],
  { channelFilter, statusFilter, severityFilter, searchTerm, appliedTenantId }: FiltersState,
): StatusSubscriptionSummary[] {
  const normalizedSearch = searchTerm.trim().toLowerCase();

  return subscriptions.filter((item) => {
    if (channelFilter !== 'all' && item.channel !== channelFilter) return false;
    if (statusFilter !== 'all' && item.status !== statusFilter) return false;
    if (severityFilter !== 'any' && item.severityFilter !== severityFilter) return false;
    if (appliedTenantId && item.tenantId !== appliedTenantId) return false;

    if (normalizedSearch) {
      const haystack = `${item.targetMasked} ${item.createdBy}`.toLowerCase();
      if (!haystack.includes(normalizedSearch)) return false;
    }

    return true;
  });
}

export function useStatusOpsFilters({
  subscriptions,
  appliedTenantId,
  defaultTenantId,
  onAppliedTenantChange,
}: UseStatusOpsFiltersParams): UseStatusOpsFiltersResult {
  const [channelFilter, setChannelFilter] = useState<ChannelFilter>('all');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>('any');
  const [searchTerm, setSearchTerm] = useState('');
  const [tenantInput, setTenantInput] = useState<string>(appliedTenantId ?? defaultTenantId ?? '');

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

  const applyTenantFilter = useCallback(() => {
    const normalizedTenant = tenantInput.trim();
    const nextTenant = normalizedTenant.length === 0 ? null : normalizedTenant;
    onAppliedTenantChange?.(nextTenant);
    return nextTenant;
  }, [onAppliedTenantChange, tenantInput]);

  const resetFilters = useCallback(() => {
    setChannelFilter('all');
    setStatusFilter('all');
    setSeverityFilter('any');
    setSearchTerm('');
    setTenantInput('');
    onAppliedTenantChange?.(null);
  }, [onAppliedTenantChange]);

  return {
    channelFilter,
    statusFilter,
    severityFilter,
    searchTerm,
    tenantInput,
    appliedTenantId,
    filteredSubscriptions,
    setChannelFilter,
    setStatusFilter,
    setSeverityFilter,
    setSearchTerm,
    setTenantInput,
    applyTenantFilter,
    resetFilters,
  };
}
