// File Path: app/(marketing)/docs/page.tsx
// Description: Public documentation hub that reuses the marketing chrome and Shadcn components.

import Link from 'next/link';

import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { NavigationMenu, NavigationMenuItem, NavigationMenuLink, NavigationMenuList } from '@/components/ui/navigation-menu';
import { Separator } from '@/components/ui/separator';
import { GlassPanel, InlineTag, SectionHeader } from '@/components/ui/foundation';

const LAST_UPDATED = 'November 12, 2025';

const DOC_SECTIONS = [
  {
    id: 'getting-started',
    title: 'Getting started',
    summary: 'Clone the repo, provision secrets, and light up the full-stack experience.',
    bullets: [
      'Install dependencies with `pnpm install` and `hatch env create`.',
      'Use `starter-cli` to generate `.env` files for FastAPI + Next.js.',
      'Run `make dev` to boot Postgres/Redis plus both apps with shared secrets.',
    ],
    cta: { label: 'Starter CLI guide', href: '/docs#starter-cli' },
  },
  {
    id: 'auth-billing',
    title: 'Auth & billing',
    summary: 'Enterprise-ready flows for JWT auth, session refresh, and Stripe-compatible billing.',
    bullets: [
      'JWT cookies (Ed25519) handled via App Router API routes and server actions.',
      'Billing stream SSE proxy keeps dashboards live without exposing secrets.',
      'TanStack hooks (account, billing, sessions) centralize API access and caching.',
    ],
    cta: { label: 'Review auth cookbook', href: '/docs#auth' },
  },
  {
    id: 'agents-chat',
    title: 'Agents & chat workspace',
    summary: 'Hook up the OpenAI Agents SDK, multi-agent handoffs, and the streaming workspace.',
    bullets: [
      'Server-side `AgentService` wires SDK sessions, memory, and handoffs.',
      '`useChatController` orchestrates streaming, optimistic updates, and errors.',
      'Tool metadata drawer, agent switcher, and billing sidebar reuse shared hooks.',
    ],
    cta: { label: 'Chat integration runbook', href: '/docs#chat' },
  },
  {
    id: 'operations',
    title: 'Operations & observability',
    summary: 'Health checks, Vault transit, and CLI runbooks for production teams.',
    bullets: [
      'Marketing footer health card pings `/health` via `getHealthStatus` server helper.',
      'Vault dev signer workflows documented in `docs/security/vault-transit-signing.md`.',
      'Observability middleware emits structured logs with correlation IDs.',
    ],
    cta: { label: 'Operations checklist', href: '/docs#ops' },
  },
] as const;

const RESOURCE_LINKS = [
  { label: 'Backend API reference', href: '/docs/api', badge: 'OpenAPI' },
  { label: 'Frontend data-access guide', href: '/docs/frontend/data-access', badge: 'Guide' },
  { label: 'CLI milestone tracker', href: '/docs/trackers/CLI_MILESTONE', badge: 'Roadmap' },
  { label: 'Security threat model', href: '/docs/security/auth-threat-model', badge: 'Security' },
] as const;

const FAQ_ITEMS = [
  {
    question: 'How do I regenerate the HeyAPI client?',
    answer:
      'Run `pnpm api:generate` inside `agent-next-15-frontend`. The generator reads `openapi-ts.config.ts`, so keep that file updated when backend schemas change.',
  },
  {
    question: 'Where do I add new Shadcn components?',
    answer:
      'Use `pnpm shadcn add <component>` from the frontend root and log the addition inside `docs/frontend/ui/components.md` so the design system inventory stays accurate.',
  },
  {
    question: 'What’s the source of truth for environment variables?',
    answer:
      'Always run the CLI (`starter-cli env sync`) or the Make targets (`make env.dev`)—manual `.env` edits drift from the secrets contracts enforced in CI.',
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
              <InlineTag tone="positive">Live</InlineTag>
              <Badge variant="outline">Updated {LAST_UPDATED}</Badge>
            </div>
          }
        />

        <NavigationMenu className="max-w-full">
          <NavigationMenuList className="flex flex-wrap gap-3 rounded-full border border-foreground/10 bg-background/80 px-4 py-1 shadow-sm">
            {DOC_SECTIONS.map((section) => (
              <NavigationMenuItem key={section.id}>
                <NavigationMenuLink asChild>
                  <Link
                    href={`#${section.id}`}
                    className="rounded-full px-3 py-2 text-sm font-medium text-foreground/70 transition hover:bg-primary/10 hover:text-foreground"
                  >
                    {section.title}
                  </Link>
                </NavigationMenuLink>
              </NavigationMenuItem>
            ))}
          </NavigationMenuList>
        </NavigationMenu>
      </div>

      <div className="grid gap-10 lg:grid-cols-[minmax(0,2fr)_minmax(260px,1fr)]">
        <div className="space-y-8">
          {DOC_SECTIONS.map((section) => (
            <Card id={section.id} key={section.id} className="border-white/5 bg-white/90 shadow-lg shadow-primary/5">
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  {section.title}
                  <Badge variant="secondary">{section.id.replace('-', ' ')}</Badge>
                </CardTitle>
                <CardDescription>{section.summary}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <ul className="space-y-3 text-sm text-foreground/70">
                  {section.bullets.map((bullet) => (
                    <li key={bullet} className="rounded-xl border border-slate-200/60 bg-slate-50/70 px-4 py-3">
                      {bullet}
                    </li>
                  ))}
                </ul>
              </CardContent>
              <CardFooter>
                <Button asChild size="sm" variant="outline">
                  <Link href={section.cta.href}>{section.cta.label}</Link>
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>

        <div className="space-y-6">
          <GlassPanel className="space-y-4">
            <h3 className="text-lg font-semibold text-foreground">Quick resources</h3>
            <Separator className="border-white/5" />
            <ul className="space-y-3">
              {RESOURCE_LINKS.map((resource) => (
                <li key={resource.href} className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 px-4 py-3">
                  <div>
                    <p className="text-sm font-semibold text-foreground">{resource.label}</p>
                    <p className="text-xs text-foreground/60">{resource.badge === 'OpenAPI' ? 'Auto-generated schema' : 'Internal reference'}</p>
                  </div>
                  <Badge variant="secondary">{resource.badge}</Badge>
                </li>
              ))}
            </ul>
          </GlassPanel>

          <GlassPanel className="space-y-3">
            <h3 className="text-lg font-semibold text-foreground">Need a refresher?</h3>
            <p className="text-sm text-foreground/70">
              Watch the recorded walkthrough or ping the Platform Foundations channel—every flow in this starter mirrors exactly what we run in
              production.
            </p>
            <div className="flex flex-wrap gap-3">
              <Button asChild size="sm">
                <Link href="https://github.com/openai/openai-agents-starter">View repo</Link>
              </Button>
              <Button asChild size="sm" variant="outline">
                <Link href="/status">Status page</Link>
              </Button>
            </div>
          </GlassPanel>
        </div>
      </div>

      <div className="space-y-4">
        <SectionHeader
          eyebrow="FAQ"
          title="Answers to the most common questions"
          description="Design can expand this into a full knowledge base—these entries keep engineering unblocked today."
        />
        <Accordion type="single" collapsible className="rounded-2xl border border-white/10 bg-white/50 px-4 py-2 shadow-inner shadow-primary/5">
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
