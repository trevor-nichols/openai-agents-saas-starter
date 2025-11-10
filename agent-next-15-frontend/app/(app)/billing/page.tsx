// File Path: app/(app)/billing/page.tsx
// Description: Placeholder billing overview page.
// Sections:
// - BillingPage component: Signals future subscription, usage, and invoice modules.

export const metadata = {
  title: 'Billing | Anything Agents',
};

export default function BillingPage() {
  return (
    <section className="space-y-4">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold text-slate-900">Billing overview</h1>
        <p className="text-sm text-slate-500">
          Summaries for current plan, usage, invoices, and live billing events will live here.
        </p>
      </header>

      <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
        Billing hub placeholder. Use the billing queries and SSE hooks to populate subscription data.
      </div>
    </section>
  );
}

