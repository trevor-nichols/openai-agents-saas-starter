import { Sparkles, Shield, BarChart3, Cable } from 'lucide-react';

import type { CtaConfig, FaqItem, FeatureHighlight, ProofPoint, LogoItem } from './types';
import type { ShowcaseTab } from '@/features/marketing/features/types';
import type { Testimonial } from '@/components/ui/testimonials';

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
    value: 'Shared auth, telemetry, and console scripts across FastAPI + Next.js 16.',
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
    bullets: ['Verified scopes on every router', 'Redis-backed refresh tokens', 'console-managed service accounts'],
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
    description: 'Health checks, status page, and Starter Console run side-by-side so ops is never an afterthought.',
    bullets: ['Status snapshot + RSS feeds', 'Starter Console env + key rotation', 'Observability middleware + Prom metrics'],
  },
];

export const FAQ_ITEMS: FaqItem[] = [
  {
    question: 'How fast can I launch with this starter?',
    answer:
      'Clone the repo, run the Starter Console to hydrate env files, and deploy the FastAPI + Next.js stacks with Docker or your preferred CI. Most teams see a branded console live in under a week.',
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
      'Health checks, status page, metrics, and the Starter Console are part of the repo. You can enable alert subscriptions via the provided API and surface them on the marketing pages immediately.',
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

export const LOGO_ITEMS: LogoItem[] = [
  'Snowshoe Capital',
  'Northwind Energy',
  'Atlas Labs',
  'Aurora Health',
  'LedgerStack',
  'Harbor Systems',
  'Bluebird Robotics',
  'Signalcraft',
];

export const TESTIMONIALS: Testimonial[] = [
  {
    quote: 'We rebranded and shipped a GPT-5 console in six days. Auth, billing, and ops were already wired.',
    name: 'Priya Narayanan',
    designation: 'VP Product, Series B SaaS',
    src: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" fill="none"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="%2364b5f6"/><stop offset="1" stop-color="%2312457a"/></linearGradient></defs><rect width="200" height="200" rx="32" fill="url(%23g)"/></svg>',
  },
  {
    quote: 'Ops loved that status feeds and incident emails were live on day one—no extra services to stitch in.',
    name: 'Caleb Rivers',
    designation: 'CTO, AI infra startup',
    src: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" fill="none"><rect width="200" height="200" rx="32" fill="%23222"/><circle cx="100" cy="100" r="90" fill="%23333"/><circle cx="100" cy="100" r="52" fill="%23555"/></svg>',
  },
  {
    quote: 'Status, billing, and the Starter Console let us pass enterprise vendor checks without slowing the launch.',
    name: 'Dana Schultz',
    designation: 'Head of Platform, fintech pilot',
    src: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" fill="none"><rect width="200" height="200" rx="32" fill="%23f5f5f5"/><path d="M30 140 L170 60" stroke="%23646cff" stroke-width="18" stroke-linecap="round"/><circle cx="60" cy="120" r="18" fill="%23646cff"/><circle cx="140" cy="80" r="18" fill="%23646cff"/></svg>',
  },
];

export const SHOWCASE_TABS: ShowcaseTab[] = [
  {
    id: 'agents',
    label: 'Agents',
    title: 'Operate multi-agent workspaces',
    description: 'Chat streaming, catalog search, and tool telemetry live in a single workspace so operators keep context.',
    bullets: ['Multi-agent routing with GPT-5 memory', 'Searchable transcripts + exports', 'Tool registry insights per run'],
  },
  {
    id: 'billing',
    label: 'Billing',
    title: 'Usage and plan automation',
    description: 'Stripe dispatcher, usage hooks, and SSE dashboards are prewired so pricing changes ship safely.',
    bullets: ['Plan catalogs + metered usage', 'Async retry worker for webhooks', 'Billing widgets powered by TanStack'],
  },
  {
    id: 'ops',
    label: 'Ops',
    title: 'Observability and status by default',
    description: 'Live uptime metrics, incident feeds, and console health checks keep stakeholders informed.',
    bullets: ['Status page + RSS feeds', 'Prom metrics + middleware', 'console-based env hydration + rotation'],
  },
];

export const OPERATOR_BULLETS = [
  'Live incident email flows with verification built in',
  'RBAC + service accounts enforced at every router',
  'Observability middleware and Prom metrics ready for scraping',
  'Starter Console hydrates envs and rotates keys without custom scripts',
] as const;
