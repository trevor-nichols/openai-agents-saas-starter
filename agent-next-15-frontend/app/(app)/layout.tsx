// File Path: app/(app)/layout.tsx
// Description: Authenticated application shell wrapping all in-app routes.
// Sections:
// - Imports & navigation config: Shared nav structure for the shell.
// - AppLayout component: Renders persistent top navigation and main content area.

import Link from 'next/link';

import { SilentRefresh } from '@/components/auth/SilentRefresh';

interface AppLayoutProps {
  children: React.ReactNode;
}

// --- Navigation configuration ---
// Central definition of primary navigation destinations inside the app shell.
const primaryNav = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/chat', label: 'Chat' },
  { href: '/conversations', label: 'Conversations' },
  { href: '/agents', label: 'Agents' },
  { href: '/tools', label: 'Tools' },
  { href: '/billing', label: 'Billing' },
];

const accountNav = [
  { href: '/account/profile', label: 'Profile' },
  { href: '/account/security', label: 'Security' },
  { href: '/account/sessions', label: 'Sessions' },
  { href: '/account/service-accounts', label: 'Service accounts' },
];

// --- AppLayout component ---
// Provides the authenticated chrome with silent session refresh and navigation.
export default function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col bg-slate-50 text-slate-900">
      <SilentRefresh />

      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-4 px-6 py-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-col gap-2">
            <Link href="/dashboard" className="text-lg font-semibold">
              Anything Agents Console
            </Link>
            <p className="text-xs text-slate-500">
              Configure agents, monitor conversations, and manage your tenant—all in one console.
            </p>
          </div>

          <nav aria-label="Primary application navigation" className="flex flex-wrap items-center gap-4 text-sm font-medium">
            {primaryNav.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-md px-3 py-1.5 text-slate-600 transition hover:bg-slate-100 hover:text-slate-900"
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>

      <div className="flex flex-1 flex-col lg:flex-row">
        <aside className="border-b border-slate-200 bg-white px-6 py-4 text-sm lg:w-64 lg:border-b-0 lg:border-r">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">Account</h2>
          <nav aria-label="Account navigation" className="mt-3 flex flex-col gap-2">
            {accountNav.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-md px-3 py-2 text-slate-600 transition hover:bg-slate-100 hover:text-slate-900"
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </aside>

        <main className="flex-1 overflow-y-auto bg-slate-50 px-6 py-10">
          <div className="mx-auto w-full max-w-6xl">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

