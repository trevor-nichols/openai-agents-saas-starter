import Link from 'next/link';
import { connection } from 'next/server';

import { Button } from '@/components/ui/button';
import { InlineTag } from '@/components/ui/foundation/InlineTag';
import { SectionHeader } from '@/components/ui/foundation/SectionHeader';
import type { PlatformStatusResponse } from '@/lib/api/client/types.gen';

import { MARKETING_FOOTER_COLUMNS, MARKETING_SOCIAL_LINKS } from './nav-links';

interface MarketingFooterProps {
  status?: PlatformStatusResponse | null;
}

export async function MarketingFooter({ status }: MarketingFooterProps) {
  await connection();

  const updatedAt = status?.overview?.updated_at ?? status?.generated_at;
  const uptimeMetric = status?.uptime_metrics?.[0];
  const metrics = [
    {
      label: 'Status',
      value: status?.overview?.state ?? 'Unavailable',
      hint: status
        ? status?.overview?.description ?? 'Operational summary from status snapshot.'
        : 'Waiting for next probe.',
    },
    {
      label: 'Uptime',
      value: uptimeMetric?.value ?? '—',
      hint: uptimeMetric?.helper_text ?? 'Rolling uptime reported by the status API.',
    },
    {
      label: 'Incidents',
      value: status ? status.incidents.length : '—',
      hint: 'Open incidents across tracked services.',
    },
  ];

  const statusLabel = status?.overview?.state?.toLowerCase() ?? '';
  const statusTone = ['healthy', 'operational', 'ok'].includes(statusLabel) ? 'positive' : 'warning';
  const statusText = metrics.map((metric) => `${metric.label}: ${metric.value}`).join(' · ');

  return (
    <footer className="border-t border-white/10 bg-background/80 py-12 text-sm text-foreground/80 backdrop-blur-glass">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-6">
        <SectionHeader
          eyebrow="Ship faster"
          title="Enterprise-ready out of the box"
          description="Every clone inherits the authenticated shell, TanStack data layer, and production-grade agent flows."
          actions={
            <Button asChild size="sm" className="rounded-full">
              <Link href="/contact">Talk to us</Link>
            </Button>
          }
        />

        <div className="grid gap-8 sm:grid-cols-3">
          {MARKETING_FOOTER_COLUMNS.map((column) => (
            <div key={column.title} className="flex flex-col gap-3">
              <p className="text-xs font-semibold uppercase tracking-[0.3em] text-foreground/50">{column.title}</p>
              <ul className="space-y-2">
                {column.links.map((link) => (
                  <li key={link.href}>
                    <Link href={link.href} className="text-foreground/70 transition hover:text-foreground">
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-foreground">
          <InlineTag tone={statusTone}>Live</InlineTag>
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

        <div className="flex flex-col gap-4 border-t border-white/10 pt-6 text-xs text-foreground/60 sm:flex-row sm:items-center sm:justify-between">
          <p>&copy; {new Date().getFullYear()} Acme. All rights reserved.</p>
          <div className="flex flex-wrap items-center gap-4">
            {MARKETING_SOCIAL_LINKS.map((link) => (
              <Link
                key={link.label}
                href={link.href}
                className="transition hover:text-foreground"
                target={link.external ? '_blank' : undefined}
                rel={link.external ? 'noreferrer' : undefined}
              >
                {link.label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
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
