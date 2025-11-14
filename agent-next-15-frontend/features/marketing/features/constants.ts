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
    title: 'Agent orchestration',
    description: 'Bundle GPT-5 triage, tool routing, and transcript exports inside a single workspace.',
    bullets: [
      'Multi-agent handoffs with reasoning traces',
      'Streaming UI with TanStack + server actions',
      'Conversation archive + tool telemetry drawers',
    ],
    icon: MessageSquare,
    cta: {
      label: 'Explore agents workspace',
      href: '/agents',
      intent: 'primary',
    },
  },
  {
    id: 'billing',
    title: 'Subscription + usage billing',
    description: 'Stripe-ready plan catalogs, SSE dashboards, and optimistic plan management flows.',
    bullets: [
      'Catalog + usage APIs wired to FastAPI',
      'SSE billing events for live dashboards',
      'Tenant settings surface with metadata + flags',
    ],
    icon: WalletMinimal,
    cta: {
      label: 'Review billing console',
      href: '/billing',
      intent: 'secondary',
    },
  },
  {
    id: 'operations',
    title: 'Operations & security',
    description: 'Health endpoints, status page, CLI workflows, and Ed25519 auth ready from day one.',
    bullets: [
      'Marketing status page + alert subscriptions',
      'Starter CLI for envs, keys, and secrets',
      'Ed25519 JWT auth with service accounts',
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
    title: 'Chat, catalog, and tool telemetry',
    description: 'Switch between agents, audit tools, and inspect transcripts without leaving the workspace.',
    bullets: ['Agent catalog with tool counts', 'Conversation detail drawers', 'Streaming GPT-5 reasoning'],
  },
  {
    id: 'billing',
    label: 'Billing control hub',
    title: 'Live plan management & usage',
    description: 'Start subscriptions, record usage, and stream billing events via SSE for real-time dashboards.',
    bullets: ['Plan catalog queries', 'Usage recording API', 'Retry-safe dispatcher workers'],
  },
  {
    id: 'operations',
    label: 'Operations toolkit',
    title: 'Status, health, and CLI workflows',
    description: 'Marketing status page, RSS feed, and CLI commands keep customers informed without extra tooling.',
    bullets: ['Status subscriptions', 'Starter CLI env sync', 'Vault transit integration'],
  },
];

export const FEATURES_FAQ: MarketingFaqItem[] = [
  {
    question: 'Do I need to wire my own auth?',
    answer: 'No. The FastAPI stack ships with Ed25519 JWTs, refresh tokens, session management, and service accounts ready to use.',
  },
  {
    question: 'Can I add new agents or tools?',
    answer: 'Yes. Register agents in the Agents SDK config and attach tools via the registry helpers. The UI auto-renders the new entries.',
  },
  {
    question: 'How customizable is the chat workspace?',
    answer: 'Panels follow the feature directory spec, so you can replace components, add tabs, or introduce new drawers without touching shared hooks.',
  },
  {
    question: 'What deployment options exist?',
    answer: 'Docker + Compose files are included. Use the Starter CLI to hydrate secrets and deploy to any environment running Postgres + Redis.',
  },
];

export const FEATURES_CTA: CtaConfig = {
  eyebrow: 'Build faster',
  title: 'Launch your AI agent SaaS with confidence',
  description: 'Clone, configure, and deploy with GPT-5 agents, billing, and observability already dialed in.',
  primaryCta: {
    label: 'Get started',
    href: '/register',
    intent: 'primary',
  },
  secondaryCta: {
    label: 'Schedule a demo',
    href: 'mailto:founders@anythingagents.com',
    intent: 'secondary',
  },
};

export const FEATURES_TESTIMONIAL: Testimonial = {
  quote: '“Anything Agents let us ship a branded GPT-5 agent console in under two weeks. The plans, auth, and tooling were already enterprise-ready.”',
  author: 'Priya Sharma',
  role: 'Head of Platform, Northwind Ops',
};
