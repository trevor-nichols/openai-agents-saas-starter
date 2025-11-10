'use client';

import React from 'react';

import type { BillingEvent, BillingStreamStatus } from '@/types/billing';

interface BillingEventsPanelProps {
  events: BillingEvent[];
  status: BillingStreamStatus;
}

export default function BillingEventsPanel({ events, status }: BillingEventsPanelProps) {
  return (
    <section className="mt-6 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-900">Billing Activity</h2>
        <span className="text-xs uppercase tracking-wide text-slate-500">{statusLabel(status)}</span>
      </div>
      {events.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">No billing updates yet. Updates will appear here in real time.</p>
      ) : (
        <ul className="mt-4 space-y-2">
          {events.map((event) => (
            <li
              key={event.stripe_event_id}
              className="rounded-md border border-slate-100 px-3 py-2 text-sm text-slate-800"
            >
              <div className="flex items-center justify-between">
                <span className="font-medium capitalize">{formatEventType(event.event_type)}</span>
                <span className="text-xs text-slate-400">{formatTimestamp(event.occurred_at)}</span>
              </div>
              {event.summary && <p className="text-xs text-slate-500">{event.summary}</p>}

              <div className="mt-2 space-y-2 text-xs text-slate-600">
                {renderSubscription(event)}
                {renderInvoice(event)}
                {renderUsage(event)}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function statusLabel(status: BillingStreamStatus): string {
  switch (status) {
    case 'open':
      return 'live';
    case 'connecting':
      return 'connecting';
    case 'error':
      return 'disconnected';
    default:
      return status;
  }
}

function formatEventType(value: string): string {
  return value.replace(/\./g, ' ');
}

function formatTimestamp(value: string): string {
  const date = new Date(value);
  return date.toLocaleString([], { hour: '2-digit', minute: '2-digit' });
}

function renderSubscription(event: BillingEvent) {
  if (!event.subscription) return null;
  const subscription = event.subscription;
  return (
    <div>
      <h3 className="font-semibold text-slate-700">Subscription</h3>
      <dl className="mt-1 grid grid-cols-2 gap-1">
        <Detail label="Plan" value={subscription.plan_code} />
        <Detail label="Status" value={subscription.status} />
        <Detail label="Seats" value={subscription.seat_count ?? '—'} />
        <Detail label="Auto renew" value={subscription.auto_renew ? 'Yes' : 'No'} />
        <Detail label="Current period" value={formatPeriod(subscription.current_period_start, subscription.current_period_end)} />
        <Detail label="Trial ends" value={formatDate(subscription.trial_ends_at)} />
        <Detail label="Cancel at" value={formatDate(subscription.cancel_at)} />
      </dl>
    </div>
  );
}

function renderInvoice(event: BillingEvent) {
  if (!event.invoice) return null;
  const invoice = event.invoice;
  return (
    <div>
      <h3 className="font-semibold text-slate-700">Invoice</h3>
      <dl className="mt-1 grid grid-cols-2 gap-1">
        <Detail label="Status" value={invoice.status} />
        <Detail label="Amount" value={formatCurrency(invoice.amount_due_cents, invoice.currency)} />
        <Detail label="Reason" value={invoice.billing_reason ?? '—'} />
        <Detail label="Collection" value={invoice.collection_method ?? '—'} />
        <Detail label="Period" value={formatPeriod(invoice.period_start, invoice.period_end)} />
        <Detail label="Invoice" value={invoice.hosted_invoice_url ? <a className="text-blue-600 hover:underline" href={invoice.hosted_invoice_url} target="_blank" rel="noreferrer">View invoice</a> : '—'} />
      </dl>
    </div>
  );
}

function renderUsage(event: BillingEvent) {
  if (!event.usage || event.usage.length === 0) return null;
  return (
    <div>
      <h3 className="font-semibold text-slate-700">Usage</h3>
      <ul className="mt-1 space-y-1">
        {event.usage.map((record) => (
          <li key={`${event.stripe_event_id}-${record.feature_key}`} className="rounded border border-slate-100 px-2 py-1">
            <div className="flex items-center justify-between">
              <span>{record.feature_key}</span>
              <span className="font-semibold">{record.quantity}</span>
            </div>
            <div className="text-[11px] text-slate-500">
              {formatPeriod(record.period_start, record.period_end)}
              {record.amount_cents != null && (
                <span className="ml-2">
                  {formatCurrency(record.amount_cents, event.invoice?.currency ?? 'usd')}
                </span>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

type DetailValue = React.ReactNode | string | number | null | undefined;

function Detail({ label, value }: { label: string; value: DetailValue }) {
  if (value === undefined || value === null || value === '') return null;
  return (
    <div>
      <dt className="text-[11px] uppercase tracking-wide text-slate-400">{label}</dt>
      <dd className="text-xs text-slate-600">{value}</dd>
    </div>
  );
}

function formatCurrency(amountCents: number, currency: string | undefined) {
  const formatter = new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency: (currency || 'usd').toUpperCase(),
    minimumFractionDigits: 2,
  });
  return formatter.format((amountCents || 0) / 100);
}

function formatDate(value?: string | null): string {
  if (!value) return '—';
  return new Date(value).toLocaleDateString();
}

function formatPeriod(start?: string | null, end?: string | null): string {
  if (!start && !end) return '—';
  if (!start || !end) return formatDate(start ?? end ?? undefined);
  return `${formatDate(start)} → ${formatDate(end)}`;
}
