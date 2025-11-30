// File Path: app/(app)/layout.tsx
// Description: Authenticated application shell wrapping all in-app routes.
// Sections:
// - Imports & navigation config: Shared nav structure for the shell.
// - AppLayout component: Renders persistent top navigation and main content area.

import { Suspense } from 'react';

import 'katex/dist/katex.min.css';

import { SilentRefresh } from '@/components/auth/SilentRefresh';
import { AppMobileNav } from '@/components/shell/AppMobileNav';
import type { AppNavItem } from '@/components/shell/AppNavLinks';
import { AppPageHeading } from '@/components/shell/AppPageHeading';
import { AppSidebar } from '@/components/shell/AppSidebar';
import { AppUserMenu } from '@/components/shell/AppUserMenu';
import { InfoMenu, NotificationMenu } from '@/components/ui/nav-bar';
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
    { href: '/workflows', label: 'Workflows' },
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
  if (!hasStatusScope) {
    return primaryNav;
  }

  const opsLinks: AppNavItem[] = [
    {
      href: '/ops/status',
      label: 'Ops',
      badge: 'Admin',
      badgeVariant: 'outline',
    },
    {
      href: '/ops/storage',
      label: 'Storage',
      badge: 'Admin',
      badgeVariant: 'outline',
    },
  ];

  return [...primaryNav, ...opsLinks];
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

      <AppSidebar navItems={navItems} accountItems={accountNav} />

      <div className="flex min-h-screen flex-1 flex-col">
        <header className="sticky top-0 z-30 border-b border-white/10 bg-background/80 backdrop-blur-glass">
          <div className="flex flex-col gap-4 px-4 py-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
            <AppPageHeading navItems={navItems} accountItems={accountNav} subtitle={subtitle} />
            <div className="flex items-center gap-3 lg:justify-end">
              <div className="hidden md:flex items-center gap-2">
                <InfoMenu />
                <NotificationMenu notificationCount={4} />
              </div>
              <div className="md:hidden">
                <AppMobileNav navItems={navItems} accountItems={accountNav} />
              </div>
              <AppUserMenu userName={null} userEmail={session?.userId ?? null} tenantId={session?.tenantId ?? null} />
            </div>
          </div>
        </header>

        <main className="relative flex-1 overflow-y-auto px-4 py-8 sm:px-6 lg:px-10">
          <div className="mx-auto w-full max-w-[1400px] space-y-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
