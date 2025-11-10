// File Path: app/(marketing)/pricing/page.tsx
// Description: Placeholder pricing page outlining tier structure until design delivers final content.
// Sections:
// - Metadata: Title configuration for the pricing route.
// - Pricing tiers: Basic card layout listing plan placeholders and feature summaries.

import Link from 'next/link';

export const metadata = {
  title: 'Pricing | Anything Agents',
};

const pricingTiers = [
  {
    name: 'Starter',
    price: '$49',
    cadence: 'per month',
    summary: 'Ideal for prototyping the console and onboarding your first customers.',
    features: ['Single tenant', '5k agent messages', 'Email-based auth flows'],
  },
  {
    name: 'Growth',
    price: '$199',
    cadence: 'per month',
    summary: 'Unlock team features and ship multi-tenant agent workflows.',
    features: ['Multi-tenant ready', '50k agent messages', 'Stripe billing integration'],
  },
  {
    name: 'Scale',
    price: 'Contact us',
    cadence: '',
    summary: 'For enterprise rollouts that require SSO, SLAs, and custom compliance.',
    features: ['Dedicated support', 'SOC2-aligned controls', 'Custom tool integrations'],
  },
];

export default function PricingPage() {
  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-12 px-6 py-16">
      <header className="text-center">
        <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">Pricing</h1>
        <p className="mt-4 text-base text-slate-600">
          Plans designed for early builders through enterprise launches. Pick the tier that matches your go-to-market
          timeline.
        </p>
      </header>

      <section className="grid gap-6 md:grid-cols-3">
        {pricingTiers.map((tier) => (
          <article key={tier.name} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-semibold text-slate-900">{tier.name}</h2>
            <p className="mt-3 text-sm text-slate-600">{tier.summary}</p>
            <p className="mt-6 text-3xl font-bold text-slate-900">
              {tier.price}
              {tier.cadence ? <span className="ml-1 text-base font-medium text-slate-500">{tier.cadence}</span> : null}
            </p>
            <ul className="mt-6 space-y-2 text-sm text-slate-600">
              {tier.features.map((feature) => (
                <li key={feature} className="rounded-md bg-slate-50 p-2">
                  {feature}
                </li>
              ))}
            </ul>
            <div className="mt-8">
              <Link
                href="/register"
                className="inline-flex w-full items-center justify-center rounded-md border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-900 transition hover:border-slate-300"
              >
                Choose plan
              </Link>
            </div>
          </article>
        ))}
      </section>

      <section className="rounded-2xl bg-slate-900 px-6 py-10 text-slate-100">
        <div className="mx-auto flex max-w-3xl flex-col gap-4 text-center">
          <h2 className="text-2xl font-semibold">Need a custom arrangement?</h2>
          <p className="text-sm text-slate-200">
            The Scale tier adapts to your compliance, deployment, and security requirements. Let’s align on what your
            customers expect.
          </p>
          <div className="flex justify-center">
            <Link
              href="mailto:founders@anythingagents.com"
              className="rounded-md bg-white px-5 py-3 text-sm font-semibold text-slate-900 transition hover:bg-slate-200"
            >
              Contact sales
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}

