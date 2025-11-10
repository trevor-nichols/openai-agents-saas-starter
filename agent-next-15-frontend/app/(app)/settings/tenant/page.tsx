// File Path: app/(app)/settings/tenant/page.tsx
// Description: Placeholder tenant settings page.
// Sections:
// - TenantSettingsPage component: Placeholder message referencing upcoming configuration UI.

export const metadata = {
  title: 'Tenant Settings | Anything Agents',
};

export default function TenantSettingsPage() {
  return (
    <section className="space-y-4">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold text-slate-900">Tenant settings</h1>
        <p className="text-sm text-slate-500">
          Configure tenant metadata, billing contacts, and webhook endpoints from this dashboard.
        </p>
      </header>

      <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
        Tenant settings placeholder. Decide on tabs or sections once product requirements finalize.
      </div>
    </section>
  );
}

