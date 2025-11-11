'use client';

import Link from 'next/link';
import { useMemo } from 'react';

import { Button } from '@/components/ui/button';
import { GlassPanel, InlineTag, SectionHeader } from '@/components/ui/foundation';
import { EmptyState, SkeletonPanel } from '@/components/ui/states';
import { useBillingStream } from '@/lib/queries/billing';
import { formatRelativeTime } from '@/lib/utils/time';

export function BillingOverview() {
  const { events, status } = useBillingStream();

  const subscriptionEvent = useMemo(() => events.find((event) => event.subscription), [events]);
  const invoiceEvent = useMemo(() => events.find((event) => event.invoice), [events]);
  const usageEvents = useMemo(() => events.flatMap((event) => event.usage ?? []).slice(0, 4), [events]);

  const planCode = subscriptionEvent?.subscription?.plan_code ?? 'Plan pending';
  const planStatus = subscriptionEvent?.subscription?.status ?? 'unknown';
  const seatCount = subscriptionEvent?.subscription?.seat_count ?? '—';
  const autoRenew = subscriptionEvent?.subscription?.auto_renew ? 'Enabled' : 'Disabled';

  return (
    <section className="space-y-8">
      <SectionHeader
        eyebrow="Billing"
        title="Subscription hub"
        description="Monitor plan status, invoices, and usage without leaving the console."
        actions={
          <div className="flex items-center gap-3">
            <InlineTag tone={statusTone(status)}>{statusLabel(status)}</InlineTag>
            <Button asChild size="sm" variant="ghost">
              <Link href="/billing/plans">Manage plan</Link>
            </Button>
          </div>
        }
      />

      <div className="grid gap-6 lg:grid-cols-[1.4fr_0.6fr]">
        <GlassPanel className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-foreground/50">Current plan</p>
              <p className="text-2xl font-semibold text-foreground">{planCode}</p>
              <p className="text-sm text-foreground/60">Subscription details stream directly from Stripe.</p>
            </div>
            <InlineTag tone={statusTone(planStatus)}>{planStatus}</InlineTag>
          </div>

          <div className="grid gap-4 text-sm text-foreground/80 sm:grid-cols-2">
            <SummaryItem label="Seats" value={seatCount} />
            <SummaryItem label="Auto renew" value={autoRenew} />
            <SummaryItem
              label="Current period"
              value={
                subscriptionEvent?.subscription
                  ? formatPeriod(
                      subscriptionEvent.subscription.current_period_start,
                      subscriptionEvent.subscription.current_period_end,
                    )
                  : 'Unknown'
              }
            />
            <SummaryItem label="Trial ends" value={formatDate(subscriptionEvent?.subscription?.trial_ends_at)} />
          </div>
        </GlassPanel>

        <GlassPanel className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-foreground">Upcoming invoice</p>
            <InlineTag tone={invoiceEvent ? 'positive' : 'default'}>
              {invoiceEvent?.invoice?.status ?? 'pending'}
            </InlineTag>
          </div>
          {invoiceEvent ? (
            <div className="space-y-2 text-sm text-foreground/70">
              <p>
                Amount{' '}
                <span className="font-semibold text-foreground">
                  {formatCurrency(invoiceEvent.invoice?.amount_due_cents, invoiceEvent.invoice?.currency ?? 'USD')}
                </span>
              </p>
              <p>Reason · {invoiceEvent.invoice?.billing_reason ?? 'Usage'}</p>
              <p>Collection · {invoiceEvent.invoice?.collection_method ?? 'auto'}</p>
              {invoiceEvent.invoice?.hosted_invoice_url ? (
                <Button asChild variant="ghost" size="sm" className="px-0 text-primary">
                  <Link href={invoiceEvent.invoice.hosted_invoice_url}>View invoice</Link>
                </Button>
              ) : null}
            </div>
          ) : (
            <SkeletonPanel lines={4} />
          )}
        </GlassPanel>
      </div>

      <GlassPanel className="space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-sm font-semibold text-foreground">Recent usage entries</p>
          <InlineTag tone={usageEvents.length ? 'positive' : 'default'}>{`${usageEvents.length} records`}</InlineTag>
        </div>
        {usageEvents.length === 0 ? (
          <EmptyState
            title="No usage recorded"
            description="When metered features emit usage, they will appear here."
          />
        ) : (
          <ul className="space-y-2 text-sm text-foreground/80">
            {usageEvents.map((usage, index) => (
              <li key={`${usage.feature_key}-${index}`} className="rounded-xl border border-white/5 bg-white/5 px-4 py-3">
                <div className="flex items-center justify-between">
                  <p className="font-semibold">{usage.feature_key}</p>
                  <span className="text-xs text-foreground/60">
                    {formatPeriod(usage.period_start, usage.period_end)}
                  </span>
                </div>
                <p className="text-xs text-foreground/60">Quantity · {usage.quantity}</p>
                {usage.amount_cents != null ? (
                  <p className="text-xs text-foreground/60">
                    Amount · {formatCurrency(usage.amount_cents, invoiceEvent?.invoice?.currency ?? 'USD')}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
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
            description="Stripe subscription, invoice, and usage events will show up in real time."
          />
        ) : (
          <ul className="space-y-2 text-sm text-foreground/80">
            {events.map((event) => (
              <li key={event.stripe_event_id} className="rounded-xl border border-white/5 bg-white/5 px-4 py-3">
                <div className="flex items-center justify-between">
                  <p className="font-semibold capitalize">{event.summary ?? event.event_type.replace(/\./g, ' ')}</p>
                  <span className="text-xs text-foreground/50">{formatRelativeTime(event.occurred_at)}</span>
                </div>
                {event.invoice?.amount_due_cents ? (
                  <p className="text-xs text-foreground/60">
                    Invoice {event.invoice.invoice_id} ·
                    {formatCurrency(event.invoice.amount_due_cents, event.invoice.currency ?? 'USD')}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </GlassPanel>
    </section>
  );
}

function SummaryItem({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-[0.3em] text-foreground/50">{label}</p>
      <p className="text-base text-foreground">{value ?? '—'}</p>
    </div>
  );
}

function statusTone(value: string) {
  if (!value) return 'default';
  const normalized = value.toLowerCase();
  if (['active', 'open', 'trialing', 'live'].includes(normalized)) return 'positive';
  if (['error', 'past_due', 'canceled', 'disconnected'].includes(normalized)) return 'warning';
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
