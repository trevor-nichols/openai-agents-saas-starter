// File Path: app/(app)/agents/page.tsx
// Description: Placeholder page for Agent roster and status telemetry.
// Sections:
// - AgentsPage component: Communicates upcoming table and card layouts.

export const metadata = {
  title: 'Agents | Anything Agents',
};

export default function AgentsPage() {
  return (
    <section className="space-y-4">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold text-slate-900">Agents</h1>
        <p className="text-sm text-slate-500">
          Provide status, model metadata, and tool access for each agent. Surface handoff relationships here.
        </p>
      </header>

      <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
        Agent roster placeholder. Expect cards or tables summarizing availability and usage.
      </div>
    </section>
  );
}

