// File Path: app/(app)/layout.tsx
// Description: Authenticated application shell wrapping all in-app routes.
// Sections:
// - Imports & navigation config: Shared nav structure for the shell.
// - AppLayout component: Renders persistent top navigation and main content area.

import { Suspense } from 'react';

import 'katex/dist/katex.min.css';

import { SilentRefresh } from '@/components/auth/SilentRefresh';
import { AppPageHeading } from '@/components/shell/AppPageHeading';
import { AppSidebar } from '@/components/shell/AppSidebar';
import { InfoMenu, NotificationMenu } from '@/components/ui/nav-bar';
import { Separator } from '@/components/ui/separator';
import { SidebarInset, SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar';
import { getSessionMetaFromCookies } from '@/lib/auth/cookies';
import { billingEnabled } from '@/lib/config/features';
import { buildNavItems } from './nav';

interface AppLayoutProps {
  children: React.ReactNode;
}

const accountNav = [
  { href: '/account', label: 'Account' },
  { href: '/settings/access', label: 'Signup guardrails' },
  { href: '/settings/tenant', label: 'Tenant settings' },
];

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
    <SidebarProvider>
      <SilentRefresh />

      <AppSidebar 
        navItems={navItems} 
        accountItems={accountNav} 
        user={{
            email: session?.userId,
            tenantId: session?.tenantId,
        }}
      />

      <SidebarInset>
        <header className="sticky top-0 z-30 flex shrink-0 items-center gap-2 border-b border-white/10 bg-background/80 px-4 py-4 backdrop-blur-glass transition-[width,height] ease-linear group-has-[[data-collapsible=icon]]/sidebar-wrapper:h-auto">
           <div className="flex items-center gap-2 self-start pt-1">
              <SidebarTrigger className="-ml-1" />
              <Separator orientation="vertical" className="mr-2 h-4" />
           </div>
          
          <div className="flex flex-1 flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <AppPageHeading navItems={navItems} accountItems={accountNav} subtitle={subtitle} />
            <div className="flex items-center gap-3 justify-end self-start sm:self-auto">
              <div className="hidden md:flex items-center gap-2">
                <InfoMenu />
                <NotificationMenu notificationCount={4} />
              </div>
            </div>
          </div>
        </header>

        <main className="relative flex-1 overflow-y-auto px-4 py-8 sm:px-6 lg:px-10">
          <div className="mx-auto w-full max-w-[1400px] space-y-8">
            {children}
          </div>
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}