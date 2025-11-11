// File Path: app/(marketing)/page.tsx
// Description: Public landing page placeholder for the Anything Agents SaaS.
// Sections:
// - Hero Section: High-level value proposition and primary call to action.
// - Feature Highlights: Quick overview cards leading to deeper content.
// - Call to Action: Secondary CTA encouraging users to create an account.

import Link from 'next/link';

export const metadata = {
  title: 'Anything Agents | AI Agent SaaS Starter',
};

// --- LandingPage component ---
// Provides a lightweight, content-only scaffold that design can extend later.
export default function LandingPage() {
  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-16 px-6 py-16">
      {/* Hero Section */}
      <section className="grid gap-6 lg:grid-cols-[1.25fr,0.75fr] lg:items-center">
        <div className="flex flex-col gap-6">
          <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
            Launch your AI agent SaaS in days, not months.
          </h1>
          <p className="text-lg text-slate-600">
            Anything Agents ships a production-ready FastAPI backend and a modern Next.js frontend that showcase the new
            OpenAI Agents SDK. Bring your brand, plug in your providers, and go live.
          </p>
          <div className="flex flex-wrap items-center gap-4">
            <Link
              href="/login"
              className="rounded-md bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-700"
            >
              Sign in to the console
            </Link>
            <Link
              href="/pricing"
              className="rounded-md border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-slate-400 hover:text-slate-900"
            >
              View pricing plans
            </Link>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-md">
          <h2 className="text-lg font-semibold text-slate-900">What’s included?</h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-600">
            <li className="rounded-md bg-slate-50 p-3">
              Agent orchestration with triage and specialist handoffs using the latest OpenAI Agents SDK.
            </li>
            <li className="rounded-md bg-slate-50 p-3">
              Fully typed data layer powered by a generated HeyAPI client and TanStack Query hooks.
            </li>
            <li className="rounded-md bg-slate-50 p-3">Enterprise-ready auth, billing, and observability primitives.</li>
          </ul>
        </div>
      </section>

      {/* Feature Highlights */}
      <section className="grid gap-6 md:grid-cols-3">
        {[
          {
            title: 'Agent Workspace',
            description:
              'A focused chat environment that supports streaming, transcripts, and tool telemetry. Built to extend.',
            href: '/chat',
          },
          {
            title: 'Billing Control Hub',
            description:
              'Track subscriptions, usage, and invoices. Wire in Stripe or your favorite billing provider.',
            href: '/billing',
          },
          {
            title: 'Security & Compliance',
            description:
              'Manage sessions, service accounts, and audit trails with patterns ready for SOC2-ready teams.',
            href: '/account?tab=security',
          },
        ].map((feature) => (
          <Link
            key={feature.title}
            href={feature.href}
            className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm transition hover:border-slate-300 hover:shadow-md"
          >
            <h3 className="text-lg font-semibold text-slate-900">{feature.title}</h3>
            <p className="mt-2 text-sm text-slate-600">{feature.description}</p>
            <span className="mt-4 inline-flex items-center text-sm font-semibold text-slate-900">
              Explore the feature →
            </span>
          </Link>
        ))}
      </section>

      {/* Call to Action */}
      <section className="rounded-2xl bg-slate-900 px-8 py-12 text-white shadow-lg">
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-2xl font-semibold">Ready to build?</h2>
            <p className="mt-2 text-sm text-slate-100">
              Clone the starter, configure your providers, and give your customers an enterprise-grade AI experience.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <Link
              href="/register"
              className="rounded-md bg-white px-5 py-3 text-sm font-semibold text-slate-900 transition hover:bg-slate-200"
            >
              Create an account
            </Link>
            <Link
              href="/docs"
              className="rounded-md border border-white/20 px-5 py-3 text-sm font-semibold text-white transition hover:border-white/40"
            >
              Read the docs
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
