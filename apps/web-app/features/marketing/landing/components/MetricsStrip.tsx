import { GlassPanel, SectionHeader, StatCard } from '@/components/ui/foundation';

import type { LandingMetrics } from '../types';

interface MetricsStripProps {
  metrics: LandingMetrics;
  isLoading: boolean;
  showHeader?: boolean;
}

export function MetricsStrip({ metrics, isLoading, showHeader = true }: MetricsStripProps) {
  return (
    <section className="space-y-6">
      {showHeader ? (
        <SectionHeader
          eyebrow="Operations"
          title="Transparent health telemetry"
          description="Live uptime metrics, billing coverage, and incident feeds keep operators informed—directly on the marketing site."
        />
      ) : null}
      <div className="grid gap-4 md:grid-cols-4">
        {metrics.statusMetrics.map((metric) => (
          <StatCard
            key={metric.label}
            label={metric.label}
            value={isLoading ? '—' : metric.value}
            helperText={metric.helperText}
          />
        ))}
        {metrics.billingSummary ? (
          <GlassPanel className="space-y-2 border border-primary/20">
            <p className="text-xs uppercase tracking-[0.3em] text-foreground/50">{metrics.billingSummary.label}</p>
            <p className="text-3xl font-semibold text-foreground">{metrics.billingSummary.value}</p>
            <p className="text-sm text-foreground/70">{metrics.billingSummary.helperText}</p>
          </GlassPanel>
        ) : null}
      </div>
    </section>
  );
}
