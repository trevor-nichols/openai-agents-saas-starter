import { cn } from '@/lib/utils';
import type { MetricsSummary } from '../types';

interface MetricsRowProps {
  metrics: MetricsSummary[];
}

export function MetricsRow({ metrics }: MetricsRowProps) {
  if (!metrics.length) {
    return null;
  }

  return (
    <div className="rounded-2xl border border-white/5 bg-white/5 p-8 backdrop-blur-sm">
      <dl className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4 lg:gap-0">
        {metrics.map((metric, index) => (
          <div 
            key={metric.label} 
            className={cn(
              "relative flex flex-col gap-2",
              // Add horizontal breathing room so wrapped helper text doesn't crowd dividers.
              index === 0 && "lg:pr-8",
              index === metrics.length - 1 && "lg:pl-8",
              index !== 0 && index !== metrics.length - 1 && "lg:px-8",
              // Add left divider for items after the first one on large screens
              index !== 0 && "lg:before:absolute lg:before:left-0 lg:before:top-4 lg:before:bottom-4 lg:before:w-px lg:before:bg-border/40"
            )}
          >
            <dt className="text-xs font-bold uppercase tracking-wider text-muted-foreground/70">
              {metric.label}
            </dt>
            <dd className="flex flex-col gap-1">
              <span className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
                {metric.value}
              </span>
              {metric.helperText && (
                <span className="text-sm font-medium text-muted-foreground">
                  {metric.helperText}
                </span>
              )}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
