import type { CtaConfig, MarketingFaqItem } from '@/features/marketing/types';

export const PRICING_HERO_COPY = {
  eyebrow: 'Pricing',
  title: 'Pick the runway that matches your launch.',
  description:
    'Every tier includes GPT-5 agents, FastAPI auth, billing, Starter Console, and the full marketing surface. Choose the plan that fits today and upgrade without migrations.',
  primaryCta: {
    label: 'Start building',
    href: '/register',
    intent: 'primary',
  },
  secondaryCta: {
    label: 'Chat with the team',
    href: 'mailto:founders@anythingagents.com',
    intent: 'secondary',
  },
} as const;

export const PRICING_FAQ: MarketingFaqItem[] = [
  {
    question: 'Can I move between plans without downtime?',
    answer:
      'Yes. Upgrades/downgrades are handled inside the billing workspace with optimistic UI and plan proration so tenants keep working.',
  },
  {
    question: 'Do I pay extra for billing automation?',
    answer:
      'No. Usage APIs, SSE dashboards, dispatcher workers, and retry tooling are included with every license.',
  },
  {
    question: 'What if I need annual or usage-only contracts?',
    answer:
      'Annual, commit, or usage-only deals are modeled as metadata on the Scale plan. Use the contact CTA to provision custom plan definitions.',
  },
  {
    question: 'Can I run my own payment provider?',
    answer:
      'Stripe ships by default, but you can implement any provider by extending the billing repository interfaces while keeping the UI intact.',
  },
];

export const PRICING_CTA: CtaConfig = {
  eyebrow: 'Deploy',
  title: 'Go live with predictable costs.',
  description: 'Provision the starter, invite your first users, and keep scaling with the same stack.',
  primaryCta: {
    label: 'Pick a plan',
    href: '/register',
    intent: 'primary',
  },
  secondaryCta: {
    label: 'See the console',
    href: '/agents',
    intent: 'secondary',
  },
};
