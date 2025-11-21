import { StatCard } from '@/components/ui/foundation/StatCard';

import type { MetricsSummary } from '../types';

interface MetricsRowProps {
  metrics: MetricsSummary[];
}

export function MetricsRow({ metrics }: MetricsRowProps) {
  if (!metrics.length) {
    return null;
  }

  return (
    <section className="grid gap-4 md:grid-cols-4">
      {metrics.map((metric) => (
        <StatCard key={metric.label} label={metric.label} value={metric.value} helperText={metric.helperText} />
      ))}
    </section>
  );
}
