// File Path: app/(app)/layout.tsx
// Description: Authenticated application shell wrapping all in-app routes.
// Sections:
// - Imports & navigation config: Shared nav structure for the shell.
// - AppLayout component: Renders persistent top navigation and main content area.

import { Suspense } from 'react';
import Link from 'next/link';

import { SilentRefresh } from '@/components/auth/SilentRefresh';
import { AppMobileNav } from '@/components/shell/AppMobileNav';
import { AppNavLinks, type AppNavItem } from '@/components/shell/AppNavLinks';
import { AppPageHeading } from '@/components/shell/AppPageHeading';
import { getSessionMetaFromCookies } from '@/lib/auth/cookies';
import { billingEnabled } from '@/lib/config/features';

interface AppLayoutProps {
  children: React.ReactNode;
}

// --- Navigation configuration ---
export async function buildPrimaryNav(): Promise<AppNavItem[]> {
  return [
    { href: '/dashboard', label: 'Dashboard' },
    { href: '/chat', label: 'Workspace' },
    { href: '/agents', label: 'Agents' },
    ...(billingEnabled ? [{ href: '/billing', label: 'Billing' }] : []),
  ];
}

const accountNav: AppNavItem[] = [
  { href: '/account', label: 'Account' },
  { href: '/settings/access', label: 'Signup guardrails' },
  { href: '/settings/tenant', label: 'Tenant settings' },
];

export async function buildNavItems(hasStatusScope: boolean) {
  const primaryNav = await buildPrimaryNav();
  return hasStatusScope ? [...primaryNav, { href: '/ops/status', label: 'Ops' }] : primaryNav;
}

// --- AppLayout component ---
export default function AppLayout({ children }: AppLayoutProps) {
  return (
    <Suspense fallback={<div className="min-h-screen bg-background" />}>
      <AppLayoutContent>{children}</AppLayoutContent>
    </Suspense>
  );
}

async function AppLayoutContent({ children }: AppLayoutProps) {
  const session = await getSessionMetaFromCookies();
  const hasStatusScope = session?.scopes?.includes('status:manage') ?? false;
  const navItems = await buildNavItems(hasStatusScope);

  const subtitle = billingEnabled
    ? 'Configure agents, monitor conversations, and keep billing healthy.'
    : 'Configure agents and monitor conversations.';

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <SilentRefresh />

      <aside className="relative hidden w-[280px] flex-col border-r border-white/10 bg-background/70 p-6 backdrop-blur-glass lg:flex">
        <Link href="/dashboard" className="text-xl font-semibold tracking-tight">
          Acme
        </Link>
        <p className="mt-2 text-sm text-foreground/60">
          Operate your AI agent stack with confidence.
        </p>

        <nav aria-label="Primary navigation" className="mt-8 text-sm font-medium">
          <AppNavLinks items={navItems} />
        </nav>

        <div className="mt-auto">
          <p className="text-xs font-semibold uppercase tracking-wide text-foreground/50">Account</p>
          <nav aria-label="Account navigation" className="mt-3 text-sm">
            <AppNavLinks items={accountNav} />
          </nav>
        </div>
      </aside>

      <div className="flex min-h-screen flex-1 flex-col">
        <header className="sticky top-0 z-30 border-b border-white/10 bg-background/80 backdrop-blur-glass">
          <div className="flex items-start justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
            <AppPageHeading navItems={navItems} accountItems={accountNav} subtitle={subtitle} />
            <div className="lg:hidden">
              <AppMobileNav navItems={navItems} accountItems={accountNav} />
            </div>
          </div>
        </header>

        <main className="relative flex-1 overflow-y-auto px-4 py-8 sm:px-6 lg:px-10">
          <div className="mx-auto w-full max-w-6xl space-y-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
