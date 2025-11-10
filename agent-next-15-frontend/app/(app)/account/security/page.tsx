// File Path: app/(app)/account/security/page.tsx
// Description: Placeholder security settings page.
// Sections:
// - SecurityPage component: Notes planned password, MFA, and audit events UI.

export const metadata = {
  title: 'Security | Anything Agents',
};

export default function SecurityPage() {
  return (
    <section className="space-y-4">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold text-slate-900">Security</h1>
        <p className="text-sm text-slate-500">
          Password changes, MFA placeholders, and recent authentication events will appear here.
        </p>
      </header>

      <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
        Security controls placeholder. Reuse server actions for password changes and session audit logs.
      </div>
    </section>
  );
}

