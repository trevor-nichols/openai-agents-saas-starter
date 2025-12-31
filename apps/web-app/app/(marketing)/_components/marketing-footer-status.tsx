'use client';

import { InlineTag } from '@/components/ui/foundation/InlineTag';
import { usePlatformStatusQuery } from '@/lib/queries/status';
import type { PlatformStatusSnapshot } from '@/types/status';

interface StatusMetric {
  label: string;
  value: string | number;
  hint: string;
}

const FALLBACK_METRICS: StatusMetric[] = [
  {
    label: 'Status',
    value: 'Unavailable',
    hint: 'Waiting for next probe.',
  },
  {
    label: 'Uptime',
    value: '—',
    hint: 'Rolling uptime reported by the status API.',
  },
  {
    label: 'Incidents',
    value: '—',
    hint: 'Open incidents across tracked services.',
  },
];

export function MarketingFooterStatus() {
  const { status } = usePlatformStatusQuery({ enabled: typeof window !== 'undefined' });
  const metrics = buildMetrics(status);
  const updatedAt = status?.overview.updatedAt ?? status?.generatedAt;
  const statusLabel = status?.overview.state?.toLowerCase() ?? '';
  const statusTone = ['healthy', 'operational', 'ok'].includes(statusLabel) ? 'positive' : 'warning';
  const statusText = metrics.map((metric) => `${metric.label}: ${metric.value}`).join(' · ');

  return (
    <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-foreground">
      <InlineTag tone={status ? statusTone : 'warning'}>Live</InlineTag>
      <p className="text-sm font-semibold">Backend telemetry</p>
      {metrics.map((metric, index) => (
        <div key={metric.label} className="flex items-center gap-2 text-xs sm:text-sm text-foreground/80">
          {index > 0 ? <span className="text-foreground/40">|</span> : null}
          <span className="uppercase tracking-[0.2em] text-foreground/50">{metric.label}</span>
          <span className="text-foreground">{metric.value}</span>
        </div>
      ))}
      <span className="text-xs text-foreground/50">
        Pulled from /api/v1/status {updatedAt ? `(${formatTimestamp(updatedAt)})` : 'every minute'}.
      </span>
      <span className="sr-only">{statusText}</span>
    </div>
  );
}

function buildMetrics(status: PlatformStatusSnapshot | null): StatusMetric[] {
  if (!status) {
    return FALLBACK_METRICS;
  }

  const uptimeMetric = status.uptimeMetrics[0];
  return [
    {
      label: 'Status',
      value: status.overview.state ?? 'Unavailable',
      hint: status.overview.description ?? 'Operational summary from status snapshot.',
    },
    {
      label: 'Uptime',
      value: uptimeMetric?.value ?? '—',
      hint: uptimeMetric?.helperText ?? 'Rolling uptime reported by the status API.',
    },
    {
      label: 'Incidents',
      value: status.incidents.length,
      hint: 'Open incidents across tracked services.',
    },
  ];
}

function formatTimestamp(timestamp?: string) {
  if (!timestamp) {
    return 'just now';
  }
  try {
    const date = new Date(timestamp);
    return date.toLocaleString();
  } catch (_error) {
    return timestamp;
  }
}
