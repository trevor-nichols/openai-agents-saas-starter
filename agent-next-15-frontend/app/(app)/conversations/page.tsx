// File Path: app/(app)/conversations/page.tsx
// Description: Placeholder conversations list that will evolve into a data table.
// Sections:
// - ConversationsPage component: Indicates future filtering and audit tooling.

export const metadata = {
  title: 'Conversations | Anything Agents',
};

export default function ConversationsPage() {
  return (
    <section className="space-y-4">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold text-slate-900">Conversations</h1>
        <p className="text-sm text-slate-500">
          Track live and historical conversations. Table layout, filtering, and exports will ship in this view.
        </p>
      </header>

      <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
        Conversation table placeholder. Refer to the UI milestone for required columns and controls.
      </div>
    </section>
  );
}

