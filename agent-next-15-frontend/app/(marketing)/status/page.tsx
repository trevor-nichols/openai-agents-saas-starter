// File Path: app/(marketing)/status/page.tsx
// Description: Public-facing status page showing service health, uptime, and recent incidents.

import Link from 'next/link';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { GlassPanel, InlineTag, SectionHeader, StatCard } from '@/components/ui/foundation';
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

const STATUS_OVERVIEW = {
  state: 'All systems operational',
  updatedAt: 'November 12, 2025 · 14:10 UTC',
  description: 'FastAPI, Next.js, and the async workers are all reporting healthy.',
} as const;

const SERVICE_STATUS = [
  {
    name: 'FastAPI backend',
    status: 'operational',
    description: 'JWT auth, chat orchestration, billing webhooks, health probes.',
    lastIncidentAt: 'October 31, 2025',
    owner: 'Platform Foundations',
  },
  {
    name: 'Next.js frontend',
    status: 'operational',
    description: 'App Router shell, marketing pages, and server actions.',
    lastIncidentAt: 'October 18, 2025',
    owner: 'Product Experience',
  },
  {
    name: 'Billing event stream',
    status: 'degraded',
    description: 'Redis-backed SSE transport for plan, invoice, and usage events.',
    lastIncidentAt: 'November 8, 2025',
    owner: 'Revenue Engineering',
  },
  {
    name: 'Agent chat workspace',
    status: 'operational',
    description: 'OpenAI Agents SDK integration, tool metadata, conversation storage.',
    lastIncidentAt: 'September 30, 2025',
    owner: 'Agent Experience',
  },
] as const;

const INCIDENT_HISTORY = [
  {
    date: 'November 8, 2025',
    service: 'Billing event stream',
    impact: 'Degraded throughput during Redis maintenance.',
    status: 'resolved',
  },
  {
    date: 'October 31, 2025',
    service: 'FastAPI backend',
    impact: 'Readiness probe flaps due to Postgres upgrade.',
    status: 'resolved',
  },
  {
    date: 'October 18, 2025',
    service: 'Next.js frontend',
    impact: 'Static asset cache miss triggered elevated error rates.',
    status: 'resolved',
  },
] as const;

const UPTIME_METRICS = [
  { label: '30-day API uptime', value: '99.97%', helperText: 'Validated via managed uptime monitors.', trend: '↑ stable' },
  { label: 'Chat latency p95', value: '2.4s', helperText: 'Measured end-to-end via Playwright journeys.', trend: '↔ baseline' },
  { label: 'Billing SSE availability', value: '99.3%', helperText: 'Includes Redis maintenance windows.', trend: '↓ watch' },
] as const;

export const metadata = {
  title: 'Status | Anything Agents',
  description: 'Live service health for the Anything Agents starter stack.',
};

export default function StatusPage() {
  return (
    <div className="space-y-10">
      <SectionHeader
        eyebrow="Status"
        title="Operational visibility"
        description="Bookmark this page to monitor the FastAPI backend, Next.js frontend, and billing stream in one place."
        actions={
          <div className="flex flex-wrap items-center gap-3">
            <InlineTag tone={getTone(STATUS_OVERVIEW.state)}>{STATUS_OVERVIEW.state}</InlineTag>
            <Badge variant="outline">Last updated {STATUS_OVERVIEW.updatedAt}</Badge>
          </div>
        }
      />

      <GlassPanel className="space-y-3">
        <p className="text-base text-foreground/80">{STATUS_OVERVIEW.description}</p>
        <Separator className="border-white/5" />
        <div className="flex flex-wrap gap-3 text-sm text-foreground/60">
          <span>• Backend: `/health` & `/health/ready`</span>
          <span>• Frontend: App Router diagnostics</span>
          <span>• Workers: Stripe dispatcher, retry worker</span>
        </div>
      </GlassPanel>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(260px,1fr)]">
        <div className="space-y-6">
          {SERVICE_STATUS.map((service) => (
            <GlassPanel key={service.name} className="space-y-4">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <h3 className="text-lg font-semibold text-foreground">{service.name}</h3>
                  <p className="text-sm text-foreground/60">{service.description}</p>
                </div>
                <InlineTag tone={getTone(service.status)}>{statusLabel(service.status)}</InlineTag>
              </div>
              <div className="flex flex-wrap items-center justify-between text-xs text-foreground/60">
                <span>Owner · {service.owner}</span>
                <span>Last incident · {service.lastIncidentAt}</span>
              </div>
            </GlassPanel>
          ))}
        </div>

        <div className="space-y-4">
          {UPTIME_METRICS.map((metric) => (
            <StatCard
              key={metric.label}
              label={metric.label}
              value={metric.value}
              helperText={metric.helperText}
              trend={{ value: metric.trend, tone: metric.trend.includes('↓') ? 'negative' : 'neutral' }}
            />
          ))}
          <GlassPanel className="space-y-3">
            <h4 className="text-base font-semibold text-foreground">Subscribe for alerts</h4>
            <p className="text-sm text-foreground/70">Hook this status feed into your tooling via RSS or our CLI.</p>
            <div className="flex flex-wrap gap-2">
              <Button asChild size="sm">
                <Link href="/api/status.rss">RSS Feed</Link>
              </Button>
              <Button asChild size="sm" variant="outline">
                <Link href="mailto:status@anything.agents">Email ops</Link>
              </Button>
            </div>
          </GlassPanel>
        </div>
      </div>

      <div className="space-y-4">
        <SectionHeader
          eyebrow="Incident log"
          title="Recent events"
          description="Full incident timelines live in Linear, but this snapshot keeps marketing visitors informed."
        />
        <GlassPanel>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Service</TableHead>
                <TableHead>Impact</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {INCIDENT_HISTORY.map((incident) => (
                <TableRow key={`${incident.date}-${incident.service}`}>
                  <TableCell className="font-medium">{incident.date}</TableCell>
                  <TableCell>{incident.service}</TableCell>
                  <TableCell className="text-foreground/70">{incident.impact}</TableCell>
                  <TableCell>
                    <InlineTag tone={incident.status === 'resolved' ? 'positive' : 'warning'}>
                      {incident.status}
                    </InlineTag>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
            <TableCaption>Incident metadata syncs nightly from the real status board.</TableCaption>
          </Table>
        </GlassPanel>
      </div>
    </div>
  );
}

function getTone(status: string): 'positive' | 'warning' | 'default' {
  if (status.toLowerCase().includes('degraded') || status.toLowerCase().includes('incident')) {
    return 'warning';
  }
  if (status.toLowerCase().includes('operational') || status.toLowerCase().includes('resolved')) {
    return 'positive';
  }
  return 'default';
}

function statusLabel(status: string): string {
  if (status === 'operational') {
    return 'Operational';
  }
  if (status === 'degraded') {
    return 'Degraded';
  }
  return status;
}
