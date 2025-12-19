// File Path: app/(app)/layout.tsx
// Description: Authenticated application shell wrapping all in-app routes.
// Sections:
// - Imports & navigation config: Shared nav structure for the shell.
// - AppLayout component: Renders persistent top navigation and main content area.

import { Suspense } from 'react';

import 'katex/dist/katex.min.css';

import { SilentRefresh } from '@/components/auth/SilentRefresh';
import { AppSidebar } from '@/components/shell/AppSidebar';
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';
import { getAppShellLayoutModel } from './_utils/getAppShellLayoutModel';

interface AppLayoutProps {
  children: React.ReactNode;
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
  const { session, navItems, accountNav, profile } = await getAppShellLayoutModel();

  return (
    <SidebarProvider>
      <SilentRefresh />

      <AppSidebar 
        navItems={navItems} 
        accountItems={accountNav} 
        user={{
            name: profile?.display_name ?? null,
            email: profile?.email ?? null,
            avatarUrl: profile?.avatar_url ?? null,
            tenantId: profile?.tenant_id ?? session?.tenantId ?? null,
        }}
      />

      <SidebarInset className="overflow-hidden">
        {children}
      </SidebarInset>
    </SidebarProvider>
  );
}
