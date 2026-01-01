import { useCallback, useMemo, useState } from 'react';

import {
  DEFAULT_TENANT_STATUS_FILTER,
  TENANT_STATUS_OPTIONS,
  type TenantStatusFilter,
} from '../constants';
import { resolveStatusFilter } from '../utils';

interface UseTenantOpsFiltersResult {
  statusFilter: TenantStatusFilter;
  query: string;
  appliedStatus: TenantStatusFilter;
  appliedQuery: string;
  appliedStatusLabel: string;
  appliedFilters: {
    status: ReturnType<typeof resolveStatusFilter>;
    q: string | undefined;
  };
  setStatusFilter: (value: TenantStatusFilter) => void;
  setQuery: (value: string) => void;
  applyFilters: () => void;
  resetFilters: () => void;
}

export function useTenantOpsFilters(): UseTenantOpsFiltersResult {
  const [statusFilter, setStatusFilter] = useState<TenantStatusFilter>(DEFAULT_TENANT_STATUS_FILTER);
  const [query, setQuery] = useState('');
  const [appliedStatus, setAppliedStatus] = useState<TenantStatusFilter>(DEFAULT_TENANT_STATUS_FILTER);
  const [appliedQuery, setAppliedQuery] = useState('');

  const appliedStatusLabel = useMemo(
    () => TENANT_STATUS_OPTIONS.find((option) => option.value === appliedStatus)?.label ?? 'Active',
    [appliedStatus],
  );

  const appliedFilters = useMemo(
    () => ({
      status: resolveStatusFilter(appliedStatus),
      q: appliedQuery || undefined,
    }),
    [appliedQuery, appliedStatus],
  );

  const applyFilters = useCallback(() => {
    setAppliedStatus(statusFilter);
    setAppliedQuery(query.trim());
  }, [query, statusFilter]);

  const resetFilters = useCallback(() => {
    setStatusFilter(DEFAULT_TENANT_STATUS_FILTER);
    setQuery('');
    setAppliedStatus(DEFAULT_TENANT_STATUS_FILTER);
    setAppliedQuery('');
  }, []);

  return {
    statusFilter,
    query,
    appliedStatus,
    appliedQuery,
    appliedStatusLabel,
    appliedFilters,
    setStatusFilter,
    setQuery,
    applyFilters,
    resetFilters,
  };
}
