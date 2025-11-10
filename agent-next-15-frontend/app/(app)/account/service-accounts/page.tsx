// File Path: app/(app)/account/service-accounts/page.tsx
// Description: Placeholder page for managing service account tokens.
// Sections:
// - ServiceAccountsPage component: Highlights upcoming issuance/revocation UX.

export const metadata = {
  title: 'Service Accounts | Anything Agents',
};

export default function ServiceAccountsPage() {
  return (
    <section className="space-y-4">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold text-slate-900">Service accounts</h1>
        <p className="text-sm text-slate-500">
          Generate, rotate, and revoke service account tokens for automation and partner integrations.
        </p>
      </header>

      <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
        Service account manager placeholder. Hook into the existing service account API routes.
      </div>
    </section>
  );
}

