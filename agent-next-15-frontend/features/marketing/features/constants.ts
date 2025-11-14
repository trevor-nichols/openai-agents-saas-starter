import { MessageSquare, ShieldCheck, WalletMinimal } from 'lucide-react';

import type { FeatureNavItem, FeaturePillar, ShowcaseTab, Testimonial } from './types';
import type { MarketingFaqItem, CtaConfig } from '@/features/marketing/types';

export const FEATURE_NAV: FeatureNavItem[] = [
  { id: 'agents', label: 'Agents' },
  { id: 'billing', label: 'Billing' },
  { id: 'operations', label: 'Operations' },
];

export const FEATURE_PILLARS: FeaturePillar[] = [
  {
    id: 'agents',
    title: 'Agents & chat control center',
    description: 'A feature-sliced workspace for GPT-5 conversations, catalog management, and tool visibility.',
    bullets: [
      'Multi-agent routing with GPT-5 sessions + handoffs',
      'Streaming UI powered by server actions + TanStack Query',
      'Conversation drawers with export + audit history',
    ],
    icon: MessageSquare,
    cta: {
      label: 'Open agents workspace',
      href: '/agents',
      intent: 'primary',
    },
  },
  {
    id: 'billing',
    title: 'Billing & usage automation',
    description: 'Stripe-ready plans, usage APIs, and optimistic UI flows backed by shared repositories.',
    bullets: [
      'Plan catalogs + usage hooks reusing FastAPI contracts',
      'SSE billing stream for dashboards and alerts',
      'Tenant settings form manages metadata and webhooks',
    ],
    icon: WalletMinimal,
    cta: {
      label: 'Review billing hub',
      href: '/billing',
      intent: 'secondary',
    },
  },
  {
    id: 'operations',
    title: 'Operations & security',
    description: 'Status, health, Starter CLI, and Vault-ready keys so ops stays in lockstep with product.',
    bullets: [
      'Status page + alert subscriptions share one API',
      'Starter CLI provisions secrets, envs, and keys',
      'Vault transit + Ed25519 key rotation runbooks',
    ],
    icon: ShieldCheck,
    cta: {
      label: 'View status & ops docs',
      href: '/status',
      intent: 'secondary',
    },
  },
];

export const SHOWCASE_TABS: ShowcaseTab[] = [
  {
    id: 'agents',
    label: 'Agents workspace',
    title: 'Command center for every agent',
    description: 'Toggle between catalog, chat, and telemetry panes with zero glue code.',
    bullets: ['Agent catalog with tool counts + filters', 'Conversation drawers with exports + retention tags', 'Streaming GPT-5 reasoning + event timeline'],
  },
  {
    id: 'billing',
    label: 'Billing control hub',
    title: 'Live plan + usage visibility',
    description: 'Manage subscriptions, log usage, and merge SSE streams into analytics instantly.',
    bullets: ['Plan catalog + usage mutations share hooks', 'Billing events stream into TanStack caches', 'Retry-safe dispatcher + worker tooling'],
  },
  {
    id: 'operations',
    label: 'Operations toolkit',
    title: 'Status, health, and CLI automation',
    description: 'Expose customer-facing status while operators run Starter CLI workflows behind the scenes.',
    bullets: ['Status alerts + RSS feeds reuse FastAPI endpoints', 'Starter CLI handles env sync + secrets rotation', 'Vault transit + Ed25519 key lifecycle docs'],
  },
];

export const FEATURES_FAQ: MarketingFaqItem[] = [
  {
    question: 'Do I need to implement auth or billing myself?',
    answer: 'No. Auth, billing, conversations, and status APIs already exist with tests and docs. You focus on brand + product decisions.',
  },
  {
    question: 'How do new agents or tools show up in the UI?',
    answer: 'Register them with the Agents SDK + tool registry and the orchestrator automatically renders updated catalogs, drawers, and badges.',
  },
  {
    question: 'Can I change the UI layout?',
    answer: 'Yes. Each feature uses the orchestrator/components/hooks pattern. Swap panels or add tabs without touching global providers.',
  },
  {
    question: 'What about deployments?',
    answer: 'Use Docker/Compose locally and promote builds through CI. The Starter CLI wires env files for dev, preview, and prod, and Vault transit handles key signing.',
  },
];

export const FEATURES_CTA: CtaConfig = {
  eyebrow: 'Feature tour',
  title: 'Own every pillar of your AI agent SaaS',
  description: 'Agents, billing, operations, and marketing surfaces stay in sync because they all share the same starter.',
  primaryCta: {
    label: 'Start building',
    href: '/register',
    intent: 'primary',
  },
  secondaryCta: {
    label: 'Inspect the workspace',
    href: '/agents',
    intent: 'secondary',
  },
};

export const FEATURES_TESTIMONIAL: Testimonial = {
  quote: '“We replaced months of platform plumbing with Anything Agents. GPT-5 routing, billing events, and ops dashboards landed together, so our team focused on the product.”',
  author: 'Priya Sharma',
  role: 'Head of Platform, Northwind Ops',
};
