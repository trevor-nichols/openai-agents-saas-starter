'use client';

import { StatCard } from '@/components/ui/foundation';

import type { StatusOpsMetrics } from '../hooks/useStatusOpsMetrics';

interface StatusOpsStatsRowProps {
  metrics: StatusOpsMetrics;
  appliedTenantId: string | null;
}

export function StatusOpsStatsRow({ metrics, appliedTenantId }: StatusOpsStatsRowProps) {
  return (
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
  );
}
