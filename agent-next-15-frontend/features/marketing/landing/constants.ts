import { Sparkles, Shield, BarChart3, Cable } from 'lucide-react';

import type { CtaConfig, FaqItem, FeatureHighlight, ProofPoint } from './types';

export const HERO_COPY = {
  eyebrow: 'Anything Agents',
  title: 'Launch an AI agent console your customers can trust.',
  description:
    'Bundle a GPT-5 powered workspace, enterprise auth, and billing-ready APIs into one shippable SaaS starter. Drop in your brand and keep scaling.',
  primaryCta: {
    label: 'Book a console demo',
    href: '/register',
    intent: 'primary',
  },
  secondaryCta: {
    label: 'Explore the docs',
    href: '/docs',
    intent: 'secondary',
  },
} as const;

export const PROOF_POINTS: ProofPoint[] = [
  {
    label: 'Backed by FastAPI + Next.js 15',
    value: 'Modern stack with shared auth and telemetry.',
  },
  {
    label: 'Agents SDK v0.5.0',
    value: 'GPT-5 reasoning, handoffs, and memory baked in.',
  },
  {
    label: 'Stripe-ready billing',
    value: 'Plan catalog + usage + retry workers wired.',
  },
];

export const FEATURE_HIGHLIGHTS: FeatureHighlight[] = [
  {
    icon: Sparkles,
    title: 'Agent workspace',
    description: 'Streaming chat, conversation archive, and tool telemetry unified inside the agents feature directory.',
    bullets: ['Multi-agent routing + GPT-5 sessions', 'Drawer exports + audit trails', 'Tool registry insights'],
  },
  {
    icon: Shield,
    title: 'Enterprise guardrails',
    description: 'Ed25519 auth, JWT refresh, tenant-scoped RBAC, and service-account lifecycle automation.',
    bullets: ['Verified scopes on every API router', 'Redis-backed refresh token cache', 'Service accounts with CLI tooling'],
  },
  {
    icon: BarChart3,
    title: 'Billing + analytics',
    description: 'Plan catalogs, usage metering, SSE billing streams, and dashboard widgets ready for your KPIs.',
    bullets: ['Async Stripe dispatcher + retry worker', 'Usage recording API + UI', 'TanStack Query billing hooks'],
  },
  {
    icon: Cable,
    title: 'Operations toolkit',
    description: 'Health checks, status page, and CLI workflows keep ops-aware teams in sync from day zero.',
    bullets: ['Status snapshot + RSS feeds', 'Starter CLI env + key rotation', 'Observability middleware + metrics'],
  },
];

export const FAQ_ITEMS: FaqItem[] = [
  {
    question: 'Can I self-host the backend + frontend?',
    answer:
      'Yes. The repo ships Docker + Compose targets plus the Starter CLI to hydrate env files in dev, preview, and prod. Deploy both stacks anywhere Docker + Postgres run.',
  },
  {
    question: 'How customizable is the UI kit?',
    answer:
      'All surfaces use shadcn/ui primitives, Tailwind tokens, and the glass foundation kit. Extend components under `components/ui` or feature-scoped directories without fighting bespoke CSS.',
  },
  {
    question: 'What’s the story for pricing + billing integrations?',
    answer:
      'Stripe adapters, plan catalogs, usage APIs, and SSE-powered dashboards are implemented today. Swap in a different billing provider by extending the repository contracts.',
  },
  {
    question: 'Do you support enterprise security reviews?',
    answer:
      'The project documents threat models, Vault transit workflows, and SOC2-aligned controls. Service accounts, audit logs, and tenant settings panels are already wired.',
  },
];

export const CTA_CONFIG: CtaConfig = {
  title: 'Ready to deploy your agent platform?',
  description: 'Clone the repo, run the Starter CLI, and go live with auth, billing, and GPT-5 agents already wired.',
  primaryCta: {
    label: 'Get started',
    href: '/register',
    intent: 'primary',
  },
  secondaryCta: {
    label: 'Chat with us',
    href: '/agents',
    intent: 'secondary',
  },
};
