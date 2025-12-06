import { StatCard } from '@/components/ui/foundation';
import type { UptimeMetric } from '@/types/status';
import { resolveTrendTone } from '../utils/statusFormatting';
import { MetricSkeleton } from './skeletons';

interface MetricsPanelProps {
  metrics: UptimeMetric[];
  showSkeletons: boolean;
}

export function MetricsPanel({ metrics, showSkeletons }: MetricsPanelProps) {
  if (showSkeletons) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((item) => (
          <MetricSkeleton key={`metric-skeleton-${item}`} />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {metrics.map((metric) => (
        <StatCard
          key={metric.label}
          label={metric.label}
          value={metric.value}
          helperText={metric.helperText}
          trend={{ value: metric.trendValue, tone: resolveTrendTone(metric.trendTone) }}
        />
      ))}
    </div>
  );
}
