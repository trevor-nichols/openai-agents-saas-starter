import type { CtaConfig, MarketingFaqItem } from '@/features/marketing/types';

export const PRICING_HERO_COPY = {
  eyebrow: 'Pricing',
  title: 'Scale from prototype to enterprise without rewriting your stack.',
  description:
    'Choose a plan that matches your launch stage. Every tier ships GPT-5 agents, FastAPI auth, and billing automation out of the box.',
  primaryCta: {
    label: 'Start building',
    href: '/register',
    intent: 'primary',
  },
  secondaryCta: {
    label: 'Talk to us',
    href: 'mailto:founders@anythingagents.com',
    intent: 'secondary',
  },
} as const;

export const PRICING_FAQ: MarketingFaqItem[] = [
  {
    question: 'Can I change plans later?',
    answer: 'Yes. Tenants can upgrade/downgrade directly from the billing workspace. Plan proration and usage limits are enforced through the billing services.',
  },
  {
    question: 'Do you support annual contracts?',
    answer: 'Annual and multi-year agreements are handled via the Scale plan. Use the contact CTA to reach the team and lock in custom terms.',
  },
  {
    question: 'What payment providers are supported?',
    answer: 'Stripe is wired today, but the billing repository pattern lets you plug in your provider of choice while keeping the UI untouched.',
  },
  {
    question: 'How are agent message limits enforced?',
    answer: 'Usage records flow through the billing usage API and appear in the dashboard widgets. Exports + retries are handled by the async worker.',
  },
];

export const PRICING_CTA: CtaConfig = {
  eyebrow: 'Deploy',
  title: 'Ready to upgrade your agent platform?',
  description: 'Provision the console in minutes, wire your providers, and invite your first customers with enterprise guardrails already enabled.',
  primaryCta: {
    label: 'Launch the console',
    href: '/register',
    intent: 'primary',
  },
  secondaryCta: {
    label: 'Schedule a walkthrough',
    href: '/agents',
    intent: 'secondary',
  },
};
