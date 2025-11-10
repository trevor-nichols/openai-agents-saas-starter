// File Path: app/(app)/dashboard/page.tsx
// Description: Placeholder dashboard surface for authenticated users.
// Sections:
// - DashboardPage component: Signals upcoming KPI and quick-action widgets.

export const metadata = {
  title: 'Dashboard | Anything Agents',
};

export default function DashboardPage() {
  return (
    <section className="space-y-4">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold text-slate-900">Tenant overview</h1>
        <p className="text-sm text-slate-500">
          We&apos;ll populate this area with conversation stats, active agents, and quick actions.
        </p>
      </header>

      <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
        Dashboard widgets coming soon. Reference the UI milestone to prioritize KPIs.
      </div>
    </section>
  );
}

