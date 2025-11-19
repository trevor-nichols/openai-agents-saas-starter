import { StatCard } from '@/components/ui/foundation/StatCard';

import type { DocMetric } from '../types';

interface MetricsStripProps {
  metrics: DocMetric[];
}

export function MetricsStrip({ metrics }: MetricsStripProps) {
  if (!metrics.length) {
    return null;
  }

  return (
    <section className="grid gap-4 md:grid-cols-4">
      {metrics.map((metric) => (
        <StatCard
          key={metric.label}
          label={metric.label}
          value={metric.value}
          helperText={metric.hint}
        />
      ))}
    </section>
  );
}
