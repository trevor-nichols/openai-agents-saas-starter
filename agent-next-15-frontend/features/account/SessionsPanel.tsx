// File Path: features/account/SessionsPanel.tsx
// Description: Placeholder active sessions manager view.

export function SessionsPanel() {
  return (
    <section className="space-y-4">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold text-slate-900">Active sessions</h1>
        <p className="text-sm text-slate-500">
          Display devices, last activity, and provide revoke controls for each session.
        </p>
      </header>

      <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
        Sessions table placeholder. Use the sessions API routes wired in the data layer.
      </div>
    </section>
  );
}

