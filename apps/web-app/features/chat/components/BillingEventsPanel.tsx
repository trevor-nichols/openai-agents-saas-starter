// File Path: features/chat/components/BillingEventsPanel.tsx
// Description: Billing stream preview styled with glass components.

'use client';

import Link from 'next/link';

import { GlassPanel, InlineTag, SectionHeader } from '@/components/ui/foundation';
import { EmptyState } from '@/components/ui/states';
import { formatRelativeTime } from '@/lib/utils/time';
import type { BillingEvent, BillingStreamStatus } from '@/types/billing';

interface BillingEventsPanelProps {
  events: BillingEvent[];
  status: BillingStreamStatus;
  className?: string;
}

export function BillingEventsPanel({ events, status, className }: BillingEventsPanelProps) {
  return (
    <GlassPanel className={className}>
      <SectionHeader
        eyebrow="Billing"
        title="Live usage feed"
        description="Stripe events mirrored in real time."
        actions={<InlineTag tone={statusTone(status)}>{statusLabel(status)}</InlineTag>}
      />

      {events.length === 0 ? (
        <EmptyState
          title="Awaiting billing activity"
          description="Usage, invoices, and subscription updates will appear here."
        />
      ) : (
        <ul className="mt-6 space-y-3 text-sm text-foreground/80">
          {events.map((event) => (
            <li key={event.stripe_event_id} className="rounded-xl border border-white/5 bg-white/5 px-4 py-3">
              <div className="flex items-center justify-between gap-2">
                <p className="font-semibold capitalize">{event.summary ?? event.event_type.replace(/\./g, ' ')}</p>
                <span className="text-xs text-foreground/50">{formatRelativeTime(event.occurred_at)}</span>
              </div>
              {event.invoice?.amount_due_cents ? (
                <p className="text-xs text-foreground/60">
                  Invoice {event.invoice.invoice_id} ·
                  {formatCurrency(event.invoice.amount_due_cents, event.invoice.currency ?? 'USD')}
                </p>
              ) : null}
              {event.subscription ? (
                <div className="mt-2 grid grid-cols-2 gap-2 text-[11px] text-foreground/60">
                  <span>Plan · {event.subscription.plan_code}</span>
                  <span>Status · {event.subscription.status}</span>
                </div>
              ) : null}
              {event.invoice?.hosted_invoice_url ? (
                <div className="mt-2 text-xs">
                  <Link href={event.invoice.hosted_invoice_url} className="text-primary underline-offset-4 hover:underline">
                    View invoice
                  </Link>
                </div>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </GlassPanel>
  );
}

function statusTone(status: BillingStreamStatus) {
  if (status === 'error') return 'warning';
  if (status === 'open') return 'positive';
  return 'default';
}

function statusLabel(status: BillingStreamStatus) {
  switch (status) {
    case 'open':
      return 'live';
    case 'connecting':
      return 'connecting';
    case 'error':
      return 'error';
    default:
      return status;
  }
}

function formatCurrency(amountCents: number | undefined, currency: string) {
  if (amountCents == null) return '';
  return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(amountCents / 100);
}
