// File Path: app/(app)/layout.tsx
// Description: Authenticated application shell wrapping all in-app routes.
// Sections:
// - Imports & navigation config: Shared nav structure for the shell.
// - AppLayout component: Renders persistent top navigation and main content area.

import Link from 'next/link';

import { SilentRefresh } from '@/components/auth/SilentRefresh';
import { getSessionMetaFromCookies } from '@/lib/auth/cookies';
import { billingEnabled } from '@/lib/config/features';

interface AppLayoutProps {
  children: React.ReactNode;
}

// --- Navigation configuration ---
const primaryNav = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/chat', label: 'Workspace' },
  { href: '/agents', label: 'Agents' },
  ...(billingEnabled ? [{ href: '/billing', label: 'Billing' }] : []),
];

const accountNav = [
  { href: '/account', label: 'Account' },
  { href: '/settings/access', label: 'Signup guardrails' },
  { href: '/settings/tenant', label: 'Tenant settings' },
];

// --- AppLayout component ---
export default async function AppLayout({ children }: AppLayoutProps) {
  const session = await getSessionMetaFromCookies();
  const hasStatusScope = session?.scopes?.includes('status:manage') ?? false;
  const navItems = hasStatusScope ? [...primaryNav, { href: '/ops/status', label: 'Ops' }] : primaryNav;

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

        <nav aria-label="Primary navigation" className="mt-8 flex flex-col gap-1 text-sm font-medium">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-lg px-3 py-2 text-foreground/70 transition duration-quick ease-apple hover:bg-white/5 hover:text-foreground"
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="mt-auto">
          <p className="text-xs font-semibold uppercase tracking-wide text-foreground/50">Account</p>
          <nav aria-label="Account navigation" className="mt-3 flex flex-col gap-1 text-sm">
            {accountNav.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-lg px-3 py-2 text-foreground/70 transition duration-quick ease-apple hover:bg-white/5 hover:text-foreground"
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </aside>

      <div className="flex min-h-screen flex-1 flex-col">
        <header className="sticky top-0 z-30 border-b border-white/10 bg-background/80 backdrop-blur-glass">
          <div className="flex flex-col gap-4 px-4 py-4 sm:px-6 lg:px-8">
            <div className="flex flex-col gap-1">
              <p className="text-xs font-semibold uppercase tracking-[0.3em] text-foreground/50">Acme Console</p>
              <p className="text-sm text-foreground/70">{subtitle}</p>
            </div>

            <nav aria-label="Primary navigation mobile" className="flex gap-2 overflow-x-auto text-sm font-medium lg:hidden">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="rounded-pill border border-white/10 px-3 py-1.5 text-foreground/70 transition duration-quick ease-apple hover:border-white/40 hover:text-foreground"
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>

        <main className="relative flex-1 overflow-y-auto px-4 py-8 sm:px-6 lg:px-10">
          <div className="mx-auto w-full max-w-6xl space-y-10">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
