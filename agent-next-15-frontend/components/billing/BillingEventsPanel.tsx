'use client';

import React from 'react';

import type { BillingEvent, BillingStreamStatus } from '@/hooks/useBillingStream';

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
                <span className="font-medium">{event.event_type}</span>
                <span className="text-xs text-slate-400">
                  {new Date(event.occurred_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
              {event.summary && (
                <p className="text-xs text-slate-500">{event.summary}</p>
              )}
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
