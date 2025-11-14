import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { InlineTag } from '@/components/ui/foundation/InlineTag';
import { KeyValueList } from '@/components/ui/foundation/KeyValueList';
import { SectionHeader } from '@/components/ui/foundation/SectionHeader';
import type { HealthResponse } from '@/lib/api/client/types.gen';

import { MARKETING_FOOTER_COLUMNS, MARKETING_SOCIAL_LINKS } from './nav-links';

interface MarketingFooterProps {
  health?: HealthResponse | null;
}

export function MarketingFooter({ health }: MarketingFooterProps) {
  const metrics = [
    {
      label: 'Status',
      value: health?.status ?? 'Unavailable',
      hint: health ? `Updated ${formatTimestamp(health.timestamp)}` : 'Waiting for next probe.',
    },
    {
      label: 'Version',
      value: health?.version ?? '—',
      hint: 'Backend semantic version reported by /health.',
    },
    {
      label: 'Uptime',
      value: formatUptime(health?.uptime),
      hint: 'Process uptime sourced from the API payload.',
    },
  ];

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

        <div className="grid gap-8 md:grid-cols-[2fr,1fr]">
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

          <div className="rounded-3xl border border-white/10 bg-white/5 p-6 text-foreground">
            <div className="flex items-center gap-2">
              <InlineTag tone="positive">Live</InlineTag>
              <p className="text-sm font-semibold">Backend telemetry</p>
            </div>
            <p className="mt-2 text-xs text-foreground/60">
              Pulled directly from <code className="font-mono text-xs">/api/health</code> every minute.
            </p>
            <KeyValueList items={metrics} className="mt-6" />
          </div>
        </div>

        <div className="flex flex-col gap-4 border-t border-white/10 pt-6 text-xs text-foreground/60 sm:flex-row sm:items-center sm:justify-between">
          <p>&copy; {new Date().getFullYear()} Anything Agents. All rights reserved.</p>
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

function formatUptime(uptime?: number | null) {
  if (!uptime || uptime <= 0) {
    return '—';
  }
  const hours = Math.floor(uptime / 3600);
  const minutes = Math.floor((uptime % 3600) / 60);
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m`;
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
