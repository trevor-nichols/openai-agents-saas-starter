// File Path: app/(marketing)/features/page.tsx
// Description: Placeholder feature overview page summarizing product capabilities.
// Sections:
// - Metadata: Sets the document title.
// - Feature grid: Highlights core areas aligned with the milestone plan.

export const metadata = {
  title: 'Features | Anything Agents',
};

const featureSections = [
  {
    title: 'Agent Orchestration',
    description:
      'Triage complex requests across specialist agents, tools, and handoffs. Configure bespoke instructions without touching backend plumbing.',
  },
  {
    title: 'Observability Built-In',
    description:
      'Trace every run, tool invocation, and billing event. Export structured logs and metrics for your preferred monitoring stack.',
  },
  {
    title: 'Secure By Default',
    description:
      'JWT-backed auth flows, session management, and service account issuance are production-ready from day one.',
  },
  {
    title: 'Billing Ready',
    description:
      'Stripe-friendly pricing tiers, subscription management, and usage reporting—so you can charge from the first customer.',
  },
  {
    title: 'Type-Safe Frontend',
    description:
      'Generated SDK, TanStack Query patterns, and shared hooks that help your team ship consistent UI quickly.',
  },
  {
    title: 'Extensible Tooling',
    description:
      'Bring your own external APIs or MCP servers. Register tools once and expose them through the same agent interfaces.',
  },
];

export default function FeaturesPage() {
  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-12 px-6 py-16">
      <header className="space-y-4 text-center">
        <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">Capabilities that scale with you</h1>
        <p className="text-base text-slate-600">
          Each module in the starter is designed to evolve from prototype to production without rewriting the foundation.
        </p>
      </header>

      <section className="grid gap-6 md:grid-cols-2">
        {featureSections.map((section) => (
          <article key={section.title} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-semibold text-slate-900">{section.title}</h2>
            <p className="mt-3 text-sm text-slate-600">{section.description}</p>
          </article>
        ))}
      </section>
    </div>
  );
}

