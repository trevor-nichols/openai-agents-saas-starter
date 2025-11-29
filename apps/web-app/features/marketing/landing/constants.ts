import { Sparkles, Shield, BarChart3, Cable } from 'lucide-react';

import type { CtaConfig, FaqItem, FeatureHighlight, ProofPoint } from './types';

export const HERO_COPY = {
  eyebrow: 'OpenAI Agent Starter',
  title: 'Ship your GPT-5 agent console without rebuilding the stack.',
  description:
    'Use the production FastAPI + Next.js 16 starter that already wires GPT-5 agents, Ed25519 auth, billing, and ops tooling. Clone it, drop in your brand, and launch.',
  primaryCta: {
    label: 'Launch the console',
    href: '/register',
    intent: 'primary',
  },
  secondaryCta: {
    label: 'Preview the docs',
    href: '/docs',
    intent: 'secondary',
  },
} as const;

export const PROOF_POINTS: ProofPoint[] = [
  {
    label: 'Full-stack acceleration',
    value: 'Shared auth, telemetry, and CLI scripts across FastAPI + Next.js 16.',
  },
  {
    label: 'Security-first defaults',
    value: 'Ed25519 JWTs, tenant RBAC, service accounts, and Vault-ready keys.',
  },
  {
    label: 'Billing + usage automation',
    value: 'Stripe catalog, usage APIs, and SSE dashboards already enabled.',
  },
];

export const FEATURE_HIGHLIGHTS: FeatureHighlight[] = [
  {
    icon: Sparkles,
    title: 'Agent workspace',
    description: 'Chat streaming, catalog search, transcripts, and tool telemetry live in one feature directory.',
    bullets: ['Multi-agent routing + GPT-5 memory', 'Drawer exports + audit trails', 'Tool registry insights'],
  },
  {
    icon: Shield,
    title: 'Enterprise guardrails',
    description: 'Ed25519 auth, refresh tokens, tenant RBAC, and service-account lifecycle automation.',
    bullets: ['Verified scopes on every router', 'Redis-backed refresh tokens', 'CLI-managed service accounts'],
  },
  {
    icon: BarChart3,
    title: 'Billing & analytics',
    description: 'Plan catalogs, usage metering, SSE billing streams, and KPI-ready UI panels.',
    bullets: ['Async Stripe dispatcher + retry worker', 'Usage recording API and hooks', 'Dashboard widgets powered by TanStack'],
  },
  {
    icon: Cable,
    title: 'Operations toolkit',
    description: 'Health checks, status page, and Starter CLI run side-by-side so ops is never an afterthought.',
    bullets: ['Status snapshot + RSS feeds', 'Starter CLI env + key rotation', 'Observability middleware + Prom metrics'],
  },
];

export const FAQ_ITEMS: FaqItem[] = [
  {
    question: 'How fast can I launch with this starter?',
    answer:
      'Clone the repo, run the Starter CLI to hydrate env files, and deploy the FastAPI + Next.js stacks with Docker or your preferred CI. Most teams see a branded console live in under a week.',
  },
  {
    question: 'Can I swap GPT-5 or add my own tools?',
    answer:
      'Yes. Agents register through the OpenAI Agents SDK config and tools flow through the registry. You can point to other LLM endpoints or custom MCP tools without touching the UI.',
  },
  {
    question: 'Is Stripe required?',
    answer:
      'Stripe adapters ship ready-to-use, but the billing repositories are provider-agnostic. Implement your gateway behind the same interfaces and the UI keeps working.',
  },
  {
    question: 'Does ops tooling ship in the box?',
    answer:
      'Health checks, status page, metrics, and the Starter CLI are part of the repo. You can enable alert subscriptions via the provided API and surface them on the marketing pages immediately.',
  },
];

export const CTA_CONFIG: CtaConfig = {
  title: 'Spin up your agent platform today.',
  description: 'Register for the console and deploy the starter with GPT-5 agents, billing, and observability pre-wired.',
  primaryCta: {
    label: 'Create an account',
    href: '/register',
    intent: 'primary',
  },
  secondaryCta: {
    label: 'See it in action',
    href: '/agents',
    intent: 'secondary',
  },
};
