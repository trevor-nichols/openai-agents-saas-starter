import { useCallback, useMemo, useState } from 'react';

import type { TenantAccountOperatorSummary } from '@/types/tenantAccount';

interface UseTenantOpsSelectionParams {
  tenants: TenantAccountOperatorSummary[];
  isMobile: boolean;
}

interface UseTenantOpsSelectionResult {
  selectedTenantId: string | null;
  resolvedTenantId: string | null;
  selectedTenantSummary: TenantAccountOperatorSummary | null;
  detailOpen: boolean;
  setDetailOpen: (open: boolean) => void;
  selectTenant: (tenantId: string) => void;
  resetSelection: () => void;
  openDetails: (tenantId: string) => void;
}

export function useTenantOpsSelection({
  tenants,
  isMobile,
}: UseTenantOpsSelectionParams): UseTenantOpsSelectionResult {
  const [activeTenantId, setActiveTenantId] = useState<string | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);

  const selectedTenantId = useMemo(() => {
    if (activeTenantId && tenants.some((tenant) => tenant.id === activeTenantId)) {
      return activeTenantId;
    }
    return null;
  }, [activeTenantId, tenants]);

  const resolvedTenantId = useMemo(
    () => selectedTenantId ?? tenants[0]?.id ?? null,
    [selectedTenantId, tenants],
  );

  const selectedTenantSummary = useMemo(
    () => tenants.find((tenant) => tenant.id === resolvedTenantId) ?? null,
    [resolvedTenantId, tenants],
  );

  const selectTenant = useCallback((tenantId: string) => {
    setActiveTenantId(tenantId);
  }, []);

  const resetSelection = useCallback(() => {
    setActiveTenantId(null);
  }, []);

  const openDetails = useCallback(
    (tenantId: string) => {
      setActiveTenantId(tenantId);
      if (isMobile) {
        setDetailOpen(true);
      }
    },
    [isMobile],
  );

  return {
    selectedTenantId,
    resolvedTenantId,
    selectedTenantSummary,
    detailOpen,
    setDetailOpen,
    selectTenant,
    resetSelection,
    openDetails,
  };
}
