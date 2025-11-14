import { StatCard } from '@/components/ui/foundation';
import { ErrorState, SkeletonPanel } from '@/components/ui/states';

import type { DashboardKpi } from '../types';

interface KpiGridProps {
  kpis: DashboardKpi[];
  isLoading: boolean;
  error?: string | null;
}

export function KpiGrid({ kpis, isLoading, error }: KpiGridProps) {
  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 3 }).map((_, index) => (
          <SkeletonPanel key={index} lines={5} />
        ))}
      </div>
    );
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {kpis.map((kpi) => (
        <StatCard
          key={kpi.id}
          label={kpi.label}
          value={kpi.value}
          helperText={kpi.helperText}
          icon={kpi.icon}
          trend={kpi.trend}
        />
      ))}
    </div>
  );
}
