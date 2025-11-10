// File Path: app/(app)/billing/plans/page.tsx
// Description: Placeholder self-serve plan management page.
// Sections:
// - BillingPlansPage component: Points to upcoming upgrade/downgrade workflows.

export const metadata = {
  title: 'Billing Plans | Anything Agents',
};

export default function BillingPlansPage() {
  return (
    <section className="space-y-4">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold text-slate-900">Manage your plan</h1>
        <p className="text-sm text-slate-500">
          Fetch plan catalog and enable upgrade/downgrade actions with confirmation dialogs.
        </p>
      </header>

      <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
        Plan selection placeholder. Wire up Shadcn dialog + form for plan changes.
      </div>
    </section>
  );
}

