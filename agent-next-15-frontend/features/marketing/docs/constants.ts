import { BookOpenText, Sparkles, ArrowUpRight } from 'lucide-react';

import type { DocGuideCard, DocNavItem, DocResourceLink, DocSectionEntry, DocMetric } from './types';
import type { MarketingFaqItem, CtaConfig } from '@/features/marketing/types';

export const DOCS_HERO = {
  eyebrow: 'Documentation',
  title: 'Guides that match the architecture',
  description: 'Starter CLI runbooks, API references, and ops checklists live alongside the codebase so your team ships faster.',
  lastUpdated: 'November 13, 2025',
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
    summary: 'Clone the repo, hydrate envs via Starter CLI, and boot both stacks with predictable defaults.',
    bullets: [
      'Starter CLI env sync and answers files',
      'Docker + Make targets for local dev',
      'Shared JWT keys + Postgres migrations',
    ],
    badge: 'Foundation',
    cta: { label: 'Starter CLI guide', href: 'https://github.com/openai/openai-agents-starter/blob/main/docs/trackers/complete/MILESTONE_CLI.md', intent: 'primary' },
  },
  {
    id: 'auth-billing',
    title: 'Auth & billing',
    summary: 'Ed25519 JWT auth, service accounts, and Stripe-compatible billing orchestration.',
    bullets: [
      'Auth cookbooks + threat models',
      'Stripe runbook + billing dispatcher',
      'Tenant settings + plan metadata docs',
    ],
    badge: 'Security',
    cta: { label: 'Auth cookbook', href: 'https://github.com/openai/openai-agents-starter/blob/main/docs/security/auth-threat-model.md', intent: 'secondary' },
  },
  {
    id: 'agents-chat',
    title: 'Agents & chat',
    summary: 'GPT-5 Agents SDK sessions, multi-agent handoffs, and chat orchestration patterns.',
    bullets: [
      'Agents SDK table of contents',
      'Tool registry + MCP integration docs',
      'Chat workspace feature directory guide',
    ],
    badge: 'Agents',
    cta: { label: 'Agents SDK guide', href: 'https://github.com/openai/openai-agents-starter/blob/main/docs/openai-agents-sdk/table-of-contents.md', intent: 'secondary' },
  },
  {
    id: 'operations',
    title: 'Operations & observability',
    summary: 'Vault transit, status alert subscriptions, and CLI workflows for ops teams.',
    bullets: [
      'Vault transit signing runbook',
      'Status alert subscription contract',
      'Observability + health endpoint docs',
    ],
    badge: 'Ops',
    cta: { label: 'Operations checklist', href: 'https://github.com/openai/openai-agents-starter/blob/main/docs/security/vault-transit-signing.md', intent: 'secondary' },
  },
];

export const DOC_RESOURCES: DocResourceLink[] = [
  {
    label: 'Backend API reference',
    description: 'OpenAPI schema for GPT-5 agents, auth, billing, and conversations.',
    href: 'https://github.com/openai/openai-agents-starter/blob/main/docs/openai-agents-sdk/openai_raw_api_reference.md',
    badge: 'OpenAPI',
  },
  {
    label: 'Frontend data-access guide',
    description: 'TanStack Query patterns, hook layering, and generated HeyAPI usage.',
    href: 'https://github.com/openai/openai-agents-starter/blob/main/docs/frontend/data-access.md',
    badge: 'Guide',
  },
  {
    label: 'Component inventory',
    description: 'Shadcn components + glass kit tracked for designers/devs.',
    href: 'https://github.com/openai/openai-agents-starter/blob/main/docs/frontend/ui/components.md',
    badge: 'UI Kit',
  },
  {
    label: 'Security threat model',
    description: 'JWT issuance, refresh, and SOC2-aligned controls.',
    href: 'https://github.com/openai/openai-agents-starter/blob/main/docs/security/auth-threat-model.md',
    badge: 'Security',
  },
];

export const DOC_GUIDES: DocGuideCard[] = [
  {
    title: 'Starter CLI playbook',
    description: 'Provision secrets and env files via interactive prompts or headless runs.',
    href: 'https://github.com/openai/openai-agents-starter/blob/main/docs/trackers/complete/MILESTONE_CLI.md',
    minutes: '10 min read',
    updated: 'Updated Nov 2025',
    badge: 'CLI',
    icon: Sparkles,
  },
  {
    title: 'Stripe billing runbook',
    description: 'Connect plan catalogs, usage events, and SSE dashboards.',
    href: 'https://github.com/openai/openai-agents-starter/blob/main/docs/billing/stripe-runbook.md',
    minutes: '12 min read',
    updated: 'Updated Oct 2025',
    badge: 'Billing',
    icon: ArrowUpRight,
  },
  {
    title: 'Agents SDK integration',
    description: 'Wire GPT-5 Agents, tools, and transcript persistence.',
    href: 'https://github.com/openai/openai-agents-starter/blob/main/docs/openai-agents-sdk/table-of-contents.md',
    minutes: '15 min read',
    updated: 'Updated Nov 2025',
    badge: 'Agents',
    icon: BookOpenText,
  },
];

export const DOC_METRICS: DocMetric[] = [
  { label: 'Doc tracks', value: '10 tracks', hint: 'architecture, auth, billing…' },
  { label: 'Guided playbooks', value: '4 live', hint: 'CLI, billing, agents, security' },
  { label: 'Live trackers', value: '3 dashboards', hint: 'Frontend UI, Issue tracker, UI milestone' },
  { label: 'SDK kits', value: '10 kits', hint: 'Agents, Tools, Memory…' },
];

export const DOCS_FAQ: MarketingFaqItem[] = [
  {
    question: 'How do I regenerate the HeyAPI client?',
    answer: 'Run `pnpm generate` in `agent-next-15-frontend`. Keep `openapi-ts.config.ts` synced with backend schema changes.',
  },
  {
    question: 'Where do new Shadcn components live?',
    answer: 'Use `pnpm shadcn add` from the frontend root and log the addition in `docs/frontend/ui/components.md`.',
  },
  {
    question: 'What is the source of truth for env vars?',
    answer: 'The Starter CLI and Make targets. Avoid manual `.env` edits to stay aligned with CI.',
  },
];

export const DOCS_CTA: CtaConfig = {
  eyebrow: 'Docs',
  title: 'Ready to put the starter to work?',
  description: 'Follow the guides, wire your providers, and invite your first customers with confidence.',
  primaryCta: {
    label: 'Clone the repo',
    href: 'https://github.com/openai/openai-agents-starter',
    intent: 'primary',
  },
  secondaryCta: {
    label: 'Open Starter CLI',
    href: '/docs',
    intent: 'secondary',
  },
};
