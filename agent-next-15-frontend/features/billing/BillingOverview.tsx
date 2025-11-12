'use client';

import Link from 'next/link';
import { useMemo } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { GlassPanel, InlineTag, KeyValueList, SectionHeader, StatCard } from '@/components/ui/foundation';
import { EmptyState, SkeletonPanel } from '@/components/ui/states';
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useBillingStream } from '@/lib/queries/billing';
import { formatRelativeTime } from '@/lib/utils/time';

export function BillingOverview() {
  const { events, status } = useBillingStream();

  const subscriptionEvent = useMemo(() => events.find((event) => event.subscription), [events]);
  const invoiceEvent = useMemo(() => events.find((event) => event.invoice), [events]);
  const usageEvents = useMemo(() => events.flatMap((event) => event.usage ?? []).slice(0, 5), [events]);

  const planCode = subscriptionEvent?.subscription?.plan_code ?? 'Plan pending';
  const planStatus = subscriptionEvent?.subscription?.status ?? 'unknown';
  const seatCount = subscriptionEvent?.subscription?.seat_count ?? '—';
  const autoRenew = subscriptionEvent?.subscription?.auto_renew ? 'Enabled' : 'Disabled';
  const trialEnds = formatDate(subscriptionEvent?.subscription?.trial_ends_at);

  const usageRows = usageEvents.map((usage, index) => ({
    key: `${usage.feature_key ?? 'feature'}-${index}`,
    feature: usage.feature_key ?? 'Unknown feature',
    quantity: usage.quantity ?? '—',
    amount: usage.amount_cents != null ? formatCurrency(usage.amount_cents, invoiceEvent?.invoice?.currency ?? 'USD') : '—',
    period: formatPeriod(usage.period_start, usage.period_end),
  }));

  return (
    <section className="space-y-10">
      <SectionHeader
        eyebrow="Billing"
        title="Subscription hub"
        description="Monitor plans, invoices, usage, and live events in one glass surface."
        actions={
          <div className="flex flex-wrap items-center gap-3">
            <InlineTag tone={statusTone(status)}>{statusLabel(status)}</InlineTag>
            <Button asChild size="sm" variant="ghost">
              <Link href="/billing/plans">Manage plan</Link>
            </Button>
          </div>
        }
      />

      <div className="grid gap-6 lg:grid-cols-[1.4fr_0.6fr]">
        <div className="space-y-6">
          <GlassPanel className="space-y-4">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-foreground/50">Current plan</p>
                <p className="text-2xl font-semibold text-foreground">{planCode}</p>
                <p className="text-sm text-foreground/60">Subscription telemetry streams directly from Stripe.</p>
              </div>
              <InlineTag tone={statusTone(planStatus)}>{planStatus}</InlineTag>
            </div>
            <KeyValueList
              columns={2}
              items={[
                { label: 'Seats', value: seatCount },
                { label: 'Auto renew', value: autoRenew },
                {
                  label: 'Current period',
                  value: formatPeriod(
                    subscriptionEvent?.subscription?.current_period_start,
                    subscriptionEvent?.subscription?.current_period_end,
                  ),
                },
                { label: 'Trial ends', value: trialEnds },
              ]}
            />
            <div className="flex flex-wrap items-center gap-3">
              <StatCard label="Active seats" value={seatCount} helperText="Rounded to the nearest seat" trend={{ value: 'Realtime', tone: 'neutral' }} />
              <StatCard
                label="Plan health"
                value={planStatus}
                trend={{ value: statusLabel(status), tone: status === 'error' ? 'negative' : 'positive' }}
              />
            </div>
          </GlassPanel>

          <GlassPanel className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold text-foreground">Recent usage entries</p>
              <InlineTag tone={usageEvents.length ? 'positive' : 'default'}>{`${usageEvents.length} records`}</InlineTag>
            </div>
            {usageRows.length === 0 ? (
              <EmptyState title="No usage recorded" description="Metered features will populate this ledger once they emit events." />
            ) : (
              <Table className="text-xs">
                <TableHeader>
                  <TableRow>
                    <TableHead>Feature</TableHead>
                    <TableHead className="text-center">Quantity</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead className="text-right">Period</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {usageRows.map((row) => (
                    <TableRow key={row.key}>
                      <TableCell>{row.feature}</TableCell>
                      <TableCell className="text-center">{row.quantity}</TableCell>
                      <TableCell className="text-right">{row.amount}</TableCell>
                      <TableCell className="text-right">{row.period}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
                <TableCaption>Mirror this table with your own billing pipeline.</TableCaption>
              </Table>
            )}
            <div className="flex justify-end">
              <Button asChild size="sm" variant="outline">
                <Link href="/billing/usage">View full usage log</Link>
              </Button>
            </div>
          </GlassPanel>
        </div>

        <div className="space-y-6">
          <GlassPanel className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-foreground/50">Upcoming invoice</p>
                <p className="text-lg font-semibold text-foreground">
                  {formatCurrency(invoiceEvent?.invoice?.amount_due_cents, invoiceEvent?.invoice?.currency ?? 'USD')}
                </p>
              </div>
              <Badge variant="outline">{invoiceEvent?.invoice?.status ?? 'pending'}</Badge>
            </div>
            {invoiceEvent ? (
              <div className="space-y-2 text-sm text-foreground/70">
                <p>
                  <strong>Reason:</strong> {invoiceEvent.invoice?.billing_reason ?? 'Usage'}
                </p>
                <p>
                  <strong>Collection:</strong> {invoiceEvent.invoice?.collection_method ?? 'auto'}
                </p>
                <div className="flex flex-wrap gap-2">
                  {invoiceEvent.invoice?.hosted_invoice_url ? (
                    <Button asChild size="sm">
                      <Link href={invoiceEvent.invoice.hosted_invoice_url}>View invoice</Link>
                    </Button>
                  ) : null}
                  <Button asChild size="sm" variant="ghost">
                    <Link href="/billing/plans">Manage plan</Link>
                  </Button>
                </div>
              </div>
            ) : (
              <SkeletonPanel lines={4} />
            )}
          </GlassPanel>

          <GlassPanel className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold text-foreground">Live billing events</p>
              <InlineTag tone={statusTone(status)}>{statusLabel(status)}</InlineTag>
            </div>
            {events.length === 0 ? (
              <EmptyState
                title="Awaiting activity"
                description="Stripe events, invoices, and usage will show up here."
              />
            ) : (
              <ul className="space-y-3 text-sm text-foreground/80">
                {events.slice(0, 5).map((event) => {
                  const eventDescription = (() => {
                    if (event.invoice) {
                      return `Invoice ${event.invoice.invoice_id} · ${formatCurrency(
                        event.invoice.amount_due_cents,
                        event.invoice.currency ?? 'USD',
                      )}`;
                    }
                    if (event.usage) {
                      const total = event.usage.reduce((sum, usage) => sum + (usage.quantity ?? 0), 0);
                      return `Usage event · ${total} units`;
                    }
                    return 'System update';
                  })();

                  return (
                    <li
                      key={event.stripe_event_id}
                      className="space-y-2 rounded-xl border border-white/5 bg-white/5 px-4 py-3"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <p className="font-semibold capitalize">
                          {event.summary ?? event.event_type.replace(/\./g, ' ')}
                        </p>
                        <span className="text-xs text-foreground/50">{formatRelativeTime(event.occurred_at)}</span>
                      </div>
                      <p className="text-xs text-foreground/60">{eventDescription}</p>
                      <InlineTag tone={event.invoice ? 'positive' : 'default'}>
                        {event.event_type.replace(/\./g, ' ')}
                      </InlineTag>
                    </li>
                  );
                })}
              </ul>
            )}
            <div className="flex justify-between text-xs text-foreground/60">
              <span>Showing latest events stream</span>
              <Button asChild size="sm" variant="ghost">
                <Link href="/billing/events">View event history</Link>
              </Button>
            </div>
          </GlassPanel>
        </div>
      </div>
    </section>
  );
}

function statusTone(value: string) {
  if (!value) return 'default';
  const normalized = value.toLowerCase();
  if (['active', 'open', 'trialing', 'live'].includes(normalized)) return 'positive';
  if (['error', 'past_due', 'canceled', 'disconnected', 'degraded'].includes(normalized)) return 'warning';
  return 'default';
}

function statusLabel(status: string) {
  if (!status) return 'unknown';
  if (status === 'open') return 'live';
  return status;
}

function formatCurrency(amountCents: number | null | undefined, currency: string) {
  if (amountCents == null) return '—';
  return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(amountCents / 100);
}

function formatDate(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '—';
  return date.toLocaleDateString();
}

function formatPeriod(start?: string | null, end?: string | null) {
  if (!start && !end) return '—';
  if (!start || !end) return formatDate(start ?? end ?? undefined);
  return `${formatDate(start)} → ${formatDate(end)}`;
}
