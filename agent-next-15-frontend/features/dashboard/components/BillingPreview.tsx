import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { GlassPanel, InlineTag, SectionHeader } from '@/components/ui/foundation';
import { formatRelativeTime } from '@/lib/utils/time';

import { DASHBOARD_COPY } from '../constants';
import type { BillingPreviewSummary } from '../types';
import { formatCurrency } from '../utils/formatters';

interface BillingPreviewProps {
  preview: BillingPreviewSummary;
}

function resolveTone(status: string) {
  if (!status) return 'default';
  if (status === 'active' || status === 'open' || status === 'trialing') {
    return 'positive';
  }
  if (status === 'past_due' || status === 'canceled' || status === 'error') {
    return 'warning';
  }
  return 'default';
}

export function BillingPreview({ preview }: BillingPreviewProps) {
  const { planCode, planStatus, streamStatus, nextInvoiceLabel, latestEvents } = preview;

  return (
    <GlassPanel className="space-y-6">
      <SectionHeader
        eyebrow={DASHBOARD_COPY.billingPreview.eyebrow}
        title={DASHBOARD_COPY.billingPreview.title}
        description={DASHBOARD_COPY.billingPreview.description}
        actions={
          <Button asChild size="sm" variant="ghost">
            <Link href="/billing">{DASHBOARD_COPY.billingPreview.ctaLabel}</Link>
          </Button>
        }
      />

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-foreground/60">Current plan</p>
            <p className="text-2xl font-semibold text-foreground">{planCode}</p>
          </div>
          <InlineTag tone={resolveTone(planStatus)}>{planStatus}</InlineTag>
        </div>
        <div className="flex items-center justify-between text-sm text-foreground/70">
          <span>Stream status</span>
          <InlineTag tone={resolveTone(streamStatus)}>{streamStatus}</InlineTag>
        </div>
        {nextInvoiceLabel ? (
          <div className="rounded-lg border border-white/5 bg-white/5 px-4 py-3 text-sm text-foreground/70">
            Next invoice: {nextInvoiceLabel}
          </div>
        ) : null}
      </div>

      <div className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-foreground/50">Latest events</p>
        {latestEvents.length === 0 ? (
          <div className="rounded-lg border border-dashed border-white/10 px-4 py-6 text-center text-sm text-foreground/60">
            {DASHBOARD_COPY.billingPreview.emptyEvents}
          </div>
        ) : (
          <ul className="space-y-2 text-sm">
            {latestEvents.map((event) => (
              <li key={event.stripe_event_id} className="rounded-lg border border-white/5 bg-white/5 px-4 py-3">
                <div className="flex items-center justify-between">
                  <p className="font-medium text-foreground">{event.summary ?? event.event_type}</p>
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
      </div>
    </GlassPanel>
  );
}
