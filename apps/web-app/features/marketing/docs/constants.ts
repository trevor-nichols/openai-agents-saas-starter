import { BookOpenText, Sparkles, ArrowUpRight } from 'lucide-react';

import type { DocGuideCard, DocNavItem, DocResourceLink, DocSectionEntry, DocMetric } from './types';
import type { MarketingFaqItem, CtaConfig } from '@/features/marketing/types';

export const DOCS_HERO = {
  eyebrow: 'Documentation',
  title: 'Guides that match the architecture',
  description:
    'Starter Console playbooks, auth runbooks, billing references, and status tooling live inside the repo so shipping never depends on tribal knowledge.',
  lastUpdated: 'November 14, 2025',
} as const;

export const DOC_NAV_ITEMS: DocNavItem[] = [
  { id: 'getting-started', label: 'Getting started' },
  { id: 'auth-billing', label: 'Auth & billing' },
  { id: 'agents-chat', label: 'Agents & chat' },
  { id: 'operations', label: 'Operations' },
];

export const DOC_SECTIONS: DocSectionEntry[] = [
  {
    id: 'getting-started',
    title: 'Getting started',
    summary: 'Prep local + cloud environments with the Starter Console, Make targets, and Docker workflow.',
    bullets: [
      'Starter Console env sync + answers files',
      'Docker + Make commands for dev/prod parity',
      'Shared JWT keys, Postgres migrations, and seed data',
    ],
    badge: 'Foundation',
    cta: { label: 'Starter Console quickstart', href: 'https://github.com/openai/openai-agents-saas-starter/blob/main/docs/trackers/complete/MILESTONE_CONSOLE.md', intent: 'primary' },
  },
  {
    id: 'auth-billing',
    title: 'Auth & billing',
    summary: 'Ed25519 JWT issuance, service accounts, Stripe billing orchestration, and tenant settings.',
    bullets: [
      'Auth threat models + token pipeline',
      'Stripe dispatcher + usage/billing APIs',
      'Tenant settings schema + form contracts',
    ],
    badge: 'Security',
    cta: { label: 'Auth + billing playbook', href: 'https://github.com/openai/openai-agents-saas-starter/blob/main/docs/security/auth-threat-model.md', intent: 'secondary' },
  },
  {
    id: 'agents-chat',
    title: 'Agents & chat',
    summary: 'GPT-5 Agents SDK sessions, tool registry guidance, and feature directory walkthroughs.',
    bullets: [
      'Agents SDK index + reasoning examples',
      'Tool registry + MCP integration docs',
      'Chat workspace structure + testing notes',
    ],
    badge: 'Agents',
    cta: { label: 'Agents SDK guide', href: 'https://github.com/openai/openai-agents-saas-starter/blob/main/docs/openai-agents-sdk/table-of-contents.md', intent: 'secondary' },
  },
  {
    id: 'operations',
    title: 'Operations & observability',
    summary: 'Status feeds, alert subscriptions, metrics, Vault transit, and Starter Console ops workflows.',
    bullets: [
      'Vault transit signing + key rotation runbook',
      'Status alert subscription API contract',
      'Observability + health endpoint reference',
    ],
    badge: 'Ops',
    cta: { label: 'Operations checklist', href: 'https://github.com/openai/openai-agents-saas-starter/blob/main/docs/security/vault-transit-signing.md', intent: 'secondary' },
  },
];

export const DOC_RESOURCES: DocResourceLink[] = [
  {
    label: 'Backend API reference',
    description: 'OpenAPI schema for GPT-5 agents, auth, billing, and conversations.',
    href: 'https://github.com/openai/openai-agents-saas-starter/blob/main/docs/openai-agents-sdk/openai_raw_api_reference.md',
    badge: 'OpenAPI',
  },
  {
    label: 'Frontend data-access guide',
    description: 'TanStack Query patterns, hook layering, and generated HeyAPI usage.',
    href: 'https://github.com/openai/openai-agents-saas-starter/blob/main/docs/frontend/data-access.md',
    badge: 'Guide',
  },
  {
    label: 'Component inventory',
    description: 'Shadcn components + glass kit tracked for designers/devs.',
    href: 'https://github.com/openai/openai-agents-saas-starter/blob/main/docs/frontend/ui/components.md',
    badge: 'UI Kit',
  },
  {
    label: 'Security threat model',
    description: 'JWT issuance, refresh, and SOC2-aligned controls.',
    href: 'https://github.com/openai/openai-agents-saas-starter/blob/main/docs/security/auth-threat-model.md',
    badge: 'Security',
  },
];

export const DOC_GUIDES: DocGuideCard[] = [
  {
    title: 'Starter Console playbook',
    description: 'Hydrate env files, rotate keys, and export audit bundles via interactive or headless runs.',
    href: 'https://github.com/openai/openai-agents-saas-starter/blob/main/docs/trackers/complete/MILESTONE_CONSOLE.md',
    minutes: '10 min read',
    updated: 'Updated Nov 2025',
    badge: 'Console',
    icon: Sparkles,
  },
  {
    title: 'Stripe billing runbook',
    description: 'Connect plan catalogs, usage events, SSE dashboards, and retry-safe workers.',
    href: 'https://github.com/openai/openai-agents-saas-starter/blob/main/docs/billing/stripe-runbook.md',
    minutes: '12 min read',
    updated: 'Updated Oct 2025',
    badge: 'Billing',
    icon: ArrowUpRight,
  },
  {
    title: 'Agents SDK integration',
    description: 'Wire GPT-5 Agents, tools, conversations, and memory persistence.',
    href: 'https://github.com/openai/openai-agents-saas-starter/blob/main/docs/openai-agents-sdk/table-of-contents.md',
    minutes: '15 min read',
    updated: 'Updated Nov 2025',
    badge: 'Agents',
    icon: BookOpenText,
  },
];

export const DOC_METRICS: DocMetric[] = [
  { label: 'Doc tracks', value: '10 tracks', hint: 'architecture · auth · billing · ops' },
  { label: 'Guided playbooks', value: '4 live', hint: 'Console · billing · agents · security' },
  { label: 'Live trackers', value: '3 dashboards', hint: 'UI milestone · issue tracker · Console roadmap' },
  { label: 'SDK kits', value: '10 kits', hint: 'Agents · tools · memory · handoffs' },
];

export const DOCS_FAQ: MarketingFaqItem[] = [
  {
    question: 'How do I regenerate the HeyAPI client?',
    answer: 'Run `pnpm generate` from `web-app`. The script reads the FastAPI OpenAPI schema and rewrites the client + types.',
  },
  {
    question: 'Where should new UI primitives be documented?',
    answer: 'Add shadcn components via `pnpm shadcn add` and log them in `docs/frontend/ui/components.md` so design + eng stay aligned.',
  },
  {
    question: 'What keeps env vars consistent?',
    answer: 'The Starter Console owns env generation. Use the console or the supplied Make targets; avoid editing `.env` files manually so CI, local, and prod stay in sync.',
  },
];

export const DOCS_CTA: CtaConfig = {
  eyebrow: 'Docs',
  title: 'Build with guidance baked in.',
  description: 'Every workflow—console, auth, billing, agents, ops—is documented here. Keep the docs open while you ship.',
  primaryCta: {
    label: 'Clone the repo',
    href: 'https://github.com/openai/openai-agents-saas-starter',
    intent: 'primary',
  },
  secondaryCta: {
    label: 'Browse the guides',
    href: '/docs',
    intent: 'secondary',
  },
};
