// File Path: app/(marketing)/docs/page.tsx
// Purpose: Marketing documentation hub with navigation, stats, deep dives, and FAQ content.

import Link from 'next/link';

import { ArrowUpRight, BookOpenText, Sparkles } from 'lucide-react';

import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { NavigationMenu, NavigationMenuItem, NavigationMenuLink, NavigationMenuList } from '@/components/ui/navigation-menu';
import { Separator } from '@/components/ui/separator';
import { GlassPanel, InlineTag, KeyValueList, SectionHeader } from '@/components/ui/foundation';

const LAST_UPDATED = 'November 12, 2025';

type DocSection = {
  id: string;
  title: string;
  summary: string;
  bullets: readonly string[];
  badge: string;
  cta: {
    label: string;
    href: string;
  };
};

type DocResource = {
  label: string;
  description: string;
  href: string;
  badge: string;
};

type DocGuide = {
  title: string;
  description: string;
  href: string;
  minutes: string;
  updated: string;
  badge: string;
};

const DOC_SECTIONS: readonly DocSection[] = [
  {
    id: 'getting-started',
    title: 'Getting started',
    summary: 'Clone the starter, provision secrets, and boot both stacks with predictable defaults.',
    bullets: [
      'Install dependencies with `pnpm install` for the frontend and `hatch env create` for FastAPI.',
      'Use `starter-cli env sync` to hydrate `.env` files for dev, preview, and CI with the same answers file.',
      'Run `make dev` to start Postgres, Redis, FastAPI, and the Next.js workspace with shared JWT keys.',
    ],
    badge: 'Foundation',
    cta: { label: 'Starter CLI guide', href: '#getting-started' },
  },
  {
    id: 'auth-billing',
    title: 'Auth & billing',
    summary: 'Enterprise-ready JWT flows, service accounts, and Stripe-compatible billing orchestration.',
    bullets: [
      'Ed25519 JWT cookies and refresh tokens flow through FastAPI dependencies and Redis-backed revoke lists.',
      'Billing SSE stream keeps dashboard/billing panels live without exposing Stripe credentials to the browser.',
      'TanStack hooks (`useAccountProfileQuery`, `useBillingOverviewQuery`) centralize network/cache logic.',
    ],
    badge: 'Security',
    cta: { label: 'Review auth cookbook', href: '#auth-billing' },
  },
  {
    id: 'agents-chat',
    title: 'Agents & chat workspace',
    summary: 'Wire GPT-5 Agents SDK sessions, multi-agent handoffs, and the streaming UI orchestrator.',
    bullets: [
      '`AgentService` encapsulates SDK clients, memory, and transcript persistence with async SQLAlchemy.',
      '`useChatController` coordinates optimistic UI, retries, and error toasts across chat + drawer panels.',
      'Tool metadata drawer, agent switcher, and billing sidebar reuse shared hooks and `GlassPanel` primitives.',
    ],
    badge: 'Agents',
    cta: { label: 'Chat integration runbook', href: '#agents-chat' },
  },
  {
    id: 'operations',
    title: 'Operations & observability',
    summary: 'Health checks, Vault transit, CLI workflows, and structured logging for production teams.',
    bullets: [
      'Marketing footer health card calls `getHealthStatus()` so ops signals stay in front of visitors.',
      'Vault dev signer workflow (make vault-up / verify / down) is documented for local signing tests.',
      'Observability middleware emits correlation IDs, structured logs, and Prometheus metrics templates.',
    ],
    badge: 'Ops',
    cta: { label: 'Operations checklist', href: '#operations' },
  },
] as const;

const RESOURCE_LINKS: readonly DocResource[] = [
  {
    label: 'Backend API reference',
    description: 'OpenAPI schema + SDK surface for GPT-5 Agents, auth, billing, and conversations.',
    href: 'https://github.com/openai/openai-agents-starter/blob/main/docs/openai-agents-sdk/openai_raw_api_reference.md',
    badge: 'OpenAPI',
  },
  {
    label: 'Frontend data-access guide',
    description: 'TanStack Query patterns, hook layering, and generated HeyAPI client usage.',
    href: 'https://github.com/openai/openai-agents-starter/blob/main/docs/frontend/data-access.md',
    badge: 'Guide',
  },
  {
    label: 'Component inventory',
    description: 'Shadcn primitives plus glass foundation kit tracked for design + engineering parity.',
    href: 'https://github.com/openai/openai-agents-starter/blob/main/docs/frontend/ui/components.md',
    badge: 'UI Kit',
  },
  {
    label: 'Security threat model',
    description: 'JWT issuance, session refresh, Vault transit, and SOC2-ready mitigations.',
    href: 'https://github.com/openai/openai-agents-starter/blob/main/docs/security/auth-threat-model.md',
    badge: 'Security',
  },
] as const;

const DOC_GUIDES: readonly DocGuide[] = [
  {
    title: 'Starter CLI playbook',
    description: 'Provision secrets and env files via interactive prompts or headless `--answers-file` runs.',
    href: 'https://github.com/openai/openai-agents-starter/blob/main/docs/trackers/complete/MILESTONE_CLI.md',
    minutes: '10 min read',
    updated: 'Updated Nov 2025',
    badge: 'CLI',
  },
  {
    title: 'Stripe SaaS billing runbook',
    description: 'Connect plan catalogs, usage events, and billing dialogs with live SSE streams.',
    href: 'https://github.com/openai/openai-agents-starter/blob/main/docs/billing/stripe-runbook.md',
    minutes: '12 min read',
    updated: 'Updated Oct 2025',
    badge: 'Billing',
  },
  {
    title: 'Agents SDK integration guide',
    description: 'Wire GPT-5 Agents, memory, tools, and transcript persistence via FastAPI services.',
    href: 'https://github.com/openai/openai-agents-starter/blob/main/docs/openai-agents-sdk/table-of-contents.md',
    minutes: '15 min read',
    updated: 'Updated Nov 2025',
    badge: 'Agents',
  },
  {
    title: 'Vault transit & key rotation',
    description: 'Bring up the dev signer, issue tokens, and verify signatures before deploying.',
    href: 'https://github.com/openai/openai-agents-starter/blob/main/docs/security/vault-transit-signing.md',
    minutes: '8 min read',
    updated: 'Updated Sep 2025',
    badge: 'Security',
  },
] as const;

const DOC_TRACKS = ['architecture', 'auth', 'billing', 'frontend', 'integrations', 'openai-agents-sdk', 'ops', 'scripts', 'security', 'trackers'];

const DOC_STATS: Array<{ label: string; value: string; hint?: string }> = [
  {
    label: 'Doc tracks',
    value: `${DOC_TRACKS.length} tracks`,
    hint: DOC_TRACKS.slice(0, 5).join(', ') + '…',
  },
  {
    label: 'Guided playbooks',
    value: `${DOC_GUIDES.length} live`,
    hint: 'CLI, Billing, Agents, Security',
  },
  {
    label: 'Live trackers',
    value: '3 dashboards',
    hint: 'Frontend UI, Issue tracker, UI milestone',
  },
  {
    label: 'SDK kits',
    value: '10 kits',
    hint: 'Agents, Tools, Memory, Streaming, Tracing…',
  },
];

const FAQ_ITEMS = [
  {
    question: 'How do I regenerate the HeyAPI client?',
    answer:
      'Run `pnpm generate` inside `agent-next-15-frontend`. The generator reads `openapi-ts.config.ts`, so keep that file updated whenever backend schemas change.',
  },
  {
    question: 'Where do I add new Shadcn components?',
    answer:
      'Use `pnpm shadcn add <component>` from the frontend root and log the addition in `docs/frontend/ui/components.md` so the shared inventory stays accurate.',
  },
  {
    question: 'What’s the source of truth for environment variables?',
    answer:
      'Always run the Starter CLI (`starter-cli env sync`) or Make targets (`make env.dev`). Manual `.env` edits drift from the secrets contracts enforced in CI.',
  },
] as const;

export const metadata = {
  title: 'Documentation | Anything Agents',
  description: 'Live technical documentation for the Anything Agents starter.',
};

export default function DocsPage() {
  return (
    <div className="space-y-12">
      <div className="space-y-4">
        <SectionHeader
          eyebrow="Documentation"
          title="Build, ship, and operate Anything Agents"
          description="Everything you need to configure auth, wire billing, and extend the chat workspace."
          actions={
            <div className="flex items-center gap-3">
              <InlineTag tone="positive" icon={<Sparkles className="h-3 w-3" aria-hidden />}>
                Live
              </InlineTag>
              <Badge variant="outline">Updated {LAST_UPDATED}</Badge>
            </div>
          }
        />

        <NavigationMenu className="max-w-full">
          <NavigationMenuList className="flex flex-wrap gap-3 rounded-full border border-white/10 bg-white/5 px-4 py-1 shadow-sm">
            {DOC_SECTIONS.map((section) => (
              <NavigationMenuItem key={section.id}>
                <NavigationMenuLink asChild>
                  <Link
                    href={`#${section.id}`}
                    className="rounded-full px-3 py-2 text-sm font-medium text-foreground/80 transition hover:bg-primary/10 hover:text-foreground"
                  >
                    {section.title}
                  </Link>
                </NavigationMenuLink>
              </NavigationMenuItem>
            ))}
          </NavigationMenuList>
        </NavigationMenu>
      </div>

      <GlassPanel className="space-y-6">
        <div className="flex flex-wrap items-center gap-4">
          <span className="rounded-full bg-primary/10 p-2 text-primary">
            <BookOpenText className="h-5 w-5" aria-hidden />
          </span>
          <div>
            <p className="text-base font-semibold text-foreground">Documentation coverage</p>
            <p className="text-sm text-foreground/70">Map backend services, frontend features, and ops workflows without leaving this route.</p>
          </div>
        </div>
        <KeyValueList items={DOC_STATS} columns={2} />
      </GlassPanel>

      <div className="grid gap-10 lg:grid-cols-[minmax(0,2fr)_minmax(280px,1fr)]">
        <div className="space-y-8">
          {DOC_SECTIONS.map((section) => (
            <GlassPanel id={section.id} key={section.id} className="space-y-5 scroll-mt-32">
              <div className="flex flex-wrap items-center gap-3">
                <h3 className="text-lg font-semibold text-foreground">{section.title}</h3>
                <InlineTag>{section.badge}</InlineTag>
              </div>
              <p className="text-sm text-foreground/70">{section.summary}</p>
              <ul className="space-y-3 text-sm text-foreground/75">
                {section.bullets.map((bullet) => (
                  <li key={bullet} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                    {bullet}
                  </li>
                ))}
              </ul>
              <Button asChild size="sm" variant="outline">
                <Link href={section.cta.href}>{section.cta.label}</Link>
              </Button>
            </GlassPanel>
          ))}
        </div>

        <div className="space-y-6">
          <GlassPanel className="space-y-4">
            <h3 className="text-lg font-semibold text-foreground">Quick resources</h3>
            <Separator className="border-white/5" />
            <ul className="space-y-3">
              {RESOURCE_LINKS.map((resource) => (
                <li key={resource.href} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-foreground">{resource.label}</p>
                      <p className="text-xs text-foreground/60">{resource.description}</p>
                    </div>
                    <Badge variant="secondary">{resource.badge}</Badge>
                  </div>
                  <Link
                    href={resource.href}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-3 inline-flex items-center text-sm font-semibold text-primary hover:underline"
                    prefetch={false}
                  >
                    Open reference
                    <ArrowUpRight className="ml-1 h-4 w-4" aria-hidden />
                  </Link>
                </li>
              ))}
            </ul>
          </GlassPanel>

          <GlassPanel className="space-y-3">
            <h3 className="text-lg font-semibold text-foreground">Stay aligned</h3>
            <p className="text-sm text-foreground/70">
              Watch the recorded walkthrough, follow the issue tracker, or subscribe to real-time platform status updates.
            </p>
            <div className="flex flex-wrap gap-3">
              <Button asChild size="sm">
                <Link href="https://github.com/openai/openai-agents-starter" target="_blank" rel="noreferrer" prefetch={false}>
                  View repo
                </Link>
              </Button>
              <Button asChild size="sm" variant="outline">
                <Link href="/status">Status page</Link>
              </Button>
              <Button asChild size="sm" variant="ghost">
                <Link
                  href="https://github.com/openai/openai-agents-starter/blob/main/docs/trackers/ISSUE_TRACKER.md"
                  target="_blank"
                  rel="noreferrer"
                  prefetch={false}
                >
                  Issue tracker
                </Link>
              </Button>
            </div>
          </GlassPanel>
        </div>
      </div>

      <div className="space-y-4">
        <SectionHeader
          eyebrow="Guided playbooks"
          title="Deep dives maintained by Platform Foundations"
          description="Use these curated runs to onboard new teammates or refresh your own context."
        />
        <div className="grid gap-4 md:grid-cols-2">
          {DOC_GUIDES.map((guide) => (
            <GlassPanel key={guide.href} className="flex flex-col gap-4">
              <div className="flex items-center justify-between gap-3">
                <InlineTag>{guide.badge}</InlineTag>
                <span className="text-xs text-foreground/60">{guide.updated}</span>
              </div>
              <div>
                <h3 className="text-base font-semibold text-foreground">{guide.title}</h3>
                <p className="mt-1 text-sm text-foreground/70">{guide.description}</p>
              </div>
              <div className="flex items-center justify-between text-sm text-foreground/60">
                <span>{guide.minutes}</span>
                <Link
                  href={guide.href}
                  target="_blank"
                  rel="noreferrer"
                  prefetch={false}
                  className="inline-flex items-center font-semibold text-primary hover:underline"
                  aria-label={`Open ${guide.title}`}
                >
                  Start guide
                  <ArrowUpRight className="ml-1 h-4 w-4" aria-hidden />
                </Link>
              </div>
            </GlassPanel>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        <SectionHeader
          eyebrow="FAQ"
          title="Answers to the most common questions"
          description="Design can expand this into a full knowledge base—these entries keep engineering unblocked today."
        />
        <Accordion type="single" collapsible className="rounded-2xl border border-white/10 bg-white/5 px-4 py-2 shadow-inner shadow-primary/5">
          {FAQ_ITEMS.map((item) => (
            <AccordionItem key={item.question} value={item.question}>
              <AccordionTrigger className="text-left text-base font-semibold">{item.question}</AccordionTrigger>
              <AccordionContent className="text-sm text-foreground/70">{item.answer}</AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </div>
  );
}
